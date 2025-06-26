# 🍽️ 冷蔵庫管理対応 晩御飯提案BOT

LINE・Slackの両方で使える、AWS Bedrock（Claude 3.5 Sonnet）を使った実用的な晩御飯メニュー提案BOTです。冷蔵庫の食材や気分を伝えると、AIが美味しいメニューを提案し、不足している調味料や小工材も教えてくれます。

## 🚀 主要機能

- **❄️ 冷蔵庫管理**: DynamoDBで冷蔵庫の食材を永続化・管理
- **🧠 インテリジェント提案**: 
  - 冷蔵庫の食材を活用したレシピ提案
  - 不足している調味料・小工材の明確な案内
  - 食材を無駄なく使えるメニュー優先
- **📱 マルチチャネル対応**: LINE・Slack両方で動作
- **2つの提案モード**:
  - **食材ベース**：「鶏肉とキャベツ」→ 冷蔵庫の食材でレシピ提案
  - **気分ベース**：「さっぱりしたものが食べたい」→ 気分に合うメニュー提案
- **⚡ 高速レスポンス**: Slack 3秒ルール対応の最適化済みアーキテクチャ
- **🎨 リッチUI**: LINE Flex Message、Slack Block Kit対応
- **☁️ サーバーレス構成**: AWS Lambda + API Gateway + DynamoDB

## 📱 対応プラットフォーム

### LINE
- Webhookメッセージ対応
- Flex Message表示
- 署名検証済み

### Slack
- スラッシュコマンド（`/dinner`）対応
- 冷蔵庫管理サブコマンド（add/list/stored/clear）
- メンション・DM対応  
- Block Kit表示
- 3秒ルール対応（非同期処理）
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
   - Request URL: `https://xxx.execute-api.region.amazonaws.com/prod/slack/slash`
   - Description: 冷蔵庫の食材で晩御飯のメニューを提案
4. Event Subscriptions:
   - Request URL: `https://xxx.execute-api.region.amazonaws.com/prod/slack`
   - Subscribe to bot events: `app_mention`, `message.im`
5. 以下を取得：
   - Bot User OAuth Token
   - Signing Secret

### 3. AWS環境の準備

#### 必要なAWSサービス
- **AWS Lambda** (3つの関数: 統合ハンドラー、即座レスポンダー、非同期プロセッサー)
- **API Gateway** (HTTP API)
- **AWS Bedrock** (Claude 3.5 Sonnet)
- **DynamoDB** (冷蔵庫食材保存用)
- **IAM** (適切な権限設定)

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
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/DinnerBotIngredients"
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
- **Slack Events**: `https://xxx.execute-api.region.amazonaws.com/prod/slack`
- **Slack Slash Commands**: `https://xxx.execute-api.region.amazonaws.com/prod/slack/slash`

## 🧪 動作確認

### LINE
1. LINE公式アカウントを友だち追加
2. メッセージを送信：
   - **冷蔵庫の食材で提案**：「キャベツと鶏むね肉」
   - **気分で提案**：「さっぱりしたものが食べたい」
   - **食材追加**：「追加 キャベツ 鶏肉」
   - **食材一覧**：「一覧」
   - **食材削除**：「削除」
   - **保存済み食材でレシピ**：「保存済み」

### Slack
1. ワークスペースにアプリをインストール
2. コマンドを実行：

#### 冷蔵庫管理
- `/dinner add キャベツ 鶏肉` - 冷蔵庫に食材を追加
- `/dinner list` - 冷蔵庫の食材を表示
- `/dinner stored` - 冷蔵庫の食材でレシピ生成
- `/dinner clear` - 冷蔵庫の食材をクリア

#### レシピ提案
- `/dinner キャベツと鶏肉` - 指定食材でレシピ提案
- `/dinner 夏バテで食欲ない` - 気分に合うメニュー提案

#### ヘルプ
- `/dinner` - 使い方を表示

## 📋 コマンド一覧

### 冷蔵庫管理
```bash
/dinner add トマト、卵、ベーコン    # 冷蔵庫に食材を追加
/dinner list                      # 冷蔵庫の食材を表示
/dinner stored                    # 冷蔵庫の食材でレシピ生成
/dinner clear                     # 冷蔵庫の食材をクリア
```

### レシピ提案
```bash
/dinner 鶏肉とキャベツ             # 指定食材でレシピ提案
/dinner さっぱりしたものが食べたい  # 気分でレシピ提案
```

## 💡 使用例

### 冷蔵庫管理の流れ
```bash
# 1. 冷蔵庫に食材を追加
/dinner add トマト、卵、ベーコン
→ ✅ 冷蔵庫に食材を追加しました！
   ❄️ 冷蔵庫の食材:
   1. トマト
   2. 卵  
   3. ベーコン

# 2. 冷蔵庫の食材でレシピ提案
/dinner stored
→ 🍽️ 冷蔵庫の食材（トマト, 卵, ベーコン）を使ったレシピを生成中です...
→ レシピ提案完了！
   1. [トマトとベーコンのオムレツ]
      卵をふんわりと焼き上げ、トマトとベーコンの旨味を包み込んだ朝食にぴったりの一品
      🛒 追加で必要: 塩、胡椒、バター
   
   2. [ベーコンとトマトのパスタ]
      シンプルながら奥深い味わいのイタリアン
      🛒 追加で必要: パスタ、オリーブオイル、ニンニク
```

### 直接食材指定の場合
```bash
/dinner 鶏むね肉とキャベツと玉ねぎ
→ 1. [鶏肉とキャベツの塩炒め]
     あっさりとした味付けでヘルシーな炒め物
     🛒 追加で必要: 塩、胡椒、ごま油
```

## 📁 プロジェクト構成

```
app/                    # Lambda関数本体（フラット構造）
├── handler.py          # 統合Lambda関数ハンドラー（エントリーポイント）
├── line_bot.py         # LINE Bot実装
├── slack_bot.py        # Slack Bot実装  
├── slack_instant_responder.py  # Slack 3秒ルール対応ハンドラー
├── slack_async_processor.py    # Slack非同期レシピ生成処理
├── recipe_service.py   # コアレシピ生成サービス（気分/食材判定含む）
├── ingredient_storage.py # DynamoDB冷蔵庫食材管理サービス
├── claude_sdk_client.py # Claude SDK代替クライアント
├── config.py           # 環境変数設定管理
└── requirements.txt    # Lambda固有の依存関係

app-ts/                 # TypeScript Lambda実装（代替バックエンド）
├── src/
│   ├── index.ts        # TypeScript Lambda関数
│   └── services/
│       └── recipeService.ts
├── build.sh            # TypeScriptビルドスクリプト
├── package.json        # Node.js依存関係
└── tsconfig.json       # TypeScript設定

deploy/                 # デプロイ関連ファイル
├── build.sh            # Lambda ZIPパッケージビルドスクリプト
├── deploy_lambda.md    # 詳細なデプロイ手順書
├── sam-deploy.sh       # SAM CLIデプロイスクリプト
└── sam-local.sh        # SAMローカル開発環境スクリプト

tests/                  # 包括的テストスイート
├── test_local.py       # ローカルテスト用スクリプト
├── test_mood_mode.py   # 気分モード検出・プロンプト生成テスト
└── test_ingredient_storage.py # DynamoDB冷蔵庫食材管理テスト

# その他のテストファイル
test_bedrock_access.py  # Bedrock接続テスト
test_claude_3_5_sonnet.py # Claude 3.5 Sonnetモデル固有テスト
test_haiku_speed.py     # パフォーマンステスト
test_lambda_endpoint.py # Lambda APIエンドポイントテスト
test_recipe_generation.py # レシピ生成テスト
test_slack_slash_endpoint.py # Slackスラッシュコマンドテスト

# プロジェクト設定ファイル
template.yaml           # AWS SAMテンプレート
samconfig.toml          # SAM CLI設定ファイル
requirements.txt        # Python依存関係
CLAUDE.md               # プロジェクト開発ガイド
README.md               # このファイル
```

## 🔧 カスタマイズ

### レシピ提案の調整

`app/recipe_service.py`の`_create_prompt`メソッドを編集：

```python
# 冷蔵庫食材ベースのプロンプト調整
# - 追加材料の提案方法
# - メニューの種類や数
# - 調理難易度の指定

# 気分ベースのプロンプト調整  
# - 気分キーワードの追加
# - 提案するメニューのテイスト
```

### UIのカスタマイズ

- **LINE**: `app/line_bot.py`のFlex Message形式
- **Slack**: `app/slack_async_processor.py`のBlock Kit形式

### 冷蔵庫管理のカスタマイズ

`app/ingredient_storage.py`でDynamoDB操作をカスタマイズ：
- 食材の有効期限管理
- カテゴリ別食材管理
- 食材の使用履歴

## 🧪 ローカル開発

### SAMローカル開発
```bash
# ローカルAPIサーバーの起動
cd deploy
./sam-local.sh

# または直接SAMコマンド
sam build
sam local start-api --port 3000 --warm-containers EAGER
```

### テスト実行
```bash
# 基本的なローカルテスト
python tests/test_local.py

# 気分モード検出テスト
python tests/test_mood_mode.py

# DynamoDB冷蔵庫食材管理テスト
python tests/test_ingredient_storage.py

# Bedrock接続テスト
python test_bedrock_access.py

# Claude 3.5 Sonnetモデル固有テスト
python test_claude_3_5_sonnet.py

# Slackスラッシュコマンドテスト
python test_slack_slash_endpoint.py
```

### FastAPI代替開発
```bash
# FastAPIローカルサーバー（Lambda代替）
pip install fastapi uvicorn
python slack_app.py
```

## ⚠️ 注意事項

- **AWS料金**: Bedrock、Lambda、DynamoDB、API Gatewayの利用料金が発生します
- **API制限**: LINE Messaging API・Slack APIの利用制限にご注意ください
- **セキュリティ**: 本番環境では適切なセキュリティ対策を実施してください
- **Bedrock利用**: Claude 3.5 Sonnetモデルへのアクセス許可が必要です
- **DynamoDB**: 冷蔵庫食材データは永続化されます（削除は手動で行ってください）

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
- 3秒ルール対応済み（非同期処理）
- `SlackInstantResponderFunction`が即座レスポンス
- `SlackAsyncProcessorFunction`がバックグラウンド処理
- CloudWatch Logsで実際の処理時間を確認

### `/dinner add`コマンドがレシピ生成される場合
- Slack App設定でRequest URLが正しいか確認
- Slash Command: `/prod/slack/slash`
- Event Subscriptions: `/prod/slack`

### 冷蔵庫の食材が保存されない場合
- DynamoDB Tableが正常に作成されているか確認
- Lambda関数にDynamoDB権限があるか確認
- CloudWatch Logsでエラーを確認

## 📝 更新履歴

### v2.2.0 (2025-06-26) - 冷蔵庫管理対応
- **🍽️ 冷蔵庫コンテキスト強化**: 全機能で冷蔵庫管理の文脈を明確化
- **🧠 インテリジェントレシピ提案**: 
  - 冷蔵庫の食材を活用したレシピ提案
  - 不足している調味料・小工材の明確な案内
  - 食材を無駄なく使えるメニュー優先
- **🛒 追加材料表示機能**: 足りない材料を「🛒 追加で必要: 醤油、みりん」として表示
- **⚡ Slack 3秒ルール対応**: `/dinner add`コマンドの修正（レシピ生成→食材追加）
- **📊 改良されたレスポンス解析**: 追加材料情報の自動抽出

### v2.1.0 (2025-06-26) - 食材管理機能
- **💾 DynamoDB食材保存**: 冷蔵庫の食材を永続化
- **📱 Slackサブコマンド**: add/list/stored/clear対応
- **🔄 LINE食材管理**: 統一された食材管理インターフェース

### v2.0.0 (2025-06-26) - マルチチャネル対応
- **📱 Slack統合**: マルチチャネルアーキテクチャ
- **🎭 気分モード**: 気分ベースの提案機能
- **⚡ 3つのLambda構成**: 統合ハンドラー、即座レスポンダー、非同期プロセッサー
- **🤖 Claude 3.5 Sonnet**: 最新AIモデル使用

### v1.0.0 - 初回リリース
- LINEのみ対応
- 基本的なレシピ提案機能

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。