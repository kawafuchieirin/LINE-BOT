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
│   └── flex_message.py     # LINE Flex Message作成ユーティリティ
├── deploy/                 # デプロイ関連ファイル
│   ├── build.sh            # Lambda ZIPパッケージビルドスクリプト
│   └── deploy_lambda.md    # 詳細なデプロイ手順書
├── tests/                  # テストファイル
│   └── test_local.py       # ローカルテスト用スクリプト
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
```

### Building for Lambda Deployment
```bash
# デプロイパッケージのビルド
cd deploy
chmod +x build.sh
./build.sh
```

## Architecture Notes

### Current Dependencies
- **line-bot-sdk (3.5.0)**: LINE Messaging API SDK
- **boto3 (1.34.14)**: AWS SDK for Python (Bedrock接続用)
- **python-dotenv (1.0.0)**: 環境変数管理（開発環境用）
- **requests (2.31.0)**: HTTP requests library
- **slack-sdk (3.27.1)**: Slack SDK for Python (Slack統合用)

### Lambda Function Details
- **Handler**: `app.handler.lambda_handler`
- **Runtime**: Python 3.12
- **Memory**: 512 MB (推奨)
- **Timeout**: 30 seconds

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

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.