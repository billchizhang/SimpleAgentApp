"""
Agent API Module

FastAPI backend for LLM-driven agent interactions.
Provides HTTP endpoints for processing user queries with chat history
and returning complete reasoning traces.
"""

from .main import app
from .models import (
    QueryRequest,
    QueryResponse,
    ChatMessage,
    ExecutionStep,
    HealthResponse,
    CreateUserRequest,
    LoginRequest,
    RemoveUserRequest,
    UserData,
    UserResponse,
    LoginResponse,
    RemoveUserResponse
)
from .auth import hash_password, verify_password, generate_uid
from .database import DatabaseManager

__all__ = [
    "app",
    "QueryRequest",
    "QueryResponse",
    "ChatMessage",
    "ExecutionStep",
    "HealthResponse",
    "CreateUserRequest",
    "LoginRequest",
    "RemoveUserRequest",
    "UserData",
    "UserResponse",
    "LoginResponse",
    "RemoveUserResponse",
    "hash_password",
    "verify_password",
    "generate_uid",
    "DatabaseManager",
]

__version__ = "1.0.0"
