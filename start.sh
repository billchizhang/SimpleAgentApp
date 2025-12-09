#!/bin/bash
set -e

echo "🚀 Starting SimpleAgentApp..."
echo ""

# Check if OPENAI_API_KEY is set (only needed for agent_api)
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set. Agent API will not be available."
    echo "   Set it with: docker run -e OPENAI_API_KEY=sk-... simpleagentapp"
    echo ""
fi

# Function to handle shutdown
shutdown() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $TOOL_API_PID $AGENT_API_PID $FRONTEND_PID 2>/dev/null
    wait $TOOL_API_PID $AGENT_API_PID $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

trap shutdown SIGTERM SIGINT

# Start Frontend in background
echo "🌐 Starting Frontend on port 3000..."
serve -s frontend/build -l 3000 &
FRONTEND_PID=$!

# Give frontend a moment to start
sleep 1

# Change to backend directory
cd backend

# Start Tool API in background
echo "📦 Starting Tool API on port 8000..."
uvicorn tool_api.main:app --host 0.0.0.0 --port 8000 &
TOOL_API_PID=$!

# Give tool API a moment to start
sleep 2

# Start Agent API in background (only if API key is set)
if [ -n "$OPENAI_API_KEY" ]; then
    echo "🤖 Starting Agent API on port 8001..."
    uvicorn agent_api.main:app --host 0.0.0.0 --port 8001 &
    AGENT_API_PID=$!
else
    echo "⏭️  Skipping Agent API (no OPENAI_API_KEY)"
    AGENT_API_PID=""
fi

echo ""
echo "✅ SimpleAgentApp is running!"
echo ""
echo "📡 Available services:"
echo "   Frontend:  http://localhost:3000"
echo "   Tool API:  http://localhost:8000/docs"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "   Agent API: http://localhost:8001/docs"
fi
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all processes
wait $FRONTEND_PID $TOOL_API_PID $AGENT_API_PID
