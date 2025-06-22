import re
from typing import List, Dict


def parse_recipe_text(recipe_text: str) -> List[Dict[str, str]]:
    """
    Bedrockからのレシピテキストを解析して構造化されたデータに変換する
    
    Args:
        recipe_text: Bedrockから返されたレシピテキスト
        
    Returns:
        レシピのリスト（各レシピは{'name': str, 'description': str}の辞書）
    """
    recipes = []
    
    # レシピパターンを検索（番号付きのメニュー名を探す）
    # パターン: "1. メニュー名" または "1．メニュー名" など
    pattern = r'(\d+)[\.．]\s*([^\n]+)\n\s*[-－]\s*([^\n]+)'
    
    matches = re.findall(pattern, recipe_text, re.MULTILINE)
    
    for match in matches:
        _, name, description = match
        recipes.append({
            'name': name.strip(),
            'description': description.strip()
        })
    
    # マッチしなかった場合のフォールバック処理
    if not recipes:
        # 単純な行ベースの解析を試みる
        lines = recipe_text.strip().split('\n')
        current_recipe = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 番号で始まる行をメニュー名として扱う
            if re.match(r'^\d+[\.．]', line):
                if current_recipe:
                    recipes.append(current_recipe)
                name = re.sub(r'^\d+[\.．]\s*', '', line)
                current_recipe = {'name': name, 'description': ''}
            # ハイフンまたは中点で始まる行を説明として扱う
            elif re.match(r'^[-－・]', line) and current_recipe:
                description = re.sub(r'^[-－・]\s*', '', line)
                current_recipe['description'] = description
        
        if current_recipe:
            recipes.append(current_recipe)
    
    # 少なくとも1つのレシピを返すようにする
    if not recipes:
        recipes = [{
            'name': '提案されたメニュー',
            'description': recipe_text[:100] + '...' if len(recipe_text) > 100 else recipe_text
        }]
    
    return recipes


def extract_ingredients(user_message: str) -> str:
    """
    ユーザーメッセージから食材を抽出する
    
    Args:
        user_message: ユーザーからのメッセージ
        
    Returns:
        抽出された食材の文字列
    """
    # 簡単な実装：現時点ではユーザーメッセージをそのまま返す
    # 将来的には、より高度な自然言語処理を実装可能
    
    # 「残ってる」「ある」などの表現を除去
    cleaned_message = user_message
    remove_patterns = [
        r'が?残って[いる|る]',
        r'があ[る|ります]',
        r'を?使って',
        r'で?何か?作[れる|れます]か？?',
        r'[。、！？…]'
    ]
    
    for pattern in remove_patterns:
        cleaned_message = re.sub(pattern, '', cleaned_message)
    
    # 「と」「、」で区切られた食材を整理
    ingredients = re.split(r'[と、]', cleaned_message)
    ingredients = [ing.strip() for ing in ingredients if ing.strip()]
    
    return '、'.join(ingredients) if ingredients else user_message