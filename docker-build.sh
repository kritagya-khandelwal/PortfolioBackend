#!/bin/bash

# PortfolioBackend Docker Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    cp env.example .env
    print_warning "Please update .env with your OpenAI API key before running the container."
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ] && ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    print_error "OPENAI_API_KEY not set in environment or .env file"
    print_error "Please set your OpenAI API key in .env file or export OPENAI_API_KEY"
    exit 1
fi

# Build the Docker image
print_status "Building PortfolioBackend Docker image..."
# docker rmi portfoliobackend:latest
docker build -t portfoliobackend:latest .

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully!"
    print_status "Image: portfoliobackend:latest"
    
    echo ""
    print_status "To run the container:"
    echo "  Development: docker-compose up"
    echo "  Production:  docker-compose -f docker-compose.prod.yml up"
    echo "  Standalone:  docker run -p 8000:8000 --env-file .env portfoliobackend:latest"
else
    print_error "Docker build failed!"
    exit 1
fi 