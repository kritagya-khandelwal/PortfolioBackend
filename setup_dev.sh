#!/bin/bash

# Development Setup Script for PortfolioBackend

echo "🔧 Setting up development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Install main dependencies
echo "📦 Installing main dependencies..."
uv sync

# Install development dependencies
echo "🧪 Installing development dependencies..."
uv add --dev requests pytest black flake8

echo "✅ Development environment setup complete!"
echo ""
echo "You can now:"
echo "  - Run the server: ./start.sh"
echo "  - Test the API: uv run python test_client.py"
echo "  - Run tests: uv run pytest"
echo "  - Format code: uv run black ."
echo "  - Lint code: uv run flake8 ." 