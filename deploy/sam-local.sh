#!/bin/bash

# SAM CLI を使用したローカル開発環境セットアップスクリプト

set -e

echo "🏠 SAM CLI を使用したローカル開発環境を開始します..."

# プロジェクトルートディレクトリに移動
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# .env ファイルが存在するかチェック
if [ ! -f ".env" ]; then
    echo "📋 .env ファイルが見つかりません。.env.example からコピーします..."
    cp .env.example .env
    echo "⚠️  .env ファイルを編集して、適切な値を設定してください"
fi

# 環境変数を読み込み
if [ -f ".env" ]; then
    echo "📖 .env ファイルから環境変数を読み込んでいます..."
    export $(grep -v '^#' .env | xargs)
fi

# SAM CLI がインストールされているかチェック
if ! command -v sam &> /dev/null; then
    echo "❌ エラー: SAM CLI がインストールされていません"
    echo "インストール手順: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# Docker がインストールされているかチェック
if ! command -v docker &> /dev/null; then
    echo "❌ エラー: Docker がインストールされていません"
    echo "SAM local には Docker が必要です"
    echo "インストール手順: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker が実行されているかチェック
if ! docker info &> /dev/null; then
    echo "❌ エラー: Docker が実行されていません"
    echo "Docker を起動してから再実行してください"
    exit 1
fi

echo "✅ 前提条件のチェックが完了しました"

# ローカル開発用の環境変数を設定
export LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN:-"test_line_token"}
export LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET:-"test_line_secret"}
export SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-"test_slack_token"}
export SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET:-"test_slack_secret"}

# SAM build
echo "🔨 SAM build を実行しています..."
sam build

# 実行モードを選択
echo ""
echo "実行モードを選択してください:"
echo "1) ローカルAPI サーバー起動 (推奨)"
echo "2) 単発テスト実行"
echo "3) ローカルLambda 起動"

read -p "選択してください (1-3): " mode

case $mode in
    1)
        echo "🌐 ローカルAPI サーバーを起動しています..."
        echo "API エンドポイント: http://localhost:3000"
        echo "利用可能なパス:"
        echo "- GET  http://localhost:3000/health"
        echo "- POST http://localhost:3000/webhook"
        echo "- POST http://localhost:3000/webhook/line"
        echo "- POST http://localhost:3000/webhook/slack"
        echo "- POST http://localhost:3000/webhook/slack/slash"
        echo ""
        echo "🛑 Ctrl+C で停止"
        sam local start-api --port 3000 --warm-containers EAGER
        ;;
    2)
        echo "🧪 テストイベントファイルを選択してください:"
        echo "1) LINE webhook テスト"
        echo "2) Slack slash command テスト"
        echo "3) Slack event テスト"
        echo "4) Health check テスト"
        
        read -p "選択してください (1-4): " test_mode
        
        case $test_mode in
            1)
                if [ -f "test-line-event.json" ]; then
                    echo "📤 LINE webhook テストを実行しています..."
                    sam local invoke DinnerSuggestionFunction --event test-line-event.json
                else
                    echo "❌ test-line-event.json が見つかりません"
                fi
                ;;
            2)
                if [ -f "test-slack-slash.json" ]; then
                    echo "📤 Slack slash command テストを実行しています..."
                    sam local invoke DinnerSuggestionFunction --event test-slack-slash.json
                else
                    echo "❌ test-slack-slash.json が見つかりません"
                fi
                ;;
            3)
                if [ -f "test-slack-event.json" ]; then
                    echo "📤 Slack event テストを実行しています..."
                    sam local invoke DinnerSuggestionFunction --event test-slack-event.json
                else
                    echo "❌ test-slack-event.json が見つかりません"
                fi
                ;;
            4)
                if [ -f "test-health-event.json" ]; then
                    echo "📤 Health check テストを実行しています..."
                    sam local invoke DinnerSuggestionFunction --event test-health-event.json
                else
                    echo "❌ test-health-event.json が見つかりません"
                fi
                ;;
            *)
                echo "❌ 無効な選択です"
                exit 1
                ;;
        esac
        ;;
    3)
        echo "🔧 ローカルLambda サーバーを起動しています..."
        echo "Lambda エンドポイント: http://localhost:3001"
        echo ""
        echo "テスト方法:"
        echo "sam local invoke DinnerSuggestionFunction --event test-line-event.json"
        echo ""
        echo "🛑 Ctrl+C で停止"
        sam local start-lambda --port 3001 --warm-containers EAGER
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac