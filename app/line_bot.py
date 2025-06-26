"""
LINE Bot handler for dinner suggestion bot
"""
import json
from typing import Dict, Any
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage,
    BubbleContainer, BoxComponent, TextComponent
)
from config import config
from recipe_service import RecipeService
from ingredient_storage import IngredientStorage


class LineBotHandler:
    """Handler for LINE Bot functionality"""
    
    def __init__(self):
        """Initialize LINE Bot handler"""
        # Validate configuration
        valid, error = config.validate_line_config()
        if not valid:
            raise ValueError(f"Invalid LINE configuration: {error}")
        
        # Initialize LINE SDK
        self.line_bot_api = LineBotApi(config.line_channel_access_token)
        self.webhook_handler = WebhookHandler(config.line_channel_secret)
        self.recipe_service = RecipeService()
        self.ingredient_storage = IngredientStorage()
        
        # Register message handler
        self.webhook_handler.add(MessageEvent, message=TextMessage)(self._handle_text_message)
    
    def handle_webhook(self, body: str, signature: str) -> Dict[str, Any]:
        """Handle LINE webhook request"""
        try:
            self.webhook_handler.handle(body, signature)
            return {'statusCode': 200, 'body': json.dumps({'status': 'OK'})}
        except InvalidSignatureError:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid signature'})}
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}
    
    def _handle_text_message(self, event: MessageEvent):
        """Handle text message from LINE user"""
        try:
            user_message = event.message.text
            user_id = event.source.user_id
            
            # Parse commands
            if user_message.startswith('追加 ') or user_message.startswith('add '):
                # Add ingredients
                ingredients_text = user_message[3:].strip()
                self._handle_add_ingredients(event, user_id, ingredients_text)
                return
            elif user_message in ['一覧', 'リスト', 'list']:
                # List ingredients
                self._handle_list_ingredients(event, user_id)
                return
            elif user_message in ['削除', 'クリア', 'clear']:
                # Clear ingredients
                self._handle_clear_ingredients(event, user_id)
                return
            elif user_message in ['保存済み', '登録済み', 'stored']:
                # Use stored ingredients for recipe
                stored_ingredients = self.ingredient_storage.get_ingredients(user_id)
                if stored_ingredients:
                    user_message = ' '.join(stored_ingredients)
                else:
                    self.line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="登録済みの食材がありません。\n「追加 食材名」で食材を登録してください。")
                    )
                    return
            
            # Generate recipe suggestions
            result = self.recipe_service.generate_recipe(user_message)
            
            if not result['success']:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    self._create_error_message(result.get('error', 'An error occurred'))
                )
                return
            
            # Send response
            if config.use_flex_message and result['recipes']:
                flex_message = self._create_flex_message(result['recipes'])
                self.line_bot_api.reply_message(event.reply_token, flex_message)
            else:
                text_response = self._format_recipes_as_text(result['recipes'])
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=text_response)
                )
                
        except Exception as e:
            try:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    self._create_error_message("general")
                )
            except:
                pass  # Reply token might be expired
    
    def _create_flex_message(self, recipes: list) -> FlexSendMessage:
        """Create Flex Message for recipe display"""
        menu_items = []
        
        for i, recipe in enumerate(recipes):
            menu_items.append(
                TextComponent(
                    text=f"{recipe['number']}. {recipe['name']}",
                    size="md",
                    weight="bold",
                    color="#1DB446",
                    margin="md" if i > 0 else None
                )
            )
            menu_items.append(
                TextComponent(
                    text=recipe['description'],
                    size="sm",
                    color="#666666",
                    wrap=True,
                    margin="sm"
                )
            )
        
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
            )
        )
        
        return FlexSendMessage(alt_text="晩御飯メニュー提案", contents=bubble)
    
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
    
    def _handle_add_ingredients(self, event: MessageEvent, user_id: str, ingredients_text: str):
        """Handle adding ingredients to storage
        
        Args:
            event: LINE message event
            user_id: LINE user ID
            ingredients_text: Text containing ingredients to add
        """
        if not ingredients_text:
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="追加する食材を指定してください。\n例: 追加 キャベツ 鶏肉")
            )
            return
        
        # Parse ingredients (comma or space separated)
        ingredients = []
        if '、' in ingredients_text or ',' in ingredients_text:
            # Handle comma-separated
            ingredients = [ing.strip() for ing in ingredients_text.replace('、', ',').split(',') if ing.strip()]
        else:
            # Handle space-separated
            ingredients = ingredients_text.split()
        
        # Add to storage
        success = self.ingredient_storage.add_ingredients(user_id, ingredients)
        
        if success:
            # Get updated list
            all_ingredients = self.ingredient_storage.get_ingredients(user_id)
            formatted_list = self.ingredient_storage.format_ingredients_list(all_ingredients)
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"✅ 食材を追加しました！\n\n{formatted_list}")
            )
        else:
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 食材の追加に失敗しました。もう一度お試しください。")
            )
    
    def _handle_list_ingredients(self, event: MessageEvent, user_id: str):
        """Handle listing stored ingredients
        
        Args:
            event: LINE message event
            user_id: LINE user ID
        """
        ingredients = self.ingredient_storage.get_ingredients(user_id)
        formatted_list = self.ingredient_storage.format_ingredients_list(ingredients)
        
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=formatted_list)
        )
    
    def _handle_clear_ingredients(self, event: MessageEvent, user_id: str):
        """Handle clearing stored ingredients
        
        Args:
            event: LINE message event
            user_id: LINE user ID
        """
        success = self.ingredient_storage.clear_ingredients(user_id)
        
        if success:
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="🗑️ 登録済みの食材をすべて削除しました。")
            )
        else:
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 食材の削除に失敗しました。もう一度お試しください。")
            )