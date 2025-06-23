"""
Slack即座レスポンス用Lambda関数
3秒ルール対応 - 即座にACKを返し、重い処理は別Lambdaに委譲
"""
import json
import os
import hashlib
import hmac
import time
import boto3
from urllib.parse import parse_qs

# Lambda client for async invocation
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """
    Slack slash command用の即座レスポンス関数
    """
    try:
        print(f"Received event: {json.dumps(event, default=str)}")
        
        # リクエストの解析
        body = event.get('body', '')
        headers = event.get('headers', {})
        is_base64 = event.get('isBase64Encoded', False)
        
        print(f"Raw body: {body}")
        print(f"Is base64 encoded: {is_base64}")
        print(f"Headers: {headers}")
        
        # Base64デコードが必要な場合
        if is_base64 and body:
            import base64
            body = base64.b64decode(body).decode('utf-8')
            print(f"Decoded body: {body}")
        
        # Slack署名検証（開発時は一時的にスキップ）
        # if not verify_slack_signature(body, headers):
        #     return {
        #         'statusCode': 401,
        #         'body': json.dumps({'error': 'Invalid signature'})
        #     }
        
        # リクエストボディの解析
        if body:
            parsed_body = parse_qs(body)
            print(f"Parsed body: {parsed_body}")
        else:
            print("Empty body received")
            return {
                'statusCode': 200,
                'body': 'OK'
            }
        
        # スラッシュコマンドかどうか確認
        if 'command' in parsed_body and parsed_body['command'][0] == '/dinner':
            print("Handling dinner command")
            return handle_dinner_command(parsed_body)
        
        # その他のSlackイベント
        print("Handling slack event")
        return handle_slack_event(json.loads(body) if body.startswith('{') else parsed_body)
        
    except Exception as e:
        print(f"Error in slack_responder: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def verify_slack_signature(body, headers):
    """
    Slack署名を検証
    """
    slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET', '')
    if not slack_signing_secret:
        print("Warning: SLACK_SIGNING_SECRET not configured")
        return True  # 開発時はスキップ
    
    timestamp = headers.get('X-Slack-Request-Timestamp', headers.get('x-slack-request-timestamp', ''))
    signature = headers.get('X-Slack-Signature', headers.get('x-slack-signature', ''))
    
    if not timestamp or not signature:
        return False
    
    # タイムスタンプ検証（5分以内）
    if abs(time.time() - int(timestamp)) > 300:
        return False
    
    # 署名検証
    sig_basestring = f"v0:{timestamp}:{body}"
    my_signature = 'v0=' + hmac.new(
        slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, signature)

def handle_dinner_command(parsed_body):
    """
    /dinner スラッシュコマンドの処理
    即座にACKを返し、重い処理は別Lambdaに委譲
    """
    try:
        # ユーザー入力の取得
        text = parsed_body.get('text', [''])[0].strip()
        user_id = parsed_body.get('user_id', [''])[0]
        channel_id = parsed_body.get('channel_id', [''])[0]
        response_url = parsed_body.get('response_url', [''])[0]
        
        if not text:
            # 即座にヘルプメッセージを返す
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'text': '🍽️ 晩御飯提案BOTです！',
                    'blocks': [
                        {
                            'type': 'section',
                            'text': {
                                'type': 'mrkdwn',
                                'text': '*使い方:*\n• `/dinner 鶏肉とキャベツ` - 材料から提案\n• `/dinner さっぱりしたものが食べたい` - 気分から提案'
                            }
                        }
                    ]
                })
            }
        
        # 即座に「処理中」レスポンスを返す
        immediate_response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'text': '🔍 レシピを考えています... 少々お待ちください',
                'response_type': 'in_channel'
            })
        }
        
        # 重い処理を別Lambdaに非同期で委譲
        invoke_recipe_processor({
            'text': text,
            'user_id': user_id,
            'channel_id': channel_id,
            'response_url': response_url,
            'source': 'slack_slash'
        })
        
        return immediate_response
        
    except Exception as e:
        print(f"Error in handle_dinner_command: {e}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'text': '❌ エラーが発生しました。しばらく待ってから再試行してください。'
            })
        }

def handle_slack_event(event_data):
    """
    Slackイベント（メンション、DM等）の処理
    """
    try:
        # URL検証チャレンジ
        if isinstance(event_data, dict) and 'challenge' in event_data:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/plain'},
                'body': event_data['challenge']
            }
        
        # イベント処理
        if isinstance(event_data, dict) and 'event' in event_data:
            event_info = event_data['event']
            
            # BOT自身のメッセージは無視
            if event_info.get('bot_id'):
                return {'statusCode': 200, 'body': 'OK'}
            
            # メンションまたはDMの場合
            if (event_info.get('type') == 'app_mention' or 
                event_info.get('channel_type') == 'im'):
                
                text = event_info.get('text', '').strip()
                user_id = event_info.get('user', '')
                channel_id = event_info.get('channel', '')
                
                # @mentionを削除
                if text.startswith('<@'):
                    text = text.split('>', 1)[1].strip() if '>' in text else text
                
                if text:
                    # 重い処理を別Lambdaに委譲
                    invoke_recipe_processor({
                        'text': text,
                        'user_id': user_id,
                        'channel_id': channel_id,
                        'source': 'slack_event'
                    })
        
        return {'statusCode': 200, 'body': 'OK'}
        
    except Exception as e:
        print(f"Error in handle_slack_event: {e}")
        return {'statusCode': 200, 'body': 'OK'}

def invoke_recipe_processor(payload):
    """
    レシピ処理Lambda関数を非同期で起動
    """
    try:
        function_name = os.environ.get('RECIPE_PROCESSOR_FUNCTION_NAME', 'dinner-suggestion-bot-recipe-processor')
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # 非同期起動
            Payload=json.dumps(payload)
        )
        
        print(f"Recipe processor invoked successfully: {response.get('StatusCode')}")
        
    except Exception as e:
        print(f"Error invoking recipe processor: {e}")