# LINE BOT × AWS Bedrock 晩御飯提案BOT

ユーザーがLINEで食材を送ると、AWS Bedrock（Claude 3）を使って晩御飯のメニューを提案するBOTです。

## 🚀 機能

- 食材からAIが晩御飯メニューを2-3個提案
- Flex Messageを使った見やすいUI（設定で切り替え可能）
- AWS Lambda + API Gatewayでサーバーレス構成
- エラーハンドリングとロギング機能

## 📋 セットアップ手順

### 1. LINE Developersでチャネル作成

1. [LINE Developers Console](https://developers.line.biz/console/)にログイン
2. 新規プロバイダーを作成（または既存のものを選択）
3. 新規チャネルを作成（Messaging API）
4. チャネル基本設定から以下を取得：
   - Channel access token
   - Channel secret

### 2. AWS環境の準備

#### 必要なAWSサービス
- AWS Lambda
- API Gateway（またはLambda Function URL）
- AWS Bedrock（Claude 3へのアクセス権限）
- IAM（適切な権限設定）
- Systems Manager Parameter Store（オプション：トークン管理用）

#### IAMロールの作成
Lambda実行用のIAMロールに以下のポリシーをアタッチ：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "arn:aws:bedrock:*:*:model/anthropic.claude-3-sonnet*"
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

### 3. Lambda関数のデプロイ

#### 方法1: ZIPファイルでアップロード

```bash
# 依存関係をインストール
pip install -r requirements.txt -t .

# ZIPファイルを作成
zip -r lambda_function.zip .

# AWS CLIでアップロード（またはコンソールから）
aws lambda update-function-code --function-name your-function-name --zip-file fileb://lambda_function.zip
```

#### 方法2: Lambda Layerを使用

1. 依存関係用のLayerを作成：
```bash
mkdir python
pip install -r requirements.txt -t python/
zip -r layer.zip python
```

2. Layerをアップロードし、Lambda関数にアタッチ

### 4. 環境変数の設定

Lambda関数の環境変数に以下を設定：

| 変数名 | 説明 | 必須 |
|--------|------|------|
| LINE_CHANNEL_ACCESS_TOKEN | LINEチャネルアクセストークン | ✓ |
| LINE_CHANNEL_SECRET | LINEチャネルシークレット | ✓ |
| AWS_REGION | AWS Bedrockのリージョン | ✓ |
| USE_FLEX_MESSAGE | Flex Messageを使用するか（true/false） | - |

### 5. API GatewayまたはLambda Function URLの設定

#### Lambda Function URLを使用する場合（推奨）
1. Lambda関数の設定から「Function URL」を有効化
2. 認証タイプを「NONE」に設定
3. 生成されたURLをコピー

#### API Gatewayを使用する場合
1. REST APIを作成
2. POSTメソッドを追加し、Lambda関数と統合
3. デプロイしてエンドポイントURLを取得

### 6. LINE Webhook URLの設定

1. LINE Developers Consoleに戻る
2. Messaging API設定でWebhook URLに上記で取得したURLを設定
3. Webhookを有効化
4. 「Verify」ボタンで接続確認

## 🧪 動作確認

1. LINE公式アカウントを友だち追加
2. 食材をメッセージで送信
   - 例：「キャベツと鶏むね肉」
   - 例：「豚肉、にんじん、玉ねぎがあります」
3. BOTからメニュー提案が返ってくることを確認

## 📁 プロジェクト構成

```
.
├── app.py              # メインのLambdaハンドラー
├── recipe_parser.py    # レシピテキスト解析ユーティリティ
├── flex_message.py     # Flex Message作成ユーティリティ
├── requirements.txt    # Python依存関係
├── .env.example       # 環境変数のテンプレート
└── README.md          # このファイル
```

## 🔧 カスタマイズ

### プロンプトの調整

`app.py`の`generate_recipe_suggestion`関数内のプロンプトを編集することで、レシピ提案の精度や形式を調整できます。

### Flex Messageのデザイン変更

`flex_message.py`を編集して、メッセージのデザインやレイアウトをカスタマイズできます。

## ⚠️ 注意事項

- AWS Bedrockの利用料金が発生します
- LINE Messaging APIの無料枠を超えると料金が発生する場合があります
- 本番環境では適切なエラーハンドリングとセキュリティ対策を実施してください

## 🐛 トラブルシューティング

### Webhookの検証に失敗する場合
- Lambda関数のログを確認
- 環境変数が正しく設定されているか確認
- IAMロールの権限を確認

### レシピが生成されない場合
- AWS Bedrockへのアクセス権限を確認
- リージョン設定が正しいか確認
- Claude 3モデルが有効化されているか確認

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
