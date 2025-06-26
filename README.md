# 多チャネル対応 晩御飯提案BOT

LINE・Slackの両方で使える、AWS Bedrock（Claude 3.5 Sonnet）を使った晩御飯メニュー提案BOTです。食材や気分を伝えると、AIが美味しいメニューを提案します。

## 🚀 機能

- **マルチチャネル対応**: LINE・Slack両方で動作
- **2つの提案モード**:
  - 食材ベース：「鶏肉とキャベツ」→ レシピ提案
  - 気分ベース：「さっぱりしたものが食べたい」→ 気分に合うメニュー提案
- **リッチUI**: LINE Flex Message、Slack Block Kit対応
- **サーバーレス構成**: AWS Lambda + API Gateway
- **3秒レスポンス対応**: Slackの制限に最適化

## 📱 対応プラットフォーム

### LINE
- Webhookメッセージ対応
- Flex Message表示
- 署名検証済み

### Slack
- スラッシュコマンド（`/dinner`）対応
- メンション・DM対応
- Block Kit表示
- 署名検証済み

## 📋 セットアップ手順

### 1. LINE Developersでチャネル作成

1. [LINE Developers Console](https://developers.line.biz/console/)にログイン
2. 新規プロバイダーを作成（または既存のものを選択）
3. 新規チャネルを作成（Messaging API）
4. チャネル基本設定から以下を取得：
   - Channel access token
   - Channel secret

### 2. Slack Appの作成

1. [Slack API](https://api.slack.com/apps)でアプリを作成
2. OAuth & Permissions:
   - `chat:write` - メッセージ送信
   - `commands` - スラッシュコマンド受信
   - `app_mentions:read` - メンション読み取り
   - `im:read` - DM読み取り
3. Slash Commands:
   - Command: `/dinner`
   - Request URL: Lambda関数のURL
4. Event Subscriptions:
   - Request URL: Lambda関数のURL
   - Subscribe to bot events: `app_mention`, `message.im`
5. 以下を取得：
   - Bot User OAuth Token
   - Signing Secret

### 3. AWS環境の準備

#### 必要なAWSサービス
- AWS Lambda
- API Gateway
- AWS Bedrock（Claude 3.5 Sonnet）
- IAM（適切な権限設定）

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
            "Resource": "arn:aws:bedrock:*:*:model/*anthropic.claude-3-5-sonnet*"
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

### 4. SAMでのデプロイ（推奨）

```bash
# 環境変数を設定
export LINE_CHANNEL_ACCESS_TOKEN="your-line-token"
export LINE_CHANNEL_SECRET="your-line-secret"
export SLACK_BOT_TOKEN="your-slack-token"
export SLACK_SIGNING_SECRET="your-slack-secret"

# SAM CLIでデプロイ
sam build
sam deploy --parameter-overrides "LineChannelAccessToken=$LINE_CHANNEL_ACCESS_TOKEN LineChannelSecret=$LINE_CHANNEL_SECRET"
```

### 5. 環境変数の設定

Lambda関数の環境変数に以下を設定：

| 変数名 | 説明 | 必須 |
|--------|------|------|
| LINE_CHANNEL_ACCESS_TOKEN | LINEチャネルアクセストークン | ✓ |
| LINE_CHANNEL_SECRET | LINEチャネルシークレット | ✓ |
| SLACK_BOT_TOKEN | Slack Bot User OAuth Token | ✓ |
| SLACK_SIGNING_SECRET | Slack Signing Secret | ✓ |
| AWS_REGION | AWS Bedrockのリージョン | - |
| BEDROCK_MODEL_ID | Bedrockモデル ID | - |
| USE_FLEX_MESSAGE | Flex Messageを使用するか | - |

### 6. Webhook URLの設定

SAMデプロイ後に出力されるURLを設定：

- **LINE**: `https://xxx.execute-api.region.amazonaws.com/prod/line`
- **Slack**: `https://xxx.execute-api.region.amazonaws.com/prod/slack`

## 🧪 動作確認

### LINE
1. LINE公式アカウントを友だち追加
2. メッセージを送信：
   - 食材例：「キャベツと鶏むね肉」
   - 気分例：「さっぱりしたものが食べたい」

### Slack
1. ワークスペースにアプリをインストール
2. コマンドを実行：
   - `/dinner キャベツと鶏肉`
   - `/dinner 夏バテで食欲ない`

## 📁 プロジェクト構成

```
app/
├── handler.py          # メインLambdaハンドラー（ルーティング）
├── line_bot.py         # LINE Bot専用ロジック
├── slack_bot.py        # Slack Bot専用ロジック
├── recipe_service.py   # レシピ生成（Claude統合）
├── config.py           # 設定管理
└── requirements.txt    # 依存関係

deploy/                 # デプロイ関連ファイル
├── build.sh           # ビルドスクリプト
├── sam-deploy.sh      # SAMデプロイスクリプト
└── sam-local.sh       # ローカル開発スクリプト

tests/                 # テストファイル
├── test_local.py      # ローカルテスト
└── test_mood_mode.py  # 気分モードテスト

template.yaml          # AWS SAMテンプレート
samconfig.toml         # SAM設定
requirements.txt       # プロジェクト依存関係
```

## 🔧 カスタマイズ

### プロンプトの調整

`app/recipe_service.py`の`_create_ingredient_based_prompt`または`_create_mood_based_prompt`を編集してレシピ提案をカスタマイズできます。

### UIのカスタマイズ

- **LINE**: `app/line_bot.py`の`_create_flex_message`を編集
- **Slack**: `app/slack_bot.py`の`_format_slack_response`を編集

## 🧪 ローカル開発

```bash
# SAMローカル開発環境
cd deploy
./sam-local.sh

# 単体テスト
python tests/test_local.py
python tests/test_mood_mode.py
```

## ⚠️ 注意事項

- AWS Bedrockの利用料金が発生します
- LINE Messaging API・Slack APIの利用制限にご注意ください
- 本番環境では適切なセキュリティ対策を実施してください

## 🐛 トラブルシューティング

### Webhookの検証に失敗する場合
- CloudWatch Logsを確認
- 環境変数が正しく設定されているか確認
- 署名検証の設定を確認

### レシピが生成されない場合
- AWS Bedrockへのアクセス権限を確認
- モデルIDが正しいか確認（inference profile形式）
- リージョン設定を確認

### Slackで3秒タイムアウトが発生する場合
- `max_tokens=800`で制限済み
- CloudWatch Logsで実際の処理時間を確認

## 📝 更新履歴

### v2.0.0 (2025-06-26)
- **マルチチャネル対応**: Slack統合
- **気分モード追加**: 気分ベースの提案機能
- **アーキテクチャ簡素化**: ファイル数60%削減
- **Claude 3.5 Sonnet対応**: 最新モデル使用

### v1.0.0
- 初回リリース（LINEのみ対応）

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。