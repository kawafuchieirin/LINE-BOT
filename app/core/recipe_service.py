"""
Core recipe service for multi-channel dinner suggestion bot
Handles both ingredient-based and mood-based recipe generation
"""
import re
from typing import Dict, Any, List, Optional
from core.claude_client import create_claude_client
from utils.logger import setup_logger, log_recipe_generation

logger = setup_logger(__name__)


class RecipeService:
    """Service for generating recipe suggestions"""
    
    def __init__(self, claude_client=None):
        """
        Initialize recipe service
        
        Args:
            claude_client: Optional Claude client instance
        """
        self.claude_client = claude_client or create_claude_client()
        
        # Mood keywords for classification
        self.mood_keywords = [
            'さっぱり', 'あっさり', 'こってり', 'ガッツリ', 'ヘルシー',
            '夏バテ', '疲れ', 'スタミナ', '温まる', '冷たい',
            '辛い', '甘い', '優しい', '濃厚', 'サッパリ',
            '気分', '食べたい', '系', 'な感じ', '的な',
            '元気', 'パワー', '軽め', '重め', '食欲',
            'がっつり', 'しっかり', 'ボリューム', '満足',
            '和風', '洋風', '中華', 'エスニック', 'イタリアン'
        ]
        
        # Ingredient indicators
        self.ingredient_indicators = ['と', 'や', '、', 'の', 'が残って', 'がある', 'を使って']
    
    def generate_recipe_suggestions(
        self, 
        user_input: str,
        channel: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate recipe suggestions based on user input
        
        Args:
            user_input: User's input (ingredients or mood)
            channel: Request channel (line, slack, etc.)
            max_tokens: Maximum tokens for generation
            temperature: Generation temperature
            
        Returns:
            Dict containing:
                - success: bool
                - recipes: List[Dict] or None
                - error: str or None
                - input_type: 'mood' or 'ingredient'
        """
        # Classify input type
        is_mood_based = self._is_mood_based_input(user_input)
        input_type = 'mood' if is_mood_based else 'ingredient'
        
        # Log the request
        log_recipe_generation(logger, channel, input_type, user_input)
        
        # Create appropriate prompt
        if is_mood_based:
            prompt = self._create_mood_based_prompt(user_input)
        else:
            prompt = self._create_ingredient_based_prompt(user_input)
        
        # Generate completion
        result = self.claude_client.generate_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if not result['success']:
            return {
                'success': False,
                'recipes': None,
                'error': result['error'],
                'input_type': input_type
            }
        
        # Parse recipes from response
        recipes = self._parse_recipe_response(result['content'])
        
        return {
            'success': True,
            'recipes': recipes,
            'error': None,
            'input_type': input_type
        }
    
    def _is_mood_based_input(self, user_input: str) -> bool:
        """
        Determine if user input is mood-based or ingredient-based
        
        Args:
            user_input: User's input text
            
        Returns:
            True if mood-based, False if ingredient-based
        """
        input_lower = user_input.lower()
        
        # Check for mood keywords
        has_mood_keyword = any(keyword in input_lower for keyword in self.mood_keywords)
        
        # Count ingredient indicators
        ingredient_count = sum(1 for indicator in self.ingredient_indicators if indicator in user_input)
        
        # If many ingredient indicators, likely ingredient-based
        if ingredient_count >= 2:
            return False
        
        return has_mood_keyword
    
    def _create_ingredient_based_prompt(self, ingredients: str) -> str:
        """Create prompt for ingredient-based recipe generation"""
        return f"""あなたは優秀な料理アドバイザーです。
以下の食材を使って、美味しい晩御飯のメニューを2-3個提案してください。
各メニューについて、簡単な説明も付けてください。

食材: {ingredients}

提案フォーマット:
🍽️ メニュー提案

1. [メニュー名]
   - 簡単な説明

2. [メニュー名]
   - 簡単な説明

必要に応じて3つ目のメニューも提案してください。
メニュー名は具体的で、作りたくなるような名前にしてください。
説明は1-2文で、調理方法の特徴や味の特徴を含めてください。"""
    
    def _create_mood_based_prompt(self, mood_input: str) -> str:
        """Create prompt for mood-based recipe generation"""
        return f"""あなたはプロの料理アドバイザーです。
ユーザーの今の気分や食べたいものの希望に基づいて、ぴったりの晩御飯メニューを提案してください。

ユーザーの気分・希望: {mood_input}

この気分にぴったり合う晩御飯メニューを2-3個提案してください。
各メニューについて、なぜその気分に合うのか、どんな味わいや特徴があるのかも含めて説明してください。

提案フォーマット:
🍽️ メニュー提案

1. [メニュー名]
   - 簡単な説明（この気分に合う理由、味の特徴、調理のポイントなど）

2. [メニュー名]
   - 簡単な説明（この気分に合う理由、味の特徴、調理のポイントなど）

必要に応じて3つ目のメニューも提案してください。
メニュー名は具体的で、作りたくなるような名前にしてください。
説明は2-3文で、なぜその気分にマッチするかを含めて記載してください。"""
    
    def _parse_recipe_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse recipe response into structured format
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            List of recipe dictionaries
        """
        recipes = []
        
        # Pattern to match recipe entries
        # Matches: 1. Recipe Name
        #         - Description
        pattern = r'(\d+)\.\s*(.+?)\n\s*-\s*(.+?)(?=\n\d+\.|$)'
        
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        for match in matches:
            number, name, description = match
            recipes.append({
                'number': number.strip(),
                'name': name.strip(),
                'description': description.strip()
            })
        
        # If no recipes found with the pattern, try a simpler approach
        if not recipes:
            logger.warning("Could not parse recipes with standard pattern, trying fallback")
            # Split by numbers and extract what we can
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
        
        logger.info(f"Parsed {len(recipes)} recipes from response")
        return recipes


# Factory function
def create_recipe_service(claude_client=None) -> RecipeService:
    """
    Create recipe service instance
    
    Args:
        claude_client: Optional Claude client instance
        
    Returns:
        RecipeService instance
    """
    return RecipeService(claude_client)