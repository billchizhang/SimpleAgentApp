"""
Tests for the agent_controller module.

This test suite includes:
- Unit tests for ResponseFormatter
- Unit tests for ToolRegistryLoader
- Unit tests for AgentController initialization
- Integration tests requiring OpenAI API key and running tool_api server

To run:
    # Run all tests (starts server automatically)
    python tests/test_agent_controller.py

    # Run with external server
    python tests/test_agent_controller.py --use-external-server

    # Skip integration tests (no API key needed)
    python tests/test_agent_controller.py --skip-integration
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_controller import AgentController, ResponseFormatter, Step, ToolRegistryLoader
from tests.test_generic_call import start_api_server, stop_api_server


class TestResponseFormatter(unittest.TestCase):
    """Test the ResponseFormatter class."""

    def setUp(self):
        self.formatter = ResponseFormatter()

    def test_initialization(self):
        """Test formatter initializes with empty steps."""
        self.assertEqual(len(self.formatter.steps), 0)
        self.assertEqual(self.formatter.step_counter, 0)

    def test_add_step(self):
        """Test adding a step."""
        self.formatter.add_step(
            "load_registry",
            "Loaded tools",
            details={"count": 3}
        )

        self.assertEqual(len(self.formatter.steps), 1)
        step = self.formatter.steps[0]
        self.assertEqual(step.step_number, 1)
        self.assertEqual(step.step_type, "load_registry")
        self.assertEqual(step.description, "Loaded tools")
        self.assertEqual(step.details["count"], 3)
        self.assertIsNone(step.error)

    def test_add_step_with_error(self):
        """Test adding a step with error."""
        self.formatter.add_step(
            "error",
            "Failed to load",
            error="File not found"
        )

        step = self.formatter.steps[0]
        self.assertEqual(step.error, "File not found")

    def test_multiple_steps(self):
        """Test adding multiple steps."""
        self.formatter.add_step("thought", "Thinking")
        self.formatter.add_step("action", "Acting")
        self.formatter.add_step("observation", "Observing")

        self.assertEqual(len(self.formatter.steps), 3)
        self.assertEqual(self.formatter.steps[0].step_number, 1)
        self.assertEqual(self.formatter.steps[1].step_number, 2)
        self.assertEqual(self.formatter.steps[2].step_number, 3)

    def test_format_final_response_success(self):
        """Test formatting successful response."""
        self.formatter.add_step("thought", "Test step")
        response = self.formatter.format_final_response(
            "Test answer",
            success=True
        )

        self.assertTrue(response["success"])
        self.assertEqual(response["answer"], "Test answer")
        self.assertEqual(len(response["steps"]), 1)
        self.assertIsNone(response["error"])

    def test_format_final_response_failure(self):
        """Test formatting failed response."""
        self.formatter.add_step("error", "Failed", error="Test error")
        response = self.formatter.format_final_response(
            "Error occurred",
            success=False,
            error="Test error"
        )

        self.assertFalse(response["success"])
        self.assertEqual(response["error"], "Test error")

    def test_get_steps_summary(self):
        """Test getting steps summary."""
        self.formatter.add_step("thought", "Thinking")
        self.formatter.add_step("action", "Acting")
        summary = self.formatter.get_steps_summary()

        self.assertIn("Execution Summary", summary)
        self.assertIn("Step 1", summary)
        self.assertIn("Step 2", summary)

    def test_get_step_count(self):
        """Test getting step count."""
        self.assertEqual(self.formatter.get_step_count(), 0)
        self.formatter.add_step("thought", "Test")
        self.assertEqual(self.formatter.get_step_count(), 1)

    def test_get_steps_by_type(self):
        """Test filtering steps by type."""
        self.formatter.add_step("thought", "Thinking 1")
        self.formatter.add_step("action", "Acting")
        self.formatter.add_step("thought", "Thinking 2")

        thought_steps = self.formatter.get_steps_by_type("thought")
        self.assertEqual(len(thought_steps), 2)

        action_steps = self.formatter.get_steps_by_type("action")
        self.assertEqual(len(action_steps), 1)


class TestToolRegistryLoader(unittest.TestCase):
    """Test the ToolRegistryLoader class."""

    def setUp(self):
        # Use the actual tool_registry directory
        self.registry_path = Path(__file__).parent.parent / "tool_registry"
        self.loader = ToolRegistryLoader(self.registry_path)

    def test_initialization(self):
        """Test loader initializes correctly."""
        self.assertEqual(self.loader.registry_path, self.registry_path)
        self.assertEqual(len(self.loader.tools), 0)

    def test_load_all_tools(self):
        """Test loading all tool definitions."""
        tools = self.loader.load_all_tools()

        # Should have at least 3 tools (weather, uppercase, count_word)
        self.assertGreaterEqual(len(tools), 3)
        self.assertIn("weather", tools)
        self.assertIn("uppercase", tools)
        self.assertIn("count_word", tools)

    def test_load_tools_validates_structure(self):
        """Test that loaded tools have required fields."""
        tools = self.loader.load_all_tools()

        for tool_name, tool_def in tools.items():
            self.assertIn("name", tool_def)
            self.assertIn("description", tool_def)
            self.assertIn("url", tool_def)
            self.assertIn("method", tool_def)

    def test_convert_to_openai_format(self):
        """Test converting tools to OpenAI format."""
        tools = self.loader.load_all_tools()
        openai_tools = self.loader.convert_to_openai_format(tools)

        self.assertGreater(len(openai_tools), 0)

        # Check first tool structure
        tool = openai_tools[0]
        self.assertEqual(tool["type"], "function")
        self.assertIn("function", tool)
        self.assertIn("name", tool["function"])
        self.assertIn("description", tool["function"])
        self.assertIn("parameters", tool["function"])

        # Check parameters structure
        params = tool["function"]["parameters"]
        self.assertEqual(params["type"], "object")
        self.assertIn("properties", params)
        self.assertIn("required", params)

    def test_get_tool_definition(self):
        """Test retrieving specific tool definition."""
        self.loader.load_all_tools()
        weather_def = self.loader.get_tool_definition("weather")

        self.assertEqual(weather_def["name"], "weather")
        self.assertEqual(weather_def["method"], "GET")
        self.assertIn("params", weather_def)

    def test_get_tool_definition_not_found(self):
        """Test error when tool not found."""
        self.loader.load_all_tools()

        with self.assertRaises(KeyError):
            self.loader.get_tool_definition("nonexistent_tool")

    def test_get_tool_names(self):
        """Test getting list of tool names."""
        self.loader.load_all_tools()
        names = self.loader.get_tool_names()

        self.assertIn("weather", names)
        self.assertIn("uppercase", names)

    def test_get_tool_count(self):
        """Test getting tool count."""
        self.assertEqual(self.loader.get_tool_count(), 0)
        self.loader.load_all_tools()
        self.assertGreater(self.loader.get_tool_count(), 0)

    def test_invalid_registry_path(self):
        """Test error when registry path doesn't exist."""
        invalid_loader = ToolRegistryLoader(Path("/nonexistent/path"))

        with self.assertRaises(FileNotFoundError):
            invalid_loader.load_all_tools()


class TestAgentControllerInitialization(unittest.TestCase):
    """Test AgentController initialization and configuration."""

    def test_missing_api_key(self):
        """Test error when no API key provided."""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                AgentController()

            self.assertIn("OpenAI API key", str(context.exception))

    def test_api_key_from_parameter(self):
        """Test initialization with API key parameter."""
        controller = AgentController(api_key="test_key_123")
        self.assertEqual(controller.api_key, "test_key_123")

    def test_api_key_from_environment(self):
        """Test initialization with API key from environment."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env_key_456'}):
            controller = AgentController()
            self.assertEqual(controller.api_key, "env_key_456")

    def test_default_tool_registry_path(self):
        """Test default tool registry path."""
        controller = AgentController(api_key="test_key")
        expected_path = Path(__file__).parent.parent / "tool_registry"
        self.assertEqual(controller.tool_registry_path, expected_path)

    def test_custom_tool_registry_path(self):
        """Test custom tool registry path."""
        custom_path = Path(__file__).parent.parent / "tool_registry"
        controller = AgentController(
            api_key="test_key",
            tool_registry_path=custom_path
        )
        self.assertEqual(controller.tool_registry_path, custom_path)

    def test_invalid_tool_registry_path(self):
        """Test error when tool registry path doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            AgentController(
                api_key="test_key",
                tool_registry_path=Path("/nonexistent/path")
            )

    def test_default_parameters(self):
        """Test default parameter values."""
        controller = AgentController(api_key="test_key")

        self.assertEqual(controller.model, "gpt-4o")
        self.assertEqual(controller.max_iterations, 5)
        self.assertTrue(controller.use_react)

    def test_custom_parameters(self):
        """Test custom parameter values."""
        controller = AgentController(
            api_key="test_key",
            model="gpt-3.5-turbo",
            max_iterations=10,
            use_react=False
        )

        self.assertEqual(controller.model, "gpt-3.5-turbo")
        self.assertEqual(controller.max_iterations, 10)
        self.assertFalse(controller.use_react)

    @patch('agent_controller.controller.OpenAI')
    def test_openai_client_initialization(self, mock_openai):
        """Test OpenAI client is initialized."""
        controller = AgentController(api_key="test_key")

        mock_openai.assert_called_once_with(api_key="test_key")


class TestAgentControllerIntegration(unittest.TestCase):
    """
    Integration tests requiring OpenAI API key and running tool_api server.

    These tests are skipped if:
    - OPENAI_API_KEY environment variable is not set
    - --skip-integration flag is provided
    """

    @classmethod
    def setUpClass(cls):
        """Start API server before integration tests."""
        # Check if we should skip integration tests
        if "--skip-integration" in sys.argv:
            raise unittest.SkipTest("Skipping integration tests (--skip-integration flag)")

        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            raise unittest.SkipTest("OPENAI_API_KEY not set")

        # Start server unless using external
        if "--use-external-server" not in sys.argv:
            print("\nStarting tool_api server for integration tests...")
            cls.server_proc, cls.log_file = start_api_server("127.0.0.1", 8000)
        else:
            cls.server_proc = None
            cls.log_file = None
            print("\nUsing external server for integration tests...")

    @classmethod
    def tearDownClass(cls):
        """Stop API server after integration tests."""
        if cls.server_proc:
            print("\nStopping tool_api server...")
            stop_api_server(cls.server_proc, cls.log_file)

    def setUp(self):
        """Initialize controller for each test."""
        self.controller = AgentController()

    def test_simple_query_no_tools(self):
        """Test query that doesn't require tools."""
        result = self.controller.process_query("What is 2 + 2?")

        self.assertTrue(result['success'])
        self.assertIn("4", result['answer'])

        # Should have load_registry and final_answer steps, no tool execution
        tool_steps = [s for s in result['steps'] if s['step_type'] == 'action']
        self.assertEqual(len(tool_steps), 0)

    def test_simple_tool_query(self):
        """Test query requiring single tool call."""
        result = self.controller.process_query("Convert 'hello world' to uppercase")

        self.assertTrue(result['success'])
        self.assertIn("HELLO WORLD", result['answer'].upper())

        # Should have action and observation steps
        action_steps = [s for s in result['steps'] if s['step_type'] == 'action']
        observation_steps = [s for s in result['steps'] if s['step_type'] == 'observation']

        self.assertGreater(len(action_steps), 0)
        self.assertGreater(len(observation_steps), 0)

    def test_weather_query(self):
        """Test weather tool query."""
        result = self.controller.process_query(
            "What's the weather in San Francisco on 2024-12-25?"
        )

        self.assertTrue(result['success'])
        self.assertIn("San Francisco", result['answer'])

        # Verify tool was called
        action_steps = [s for s in result['steps'] if s['step_type'] == 'action']
        self.assertGreater(len(action_steps), 0)

        # Check that weather tool was used
        weather_called = any(
            s['details']['tool_name'] == 'weather'
            for s in action_steps
        )
        self.assertTrue(weather_called)

    def test_react_reasoning_recorded(self):
        """Test that ReAct reasoning is recorded in steps."""
        result = self.controller.process_query("Count words in 'hello world'")

        self.assertTrue(result['success'])

        # Should have thought steps (if ReAct is enabled)
        thought_steps = [s for s in result['steps'] if s['step_type'] == 'thought']

        if self.controller.use_react:
            self.assertGreater(len(thought_steps), 0)
            # Check that reasoning contains content
            for step in thought_steps:
                self.assertIn('reasoning', step['details'])
                self.assertIsInstance(step['details']['reasoning'], str)

    def test_multiple_tools_query(self):
        """Test query that might use multiple tools."""
        result = self.controller.process_query(
            "Convert 'test string' to uppercase and count its words"
        )

        self.assertTrue(result['success'])

        # Count action steps
        action_steps = [s for s in result['steps'] if s['step_type'] == 'action']

        # Might call 1 or 2 tools depending on LLM reasoning
        self.assertGreater(len(action_steps), 0)

    def test_error_handling_invalid_tool(self):
        """Test handling when LLM tries to call non-existent tool."""
        # This test is tricky - we'd need to mock the OpenAI response
        # For now, just verify the controller handles errors gracefully
        pass  # Skip for now

    def test_response_structure(self):
        """Test that response has correct structure."""
        result = self.controller.process_query("Say hello")

        # Check required fields
        self.assertIn('success', result)
        self.assertIn('answer', result)
        self.assertIn('steps', result)
        self.assertIn('error', result)

        # Check types
        self.assertIsInstance(result['success'], bool)
        self.assertIsInstance(result['answer'], str)
        self.assertIsInstance(result['steps'], list)

        # Check step structure
        for step in result['steps']:
            self.assertIn('step_number', step)
            self.assertIn('step_type', step)
            self.assertIn('description', step)
            self.assertIn('timestamp', step)


def main():
    """Main test runner."""
    # Parse custom arguments
    import sys
    unittest_args = [sys.argv[0]]

    # Pass through unittest arguments, keep custom ones for our logic
    for arg in sys.argv[1:]:
        if arg not in ['--use-external-server', '--skip-integration']:
            unittest_args.append(arg)

    # Run tests
    unittest.main(argv=unittest_args, verbosity=2)


if __name__ == '__main__':
    main()
