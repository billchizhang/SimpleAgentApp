from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import os

from openai import OpenAI, OpenAIError, APIError, RateLimitError, AuthenticationError

from function_call.generic_call import ApiToolCall, call_api
from .tool_loader import ToolRegistryLoader
from .response_formatter import ResponseFormatter


# ReAct-style system prompt for explicit reasoning
REACT_SYSTEM_PROMPT = """You are a helpful assistant with access to tools.

Before calling tools, briefly explain your reasoning about what information you need.
After receiving results, explain what you learned and whether you need more information.

Use the available tools when needed to answer user questions accurately.

Think step-by-step and be explicit about your reasoning process."""

# Simple system prompt without ReAct reasoning
SIMPLE_SYSTEM_PROMPT = """You are a helpful assistant with access to tools.

Use the available tools when needed to answer user questions accurately."""


class AgentController:
    """
    Orchestrates LLM-driven tool selection and execution for user queries.

    This controller:
    1. Loads available tools from the tool_registry/ directory
    2. Converts tool definitions to OpenAI function calling format
    3. Sends user queries to OpenAI with available tools
    4. Executes API calls via the generic_call module
    5. Supports multi-step tool execution (iterative calls)
    6. Records all steps including ReAct-style reasoning (Thought, Action, Observation)
    7. Returns structured responses with complete execution traces
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        tool_registry_path: Optional[Path] = None,
        model: str = "gpt-4o",
        max_iterations: int = 5,
        use_react: bool = True
    ):
        """
        Initialize the AgentController.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var
            tool_registry_path: Path to tool_registry directory. Defaults to ../tool_registry/
            model: OpenAI model to use for function calling (default: gpt-4o)
            max_iterations: Maximum number of tool call iterations to prevent loops (default: 5)
            use_react: Enable ReAct-style prompting for explicit reasoning (default: True)

        Raises:
            ValueError: If api_key is not provided and OPENAI_API_KEY env var is not set
            FileNotFoundError: If tool_registry_path doesn't exist
        """
        # Resolve API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key must be provided either as constructor parameter "
                "or via OPENAI_API_KEY environment variable"
            )

        # Resolve tool registry path
        if tool_registry_path is None:
            # Default to ../tool_registry/ relative to this file
            default_path = Path(__file__).parent.parent / "tool_registry"
            self.tool_registry_path = default_path
        else:
            self.tool_registry_path = Path(tool_registry_path)

        # Validate registry path exists
        if not self.tool_registry_path.exists():
            raise FileNotFoundError(
                f"Tool registry directory not found: {self.tool_registry_path}"
            )

        self.model = model
        self.max_iterations = max_iterations
        self.use_react = use_react

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        # Initialize tool loader and formatter
        self.tool_loader = ToolRegistryLoader(self.tool_registry_path)
        self.formatter: Optional[ResponseFormatter] = None

        # Tools will be loaded on first query
        self.tools: Dict[str, Any] = {}
        self.openai_tools: List[Dict[str, Any]] = []
        self._tools_loaded = False

    def _load_tools(self) -> None:
        """
        Load and convert tool definitions from registry.

        Raises:
            FileNotFoundError: If registry directory not found
            json.JSONDecodeError: If tool definitions contain invalid JSON
            ValueError: If no tools found or tool definitions invalid
        """
        if self._tools_loaded:
            return

        try:
            self.tools = self.tool_loader.load_all_tools()
            self.openai_tools = self.tool_loader.convert_to_openai_format(self.tools)
            self._tools_loaded = True

            self.formatter.add_step(
                "load_registry",
                f"Loaded {len(self.tools)} tools from registry",
                details={
                    "tools_loaded": list(self.tools.keys()),
                    "registry_path": str(self.tool_registry_path)
                }
            )

        except FileNotFoundError as e:
            self.formatter.add_step(
                "load_registry",
                "Failed to load tool registry",
                error=str(e)
            )
            raise

        except json.JSONDecodeError as e:
            self.formatter.add_step(
                "load_registry",
                "Failed to parse tool definition",
                error=f"Invalid JSON in tool registry: {str(e)}"
            )
            raise

        except ValueError as e:
            self.formatter.add_step(
                "load_registry",
                "Invalid tool registry",
                error=str(e)
            )
            raise

    def _build_messages(self, query: str) -> List[Dict[str, str]]:
        """
        Build initial messages for OpenAI API call.

        Args:
            query: User's query

        Returns:
            List of message dicts with system and user messages
        """
        system_prompt = REACT_SYSTEM_PROMPT if self.use_react else SIMPLE_SYSTEM_PROMPT

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

    def _call_openai_with_tools(self, messages: List[Dict[str, Any]]) -> Any:
        """
        Call OpenAI API with tool definitions.

        Args:
            messages: Conversation history

        Returns:
            OpenAI completion response

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            APIError: General OpenAI API error
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.openai_tools
            )

            message = response.choices[0].message

            # Record reasoning (Thought) if present
            if message.content and self.use_react:
                self.formatter.add_step(
                    "thought",
                    "Agent reasoning",
                    details={"reasoning": message.content}
                )

            # Record tool calls (Action) if present
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    self.formatter.add_step(
                        "action",
                        f"Calling tool: {tool_call.function.name}",
                        details={
                            "tool_name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments)
                        }
                    )

            return response

        except AuthenticationError as e:
            self.formatter.add_step(
                "error",
                "OpenAI authentication failed",
                error="Invalid API key"
            )
            raise

        except RateLimitError as e:
            self.formatter.add_step(
                "error",
                "OpenAI rate limit exceeded",
                error=str(e)
            )
            raise

        except APIError as e:
            self.formatter.add_step(
                "error",
                "OpenAI API error",
                error=str(e)
            )
            raise

    def _execute_single_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single tool call by converting to ApiToolCall and using call_api.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool call

        Returns:
            Result from the API call (or error dict)
        """
        try:
            # Get tool definition
            tool_def = self.tool_loader.get_tool_definition(tool_name)

            # Build ApiToolCall instance
            api_tool_call = ApiToolCall(
                url=tool_def["url"],
                method=tool_def["method"],
                params=arguments if tool_def["method"].upper() == "GET" else None,
                json_body=arguments if tool_def["method"].upper() != "GET" else None
            )

            # Execute API call
            result = call_api(api_tool_call)

            # Record observation
            if "error" in result:
                self.formatter.add_step(
                    "observation",
                    f"Tool {tool_name} execution failed",
                    details={
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result
                    },
                    error=result["error"]
                )
            else:
                self.formatter.add_step(
                    "observation",
                    f"Received result from {tool_name}",
                    details={
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result
                    }
                )

            return result

        except KeyError as e:
            # Tool not found in registry
            error_result = {
                "error": f"Tool '{tool_name}' not found in registry. Available tools: {list(self.tools.keys())}"
            }
            self.formatter.add_step(
                "observation",
                f"Invalid tool requested: {tool_name}",
                error=error_result["error"]
            )
            return error_result

        except Exception as e:
            # Unexpected error
            error_result = {"error": f"Failed to execute tool {tool_name}: {str(e)}"}
            self.formatter.add_step(
                "observation",
                f"Tool execution error: {tool_name}",
                error=error_result["error"]
            )
            return error_result

    def _execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls from OpenAI response.

        Args:
            tool_calls: List of tool call objects from OpenAI

        Returns:
            List of results to send back to OpenAI
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            result = self._execute_single_tool(tool_name, arguments)
            results.append(result)

        return results

    def process_query_with_history(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query with optional chat history.

        Args:
            query: User's natural language query
            chat_history: List of previous messages [{"role": "user/assistant", "content": "..."}]

        Returns:
            Dict containing:
                - success: bool
                - answer: str (final answer to user)
                - steps: List[Dict] (all steps taken)
                - error: Optional[str] (if any error occurred)
        """
        # Initialize formatter for this query
        self.formatter = ResponseFormatter()

        try:
            # Load tools if not already loaded
            self._load_tools()

            # Build messages with history
            system_prompt = REACT_SYSTEM_PROMPT if self.use_react else SIMPLE_SYSTEM_PROMPT
            messages = [{"role": "system", "content": system_prompt}]

            # Add chat history if provided
            if chat_history:
                messages.extend(chat_history)

            # Add current query
            messages.append({"role": "user", "content": query})

            # Continue with existing iteration logic
            return self._process_messages(messages)

        except (AuthenticationError, RateLimitError, APIError) as e:
            return self.formatter.format_final_response(
                answer="Unable to process request due to API error.",
                success=False,
                error=str(e)
            )
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            return self.formatter.format_final_response(
                answer="Unable to process request: tool registry error.",
                success=False,
                error=str(e)
            )
        except Exception as e:
            self.formatter.add_step(
                "error",
                "Unexpected error occurred",
                error=str(e)
            )
            return self.formatter.format_final_response(
                answer="Unable to process request due to unexpected error.",
                success=False,
                error=str(e)
            )

    def _process_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process messages through the ReAct loop.

        Args:
            messages: List of conversation messages

        Returns:
            Formatted response with answer and steps
        """
        iteration = 0

        while iteration < self.max_iterations:
            # Call OpenAI with tools
            response = self._call_openai_with_tools(messages)

            choice = response.choices[0]
            message = choice.message

            # Check finish reason
            if choice.finish_reason == "stop":
                # Final answer reached
                final_answer = message.content or "No response generated."

                self.formatter.add_step(
                    "final_answer",
                    "Generated final answer",
                    details={"finish_reason": "stop", "iterations": iteration}
                )

                return self.formatter.format_final_response(
                    answer=final_answer,
                    success=True
                )

            elif choice.finish_reason == "tool_calls" and message.tool_calls:
                # Execute tool calls
                tool_results = self._execute_tool_calls(message.tool_calls)

                # Add assistant's message to conversation
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })

                # Add tool results to conversation
                for tool_call, result in zip(message.tool_calls, tool_results):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

                # Continue to next iteration
                iteration += 1

            else:
                # Unexpected finish reason
                self.formatter.add_step(
                    "error",
                    f"Unexpected finish reason: {choice.finish_reason}",
                    error=f"OpenAI returned unexpected finish_reason: {choice.finish_reason}"
                )

                return self.formatter.format_final_response(
                    answer="Unable to process query due to unexpected response.",
                    success=False,
                    error=f"Unexpected finish reason: {choice.finish_reason}"
                )

        # Max iterations reached
        self.formatter.add_step(
            "error",
            "Maximum iteration limit reached",
            error=f"Stopped after {self.max_iterations} iterations to prevent infinite loop"
        )

        return self.formatter.format_final_response(
            answer="Unable to complete request: too many tool calls required.",
            success=False,
            error=f"Maximum iteration limit ({self.max_iterations}) reached"
        )

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point: process a user query and return the complete response.

        Args:
            query: User's natural language query

        Returns:
            Dict containing:
                - success: bool
                - answer: str (final answer to user)
                - steps: List[Dict] (all steps taken)
                - error: Optional[str] (if any error occurred)
        """
        # Use process_query_with_history without history
        return self.process_query_with_history(query, chat_history=None)
