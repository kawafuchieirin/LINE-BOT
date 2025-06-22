# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based LINE Bot project that integrates AI capabilities using AWS Bedrock (Claude 3.5 Sonnet) to suggest dinner recipes based on either:
1. **Ingredients** provided by users (e.g., "鶏肉とキャベツ")
2. **Mood/Feeling** expressed by users (e.g., "さっぱりしたものが食べたい", "夏バテで食欲ない")

The Lambda function is deployed on AWS and processes webhook events from LINE.

## Directory Structure

```
LINE-BOT/
├── app/                 # Lambda関数本体
│   ├── __init__.py      # パッケージ初期化
│   ├── handler.py       # メインのLambdaハンドラー（エントリーポイント: lambda_handler）
│   ├── bedrock_client.py # AWS Bedrock Claude 3.5 Sonnet統合（気分モード対応）
│   ├── recipe_parser.py # レシピテキスト解析ユーティリティ
│   ├── line_message.py  # LINEメッセージ処理ユーティリティ
│   └── flex_message.py  # LINE Flex Message作成ユーティリティ
├── deploy/              # デプロイ関連ファイル
│   ├── build.sh         # Lambda ZIPパッケージビルドスクリプト
│   └── deploy_lambda.md # 詳細なデプロイ手順書
├── tests/               # テストファイル
│   └── test_local.py    # ローカルテスト用スクリプト
├── requirements.txt     # Python依存関係
├── CLAUDE.md           # このファイル
└── README.md           # プロジェクトのメインドキュメント
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
- **boto3 (1.28.57)**: AWS SDK for Python (Bedrock接続用)
- **python-dotenv (1.0.0)**: 環境変数管理（開発環境用）

### Lambda Function Details
- **Handler**: `app.handler.lambda_handler`
- **Runtime**: Python 3.11
- **Memory**: 512 MB (推奨)
- **Timeout**: 30 seconds

### Key Components

1. **app/handler.py**
   - Lambda関数のエントリーポイント
   - LINE Webhookイベントの処理
   - AWS Bedrockへのリクエスト送信
   - エラーハンドリング

2. **app/bedrock_client.py**
   - Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0) への接続
   - 気分ベース/食材ベースの入力判定
   - 適切なプロンプトテンプレートの選択
   - APIレスポンスの処理

3. **app/recipe_parser.py**
   - Bedrockからのレスポンステキストを解析
   - レシピ情報の構造化

4. **app/flex_message.py**
   - LINE Flex Messageの作成
   - リッチなUIでレシピを表示

### Environment Variables Required
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Messaging APIのアクセストークン
- `LINE_CHANNEL_SECRET`: Webhook署名検証用のシークレット
- `AWS_REGION`: AWS Bedrockのリージョン（デフォルト: us-east-1）
- `USE_FLEX_MESSAGE`: Flex Messageを使用するか（true/false、デフォルト: true）

## Important Implementation Notes

### Import Paths
appディレクトリ内のモジュール間でインポートする際は、相対インポートを使用：
```python
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
- `bedrock_client.py`の`_is_mood_based_input()`メソッドで入力を分類
- 気分ベースの場合は専用のプロンプトテンプレートを使用
- CloudWatch Logsで「mood-based」または「ingredient-based」として記録

### Claude 3.5 Sonnet 対応
- モデルIDを`anthropic.claude-3-5-sonnet-20241022-v2:0`に更新
- より自然で多様なレシピ提案が可能に
- プロンプトテンプレートをClaude 3.5用に最適化