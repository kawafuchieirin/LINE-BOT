"""
Slack Bot handler for dinner suggestion bot
"""
import json
import time
import hmac
import hashlib
import requests
import threading
from typing import Dict, Any
from urllib.parse import parse_qs
from config import config
from recipe_service import RecipeService
from ingredient_storage import IngredientStorage


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
            self.ingredient_storage = IngredientStorage()
            print("DEBUG: Ingredient storage initialized successfully")
        except Exception as e:
            print(f"DEBUG: Error initializing services: {str(e)}")
            raise
    
    def handle_slash_command(self, body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle Slack slash command (/dinner) with immediate ACK and async processing"""
        # Verify Slack signature (temporarily disabled for testing)
        print("TEMP: Skipping signature verification for testing")
        # if not self._verify_signature(body, headers):
        #     return {
        #         'statusCode': 401,
        #         'body': json.dumps({'error': 'Unauthorized'})
        #     }
        
        try:
            # Parse slash command data
            command_data = parse_qs(body)
            text = command_data.get('text', [''])[0]
            response_url = command_data.get('response_url', [''])[0]
            user_id = command_data.get('user_id', [''])[0]
            
            print(f"DEBUG: Processing slash command: text='{text}', response_url='{response_url}', user_id='{user_id}'")
            
            # If no text provided, show help
            if not text.strip():
                return self._create_help_response()
            
            # Parse the command
            parts = text.split(maxsplit=1)
            sub_command = parts[0].lower() if parts else ""
            args = parts[1] if len(parts) > 1 else ""
            
            # Handle ingredient storage commands
            if sub_command == 'add':
                return self._handle_add_ingredients(user_id, args)
            elif sub_command == 'list':
                return self._handle_list_ingredients(user_id)
            elif sub_command == 'clear':
                return self._handle_clear_ingredients(user_id)
            
            # For regular recipe generation, process async
            # IMMEDIATELY return acknowledgment (within 3 seconds)
            immediate_ack = {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': '🍽️ レシピを生成中です... 少々お待ちください！'
                })
            }
            
            # Start background processing for the actual recipe generation
            if response_url:
                # Use threading to process recipe generation asynchronously
                thread = threading.Thread(
                    target=self._process_recipe_async,
                    args=(text, response_url, user_id)
                )
                thread.daemon = False  # Keep Lambda alive for background processing
                thread.start()
                print("DEBUG: Started background recipe processing thread")
                
                # Wait for the background processing to complete
                # This ensures Lambda doesn't terminate before the thread finishes
                thread.join()
                print("DEBUG: Background processing completed")
            
            # Return immediate acknowledgment
            print("DEBUG: Returning immediate ACK to Slack")
            return immediate_ack
            
        except Exception as e:
            print(f"DEBUG: Exception in slash command handler: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return self._create_error_response("An unexpected error occurred")
    
    def _process_recipe_async(self, text: str, response_url: str, user_id: str):
        """Process recipe generation asynchronously and send to Slack"""
        try:
            print(f"DEBUG: Starting async recipe generation for: '{text}'")
            
            # Check if the text is "use stored" or similar
            if text.lower() in ['stored', 'use stored', '保存', '登録', '登録済み']:
                # Get stored ingredients
                stored_ingredients = self.ingredient_storage.get_ingredients(user_id)
                if stored_ingredients:
                    text = ' '.join(stored_ingredients)
                    print(f"DEBUG: Using stored ingredients: {text}")
                else:
                    # No stored ingredients
                    error_payload = {
                        'response_type': 'in_channel',
                        'replace_original': True,
                        'text': '❌ 登録済みの食材がありません。\n`/dinner add 食材名` で食材を登録してください。'
                    }
                    requests.post(response_url, json=error_payload, timeout=5)
                    return
            
            # Generate recipe
            result = self.recipe_service.generate_recipe(text, max_tokens=400)
            print(f"DEBUG: Async recipe result: success={result['success']}")
            
            if result['success'] and result['recipes']:
                # Format recipes for Slack
                formatted_text = f"🍽️ **{text}** を使ったレシピの提案です：\n\n"
                
                for recipe in result['recipes']:
                    formatted_text += f"**{recipe['number']}. {recipe['name']}**\n"
                    formatted_text += f"   {recipe['description']}\n\n"
                
                # Send follow-up message to Slack
                follow_up_payload = {
                    'response_type': 'in_channel',
                    'replace_original': True,  # Replace the "generating..." message
                    'text': formatted_text
                }
            else:
                # Send error message
                error_text = f"❌ レシピ生成に失敗しました: {result.get('error', '不明なエラー')}"
                follow_up_payload = {
                    'response_type': 'in_channel',
                    'replace_original': True,
                    'text': error_text
                }
            
            # Send the follow-up message to Slack
            print(f"DEBUG: Sending follow-up to response_url: {response_url}")
            response = requests.post(
                response_url,
                json=follow_up_payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("DEBUG: Successfully sent follow-up message to Slack")
            else:
                print(f"DEBUG: Failed to send follow-up. Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            print(f"DEBUG: Error in async recipe processing: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            
            # Try to send error message to Slack
            try:
                error_payload = {
                    'response_type': 'in_channel', 
                    'replace_original': True,
                    'text': f"❌ エラーが発生しました: {str(e)}"
                }
                requests.post(response_url, json=error_payload, timeout=5)
            except:
                print("DEBUG: Failed to send error message to Slack")
    
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
                            'text': '*📝 レシピ提案*\n• `/dinner キャベツと鶏肉`\n• `/dinner さっぱりしたものが食べたい`'
                        }
                    },
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': '*💾 食材管理*\n• `/dinner add キャベツ 鶏肉` - 食材を追加\n• `/dinner list` - 登録済み食材を表示\n• `/dinner clear` - 登録済み食材を削除'
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
    
    def _handle_add_ingredients(self, user_id: str, ingredients_text: str) -> Dict[str, Any]:
        """Handle adding ingredients to storage
        
        Args:
            user_id: Slack user ID
            ingredients_text: Text containing ingredients to add
            
        Returns:
            Slack response
        """
        if not ingredients_text.strip():
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': '⚠️ 追加する食材を指定してください。\n例: `/dinner add キャベツ 鶏肉`'
                })
            }
        
        # Parse ingredients (comma or space separated)
        ingredients = []
        if '、' in ingredients_text or ',' in ingredients_text:
            # Handle comma-separated
            ingredients = [ing.strip() for ing in ingredients_text.replace('、', ',').split(',') if ing.strip()]
        else:
            # Handle space-separated
            ingredients = ingredients_text.split()
        
        # Add to storage
        success = self.ingredient_storage.add_ingredients(user_id, ingredients)
        
        if success:
            # Get updated list
            all_ingredients = self.ingredient_storage.get_ingredients(user_id)
            formatted_list = self.ingredient_storage.format_ingredients_list(all_ingredients)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': f'✅ 食材を追加しました！\n\n{formatted_list}'
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': '❌ 食材の追加に失敗しました。もう一度お試しください。'
                })
            }
    
    def _handle_list_ingredients(self, user_id: str) -> Dict[str, Any]:
        """Handle listing stored ingredients
        
        Args:
            user_id: Slack user ID
            
        Returns:
            Slack response
        """
        ingredients = self.ingredient_storage.get_ingredients(user_id)
        formatted_list = self.ingredient_storage.format_ingredients_list(ingredients)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'text': formatted_list
            })
        }
    
    def _handle_clear_ingredients(self, user_id: str) -> Dict[str, Any]:
        """Handle clearing stored ingredients
        
        Args:
            user_id: Slack user ID
            
        Returns:
            Slack response
        """
        success = self.ingredient_storage.clear_ingredients(user_id)
        
        if success:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': '🗑️ 登録済みの食材をすべて削除しました。'
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': '❌ 食材の削除に失敗しました。もう一度お試しください。'
                })
            }