"""
Multi-channel Lambda handler for dinner suggestion bot
Routes requests to appropriate channel handlers (LINE, Slack)
"""
import json
from typing import Dict, Any, Optional

from .handlers.line_handler import create_line_handler
from .handlers.slack_handler import create_slack_handler
from .utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Initialize handlers (lazy loading)
_line_handler = None
_slack_handler = None


def get_line_handler():
    """Get or create LINE handler"""
    global _line_handler
    if _line_handler is None:
        try:
            _line_handler = create_line_handler()
        except Exception as e:
            logger.error(f"Failed to initialize LINE handler: {str(e)}")
    return _line_handler


def get_slack_handler():
    """Get or create Slack handler"""
    global _slack_handler
    if _slack_handler is None:
        try:
            _slack_handler = create_slack_handler()
        except Exception as e:
            logger.error(f"Failed to initialize Slack handler: {str(e)}")
    return _slack_handler


def detect_channel(event: Dict[str, Any]) -> Optional[str]:
    """
    Detect which channel the request is from
    
    Args:
        event: Lambda event
        
    Returns:
        Channel name ('line', 'slack') or None
    """
    headers = event.get('headers', {})
    body = event.get('body', '')
    
    # Check for LINE signature
    if 'x-line-signature' in headers:
        return 'line'
    
    # Check for Slack signature
    if 'x-slack-signature' in headers:
        return 'slack'
    
    # Check body content for additional hints
    try:
        if body:
            # Check if it's URL-encoded (Slack slash command)
            if 'command=' in body and 'text=' in body:
                return 'slack'
            
            # Check if it's JSON
            body_json = json.loads(body)
            
            # LINE webhook events have specific structure
            if 'events' in body_json and isinstance(body_json['events'], list):
                return 'line'
            
            # Slack events have type field
            if 'type' in body_json or 'event' in body_json:
                return 'slack'
    except:
        pass
    
    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda main handler function
    Routes requests to appropriate channel handler
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Response dict with statusCode and body
    """
    logger.info("Lambda handler invoked", extra={"path": event.get("path", "/")})
    
    try:
        # Detect channel
        channel = detect_channel(event)
        
        if not channel:
            logger.error("Could not detect channel from request")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Could not detect channel'})
            }
        
        logger.info(f"Detected channel: {channel}")
        
        # Route to appropriate handler
        if channel == 'line':
            handler = get_line_handler()
            if not handler:
                return {
                    'statusCode': 503,
                    'body': json.dumps({'error': 'LINE handler not available'})
                }
            
            body = event.get('body', '')
            signature = event.get('headers', {}).get('x-line-signature', '')
            return handler.handle_webhook(body, signature)
            
        elif channel == 'slack':
            handler = get_slack_handler()
            if not handler:
                return {
                    'statusCode': 503,
                    'body': json.dumps({'error': 'Slack handler not available'})
                }
            
            body = event.get('body', '')
            headers = event.get('headers', {})
            
            # Check if it's a slash command or event
            if 'command=' in body:
                return handler.handle_slash_command(body, headers)
            else:
                return handler.handle_event(body, headers)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unsupported channel: {channel}'})
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in Lambda handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }