# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SimpleAgentApp is a generic API tool-calling framework that enables LLMs to invoke external APIs through a standardized schema. The system consists of:
- **Tool API Server** (`tool_api/`): FastAPI service providing various tool endpoints
- **Generic Call Module** (`function_call/`): Pydantic-based schema and execution engine for API calls
- **Tool Registry** (`tool_registry/`): JSON definitions of available tools
- **Integration Tests** (`tests/`): Comprehensive test harness with test data

## Commands

### Development Server
```bash
# Start the API server locally
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

# Or using Docker
docker build -t simpleagentapp .
docker run -p 8000:8000 simpleagentapp
```

### Running Tests
```bash
# Run all integration tests (automatically starts/stops server)
python tests/test_generic_call.py

# Run tests against an already-running server
python tests/test_generic_call.py --use-external-server

# Run tests with custom host/port
python tests/test_generic_call.py --host 127.0.0.1 --port 8000
```

## Architecture

### Core Components

**ApiToolCall Schema** (`function_call/generic_call.py:7-19`):
- Defines the contract for API calls with Pydantic validation
- Fields: `url`, `method`, `params` (for GET), `json_body` (for POST/PUT)
- Method validator normalizes to uppercase and restricts to GET/POST/PUT/DELETE

**call_api Function** (`function_call/generic_call.py:22-48`):
- Generic executor that accepts ApiToolCall instances
- Handles all HTTP methods uniformly via `requests.request()`
- Returns JSON response or error dict on failure
- Includes 10-second timeout for all requests

**Tool Registry Format**:
Tool definitions (in `tool_registry/`) describe available tools for LLMs:
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

**Test Data Format** (`tests/data/`):
Test cases use simplified JSON (only url, method, params/json_body) that maps directly to ApiToolCall:
```json
{
  "url": "http://127.0.0.1:8000/endpoint",
  "method": "get",
  "params": {"text": "value"}
}
```

### Test Harness Design

The integration test (`tests/test_generic_call.py`) manages the full lifecycle:
1. Optionally starts uvicorn server in subprocess
2. Waits for health check via `/docs` endpoint
3. Loads test cases from `tests/data/`
4. Validates responses against expected outputs
5. Cleans up server process on exit

Key test utilities:
- `start_api_server()`: Spawns uvicorn, logs to `api_server.log`
- `_wait_for_server_ready()`: Polls until server responds (15s timeout)
- `run_test_case()`: Loads JSON, calls `call_api()`, validates response

## Available API Endpoints

All endpoints in `tool_api/main.py`:
- `/weather` - GET: Returns random temperature for city/date
- `/uppercase` - GET: Converts text to uppercase
- `/lowercase` - GET: Converts text to lowercase
- `/count_word` - GET: Counts words in text (whitespace-split)
- `/calculate` - GET: Performs arithmetic (+, -, *, /)