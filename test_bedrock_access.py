#!/usr/bin/env python3
"""
Test script to verify Bedrock Claude 3.5 Sonnet access
"""
import boto3
import json

def test_bedrock_access():
    """Test access to Claude 3.5 Sonnet via Bedrock"""
    client = boto3.client(
        service_name='bedrock-runtime',
        region_name='ap-northeast-1'
    )
    
    model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    
    print(f"Testing access to model: {model_id}")
    print(f"Region: ap-northeast-1")
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Hello, Claude. Please respond with 'Access granted' if you can read this."
            }
        ],
        "temperature": 0.0
    }
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        print("\n✅ Success! Model response:")
        print(response_body['content'][0]['text'])
        
    except client.exceptions.AccessDeniedException as e:
        print("\n❌ Access Denied Error:")
        print(f"Error: {str(e)}")
        print("\nPlease enable model access in AWS Bedrock console:")
        print("https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess")
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"Details: {str(e)}")

if __name__ == "__main__":
    test_bedrock_access()