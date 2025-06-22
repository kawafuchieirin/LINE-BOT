#!/usr/bin/env python3
"""
気分モードのテストスクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.bedrock_client import BedrockClient


def test_mood_detection():
    """気分ベース入力の検出テスト"""
    client = BedrockClient()
    
    # 気分ベースの入力例
    mood_inputs = [
        "さっぱりしたものが食べたい",
        "夏バテで食欲ないんだけど...",
        "ガッツリ系でスタミナつくもの",
        "こってり濃厚な気分",
        "ヘルシーで軽めがいい",
        "温まるものが食べたい",
        "疲れたから元気が出るもの"
    ]
    
    # 食材ベースの入力例
    ingredient_inputs = [
        "鶏肉とキャベツ",
        "豚肉、にんじん、玉ねぎ",
        "卵とトマトとベーコン",
        "白菜と豆腐が残ってる",
        "牛肉と大根がある"
    ]
    
    print("=== 気分モード検出テスト ===\n")
    
    print("【気分ベース入力のテスト】")
    for input_text in mood_inputs:
        is_mood = client._is_mood_based_input(input_text)
        print(f"入力: '{input_text}'")
        print(f"判定: {'気分ベース' if is_mood else '食材ベース'}")
        print()
    
    print("\n【食材ベース入力のテスト】")
    for input_text in ingredient_inputs:
        is_mood = client._is_mood_based_input(input_text)
        print(f"入力: '{input_text}'")
        print(f"判定: {'気分ベース' if is_mood else '食材ベース'}")
        print()


def test_prompt_generation():
    """プロンプト生成のテスト"""
    client = BedrockClient()
    
    print("\n=== プロンプト生成テスト ===\n")
    
    # 気分ベースのプロンプト
    mood_input = "さっぱりしたものが食べたい"
    mood_prompt = client._create_mood_based_prompt(mood_input)
    print("【気分ベースプロンプト】")
    print(f"入力: {mood_input}")
    print("生成されたプロンプト:")
    print("-" * 50)
    print(mood_prompt)
    print("-" * 50)
    
    print("\n")
    
    # 食材ベースのプロンプト
    ingredient_input = "鶏肉、キャベツ、人参"
    ingredient_prompt = client._create_recipe_prompt(ingredient_input)
    print("【食材ベースプロンプト】")
    print(f"入力: {ingredient_input}")
    print("生成されたプロンプト:")
    print("-" * 50)
    print(ingredient_prompt)
    print("-" * 50)


if __name__ == "__main__":
    test_mood_detection()
    test_prompt_generation()
    
    print("\n" + "=" * 50)
    print("気分モードのテストが完了しました。")
    print("AWS認証情報がある場合は、test_local.pyで実際のAPI呼び出しもテストしてください。")