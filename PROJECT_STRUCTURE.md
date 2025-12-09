# Project Structure

## Overview

SimpleAgentApp has been reorganized with all backend code in the `backend/` directory, while Docker-related files remain in the root for easy deployment.

## Directory Layout

```
SimpleAgentApp/
├── backend/                    # All backend code
│   ├── agent_api/             # FastAPI REST API for LLM queries
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application with auth endpoints
│   │   ├── models.py          # Pydantic models
│   │   ├── auth.py            # Password hashing utilities
│   │   └── database.py        # SQLite database manager
│   ├── agent_controller/      # LLM orchestration with ReAct loop
│   │   ├── __init__.py
│   │   ├── controller.py      # Main AgentController class
│   │   ├── tool_loader.py     # Tool registry loader
│   │   ├── response_formatter.py
│   │   └── README.md
│   ├── tool_api/              # Tool endpoints API
│   │   ├── __init__.py
│   │   └── main.py
│   ├── function_call/         # Generic API call module
│   │   ├── __init__.py
│   │   └── generic_call.py
│   ├── tool_registry/         # JSON tool definitions
│   │   ├── weather.json
│   │   ├── uppercase.json
│   │   └── ...
│   ├── tests/                 # All test files
│   │   ├── test_generic_call.py
│   │   ├── test_agent_controller.py
│   │   ├── test_agent_api.py
│   │   ├── test_auth_api.py
│   │   └── data/              # Test data
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment template
│
├── Dockerfile                 # Docker build configuration
├── docker-compose.yml         # Multi-service orchestration
├── start.sh                   # Startup script for both services
├── Makefile                   # Convenient build/run commands
├── .gitignore                 # Git ignore patterns
├── CLAUDE.md                  # Project documentation for Claude Code
├── README.md                  # Project README
└── data/                      # Runtime data (databases, logs)
    └── users.db               # SQLite database (gitignored)
```

## Key Changes

1. **Backend Directory**: All Python code now resides in `backend/`
   - `agent_api/`, `agent_controller/`, `tool_api/`
   - `function_call/`, `tool_registry/`, `tests/`
   - `requirements.txt`, `.env.example`

2. **Root Directory**: Docker and deployment files remain in root
   - `Dockerfile`, `docker-compose.yml`, `start.sh`
   - `Makefile` for convenient commands
   - Documentation: `README.md`, `CLAUDE.md`

3. **Updated Configurations**:
   - `Dockerfile`: Copies `backend/` to `/app/backend` and installs from `backend/requirements.txt`
   - `start.sh`: Changes to `backend/` directory before starting services
   - `docker-compose.yml`: Sets `working_dir: /app/backend` for both services
   - `Makefile`: Test commands reference `backend/tests/`

## Running the Application

### Using Make (Recommended)
```bash
make build && make run
```

### Using Docker Compose
```bash
cp backend/.env.example .env
# Edit .env and add OPENAI_API_KEY
docker-compose up
```

### Manual Development
```bash
cd backend
python -m uvicorn tool_api.main:app --port 8000
python -m uvicorn agent_api.main:app --port 8001
```

## Running Tests

From project root:
```bash
make test                              # Run all tests
make test-auth                         # Authentication tests only
python backend/tests/test_auth_api.py  # Specific test
```

## Benefits of This Structure

1. **Clear Separation**: Backend code vs deployment configuration
2. **Easier Deployment**: Docker files in root for straightforward builds
3. **Better Organization**: All Python code in one directory
4. **Simpler Imports**: All backend modules can import each other directly
5. **Cleaner Root**: Less clutter in root directory
