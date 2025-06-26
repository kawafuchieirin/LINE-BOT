# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based multi-channel dinner suggestion bot that integrates AI capabilities using AWS Bedrock (Claude 3.5 Sonnet) to suggest dinner recipes based on either:
1. **Ingredients** provided by users (e.g., "鶏肉とキャベツ")
2. **Mood/Feeling** expressed by users (e.g., "さっぱりしたものが食べたい", "夏バテで食欲ない")

The Lambda function is deployed on AWS and supports multiple messaging channels:
- **LINE**: Webhook events from LINE Messaging API
- **Slack**: Slash commands (/dinner) and event subscriptions (mentions, DMs)

## Directory Structure

```
LINE-BOT/
├── app/                    # Lambda関数本体（フラット構造）
│   ├── handler.py          # 統合Lambda関数ハンドラー（エントリーポイント）
│   ├── line_bot.py         # LINE Bot実装
│   ├── slack_bot.py        # Slack Bot実装
│   ├── slack_instant_responder.py  # Slack 3秒ルール対応ハンドラー
│   ├── slack_async_processor.py    # Slack非同期レシピ生成処理
│   ├── recipe_service.py   # コアレシピ生成サービス（気分/食材判定含む）
│   ├── ingredient_storage.py # DynamoDB食材管理サービス
│   ├── claude_sdk_client.py # Claude SDK代替クライアント
│   ├── config.py           # 環境変数設定管理
│   └── requirements.txt    # Lambda固有の依存関係
├── app-ts/                 # TypeScript Lambda実装（代替バックエンド）
│   ├── src/
│   │   ├── index.ts        # TypeScript Lambda関数
│   │   └── services/
│   │       └── recipeService.ts
│   ├── build.sh            # TypeScriptビルドスクリプト
│   ├── package.json        # Node.js依存関係
│   └── tsconfig.json       # TypeScript設定
├── deploy/                 # デプロイ関連ファイル
│   ├── build.sh            # Lambda ZIPパッケージビルドスクリプト
│   ├── deploy_lambda.md    # 詳細なデプロイ手順書
│   ├── sam-deploy.sh       # SAM CLIデプロイスクリプト
│   └── sam-local.sh        # SAMローカル開発環境スクリプト
├── tests/                  # 包括的テストスイート
│   ├── test_local.py       # ローカルテスト用スクリプト
│   ├── test_mood_mode.py   # 気分モード検出・プロンプト生成テスト
│   └── test_ingredient_storage.py # DynamoDB食材管理テスト
├── test_bedrock_access.py  # Bedrock接続テスト
├── test_claude_3_5_sonnet.py # Claude 3.5 Sonnetモデル固有テスト
├── test_haiku_speed.py     # パフォーマンステスト
├── test_lambda_endpoint.py # Lambda APIエンドポイントテスト
├── test_recipe_generation.py # レシピ生成テスト
├── test_slack_slash_endpoint.py # Slackスラッシュコマンドテスト
├── slack_app.py            # FastAPI ローカル開発用サーバー
├── fastapi_README.md       # FastAPI実装ガイド
├── CLAUDE_SDK_INTEGRATION.md # TypeScript Claude SDK統合ガイド
├── template.yaml           # AWS SAMテンプレート
├── samconfig.toml          # SAM CLI設定ファイル
├── requirements.txt        # Python依存関係
├── CLAUDE.md               # このファイル
└── README.md               # プロジェクトのメインドキュメント
```

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
# 基本的なローカルテストの実行
python tests/test_local.py

# 気分モード検出テストの実行
python tests/test_mood_mode.py

# DynamoDB食材管理テストの実行
python tests/test_ingredient_storage.py

# Bedrock接続テスト
python test_bedrock_access.py

# Claude 3.5 Sonnetモデル固有テスト
python test_claude_3_5_sonnet.py

# パフォーマンステスト（Haiku速度比較）
python test_haiku_speed.py

# Lambda APIエンドポイントテスト
python test_lambda_endpoint.py

# レシピ生成機能テスト
python test_recipe_generation.py

# Slackスラッシュコマンドテスト
python test_slack_slash_endpoint.py

# 利用可能なBedrockモデル確認
python check_bedrock_models.py
```

### FastAPI Local Development
```bash
# FastAPIローカルサーバーの起動（Lambda代替）
pip install fastapi uvicorn
python slack_app.py

# または
uvicorn slack_app:app --reload --port 8000
```

### TypeScript Build Commands
```bash
# TypeScript Lambda関数のビルド
cd app-ts
chmod +x build.sh
./build.sh

# TypeScript ローカルテスト
cd app-ts
node test-local.js
```

### Building for Lambda Deployment
```bash
# デプロイパッケージのビルド
cd deploy
chmod +x build.sh
./build.sh
```

### SAM Deployment
```bash
# 環境変数を設定
export LINE_CHANNEL_ACCESS_TOKEN="your-line-token"
export LINE_CHANNEL_SECRET="your-line-secret"
export SLACK_BOT_TOKEN="your-slack-token"  # Optional
export SLACK_SIGNING_SECRET="your-slack-secret"  # Optional

# SAM CLIでデプロイ
cd deploy
chmod +x sam-deploy.sh
./sam-deploy.sh

# または直接SAMコマンドを使用
sam build
sam deploy --parameter-overrides "LineChannelAccessToken=$LINE_CHANNEL_ACCESS_TOKEN LineChannelSecret=$LINE_CHANNEL_SECRET"
```

### Local Development with SAM
```bash
# ローカル開発環境の起動
cd deploy
chmod +x sam-local.sh
./sam-local.sh

# 直接SAMローカルサーバーを起動
sam build
sam local start-api --port 3000 --warm-containers EAGER

# 単発テスト実行（テストイベントファイルが必要）
sam local invoke DinnerSuggestionFunction --event test-line-event.json
```

## Architecture Notes

### Current Dependencies
- **line-bot-sdk (3.12.0)**: LINE Messaging API SDK
- **boto3 (1.35.0)**: AWS SDK for Python (Bedrock/DynamoDB接続用)
- **requests (2.32.0)**: HTTP requests library
- **fastapi**: FastAPI framework (local development)
- **uvicorn**: ASGI server (FastAPI用)

### Lambda Function Architecture

#### 1. Unified Handler Function (統合ハンドラー)
- **Handler**: `app.handler.lambda_handler`
- **Runtime**: Python 3.12
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Purpose**: LINE/Slack統合処理
- **Endpoints**: `/line`, `/slack`

#### 2. Slack Instant Responder Function (3秒ルール対応)
- **Handler**: `app.slack_instant_responder.lambda_handler`
- **Memory**: 512 MB
- **Timeout**: 3 seconds (Slack 3秒ルール準拠)
- **Purpose**: Slackスラッシュコマンドの即座レスポンス
- **Endpoint**: `/slack/slash`

#### 3. Slack Async Processor Function (非同期処理)
- **Handler**: `app.slack_async_processor.lambda_handler`
- **Memory**: 512 MB
- **Timeout**: 60 seconds
- **Purpose**: バックグラウンドでのレシピ生成とSlack投稿
- **Invocation**: Lambda間の非同期呼び出し

#### 4. TypeScript Claude SDK Function (無効化)
- **Handler**: `dist/index.handler` (Node.js 20.x)
- **Status**: 一時的に無効化（npm permissions issues）
- **Purpose**: Claude SDK (`@instantlyeasy/claude-code-sdk-ts`) を使用した代替実装
- **Endpoint**: `/claude-sdk` (commented out)

### DynamoDB Ingredient Storage
このプロジェクトには食材の永続化機能が組み込まれています。

#### DynamoDB Table構成
- **Table Name**: `DinnerBotIngredients`
- **Partition Key**: `user_id` (String)
- **Billing Mode**: PAY_PER_REQUEST（オンデマンド課金）

#### 食材管理機能
- **食材追加**: ユーザーが食材を登録・追加
- **食材一覧**: 登録済み食材の表示
- **食材クリア**: すべての食材を削除
- **重複排除**: 同じ食材の重複登録を自動防止

#### ingredient_storage.pyの主要メソッド
- `get_ingredients(user_id)`: ユーザーの食材を取得
- `add_ingredients(user_id, ingredients)`: 食材を追加
- `clear_ingredients(user_id)`: 食材をクリア
- `format_ingredients_list(ingredients)`: 表示用フォーマット

### AWS SAM Architecture
このプロジェクトはAWS SAM (Serverless Application Model)を使用しており、`template.yaml`でインフラをコード化しています。

#### インフラ構成
- **3つのLambda関数**: 統合ハンドラー、即座レスポンダー、非同期プロセッサー
- **1つのDynamoDB Table**: 食材管理用
- **HTTP API Gateway**: 複数エンドポイント（/line, /slack, /slack/slash）
- **IAM Roles**: Bedrock、DynamoDB、CloudWatch Logsへの最小権限アクセス

### Key Components

1. **app/handler.py**
   - 統合Lambda関数のエントリーポイント
   - リクエストのチャネル判定（LINE/Slack）
   - 適切なボットハンドラーへのルーティング
   - 共通エラーハンドリング

2. **app/recipe_service.py**
   - コアレシピ生成サービス
   - 気分ベース/食材ベースの入力判定
   - 適切なプロンプトテンプレートの選択
   - Bedrock Claude 3.5 Sonnet呼び出し
   - レシピ生成とレスポンス解析

3. **app/line_bot.py**
   - LINE Bot実装
   - LINE Webhookイベントの処理
   - LINE署名検証
   - LINE Bot APIを使用した返信
   - Flex Messageフォーマット対応

4. **app/slack_bot.py**
   - Slack Bot基本実装
   - Slackイベント（mentions, DMs）処理
   - Slack署名検証
   - Block Kitフォーマット対応

5. **app/slack_instant_responder.py**
   - Slack 3秒ルール対応ハンドラー
   - スラッシュコマンドの即座レスポンス
   - 非同期プロセッサーへのタスク移譲
   - Lambda間呼び出し処理

6. **app/slack_async_processor.py**
   - Slack非同期レシピ生成プロセッサー
   - バックグラウンドでのレシピ生成
   - Slack APIへの結果投稿
   - 長時間処理対応（60秒タイムアウト）

7. **app/ingredient_storage.py**
   - DynamoDB食材管理サービス
   - ユーザー別食材の永続化
   - CRUD操作（作成・読取・更新・削除）
   - 食材フォーマット処理

8. **app/config.py**
   - 環境変数の一元管理
   - チャネル別設定の検証
   - AWS設定とクレデンシャル管理

9. **app/claude_sdk_client.py**
   - Claude SDK代替クライアント
   - Bedrock以外のClaude接続オプション
   - 設定により切り替え可能（USE_CLAUDE_SDK環境変数）

### Environment Variables Required

#### Common Variables
- `AWS_REGION`: AWS Bedrockのリージョン（デフォルト: ap-northeast-1）
- `LOG_LEVEL`: ログレベル（DEBUG/INFO/WARNING/ERROR、デフォルト: INFO）
- `BEDROCK_MODEL_ID`: 使用するモデルID（デフォルト: anthropic.claude-3-5-sonnet-20240620-v1:0）
- `BEDROCK_REGION`: Bedrock専用リージョン設定（デフォルト: ap-northeast-1）
- `STAGE`: デプロイステージ（prod/dev/test、デフォルト: prod）

#### LINE Channel Variables
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Messaging APIのアクセストークン
- `LINE_CHANNEL_SECRET`: Webhook署名検証用のシークレット
- `USE_FLEX_MESSAGE`: Flex Messageを使用するか（true/false、デフォルト: true）

#### Slack Channel Variables
- `SLACK_BOT_TOKEN`: Slack Bot Userトークン
- `SLACK_SIGNING_SECRET`: Slack署名検証用のシークレット
- `ASYNC_PROCESSOR_FUNCTION_NAME`: 非同期処理用Lambda関数名（自動設定）

#### Alternative Backend Configuration
- `USE_CLAUDE_SDK`: Claude SDKを使用するか（true/false、デフォルト: false）

## Important Implementation Notes

### Import Paths
appディレクトリ内のモジュール間でインポートする際は、フラット構造のため直接インポートを使用：
```python
# 同一階層のモジュールをインポート（フラット構造）
from recipe_service import RecipeService
from ingredient_storage import IngredientStorage
from config import Config
from line_bot import LineBot
from slack_bot import SlackBot

# Lambda関数からの相対インポート（別Lambda関数から呼び出す場合）
from .recipe_service import RecipeService
from .ingredient_storage import IngredientStorage
```

### Error Handling
- すべての例外をキャッチしてユーザーフレンドリーなメッセージを返す
- CloudWatch Logsに詳細なエラー情報を記録
- Lambda関数は常に適切なHTTPステータスコードを返す

### Security Considerations
- LINE署名の検証を必ず実施
- 環境変数に機密情報を保存（ハードコーディングしない）
- IAMロールで最小権限の原則を適用

## Testing Guidelines

### Local Testing
`tests/test_local.py`を使用してローカルでテスト：
- レシピパーサーの単体テスト
- Bedrockへの接続テスト（AWS認証情報が必要）
- Lambda関数のイベント形式テスト

### Test Data
テスト用の食材例：
- "キャベツと鶏むね肉"
- "豚肉、にんじん、玉ねぎ"
- "卵とトマトとベーコン"
- "白菜と豆腐が残ってる"

テスト用の気分例：
- "さっぱりしたものが食べたい"
- "夏バテで食欲ないんだけど..."
- "ガッツリ系でスタミナつくもの"
- "こってり濃厚な気分"
- "ヘルシーで軽めがいい"

## Deployment Notes

### Lambda Deployment Package
`deploy/build.sh`スクリプトが以下を自動化：
1. 依存関係のインストール
2. アプリケーションコードのコピー
3. 不要なファイルの削除
4. ZIPファイルの作成
5. ファイルサイズの確認

### Post-Deployment Checklist
- [ ] Lambda関数の環境変数を設定（3つの関数すべて）
- [ ] DynamoDB Tableが正常に作成されていることを確認
- [ ] CloudWatch Logsでエラーを確認
- [ ] LINE Developers ConsoleでWebhook URLを更新 (`/line`)
- [ ] LINE公式アカウントで動作確認
- [ ] Slack AppでEvent Subscriptions URLを設定 (`/slack`)
- [ ] Slack AppでSlash Commands URLを設定 (`/slack/slash`)
- [ ] Slackワークスペースで動作確認
- [ ] 食材管理機能のテスト（追加・一覧・クリア）
- [ ] 3秒ルール対応の確認（Slackスラッシュコマンド）

## Common Issues and Solutions

### Issue: ModuleNotFoundError
**原因**: パッケージ構造が正しくない
**解決**: `app/__init__.py`が存在することを確認し、相対インポートを使用

### Issue: Webhook検証エラー
**原因**: LINE_CHANNEL_SECRETが正しく設定されていない
**解決**: 環境変数を確認し、LINE Developers Consoleの値と一致させる

### Issue: Bedrockタイムアウト
**原因**: レスポンス生成に時間がかかりすぎる
**解決**: Lambda関数のタイムアウト値を増やす（最大15分）

### Issue: Amazon Bedrock ValidationException または AccessDeniedException
**原因**: Claude 3.5 Sonnetモデルへのアクセス権限がない、または適切なinference profileを使用していない
**解決手順**:
1. **AWS Bedrockコンソールでモデルアクセスを有効化**:
   - [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/home#/modelaccess) にアクセス
   - 左メニューから「Model access」を選択
   - 「Anthropic Claude 3.5 Sonnet」のアクセスをリクエスト
   - アクセス承認まで数分～数時間かかる場合がある

2. **Inference Profileの使用**:
   ```python
   # 従来のモデルID (動作しない)
   "anthropic.claude-3-5-sonnet-20241022-v2:0"
   
   # Inference Profile (推奨)
   "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
   ```

3. **環境変数での設定**:
   ```bash
   export BEDROCK_MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
   ```

4. **診断スクリプトの実行**:
   ```bash
   python bedrock_test.py  # Bedrock接続テスト
   python check_accessible_models.py  # アクセス可能モデル確認
   ```

**エラーメッセージの対応**:
- `ValidationException: Invocation of model ID ... with on-demand throughput isn't supported` 
  → Inference Profileを使用する必要がある
- `AccessDeniedException: You don't have access to the model`
  → AWS Bedrockコンソールでモデルアクセスを有効化する必要がある

## New Features (2025年6月)

### マルチチャネル対応 (Multi-Channel Support)
複数のメッセージングプラットフォームに対応しました。

#### 対応チャネル
- **LINE**: 既存のLINE Bot機能を維持
- **Slack**: スラッシュコマンド（/dinner）とメンション対応

#### アーキテクチャの改善
- コアロジックとチャネル固有の処理を分離
- 共通の設定管理とロギング機構
- チャネル判定の自動化
- 新チャネル追加が容易な拡張可能な設計

### 気分モード (Mood Mode)
ユーザーの気分や食べたいものの雰囲気から晩御飯を提案する機能を追加しました。

#### 気分キーワードの例
- さっぱり/あっさり系
- こってり/ガッツリ系
- ヘルシー/軽め
- スタミナ/元気が出る
- 夏バテ/食欲ない
- 温まる/冷たい
- 和風/洋風/中華/エスニック

#### 実装詳細
- `core/recipe_service.py`の`_is_mood_based_input()`メソッドで入力を分類
- 気分ベースの場合は専用のプロンプトテンプレートを使用
- CloudWatch Logsで「mood」または「ingredient」として記録

### Claude 3.5 Sonnet 対応
- モデルIDを`anthropic.claude-3-5-sonnet-20240620-v1:0`に更新（template.yaml準拠）
- より自然で多様なレシピ提案が可能に
- プロンプトテンプレートをClaude 3.5用に最適化

## Multi-Backend Architecture (2025年6月追加)

### 3つの実装オプション

#### 1. AWS Bedrock Backend（主要実装）
- **技術スタック**: Python 3.12 + boto3 + AWS Bedrock
- **エンドポイント**: `/line`, `/slack`, `/slack/slash`
- **特徴**: 本番環境での安定性、AWS統合、DynamoDB食材管理
- **デプロイ**: AWS Lambda (SAM)

#### 2. Claude SDK Backend（TypeScript - 一時無効）
- **技術スタック**: Node.js 20.x + TypeScript + `@instantlyeasy/claude-code-sdk-ts`
- **エンドポイント**: `/claude-sdk` (commented out)
- **特徴**: 直接Claude API接続、TypeScript型安全性
- **状況**: npm permissions issuesにより一時的に無効化

#### 3. FastAPI Local Development Backend
- **技術スタック**: Python + FastAPI + uvicorn
- **用途**: ローカル開発・テスト環境
- **特徴**: 高速開発サイクル、Lambdaデプロイ不要
- **起動**: `python slack_app.py` または `uvicorn slack_app:app --reload`

### バックエンド切り替え
環境変数`USE_CLAUDE_SDK`でベdrock/Claude SDK間の切り替えが可能（現在Claude SDKは無効化）

### 食材管理の統合
すべてのバックエンドでDynamoDB食材管理機能を利用し、一貫したユーザー体験を提供

## Slack Integration Setup

### Slack App設定手順
1. [Slack API](https://api.slack.com/apps)でアプリを作成
2. OAuth & Permissions:
   - `chat:write` - メッセージ送信
   - `commands` - スラッシュコマンド受信
   - `app_mentions:read` - メンション読み取り
   - `im:read` - DM読み取り
3. Slash Commands:
   - Command: `/dinner`
   - Request URL: Lambda関数のURL
   - Description: 晩御飯のメニューを提案します
4. Event Subscriptions:
   - Request URL: Lambda関数のURL
   - Subscribe to bot events: `app_mention`, `message.im`
5. 環境変数の設定:
   - Bot User OAuth Token → `SLACK_BOT_TOKEN`
   - Signing Secret → `SLACK_SIGNING_SECRET`

## Extending to New Channels

新しいチャネルを追加する手順:

1. **ハンドラーの作成**
   ```python
   # app/handlers/new_channel_handler.py
   class NewChannelHandler:
       def __init__(self):
           self.recipe_service = create_recipe_service()
       
       def handle_request(self, body, headers):
           # チャネル固有の処理
           pass
   ```

2. **チャネル検出の追加**
   `app/handler.py`の`detect_channel()`関数に検出ロジックを追加

3. **ルーティングの追加**
   `app/handler.py`の`lambda_handler()`関数にルーティングを追加

4. **環境変数の追加**
   `app/utils/config.py`に新チャネルの設定を追加

## SAM Configuration

### samconfig.toml Settings
- **Stack Name**: `dinner-suggestion-bot`
- **Default Region**: `ap-northeast-1`
- **Build Settings**: Cached builds enabled for faster iteration
- **S3 Bucket**: Auto-resolved for deployment artifacts

### Missing Test Event Files
以下のテストイベントファイルは`sam-local.sh`で参照されていますが、現在存在しません。必要に応じて作成してください：
- `test-line-event.json` - LINE webhookイベントのテスト
- `test-slack-slash.json` - Slackスラッシュコマンドのテスト
- `test-slack-event.json` - Slackイベント（メンション、DM）のテスト
- `test-health-event.json` - ヘルスチェックのテスト

## Development Workflow

### Recommended Development Flow
1. **ローカル開発**: `sam-local.sh`でローカルAPIサーバーを起動
2. **テスト実行**: `test_local.py`と`test_mood_mode.py`で単体テスト
3. **SAMビルド**: `sam build`でLambda関数をビルド
4. **デプロイ**: `sam-deploy.sh`で本番環境にデプロイ
5. **動作確認**: CloudWatch Logsでエラーを確認

### Debugging Tips
- **Debug Handler**: 詳細なログが必要な場合は`recipe_processor_debug.py`を使用
- **Local Testing**: SAM localは実際のAWS環境を模倣するため、本番に近い環境でテスト可能

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.