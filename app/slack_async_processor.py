"""
Slack Async Processor - Handle recipe generation and send results back to Slack
This function is invoked asynchronously by the instant responder
"""
import json
import requests
import sys
import os
from typing import Dict, Any

# Add app directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from recipe_service import RecipeService

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process recipe generation asynchronously and send result to Slack
    This function has no time constraints since it's invoked asynchronously
    """
    print(f"DEBUG: Slack async processor invoked with event: {json.dumps(event)}")
    
    try:
        # Extract data from the event
        text = event.get('text', '')
        response_url = event.get('response_url', '')
        user_id = event.get('user_id', 'unknown')
        channel_id = event.get('channel_id', 'unknown')
        
        print(f"DEBUG: Processing recipe for text='{text}', user={user_id}, channel={channel_id}")
        
        if not text.strip():
            print("DEBUG: Empty text provided")
            return {'statusCode': 400, 'body': 'No text provided'}
        
        if not response_url:
            print("DEBUG: No response_url provided")
            return {'statusCode': 400, 'body': 'No response_url provided'}
        
        # Initialize recipe service
        try:
            recipe_service = RecipeService()
            print("DEBUG: Recipe service initialized successfully")
        except Exception as e:
            print(f"DEBUG: Failed to initialize recipe service: {str(e)}")
            # Send error message to Slack
            error_payload = {
                'response_type': 'in_channel',
                'replace_original': True,
                'text': f"❌ サービス初期化エラー: {str(e)}"
            }
            try:
                requests.post(response_url, json=error_payload, timeout=10)
            except:
                pass
            return {'statusCode': 500, 'body': 'Service initialization failed'}
        
        # Generate recipe
        print(f"DEBUG: Starting recipe generation for: '{text}'")
        result = recipe_service.generate_recipe(text, max_tokens=400)
        print(f"DEBUG: Recipe generation result: success={result['success']}")
        
        if result['success'] and result['recipes']:
            # Format recipes for Slack using Block Kit
            blocks = [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': '🍽️ レシピ提案完了！'
                    }
                },
                {
                    'type': 'context',
                    'elements': [{
                        'type': 'mrkdwn',
                        'text': f'_{result["input_type"]}_ に基づく提案'
                    }]
                }
            ]
            
            # Add each recipe as a section
            for recipe in result['recipes']:
                blocks.append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f"*{recipe['number']}. {recipe['name']}*\n{recipe['description']}"
                    }
                })
            
            # Add divider at the end
            blocks.append({'type': 'divider'})
            
            # Prepare the payload
            success_payload = {
                'response_type': 'in_channel',
                'replace_original': True,
                'text': f'🍽️ **{text}** のレシピ提案完了！',
                'blocks': blocks
            }
        else:
            # Handle recipe generation failure
            error_text = f"❌ レシピ生成に失敗しました: {result.get('error', '不明なエラー')}"
            success_payload = {
                'response_type': 'in_channel',
                'replace_original': True,
                'text': error_text
            }
        
        # Send the result back to Slack
        print(f"DEBUG: Sending result to Slack response_url: {response_url}")
        response = requests.post(
            response_url,
            json=success_payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        if response.status_code == 200:
            print("DEBUG: Successfully sent result to Slack")
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'success', 'message': 'Recipe sent to Slack'})
            }
        else:
            print(f"DEBUG: Failed to send to Slack. Status: {response.status_code}, Response: {response.text}")
            return {
                'statusCode': 500,
                'body': json.dumps({'status': 'error', 'message': f'Slack API error: {response.status_code}'})
            }
            
    except Exception as e:
        print(f"DEBUG: Error in async processor: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        
        # Try to send error message to Slack if response_url is available
        if 'response_url' in event and event['response_url']:
            try:
                error_payload = {
                    'response_type': 'in_channel',
                    'replace_original': True,
                    'text': f"❌ エラーが発生しました: {str(e)}"
                }
                requests.post(event['response_url'], json=error_payload, timeout=5)
                print("DEBUG: Sent error message to Slack")
            except:
                print("DEBUG: Failed to send error message to Slack")
        
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }