"""
Recipe service for generating dinner suggestions using Claude 3.5 Sonnet
Handles both ingredient-based and mood-based recipe generation
Supports both AWS Bedrock and Claude SDK backends
"""
import json
import re
import os
import boto3
from typing import Dict, Any, List
from botocore.exceptions import ClientError
from config import config
from claude_sdk_client import ClaudeSDKClient


class RecipeService:
    """Service for generating recipe suggestions using AWS Bedrock Claude"""
    
    def __init__(self):
        """Initialize recipe service with Bedrock client and optionally Claude SDK"""
        # Check if we should use Claude SDK
        self.use_claude_sdk = os.environ.get('USE_CLAUDE_SDK', 'false').lower() == 'true'
        
        if self.use_claude_sdk:
            self.claude_sdk_client = ClaudeSDKClient()
            print("RecipeService: Using Claude SDK backend")
        else:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=config.aws_region
            )
            self.model_id = config.bedrock_model_id
            print("RecipeService: Using AWS Bedrock backend")
        
        # Mood keywords for classification
        self.mood_keywords = [
            'さっぱり', 'あっさり', 'こってり', 'ガッツリ', 'ヘルシー',
            '夏バテ', '疲れ', 'スタミナ', '温まる', '冷たい', '辛い', '甘い',
            '気分', '食べたい', '系', '元気', '軽め', '重め', '食欲'
        ]
    
    def generate_recipe(self, user_input: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate recipe suggestions based on user input
        
        Args:
            user_input: User's input (ingredients or mood)
            max_tokens: Maximum tokens for generation
            
        Returns:
            Dict with success, recipes, error, and input_type
        """
        # Use Claude SDK if enabled
        if self.use_claude_sdk:
            channel = os.environ.get('CHANNEL_TYPE', 'unknown')
            user_id = os.environ.get('USER_ID', 'unknown')
            return self.claude_sdk_client.generate_recipe(user_input, channel, user_id)
        
        # Otherwise use Bedrock
        try:
            # Determine input type
            is_mood_based = self._is_mood_based_input(user_input)
            input_type = 'mood' if is_mood_based else 'ingredient'
            
            # Create appropriate prompt
            prompt = self._create_prompt(user_input, is_mood_based)
            
            # Generate response
            response = self._invoke_claude(prompt, max_tokens)
            
            # Parse recipes
            recipes = self._parse_recipes(response)
            
            return {
                'success': True,
                'recipes': recipes,
                'error': None,
                'input_type': input_type
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = self._handle_bedrock_error(error_code)
            return {
                'success': False,
                'recipes': None,
                'error': error_message,
                'input_type': 'ingredient'
            }
        except Exception as e:
            return {
                'success': False,
                'recipes': None,
                'error': "An unexpected error occurred",
                'input_type': 'ingredient'
            }
    
    def _is_mood_based_input(self, user_input: str) -> bool:
        """Determine if input is mood-based or ingredient-based"""
        input_lower = user_input.lower()
        has_mood_keyword = any(keyword in input_lower for keyword in self.mood_keywords)
        ingredient_indicators = ['と', 'や', '、', 'の', 'が残って', 'がある']
        ingredient_count = sum(1 for indicator in ingredient_indicators if indicator in user_input)
        
        if ingredient_count >= 2:
            return False
        return has_mood_keyword
    
    def _create_prompt(self, user_input: str, is_mood_based: bool) -> str:
        """Create appropriate prompt based on input type"""
        if is_mood_based:
            return f"""あなたはプロの料理アドバイザーです。
ユーザーの今の気分や食べたいものの希望に基づいて、ぴったりの晩御飯メニューを提案してください。

ユーザーの気分・希望: {user_input}

この気分にぴったり合う晩御飯メニューを2-3個提案してください。

提案フォーマット:
1. [メニュー名]
   - 簡単な説明

2. [メニュー名]  
   - 簡単な説明

メニュー名は具体的で、説明は2-3文で記載してください。"""
        else:
            return f"""あなたは優秀な料理アドバイザーです。
以下の食材を使って、美味しい晩御飯のメニューを2-3個提案してください。

食材: {user_input}

提案フォーマット:
1. [メニュー名]
   - 簡単な説明

2. [メニュー名]
   - 簡単な説明

メニュー名は具体的で、説明は1-2文で記載してください。"""
    
    def _invoke_claude(self, prompt: str, max_tokens: int) -> str:
        """Invoke Claude model via Bedrock"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.95
        }
        
        print(f"DEBUG: Bedrock request body: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        print(f"DEBUG: Model ID: {self.model_id}")
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            print(f"DEBUG: Bedrock response body: {json.dumps(response_body, indent=2, ensure_ascii=False)}")
            return response_body['content'][0]['text']
            
        except ClientError as e:
            print(f"DEBUG: Bedrock ClientError: {e.response}")
            raise
        except Exception as e:
            print(f"DEBUG: Bedrock Exception: {str(e)}")
            raise
    
    def _parse_recipes(self, response_text: str) -> List[Dict[str, str]]:
        """Parse recipe response into structured format"""
        recipes = []
        pattern = r'(\d+)\.\s*(.+?)\n\s*-\s*(.+?)(?=\n\d+\.|$)'
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        for match in matches:
            number, name, description = match
            recipes.append({
                'number': number.strip(),
                'name': name.strip(),
                'description': description.strip()
            })
        
        # Fallback parsing if no matches
        if not recipes:
            lines = response_text.split('\n')
            current_recipe = None
            
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    if current_recipe:
                        recipes.append(current_recipe)
                    current_recipe = {
                        'number': re.match(r'^(\d+)\.', line).group(1),
                        'name': re.sub(r'^\d+\.\s*', '', line),
                        'description': ''
                    }
                elif line.startswith('-') and current_recipe:
                    current_recipe['description'] = line[1:].strip()
            
            if current_recipe:
                recipes.append(current_recipe)
        
        return recipes
    
    def _handle_bedrock_error(self, error_code: str) -> str:
        """Convert Bedrock error codes to user-friendly messages"""
        error_messages = {
            'ThrottlingException': "The service is currently experiencing high demand. Please try again in a moment.",
            'ModelNotReadyException': "The AI model is preparing. Please wait a moment and try again.",
            'ValidationException': "Invalid request format. Please check your input.",
            'AccessDeniedException': "Access denied to the AI service.",
            'ServiceUnavailableException': "The service is temporarily unavailable."
        }
        return error_messages.get(error_code, "An error occurred while processing your request.")