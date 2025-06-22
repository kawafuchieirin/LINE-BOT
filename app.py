import os
import json
import logging
from typing import Dict, Any

import boto3
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from recipe_parser import parse_recipe_text, extract_ingredients
from flex_message import create_recipe_flex_message

# ロガー設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数から設定を読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# LINE Bot APIとWebhookハンドラーの初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# AWS Bedrockクライアントの初期化
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=AWS_REGION
)


def generate_recipe_suggestion(ingredients: str) -> str:
    """
    AWS Bedrock (Claude 3) を使用して食材から晩御飯のメニューを提案する
    
    Args:
        ingredients: ユーザーが入力した食材
        
    Returns:
        提案されたメニューのテキスト
    """
    prompt = f"""あなたは優秀な料理アドバイザーです。
以下の食材を使って、美味しい晩御飯のメニューを2-3個提案してください。
各メニューについて、簡単な説明も付けてください。

食材: {ingredients}

提案フォーマット:
🍽️ メニュー提案

1. [メニュー名]
   - 簡単な説明

2. [メニュー名]
   - 簡単な説明
"""
    
    try:
        # Claude 3 Sonnetのモデルを使用
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        # リクエストボディの作成
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
        
        # Bedrockへのリクエスト
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        # レスポンスの解析
        response_body = json.loads(response['body'].read())
        recipe_suggestion = response_body['content'][0]['text']
        
        return recipe_suggestion
        
    except Exception as e:
        logger.error(f"Error generating recipe suggestion: {str(e)}")
        return "申し訳ございません。レシピの提案中にエラーが発生しました。もう一度お試しください。"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    LINEからのテキストメッセージを処理する
    """
    try:
        # ユーザーからのメッセージを取得
        user_message = event.message.text
        logger.info(f"Received message: {user_message}")
        
        # 食材を抽出
        ingredients = extract_ingredients(user_message)
        logger.info(f"Extracted ingredients: {ingredients}")
        
        # AWS Bedrockでレシピを生成
        recipe_suggestion = generate_recipe_suggestion(ingredients)
        
        # レシピテキストを解析して構造化
        recipes = parse_recipe_text(recipe_suggestion)
        
        # Flex Messageを使用するかテキストメッセージを使用するか判断
        use_flex = os.environ.get('USE_FLEX_MESSAGE', 'true').lower() == 'true'
        
        if use_flex and len(recipes) > 0:
            # Flex Messageで返信
            flex_message = create_recipe_flex_message(recipes)
            line_bot_api.reply_message(
                event.reply_token,
                flex_message
            )
        else:
            # 通常のテキストメッセージで返信
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=recipe_suggestion)
            )
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        logger.exception(e)  # スタックトレースもログに出力
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ございません。エラーが発生しました。\nもう一度食材を教えてください。")
        )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda のメインハンドラー関数
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # リクエストボディとヘッダーを取得
    body = event.get('body', '')
    headers = event.get('headers', {})
    
    # LINE署名の検証
    signature = headers.get('x-line-signature', '')
    
    try:
        # Webhookハンドラーでリクエストを処理
        handler.handle(body, signature)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'OK'})
        }
        
    except InvalidSignatureError:
        logger.error("Invalid signature")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid signature'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }