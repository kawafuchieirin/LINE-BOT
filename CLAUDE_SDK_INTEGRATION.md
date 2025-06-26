# Claude SDK Integration

This document describes the integration of `@instantlyeasy/claude-code-sdk-ts` into the LINE-BOT project.

## Overview

The claude-code-sdk-ts has been integrated as an alternative backend for recipe generation, alongside the existing AWS Bedrock integration. This provides flexibility in choosing between:

1. **AWS Bedrock** (default): Direct API calls to Claude via AWS Bedrock
2. **Claude SDK**: Using the TypeScript SDK with the Claude CLI tool

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  LINE/Slack     │────▶│ Python Lambda    │
│   Webhook       │     │  (app/)          │
└─────────────────┘     └──────┬───────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Recipe Service   │
                    │ (USE_CLAUDE_SDK) │
                    └──────┬───────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ AWS Bedrock      │      │ Claude SDK Lambda│
    │ (Direct API)     │      │ (app-ts/)        │
    └──────────────────┘      └──────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ claude-code CLI  │
                              └──────────────────┘
```

## Setup Instructions

### 1. Install Dependencies (TypeScript Lambda)

```bash
cd app-ts
npm install
```

### 2. Build TypeScript Lambda

```bash
# Using the build script
cd app-ts
./build.sh

# Or manually
npm run build
```

### 3. Deploy with SAM

```bash
# Build and deploy
sam build
sam deploy
```

### 4. Enable Claude SDK Backend

To use the Claude SDK instead of AWS Bedrock, set the environment variable:

```bash
# In SAM template or Lambda console
USE_CLAUDE_SDK=true
```

## Configuration

### Environment Variables

#### For Python Lambda (app/)
- `USE_CLAUDE_SDK`: Set to "true" to use Claude SDK backend (default: "false")
- `HTTP_API_ID`: API Gateway ID (automatically set by SAM)
- `STAGE`: Deployment stage (prod/dev/test)

#### For TypeScript Lambda (app-ts/)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Testing

### Local Testing (TypeScript)

```bash
cd app-ts
# First build the project
npm run build

# Run local test
node test-local.js
```

### Testing via API

```bash
# Test the Claude SDK endpoint directly
curl -X POST https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/claude-sdk \
  -H "Content-Type: application/json" \
  -d '{
    "userInput": "キャベツと鶏むね肉",
    "channel": "test",
    "userId": "test-user"
  }'
```

## Usage Examples

### 1. Direct Claude SDK API Call

```python
from claude_sdk_client import ClaudeSDKClient

client = ClaudeSDKClient()
result = client.generate_recipe(
    user_input="さっぱりしたものが食べたい",
    channel="LINE",
    user_id="U123456"
)
```

### 2. Through Recipe Service (Auto-selection)

```python
from recipe_service import RecipeService

# Will use Claude SDK if USE_CLAUDE_SDK=true
service = RecipeService()
result = service.generate_recipe("キャベツと豚肉")
```

## Benefits of Claude SDK Integration

1. **Alternative Backend**: Provides a fallback option if AWS Bedrock is unavailable
2. **CLI Features**: Access to Claude CLI-specific features
3. **TypeScript Support**: Modern TypeScript development with type safety
4. **Flexibility**: Easy switching between backends via environment variable

## Limitations

1. **Requires Claude CLI**: The claude-code-sdk-ts requires the Claude CLI to be installed
2. **Different Authentication**: Uses Claude CLI authentication instead of AWS IAM
3. **Additional Lambda**: Requires a separate TypeScript Lambda function

## Troubleshooting

### Issue: Claude SDK Lambda not working
- Check if the TypeScript Lambda is deployed: Look for `{stack-name}-claude-sdk` in Lambda console
- Verify npm dependencies are installed
- Check CloudWatch logs for the Claude SDK Lambda function

### Issue: Cannot connect to Claude CLI
- Ensure Claude CLI is properly configured in the Lambda environment
- Check authentication with the Claude service

### Issue: Switching between backends
- Verify `USE_CLAUDE_SDK` environment variable is set correctly
- Restart/redeploy the Lambda function after changing the variable

## Future Enhancements

1. **Caching**: Implement response caching for common queries
2. **Metrics**: Add CloudWatch metrics for Claude SDK usage
3. **A/B Testing**: Use both backends and compare results
4. **Feature Flags**: More granular control over which features use which backend