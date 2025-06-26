#!/usr/bin/env python3
"""
Test script for recipe generation with Claude 3.5 Sonnet
"""
import sys
import os
sys.path.append('/Users/kawabuchieirin/Desktop/LINE-BOT/app')

from recipe_service import RecipeService

def test_recipe_generation():
    """Test recipe generation functionality"""
    print("🍽️ Testing recipe generation with Claude 3.5 Sonnet")
    print("=" * 60)
    
    service = RecipeService()
    
    # Test cases
    test_cases = [
        {
            "input": "キャベツと鶏むね肉",
            "type": "食材ベース",
            "description": "典型的な食材の組み合わせ"
        },
        {
            "input": "さっぱりしたものが食べたい",
            "type": "気分ベース", 
            "description": "気分を表現した入力"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 テストケース {i}: {test_case['type']}")
        print(f"入力: {test_case['input']}")
        print(f"説明: {test_case['description']}")
        print("-" * 40)
        
        result = service.generate_recipe(test_case['input'])
        
        if result['success']:
            print(f"✅ 成功 - 入力タイプ: {result['input_type']}")
            print(f"🍽️ 生成されたレシピ ({len(result['recipes'])}個):")
            
            for recipe in result['recipes']:
                print(f"\n{recipe['number']}. {recipe['name']}")
                print(f"   - {recipe['description']}")
        else:
            print(f"❌ エラー: {result['error']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_recipe_generation()