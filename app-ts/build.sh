#!/bin/bash

# Build script for TypeScript Lambda function with claude-code-sdk-ts

echo "🔨 Building TypeScript Lambda function..."

# Change to app-ts directory
cd "$(dirname "$0")"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build TypeScript
echo "🏗️ Compiling TypeScript..."
npm run build

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf lambda-package
mkdir -p lambda-package

# Copy compiled code
cp -r dist/* lambda-package/

# Copy node_modules (excluding dev dependencies)
npm prune --production
cp -r node_modules lambda-package/

# Create zip file
cd lambda-package
zip -r ../claude-sdk-function.zip .
cd ..

# Clean up
rm -rf lambda-package

echo "✅ Build complete! Deployment package: claude-sdk-function.zip"
echo "📏 Package size: $(du -h claude-sdk-function.zip | cut -f1)"

# Restore all dependencies
npm install