"""
ローカルテスト用スクリプト
Lambda関数をローカルで動作確認するために使用
"""

import json
import os
from dotenv import load_dotenv
from app import lambda_handler, generate_recipe_suggestion
from recipe_parser import parse_recipe_text, extract_ingredients

# .envファイルから環境変数を読み込み
load_dotenv()


def test_recipe_generation():
    """レシピ生成機能のテスト"""
    print("=== レシピ生成テスト ===")
    
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
            suggestion = generate_recipe_suggestion(extracted)
            print(f"生成されたレシピ:\n{suggestion}")
            
            # レシピ解析のテスト
            recipes = parse_recipe_text(suggestion)
            print(f"\n解析されたレシピ数: {len(recipes)}")
            for i, recipe in enumerate(recipes):
                print(f"{i+1}. {recipe['name']}")
                print(f"   {recipe['description']}")
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
    else:
        print("\nAWS認証情報が設定されていないため、レシピ生成テストをスキップします")
    
    # test_webhook_handler()  # 署名検証があるため、実際のLINE署名が必要