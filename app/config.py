"""
Configuration management for dinner suggestion bot
"""
import os
from typing import Optional, Tuple


class Config:
    """Configuration class for environment variables"""
    
    def __init__(self):
        # AWS Configuration
        self.aws_region = os.environ.get("BEDROCK_REGION", "us-east-1")
        self.bedrock_model_id = os.environ.get(
            "BEDROCK_MODEL_ID", 
            "anthropic.claude-3-haiku-20240307-v1:0"
        )
        
        # Logging
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        
        # LINE Configuration
        self.line_channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        self.line_channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
        self.use_flex_message = os.environ.get("USE_FLEX_MESSAGE", "true").lower() == "true"
        
        # Slack Configuration
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    
    def validate_line_config(self) -> Tuple[bool, Optional[str]]:
        """Validate LINE configuration"""
        if not self.line_channel_access_token:
            return False, "LINE_CHANNEL_ACCESS_TOKEN not set"
        if not self.line_channel_secret:
            return False, "LINE_CHANNEL_SECRET not set"
        return True, None
    
    def validate_slack_config(self) -> Tuple[bool, Optional[str]]:
        """Validate Slack configuration"""
        if not self.slack_bot_token:
            return False, "SLACK_BOT_TOKEN not set"
        if not self.slack_signing_secret:
            return False, "SLACK_SIGNING_SECRET not set"
        return True, None


# Global config instance
config = Config()