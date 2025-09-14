# AI Blogging Platform with Gemini 2.5 Flash

## 🚀 Overview
This project is an advanced AI-powered blogging backend that uses Google Gemini 2.5 Flash via the Google Generative AI package for high-performance content generation. It features Microsoft AutoGen for agentic, parallel content and image generation with enterprise-grade security, comprehensive error handling, and production-ready architecture.

## ✨ Features

### 🔐 Security & Reliability
- **Environment-based Configuration:** Secure API key management with validation
- **Rate Limiting:** Protection against API abuse with configurable limits
- **Input Validation:** Comprehensive Pydantic schema validation
- **CORS Security:** Proper CORS configuration with origin validation
- **Error Handling:** Global exception handling with structured error responses

### 🤖 AI & Multi-Agent
- **Google Gemini 2.5 Flash:** High-performance content generation using Google's latest model
- **Agentic Workflow:** Uses UserProxyAgent, AssistantAgents, and GroupChatManager from Microsoft AutoGen
- **Parallel Generation:** Blog and image description are generated concurrently
- **Streaming API:** WebSocket endpoint streams results as soon as each is ready
- **Tool Integration:** Agents can call registered Python tools (e.g., for image generation)
- **Style Customization:** Support for different writing styles (professional, casual, etc.)
- **Multiple Output Formats:** HTML, Markdown, and plain text generation

### 📊 Monitoring & Observability
- **Structured Logging:** Comprehensive logging with different levels
- **Request Tracking:** Detailed request/response logging with timing
- **Health Checks:** Built-in health check endpoints
- **Performance Metrics:** Request processing time tracking

### 🏗️ Architecture
```
Client (WebSocket/HTTP)
    |
    v
FastAPI (app.py) with Middleware
    |
    v
Rate Limiting & Logging
    |
    v
routes/agent_routes.py (Validated endpoints)
    |
    v
services/autogen_agents.py (AutoGen multi-agent workflow)
    |         |
    |         +-- services/gemini_service.py (Gemini 2.5 Flash integration)
    |         +-- tools/image_tools.py (image generation tool)
    |         +-- tools/web_search_tools.py (web search tool)
    |
    v
Microsoft AutoGen (UserProxyAgent, AssistantAgents, GroupChatManager)
    |
    v
Google Gemini 2.5 Flash (via google-generativeai package)
```

## 📁 File Structure
```
ai_blogging/
├── app.py                          # Main FastAPI application
├── config.py                       # Configuration management
├── routes/
│   └── agent_routes.py            # API endpoints with validation
├── services/
│   ├── autogen_agents.py          # Multi-agent orchestration
│   ├── gemini_service.py          # Google Gemini 2.5 Flash integration
│   └── chatollama_service.py      # Legacy Ollama integration (deprecated)
├── tools/
│   ├── image_tools.py             # Image generation utilities
│   └── web_search_tools.py        # Web search functionality
├── models/
│   └── chat.py                    # Data models for chat sessions
├── schemas/
│   ├── requests.py                # Request validation schemas
│   └── responses.py               # Response schemas
├── middleware/
│   ├── logging.py                 # Structured logging middleware
│   └── rate_limiter.py           # Rate limiting middleware
├── tests/                         # Comprehensive test suite
│   ├── test_gemini_service.py     # Gemini service tests
│   └── test_chatollama_service.py # Legacy Ollama tests
├── examples/
│   ├── gemini_usage.py            # Gemini service examples
│   └── chatollama_usage.py        # Legacy Ollama examples
├── requirements.txt               # Dependencies
├── env.example                   # Environment template
└── README.md                     # This file
```

## 🛠️ Setup

### 1. Clone and Install
```bash
git clone <repo-url>
cd ai_blogging
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your settings
GEMINI_API_KEY=your_google_gemini_api_key_here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Get your Gemini API key:** Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to generate your API key.

### 3. Run the Server
```bash
# Development mode
uvicorn app:app --reload

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

### WebSocket Streaming Endpoint
- **URL:** `ws://localhost:8000/api/v1/ws/agent-blog`
- **Send:** 
  ```json
  {
    "topic": "Your blog topic",
    "include_image": true,
    "style": "professional"
  }
  ```
- **Receive:** Structured responses with type and data
  ```json
  {
    "type": "blog",
    "data": {"blog_html": "<h1>...</h1>"},
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```

### HTTP REST Endpoints
- **POST** `/api/v1/blog` - Synchronous blog generation
- **GET** `/api/v1/health` - Health check
- **GET** `/docs` - Interactive API documentation

### Example Usage

#### Python WebSocket Client
```python
import websockets
import asyncio
import json

async def main():
    uri = "ws://localhost:8000/api/v1/ws/agent-blog"
    async with websockets.connect(uri) as websocket:
        message = {
            "topic": "The Future of AI Blogging",
            "style": "professional"
        }
        await websocket.send(json.dumps(message))
        
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Type: {data['type']}")
                print(f"Data: {data['data']}")
                
                if data['type'] == 'complete':
                    break
            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(main())
```

#### Python HTTP Client
```python
import httpx
import json

async def generate_blog():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/blog",
            json={
                "topic": "The Future of AI Blogging",
                "style": "professional"
            }
        )
        return response.json()

# Usage
result = asyncio.run(generate_blog())
print(result['blog_html'])
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_config.py
```

### Test Structure
- `tests/test_config.py` - Configuration validation tests
- `tests/test_schemas.py` - Pydantic schema validation tests
- Additional tests for services, middleware, etc.

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (gemini/openai) | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_MAX_OUTPUT_TOKENS` | Max output tokens | `8192` |
| `GEMINI_TEMPERATURE` | Generation temperature | `0.7` |
| `GEMINI_TOP_P` | Top-p sampling | `0.8` |
| `GEMINI_TOP_K` | Top-k sampling | `40` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `RATE_LIMIT_PER_MINUTE` | Rate limiting | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ALLOWED_ORIGINS` | CORS origins | `http://localhost:3000,http://localhost:8080` |

### Security Features
- ✅ API key validation
- ✅ Rate limiting per IP
- ✅ Input sanitization
- ✅ CORS origin validation
- ✅ Structured error responses
- ✅ Comprehensive logging

## 🚀 Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
```bash
# Production environment variables
export GEMINI_API_KEY=your_production_gemini_key
export ALLOWED_ORIGINS=https://yourdomain.com
export LOG_LEVEL=WARNING
export RATE_LIMIT_PER_MINUTE=30
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `pip install -r requirements.txt`
4. Run tests: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Include tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues:** Create an issue on GitHub
- **Documentation:** Check `/docs` endpoint for interactive API docs
- **Health Check:** Use `/api/v1/health` to verify service status

---

**Built with ❤️ using FastAPI, AutoGen, and Google Gemini 2.5 Flash**