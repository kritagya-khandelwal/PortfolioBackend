#!/bin/bash

# PortfolioBackend - Startup Script

echo "🚀 Starting PortfolioBackend..."

# Check if OPENAI_API_KEY is set
# if [ -z "$OPENAI_API_KEY" ]; then
#     echo "❌ Error: OPENAI_API_KEY environment variable is not set"
#     echo "Please set your OpenAI API key:"
#     echo "export OPENAI_API_KEY='your-api-key-here'"
#     exit 1
# fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Install dependencies if pyproject.toml exists
if [ -f "pyproject.toml" ]; then
    echo "📦 Installing dependencies with uv..."
    uv sync
fi

# Start the FastAPI server
echo "🌐 Starting server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run python main.py 