"""
Slack channel handler for dinner suggestion bot
"""
import json
import time
import hmac
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import parse_qs

from ..core.recipe_service import create_recipe_service
from ..utils.config import config
from ..utils.logger import setup_logger, log_channel_request

logger = setup_logger(__name__)


class SlackHandler:
    """Handler for Slack channel requests"""
    
    def __init__(self):
        """Initialize Slack handler"""
        # Validate configuration
        valid, error = config.validate_slack_config()
        if not valid:
            logger.warning(f"Slack configuration not complete: {error}")
            # Don't raise error, allow partial functionality
        
        # Initialize recipe service
        self.recipe_service = create_recipe_service()
        
        logger.info("Slack handler initialized")
    
    def handle_slash_command(self, body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle Slack slash command (/dinner)
        
        Args:
            body: Request body (URL-encoded form data)
            headers: Request headers
            
        Returns:
            Response dict for Lambda
        """
        # Verify Slack signature
        if not self._verify_slack_signature(body, headers):
            logger.error("Invalid Slack signature")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        try:
            # Parse slash command data
            command_data = parse_qs(body)
            
            # Extract relevant information
            user_id = command_data.get('user_id', [''])[0]
            user_name = command_data.get('user_name', [''])[0]
            text = command_data.get('text', [''])[0]
            response_url = command_data.get('response_url', [''])[0]
            
            # Log the request
            log_channel_request(logger, "slack", user_id, text)
            
            # If no text provided, show help
            if not text.strip():
                return self._create_help_response()
            
            # Generate recipe suggestions
            result = self.recipe_service.generate_recipe_suggestions(
                user_input=text,
                channel="slack"
            )
            
            if not result['success']:
                return self._create_error_response(result.get('error'))
            
            # Format response for Slack
            response = self._format_slack_response(result['recipes'], result['input_type'])
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response)
            }
            
        except Exception as e:
            logger.error(f"Error handling Slack command: {str(e)}", exc_info=True)
            return self._create_error_response("An unexpected error occurred")
    
    def handle_event(self, body: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle Slack event (mentions, DMs)
        
        Args:
            body: Request body (JSON)
            headers: Request headers
            
        Returns:
            Response dict for Lambda
        """
        # Verify Slack signature
        if not self._verify_slack_signature(body, headers):
            logger.error("Invalid Slack signature")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        try:
            event_data = json.loads(body)
            
            # Handle URL verification challenge
            if event_data.get('type') == 'url_verification':
                return {
                    'statusCode': 200,
                    'body': json.dumps({'challenge': event_data['challenge']})
                }
            
            # Handle event
            event = event_data.get('event', {})
            event_type = event.get('type')
            
            # We only handle app_mention and message events
            if event_type not in ['app_mention', 'message']:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'ignored'})
                }
            
            # Extract message text and user
            text = event.get('text', '')
            user_id = event.get('user', '')
            
            # Remove bot mention from text
            text = self._remove_bot_mention(text)
            
            # Log the request
            log_channel_request(logger, "slack", user_id, text)
            
            # Generate recipe suggestions
            result = self.recipe_service.generate_recipe_suggestions(
                user_input=text,
                channel="slack"
            )
            
            # Note: For events, we would need to use Slack Web API to post response
            # This requires additional setup with slack_sdk
            logger.info(f"Generated recipes for Slack event: {result}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'})
            }
            
        except Exception as e:
            logger.error(f"Error handling Slack event: {str(e)}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }
    
    def _verify_slack_signature(self, body: str, headers: Dict[str, str]) -> bool:
        """
        Verify Slack request signature
        
        Args:
            body: Request body
            headers: Request headers
            
        Returns:
            True if signature is valid
        """
        if not config.slack_signing_secret:
            logger.warning("Slack signing secret not configured, skipping verification")
            return True
        
        timestamp = headers.get('x-slack-request-timestamp', '')
        signature = headers.get('x-slack-signature', '')
        
        if not timestamp or not signature:
            return False
        
        # Check timestamp to prevent replay attacks
        if abs(time.time() - float(timestamp)) > 60 * 5:
            return False
        
        # Create signature base string
        sig_basestring = f"v0:{timestamp}:{body}"
        
        # Calculate expected signature
        expected_sig = 'v0=' + hmac.new(
            config.slack_signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_sig, signature)
    
    def _create_help_response(self) -> Dict[str, Any]:
        """Create help response for Slack"""
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': '🍽️ 晩御飯提案BOTの使い方',
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': '*晩御飯提案BOTの使い方*\n\n'
                                   '食材や気分を教えてください。美味しいメニューを提案します！'
                        }
                    },
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': '*📝 使用例*\n'
                                   '• `/dinner キャベツと鶏肉`\n'
                                   '• `/dinner さっぱりしたものが食べたい`\n'
                                   '• `/dinner 夏バテで食欲ない`\n'
                                   '• `/dinner こってり系でスタミナつくもの`'
                        }
                    }
                ]
            })
        }
    
    def _create_error_response(self, error: str) -> Dict[str, Any]:
        """Create error response for Slack"""
        error_messages = {
            "The service is currently experiencing high demand. Please try again in a moment.": 
                "現在アクセスが集中しています。少し時間をおいてからお試しください。",
            "The AI model is preparing. Please wait a moment and try again.":
                "AIモデルが準備中です。しばらくお待ちください。",
            "An error occurred while processing your request.":
                "レシピの生成中にエラーが発生しました。"
        }
        
        message = error_messages.get(error, "エラーが発生しました。もう一度お試しください。")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': f'⚠️ {message}'
            })
        }
    
    def _format_slack_response(self, recipes: list, input_type: str) -> Dict[str, Any]:
        """
        Format recipes for Slack response
        
        Args:
            recipes: List of recipe dicts
            input_type: 'mood' or 'ingredient'
            
        Returns:
            Slack message format
        """
        if not recipes:
            return {
                'response_type': 'in_channel',
                'text': 'レシピが見つかりませんでした。'
            }
        
        # Create blocks for rich formatting
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': '🍽️ メニュー提案'
                }
            }
        ]
        
        # Add context about input type
        context_text = "気分に合わせた提案" if input_type == 'mood' else "食材を使った提案"
        blocks.append({
            'type': 'context',
            'elements': [{
                'type': 'mrkdwn',
                'text': f'_{context_text}_'
            }]
        })
        
        # Add each recipe as a section
        for recipe in recipes:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*{recipe['number']}. {recipe['name']}*\n{recipe['description']}"
                }
            })
        
        # Add divider at the end
        blocks.append({'type': 'divider'})
        
        return {
            'response_type': 'in_channel',
            'text': '🍽️ メニュー提案',
            'blocks': blocks
        }
    
    def _remove_bot_mention(self, text: str) -> str:
        """Remove bot mention from message text"""
        # Remove <@BOTID> pattern
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()


# Factory function
def create_slack_handler() -> SlackHandler:
    """Create Slack handler instance"""
    return SlackHandler()