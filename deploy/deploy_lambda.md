# AWS Lambda デプロイメントガイド

## 前提条件

- AWS CLIがインストール・設定済み
- Python 3.9以上
- LINE Developers アカウント
- AWS Bedrockへのアクセス権限

## デプロイ手順

### 1. Lambda関数の作成

AWS Lambdaコンソールまたは以下のCLIコマンドで関数を作成：

```bash
aws lambda create-function \
  --function-name line-dinner-bot \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler app.handler.lambda_handler \
  --timeout 30 \
  --memory-size 512
```

### 2. 依存関係のパッケージング

#### オプション1: build.shスクリプトを使用（推奨）

```bash
cd deploy
./build.sh
```

#### オプション2: 手動パッケージング

```bash
# プロジェクトルートで実行
pip install -r requirements.txt -t package/
cp -r app package/
cd package
zip -r ../deployment.zip . -x "*.git*" "__pycache__/*" "*.pyc"
```

#### オプション3: Docker を使用

```bash
# Dockerfileを作成
cat << EOF > Dockerfile
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

CMD ["app.handler.lambda_handler"]
EOF

# ビルドとプッシュ
docker build -t line-dinner-bot .
docker tag line-dinner-bot:latest YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/line-dinner-bot:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/line-dinner-bot:latest
```

### 3. Lambda関数の更新

ZIPファイルの場合：
```bash
aws lambda update-function-code \
  --function-name line-dinner-bot \
  --zip-file fileb://deployment.zip
```

Dockerイメージの場合：
```bash
aws lambda update-function-code \
  --function-name line-dinner-bot \
  --image-uri YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/line-dinner-bot:latest
```

### 4. 環境変数の設定

```bash
aws lambda update-function-configuration \
  --function-name line-dinner-bot \
  --environment Variables="{
    LINE_CHANNEL_ACCESS_TOKEN=your_token_here,
    LINE_CHANNEL_SECRET=your_secret_here,
    AWS_REGION=us-east-1,
    USE_FLEX_MESSAGE=true
  }"
```

### 5. Lambda Function URLの有効化

```bash
# Function URLを作成
aws lambda create-function-url-config \
  --function-name line-dinner-bot \
  --auth-type NONE

# URLを取得
aws lambda get-function-url-config \
  --function-name line-dinner-bot \
  --query FunctionUrl \
  --output text
```

### 6. 実行ロールの権限設定

以下のポリシーをLambda実行ロールにアタッチ：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": [
                "arn:aws:bedrock:*:*:model/anthropic.claude-3-sonnet*",
                "arn:aws:bedrock:*:*:model/anthropic.claude-3-haiku*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream", 
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### 7. CloudWatch Logsの確認

デプロイ後、以下のコマンドでログを確認：

```bash
aws logs tail /aws/lambda/line-dinner-bot --follow
```

## セキュリティのベストプラクティス

### 1. Parameter Storeを使用した秘密情報の管理

```python
import boto3

ssm = boto3.client('ssm')

def get_parameter(name):
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']

# 使用例
LINE_CHANNEL_ACCESS_TOKEN = get_parameter('/line-bot/channel-access-token')
```

### 2. API Gatewayでのレート制限

API Gatewayを使用する場合は、使用量プランを設定してレート制限を適用。

### 3. Lambda関数の同時実行数制限

```bash
aws lambda put-function-concurrency \
  --function-name line-dinner-bot \
  --reserved-concurrent-executions 100
```

## モニタリング設定

### CloudWatch アラーム

エラー率のアラーム設定：

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name line-dinner-bot-errors \
  --alarm-description "Lambda function error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=line-dinner-bot
```

## トラブルシューティング

### よくある問題と解決方法

1. **タイムアウトエラー**
   - Lambda関数のタイムアウト値を増やす（最大15分）
   - Bedrockのレスポンス時間を確認

2. **メモリ不足エラー**
   - Lambda関数のメモリサイズを増やす（512MB以上推奨）

3. **権限エラー**
   - IAMロールにBedrock関連の権限があるか確認
   - CloudWatch Logsへの書き込み権限を確認

4. **署名検証エラー**
   - LINE_CHANNEL_SECRETが正しく設定されているか確認
   - リクエストボディが正しく渡されているか確認