"""
Client for interacting with the Claude SDK TypeScript Lambda function
This provides an alternative to the direct Bedrock integration
"""
import json
import os
import requests
from typing import Dict, Any, List, Optional
from config import config


class ClaudeSDKClient:
    """Client for Claude SDK Lambda function"""
    
    def __init__(self):
        """Initialize Claude SDK client"""
        # Get the Claude SDK API endpoint from environment or use a default
        self.api_endpoint = os.environ.get('CLAUDE_SDK_API_URL')
        if not self.api_endpoint:
            # If running in Lambda, construct the URL from the API Gateway
            api_id = os.environ.get('HTTP_API_ID')
            region = os.environ.get('AWS_REGION', 'ap-northeast-1')
            stage = os.environ.get('STAGE', 'prod')
            if api_id:
                self.api_endpoint = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}/claude-sdk"
            else:
                # Fallback for local development
                self.api_endpoint = "http://localhost:3000/claude-sdk"
    
    def generate_recipe(self, user_input: str, channel: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Generate recipe using Claude SDK Lambda function
        
        Args:
            user_input: User's input (ingredients or mood)
            channel: Source channel (LINE/Slack)
            user_id: User identifier
            
        Returns:
            Dict with success, recipes, error, and input_type
        """
        try:
            # Prepare request payload
            payload = {
                "userInput": user_input,
                "channel": channel,
                "userId": user_id
            }
            
            # Make request to Claude SDK Lambda
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=25  # 25 second timeout
            )
            
            # Check response status
            if response.status_code != 200:
                print(f"Claude SDK API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'recipes': None,
                    'error': f"API error: {response.status_code}",
                    'input_type': 'ingredient'
                }
            
            # Parse response
            result = response.json()
            return result
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'recipes': None,
                'error': "Request timeout - please try again",
                'input_type': 'ingredient'
            }
        except requests.exceptions.RequestException as e:
            print(f"Request error: {str(e)}")
            return {
                'success': False,
                'recipes': None,
                'error': "Failed to connect to recipe service",
                'input_type': 'ingredient'
            }
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'recipes': None,
                'error': "An unexpected error occurred",
                'input_type': 'ingredient'
            }
    
    def is_available(self) -> bool:
        """Check if Claude SDK service is available"""
        try:
            # Try a simple health check
            response = requests.get(
                self.api_endpoint.replace('/claude-sdk', '/health'),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False