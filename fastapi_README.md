# FastAPI Implementation for Slack Bot

このファイルは、Lambda関数とは別に、FastAPIを使用してSlack Botを実行するための実装です。

## 概要

`slack_app.py` は、以下の機能を提供するFastAPIアプリケーションです：

- `/slack/events` - Slackイベント（メンション、DM）を処理
- `/slack/slash/dinner` - `/dinner` スラッシュコマンドを処理
- 既存のレシピサービスとの統合
- Slack署名検証

## セットアップ

1. **環境変数の設定**

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_SIGNING_SECRET="your-signing-secret"
export AWS_REGION="us-east-1"
export BEDROCK_MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
```

2. **依存関係のインストール**

```bash
pip install -r requirements.txt
```

3. **アプリケーションの起動**

```bash
python slack_app.py
```

または、uvicornを直接使用：

```bash
uvicorn slack_app:app --reload --host 0.0.0.0 --port 8000
```

## Slack Appの設定

### Event Subscriptions

1. Slack App設定ページで「Event Subscriptions」を有効化
2. Request URL: `https://your-domain.com/slack/events`
3. Subscribe to bot events:
   - `app_mention` - ボットがメンションされた時
   - `message.im` - DMを受信した時

### Slash Commands

1. Slack App設定ページで「Slash Commands」を追加
2. Command: `/dinner`
3. Request URL: `https://your-domain.com/slack/slash/dinner`
4. Short Description: 晩御飯のメニューを提案します
5. Usage Hint: [食材や気分]

### OAuth & Permissions

必要なBot Token Scopes:
- `chat:write` - メッセージを送信
- `commands` - スラッシュコマンドを受信
- `app_mentions:read` - メンションを読み取り
- `im:read` - DMを読み取り
- `im:history` - DM履歴を読み取り

## ローカル開発

ngrokを使用してローカル開発環境でテスト：

```bash
# FastAPIを起動
python slack_app.py

# 別のターミナルでngrokを起動
ngrok http 8000
```

ngrokのHTTPS URLをSlack Appの設定に使用してください。

## エンドポイント

### GET /
ヘルスチェック用エンドポイント

### POST /slack/events
Slackイベントを処理:
- URL検証チャレンジ
- アプリメンション
- ダイレクトメッセージ

### POST /slack/slash/dinner
`/dinner` スラッシュコマンドを処理

## Lambda vs FastAPI

| 項目 | Lambda | FastAPI |
|------|--------|---------|
| デプロイ | AWS Lambda | EC2/ECS/K8s等 |
| スケーリング | 自動 | 手動設定必要 |
| コスト | 使用分のみ | 常時稼働 |
| ローカル開発 | 複雑 | 簡単 |
| レスポンス時間 | コールドスタート有 | 常時高速 |

## トラブルシューティング

### 署名検証エラー
- `SLACK_SIGNING_SECRET`が正しく設定されているか確認
- リクエストのタイムスタンプが5分以内か確認

### メッセージが送信されない
- `SLACK_BOT_TOKEN`が正しく設定されているか確認
- Bot Token Scopesが適切に設定されているか確認

### イベントが受信されない
- Event SubscriptionsのURLが正しいか確認
- ngrokを使用している場合、URLが最新か確認