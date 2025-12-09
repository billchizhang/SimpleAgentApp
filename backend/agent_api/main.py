"""
Agent API - FastAPI backend for LLM-driven agent interactions.

This API wraps the agent_controller module to provide HTTP endpoints for:
- Processing user queries with chat history
- Returning LLM responses with complete reasoning traces
- Health checks and status monitoring
"""

import os
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from agent_controller import AgentController
from .models import (
    QueryRequest,
    QueryResponse,
    ExecutionStep,
    HealthResponse,
    CreateUserRequest,
    LoginRequest,
    RemoveUserRequest,
    UserResponse,
    LoginResponse,
    RemoveUserResponse,
    UserData
)
from .database import DatabaseManager
from .auth import hash_password, verify_password

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Agent API",
    description="LLM-driven agent API with ReAct loop for tool calling and reasoning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
agent_controller: Optional[AgentController] = None
db_manager: Optional[DatabaseManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent controller and database on startup."""
    global agent_controller, db_manager

    print("🚀 Initializing Agent API...")
    print()

    # Initialize database
    try:
        db_path = Path(os.getenv("DB_PATH", "data/users.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        db_manager = DatabaseManager(db_path)
        print(f"✅ Database initialized successfully")
        print(f"   - Database path: {db_path}")

        # Initialize default users
        print("   - Creating default users...")
        db_manager.initialize_default_users()

        # Display default credentials
        print()
        print("🔐 Default User Accounts:")
        print("   Admin:")
        print("     - Username: admin")
        print("     - Password: AdminPass123!")
        print("     - Email: admin@simpleagent.local")
        print()
        print("   User:")
        print("     - Username: demo_user")
        print("     - Password: UserPass123!")
        print("     - Email: user@simpleagent.local")
        print()

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        db_manager = None

    # Get configuration from environment
    api_key = os.getenv("OPENAI_API_KEY")
    tool_registry_path = os.getenv("TOOL_REGISTRY_PATH")

    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not set. Agent controller will not be available.")
        print()
        return

    try:
        # Initialize agent controller
        if tool_registry_path:
            registry_path = Path(tool_registry_path)
        else:
            # Default to ../tool_registry relative to this file
            registry_path = Path(__file__).parent.parent / "tool_registry"

        agent_controller = AgentController(
            api_key=api_key,
            tool_registry_path=registry_path,
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            max_iterations=int(os.getenv("MAX_ITERATIONS", "5")),
            use_react=os.getenv("USE_REACT", "true").lower() == "true"
        )

        print(f"✅ Agent controller initialized successfully")
        print(f"   - Model: {agent_controller.model}")
        print(f"   - Tool registry: {agent_controller.tool_registry_path}")
        print(f"   - ReAct enabled: {agent_controller.use_react}")
        print()

    except Exception as e:
        print(f"❌ Failed to initialize agent controller: {e}")
        agent_controller = None


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agent API",
        "version": "1.0.0",
        "description": "LLM-driven agent API with ReAct loop and user authentication",
        "endpoints": {
            "health": "/health",
            "query": "/query (POST)",
            "query_stream": "/query/stream (POST) - Streaming responses",
            "tools": "/tools",
            "auth_create_user": "/auth/create_user (POST)",
            "auth_login": "/auth/login (POST)",
            "auth_remove_user": "/auth/remove_user (DELETE)",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the status of the API and its dependencies:
    - Agent controller availability
    - Tool registry accessibility
    - OpenAI API configuration
    """
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))

    # Check if agent controller is available
    controller_available = agent_controller is not None

    # Check if tool registry is accessible
    tool_registry_available = False
    if agent_controller:
        try:
            tool_registry_available = agent_controller.tool_registry_path.exists()
        except Exception:
            pass

    # Determine overall status
    if controller_available and tool_registry_available and openai_configured:
        overall_status = "healthy"
    elif controller_available:
        overall_status = "degraded"
    else:
        overall_status = "unavailable"

    return HealthResponse(
        status=overall_status,
        agent_controller_available=controller_available,
        tool_registry_available=tool_registry_available,
        openai_api_configured=openai_configured
    )


@app.post("/query", response_model=QueryResponse, tags=["Agent"])
async def process_query(request: QueryRequest):
    """
    Process a user query with optional chat history.

    This endpoint:
    1. Takes a user query and optional conversation history
    2. Uses the agent controller to process the query
    3. Returns the LLM's answer along with complete reasoning steps

    Args:
        request: QueryRequest containing query, chat_history, and configuration

    Returns:
        QueryResponse with answer, execution steps, and metadata

    Raises:
        HTTPException: If agent controller is not available or processing fails
    """
    # Check if agent controller is available
    if agent_controller is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent controller not available. Check OPENAI_API_KEY configuration."
        )

    try:
        # Update controller configuration if provided
        if request.use_react is not None:
            agent_controller.use_react = request.use_react
        if request.model is not None:
            agent_controller.model = request.model
        if request.max_iterations is not None:
            agent_controller.max_iterations = request.max_iterations

        # Build query with chat history context
        query_with_context = request.query

        if request.chat_history:
            # Prepend chat history as context
            history_context = "\n\nPrevious conversation:\n"
            for msg in request.chat_history:
                history_context += f"{msg.role}: {msg.content}\n"
            history_context += f"\nCurrent query: {request.query}"
            query_with_context = history_context

        # Process the query
        result = agent_controller.process_query(query_with_context)

        # Convert steps to ExecutionStep models
        steps = [
            ExecutionStep(**step) for step in result["steps"]
        ]

        # Build metadata
        metadata = {
            "model": agent_controller.model,
            "total_steps": len(steps),
            "tools_called": len([s for s in steps if s.step_type == "action"]),
            "react_enabled": agent_controller.use_react
        }

        return QueryResponse(
            success=result["success"],
            answer=result["answer"],
            steps=steps,
            error=result.get("error"),
            metadata=metadata
        )

    except Exception as e:
        # Log the error
        print(f"Error processing query: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@app.post("/query/stream", tags=["Agent"])
async def process_query_stream(request: QueryRequest):
    """
    Process a user query with streaming responses.

    This endpoint streams the response as it's generated, allowing for
    real-time display in the frontend. Responses are sent as newline-delimited JSON.

    Each chunk is a JSON object with:
    - {"type": "step", "data": {...}} - Reasoning/action steps
    - {"type": "content", "data": "text"} - Incremental text content
    - {"type": "metadata", "data": {...}} - Final metadata
    - {"type": "error", "data": "error_msg"} - Error information

    Args:
        request: QueryRequest containing query, chat_history, and configuration

    Returns:
        StreamingResponse with newline-delimited JSON chunks

    Raises:
        HTTPException: If agent controller is not available
    """
    # Check if agent controller is available
    if agent_controller is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent controller not available. Check OPENAI_API_KEY configuration."
        )

    async def generate():
        """Generate streaming response chunks."""
        try:
            # Update controller configuration if provided
            if request.use_react is not None:
                agent_controller.use_react = request.use_react
            if request.model is not None:
                agent_controller.model = request.model
            if request.max_iterations is not None:
                agent_controller.max_iterations = request.max_iterations

            # Process the query with streaming
            for chunk in agent_controller.process_query_stream(
                request.query,
                request.chat_history
            ):
                # Send each chunk as newline-delimited JSON
                yield json.dumps(chunk) + "\n"

        except Exception as e:
            # Send error as final chunk
            error_chunk = {
                "type": "error",
                "data": str(e)
            }
            yield json.dumps(error_chunk) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",  # newline-delimited JSON
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@app.get("/tools", tags=["Agent"])
async def list_tools():
    """
    List all available tools from the tool registry.

    Returns:
        Dictionary with tool names and descriptions
    """
    if agent_controller is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent controller not available."
        )

    try:
        # Ensure tools are loaded
        if not agent_controller._tools_loaded:
            agent_controller._load_tools()

        # Return tool information
        tools_info = {}
        for tool_name, tool_def in agent_controller.tools.items():
            tools_info[tool_name] = {
                "name": tool_def.get("name"),
                "description": tool_def.get("description"),
                "method": tool_def.get("method"),
                "params": tool_def.get("params", {})
            }

        return {
            "total_tools": len(tools_info),
            "tools": tools_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tools: {str(e)}"
        )


# Authentication Endpoints

@app.post("/auth/create_user", response_model=UserResponse, tags=["Authentication"])
async def create_user(request: CreateUserRequest):
    """
    Create a new user account.

    Args:
        request: CreateUserRequest with username, password, email, and role

    Returns:
        UserResponse with created user data

    Raises:
        HTTPException: If database not initialized, user exists, or creation fails
    """
    # Check if database is available
    if db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized"
        )

    try:
        # Check if username already exists
        if db_manager.user_exists(request.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{request.username}' already exists"
            )

        # Check if email already exists
        if db_manager.get_user_by_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{request.email}' already exists"
            )

        # Hash the password
        password_hash = hash_password(request.password)

        # Create the user
        user_data = db_manager.create_user(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            role=request.role
        )

        # Return success response
        return UserResponse(
            success=True,
            uid=user_data["uid"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"],
            created_at=user_data["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@app.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Authenticate a user with username and password.

    Args:
        request: LoginRequest with username and password

    Returns:
        LoginResponse with success status and user data

    Raises:
        HTTPException: If database not initialized or authentication fails
    """
    # Check if database is available
    if db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized"
        )

    try:
        # Get user from database
        user_data = db_manager.get_user_by_username(request.username)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Verify password
        if not verify_password(request.password, user_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Remove password_hash from user_data before returning
        user_data_clean = {
            "uid": user_data["uid"],
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data["role"],
            "created_at": user_data["created_at"],
            "updated_at": user_data["updated_at"]
        }

        return LoginResponse(
            success=True,
            message="Login successful",
            user=UserData(**user_data_clean)
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@app.delete("/auth/remove_user", response_model=RemoveUserResponse, tags=["Authentication"])
async def remove_user(request: RemoveUserRequest):
    """
    Remove a user account by username.

    Args:
        request: RemoveUserRequest with username

    Returns:
        RemoveUserResponse with success status

    Raises:
        HTTPException: If database not initialized, user not found, or removal fails
    """
    # Check if database is available
    if db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized"
        )

    try:
        # Check if user exists
        if not db_manager.user_exists(request.username):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{request.username}' not found"
            )

        # Remove the user
        success = db_manager.remove_user(request.username)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove user"
            )

        return RemoveUserResponse(
            success=True,
            message=f"User '{request.username}' removed successfully",
            username=request.username
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove user: {str(e)}"
        )


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent_api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
