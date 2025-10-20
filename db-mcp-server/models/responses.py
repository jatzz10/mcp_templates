"""
Response models for MCP Client and Server

This module contains all Pydantic response models used in the API endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AskLLMResponse(BaseModel):
    """Natural language database query response"""
    success: bool
    question: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    error: Optional[str] = None
