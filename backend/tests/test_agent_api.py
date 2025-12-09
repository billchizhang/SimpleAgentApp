"""
Test script for Agent API endpoints.

Tests the FastAPI REST API with various query scenarios.
Requires both tool_api and agent_api to be running.

Usage:
    # Start both servers first:
    # Terminal 1: python -m uvicorn tool_api.main:app --host 127.0.0.1 --port 8000
    # Terminal 2: python -m uvicorn agent_api.main:app --host 127.0.0.1 --port 8001

    # Then run tests:
    python tests/test_agent_api.py

    # Or use Docker Compose:
    docker-compose up
    python tests/test_agent_api.py --host localhost
"""

import requests
import json
import sys
import time
from typing import Dict, Any


BASE_URL = "http://localhost:8001"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_response(response: Dict[str, Any], show_steps: bool = True):
    """Pretty print API response."""
    print(f"\n✓ Success: {response.get('success', False)}")
    print(f"📝 Answer: {response.get('answer', 'N/A')}")

    if response.get('error'):
        print(f"❌ Error: {response['error']}")

    if show_steps and 'steps' in response:
        print(f"\n📋 Execution Steps ({len(response['steps'])} total):")
        for step in response['steps']:
            step_type = step['step_type']
            description = step['description']
            print(f"  [{step['step_number']}] {step_type}: {description}")

            # Show reasoning for thought steps
            if step_type == 'thought' and step.get('details', {}).get('reasoning'):
                print(f"      💭 {step['details']['reasoning']}")

    if 'metadata' in response:
        meta = response['metadata']
        print(f"\n📊 Metadata:")
        print(f"  - Model: {meta.get('model')}")
        print(f"  - Total steps: {meta.get('total_steps')}")
        print(f"  - Tools called: {meta.get('tools_called')}")
        print(f"  - ReAct enabled: {meta.get('react_enabled')}")


def test_health_check():
    """Test the health check endpoint."""
    print_section("Test 1: Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()

        health = response.json()
        print(f"\n✓ Status: {health['status']}")
        print(f"✓ Agent Controller: {'✓' if health['agent_controller_available'] else '✗'}")
        print(f"✓ Tool Registry: {'✓' if health['tool_registry_available'] else '✗'}")
        print(f"✓ OpenAI Configured: {'✓' if health['openai_api_configured'] else '✗'}")

        return health['status'] == 'healthy'

    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        return False


def test_list_tools():
    """Test the list tools endpoint."""
    print_section("Test 2: List Available Tools")

    try:
        response = requests.get(f"{BASE_URL}/tools")
        response.raise_for_status()

        data = response.json()
        print(f"\n✓ Total tools: {data['total_tools']}")

        for tool_name, tool_info in data['tools'].items():
            print(f"\n📦 {tool_name}:")
            print(f"   Description: {tool_info['description']}")
            print(f"   Method: {tool_info['method']}")

        return True

    except Exception as e:
        print(f"\n❌ List tools failed: {e}")
        return False


def test_simple_query():
    """Test a simple query without tools."""
    print_section("Test 3: Simple Query (No Tools)")

    try:
        payload = {
            "query": "What is 2 + 2?",
            "use_react": True
        }

        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        result = response.json()
        print_response(result)

        # Verify no tools were called
        tool_calls = len([s for s in result['steps'] if s['step_type'] == 'action'])
        assert tool_calls == 0, "Expected no tool calls for simple math question"

        return result['success']

    except Exception as e:
        print(f"\n❌ Simple query failed: {e}")
        return False


def test_tool_query():
    """Test a query that requires tool calling."""
    print_section("Test 4: Tool Query (Uppercase)")

    try:
        payload = {
            "query": "Convert 'hello world' to uppercase",
            "use_react": True
        }

        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        result = response.json()
        print_response(result)

        # Verify tool was called
        tool_calls = len([s for s in result['steps'] if s['step_type'] == 'action'])
        assert tool_calls > 0, "Expected at least one tool call"

        # Verify answer contains uppercase text
        assert "HELLO WORLD" in result['answer'].upper(), "Answer should contain uppercase text"

        return result['success']

    except Exception as e:
        print(f"\n❌ Tool query failed: {e}")
        return False


def test_query_with_history():
    """Test a query with chat history."""
    print_section("Test 5: Query with Chat History")

    try:
        # First query
        payload1 = {
            "query": "What is the weather in Boston?",
            "use_react": True
        }

        response1 = requests.post(f"{BASE_URL}/query", json=payload1)
        response1.raise_for_status()
        result1 = response1.json()

        print("First query:")
        print(f"  Q: {payload1['query']}")
        print(f"  A: {result1['answer'][:100]}...")

        # Follow-up query with history
        payload2 = {
            "query": "What about tomorrow?",
            "chat_history": [
                {"role": "user", "content": payload1['query']},
                {"role": "assistant", "content": result1['answer']}
            ],
            "use_react": True
        }

        response2 = requests.post(f"{BASE_URL}/query", json=payload2)
        response2.raise_for_status()
        result2 = response2.json()

        print("\nFollow-up query with context:")
        print(f"  Q: {payload2['query']}")
        print(f"  A: {result2['answer'][:100]}...")

        print_response(result2, show_steps=False)

        return result2['success']

    except Exception as e:
        print(f"\n❌ Query with history failed: {e}")
        return False


def test_multiple_tools_query():
    """Test a query that might use multiple tools."""
    print_section("Test 6: Multi-Tool Query")

    try:
        payload = {
            "query": "Convert 'test string' to uppercase and count how many words it has",
            "use_react": True
        }

        response = requests.post(f"{BASE_URL}/query", json=payload)
        response.raise_for_status()

        result = response.json()
        print_response(result)

        # Count tool calls
        tool_calls = len([s for s in result['steps'] if s['step_type'] == 'action'])
        print(f"\n📊 Tool calls made: {tool_calls}")

        return result['success']

    except Exception as e:
        print(f"\n❌ Multi-tool query failed: {e}")
        return False


def test_react_disabled():
    """Test query with ReAct disabled."""
    print_section("Test 7: Query with ReAct Disabled")

    try:
        payload = {
            "query": "Convert 'hello' to uppercase",
            "use_react": False
        }

        response = requests.post(f"{BASE_URL}/query", json=payload)
        response.raise_for_status()

        result = response.json()
        print_response(result, show_steps=False)

        # Should have fewer thought steps with ReAct disabled
        thought_steps = len([s for s in result['steps'] if s['step_type'] == 'thought'])
        print(f"\n💭 Thought steps: {thought_steps} (should be minimal with ReAct disabled)")

        return result['success']

    except Exception as e:
        print(f"\n❌ ReAct disabled test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  AGENT API TEST SUITE")
    print("=" * 80)
    print(f"\nTesting against: {BASE_URL}")
    print("\nPrerequisites:")
    print("  1. Tool API running on port 8000")
    print("  2. Agent API running on port 8001")
    print("  3. OPENAI_API_KEY environment variable set")

    # Wait a moment for server to be ready
    print("\nWaiting for server to be ready...")
    time.sleep(2)

    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("List Tools", test_list_tools),
        ("Simple Query", test_simple_query),
        ("Tool Query", test_tool_query),
        ("Query with History", test_query_with_history),
        ("Multi-Tool Query", test_multiple_tools_query),
        ("ReAct Disabled", test_react_disabled),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
