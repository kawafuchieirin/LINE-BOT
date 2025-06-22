import os
from typing import Optional

class Config:
    """Centralized configuration management for multi-channel bot"""
    
    def __init__(self):
        # AWS Configuration
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        
        # LINE Configuration
        self.line_channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        self.line_channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
        
        # Slack Configuration
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
        self.slack_app_token = os.environ.get("SLACK_APP_TOKEN")
        
        # Common Configuration
        self.use_flex_message = os.environ.get("USE_FLEX_MESSAGE", "true").lower() == "true"
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        
        # Bedrock Configuration
        self.bedrock_model_id = os.environ.get(
            "BEDROCK_MODEL_ID", 
            "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
        
    def validate_line_config(self) -> tuple[bool, Optional[str]]:
        """Validate LINE configuration"""
        if not self.line_channel_access_token:
            return False, "LINE_CHANNEL_ACCESS_TOKEN is not set"
        if not self.line_channel_secret:
            return False, "LINE_CHANNEL_SECRET is not set"
        return True, None
    
    def validate_slack_config(self) -> tuple[bool, Optional[str]]:
        """Validate Slack configuration"""
        if not self.slack_bot_token:
            return False, "SLACK_BOT_TOKEN is not set"
        if not self.slack_signing_secret:
            return False, "SLACK_SIGNING_SECRET is not set"
        return True, None

# Global config instance
config = Config()