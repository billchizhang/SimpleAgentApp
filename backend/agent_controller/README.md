# Agent Controller Module

An LLM-driven orchestration layer for tool selection and execution with ReAct (Reasoning and Acting) loop integration.

## Overview

The `agent_controller` module provides an intelligent agent that:
- Takes natural language queries as input
- Uses OpenAI's LLM to determine which tools to call
- Executes API calls via the existing `generic_call` module
- Implements ReAct-style reasoning for transparency
- Records complete execution traces with all steps

## Architecture

### Components

1. **AgentController** (`controller.py`)
   - Main orchestration class
   - Coordinates OpenAI calls, tool execution, and response generation
   - Implements iterative ReAct loop with loop prevention

2. **ToolRegistryLoader** (`tool_loader.py`)
   - Loads tool definitions from `tool_registry/` directory
   - Converts tool schemas to OpenAI function calling format
   - Provides access to original tool definitions for execution

3. **ResponseFormatter** (`response_formatter.py`)
   - Records all execution steps with timestamps
   - Supports ReAct step types: thought, action, observation
   - Formats final responses with complete execution traces

4. **Step** (dataclass in `response_formatter.py`)
   - Represents individual execution steps
   - Fields: step_number, step_type, description, timestamp, details, error

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `openai>=1.0.0` - OpenAI API client
- `python-dotenv` - Environment variable management
- `fastapi`, `pydantic`, `requests`, `uvicorn` - Existing dependencies

### 2. Set Up OpenAI API Key

Option A: Environment variable
```bash
export OPENAI_API_KEY="sk-..."
```

Option B: `.env` file
```bash
# Create .env file in project root
echo "OPENAI_API_KEY=sk-..." > .env
```

Option C: Pass directly to constructor
```python
controller = AgentController(api_key="sk-...")
```

### 3. Start Tool API Server

The agent needs the tool API server running:

```bash
# Start server on localhost:8000
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000
```

## Usage

### Basic Example

```python
from agent_controller import AgentController

# Initialize controller
controller = AgentController()

# Process a query
result = controller.process_query("What's the weather in Boston today?")

# Access results
print(f"Success: {result['success']}")
print(f"Answer: {result['answer']}")

# View execution steps
for step in result['steps']:
    print(f"{step['step_number']}. {step['description']}")
```

### Custom Configuration

```python
from agent_controller import AgentController
from pathlib import Path

controller = AgentController(
    api_key="sk-...",                          # OpenAI API key
    tool_registry_path=Path("./tool_registry"), # Custom tool registry path
    model="gpt-3.5-turbo",                      # Model to use
    max_iterations=10,                          # Max tool call iterations
    use_react=True                              # Enable ReAct reasoning
)
```

### ReAct Loop Example

With `use_react=True` (default), the agent explains its reasoning:

```python
result = controller.process_query("Convert 'hello' to uppercase and count words")

# Response includes reasoning steps
for step in result['steps']:
    if step['step_type'] == 'thought':
        print(f"Reasoning: {step['details']['reasoning']}")
    elif step['step_type'] == 'action':
        print(f"Action: {step['details']['tool_name']}")
    elif step['step_type'] == 'observation':
        print(f"Result: {step['details']['result']}")
```

### Response Format

Every query returns a structured response:

```python
{
    "success": bool,           # Whether query was processed successfully
    "answer": str,            # Final answer to user
    "steps": [                # Complete execution trace
        {
            "step_number": int,
            "step_type": str,  # load_registry, thought, action, observation, final_answer, error
            "description": str,
            "timestamp": str,  # ISO format
            "details": dict,   # Step-specific details
            "error": str       # Error message if applicable
        }
    ],
    "error": str              # Overall error message if failed
}
```

### ReAct Step Types

- **load_registry**: Tools loaded from registry
- **thought**: Agent reasoning about what to do
- **action**: Tool call being made
- **observation**: Result received from tool
- **final_answer**: Final answer generated
- **error**: Error occurred during execution

## Example Queries

### Query Without Tools
```python
result = controller.process_query("What is 2 + 2?")
# LLM answers directly without calling tools
```

### Single Tool Query
```python
result = controller.process_query("Convert 'hello world' to uppercase")
# Calls uppercase tool
```

### Multiple Tool Query
```python
result = controller.process_query(
    "What's the weather in Boston and how many words are in that city name?"
)
# Calls weather tool and count_word tool
```

### Multi-Step Reasoning
```python
result = controller.process_query(
    "Get the weather for San Francisco on Christmas 2024, "
    "convert the city name to uppercase, and count its words"
)
# Multiple tool calls in sequence
```

## Advanced Features

### Error Handling

The controller handles errors gracefully:

```python
result = controller.process_query("Some query")

if not result['success']:
    print(f"Error: {result['error']}")

    # Check where error occurred
    for step in result['steps']:
        if step.get('error'):
            print(f"Failed at step {step['step_number']}: {step['error']}")
```

### Accessing Execution Trace

```python
# Get specific step types
thought_steps = [s for s in result['steps'] if s['step_type'] == 'thought']
action_steps = [s for s in result['steps'] if s['step_type'] == 'action']

# Count tool calls
tool_call_count = len([s for s in result['steps'] if s['step_type'] == 'action'])

# Get timing information
first_step_time = result['steps'][0]['timestamp']
last_step_time = result['steps'][-1]['timestamp']
```

### Disable ReAct Mode

For simpler prompting without explicit reasoning:

```python
controller = AgentController(use_react=False)
result = controller.process_query("Convert 'test' to uppercase")
# No thought steps in response
```

## Testing

### Run All Tests

```bash
# Run unit and integration tests (requires OpenAI API key)
python tests/test_agent_controller.py
```

### Skip Integration Tests

```bash
# Run only unit tests (no API key needed)
python tests/test_agent_controller.py --skip-integration
```

### Use External Server

```bash
# Use already-running server instead of starting new one
python tests/test_agent_controller.py --use-external-server
```

### Test Coverage

- ✅ Unit tests for ResponseFormatter
- ✅ Unit tests for ToolRegistryLoader
- ✅ Unit tests for AgentController initialization
- ✅ Integration tests with real OpenAI API and tool server
- ✅ Error handling and edge cases

## Configuration Options

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | Optional[str] | `OPENAI_API_KEY` env var | OpenAI API key |
| `tool_registry_path` | Optional[Path] | `../tool_registry/` | Path to tool definitions |
| `model` | str | `"gpt-4o"` | OpenAI model to use |
| `max_iterations` | int | `5` | Max tool call iterations (prevents loops) |
| `use_react` | bool | `True` | Enable ReAct reasoning |

### Supported Models

- `gpt-4o` (recommended, default)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo` (cheaper, less capable)

## Error Reference

### Common Errors

**ValueError: OpenAI API key must be provided**
- Cause: No API key provided via parameter or environment variable
- Solution: Set `OPENAI_API_KEY` or pass `api_key` parameter

**FileNotFoundError: Tool registry directory not found**
- Cause: Tool registry path doesn't exist
- Solution: Verify `tool_registry/` directory exists or provide correct path

**AuthenticationError: Invalid API key**
- Cause: OpenAI API key is invalid or expired
- Solution: Check your API key at platform.openai.com

**RateLimitError: Rate limit exceeded**
- Cause: Too many requests to OpenAI API
- Solution: Implement rate limiting or upgrade API tier

**Maximum iteration limit reached**
- Cause: Agent made too many tool calls (possible loop)
- Solution: Increase `max_iterations` or simplify query

## Performance Tips

1. **Use GPT-4o for best results**: More reliable tool calling
2. **Adjust max_iterations**: Increase for complex multi-step queries
3. **Enable ReAct selectively**: Disable for faster responses when transparency not needed
4. **Cache tool registry**: Tools are loaded once and reused across queries
5. **Use external server**: Avoid server startup overhead in production

## Integration with Existing Code

The agent controller integrates seamlessly with existing components:

```python
# Uses existing generic_call module
from function_call.generic_call import ApiToolCall, call_api

# Uses existing tool registry format
# No changes needed to tool_registry/*.json files

# Compatible with existing test harness
# Can run alongside existing tests
```

## Example Script

See [`test_llm_response.py`](../tests/test_llm_response.py) for a complete demonstration with:
- Multiple query examples
- Pretty-printed execution traces
- Error handling
- Interactive mode

Run it:
```bash
python tests/test_llm_response.py
```

## Troubleshooting

### Issue: "Package openai is not installed"
Solution:
```bash
pip install openai>=1.0.0
```

### Issue: "Connection refused to localhost:8000"
Solution: Start the tool API server first
```bash
python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000
```

### Issue: "Tool not found in registry"
Solution: Check that tool definition exists in `tool_registry/` directory

### Issue: "Rate limit exceeded"
Solution: Add delays between requests or upgrade OpenAI API tier

## Contributing

When adding new tools:

1. Add tool definition to `tool_registry/tool_name.json`
2. Follow the existing schema format
3. Test with the agent controller
4. The tool is automatically available to the agent

## License

Same as parent project (SimpleAgentApp).

## Support

For issues or questions:
- Check the [main CLAUDE.md](../CLAUDE.md) documentation
- Review [test_llm_response.py](../tests/test_llm_response.py) for usage patterns
- Run tests to verify setup: `python tests/test_agent_controller.py`
