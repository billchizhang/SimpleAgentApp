# Agent API

FastAPI backend service that wraps the `agent_controller` module to provide HTTP endpoints for LLM-driven agent interactions with chat history support.

## Overview

The Agent API provides a REST API for:
- Processing user queries with OpenAI's LLM
- Supporting conversation history for context-aware responses
- Automatic tool selection and execution
- Complete reasoning traces with ReAct (Reasoning and Acting) methodology
- Health monitoring and tool discovery

## Architecture

```
┌─────────────────┐
│   Client App    │
│  (Frontend/CLI) │
└────────┬────────┘
         │ HTTP REST API
         ▼
┌─────────────────┐
│   Agent API     │  Port 8001
│   (FastAPI)     │
└────────┬────────┘
         │ Python calls
         ▼
┌─────────────────┐
│ Agent Controller│  (ReAct Loop)
│   + OpenAI API  │
└────────┬────────┘
         │ HTTP calls
         ▼
┌─────────────────┐
│   Tool API      │  Port 8000
│   (FastAPI)     │
└─────────────────┘
```

## API Endpoints

### `GET /`
Root endpoint with API information and available endpoints.

### `GET /health`
Health check endpoint that returns service status.

**Response:**
```json
{
  "status": "healthy",
  "agent_controller_available": true,
  "tool_registry_available": true,
  "openai_api_configured": true
}
```

### `POST /query`
Main endpoint for processing user queries with chat history.

**Request Body:**
```json
{
  "query": "What's the weather in Boston today?",
  "chat_history": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help you today?"}
  ],
  "use_react": true,
  "model": "gpt-4o",
  "max_iterations": 5
}
```

**Response:**
```json
{
  "success": true,
  "answer": "The temperature in Boston today is 15.2°C.",
  "steps": [
    {
      "step_number": 1,
      "step_type": "thought",
      "description": "Agent reasoning",
      "timestamp": "2025-12-09T15:30:00",
      "details": {"reasoning": "I need to call the weather tool"},
      "error": null
    }
  ],
  "error": null,
  "metadata": {
    "model": "gpt-4o",
    "total_steps": 5,
    "tools_called": 1,
    "react_enabled": true
  }
}
```

### `GET /tools`
List all available tools from the tool registry.

**Response:**
```json
{
  "total_tools": 3,
  "tools": {
    "weather": {
      "name": "weather",
      "description": "Returns temperature...",
      "method": "GET",
      "params": {...}
    }
  }
}
```

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1. Set your OpenAI API key in .env file
cp .env.example .env
# Edit .env and add your API key

# 2. Start both services (tool_api and agent_api)
docker-compose up

# 3. Access the APIs
# - Agent API: http://localhost:8001/docs
# - Tool API: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export OPENAI_API_KEY="sk-..."

# 3. Start tool API (in one terminal)
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

# 4. Start agent API (in another terminal)
python -m uvicorn agent_api.main:app --host 127.0.0.1 --port 8001
```

### Option 3: Direct Python

```bash
# Start agent API directly
python -m agent_api.main
```

## Usage Examples

### cURL

```bash
# Simple query without history
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather in Boston?",
    "use_react": true
  }'

# Query with chat history
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about tomorrow?",
    "chat_history": [
      {"role": "user", "content": "What is the weather in Boston today?"},
      {"role": "assistant", "content": "The temperature in Boston today is 15.2°C."}
    ]
  }'
```

### Python Requests

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8001/query",
    json={
        "query": "Convert 'hello world' to uppercase",
        "use_react": True
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Steps: {len(result['steps'])}")

# With chat history
response = requests.post(
    "http://localhost:8001/query",
    json={
        "query": "What about tomorrow?",
        "chat_history": [
            {"role": "user", "content": "What's the weather today?"},
            {"role": "assistant", "content": "It's 15°C in Boston."}
        ]
    }
)
```

### JavaScript (fetch)

```javascript
// Simple query
const response = await fetch('http://localhost:8001/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: "What's the weather in Boston?",
    use_react: true
  })
});

const result = await response.json();
console.log('Answer:', result.answer);
console.log('Steps:', result.steps);
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | **Required**. OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | Model to use (gpt-4o, gpt-4-turbo, etc.) |
| `MAX_ITERATIONS` | `5` | Max tool call iterations to prevent loops |
| `USE_REACT` | `true` | Enable ReAct-style reasoning |
| `TOOL_REGISTRY_PATH` | `./tool_registry` | Path to tool definitions |

### Docker Compose Configuration

Edit `docker-compose.yml` to customize ports, environment variables, or resource limits:

```yaml
agent-api:
  ports:
    - "8001:8001"  # Change external port here
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - OPENAI_MODEL=gpt-3.5-turbo  # Use cheaper model
    - MAX_ITERATIONS=10  # Allow more iterations
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Chat History

The agent API supports conversation history for context-aware responses:

```python
# First query
response1 = requests.post("http://localhost:8001/query", json={
    "query": "What's the weather in Boston?"
})

# Follow-up with context
response2 = requests.post("http://localhost:8001/query", json={
    "query": "What about tomorrow?",
    "chat_history": [
        {"role": "user", "content": "What's the weather in Boston?"},
        {"role": "assistant", "content": response1.json()['answer']}
    ]
})
```

## Response Format

Every query returns a structured response:

```typescript
{
  success: boolean;           // Whether processing succeeded
  answer: string;            // Final answer from LLM
  steps: ExecutionStep[];    // Complete reasoning trace
  error?: string;            // Error message if failed
  metadata?: {               // Additional information
    model: string;           // Model used
    total_steps: number;     // Number of steps
    tools_called: number;    // Number of tool calls
    react_enabled: boolean;  // ReAct mode status
  };
}
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful query processing
- `503 Service Unavailable`: Agent controller not initialized (check API key)
- `500 Internal Server Error`: Processing error (check logs)

Error responses include details:

```json
{
  "detail": "Agent controller not available. Check OPENAI_API_KEY configuration."
}
```

## Health Monitoring

Use the `/health` endpoint for monitoring:

```bash
# Check if service is healthy
curl http://localhost:8001/health

# Use in health checks (returns non-zero on unhealthy)
curl -f http://localhost:8001/health || echo "Service unhealthy"
```

## CORS Configuration

CORS is enabled by default for all origins (`*`). For production, restrict origins in `agent_api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t simpleagent-api .

# Run agent API
docker run -d \
  -p 8001:8001 \
  -e OPENAI_API_KEY=sk-... \
  simpleagent-api \
  uvicorn agent_api.main:app --host 0.0.0.0 --port 8001
```

### Using Docker Compose

```bash
# Production with .env file
docker-compose up -d

# View logs
docker-compose logs -f agent-api

# Stop services
docker-compose down
```

### Performance Considerations

1. **Model Selection**: Use `gpt-3.5-turbo` for faster, cheaper responses
2. **Max Iterations**: Reduce for simpler queries, increase for complex reasoning
3. **ReAct Mode**: Disable for faster responses when transparency not needed
4. **Caching**: Tool registry is loaded once and cached
5. **Concurrent Requests**: FastAPI handles concurrent requests efficiently

## Troubleshooting

### "Agent controller not available"
- Check that `OPENAI_API_KEY` is set correctly
- Verify API key is valid at https://platform.openai.com/api-keys

### "Tool registry directory not found"
- Ensure `tool_registry/` directory exists
- Check `TOOL_REGISTRY_PATH` environment variable
- In Docker, verify volume mounts

### "Rate limit exceeded"
- Implement rate limiting in your client
- Upgrade OpenAI API tier
- Use `gpt-3.5-turbo` for lower costs

### "Connection refused to localhost:8000"
- Ensure `tool_api` is running (required for tool calls)
- In Docker Compose, services start automatically

## Development

### Running Tests

```bash
# Test agent API endpoints
python tests/test_agent_controller.py

# Test with live API
python tests/test_llm_response.py
```

### Adding New Endpoints

1. Add Pydantic model to `agent_api/models.py`
2. Add endpoint to `agent_api/main.py`
3. Update this README with documentation

### Extending Functionality

To add custom processing logic:

```python
# agent_api/main.py

@app.post("/custom-endpoint")
async def custom_endpoint(request: CustomRequest):
    # Your custom logic here
    result = agent_controller.process_query_with_history(
        query=request.query,
        chat_history=request.history
    )
    return result
```

## Security Considerations

1. **API Key Protection**: Never commit `.env` files
2. **CORS**: Restrict origins in production
3. **Rate Limiting**: Implement rate limiting for public APIs
4. **Input Validation**: Pydantic handles validation automatically
5. **Secrets Management**: Use secrets manager in production

## License

Same as parent project (SimpleAgentApp).

## Support

- Main documentation: [../CLAUDE.md](../CLAUDE.md)
- Agent controller docs: [../agent_controller/README.md](../agent_controller/README.md)
- API documentation: http://localhost:8001/docs
