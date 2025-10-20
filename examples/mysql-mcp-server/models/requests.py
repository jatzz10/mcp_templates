"""
Request models for MCP Client and Server

This module contains all Pydantic request models used in the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AskLLMRequest(BaseModel):
    """Natural language database query request"""
    question: str = Field(
        ..., 
        description="Natural language question about the database", 
        json_schema_extra={"example": "Show me the top 5 users by registration date"}
    )
    max_results: Optional[int] = Field(
        100, 
        description="Maximum number of results to return", 
        ge=1, 
        le=1000
    )
