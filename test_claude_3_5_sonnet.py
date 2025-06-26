#!/usr/bin/env python3
"""
Claude 3.5 Sonnet (20240620-v1:0) のテストスクリプト
ap-northeast-1リージョンでの動作確認
"""

import boto3
import json
from botocore.exceptions import ClientError
import os

def test_claude_3_5_sonnet():
    """Claude 3.5 Sonnet (20240620-v1:0) のテスト"""
    
    # 設定
    region = "ap-northeast-1"
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    print(f"テスト設定:")
    print(f"  リージョン: {region}")
    print(f"  モデルID: {model_id}")
    print("-" * 50)
    
    try:
        # Bedrock Runtime clientを作成
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        # テストリクエスト
        test_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [
                {
                    "role": "user",
                    "content": "鶏肉とキャベツが余っています。簡単で美味しい晩御飯のレシピを1つ教えてください。"
                }
            ]
        }
        
        print("リクエスト送信中...")
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(test_request)
        )
        
        # レスポンスを解析
        response_body = json.loads(response['body'].read())
        
        print("✅ 成功! Claude 3.5 Sonnetからのレスポンス:")
        print("-" * 50)
        print(response_body['content'][0]['text'])
        print("-" * 50)
        
        # メタデータ情報
        print(f"\nメタデータ:")
        print(f"  入力トークン数: {response_body.get('usage', {}).get('input_tokens', 'N/A')}")
        print(f"  出力トークン数: {response_body.get('usage', {}).get('output_tokens', 'N/A')}")
        print(f"  モデル: {response_body.get('model', 'N/A')}")
        print(f"  ストップ理由: {response_body.get('stop_reason', 'N/A')}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"❌ AWS APIエラー:")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        
        if error_code == 'ValidationException':
            if 'on-demand throughput' in error_message:
                print(f"\n💡 解決策:")
                print(f"  このモデルはInference Profileが必要です。")
                print(f"  以下のモデルIDを試してください:")
                print(f"  - us.anthropic.claude-3-5-sonnet-20240620-v1:0")
            else:
                print(f"\n💡 解決策:")
                print(f"  モデルIDが正しくない可能性があります。")
                
        elif error_code == 'AccessDeniedException':
            print(f"\n💡 解決策:")
            print(f"  AWS Bedrockコンソールでモデルアクセスを有効化してください:")
            print(f"  https://console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")
            
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")
        return False

def test_alternative_models():
    """代替モデルのテスト"""
    
    print(f"\n" + "="*60)
    print("代替モデルのテスト")
    print("="*60)
    
    # テストするモデル
    alternative_models = [
        {
            "id": "anthropic.claude-3-haiku-20240307-v1:0",
            "name": "Claude 3 Haiku",
            "region": "ap-northeast-1"
        },
        {
            "id": "anthropic.claude-3-sonnet-20240229-v1:0", 
            "name": "Claude 3 Sonnet",
            "region": "ap-northeast-1"
        }
    ]
    
    for model in alternative_models:
        print(f"\n{model['name']} ({model['id']}) のテスト:")
        print("-" * 40)
        
        try:
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=model['region'])
            
            test_request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, how are you?"
                    }
                ]
            }
            
            response = bedrock_runtime.invoke_model(
                modelId=model['id'],
                contentType='application/json',
                accept='application/json',
                body=json.dumps(test_request)
            )
            
            response_body = json.loads(response['body'].read())
            print(f"✅ {model['name']} - 成功!")
            print(f"   レスポンス: {response_body['content'][0]['text'][:50]}...")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"❌ {model['name']} - {error_code}")
            
        except Exception as e:
            print(f"❌ {model['name']} - エラー: {str(e)}")

if __name__ == "__main__":
    print("Claude 3.5 Sonnet (20240620-v1:0) テストスクリプト")
    print("=" * 60)
    
    # メインテスト
    success = test_claude_3_5_sonnet()
    
    # 失敗した場合は代替モデルをテスト
    if not success:
        test_alternative_models()
    
    print(f"\n" + "="*60)
    print("テスト完了")
    print("="*60)