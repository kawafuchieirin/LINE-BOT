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
├── app/                    # Lambda関数本体
│   ├── __init__.py         # パッケージ初期化
│   ├── handler.py          # メインのLambdaハンドラー（エントリーポイント: lambda_handler）
│   ├── core/               # チャネル共通のコアロジック
│   │   ├── __init__.py
│   │   ├── claude_client.py  # AWS Bedrock Claude 3.5 Sonnet統合
│   │   └── recipe_service.py # レシピ生成サービス（気分/食材判定含む）
│   ├── handlers/           # チャネル別ハンドラー
│   │   ├── __init__.py
│   │   ├── line_handler.py   # LINE Messaging API用ハンドラー
│   │   └── slack_handler.py  # Slack API用ハンドラー
│   ├── utils/              # 共通ユーティリティ
│   │   ├── __init__.py
│   │   ├── config.py         # 環境変数設定管理
│   │   └── logger.py         # ロギング設定
│   ├── bedrock_client.py   # (後方互換性のため残存、将来削除予定)
│   ├── recipe_parser.py    # レシピテキスト解析ユーティリティ
│   ├── line_message.py     # LINEメッセージ処理ユーティリティ
│   ├── flex_message.py     # LINE Flex Message作成ユーティリティ
│   ├── slack_responder.py  # Slack即座レスポンス用Lambda関数
│   ├── recipe_processor.py # レシピ生成処理Lambda（本番用）
│   ├── recipe_processor_debug.py # レシピ生成処理Lambda（デバッグ用）
│   └── recipe_processor_simple.py # レシピ生成処理Lambda（シンプル版）
├── deploy/                 # デプロイ関連ファイル
│   ├── build.sh            # Lambda ZIPパッケージビルドスクリプト
│   ├── deploy_lambda.md    # 詳細なデプロイ手順書
│   ├── sam-deploy.sh       # SAM CLIデプロイスクリプト
│   └── sam-local.sh        # SAMローカル開発環境スクリプト
├── tests/                  # テストファイル
│   ├── test_local.py       # ローカルテスト用スクリプト
│   └── test_mood_mode.py   # 気分モード検出・プロンプト生成テスト
├── template.yaml          # AWS SAMテンプレート
├── samconfig.toml         # SAM CLI設定ファイル
├── requirements.txt        # Python依存関係
├── CLAUDE.md              # このファイル
└── README.md              # プロジェクトのメインドキュメント
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
# ローカルテストの実行
python tests/test_local.py

# 気分モード検出テストの実行
python tests/test_mood_mode.py
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
- **line-bot-sdk (3.5.0)**: LINE Messaging API SDK
- **boto3 (1.34.14)**: AWS SDK for Python (Bedrock接続用)
- **python-dotenv (1.0.0)**: 環境変数管理（開発環境用）
- **requests (2.31.0)**: HTTP requests library
- **slack-sdk (3.27.1)**: Slack SDK for Python (Slack統合用)

### Lambda Function Details

#### Main Lambda Function (LINE & Slack Events)
- **Handler**: `app.handler.lambda_handler`
- **Runtime**: Python 3.12
- **Memory**: 512 MB (推奨)
- **Timeout**: 30 seconds

#### Slack Responder Function (Slack 3秒ルール対応 - 同期版)
- **Handler**: `app.slack_responder_sync.lambda_handler`
- **Purpose**: Slackコマンドを同期的に処理し、3秒以内にレシピを生成して返答
- **Memory**: 512 MB
- **Timeout**: 3 seconds (Slack 3秒ルール準拠)
- **Note**: 2025年6月更新 - 非同期版から同期版に変更

#### Recipe Processor Function (廃止)
- **Status**: 2025年6月に廃止
- **理由**: Slack同期版実装により不要となった
- **旧Handler**: `app.recipe_processor.lambda_handler`

### AWS SAM Architecture
このプロジェクトはAWS SAM (Serverless Application Model)を使用しており、`template.yaml`でインフラをコード化しています。2025年6月にSlack同期版に更新し、シンプルな構成になりました。

### Key Components

1. **app/handler.py**
   - Lambda関数のエントリーポイント
   - リクエストのチャネル判定（LINE/Slack）
   - 適切なハンドラーへのルーティング
   - 共通エラーハンドリング

2. **app/core/claude_client.py**
   - Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0) への接続
   - チャネル非依存のAI生成処理
   - Bedrock APIエラーハンドリング

3. **app/core/recipe_service.py**
   - 気分ベース/食材ベースの入力判定
   - 適切なプロンプトテンプレートの選択
   - レシピ生成とレスポンス解析
   - チャネル横断的なロギング

4. **app/handlers/line_handler.py**
   - LINE Webhookイベントの処理
   - LINE署名検証
   - LINE Bot APIを使用した返信
   - Flex Messageフォーマット対応

5. **app/handlers/slack_handler.py**
   - Slackスラッシュコマンド処理
   - Slackイベント（mentions, DMs）処理
   - Slack署名検証
   - Block Kitフォーマット対応

6. **app/utils/config.py**
   - 環境変数の一元管理
   - チャネル別設定の検証

7. **app/utils/logger.py**
   - 構造化ログの設定
   - チャネル横断的なログフォーマット

### Environment Variables Required

#### Common Variables
- `AWS_REGION`: AWS Bedrockのリージョン（デフォルト: us-east-1）
- `LOG_LEVEL`: ログレベル（DEBUG/INFO/WARNING/ERROR、デフォルト: INFO）
- `BEDROCK_MODEL_ID`: 使用するモデルID（デフォルト: anthropic.claude-3-5-sonnet-20241022-v2:0）

#### LINE Channel Variables
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Messaging APIのアクセストークン
- `LINE_CHANNEL_SECRET`: Webhook署名検証用のシークレット
- `USE_FLEX_MESSAGE`: Flex Messageを使用するか（true/false、デフォルト: true）

#### Slack Channel Variables
- `SLACK_BOT_TOKEN`: Slack Bot Userトークン
- `SLACK_SIGNING_SECRET`: Slack署名検証用のシークレット
- `SLACK_APP_TOKEN`: Slack Appトークン（Socket Mode使用時）

## Important Implementation Notes

### Import Paths
appディレクトリ内のモジュール間でインポートする際は、相対インポートを使用：
```python
# ハンドラーからコアモジュールをインポート
from ..core.recipe_service import create_recipe_service
from ..utils.config import config
from ..utils.logger import setup_logger

# 同一階層のモジュールをインポート
from .recipe_parser import parse_recipe_text
from .flex_message import create_recipe_flex_message
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
- [ ] Lambda関数の環境変数を設定
- [ ] CloudWatch Logsでエラーを確認
- [ ] LINE Developers ConsoleでWebhook URLを更新
- [ ] LINE公式アカウントで動作確認
- [ ] Slack AppでRequest URLを設定
- [ ] Slackワークスペースで動作確認

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
- モデルIDを`anthropic.claude-3-5-sonnet-20241022-v2:0`に更新
- より自然で多様なレシピ提案が可能に
- プロンプトテンプレートをClaude 3.5用に最適化

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