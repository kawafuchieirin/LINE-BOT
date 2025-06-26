#!/usr/bin/env python3
"""
Test script for Lambda endpoint with LINE webhook simulation
"""
import requests
import json

def test_lambda_endpoint():
    """Test Lambda endpoint with simulated LINE webhook"""
    
    # Lambda endpoint URL
    endpoint_url = "https://q09aevzmql.execute-api.ap-northeast-1.amazonaws.com/prod/line"
    
    # Simulated LINE webhook event
    test_event = {
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "text": "キャベツと鶏むね肉"
                },
                "replyToken": "test-reply-token",
                "source": {
                    "userId": "test-user-id",
                    "type": "user"
                },
                "timestamp": 1640995200000
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Line-Signature": "dummy-signature"  # This will fail signature validation but that's expected
    }
    
    print("🚀 Testing Lambda endpoint...")
    print(f"URL: {endpoint_url}")
    print(f"Payload: {json.dumps(test_event, indent=2, ensure_ascii=False)}")
    print("=" * 60)
    
    try:
        response = requests.post(
            endpoint_url,
            json=test_event,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📝 Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 Response Body (text): {response.text}")
            
        if response.status_code == 200:
            print("\n✅ Lambda endpoint is responding successfully!")
        elif response.status_code == 400:
            print("\n⚠️ 400 Bad Request - Expected due to invalid LINE signature")
            print("This means the Lambda is working but signature validation failed (as expected)")
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_lambda_endpoint()