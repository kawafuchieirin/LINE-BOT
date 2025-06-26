#!/usr/bin/env python3
"""
Test script for new Slack slash command endpoint with separate Lambda functions
"""
import requests
import json
from urllib.parse import urlencode

def test_slack_slash_endpoint():
    """Test the new Slack slash command endpoint"""
    
    # New Slack slash command endpoint
    endpoint_url = "https://q09aevzmql.execute-api.ap-northeast-1.amazonaws.com/prod/slack/slash"
    
    # Simulated Slack slash command payload
    slack_payload = {
        'token': 'test-verification-token',
        'team_id': 'T1234567890',
        'team_domain': 'testteam',
        'channel_id': 'C1234567890',
        'channel_name': 'general',
        'user_id': 'U1234567890',
        'user_name': 'testuser',
        'command': '/dinner',
        'text': 'キャベツと鶏肉',
        'response_url': 'https://hooks.slack.com/commands/T1234567890/1234567890/abcdefghijklmnopqrstuvwx',
        'trigger_id': '123456789.123456789.123456789'
    }
    
    # Encode as form data (Slack sends form-encoded data)
    form_data = urlencode(slack_payload)
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Slack-Signature": "v0=dummy-signature",  # Will fail verification but that's expected
        "X-Slack-Request-Timestamp": "1234567890"
    }
    
    print("🚀 Testing new Slack slash command endpoint...")
    print(f"URL: {endpoint_url}")
    print(f"Command: {slack_payload['command']} {slack_payload['text']}")
    print("=" * 60)
    
    try:
        response = requests.post(
            endpoint_url,
            data=form_data,
            headers=headers,
            timeout=10  # Should respond within 3 seconds
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📝 Response Body: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 Response Body (text): {response.text}")
            
        if response.status_code == 200:
            print("\n✅ Slack slash command endpoint is responding successfully!")
            print("🔄 Check CloudWatch Logs for async processor execution")
        elif response.status_code == 400:
            print("\n⚠️  400 Bad Request - May be due to signature validation")
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    test_slack_slash_endpoint()