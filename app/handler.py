"""
Simplified Lambda handler for dinner suggestion bot
Routes requests to LINE or Slack handlers
"""
import json
from typing import Dict, Any, Optional
from line_bot import LineBotHandler
from slack_bot import SlackBotHandler


# Global handler instances (lazy loading)
_line_handler = None
_slack_handler = None


def get_line_handler():
    """Get or create LINE handler"""
    global _line_handler
    if _line_handler is None:
        try:
            _line_handler = LineBotHandler()
        except Exception as e:
            print(f"Failed to initialize LINE handler: {str(e)}")
    return _line_handler


def get_slack_handler():
    """Get or create Slack handler"""
    global _slack_handler
    if _slack_handler is None:
        try:
            _slack_handler = SlackBotHandler()
        except Exception as e:
            print(f"Failed to initialize Slack handler: {str(e)}")
    return _slack_handler


def detect_channel(event: Dict[str, Any]) -> Optional[str]:
    """Detect which channel the request is from"""
    print(f"DEBUG: Full event structure: {json.dumps(event, indent=2, default=str)}")
    headers = event.get('headers', {})
    body = event.get('body', '')
    path = event.get('path', '')
    
    print(f"DEBUG: Headers: {headers}")
    print(f"DEBUG: Path: {path}")
    print(f"DEBUG: Body: {body[:100]}...")
    
    # Check path first - API Gateway routes
    if '/slack' in path:
        print("DEBUG: Detected Slack from path")
        return 'slack'
    if '/line' in path:
        print("DEBUG: Detected LINE from path")
        return 'line'
    
    # Check for headers (case-insensitive)
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    if 'x-line-signature' in headers_lower:
        print("DEBUG: Detected LINE from signature header")
        return 'line'
    
    if 'x-slack-signature' in headers_lower:
        print("DEBUG: Detected Slack from signature header")
        return 'slack'
    
    # Check body content for additional hints
    try:
        if body:
            # Check if it's URL-encoded (Slack slash command)
            if 'command=' in body and 'text=' in body:
                print("DEBUG: Detected Slack from command in body")
                return 'slack'
            
            # Check if it's JSON
            body_json = json.loads(body)
            
            # LINE webhook events have specific structure
            if 'events' in body_json and isinstance(body_json['events'], list):
                print("DEBUG: Detected LINE from events structure")
                return 'line'
            
            # Slack events have type field
            if 'type' in body_json or 'event' in body_json:
                print("DEBUG: Detected Slack from event structure")
                return 'slack'
    except Exception as e:
        print(f"DEBUG: Body parsing failed: {str(e)}")
    
    print("DEBUG: Could not detect channel")
    return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda main handler function
    Routes requests to appropriate channel handler
    """
    print(f"Lambda handler invoked: {event.get('path', '/')}")
    
    try:
        # Detect channel
        channel = detect_channel(event)
        
        # Fallback: if we can't detect but the path suggests Slack, assume Slack
        if not channel:
            path = event.get('path', '')
            raw_path = event.get('rawPath', '')
            request_context = event.get('requestContext', {})
            resource_path = request_context.get('resourcePath', '')
            
            print(f"DEBUG: Fallback - path='{path}', rawPath='{raw_path}', resourcePath='{resource_path}'")
            
            # Check multiple possible path sources
            all_paths = [path, raw_path, resource_path]
            for check_path in all_paths:
                if check_path and '/slack' in str(check_path):
                    print("DEBUG: Fallback detection - assuming Slack from path")
                    channel = 'slack'
                    break
                elif check_path and '/line' in str(check_path):
                    print("DEBUG: Fallback detection - assuming LINE from path") 
                    channel = 'line'
                    break
        
        # Ultimate fallback: if it looks like a Slack command, assume Slack
        if not channel:
            body = event.get('body', '')
            if 'command=' in body and ('text=' in body or 'user_name=' in body):
                print("DEBUG: Ultimate fallback - assuming Slack from command structure")
                channel = 'slack'
        
        if not channel:
            print("Could not detect channel from request")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Could not detect channel'})
            }
        
        print(f"Detected channel: {channel}")
        
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
            
            # Handle base64 encoded body from API Gateway
            is_base64_encoded = event.get('isBase64Encoded', False)
            if is_base64_encoded:
                import base64
                body = base64.b64decode(body).decode('utf-8')
                print(f"DEBUG: Decoded base64 body: {body[:100]}...")
            
            # Check if it's a slash command or event
            if 'command=' in body:
                print(f"DEBUG: Processing slash command: {body[:100]}...")
                try:
                    result = handler.handle_slash_command(body, headers)
                    print(f"DEBUG: Slash command result: {result.get('statusCode', 'unknown')}")
                    return result
                except Exception as e:
                    print(f"ERROR: Slash command failed: {str(e)}")
                    import traceback
                    print(f"TRACEBACK: {traceback.format_exc()}")
                    raise
            else:
                print(f"DEBUG: Processing event: {body[:100]}...")
                return handler.handle_event(body, headers)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unsupported channel: {channel}'})
            }
            
    except Exception as e:
        print(f"ERROR: Unexpected error in Lambda handler: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }