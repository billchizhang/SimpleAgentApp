import requests
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

# --- 1. Define the Schema (The Contract) ---
# We use Pydantic to ensure the LLM's JSON contains exactly what we need.
class ApiToolCall(BaseModel):
    url: str = Field(..., description="The full API endpoint URL.")
    method: str = Field(..., description="HTTP Method (GET, POST, PUT, DELETE)")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters for GET requests")
    json_body: Optional[Dict[str, Any]] = Field(default=None, description="JSON payload for non-GET requests")

    @validator("method")
    def normalize_method(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"GET", "POST", "PUT", "DELETE"}
        if normalized not in allowed:
            raise ValueError(f"HTTP method must be one of {', '.join(allowed)}")
        return normalized

# --- 2. Generic Function to Call APIs Based on the Schema ---
def call_api(tool_data: ApiToolCall) -> Dict[str, Any]:
    try:
        print(f"Executing {tool_data.method} request to: {tool_data.url}")

        request_kwargs: Dict[str, Any] = {
            "method": tool_data.method,
            "url": tool_data.url,
            "timeout": 10, # Always add a timeout!
        }

        if tool_data.params:
            request_kwargs["params"] = tool_data.params

        if tool_data.json_body:
            request_kwargs["json"] = tool_data.json_body

        response = requests.request(**request_kwargs)
        
        # Raise error for 4xx or 5xx status codes
        response.raise_for_status()
        
        # Return the JSON response from the external API
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": f"API Request Failed: {str(e)}"}
