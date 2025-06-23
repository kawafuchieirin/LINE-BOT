"""
高品質なモックレスポンス版
Bedrockの代わりに事前定義された高品質レシピを提供
"""
import json
import os
import requests
from datetime import datetime
import random

def lambda_handler(event, context):
    """
    モックレシピ生成処理
    """
    try:
        print(f"Mock recipe processor started: {event}")
        
        # イベントデータの取得
        text = event.get('text', '').strip()
        user_id = event.get('user_id', '')
        channel_id = event.get('channel_id', '')
        response_url = event.get('response_url', '')
        source = event.get('source', 'unknown')
        
        if not text:
            print("No text provided in event")
            return {'statusCode': 400, 'body': 'No text provided'}
        
        # 高品質なモックレシピを生成
        print(f"Generating mock recipe for: {text}")
        recipe_text = generate_mock_recipe(text)
        
        # Slackに送信
        if source == 'slack_slash' and response_url:
            send_slack_slash_response(response_url, recipe_text, text)
        elif source == 'slack_event' and channel_id:
            send_slack_message(channel_id, format_recipe_for_slack(recipe_text, text))
        
        print("Mock recipe sent successfully")
        return {'statusCode': 200, 'body': 'Mock recipe sent successfully'}
        
    except Exception as e:
        print(f"Error in mock recipe processor: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # エラー時のフォールバック応答
        if source == 'slack_slash' and response_url:
            send_slack_error_response(response_url, str(e))
        elif source == 'slack_event' and channel_id:
            send_slack_message(channel_id, "❌ エラーが発生しました。しばらく待ってから再試行してください。")
        
        return {'statusCode': 500, 'body': f'Error: {e}'}

def generate_mock_recipe(user_input):
    """
    入力に基づいて高品質なモックレシピを生成
    """
    # 食材キーワードを検出
    ingredients = []
    if "鶏肉" in user_input or "チキン" in user_input:
        ingredients.append("鶏肉")
    if "キャベツ" in user_input:
        ingredients.append("キャベツ")
    if "豚肉" in user_input:
        ingredients.append("豚肉")
    if "牛肉" in user_input:
        ingredients.append("牛肉")
    if "卵" in user_input:
        ingredients.append("卵")
    if "トマト" in user_input:
        ingredients.append("トマト")
    if "玉ねぎ" in user_input or "たまねぎ" in user_input:
        ingredients.append("玉ねぎ")
    
    # 気分キーワードを検出
    mood_keywords = []
    if any(word in user_input for word in ["さっぱり", "あっさり"]):
        mood_keywords.append("さっぱり")
    if any(word in user_input for word in ["こってり", "ガッツリ", "がっつり"]):
        mood_keywords.append("こってり")
    if any(word in user_input for word in ["ヘルシー", "軽め"]):
        mood_keywords.append("ヘルシー")
    if any(word in user_input for word in ["スタミナ", "元気"]):
        mood_keywords.append("スタミナ")
    
    # レシピデータベース
    recipes = {
        "鶏肉_キャベツ": [
            {
                "name": "鶏胸肉とキャベツの中華風炒め",
                "description": "鶏胸肉を一口大に切り、片栗粉をまぶして下味をつける。キャベツはざく切りにし、強火でサッと炒めてシャキシャキ感を残す。オイスターソースと醤油で味付けし、最後にごま油で風味をプラス。"
            },
            {
                "name": "チキンとキャベツのクリーム煮",
                "description": "鶏もも肉を焼き色がつくまで炒め、キャベツと玉ねぎを加えてしんなりするまで煮る。牛乳と小麦粉でとろみをつけ、塩コショウで味を調える。優しい味わいで体が温まる一品。"
            },
            {
                "name": "鶏肉とキャベツの和風蒸し煮",
                "description": "鶏もも肉に塩を振って下味をつけ、キャベツと一緒に酒蒸しにする。だし汁と醤油、みりんで上品な和風味に仕上げ、最後に刻みネギを散らして香りをプラス。"
            }
        ],
        "さっぱり": [
            {
                "name": "鶏ささみとキャベツのレモン蒸し",
                "description": "鶏ささみを塩とレモン汁でマリネし、キャベツと一緒に蒸し上げる。ポン酢とおろし大根でさっぱりと仕上げ、大葉を添えて爽やかな風味に。"
            },
            {
                "name": "野菜たっぷり冷しゃぶサラダ",
                "description": "豚しゃぶ肉をさっと茹でて冷まし、千切りキャベツ、きゅうり、トマトと合わせる。ごまだれとポン酢を混ぜたドレッシングでさっぱりと。"
            }
        ],
        "こってり": [
            {
                "name": "鶏もも肉とキャベツのガーリックバター炒め",
                "description": "鶏もも肉を皮目からしっかり焼き、にんにくとバターで香ばしく炒める。キャベツを加えて炒め合わせ、醤油と黒胡椒で濃厚な味付けに。"
            },
            {
                "name": "豚バラとキャベツの味噌炒め",
                "description": "豚バラ肉をカリッと炒めて脂を出し、キャベツを加えてしんなりするまで炒める。味噌、砂糖、酒を合わせた甘辛だれで濃厚に味付け。"
            }
        ],
        "default": [
            {
                "name": "基本の野菜炒め",
                "description": "お好みの野菜を使って、塩コショウとしょうゆで味付けした簡単な炒め物。"
            },
            {
                "name": "シンプル煮物",
                "description": "だし汁で野菜を煮込んだ、やさしい味の煮物。"
            }
        ]
    }
    
    # 適切なレシピを選択
    selected_recipes = []
    
    if "鶏肉" in ingredients and "キャベツ" in ingredients:
        selected_recipes = recipes["鶏肉_キャベツ"]
    elif "さっぱり" in mood_keywords:
        selected_recipes = recipes["さっぱり"]
    elif "こってり" in mood_keywords:
        selected_recipes = recipes["こってり"]
    else:
        # 材料に基づいた汎用レシピ
        selected_recipes = recipes["default"]
    
    # レシピをフォーマット
    recipe_text = "🍽️ おすすめレシピ\n\n"
    for i, recipe in enumerate(selected_recipes[:3], 1):
        recipe_text += f"{i}. {recipe['name']}\n   - {recipe['description']}\n\n"
    
    recipe_text += "💡 ポイント: 材料の鮮度と火加減が美味しさの秘訣です！\n"
    recipe_text += "🤖 高品質モックレシピ（Bedrock代替版）で生成"
    
    return recipe_text

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
            'response_type': 'ephemeral'
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