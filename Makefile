# SimpleAgentApp Makefile
# Quick commands for building and running the application

.PHONY: help build run run-no-key stop clean test test-auth

# Default target
help:
	@echo "SimpleAgentApp - Quick Start Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make build        - Build Docker image"
	@echo "  make run          - Run both services (requires OPENAI_API_KEY in .env)"
	@echo "  make run-no-key   - Run tool API only (no OpenAI key needed)"
	@echo "  make stop         - Stop running container"
	@echo "  make clean        - Remove Docker image and containers"
	@echo "  make test         - Run all tests"
	@echo "  make test-auth    - Run authentication tests only"
	@echo "  make logs         - View container logs"
	@echo ""
	@echo "One-liner quick start:"
	@echo "  make build && make run"
	@echo ""

# Build the Docker image
build:
	@echo "🔨 Building Docker image..."
	docker build -t simpleagentapp .
	@echo "✅ Build complete!"

# Run with OpenAI API key from .env file
run:
	@if [ ! -f .env ]; then \
		echo "❌ Error: .env file not found"; \
		echo "   Create it from template: cp .env.example .env"; \
		echo "   Then add your OPENAI_API_KEY"; \
		exit 1; \
	fi
	@echo "🚀 Starting SimpleAgentApp..."
	@echo "   Tool API:  http://localhost:8000/docs"
	@echo "   Agent API: http://localhost:8001/docs"
	@echo ""
	docker run -d \
		--name simpleagentapp \
		-p 8000:8000 \
		-p 8001:8001 \
		--env-file .env \
		simpleagentapp
	@echo "✅ Running! Use 'make logs' to view output"
	@echo "   Stop with: make stop"

# Run without OpenAI key (tool API only)
run-no-key:
	@echo "🚀 Starting Tool API only (no OpenAI key)..."
	@echo "   Tool API: http://localhost:8000/docs"
	@echo ""
	docker run -d \
		--name simpleagentapp \
		-p 8000:8000 \
		simpleagentapp
	@echo "✅ Running! Use 'make logs' to view output"

# Stop the container
stop:
	@echo "🛑 Stopping SimpleAgentApp..."
	-docker stop simpleagentapp
	-docker rm simpleagentapp
	@echo "✅ Stopped"

# Clean up Docker artifacts
clean: stop
	@echo "🧹 Cleaning up Docker image..."
	-docker rmi simpleagentapp
	@echo "✅ Cleaned"

# View logs
logs:
	docker logs -f simpleagentapp

# Run tests (requires services to be running)
test:
	@echo "🧪 Running tests..."
	python3 backend/tests/test_generic_call.py
	@if [ -n "$$OPENAI_API_KEY" ]; then \
		python3 backend/tests/test_agent_controller.py; \
	else \
		echo "⏭️  Skipping agent tests (no OPENAI_API_KEY)"; \
	fi
	@echo ""
	@echo "🔐 Running authentication tests..."
	python3 backend/tests/test_auth_api.py

# Run authentication tests only (requires agent_api to be running)
test-auth:
	@echo "🔐 Running authentication tests..."
	python3 backend/tests/test_auth_api.py

# Quick start: build and run in one command
quick: build run
	@echo ""
	@echo "🎉 Quick start complete!"
	@echo "   Access the APIs at the URLs above"
