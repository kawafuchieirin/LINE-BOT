"""
ローカルテスト用スクリプト
Lambda関数をローカルで動作確認するために使用
"""

import json
import os
import sys
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.handler import lambda_handler
from app.core.recipe_service import create_recipe_service
from app.recipe_parser import parse_recipe_text, extract_ingredients

# .envファイルから環境変数を読み込み
load_dotenv()


def test_recipe_generation():
    """レシピ生成機能のテスト（食材ベース）"""
    print("=== レシピ生成テスト（食材ベース） ===")
    
    recipe_service = create_recipe_service()
    
    test_ingredients = [
        "キャベツと鶏むね肉",
        "豚肉、にんじん、玉ねぎ",
        "卵とトマトとベーコン",
        "白菜と豆腐が残ってる"
    ]
    
    for ingredients in test_ingredients:
        print(f"\n食材: {ingredients}")
        print("-" * 50)
        
        # 食材抽出のテスト
        extracted = extract_ingredients(ingredients)
        print(f"抽出された食材: {extracted}")
        
        # レシピ生成のテスト（実際のAWS Bedrockへの接続が必要）
        try:
            result = recipe_service.generate_recipe_suggestions(ingredients, "test")
            if result['success']:
                print(f"入力タイプ: {result['input_type']}")
                print(f"\n解析されたレシピ数: {len(result['recipes'])}")
                for recipe in result['recipes']:
                    print(f"{recipe['number']}. {recipe['name']}")
                    print(f"   {recipe['description']}")
            else:
                print(f"エラー: {result['error']}")
        except Exception as e:
            print(f"エラー: {e}")


def test_mood_generation():
    """レシピ生成機能のテスト（気分ベース）"""
    print("\n=== レシピ生成テスト（気分ベース） ===")
    
    recipe_service = create_recipe_service()
    
    test_moods = [
        "さっぱりしたものが食べたい",
        "夏バテで食欲ないんだけど...",
        "ガッツリ系でスタミナつくもの",
        "こってり濃厚な気分",
        "ヘルシーで軽めがいい"
    ]
    
    for mood in test_moods:
        print(f"\n気分: {mood}")
        print("-" * 50)
        
        # レシピ生成のテスト（実際のAWS Bedrockへの接続が必要）
        try:
            result = recipe_service.generate_recipe_suggestions(mood, "test")
            if result['success']:
                print(f"入力タイプ: {result['input_type']}")
                print(f"\n解析されたレシピ数: {len(result['recipes'])}")
                for recipe in result['recipes']:
                    print(f"{recipe['number']}. {recipe['name']}")
                    print(f"   {recipe['description']}")
            else:
                print(f"エラー: {result['error']}")
        except Exception as e:
            print(f"エラー: {e}")


def test_webhook_handler():
    """Webhookハンドラーのテスト"""
    print("\n=== Webhookハンドラーテスト ===")
    
    # LINE Webhookイベントのモック
    test_event = {
        "body": json.dumps({
            "events": [{
                "type": "message",
                "replyToken": "test_reply_token",
                "message": {
                    "type": "text",
                    "text": "キャベツと鶏むね肉"
                }
            }]
        }),
        "headers": {
            "x-line-signature": "test_signature"  # 実際のテストでは正しい署名が必要
        }
    }
    
    # Lambda関数の呼び出し
    response = lambda_handler(test_event, None)
    print(f"レスポンス: {json.dumps(response, ensure_ascii=False, indent=2)}")


def test_parser():
    """レシピパーサーのテスト"""
    print("\n=== レシピパーサーテスト ===")
    
    test_texts = [
        """🍽️ メニュー提案

1. 鶏むね肉とキャベツの味噌炒め
   - 鶏むね肉を一口大に切り、キャベツと一緒に味噌ダレで炒める簡単料理

2. 蒸し鶏とキャベツのポン酢和え
   - 鶏むね肉を蒸して、千切りキャベツと和えてさっぱりといただく一品""",
        
        """以下のメニューがおすすめです：

1．豚肉と野菜の甘酢炒め
－ 豚肉、にんじん、玉ねぎを甘酢ダレで炒めた中華風の一品

2．ポークカレー
－ 定番のカレーライス。野菜たっぷりで栄養満点"""
    ]
    
    for text in test_texts:
        print(f"\n入力テキスト:\n{text}")
        print("-" * 50)
        recipes = parse_recipe_text(text)
        print(f"解析結果: {len(recipes)}個のレシピ")
        for recipe in recipes:
            print(f"- {recipe['name']}: {recipe['description']}")


def test_lambda_event():
    """実際のLambdaイベント形式でのテスト"""
    print("\n=== Lambda イベント形式テスト ===")
    
    # API Gateway経由のイベント形式（食材ベース）
    api_gateway_event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "POST",
        "headers": {
            "x-line-signature": "test_signature",
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "events": [{
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {
                    "userId": "test_user_id",
                    "type": "user"
                },
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "トマトとチーズとバジル"
                }
            }]
        }),
        "isBase64Encoded": False
    }
    
    try:
        response = lambda_handler(api_gateway_event, None)
        print(f"API Gateway形式のレスポンス（食材ベース）: {json.dumps(response, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"エラー: {e}")
    
    # API Gateway経由のイベント形式（気分ベース）
    mood_event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "POST",
        "headers": {
            "x-line-signature": "test_signature",
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "events": [{
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {
                    "userId": "test_user_id",
                    "type": "user"
                },
                "message": {
                    "type": "text",
                    "id": "test_message_id",
                    "text": "さっぱりしたものが食べたい"
                }
            }]
        }),
        "isBase64Encoded": False
    }
    
    try:
        response = lambda_handler(mood_event, None)
        print(f"\nAPI Gateway形式のレスポンス（気分ベース）: {json.dumps(response, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"エラー: {e}")


def test_slack_event():
    """Slackイベント形式でのテスト"""
    print("\n=== Slack イベント形式テスト ===")
    
    # Slackスラッシュコマンドのイベント形式
    slash_command_event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "POST",
        "headers": {
            "x-slack-signature": "v0=test_signature",
            "x-slack-request-timestamp": str(int(time.time())),
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "body": "token=test_token&team_id=T1234&team_domain=test&channel_id=C1234&channel_name=test&user_id=U1234&user_name=testuser&command=%2Fdinner&text=%E3%82%AD%E3%83%A3%E3%83%99%E3%83%84%E3%81%A8%E5%8D%B5&response_url=https%3A%2F%2Fhooks.slack.com%2Fcommands%2Ftest",
        "isBase64Encoded": False
    }
    
    try:
        response = lambda_handler(slash_command_event, None)
        print(f"Slackスラッシュコマンドのレスポンス: {json.dumps(response, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"エラー: {e}")
    
    # Slack app_mentionイベントの形式
    mention_event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "POST",
        "headers": {
            "x-slack-signature": "v0=test_signature",
            "x-slack-request-timestamp": str(int(time.time())),
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "token": "test_token",
            "team_id": "T1234",
            "type": "event_callback",
            "event": {
                "type": "app_mention",
                "user": "U1234",
                "text": "<@U5678> さっぱりしたものが食べたい",
                "ts": "1234567890.123456",
                "channel": "C1234",
                "event_ts": "1234567890.123456"
            }
        }),
        "isBase64Encoded": False
    }
    
    try:
        response = lambda_handler(mention_event, None)
        print(f"\nSlack mentionイベントのレスポンス: {json.dumps(response, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    # 環境変数のチェック
    print("=== 環境変数チェック ===")
    required_vars = ["LINE_CHANNEL_ACCESS_TOKEN", "LINE_CHANNEL_SECRET", "AWS_REGION"]
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var}: 設定済み")
        else:
            print(f"✗ {var}: 未設定")
    
    print("\n")
    
    # 各種テストの実行
    test_parser()  # パーサーは外部APIに依存しないため最初にテスト
    
    # 以下のテストはAWS/LINE APIの認証情報が必要
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        test_recipe_generation()
        test_mood_generation()
    else:
        print("\nAWS認証情報が設定されていないため、レシピ生成テストをスキップします")
    
    # Lambda イベント形式のテスト
    test_lambda_event()
    
    # Slack イベントのテスト
    test_slack_event()
    
    # 実際のLINE署名が必要なため、通常はコメントアウト
    # test_webhook_handler()