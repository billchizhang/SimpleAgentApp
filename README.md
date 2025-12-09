# SimpleAgentApp

A generic API tool-calling framework that enables LLMs to invoke external APIs through a standardized schema with ReAct (Reasoning and Acting) loop integration.

## 🚀 Quick Start (One-Liner)

```bash
# Build and run everything
make build && make run
```

That's it! All three services will be running:
- **Frontend**: http://localhost:3000 (Login page)
- **Tool API**: http://localhost:8000/docs
- **Agent API**: http://localhost:8001/docs

## 📋 Prerequisites

1. **Docker** installed (for containerized deployment)
2. **OpenAI API Key** - Get one from [OpenAI](https://platform.openai.com/api-keys)
3. **Node.js** (v14+) and **npm** (for local frontend development only)
4. **Python 3.8+** (for local backend development only)

## 🎯 Installation

### Option 1: Make Commands (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd SimpleAgentApp

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Build and run
make build
make run

# View logs
make logs

# Stop
make stop
```

### Option 2: Docker One-Liner

```bash
# Build image
docker build -t simpleagentapp .

# Run with API key (all three services: Frontend + Tool API + Agent API)
docker run -d -p 3000:3000 -p 8000:8000 -p 8001:8001 -e OPENAI_API_KEY=sk-... simpleagentapp

# Run without API key (Frontend + Tool API only, no Agent API)
docker run -d -p 3000:3000 -p 8000:8000 simpleagentapp
```

### Option 3: Docker Compose

```bash
# Setup
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Start
docker-compose up

# Stop
docker-compose down
```

### Option 4: Local Development

```bash
# Backend setup (from project root)
cd backend
pip install -r requirements.txt

# Terminal 1: Tool API
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Agent API
export OPENAI_API_KEY="sk-..."
python -m uvicorn agent_api.main:app --host 127.0.0.1 --port 8001

# Terminal 3: Frontend (from project root)
cd frontend
npm install
npm start  # Runs on port 3000
```

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │  Port 3000 (React + serve)
│  Login & Chat   │  User authentication & chat UI
└────────┬────────┘
         │ HTTP REST
         ▼
┌─────────────────┐
│   Agent API     │  Port 8001 (FastAPI)
│   + OpenAI      │  LLM-driven orchestration
└────────┬────────┘
         │ Python calls
         ▼
┌─────────────────┐
│ Agent Controller│  ReAct Loop
│   (Python)      │  Thought → Action → Observation
└────────┬────────┘
         │ HTTP calls
         ▼
┌─────────────────┐
│   Tool API      │  Port 8000 (FastAPI)
│   (Python)      │  Actual tool endpoints
└─────────────────┘
```

## 📡 Usage Examples

### cURL

```bash
# Simple query
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Boston?"}'

# With chat history
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about tomorrow?",
    "chat_history": [
      {"role": "user", "content": "What is the weather today?"},
      {"role": "assistant", "content": "It is 15°C in Boston."}
    ]
  }'
```

### Python

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8001/query",
    json={"query": "Convert 'hello world' to uppercase"}
)

result = response.json()
print(f"Answer: {result['answer']}")

# View reasoning steps
for step in result['steps']:
    print(f"{step['step_type']}: {step['description']}")
```

### JavaScript

```javascript
// Using fetch
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
console.log('Steps:', result.steps.length);
```

## 🎮 Available Commands

### Make Commands

```bash
make help         # Show all commands
make build        # Build Docker image
make run          # Run both services
make run-no-key   # Run tool API only (no OpenAI key)
make stop         # Stop container
make clean        # Remove image and containers
make logs         # View logs
make test         # Run tests
make quick        # Build and run in one command
```

### Docker Commands

```bash
# Build
docker build -t simpleagentapp .

# Run with everything (Frontend + Tool API + Agent API)
docker run -d -p 3000:3000 -p 8000:8000 -p 8001:8001 -e OPENAI_API_KEY=sk-... simpleagentapp

# Run without API key (Frontend + Tool API only)
docker run -d -p 3000:3000 -p 8000:8000 simpleagentapp

# Stop
docker stop $(docker ps -q --filter ancestor=simpleagentapp)

# Logs
docker logs -f <container-id>
```

## 🧪 Testing

```bash
# Run all tests
make test

# Or manually
python tests/test_generic_call.py
python tests/test_agent_controller.py
python tests/test_agent_api.py

# Interactive demo
python tests/test_llm_response.py
```

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Main project documentation
- **[frontend/README.md](frontend/README.md)** - Frontend application guide
- **[agent_api/README.md](agent_api/README.md)** - Agent API documentation
- **[agent_controller/README.md](agent_controller/README.md)** - Agent controller documentation
- **[tests/README.md](tests/README.md)** - Testing guide

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes* | - | OpenAI API key (*for Agent API) |
| `OPENAI_MODEL` | No | `gpt-4o` | Model to use |
| `MAX_ITERATIONS` | No | `5` | Max tool call iterations |
| `USE_REACT` | No | `true` | Enable ReAct reasoning |
| `TOOL_REGISTRY_PATH` | No | `./tool_registry` | Tool definitions path |

### .env File

```bash
# Copy template
cp .env.example .env

# Edit and add your API key
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
MAX_ITERATIONS=5
USE_REACT=true
```

## 🛠️ Components

### Frontend (`frontend/`)
React-based web application providing user authentication and chat interface.

**Features:**
- User authentication with role-based access
- Interactive chat with AI agent
- Admin panel for user management
- ReAct reasoning visualization
- Responsive design

**Default Login:**
- Admin: `admin` / `AdminPass123!`
- User: `demo_user` / `UserPass123!`

### Agent API (`agent_api/`)
FastAPI REST API providing HTTP endpoints for LLM queries with chat history support.

**Endpoints:**
- `POST /query` - Process queries
- `GET /health` - Health check
- `GET /tools` - List available tools
- `GET /docs` - API documentation

### Agent Controller (`agent_controller/`)
Python module implementing ReAct loop for intelligent tool selection and execution.

**Features:**
- ReAct methodology (Reasoning → Acting)
- Automatic tool selection
- Multi-step reasoning
- Complete execution traces

### Tool API (`tool_api/`)
FastAPI service providing actual tool endpoints (weather, uppercase, etc.).

### Tool Registry (`tool_registry/`)
JSON definitions of available tools with schemas and descriptions.

### Generic Call (`function_call/`)
Pydantic-based schema and execution engine for API calls.

## 🌟 Features

- ✅ **One-Command Startup** - `make build && make run`
- ✅ **React Frontend** - Complete web UI with authentication and chat
- ✅ **User Management** - Role-based access control (Admin/User)
- ✅ **REST API** - HTTP interface for LLM queries
- ✅ **Chat History** - Conversational context support
- ✅ **ReAct Loop** - Transparent reasoning traces
- ✅ **Docker Support** - Easy deployment with all services
- ✅ **Interactive Docs** - Swagger UI included
- ✅ **CORS Enabled** - Frontend integration
- ✅ **Health Monitoring** - Service status checks
- ✅ **Comprehensive Tests** - Full test coverage

## 🐛 Troubleshooting

### Port already in use
```bash
# Kill processes on ports 3000, 8000, and 8001
lsof -ti:3000,8000,8001 | xargs kill -9
```

### Container won't start
```bash
# Check logs
make logs

# Or
docker logs <container-id>
```

### OpenAI API errors
```bash
# Verify API key is set
docker exec simpleagentapp env | grep OPENAI_API_KEY

# Check health
curl http://localhost:8001/health
```

### Need to rebuild
```bash
make clean
make build
```

## 📄 License

[Your License Here]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## 📞 Support

- Documentation: [CLAUDE.md](CLAUDE.md)
- API Docs: http://localhost:8001/docs
- Issues: [GitHub Issues](your-repo-url/issues)

## 🎯 Next Steps

After starting the application:

1. **Use the Frontend** - Visit http://localhost:3000 to login and chat with the AI agent
2. **Explore the APIs** - Check out http://localhost:8001/docs and http://localhost:8000/docs
3. **Try example queries** - Use the test scripts in `tests/`
4. **Read the docs** - Check out the README files in each module
5. **Build your app** - Integrate the APIs into your application

---

**Quick Start Reminder:**
```bash
make build && make run
```

That's all you need! 🚀
