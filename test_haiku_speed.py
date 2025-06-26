#!/usr/bin/env python3
"""
Test Claude Haiku speed vs Claude 3.5 Sonnet
"""
import boto3
import json
import time
import sys
import os

sys.path.append('/Users/kawabuchieirin/Desktop/LINE-BOT/app')

def test_model_speed(model_id: str, model_name: str):
    """Test speed of a specific model"""
    client = boto3.client(
        service_name='bedrock-runtime',
        region_name='ap-northeast-1'
    )
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 400,
        "messages": [
            {
                "role": "user",
                "content": """あなたは優秀な料理アドバイザーです。
以下の食材を使って、美味しい晩御飯のメニューを2-3個提案してください。

食材: キャベツと鶏肉

提案フォーマット:
1. [メニュー名]
   - 簡単な説明

2. [メニュー名]
   - 簡単な説明

メニュー名は具体的で、説明は1-2文で記載してください。"""
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95
    }
    
    print(f"\n🧪 Testing {model_name} ({model_id})")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        response_body = json.loads(response['body'].read())
        
        print(f"⏱️  Response Time: {duration:.2f} seconds")
        print(f"📊 Input Tokens: {response_body['usage']['input_tokens']}")
        print(f"📊 Output Tokens: {response_body['usage']['output_tokens']}")
        print(f"📝 Response Preview:")
        print(response_body['content'][0]['text'][:200] + "...")
        
        return duration
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    print("🚀 Testing Model Speed for Slack 3-second rule compliance")
    
    models_to_test = [
        ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku"),
        ("anthropic.claude-3-5-sonnet-20240620-v1:0", "Claude 3.5 Sonnet")
    ]
    
    results = {}
    
    for model_id, model_name in models_to_test:
        duration = test_model_speed(model_id, model_name)
        if duration:
            results[model_name] = duration
    
    print("\n" + "=" * 60)
    print("📈 SPEED COMPARISON RESULTS")
    print("=" * 60)
    
    for model_name, duration in results.items():
        compliance = "✅ Compliant" if duration < 3.0 else "❌ Too slow"
        print(f"{model_name}: {duration:.2f}s {compliance}")
    
    print("\n💡 Recommendation:")
    if any(duration < 3.0 for duration in results.values()):
        fastest = min(results.items(), key=lambda x: x[1])
        print(f"Use {fastest[0]} for Slack commands ({fastest[1]:.2f}s)")
    else:
        print("Consider implementing asynchronous response pattern")

if __name__ == "__main__":
    main()