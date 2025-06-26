"""
Slack Instant Responder - Immediate ACK within 3 seconds for Slack commands
"""
import json
import os
import sys
import boto3
from typing import Dict, Any
from urllib.parse import parse_qs

# Add app directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingredient_storage import IngredientStorage

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle Slack slash command with immediate ACK and invoke async processor
    This function MUST respond within 3 seconds
    """
    print(f"DEBUG: Slack instant responder invoked")
    
    try:
        # Parse the event body
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        # Parse slash command data
        command_data = parse_qs(body)
        text = command_data.get('text', [''])[0]
        response_url = command_data.get('response_url', [''])[0]
        user_id = command_data.get('user_id', ['unknown'])[0]
        channel_id = command_data.get('channel_id', ['unknown'])[0]
        
        print(f"DEBUG: Parsed command - text='{text}', response_url present={bool(response_url)}")
        
        # Validate input
        if not text.strip():
            return _create_help_response()
        
        # Parse the command for ingredient management
        parts = text.split(maxsplit=1)
        sub_command = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        # Handle ingredient storage commands immediately (no async processing needed)
        if sub_command == 'add':
            return _handle_add_ingredients(user_id, args)
        elif sub_command == 'list':
            return _handle_list_ingredients(user_id)
        elif sub_command == 'clear':
            return _handle_clear_ingredients(user_id)
        elif sub_command in ['stored', 'use', '登録', '登録済み']:
            return _handle_use_stored_ingredients(user_id, response_url)
        
        # Invoke the async processor Lambda function
        if response_url:
            lambda_client = boto3.client('lambda')
            
            # Payload for the async processor
            async_payload = {
                'text': text,
                'response_url': response_url,
                'user_id': user_id,
                'channel_id': channel_id
            }
            
            # Invoke async processor (fire-and-forget)
            try:
                async_function_name = os.environ.get('ASYNC_PROCESSOR_FUNCTION_NAME', 'dinner-suggestion-bot-slack-async-processor')
                lambda_client.invoke(
                    FunctionName=async_function_name,
                    InvocationType='Event',  # Asynchronous invocation
                    Payload=json.dumps(async_payload)
                )
                print(f"DEBUG: Successfully invoked async processor")
            except Exception as e:
                print(f"DEBUG: Failed to invoke async processor: {str(e)}")
        
        # IMMEDIATE response (within 3 seconds)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'text': '🍽️ レシピを生成中です... 少々お待ちください！'
            })
        }
        
    except Exception as e:
        print(f"DEBUG: Error in instant responder: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'❌ エラーが発生しました: {str(e)}'
            })
        }

def _create_help_response() -> Dict[str, Any]:
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
                        'text': '*📝 レシピ提案*\n• `/dinner キャベツと鶏肉` - 冷蔵庫の食材でレシピ提案\n• `/dinner さっぱりしたものが食べたい` - 気分でレシピ提案'
                    }
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': '*❄️ 冷蔵庫管理*\n• `/dinner add キャベツ 鶏肉` - 冷蔵庫に食材を追加\n• `/dinner list` - 冷蔵庫の食材を表示\n• `/dinner stored` - 冷蔵庫の食材でレシピ生成\n• `/dinner clear` - 冷蔵庫の食材をクリア'
                    }
                }
            ]
        })
    }

def _handle_add_ingredients(user_id: str, ingredients_text: str) -> Dict[str, Any]:
    """Handle adding ingredients to storage"""
    if not ingredients_text.strip():
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': '⚠️ 冷蔵庫に追加する食材を指定してください。\n例: `/dinner add キャベツ 鶏肉`'
            })
        }
    
    try:
        ingredient_storage = IngredientStorage()
        
        # Parse ingredients (comma or space separated)
        ingredients = []
        if '、' in ingredients_text or ',' in ingredients_text:
            # Handle comma-separated
            ingredients = [ing.strip() for ing in ingredients_text.replace('、', ',').split(',') if ing.strip()]
        else:
            # Handle space-separated
            ingredients = ingredients_text.split()
        
        # Add to storage
        success = ingredient_storage.add_ingredients(user_id, ingredients)
        
        if success:
            # Get updated list
            all_ingredients = ingredient_storage.get_ingredients(user_id)
            formatted_list = ingredient_storage.format_ingredients_list(all_ingredients)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': f'✅ 冷蔵庫に食材を追加しました！\n\n{formatted_list}'
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
    
    except Exception as e:
        print(f"DEBUG: Error in _handle_add_ingredients: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'❌ エラーが発生しました: {str(e)}'
            })
        }

def _handle_list_ingredients(user_id: str) -> Dict[str, Any]:
    """Handle listing stored ingredients"""
    try:
        ingredient_storage = IngredientStorage()
        ingredients = ingredient_storage.get_ingredients(user_id)
        formatted_list = ingredient_storage.format_ingredients_list(ingredients)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'text': formatted_list
            })
        }
    
    except Exception as e:
        print(f"DEBUG: Error in _handle_list_ingredients: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'❌ エラーが発生しました: {str(e)}'
            })
        }

def _handle_clear_ingredients(user_id: str) -> Dict[str, Any]:
    """Handle clearing stored ingredients"""
    try:
        ingredient_storage = IngredientStorage()
        success = ingredient_storage.clear_ingredients(user_id)
        
        if success:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'in_channel',
                    'text': '🗑️ 冷蔵庫の食材をすべて削除しました。'
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
    
    except Exception as e:
        print(f"DEBUG: Error in _handle_clear_ingredients: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'❌ エラーが発生しました: {str(e)}'
            })
        }

def _handle_use_stored_ingredients(user_id: str, response_url: str) -> Dict[str, Any]:
    """Handle using stored ingredients for recipe generation"""
    try:
        ingredient_storage = IngredientStorage()
        stored_ingredients = ingredient_storage.get_ingredients(user_id)
        
        if not stored_ingredients:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': '❌ 冷蔵庫に食材がありません。\n`/dinner add 食材名` で冷蔵庫に食材を追加してください。'
                })
            }
        
        # If we have stored ingredients, pass them to async processor
        if response_url:
            lambda_client = boto3.client('lambda')
            
            # Create text from stored ingredients
            ingredients_text = ' '.join(stored_ingredients)
            
            # Payload for the async processor
            async_payload = {
                'text': ingredients_text,
                'response_url': response_url,
                'user_id': user_id,
                'channel_id': 'stored'
            }
            
            # Invoke async processor (fire-and-forget)
            try:
                async_function_name = os.environ.get('ASYNC_PROCESSOR_FUNCTION_NAME', 'dinner-suggestion-bot-slack-async-processor')
                lambda_client.invoke(
                    FunctionName=async_function_name,
                    InvocationType='Event',  # Asynchronous invocation
                    Payload=json.dumps(async_payload)
                )
                print(f"DEBUG: Successfully invoked async processor for stored ingredients: {ingredients_text}")
            except Exception as e:
                print(f"DEBUG: Failed to invoke async processor: {str(e)}")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'response_type': 'ephemeral',
                        'text': f'❌ レシピ生成の開始に失敗しました: {str(e)}'
                    })
                }
        
        # Return immediate acknowledgment
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'in_channel',
                'text': f'🍽️ 冷蔵庫の食材（{", ".join(stored_ingredients)}）を使ったレシピを生成中です...'
            })
        }
    
    except Exception as e:
        print(f"DEBUG: Error in _handle_use_stored_ingredients: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'❌ エラーが発生しました: {str(e)}'
            })
        }