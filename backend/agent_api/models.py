"""
Pydantic models for the Agent API.

Defines request and response schemas for the FastAPI endpoints.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime


class ChatMessage(BaseModel):
    """Represents a single message in the chat history."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What's the weather in Boston?"
            }
        }


class QueryRequest(BaseModel):
    """Request model for the query endpoint."""
    query: str = Field(..., description="User's natural language query", min_length=1)
    chat_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous conversation history for context"
    )
    use_react: Optional[bool] = Field(
        default=True,
        description="Enable ReAct-style reasoning (thought, action, observation)"
    )
    model: Optional[str] = Field(
        default="gpt-4o",
        description="OpenAI model to use"
    )
    max_iterations: Optional[int] = Field(
        default=5,
        description="Maximum number of tool call iterations"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's the weather in Boston today?",
                "chat_history": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hi! How can I help you today?"}
                ],
                "use_react": True,
                "model": "gpt-4o",
                "max_iterations": 5
            }
        }


class ExecutionStep(BaseModel):
    """Represents a single execution step from the agent."""
    step_number: int = Field(..., description="Sequential step number")
    step_type: str = Field(..., description="Type of step (thought, action, observation, etc.)")
    description: str = Field(..., description="Human-readable description")
    timestamp: str = Field(..., description="ISO timestamp of the step")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Step-specific details")
    error: Optional[str] = Field(default=None, description="Error message if step failed")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "step_type": "thought",
                "description": "Agent reasoning",
                "timestamp": "2025-12-09T15:30:00",
                "details": {
                    "reasoning": "The user wants to know the weather. I need to call the weather tool."
                },
                "error": None
            }
        }


class QueryResponse(BaseModel):
    """Response model for the query endpoint."""
    success: bool = Field(..., description="Whether the query was processed successfully")
    answer: str = Field(..., description="Final answer from the agent")
    steps: List[ExecutionStep] = Field(..., description="Complete execution trace")
    error: Optional[str] = Field(default=None, description="Error message if processing failed")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (model used, token count, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "The temperature in Boston today is 15.2°C.",
                "steps": [
                    {
                        "step_number": 1,
                        "step_type": "load_registry",
                        "description": "Loaded 3 tools from registry",
                        "timestamp": "2025-12-09T15:30:00",
                        "details": {"tools_loaded": ["weather", "uppercase", "count_word"]},
                        "error": None
                    }
                ],
                "error": None,
                "metadata": {
                    "model": "gpt-4o",
                    "total_steps": 5,
                    "tools_called": 1
                }
            }
        }


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""
    status: str = Field(..., description="Service status")
    agent_controller_available: bool = Field(..., description="Whether agent controller is initialized")
    tool_registry_available: bool = Field(..., description="Whether tool registry is accessible")
    openai_api_configured: bool = Field(..., description="Whether OpenAI API key is configured")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "agent_controller_available": True,
                "tool_registry_available": True,
                "openai_api_configured": True
            }
        }


# Authentication Models

class CreateUserRequest(BaseModel):
    """Request model for creating a new user."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters, alphanumeric and underscores only)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=12,
        description="Password (8-12 characters)"
    )
    email: EmailStr = Field(..., description="Valid email address")
    role: Literal["user", "admin"] = Field(
        default="user",
        description="User role (user or admin)"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters and underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "SecurePass123!",
                "email": "john@example.com",
                "role": "user"
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "SecurePass123!"
            }
        }


class RemoveUserRequest(BaseModel):
    """Request model for removing a user."""
    username: str = Field(..., description="Username of user to remove")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe"
            }
        }


class UserData(BaseModel):
    """User data model (without password hash)."""
    uid: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role (user or admin)")
    created_at: Optional[str] = Field(default=None, description="Account creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "abc123xyz789",
                "username": "johndoe",
                "email": "john@example.com",
                "role": "user",
                "created_at": "2025-12-09T15:30:00",
                "updated_at": "2025-12-09T15:30:00"
            }
        }


class UserResponse(BaseModel):
    """Response model for user creation."""
    success: bool = Field(..., description="Whether the operation was successful")
    uid: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role")
    created_at: str = Field(..., description="Account creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "uid": "abc123xyz789",
                "username": "johndoe",
                "email": "john@example.com",
                "role": "user",
                "created_at": "2025-12-09T15:30:00"
            }
        }


class LoginResponse(BaseModel):
    """Response model for user login."""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Status message")
    user: Optional[UserData] = Field(default=None, description="User data (if login successful)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "user": {
                    "uid": "abc123xyz789",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "role": "user",
                    "created_at": "2025-12-09T15:30:00",
                    "updated_at": "2025-12-09T15:30:00"
                }
            }
        }


class RemoveUserResponse(BaseModel):
    """Response model for user removal."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    username: str = Field(..., description="Username that was removed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "User 'johndoe' removed successfully",
                "username": "johndoe"
            }
        }
