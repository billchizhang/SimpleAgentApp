"""
Agent Controller Module

This module provides an LLM-driven orchestration layer for tool selection and execution.
It integrates OpenAI's function calling with the generic API calling framework, implementing
ReAct-style reasoning for transparent agent behavior.

Main Components:
- AgentController: Main orchestration class for processing user queries
- ToolRegistryLoader: Loads and converts tool definitions to OpenAI format
- ResponseFormatter: Records execution steps and formats responses
- Step: Dataclass representing individual execution steps

Usage:
    from agent_controller import AgentController

    # Initialize controller
    controller = AgentController(api_key="sk-...")

    # Process a query
    result = controller.process_query("What's the weather in Boston?")

    # Access results
    print(result['answer'])
    for step in result['steps']:
        print(f"{step['step_number']}. {step['description']}")
"""

from .controller import AgentController
from .response_formatter import ResponseFormatter, Step
from .tool_loader import ToolRegistryLoader

__all__ = [
    "AgentController",
    "ResponseFormatter",
    "Step",
    "ToolRegistryLoader",
]

__version__ = "1.0.0"
