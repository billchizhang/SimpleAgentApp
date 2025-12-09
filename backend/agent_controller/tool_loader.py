from pathlib import Path
from typing import Dict, List, Any
import json


class ToolRegistryLoader:
    """
    Loads tool definitions from JSON files and converts them to OpenAI function format.

    This class handles:
    - Loading tool definitions from the tool_registry directory
    - Converting tool registry format to OpenAI function calling schema
    - Providing access to original tool definitions for execution
    """

    def __init__(self, registry_path: Path):
        """
        Initialize the tool registry loader.

        Args:
            registry_path: Path to the tool_registry directory containing JSON files
        """
        self.registry_path = Path(registry_path)
        self.tools: Dict[str, Any] = {}
        self.openai_tools: List[Dict[str, Any]] = []

    def load_all_tools(self) -> Dict[str, Any]:
        """
        Load all .json files from tool_registry directory.

        Returns:
            Dict mapping tool names to their complete definitions

        Raises:
            FileNotFoundError: If registry_path doesn't exist
            json.JSONDecodeError: If a tool definition file contains invalid JSON
        """
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Tool registry directory not found: {self.registry_path}")

        if not self.registry_path.is_dir():
            raise ValueError(f"Tool registry path is not a directory: {self.registry_path}")

        # Load all .json files from the directory
        tool_files = list(self.registry_path.glob("*.json"))

        if not tool_files:
            raise ValueError(f"No tool definition files found in: {self.registry_path}")

        for tool_file in tool_files:
            try:
                with open(tool_file, 'r') as f:
                    tool_def = json.load(f)

                # Validate that the tool has required fields
                if "name" not in tool_def:
                    raise ValueError(f"Tool definition missing 'name' field: {tool_file}")

                tool_name = tool_def["name"]
                self.tools[tool_name] = tool_def

            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON in tool file {tool_file}: {e.msg}",
                    e.doc,
                    e.pos
                )

        return self.tools

    def convert_to_openai_format(self, tools: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert tool registry format to OpenAI function calling format.

        Input format (tool_registry/*.json):
        {
            "name": "weather",
            "description": "...",
            "url": "http://...",
            "method": "GET",
            "params": {
                "city": {"type": "string", "required": true, "description": "..."},
                "date": {"type": "string", "required": true, "format": "YYYY-MM-DD", ...}
            }
        }

        Output format (OpenAI function calling):
        {
            "type": "function",
            "function": {
                "name": "weather",
                "description": "...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "..."},
                        "date": {"type": "string", "description": "..."}
                    },
                    "required": ["city", "date"]
                }
            }
        }

        Args:
            tools: Dict of tool definitions from load_all_tools()

        Returns:
            List of tool definitions in OpenAI function calling format
        """
        openai_tools = []

        for tool_name, tool_def in tools.items():
            # Build OpenAI parameters schema
            properties = {}
            required = []

            # Process params if they exist
            if "params" in tool_def and tool_def["params"]:
                for param_name, param_def in tool_def["params"].items():
                    # Extract basic type and description
                    properties[param_name] = {
                        "type": param_def.get("type", "string"),
                        "description": param_def.get("description", "")
                    }

                    # Add format info to description if present
                    if "format" in param_def:
                        properties[param_name]["description"] += f" Format: {param_def['format']}"

                    # Track required parameters
                    if param_def.get("required", False):
                        required.append(param_name)

            # Build OpenAI function definition
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }

            openai_tools.append(openai_tool)

        self.openai_tools = openai_tools
        return openai_tools

    def get_tool_definition(self, tool_name: str) -> Dict[str, Any]:
        """
        Get original tool definition by name for execution.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Complete tool definition including url, method, params

        Raises:
            KeyError: If tool_name not found in loaded tools
        """
        if tool_name not in self.tools:
            raise KeyError(f"Tool '{tool_name}' not found in registry. Available tools: {list(self.tools.keys())}")

        return self.tools[tool_name]

    def get_tool_names(self) -> List[str]:
        """
        Get list of all loaded tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_tool_count(self) -> int:
        """
        Get the number of loaded tools.

        Returns:
            Count of tools
        """
        return len(self.tools)
