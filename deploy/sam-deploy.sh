#!/bin/bash

# SAM CLI を使用したデプロイスクリプト

set -e

echo "🚀 SAM CLI を使用した晩御飯提案BOTのデプロイを開始します..."

# 必要な変数をチェック
if [ -z "$LINE_CHANNEL_ACCESS_TOKEN" ] || [ -z "$LINE_CHANNEL_SECRET" ]; then
    echo "❌ エラー: LINE設定が不完全です"
    echo "以下の環境変数を設定してください:"
    echo "- LINE_CHANNEL_ACCESS_TOKEN"
    echo "- LINE_CHANNEL_SECRET"
    echo ""
    echo "または、デプロイ時にパラメータで指定してください"
    exit 1
fi

# オプションのSlack設定
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-""}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET:-""}

# プロジェクトルートディレクトリに移動
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 プロジェクトディレクトリ: $PROJECT_ROOT"

# SAM CLI がインストールされているかチェック
if ! command -v sam &> /dev/null; then
    echo "❌ エラー: SAM CLI がインストールされていません"
    echo "インストール手順: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# AWS CLI がインストールされているかチェック
if ! command -v aws &> /dev/null; then
    echo "❌ エラー: AWS CLI がインストールされていません"
    echo "インストール手順: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# AWS認証情報をチェック
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ エラー: AWS認証情報が設定されていません"
    echo "以下のコマンドで設定してください:"
    echo "aws configure"
    exit 1
fi

echo "✅ 前提条件のチェックが完了しました"

# SAM build
echo "🔨 SAM build を実行しています..."
sam build

# SAM deploy
echo "🚀 SAM deploy を実行しています..."

# パラメータオーバーライドを構築
PARAM_OVERRIDES="LineChannelAccessToken=$LINE_CHANNEL_ACCESS_TOKEN LineChannelSecret=$LINE_CHANNEL_SECRET"

if [ -n "$SLACK_BOT_TOKEN" ] && [ "$SLACK_BOT_TOKEN" != "" ]; then
    PARAM_OVERRIDES="$PARAM_OVERRIDES SlackBotToken=$SLACK_BOT_TOKEN"
fi

if [ -n "$SLACK_SIGNING_SECRET" ] && [ "$SLACK_SIGNING_SECRET" != "" ]; then
    PARAM_OVERRIDES="$PARAM_OVERRIDES SlackSigningSecret=$SLACK_SIGNING_SECRET"
fi

sam deploy \
    --parameter-overrides "$PARAM_OVERRIDES" \
    --no-confirm-changeset \
    --resolve-s3

if [ $? -eq 0 ]; then
    echo "✅ デプロイが完了しました！"
    echo ""
    echo "📋 次のステップ:"
    echo "1. CloudFormation出力でWebhook URLを確認:"
    echo "   aws cloudformation describe-stacks --stack-name dinner-suggestion-bot --query 'Stacks[0].Outputs'"
    echo ""
    echo "2. LINE Developers ConsoleでWebhook URLを設定"
    echo "3. Slack App設定でRequest URLを設定"
    echo ""
    echo "4. 動作確認:"
    echo "   - LINEで食材を送信してテスト"
    echo "   - Slackで /dinner コマンドをテスト"
else
    echo "❌ デプロイに失敗しました"
    exit 1
fi