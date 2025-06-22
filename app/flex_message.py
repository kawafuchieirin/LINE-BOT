from linebot.models import FlexSendMessage, BubbleContainer, BoxComponent, TextComponent

def create_recipe_flex_message(recipes: list) -> FlexSendMessage:
    """
    レシピ提案をFlex Messageフォーマットで作成する
    
    Args:
        recipes: レシピのリスト（各レシピは{'name': str, 'description': str}の辞書）
    
    Returns:
        FlexSendMessage
    """
    # メニューアイテムのコンポーネントを作成
    menu_items = []
    
    for i, recipe in enumerate(recipes):
        # レシピ名
        menu_items.append(
            TextComponent(
                text=f"{i+1}. {recipe['name']}",
                size="md",
                weight="bold",
                color="#1DB446",
                margin="md" if i > 0 else None
            )
        )
        
        # レシピの説明
        menu_items.append(
            TextComponent(
                text=recipe['description'],
                size="sm",
                color="#666666",
                wrap=True,
                margin="sm"
            )
        )
    
    # Bubbleコンテナの作成
    bubble = BubbleContainer(
        header=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="🍽️ 晩御飯メニュー提案",
                    weight="bold",
                    color="#FFFFFF",
                    size="lg"
                )
            ],
            backgroundColor="#FF6B6B",
            paddingAll="20px"
        ),
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="本日のおすすめメニューです！",
                    size="sm",
                    color="#999999",
                    margin="md"
                ),
                *menu_items
            ],
            paddingAll="20px"
        ),
        footer=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(
                    text="どれか作ってみてくださいね😊",
                    size="xs",
                    color="#AAAAAA",
                    align="center"
                )
            ],
            paddingAll="10px"
        )
    )
    
    return FlexSendMessage(
        alt_text="晩御飯メニュー提案",
        contents=bubble
    )