"""
Slack Bot handler for dinner suggestion bot
"""
import json
import time
import hmac
import hashlib
from typing import Dict, Any
from urllib.parse import parse_qs
from config import config
from recipe_service import RecipeService


class SlackBotHandler:
    """Handler for Slack Bot functionality"""
    
    def __init__(self):
        """Initialize Slack Bot handler"""
        print("DEBUG: Initializing SlackBotHandler")
        # Validate configuration
        valid, error = config.validate_slack_config()
        if not valid:
            print(f"Slack configuration not complete: {error}")
        else:
            print("DEBUG: Slack configuration is valid")
        
        try:
            self.recipe_service = RecipeService()
            print("DEBUG: Recipe service initialized successfully")
        except Exception as e:
            print(f"DEBUG: Error initializing recipe service: {str(e)}")
            raise
    
    def handle_slash_command(self, body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Slack slash command (/dinner)"""
        # Verify Slack signature
        if not self._verify_signature(body, headers):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        try:
            # Parse slash command data
            command_data = parse_qs(body)
            text = command_data.get('text', [''])[0]
            
            # If no text provided, show help
            if not text.strip():
                return self._create_help_response()
            
            # Generate recipe suggestions (optimized for 3-second limit)
            print(f"DEBUG: Generating recipe for text: '{text}'")
            result = self.recipe_service.generate_recipe(text, max_tokens=800)
            print(f"DEBUG: Recipe generation result: success={result['success']}, error={result.get('error')}")
            
            if not result['success']:
                print(f"DEBUG: Recipe generation failed: {result.get('error')}")
                # Temporarily return the actual error for debugging
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'ephemeral',
                        'text': f'🔍 Debug Error: {result.get("error", "Unknown error")}'
                    })
                }
            
            # Format response for Slack
            response = self._format_slack_response(result['recipes'], result['input_type'])
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response)
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in slash command handler: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return self._create_error_response("An unexpected error occurred")
    
    def handle_event(self, body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Slack event (mentions, DMs)"""
        # Verify Slack signature
        if not self._verify_signature(body, headers):
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        try:
            event_data = json.loads(body)
            
            # Handle URL verification challenge
            if event_data.get('type') == 'url_verification':
                return {
                    'statusCode': 200,
                    'body': json.dumps({'challenge': event_data['challenge']})
                }
            
            # Handle app_mention and message events
            event = event_data.get('event', {})
            event_type = event.get('type')
            
            if event_type not in ['app_mention', 'message']:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'ignored'})
                }
            
            # Extract message text
            text = event.get('text', '')
            text = self._remove_bot_mention(text)
            
            # Generate recipe suggestions
            result = self.recipe_service.generate_recipe(text, max_tokens=800)
            
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'})
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }
    
    def _verify_signature(self, body: str, headers: Dict[str, str]) -> bool:
        """Verify Slack request signature"""
        if not config.slack_signing_secret:
            return True
        
        # Temporarily skip verification for testing
        print("TEMP: Skipping signature verification for testing")
        return True
        
        # Get headers with case-insensitive lookup
        timestamp = None
        signature = None
        
        for key, value in headers.items():
            if key.lower() == 'x-slack-request-timestamp':
                timestamp = value
            elif key.lower() == 'x-slack-signature':
                signature = value
        
        if not timestamp or not signature:
            print(f"Missing headers - timestamp: {bool(timestamp)}, signature: {bool(signature)}")
            return False
        
        try:
            # Check timestamp to prevent replay attacks (5 minutes tolerance)
            current_time = time.time()
            request_time = float(timestamp)
            if abs(current_time - request_time) > 300:
                print(f"Timestamp too old: {current_time - request_time} seconds")
                return False
            
            # Create signature base string
            sig_basestring = f"v0:{timestamp}:{body}"
            
            # Calculate expected signature
            expected_sig = 'v0=' + hmac.new(
                config.slack_signing_secret.encode('utf-8'),
                sig_basestring.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(expected_sig, signature)
            
            if not is_valid:
                print(f"Signature mismatch - expected: {expected_sig[:20]}..., got: {signature[:20]}...")
                print(f"Base string: {sig_basestring}")
            
            return is_valid
            
        except (ValueError, TypeError) as e:
            print(f"Signature verification error: {str(e)}")
            return False
    
    def _create_help_response(self) -> Dict[str, Any]:
        """Create help response for Slack"""
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': '🍽️ 晩御飯提案BOTの使い方',
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': '*晩御飯提案BOTの使い方*\n\n食材や気分を教えてください。美味しいメニューを提案します！'
                        }
                    },
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': '*📝 使用例*\n• `/dinner キャベツと鶏肉`\n• `/dinner さっぱりしたものが食べたい`'
                        }
                    }
                ]
            })
        }
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create error response for Slack"""
        error_messages = {
            "The service is currently experiencing high demand. Please try again in a moment.": 
                "現在アクセスが集中しています。少し時間をおいてからお試しください。",
            "The AI model is preparing. Please wait a moment and try again.":
                "AIモデルが準備中です。しばらくお待ちください。",
            "An error occurred while processing your request.":
                "レシピの生成中にエラーが発生しました。"
        }
        
        message = error_messages.get(error, "エラーが発生しました。もう一度お試しください。")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'⚠️ {message}'
            })
        }
    
    def _format_slack_response(self, recipes: list, input_type: str) -> Dict[str, Any]:
        """Format recipes for Slack response"""
        if not recipes:
            return {
                'response_type': 'in_channel',
                'text': 'レシピが見つかりませんでした。'
            }
        
        # Create blocks for rich formatting
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': '🍽️ メニュー提案'
                }
            }
        ]
        
        # Add context about input type
        context_text = "気分に合わせた提案" if input_type == 'mood' else "食材を使った提案"
        blocks.append({
            'type': 'context',
            'elements': [{
                'type': 'mrkdwn',
                'text': f'_{context_text}_'
            }]
        })
        
        # Add each recipe as a section
        for recipe in recipes:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*{recipe['number']}. {recipe['name']}*\n{recipe['description']}"
                }
            })
        
        # Add divider at the end
        blocks.append({'type': 'divider'})
        
        return {
            'response_type': 'in_channel',
            'text': '🍽️ メニュー提案',
            'blocks': blocks
        }
    
    def _remove_bot_mention(self, text: str) -> str:
        """Remove bot mention from message text"""
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()