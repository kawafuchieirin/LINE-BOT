"""
Core Claude 3.5 Sonnet client for multi-channel bot
Channel-agnostic AWS Bedrock integration
"""
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from utils.config import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ClaudeClient:
    """Channel-agnostic Claude 3.5 Sonnet client"""
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize Claude client
        
        Args:
            region_name: AWS region name (uses config if not specified)
        """
        self.region_name = region_name or config.aws_region
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region_name
        )
        self.model_id = config.bedrock_model_id
        logger.info(f"Initialized Claude client with model: {self.model_id}")
    
    def generate_completion(
        self, 
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate completion from Claude
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0-1)
            system_prompt: Optional system prompt
            
        Returns:
            Dict containing:
                - success: bool
                - content: str (generated text) or None
                - error: str (error message) or None
        """
        try:
            response = self._invoke_model(prompt, max_tokens, temperature, system_prompt)
            content = self._extract_text_from_response(response)
            
            logger.info(
                "Successfully generated completion",
                extra={"prompt_length": len(prompt), "response_length": len(content)}
            )
            
            return {
                "success": True,
                "content": content,
                "error": None
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = self._handle_bedrock_error(error_code)
            logger.error(f"Bedrock API error: {error_code}", exc_info=True)
            
            return {
                "success": False,
                "content": None,
                "error": error_message
            }
                
        except Exception as e:
            logger.error(f"Unexpected error in completion generation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "content": None,
                "error": "An unexpected error occurred while generating the response."
            }
    
    def _invoke_model(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens
            temperature: Temperature parameter
            system_prompt: Optional system prompt
            
        Returns:
            Bedrock response
        """
        messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.95
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_body["system"] = system_prompt
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        return json.loads(response['body'].read())
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text from Bedrock response
        
        Args:
            response: Bedrock response
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            return response['content'][0]['text']
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract text from response: {str(e)}")
            raise ValueError("Invalid response format from Bedrock")
    
    def _handle_bedrock_error(self, error_code: str) -> str:
        """
        Convert Bedrock error codes to user-friendly messages
        
        Args:
            error_code: AWS error code
            
        Returns:
            User-friendly error message
        """
        error_messages = {
            'ThrottlingException': "The service is currently experiencing high demand. Please try again in a moment.",
            'ModelNotReadyException': "The AI model is preparing. Please wait a moment and try again.",
            'ValidationException': "Invalid request format. Please check your input.",
            'AccessDeniedException': "Access denied to the AI service.",
            'ServiceUnavailableException': "The service is temporarily unavailable."
        }
        
        return error_messages.get(
            error_code, 
            "An error occurred while processing your request."
        )


# Factory function
def create_claude_client(region_name: Optional[str] = None) -> ClaudeClient:
    """
    Create Claude client instance
    
    Args:
        region_name: AWS region name
        
    Returns:
        ClaudeClient instance
    """
    return ClaudeClient(region_name)