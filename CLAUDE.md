# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based LINE Bot project that integrates AI capabilities using LangChain and OpenAI. The project is in its initial stages with core dependencies defined but implementation pending.

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
No test framework is currently configured. When implementing tests, consider using pytest for Python testing.

## Architecture Notes

### Current Dependencies
- **langchain (0.0.268)**: Framework for building applications with language models
- **openai (0.27.8)**: OpenAI API client for GPT model integration

### Missing Components for LINE Bot
The project currently lacks:
1. **line-bot-sdk**: Essential for LINE messaging API integration
2. Main application file (app.py or main.py)
3. Environment configuration (.env file)
4. LINE webhook handlers
5. Deployment configuration

### Expected Architecture
When fully implemented, the bot should follow this pattern:
1. **Web Framework**: Flask or FastAPI to handle LINE webhooks
2. **LINE Integration**: Handle messages, process events via LINE Bot SDK
3. **AI Processing**: Use LangChain to process user messages and generate responses
4. **Response Flow**: LINE → Webhook → LangChain/OpenAI → Response → LINE

### Environment Variables Required
When implementing, ensure these are configured:
- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `OPENAI_API_KEY`