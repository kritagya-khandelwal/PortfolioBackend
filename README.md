# PortfolioBackend

A FastAPI backend service that provides streaming responses from OpenAI's GPT-4o-mini model with IP-based rate limiting.

## Features

- **Streaming Responses**: Real-time streaming of LLM responses
- **FastAPI**: Modern, fast web framework for building APIs
- **OpenAI Integration**: Direct integration with OpenAI's GPT-4o-mini model
- **Rate Limiting**: IP-based rate limiting using Redis (10 requests/day per IP)
- **Error Handling**: Comprehensive error handling and validation
- **Health Checks**: Built-in health check endpoint with Redis status
- **uv**: Fast Python package manager and installer
- **Docker Support**: Full containerization with Docker and Docker Compose
- **Redis Caching**: Redis integration for rate limiting and caching

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- uv (Python package manager)
- Docker (optional, for containerized deployment)
- Redis (optional, for local development)

### Local Development Setup

1. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or using pip
   pip install uv
   ```

2. Clone or navigate to the project directory:
   ```bash
   cd PortfolioBackend
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Set up your environment variables:
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Edit .env with your API keys
   nano .env
   ```

5. Start Redis (if running locally):
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Or install Redis locally
   # brew install redis  # macOS
   # sudo apt-get install redis-server  # Ubuntu
   ```

### Running the Service

Start the FastAPI server:
```bash
./start.sh
```

Or manually:
```bash
uv run python main.py
```

Or using uvicorn directly:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The service will be available at `http://localhost:8000`

## Docker Deployment

### Quick Start with Docker

1. **Build and run with Docker Compose (Recommended)**:
   ```bash
   # Build and start the service with Redis
   ./docker-build.sh
   docker-compose up
   ```

2. **Production deployment**:
   ```bash
   ./docker-build.sh
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Standalone Docker container** (requires external Redis):
   ```bash
   # Build the image
   docker build -t portfoliobackend:latest .
   
   # Run the container
   docker run -p 8000:8000 --env-file .env portfoliobackend:latest
   ```

### Docker Features

- **Multi-stage build** for optimized image size
- **Security**: Non-root user execution
- **Health checks** for container monitoring
- **Environment variable support** via `.env` file
- **Production optimizations** with resource limits
- **Read-only filesystem** for enhanced security
- **Redis integration** for rate limiting

### Docker Commands

```bash
# Build the image
./docker-build.sh

# Run in development mode (with Redis)
docker-compose up

# Run in production mode (with Redis)
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild and restart
docker-compose up --build

# Check Redis status
docker-compose exec redis redis-cli ping
```

## API Endpoints

### 1. Root Endpoint
- **URL**: `GET /`
- **Description**: Returns basic service information
- **Response**: JSON with service status

### 2. Streaming LLM Endpoint
- **URL**: `POST /stream`
- **Description**: Streams LLM response for a given prompt
- **Rate Limit**: 10 requests per day per IP address
- **Request Body**:
```json
{
    "prompt": "Your prompt string here"
}
```
- **Response**: Server-Sent Events (SSE) stream with JSON chunks including timestamps

### 3. Health Check
- **URL**: `GET /health`
- **Description**: Health check endpoint with Redis status
- **Response**: JSON with health status and Redis connection status

### 4. Rate Limit Info
- **URL**: `GET /rate-limit-info`
- **Description**: Get current rate limit information for your IP
- **Response**: JSON with current request count and limits

## Rate Limiting

The service implements IP-based rate limiting using Redis:

- **Limit**: 10 requests per day per IP address
- **Storage**: Redis for distributed rate limiting
- **Headers**: Rate limit information included in response headers
- **Error**: 429 Too Many Requests when limit exceeded

### Rate Limit Headers

When making requests, you'll receive headers like:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1640995200
```

## Usage Examples

### Using curl

```bash
# Basic request
curl -X POST "http://localhost:8000/stream" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Tell me a short story about a robot"}' \
     --no-buffer

# Check rate limit info
curl "http://localhost:8000/rate-limit-info"

# Check health
curl "http://localhost:8000/health"
```

### Using Python requests

```bash
# Install requests for testing
uv add requests

# Run the test client
uv run python test_client.py

# Test rate limiting
uv run python test_rate_limiting.py
```

```python
import requests
import json

url = "http://localhost:8000/stream"
data = {"prompt": "Explain quantum computing in simple terms"}

response = requests.post(url, json=data, stream=True)

for line in response.iter_lines():
    if line:
        # Remove 'data: ' prefix and parse JSON
        line = line.decode('utf-8')
        if line.startswith('data: '):
            json_str = line[6:]  # Remove 'data: ' prefix
            try:
                chunk = json.loads(json_str)
                if chunk['type'] == 'chunk':
                    print(chunk['content'], end='', flush=True)
                    print(f" (timestamp: {chunk['timestamp']})")
                elif chunk['type'] == 'end':
                    print()  # New line at end
                    break
                elif chunk['type'] == 'error':
                    print(f"Error: {chunk['error']}")
                    break
            except json.JSONDecodeError:
                continue
```

### Using JavaScript (Frontend)

```javascript
async function streamLLMResponse(prompt) {
    const response = await fetch('/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
    });

    // Check rate limit headers
    const rateLimitRemaining = response.headers.get('X-RateLimit-Remaining');
    console.log(`Remaining requests: ${rateLimitRemaining}`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.type === 'chunk') {
                        console.log(data.content);
                        console.log(`Timestamp: ${data.timestamp}`);
                        // Update your UI here
                    } else if (data.type === 'end') {
                        console.log('Stream ended');
                        return;
                    } else if (data.type === 'error') {
                        console.error('Error:', data.error);
                        return;
                    }
                } catch (e) {
                    // Skip invalid JSON
                }
            }
        }
    }
}

// Usage
streamLLMResponse("Write a poem about technology");
```

## API Documentation

Once the service is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `REDIS_HOST`: Redis server host (default: localhost)
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)

## Error Handling

The service includes comprehensive error handling:
- Empty prompt validation
- OpenAI API error handling
- Network error handling
- Rate limiting with proper HTTP status codes
- Redis connection error handling

## Development

### Project Structure
```
PortfolioBackend/
├── main.py                    # Main FastAPI application
├── pyproject.toml            # Project configuration and dependencies
├── test_client.py            # Test client for the API
├── test_streaming.py         # Streaming test script
├── test_rate_limiting.py     # Rate limiting test script
├── env.example               # Environment variables template
├── start.sh                  # Startup script
├── setup_dev.sh              # Development setup script
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Development Docker Compose
├── docker-compose.prod.yml   # Production Docker Compose
├── docker-build.sh           # Docker build script
├── .dockerignore             # Docker ignore file
└── README.md                 # This file
```

### Development Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py

# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Run tests (if pytest is added)
uv run pytest

# Format code (if black is added)
uv run black .

# Lint code (if flake8 is added)
uv run flake8 .

# Test streaming
uv run python test_streaming.py

# Test rate limiting
uv run python test_rate_limiting.py
```

### Docker Development

```bash
# Build and run in development mode
./docker-build.sh
docker-compose up

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build

# Run tests in container
docker-compose exec portfoliobackend uv run python test_streaming.py
docker-compose exec portfoliobackend uv run python test_rate_limiting.py

# Check Redis status
docker-compose exec redis redis-cli ping
```

### Adding New Features

1. The service is built with FastAPI, making it easy to add new endpoints
2. The streaming functionality can be extended to support different models
3. Additional middleware can be added for authentication, logging, etc.
4. Docker configuration supports both development and production environments
5. Rate limiting can be customized per endpoint or user

## License

This project is open source and available under the MIT License. 