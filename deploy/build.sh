#!/bin/bash

# Lambda デプロイ用ZIPファイルを作成するスクリプト

set -e

echo "🔨 LINE Bot Lambda デプロイパッケージのビルドを開始します..."

# プロジェクトルートディレクトリを取得
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
PACKAGE_DIR="${BUILD_DIR}/package"
DEPLOYMENT_ZIP="${PROJECT_ROOT}/deployment.zip"

# 既存のビルドディレクトリをクリーンアップ
echo "📁 ビルドディレクトリをクリーンアップしています..."
rm -rf "${BUILD_DIR}"
rm -f "${DEPLOYMENT_ZIP}"

# ビルドディレクトリを作成
mkdir -p "${PACKAGE_DIR}"

# 依存関係をインストール
echo "📦 依存関係をインストールしています..."
pip install -r "${PROJECT_ROOT}/requirements.txt" -t "${PACKAGE_DIR}" --upgrade

# アプリケーションコードをコピー
echo "📋 アプリケーションコードをコピーしています..."
cp -r "${PROJECT_ROOT}/app" "${PACKAGE_DIR}/"

# 不要なファイルを削除
echo "🧹 不要なファイルを削除しています..."
find "${PACKAGE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${PACKAGE_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true
find "${PACKAGE_DIR}" -type f -name "*.pyo" -delete 2>/dev/null || true
find "${PACKAGE_DIR}" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "${PACKAGE_DIR}" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# ZIPファイルを作成
echo "🗜️ ZIPファイルを作成しています..."
cd "${PACKAGE_DIR}"
zip -r "${DEPLOYMENT_ZIP}" . -x "*.git*" "*.DS_Store"

# ファイルサイズを確認
FILESIZE=$(ls -lh "${DEPLOYMENT_ZIP}" | awk '{print $5}')
echo "✅ デプロイパッケージが作成されました: ${DEPLOYMENT_ZIP} (${FILESIZE})"

# Lambda のサイズ制限チェック（50MB）
FILESIZE_BYTES=$(stat -f%z "${DEPLOYMENT_ZIP}" 2>/dev/null || stat -c%s "${DEPLOYMENT_ZIP}")
if [ ${FILESIZE_BYTES} -gt 52428800 ]; then
    echo "⚠️  警告: ZIPファイルが50MBを超えています。Lambda直接アップロードの制限を超えている可能性があります。"
    echo "    S3経由でのアップロードまたはLambda Layersの使用を検討してください。"
fi

# クリーンアップ
echo "🧹 一時ファイルをクリーンアップしています..."
rm -rf "${BUILD_DIR}"

echo "✨ ビルドが完了しました！"
echo ""
echo "次のステップ:"
echo "1. AWS CLIでLambda関数を更新:"
echo "   aws lambda update-function-code --function-name line-dinner-bot --zip-file fileb://${DEPLOYMENT_ZIP}"
echo ""
echo "2. または、AWS コンソールから ${DEPLOYMENT_ZIP} をアップロード"