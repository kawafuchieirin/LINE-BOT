"""
Bedrockアクセステスト用のデバッグ版
"""
import json
import os
import boto3
import requests
from datetime import datetime

def lambda_handler(event, context):
    """
    Bedrockアクセステスト
    """
    try:
        print(f"Debug processor started: {event}")
        
        # 簡単なテスト応答を送信
        text = event.get('text', '').strip()
        response_url = event.get('response_url', '')
        source = event.get('source', 'unknown')
        
        # Bedrockを使わずに固定レスポンスでテスト
        test_recipe = f"""🍽️ テストレシピ for {text}

1. 簡単チキンキャベツ炒め
   - {text}をフライパンで炒めて塩コショウで味付け

2. キャベツと鶏肉の煮物
   - 醤油と砂糖で煮込んで和風の味付けに

🤖 これはBedrockを使わないテストレスポンスです"""
        
        # Slackに送信
        if source == 'slack_slash' and response_url:
            send_slack_response(response_url, test_recipe, text)
        
        print("Test response sent successfully")
        return {'statusCode': 200, 'body': 'Test response sent'}
        
    except Exception as e:
        print(f"Error in debug processor: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {'statusCode': 500, 'body': f'Error: {e}'}

def send_slack_response(response_url, recipe_text, original_text):
    """
    Slackにテストレスポンスを送信
    """
    try:
        blocks = [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'*🔍 リクエスト:* {original_text}'
                }
            },
            {
                'type': 'divider'
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'*🍽️ テストレシピ:*\n{recipe_text}'
                }
            },
            {
                'type': 'context',
                'elements': [
                    {
                        'type': 'mrkdwn',
                        'text': f'🤖 テスト時刻: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                    }
                ]
            }
        ]
        
        payload = {
            'text': '🍽️ テストレスポンス',
            'blocks': blocks,
            'response_type': 'in_channel'
        }
        
        response = requests.post(
            response_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Failed to send response: {response.status_code} - {response.text}")
        else:
            print("Test response sent successfully")
            
    except Exception as e:
        print(f"Error sending test response: {e}")