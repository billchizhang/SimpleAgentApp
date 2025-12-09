"""
Test script for AgentController with real LLM responses using ReAct loop integration.

This script demonstrates how to use the agent_controller module to:
1. Initialize the controller with OpenAI API key
2. Process user queries with tool calling
3. View the complete execution trace including ReAct reasoning

Prerequisites:
- Install dependencies: pip install -r requirements.txt
- Set OPENAI_API_KEY environment variable or provide it directly
- Start the tool_api server: python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000

Usage:
    # With environment variable
    export OPENAI_API_KEY="sk-..."
    python tests/test_llm_response.py

    # Or set in .env file
    # OPENAI_API_KEY=sk-...
    python tests/test_llm_response.py
"""

import os
from dotenv import load_dotenv
from agent_controller import AgentController


def print_step(step):
    """Pretty print a single step."""
    step_type = step['step_type']
    step_num = step['step_number']
    description = step['description']

    # Color coding by step type (if terminal supports it)
    colors = {
        'load_registry': '\033[94m',  # Blue
        'thought': '\033[95m',         # Magenta
        'action': '\033[93m',          # Yellow
        'observation': '\033[92m',     # Green
        'final_answer': '\033[96m',    # Cyan
        'error': '\033[91m'            # Red
    }
    reset = '\033[0m'

    color = colors.get(step_type, '')

    print(f"{color}[Step {step_num}] {step_type.upper()}: {description}{reset}")

    # Print reasoning for thought steps
    if step_type == 'thought' and step.get('details', {}).get('reasoning'):
        reasoning = step['details']['reasoning']
        print(f"  💭 {reasoning}")

    # Print tool details for action steps
    if step_type == 'action' and step.get('details'):
        tool_name = step['details'].get('tool_name')
        arguments = step['details'].get('arguments')
        print(f"  🔧 Tool: {tool_name}")
        print(f"  📝 Arguments: {arguments}")

    # Print results for observation steps
    if step_type == 'observation' and step.get('details'):
        result = step['details'].get('result')
        if 'error' not in result:
            print(f"  ✅ Result: {result}")
        else:
            print(f"  ❌ Error: {result['error']}")

    # Print errors
    if step.get('error'):
        print(f"  ❌ Error: {step['error']}")

    print()  # Blank line


def print_response(result):
    """Pretty print the complete response."""
    print("=" * 80)
    print("AGENT CONTROLLER RESPONSE")
    print("=" * 80)

    print(f"\n🎯 Success: {result['success']}")

    print("\n📋 EXECUTION TRACE:")
    print("-" * 80)
    for step in result['steps']:
        print_step(step)

    print("-" * 80)
    print(f"\n💬 FINAL ANSWER:\n{result['answer']}")

    if result.get('error'):
        print(f"\n❌ ERROR: {result['error']}")

    print("\n" + "=" * 80)


def main():
    """Run example queries."""
    # Load environment variables from .env file
    load_dotenv()

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set it using:")
        print("  export OPENAI_API_KEY='sk-...'")
        print("Or create a .env file with:")
        print("  OPENAI_API_KEY=sk-...")
        return

    print("🚀 Initializing AgentController with ReAct loop...\n")

    # Initialize controller
    controller = AgentController(
        api_key=api_key,
        model="gpt-4o",
        max_iterations=5,
        use_react=True  # Enable ReAct reasoning
    )

    print("✅ Controller initialized successfully!\n")

    # Example queries
    queries = [
        "What's the weather in Boston on 2024-12-25?",
        "Convert 'hello world' to uppercase",
        "Count the words in 'The quick brown fox jumps over the lazy dog'",
        "What is the capital of France?",  # No tools needed
    ]

    print(f"Running {len(queries)} example queries...\n")

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"QUERY {i}/{len(queries)}: {query}")
        print(f"{'='*80}\n")

        try:
            # Process query
            result = controller.process_query(query)

            # Print detailed response
            print_response(result)

            # Wait for user input to continue (optional)
            if i < len(queries):
                input("\nPress Enter to continue to next query...")

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()

    print("\n✅ All queries completed!\n")


if __name__ == '__main__':
    main()
