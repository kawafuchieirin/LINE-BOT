"""
FastAPI implementation for Slack Bot endpoints
Provides local development and alternative deployment option for the Lambda-based bot
"""
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import hmac
import hashlib
import os
import time
import json
import logging
from typing import Optional, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Import the existing recipe service from the Lambda app
from app.core.recipe_service import create_recipe_service
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dinner Suggestion Bot API",
    description="FastAPI endpoints for Slack integration",
    version="1.0.0"
)

# Environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

# Initialize recipe service
recipe_service = create_recipe_service()


def verify_slack_signature(
    body: bytes,
    slack_signature: str,
    slack_timestamp: str
) -> bool:
    """
    Verify Slack request signature
    
    Args:
        body: Raw request body
        slack_signature: X-Slack-Signature header
        slack_timestamp: X-Slack-Request-Timestamp header
        
    Returns:
        True if signature is valid
    """
    if not SLACK_SIGNING_SECRET:
        logger.warning("SLACK_SIGNING_SECRET not configured, skipping verification")
        return True
    
    # Check timestamp to prevent replay attacks (5 minutes)
    if abs(time.time() - int(slack_timestamp)) > 60 * 5:
        logger.error("Slack request timestamp too old")
        return False
    
    # Create signature base string
    basestring = f"v0:{slack_timestamp}:{body.decode('utf-8')}"
    
    # Calculate expected signature
    my_signature = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(my_signature, slack_signature)


def send_slack_message(channel: str, text: str, blocks: Optional[list] = None) -> bool:
    """
    Send a message to Slack channel
    
    Args:
        channel: Channel ID to send message to
        text: Message text
        blocks: Optional Block Kit blocks
        
    Returns:
        True if message sent successfully
    """
    if not slack_client:
        logger.error("Slack client not initialized")
        return False
    
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks
        )
        return response["ok"]
    except SlackApiError as e:
        logger.error(f"Failed to send Slack message: {e.response['error']}")
        return False


def format_recipe_blocks(recipes: list, input_type: str) -> list:
    """
    Format recipes as Slack Block Kit blocks
    
    Args:
        recipes: List of recipe dicts
        input_type: 'mood' or 'ingredient'
        
    Returns:
        List of Block Kit blocks
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🍽️ メニュー提案"
            }
        }
    ]
    
    # Add context about input type
    context_text = "気分に合わせた提案" if input_type == "mood" else "食材を使った提案"
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"_{context_text}_"
        }]
    })
    
    # Add each recipe as a section
    for recipe in recipes:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{recipe['number']}. {recipe['name']}*\n{recipe['description']}"
            }
        })
    
    # Add divider at the end
    blocks.append({"type": "divider"})
    
    return blocks


def remove_bot_mention(text: str) -> str:
    """Remove bot mention from message text"""
    import re
    return re.sub(r'<@[A-Z0-9]+>', '', text).strip()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Dinner Suggestion Bot FastAPI"}


@app.post("/slack/events")
async def slack_events(
    request: Request,
    x_slack_signature: Optional[str] = Header(None),
    x_slack_request_timestamp: Optional[str] = Header(None)
):
    """
    Handle Slack events (mentions, DMs, url_verification)
    
    This endpoint handles:
    - URL verification challenges from Slack
    - Event callbacks (app_mention, message.im)
    """
    # Get request body
    body = await request.body()
    
    # Verify Slack signature
    if not verify_slack_signature(body, x_slack_signature, x_slack_request_timestamp):
        logger.error("Invalid Slack signature")
        raise HTTPException(status_code=403, detail="Invalid Slack signature")
    
    # Parse JSON payload
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle URL verification challenge
    if payload.get("type") == "url_verification":
        challenge = payload.get("challenge")
        logger.info(f"Handling url_verification with challenge: {challenge}")
        return PlainTextResponse(content=challenge)
    
    # Handle event callback
    if payload.get("type") == "event_callback":
        event = payload.get("event", {})
        event_type = event.get("type")
        
        logger.info(f"Handling event: {event_type}")
        
        if event_type == "app_mention":
            # Bot was mentioned
            text = event.get("text", "")
            channel = event.get("channel")
            user = event.get("user")
            
            # Remove bot mention from text
            text = remove_bot_mention(text)
            
            logger.info(f"App mention from user {user}: {text}")
            
            # Generate recipe suggestions
            if text.strip():
                result = recipe_service.generate_recipe_suggestions(
                    user_input=text,
                    channel="slack"
                )
                
                if result["success"]:
                    # Format and send response
                    blocks = format_recipe_blocks(
                        result["recipes"],
                        result["input_type"]
                    )
                    send_slack_message(
                        channel=channel,
                        text="🍽️ メニュー提案",
                        blocks=blocks
                    )
                else:
                    # Send error message
                    send_slack_message(
                        channel=channel,
                        text=f"⚠️ エラーが発生しました: {result.get('error', 'Unknown error')}"
                    )
            else:
                # Send help message
                help_blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*晩御飯提案BOTの使い方*\n\n食材や気分を教えてください。美味しいメニューを提案します！"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*📝 使用例*\n• キャベツと鶏肉\n• さっぱりしたものが食べたい\n• 夏バテで食欲ない\n• こってり系でスタミナつくもの"
                        }
                    }
                ]
                send_slack_message(
                    channel=channel,
                    text="🍽️ 晩御飯提案BOTの使い方",
                    blocks=help_blocks
                )
        
        elif event_type == "message" and event.get("channel_type") == "im":
            # Direct message
            text = event.get("text", "")
            channel = event.get("channel")
            user = event.get("user")
            
            # Skip bot messages
            if event.get("bot_id"):
                return JSONResponse(content={"status": "ok"})
            
            logger.info(f"DM from user {user}: {text}")
            
            # Generate recipe suggestions
            if text.strip():
                result = recipe_service.generate_recipe_suggestions(
                    user_input=text,
                    channel="slack"
                )
                
                if result["success"]:
                    # Format and send response
                    blocks = format_recipe_blocks(
                        result["recipes"],
                        result["input_type"]
                    )
                    send_slack_message(
                        channel=channel,
                        text="🍽️ メニュー提案",
                        blocks=blocks
                    )
                else:
                    # Send error message
                    send_slack_message(
                        channel=channel,
                        text=f"⚠️ エラーが発生しました: {result.get('error', 'Unknown error')}"
                    )
            else:
                # Send help message
                help_blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*晩御飯提案BOTの使い方*\n\n食材や気分を教えてください。美味しいメニューを提案します！"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*📝 使用例*\n• キャベツと鶏肉\n• さっぱりしたものが食べたい\n• 夏バテで食欲ない\n• こってり系でスタミナつくもの"
                        }
                    }
                ]
                send_slack_message(
                    channel=channel,
                    text="🍽️ 晩御飯提案BOTの使い方",
                    blocks=help_blocks
                )
    
    # Return OK response
    return JSONResponse(content={"status": "ok"})


@app.post("/slack/slash/dinner")
async def slack_slash_dinner(
    request: Request,
    x_slack_signature: Optional[str] = Header(None),
    x_slack_request_timestamp: Optional[str] = Header(None)
):
    """
    Handle /dinner slash command
    
    This endpoint processes the /dinner command and returns recipe suggestions
    """
    # Get request body
    body = await request.body()
    
    # Verify Slack signature
    if not verify_slack_signature(body, x_slack_signature, x_slack_request_timestamp):
        logger.error("Invalid Slack signature")
        raise HTTPException(status_code=403, detail="Invalid Slack signature")
    
    # Parse form data
    form_data = await request.form()
    
    # Extract relevant information
    user_id = form_data.get("user_id", "")
    user_name = form_data.get("user_name", "")
    text = form_data.get("text", "")
    channel_id = form_data.get("channel_id", "")
    
    logger.info(f"Slash command from {user_name} ({user_id}): {text}")
    
    # If no text provided, show help
    if not text.strip():
        return JSONResponse(content={
            "response_type": "ephemeral",
            "text": "🍽️ 晩御飯提案BOTの使い方",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*晩御飯提案BOTの使い方*\n\n食材や気分を教えてください。美味しいメニューを提案します！"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📝 使用例*\n• `/dinner キャベツと鶏肉`\n• `/dinner さっぱりしたものが食べたい`\n• `/dinner 夏バテで食欲ない`\n• `/dinner こってり系でスタミナつくもの`"
                    }
                }
            ]
        })
    
    # Generate recipe suggestions
    result = recipe_service.generate_recipe_suggestions(
        user_input=text,
        channel="slack"
    )
    
    if result["success"]:
        # Format response
        blocks = format_recipe_blocks(
            result["recipes"],
            result["input_type"]
        )
        
        return JSONResponse(content={
            "response_type": "in_channel",
            "text": "🍽️ メニュー提案",
            "blocks": blocks
        })
    else:
        # Return error message
        error_message = {
            "The service is currently experiencing high demand. Please try again in a moment.": 
                "現在アクセスが集中しています。少し時間をおいてからお試しください。",
            "The AI model is preparing. Please wait a moment and try again.":
                "AIモデルが準備中です。しばらくお待ちください。",
            "An error occurred while processing your request.":
                "レシピの生成中にエラーが発生しました。"
        }.get(result.get("error"), "エラーが発生しました。もう一度お試しください。")
        
        return JSONResponse(content={
            "response_type": "ephemeral",
            "text": f"⚠️ {error_message}"
        })


if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )