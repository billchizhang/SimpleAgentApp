# Tests Directory

Comprehensive test suite for SimpleAgentApp components.

## Test Files

### Unit & Integration Tests

#### `test_generic_call.py`
Tests the generic API calling module (`function_call/generic_call.py`).

- **What it tests**: ApiToolCall schema, call_api function, API endpoints
- **Requirements**: None (starts server automatically)
- **Usage**:
  ```bash
  # Run all tests (auto-starts server)
  python tests/test_generic_call.py

  # Use external server
  python tests/test_generic_call.py --use-external-server
  ```

#### `test_agent_controller.py`
Tests the agent controller module (`agent_controller/`).

- **What it tests**:
  - ResponseFormatter step recording
  - ToolRegistryLoader functionality
  - AgentController initialization
  - Integration tests with real OpenAI API
- **Requirements**:
  - OPENAI_API_KEY (for integration tests)
  - Tool API running (for integration tests)
- **Usage**:
  ```bash
  # Run all tests
  export OPENAI_API_KEY="sk-..."
  python tests/test_agent_controller.py

  # Skip integration tests (no API key needed)
  python tests/test_agent_controller.py --skip-integration

  # Use external server
  python tests/test_agent_controller.py --use-external-server
  ```

#### `test_agent_api.py`
Tests the FastAPI REST API endpoints (`agent_api/`).

- **What it tests**:
  - Health check endpoint
  - Tool listing endpoint
  - Query endpoint with/without chat history
  - ReAct mode toggling
  - Multi-tool queries
- **Requirements**:
  - OPENAI_API_KEY
  - Tool API running on port 8000
  - Agent API running on port 8001
- **Usage**:
  ```bash
  # Start both servers
  docker-compose up

  # Run tests
  python tests/test_agent_api.py
  ```

### Interactive Tests

#### `test_endpoints.py`
Simple endpoint testing script for tool API.

- **What it tests**: Basic functionality of tool API endpoints
- **Requirements**: Tool API running on port 8000
- **Usage**:
  ```bash
  # Start tool API
  python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

  # Run tests
  python tests/test_endpoints.py
  ```

#### `test_llm_response.py`
Interactive demo of agent controller with ReAct reasoning (formerly `example_usage.py`).

- **What it demonstrates**:
  - Agent controller usage
  - ReAct loop with reasoning traces
  - Multiple query types (tools, no-tools, multi-tool)
  - Pretty-printed execution steps
- **Requirements**:
  - OPENAI_API_KEY
  - Tool API running on port 8000
- **Usage**:
  ```bash
  export OPENAI_API_KEY="sk-..."

  # Start tool API
  python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

  # Run demo
  python tests/test_llm_response.py
  ```

## Test Data

The `data/` directory contains test case files in JSON format:
- `uppercase_call.json` - Test uppercase tool
- `weather_call.json` - Test weather tool
- `count_word_call.json` - Test word count tool

These files follow the ApiToolCall schema and are used by `test_generic_call.py`.

## Running All Tests

### Quick Test (No API Key)
```bash
# Run unit tests only
python tests/test_generic_call.py
python tests/test_agent_controller.py --skip-integration
```

### Full Test Suite (With API Key)
```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Start services with Docker Compose
docker-compose up -d

# Wait for services to be ready
sleep 5

# Run all tests
python tests/test_generic_call.py
python tests/test_agent_controller.py
python tests/test_agent_api.py

# Cleanup
docker-compose down
```

### Test with External Servers
```bash
# Terminal 1: Start tool API
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Start agent API
export OPENAI_API_KEY="sk-..."
python -m uvicorn agent_api.main:app --host 127.0.0.1 --port 8001

# Terminal 3: Run tests
python tests/test_generic_call.py --use-external-server
python tests/test_agent_controller.py --use-external-server
python tests/test_agent_api.py
```

## Test Output

All tests provide detailed output:
- ✓ Pass indicators
- ✗ Fail indicators
- Execution traces for debugging
- Summary statistics

Example output:
```
==================== TEST SUMMARY ====================
  ✓ PASS: Health Check
  ✓ PASS: List Tools
  ✓ PASS: Simple Query
  ✓ PASS: Tool Query
  ✓ PASS: Query with History
  ✓ PASS: Multi-Tool Query
  ✓ PASS: ReAct Disabled

Results: 7/7 tests passed

🎉 All tests passed!
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    # Start services
    docker-compose up -d

    # Wait for readiness
    sleep 10

    # Run tests
    python tests/test_generic_call.py
    python tests/test_agent_controller.py
    python tests/test_agent_api.py

    # Cleanup
    docker-compose down
```

## Troubleshooting

### "Connection refused"
- Ensure servers are running
- Check ports 8000 and 8001 are not in use
- Wait a few seconds after starting servers

### "OPENAI_API_KEY not set"
- Set environment variable: `export OPENAI_API_KEY="sk-..."`
- Or use `.env` file (requires `python-dotenv`)

### "Tool registry directory not found"
- Run tests from project root directory
- Verify `tool_registry/` directory exists

### "Rate limit exceeded"
- Reduce test frequency
- Upgrade OpenAI API tier
- Use `--skip-integration` flag

## Adding New Tests

1. Create test file: `tests/test_<feature>.py`
2. Follow existing patterns (unittest or pytest)
3. Document requirements and usage
4. Update this README

## Test Coverage

Current coverage areas:
- ✅ Generic API calling
- ✅ Tool registry loading
- ✅ Agent controller initialization
- ✅ ReAct loop execution
- ✅ REST API endpoints
- ✅ Chat history support
- ✅ Error handling
- ✅ Health monitoring

Future coverage:
- ⏳ Performance/load testing
- ⏳ Security testing
- ⏳ End-to-end workflow tests
- ⏳ Mocked LLM responses
