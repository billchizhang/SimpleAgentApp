# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SimpleAgentApp is a generic API tool-calling framework that enables LLMs to invoke external APIs through a standardized schema. The system consists of:
- **Backend** (`backend/`): All backend code organized in a single directory
  - **Agent API Server** (`backend/agent_api/`): FastAPI REST API for LLM-driven queries with chat history support
  - **Tool API Server** (`backend/tool_api/`): FastAPI service providing various tool endpoints
  - **Agent Controller** (`backend/agent_controller/`): LLM-driven orchestration with ReAct loop for intelligent tool selection
  - **Generic Call Module** (`backend/function_call/`): Pydantic-based schema and execution engine for API calls
  - **Tool Registry** (`backend/tool_registry/`): JSON definitions of available tools
  - **Integration Tests** (`backend/tests/`): Comprehensive test harness with test data
- **Docker Configuration**: Dockerfile, docker-compose.yml, start.sh in root directory

## Commands

### Quick Start (One-Liner)

**Option 1: Using Make (Easiest)**
```bash
# Build and run everything
make build && make run

# Access APIs:
# - Agent API: http://localhost:8001/docs
# - Tool API: http://localhost:8000/docs
```

**Option 2: Using Docker**
```bash
# Build and run with API key
docker build -t simpleagentapp . && docker run -d -p 8000:8000 -p 8001:8001 -e OPENAI_API_KEY=sk-... simpleagentapp

# Or run tool API only (no API key needed)
docker build -t simpleagentapp . && docker run -d -p 8000:8000 simpleagentapp
```

**What happens:** The single Docker container runs both services automatically using `start.sh`:
- Tool API on port 8000 (always)
- Agent API on port 8001 (if `OPENAI_API_KEY` is set)

### Development Servers

#### Using Make Commands
```bash
make help         # Show all available commands
make build        # Build Docker image
make run          # Run both services (reads .env file)
make run-no-key   # Run tool API only (no OpenAI key)
make stop         # Stop container
make logs         # View logs
make clean        # Remove image and containers
```

#### Using Docker Compose
```bash
# Copy environment template
cp backend/.env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start both services
docker-compose up

# Stop
docker-compose down
```

#### Manual Start (Local Development)
```bash
# Change to backend directory
cd backend

# Terminal 1: Tool API
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Agent API
export OPENAI_API_KEY="sk-..."
python -m uvicorn agent_api.main:app --host 127.0.0.1 --port 8001
```

### Running Tests
```bash
# Run all tests using Make (from project root)
make test

# Run authentication tests only (from project root)
make test-auth

# Run specific tests directly (from project root)
python backend/tests/test_auth_api.py
python backend/tests/test_generic_call.py
python backend/tests/test_agent_controller.py
python backend/tests/test_agent_api.py

# Run tests against an already-running server
python backend/tests/test_generic_call.py --use-external-server

# Run tests with custom host/port
python backend/tests/test_generic_call.py --host 127.0.0.1 --port 8000

# Run agent_controller tests without integration tests
python backend/tests/test_agent_controller.py --skip-integration
```

### Using Agent Controller

#### Python Module (Direct)
```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# Change to backend directory
cd backend

# Start the tool API server
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

# Run example queries with ReAct reasoning (from backend directory)
python tests/test_llm_response.py
```

#### REST API (via Agent API)
```bash
# Start both services with Docker Compose
docker-compose up

# Make API requests
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Boston?"}'
```

## Architecture

### Core Components

**ApiToolCall Schema** (`backend/function_call/generic_call.py:7-19`):
- Defines the contract for API calls with Pydantic validation
- Fields: `url`, `method`, `params` (for GET), `json_body` (for POST/PUT)
- Method validator normalizes to uppercase and restricts to GET/POST/PUT/DELETE

**call_api Function** (`backend/function_call/generic_call.py:22-48`):
- Generic executor that accepts ApiToolCall instances
- Handles all HTTP methods uniformly via `requests.request()`
- Returns JSON response or error dict on failure
- Includes 10-second timeout for all requests

**Tool Registry Format**:
Tool definitions (in `backend/tool_registry/`) describe available tools for LLMs:
```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "url": "http://endpoint",
  "method": "GET",
  "params": {
    "param_name": {
      "type": "string",
      "required": true,
      "description": "Parameter description"
    }
  }
}
```

**Test Data Format** (`backend/tests/data/`):
Test cases use simplified JSON (only url, method, params/json_body) that maps directly to ApiToolCall:
```json
{
  "url": "http://127.0.0.1:8000/endpoint",
  "method": "get",
  "params": {"text": "value"}
}
```

### Test Harness Design

The integration test (`backend/tests/test_generic_call.py`) manages the full lifecycle:
1. Optionally starts uvicorn server in subprocess
2. Waits for health check via `/docs` endpoint
3. Loads test cases from `backend/tests/data/`
4. Validates responses against expected outputs
5. Cleans up server process on exit

Key test utilities:
- `start_api_server()`: Spawns uvicorn, logs to `api_server.log`
- `_wait_for_server_ready()`: Polls until server responds (15s timeout)
- `run_test_case()`: Loads JSON, calls `call_api()`, validates response

## Available API Endpoints

### Tool API Endpoints (`backend/tool_api/main.py`)
- `/weather` - GET: Returns random temperature for city/date
- `/uppercase` - GET: Converts text to uppercase
- `/lowercase` - GET: Converts text to lowercase
- `/count_word` - GET: Counts words in text (whitespace-split)
- `/calculate` - GET: Performs arithmetic (+, -, *, /)

### Agent API Endpoints (`backend/agent_api/main.py`)
- `POST /query` - Process user query with chat history and ReAct reasoning
- `GET /health` - Health check for agent controller and dependencies
- `GET /tools` - List all available tools from registry
- `POST /auth/create_user` - Create new user account
- `POST /auth/login` - Authenticate user with username/password
- `DELETE /auth/remove_user` - Remove user account

## Authentication System

The Agent API includes a SQLite-based user authentication system with secure password hashing and role-based access control.

### Database Schema
- **Location**: `data/users.db` (configurable via `DB_PATH` env var)
- **Table**: `users` with fields: uid (12-char primary key), username, email, password_hash, role (user/admin), created_at, updated_at
- **Indexes**: On username, email, and role for performance

### Default User Accounts
Created automatically on first startup:
- **Admin**: username=`admin`, password=`AdminPass123!`, email=`admin@simpleagent.local`, role=`admin`
- **User**: username=`demo_user`, password=`UserPass123!`, email=`user@simpleagent.local`, role=`user`

### Security Features
- **Password Hashing**: Bcrypt with 12 rounds (2^12 iterations)
- **UID Generation**: Cryptographically secure 12-character alphanumeric identifiers
- **SQL Injection Prevention**: Parameterized queries only
- **Input Validation**: Pydantic models with constraints (username 3-50 chars, password min 8 chars, email validation)
- **Vague Error Messages**: Generic "Invalid username or password" to prevent information leakage

### Authentication Endpoints

#### Create User
```bash
curl -X POST "http://localhost:8001/auth/create_user" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"SecurePass123!","email":"user@example.com","role":"user"}'
```

#### Login
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"AdminPass123!"}'
```

#### Remove User
```bash
curl -X DELETE "http://localhost:8001/auth/remove_user" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser"}'
```

### Implementation Files
- `backend/agent_api/auth.py` - Password hashing and UID generation utilities
- `backend/agent_api/database.py` - DatabaseManager class with CRUD operations
- `backend/agent_api/models.py` - Pydantic models for authentication requests/responses
- `backend/tests/test_auth_api.py` - Comprehensive authentication test suite

## Agent Controller Module

The `backend/agent_controller` module provides an intelligent orchestration layer that uses OpenAI's LLM to automatically select and execute tools based on user queries.

**Key Features**:
- **ReAct Loop**: Implements Reasoning and Acting for transparent agent behavior
- **Automatic Tool Selection**: LLM decides which tools to call based on query
- **Multi-Step Reasoning**: Supports iterative tool calls for complex queries
- **Complete Execution Traces**: Records all steps including thoughts, actions, and observations
- **Error Handling**: Gracefully handles tool failures and API errors

**Quick Start**:
```python
# From backend directory
from agent_controller import AgentController

# Initialize with API key
controller = AgentController(api_key="sk-...")

# Process natural language query
result = controller.process_query("What's the weather in Boston?")

# Access answer and execution trace
print(result['answer'])
for step in result['steps']:
    print(f"{step['step_type']}: {step['description']}")
```

**Components** (`backend/agent_controller/`):
- `controller.py`: Main AgentController class with ReAct loop implementation
- `tool_loader.py`: Loads tool registry and converts to OpenAI function calling format
- `response_formatter.py`: Records execution steps and formats responses
- `README.md`: Comprehensive documentation and examples

See [backend/agent_controller/README.md](backend/agent_controller/README.md) for detailed usage and configuration.

## Agent API Server

The `agent_api` module provides a FastAPI REST API that wraps the agent_controller for HTTP-based access.

**Key Features**:
- **REST API Endpoints**: HTTP interface for LLM queries
- **Chat History Support**: Maintains conversation context across requests
- **Health Monitoring**: Service status and dependency checks
- **Tool Discovery**: List available tools via API
- **CORS Enabled**: Ready for frontend integration

**Quick Start**:
```bash
# Start with Docker Compose (includes both APIs)
docker-compose up

# Or start manually
export OPENAI_API_KEY="sk-..."
python -m uvicorn agent_api.main:app --host 0.0.0.0 --port 8001
```

**API Endpoints**:
- `POST /query` - Process user queries with chat history
- `GET /health` - Health check and status
- `GET /tools` - List available tools
- `GET /docs` - Interactive API documentation

**Example Request**:
```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather in Boston?",
    "chat_history": [],
    "use_react": true
  }'
```

**Example Response**:
```json
{
  "success": true,
  "answer": "The temperature in Boston is 15.2°C.",
  "steps": [...],
  "metadata": {
    "model": "gpt-4o",
    "total_steps": 5,
    "tools_called": 1
  }
}
```

See [agent_api/README.md](agent_api/README.md) for detailed API documentation.