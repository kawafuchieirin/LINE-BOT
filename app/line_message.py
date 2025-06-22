"""
LINE メッセージ処理ユーティリティ
"""
from typing import List, Dict, Any
from linebot.models import (
    TextSendMessage, 
    FlexSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction
)


def create_text_message(text: str) -> TextSendMessage:
    """
    シンプルなテキストメッセージを作成
    
    Args:
        text: 送信するテキスト
        
    Returns:
        TextSendMessage
    """
    return TextSendMessage(text=text)


def create_error_message(error_type: str = "general") -> TextSendMessage:
    """
    エラーメッセージを作成
    
    Args:
        error_type: エラーの種類（general, timeout, auth）
        
    Returns:
        TextSendMessage
    """
    error_messages = {
        "general": "申し訳ございません。エラーが発生しました。\nもう一度食材を教えてください。",
        "timeout": "申し訳ございません。処理に時間がかかりすぎました。\nもう一度お試しください。",
        "auth": "申し訳ございません。認証エラーが発生しました。\n管理者にお問い合わせください。",
        "no_ingredients": "食材が見つかりませんでした。\n「〇〇と△△」のように食材を教えてください。"
    }
    
    message = error_messages.get(error_type, error_messages["general"])
    return TextSendMessage(text=message)


def create_quick_reply_message(
    text: str, 
    quick_reply_items: List[Dict[str, str]]
) -> TextSendMessage:
    """
    クイックリプライ付きメッセージを作成
    
    Args:
        text: メッセージ本文
        quick_reply_items: クイックリプライアイテムのリスト
                          [{"label": "表示テキスト", "text": "送信テキスト"}]
    
    Returns:
        TextSendMessage with QuickReply
    """
    quick_reply_buttons = []
    
    for item in quick_reply_items:
        quick_reply_buttons.append(
            QuickReplyButton(
                action=MessageAction(
                    label=item["label"],
                    text=item["text"]
                )
            )
        )
    
    return TextSendMessage(
        text=text,
        quick_reply=QuickReply(items=quick_reply_buttons)
    )


def create_ingredient_suggestions() -> TextSendMessage:
    """
    食材入力のサンプルを提示するクイックリプライメッセージを作成
    
    Returns:
        TextSendMessage with ingredient suggestions
    """
    suggestions = [
        {"label": "肉と野菜", "text": "鶏肉、キャベツ、にんじん"},
        {"label": "魚介類", "text": "サーモン、えび、ブロッコリー"},
        {"label": "和食材料", "text": "豆腐、大根、ねぎ"},
        {"label": "洋食材料", "text": "トマト、チーズ、バジル"},
        {"label": "中華材料", "text": "豚肉、ピーマン、たけのこ"}
    ]
    
    return create_quick_reply_message(
        "どんな食材がありますか？\n以下から選ぶか、自由に入力してください。",
        suggestions
    )


def parse_line_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    LINE Webhookイベントを解析して必要な情報を抽出
    
    Args:
        event: LINE Webhookイベント
        
    Returns:
        解析された情報の辞書
    """
    parsed = {
        "type": event.get("type"),
        "reply_token": event.get("replyToken"),
        "user_id": None,
        "message_text": None,
        "message_type": None
    }
    
    # ソース情報の取得
    if "source" in event:
        parsed["user_id"] = event["source"].get("userId")
    
    # メッセージ情報の取得
    if "message" in event:
        parsed["message_type"] = event["message"].get("type")
        if parsed["message_type"] == "text":
            parsed["message_text"] = event["message"].get("text")
    
    return parsed