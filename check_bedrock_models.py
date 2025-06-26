#!/usr/bin/env python3
"""
AWS Bedrockで利用可能なモデルを確認するスクリプト
Claude 3.5 Sonnetモデルの正確なモデルIDとinference profileを調査します
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError
import sys

def check_bedrock_models():
    """Bedrockで利用可能なモデルを確認"""
    
    # 複数のリージョンをチェック
    regions = ['us-east-1', 'us-west-2', 'ap-northeast-1', 'eu-west-1']
    
    for region in regions:
        print(f"\n{'='*80}")
        print(f"リージョン: {region}")
        print(f"{'='*80}")
        
        try:
            # Bedrock clientを作成
            bedrock = boto3.client('bedrock', region_name=region)
            
            # 利用可能な基盤モデルを一覧表示
            print("\n利用可能な基盤モデル:")
            print("-" * 40)
            
            response = bedrock.list_foundation_models()
            models = response.get('modelSummaries', [])
            
            # Claude関連のモデルをフィルタリング
            claude_models = [m for m in models if 'claude' in m.get('modelId', '').lower()]
            
            if claude_models:
                for model in claude_models:
                    print(f"\nモデルID: {model.get('modelId')}")
                    print(f"  プロバイダー: {model.get('providerName')}")
                    print(f"  モデル名: {model.get('modelName')}")
                    print(f"  入力モダリティ: {model.get('inputModalities')}")
                    print(f"  出力モダリティ: {model.get('outputModalities')}")
                    print(f"  レスポンスストリーミング: {model.get('responseStreamingSupported')}")
                    
                    # カスタマイズオプション
                    customizations = model.get('customizationsSupported', [])
                    if customizations:
                        print(f"  カスタマイズ: {', '.join(customizations)}")
                    
                    # 推論タイプ
                    inference_types = model.get('inferenceTypesSupported', [])
                    if inference_types:
                        print(f"  推論タイプ: {', '.join(inference_types)}")
            else:
                print("  Claudeモデルが見つかりませんでした")
            
            # Inference profilesを確認
            print("\n\nInference Profiles:")
            print("-" * 40)
            
            try:
                # list_inference_profilesは新しいAPIなので、try-exceptで囲む
                if hasattr(bedrock, 'list_inference_profiles'):
                    profiles_response = bedrock.list_inference_profiles()
                    profiles = profiles_response.get('inferenceProfileSummaries', [])
                    
                    claude_profiles = [p for p in profiles if 'claude' in str(p).lower()]
                    
                    if claude_profiles:
                        for profile in claude_profiles:
                            print(f"\nProfile ARN: {profile.get('inferenceProfileArn')}")
                            print(f"  Profile名: {profile.get('inferenceProfileName')}")
                            print(f"  説明: {profile.get('description')}")
                            print(f"  ステータス: {profile.get('status')}")
                            print(f"  タイプ: {profile.get('type')}")
                            
                            # モデル情報
                            models_info = profile.get('models', [])
                            if models_info:
                                print(f"  関連モデル:")
                                for model_info in models_info:
                                    print(f"    - {model_info.get('modelArn')}")
                    else:
                        print("  Claude用のInference Profileが見つかりませんでした")
                else:
                    print("  list_inference_profiles APIが利用できません")
                    
            except Exception as e:
                print(f"  Inference Profiles取得エラー: {str(e)}")
            
            # Claude 3.5 Sonnetの具体的なモデルIDを試す
            print("\n\nClaude 3.5 Sonnetモデルのテスト:")
            print("-" * 40)
            
            # 試すモデルID
            test_model_ids = [
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                f"{region}.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
                "anthropic.claude-3-sonnet-20240307-v1:0",
                "anthropic.claude-3-5-sonnet-v2:0",
                "anthropic.claude-3-5-sonnet-v1:0"
            ]
            
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
            
            for model_id in test_model_ids:
                try:
                    # 簡単なテストリクエストを送信
                    test_request = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 10,
                        "messages": [
                            {
                                "role": "user",
                                "content": "Hello"
                            }
                        ]
                    }
                    
                    response = bedrock_runtime.invoke_model(
                        modelId=model_id,
                        contentType='application/json',
                        accept='application/json',
                        body=json.dumps(test_request)
                    )
                    
                    print(f"✅ {model_id} - 成功!")
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    error_message = e.response['Error']['Message']
                    
                    if error_code == 'ValidationException':
                        if 'on-demand throughput' in error_message:
                            print(f"⚠️  {model_id} - Inference Profile必要")
                        else:
                            print(f"❌ {model_id} - ValidationException: {error_message}")
                    elif error_code == 'AccessDeniedException':
                        print(f"🔒 {model_id} - アクセス拒否 (モデルアクセスを有効化してください)")
                    elif error_code == 'ResourceNotFoundException':
                        print(f"❌ {model_id} - モデルが見つかりません")
                    else:
                        print(f"❌ {model_id} - {error_code}: {error_message}")
                        
                except Exception as e:
                    print(f"❌ {model_id} - エラー: {str(e)}")
            
        except NoCredentialsError:
            print(f"エラー: AWS認証情報が見つかりません。")
            print("以下のいずれかの方法で認証情報を設定してください:")
            print("1. aws configure コマンドを実行")
            print("2. 環境変数 AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY を設定")
            print("3. ~/.aws/credentials ファイルを作成")
            break
            
        except ClientError as e:
            print(f"エラー: {e.response['Error']['Message']}")
            
        except Exception as e:
            print(f"予期しないエラー: {str(e)}")

def check_model_access():
    """モデルアクセスの状態を確認"""
    print("\n\n" + "="*80)
    print("モデルアクセス状態の確認")
    print("="*80)
    
    try:
        # デフォルトリージョンでチェック
        region = boto3.Session().region_name or 'us-east-1'
        bedrock = boto3.client('bedrock', region_name=region)
        
        # モデルアクセス状態を確認（このAPIが存在する場合）
        try:
            if hasattr(bedrock, 'get_model_access_status'):
                response = bedrock.get_model_access_status()
                print(f"\nモデルアクセス状態 (リージョン: {region}):")
                print(json.dumps(response, indent=2, default=str))
        except:
            pass
        
        # 推奨事項
        print("\n\n推奨事項:")
        print("-" * 40)
        print("1. AWS Bedrockコンソールでモデルアクセスを確認:")
        print("   https://console.aws.amazon.com/bedrock/home#/modelaccess")
        print("\n2. Claude 3.5 Sonnetへのアクセスをリクエスト")
        print("\n3. 環境変数でモデルIDを設定:")
        print("   export BEDROCK_MODEL_ID='us.anthropic.claude-3-5-sonnet-20241022-v2:0'")
        print("\n4. リージョンを確認:")
        print("   export AWS_DEFAULT_REGION='us-east-1'")
        
    except Exception as e:
        print(f"モデルアクセス確認エラー: {str(e)}")

if __name__ == "__main__":
    print("AWS Bedrock Claude 3.5 Sonnetモデル調査スクリプト")
    print("=" * 80)
    
    # Bedrockモデルをチェック
    check_bedrock_models()
    
    # モデルアクセス状態を確認
    check_model_access()
    
    print("\n\n完了しました。")