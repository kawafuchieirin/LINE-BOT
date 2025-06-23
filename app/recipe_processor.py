"""
重い処理用レシピ生成Lambda関数
Bedrock通信、レシピ生成、結果送信を担当
"""
import json
import os
import boto3
import requests
from datetime import datetime
from core.recipe_service import create_recipe_service
from utils.logger import setup_logger

# AWS clients
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """
    レシピ生成処理のメイン関数
    """
    logger = setup_logger()
    
    try:
        logger.info(f"Recipe processor started: {event}")
        
        # イベントデータの取得
        text = event.get('text', '').strip()
        user_id = event.get('user_id', '')
        channel_id = event.get('channel_id', '')
        response_url = event.get('response_url', '')
        source = event.get('source', 'unknown')
        
        if not text:
            logger.warning("No text provided in event")
            return {'statusCode': 400, 'body': 'No text provided'}
        
        # レシピサービスを作成
        recipe_service = create_recipe_service()
        
        # レシピ生成
        logger.info(f"Generating recipe for: {text}")
        recipe_result = recipe_service.generate_recipe(text)
        
        if not recipe_result or not recipe_result.get('success'):
            error_msg = recipe_result.get('error', 'Unknown error') if recipe_result else 'Failed to generate recipe'
            logger.error(f"Recipe generation failed: {error_msg}")
            
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
            # LINE用の処理は後で実装
            logger.info("LINE response not implemented yet")
        
        logger.info("Recipe processing completed successfully")
        return {'statusCode': 200, 'body': 'Recipe sent successfully'}
        
    except Exception as e:
        logger.error(f"Error in recipe processor: {e}")
        
        # エラー時のフォールバック応答
        if source == 'slack_slash' and response_url:
            send_slack_error_response(response_url, str(e))
        elif source == 'slack_event' and channel_id:
            send_slack_message(channel_id, "❌ エラーが発生しました。しばらく待ってから再試行してください。")
        
        return {'statusCode': 500, 'body': f'Error: {e}'}

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
    
    # レシピが長い場合は分割
    if len(recipe_text) > 2000:
        # 材料と作り方を分離して表示
        parts = recipe_text.split('\n\n')
        blocks = [blocks[0], blocks[1]]  # ヘッダー部分のみ保持
        
        for i, part in enumerate(parts):
            if part.strip():
                blocks.append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': part.strip()
                    }
                })
    
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