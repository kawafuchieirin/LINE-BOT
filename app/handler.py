import os
import json
import logging
from typing import Dict, Any

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from .recipe_parser import parse_recipe_text, extract_ingredients
from .flex_message import create_recipe_flex_message
from .bedrock_client import create_bedrock_client
from .line_message import create_error_message

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
bedrock_client = create_bedrock_client(AWS_REGION)


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
        recipe_suggestion = bedrock_client.generate_recipe_suggestion(ingredients)
        
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
            create_error_message("general")
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