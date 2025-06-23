"""
単体動作するレシピ生成Lambda関数
Bedrock通信、レシピ生成、結果送信を担当
"""
import json
import os
import boto3
import requests
from datetime import datetime

def lambda_handler(event, context):
    """
    レシピ生成処理のメイン関数
    """
    try:
        print(f"Recipe processor started: {event}")
        
        # イベントデータの取得
        text = event.get('text', '').strip()
        user_id = event.get('user_id', '')
        channel_id = event.get('channel_id', '')
        response_url = event.get('response_url', '')
        source = event.get('source', 'unknown')
        
        if not text:
            print("No text provided in event")
            return {'statusCode': 400, 'body': 'No text provided'}
        
        # レシピ生成
        print(f"Generating recipe for: {text}")
        recipe_result = generate_recipe_with_bedrock(text)
        
        if not recipe_result or not recipe_result.get('success'):
            error_msg = recipe_result.get('error', 'Unknown error') if recipe_result else 'Failed to generate recipe'
            print(f"Recipe generation failed: {error_msg}")
            
            if source == 'slack_slash' and response_url:
                send_slack_error_response(response_url, error_msg)
            elif source == 'slack_event' and channel_id:
                send_slack_message(channel_id, f"❌ レシピ生成に失敗しました: {error_msg}")
            
            return {'statusCode': 500, 'body': f'Recipe generation failed: {error_msg}'}
        
        # 成功時のレスポンス送信
        recipe_text = recipe_result.get('recipe', 'レシピが見つかりませんでした')
        
        if source == 'slack_slash' and response_url:
            send_slack_slash_response(response_url, recipe_text, text)
        elif source == 'slack_event' and channel_id:
            send_slack_message(channel_id, format_recipe_for_slack(recipe_text, text))
        elif source == 'line' and channel_id:
            print("LINE response not implemented yet")
        
        print("Recipe processing completed successfully")
        return {'statusCode': 200, 'body': 'Recipe sent successfully'}
        
    except Exception as e:
        print(f"Error in recipe processor: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # エラー時のフォールバック応答
        if source == 'slack_slash' and response_url:
            send_slack_error_response(response_url, str(e))
        elif source == 'slack_event' and channel_id:
            send_slack_message(channel_id, "❌ エラーが発生しました。しばらく待ってから再試行してください。")
        
        return {'statusCode': 500, 'body': f'Error: {e}'}

def generate_recipe_with_bedrock(user_input):
    """
    Bedrockを使ってレシピを生成
    """
    try:
        # Bedrockクライアント作成
        bedrock_region = os.environ.get('BEDROCK_REGION', 'ap-northeast-1')
        bedrock_client = boto3.client('bedrock-runtime', region_name=bedrock_region)
        
        # プロンプト作成
        prompt = f"""あなたは優秀な料理アドバイザーです。
以下の内容を基に、美味しい晩御飯のメニューを2-3個提案してください。

リクエスト: {user_input}

提案フォーマット:
🍽️ メニュー提案

1. [メニュー名]
   - 簡単な説明

2. [メニュー名] 
   - 簡単な説明

必要に応じて3つ目のメニューも提案してください。
メニュー名は具体的で、作りたくなるような名前にしてください。
説明は1-2文で、調理方法の特徴や味の特徴を含めてください。"""
        
        # Bedrock API呼び出し
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "temperature": 0.7,
            "top_p": 0.95
        }
        
        # Use Claude 3.5 Sonnet (confirmed available) with fallbacks
        model_ids = [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",     # Claude 3.5 Sonnet v2 (latest)
            "anthropic.claude-3-5-sonnet-20240620-v1:0",     # Claude 3.5 Sonnet v1
            "anthropic.claude-3-sonnet-20240229-v1:0",       # Claude 3 Sonnet
            "anthropic.claude-3-haiku-20240307-v1:0",        # Claude 3 Haiku
            "anthropic.claude-instant-v1",                   # Claude Instant (fallback)
        ]
        
        for model_id in model_ids:
            try:
                print(f"Trying model: {model_id}")
                response = bedrock_client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body)
                )
                print(f"Successfully used model: {model_id}")
                break
            except Exception as model_error:
                print(f"Failed with model {model_id}: {model_error}")
                if model_id == model_ids[-1]:  # Last model
                    raise model_error
                continue
        
        # レスポンス解析
        response_body = json.loads(response['body'].read())
        recipe_text = response_body['content'][0]['text']
        
        print(f"Generated recipe: {recipe_text[:200]}...")
        
        return {
            'success': True,
            'recipe': recipe_text,
            'error': None
        }
        
    except Exception as e:
        print(f"Error generating recipe with Bedrock: {e}")
        return {
            'success': False,
            'recipe': None,
            'error': str(e)
        }

def send_slack_slash_response(response_url, recipe_text, original_text):
    """
    Slackスラッシュコマンドのレスポンスを送信
    """
    try:
        blocks = create_recipe_blocks(recipe_text, original_text)
        
        payload = {
            'text': '🍽️ おすすめレシピです！',
            'blocks': blocks,
            'response_type': 'in_channel'
        }
        
        response = requests.post(
            response_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Failed to send slash response: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error sending slack slash response: {e}")

def send_slack_message(channel_id, text):
    """
    Slack Web APIを使用してメッセージを送信
    """
    try:
        bot_token = os.environ.get('SLACK_BOT_TOKEN')
        if not bot_token:
            print("SLACK_BOT_TOKEN not configured")
            return
        
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        if isinstance(text, str):
            payload = {
                'channel': channel_id,
                'text': text
            }
        else:
            payload = {
                'channel': channel_id,
                'text': '🍽️ おすすめレシピです！',
                'blocks': text
            }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to send message: {response.status_code} - {response.text}")
        else:
            result = response.json()
            if not result.get('ok'):
                print(f"Slack API error: {result.get('error')}")
                
    except Exception as e:
        print(f"Error sending slack message: {e}")

def send_slack_error_response(response_url, error_message):
    """
    エラー時のSlackレスポンスを送信
    """
    try:
        payload = {
            'text': f'❌ エラーが発生しました: {error_message}',
            'response_type': 'ephemeral'  # 本人にのみ表示
        }
        
        response = requests.post(
            response_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"Failed to send error response: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error sending slack error response: {e}")

def create_recipe_blocks(recipe_text, original_text):
    """
    Slack Block Kit形式のレシピブロックを作成
    """
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
                'text': f'*🍽️ おすすめレシピ:*\n{recipe_text}'
            }
        }
    ]
    
    # 時刻を追加
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    blocks.append({
        'type': 'context',
        'elements': [
            {
                'type': 'mrkdwn',
                'text': f'🤖 生成時刻: {current_time}'
            }
        ]
    })
    
    return blocks

def format_recipe_for_slack(recipe_text, original_text):
    """
    Slackイベント用のシンプルなレシピフォーマット
    """
    return create_recipe_blocks(recipe_text, original_text)