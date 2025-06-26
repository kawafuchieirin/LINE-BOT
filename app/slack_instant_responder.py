"""
Slack Instant Responder - Immediate ACK within 3 seconds for Slack commands
"""
import json
import os
import boto3
from typing import Dict, Any
from urllib.parse import parse_qs

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
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'response_type': 'ephemeral',
                    'text': '使用方法: `/dinner キャベツと鶏肉` または `/dinner さっぱりしたものが食べたい`'
                })
            }
        
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