"""
LINE channel handler for dinner suggestion bot
"""
import json
from typing import Dict, Any, Optional
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
)

from ..core.recipe_service import create_recipe_service
from ..utils.config import config
from ..utils.logger import setup_logger, log_channel_request
from ..recipe_parser import parse_recipe_text
from ..flex_message import create_recipe_flex_message

logger = setup_logger(__name__)


class LineHandler:
    """Handler for LINE channel requests"""
    
    def __init__(self):
        """Initialize LINE handler"""
        # Validate configuration
        valid, error = config.validate_line_config()
        if not valid:
            raise ValueError(f"Invalid LINE configuration: {error}")
        
        # Initialize LINE SDK
        self.line_bot_api = LineBotApi(config.line_channel_access_token)
        self.webhook_handler = WebhookHandler(config.line_channel_secret)
        
        # Initialize recipe service
        self.recipe_service = create_recipe_service()
        
        # Register message handler
        self.webhook_handler.add(MessageEvent, message=TextMessage)(self._handle_text_message)
        
        logger.info("LINE handler initialized successfully")
    
    def handle_webhook(self, body: str, signature: str) -> Dict[str, Any]:
        """
        Handle LINE webhook request
        
        Args:
            body: Request body
            signature: LINE signature header
            
        Returns:
            Response dict with statusCode and body
        """
        try:
            self.webhook_handler.handle(body, signature)
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'OK'})
            }
        except InvalidSignatureError:
            logger.error("Invalid LINE signature")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid signature'})
            }
        except Exception as e:
            logger.error(f"Error handling LINE webhook: {str(e)}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }
    
    def _handle_text_message(self, event: MessageEvent):
        """
        Handle text message from LINE
        
        Args:
            event: LINE message event
        """
        try:
            user_message = event.message.text
            user_id = event.source.user_id
            
            # Log the request
            log_channel_request(logger, "line", user_id, user_message)
            
            # Generate recipe suggestions
            result = self.recipe_service.generate_recipe_suggestions(
                user_input=user_message,
                channel="line"
            )
            
            if not result['success']:
                # Send error message
                self.line_bot_api.reply_message(
                    event.reply_token,
                    self._create_error_message(result.get('error', 'An error occurred'))
                )
                return
            
            # Format and send response
            if config.use_flex_message and result['recipes']:
                # Use Flex Message for rich display
                flex_message = create_recipe_flex_message(result['recipes'])
                self.line_bot_api.reply_message(
                    event.reply_token,
                    flex_message
                )
            else:
                # Use plain text message
                text_response = self._format_recipes_as_text(result['recipes'])
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=text_response)
                )
                
        except Exception as e:
            logger.error(f"Error handling LINE message: {str(e)}", exc_info=True)
            try:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    self._create_error_message("general")
                )
            except:
                # Reply token might be expired
                pass
    
    def _create_error_message(self, error_type: str = "general") -> TextSendMessage:
        """Create error message for LINE"""
        error_messages = {
            "general": "申し訳ございません。エラーが発生しました。\nもう一度お試しください。",
            "The service is currently experiencing high demand. Please try again in a moment.": 
                "申し訳ございません。現在アクセスが集中しています。\n少し時間をおいてからお試しください。",
            "The AI model is preparing. Please wait a moment and try again.":
                "申し訳ございません。AIモデルが準備中です。\nしばらくお待ちください。",
            "An error occurred while processing your request.":
                "申し訳ございません。レシピの生成中にエラーが発生しました。"
        }
        
        message = error_messages.get(error_type, error_messages["general"])
        return TextSendMessage(text=message)
    
    def _format_recipes_as_text(self, recipes: list) -> str:
        """Format recipes as plain text"""
        if not recipes:
            return "レシピが見つかりませんでした。もう一度お試しください。"
        
        text = "🍽️ メニュー提案\n\n"
        for recipe in recipes:
            text += f"{recipe['number']}. {recipe['name']}\n"
            text += f"   - {recipe['description']}\n\n"
        
        return text.strip()
    
    def create_quick_reply_message(
        self, 
        text: str, 
        quick_reply_items: list
    ) -> TextSendMessage:
        """
        Create message with quick reply buttons
        
        Args:
            text: Message text
            quick_reply_items: List of {"label": "...", "text": "..."}
            
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


# Factory function
def create_line_handler() -> LineHandler:
    """Create LINE handler instance"""
    return LineHandler()