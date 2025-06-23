import logging
import json
from typing import Any, Dict
from config import config

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "channel"):
            log_data["channel"] = record.channel
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_type"):
            log_data["request_type"] = record.request_type
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: str) -> logging.Logger:
    """Setup logger with consistent configuration"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))
    
    return logger

def log_channel_request(logger: logging.Logger, channel: str, user_id: str, message: str):
    """Log channel request with structured data"""
    logger.info(
        f"Received {channel} request",
        extra={
            "channel": channel,
            "user_id": user_id,
            "message": message[:100]  # Truncate long messages
        }
    )

def log_recipe_generation(logger: logging.Logger, channel: str, request_type: str, input_text: str):
    """Log recipe generation request"""
    logger.info(
        f"Generating {request_type} recipe",
        extra={
            "channel": channel,
            "request_type": request_type,
            "input": input_text[:100]
        }
    )