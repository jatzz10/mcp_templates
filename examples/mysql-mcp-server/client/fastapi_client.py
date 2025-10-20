"""
FastAPI Client module

This module contains the FastAPIClient class for handling HTTP endpoints and app lifecycle.
"""

import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.config import MCPClientConfig
from models.requests import AskLLMRequest
from models.responses import AskLLMResponse, HealthResponse
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class FastAPIClient:
    """FastAPI Client class to handle HTTP endpoints and app lifecycle"""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.mcp_client = MCPClient(config)
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title="Simplified Database MCP Client",
            description="Minimal FastAPI client for natural language database queries",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add lifespan context manager
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self.mcp_client.startup()
            yield
            # Shutdown
            await self.mcp_client.shutdown()
        
        app.router.lifespan_context = lifespan
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI):
        """Add all API routes to the FastAPI app"""
        
        @app.get("/")
        async def root():
            """Root endpoint with API information"""
            return {
                "message": "Simplified Database MCP Client",
                "version": "1.0.0",
                "endpoints": {
                    "ask_llm": "POST /ask_llm - Natural language database queries",
                    "health": "GET /health - Client health check",
                    "mcp_health": "GET /mcp/health - MCP server connection check",
                    "mcp_capabilities": "GET /mcp/capabilities - MCP server capabilities"
                }
            }
        
        @app.post("/ask_llm", response_model=AskLLMResponse)
        async def ask_llm(request: AskLLMRequest):
            """Process natural language database query using LLM and MCP tools"""
            return await self.mcp_client.ask_llm(request.question, request.max_results)
        
        @app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Client health check endpoint"""
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now(timezone.utc).isoformat(),
                error=None
            )
        
        @app.get("/mcp/health", response_model=HealthResponse)
        async def mcp_health_check():
            """MCP server connection health check"""
            try:
                # Try to get MCP server info
                result = await self.mcp_client.call_mcp_tool("health_check")
                return HealthResponse(
                    status="healthy",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error=None
                )
            except Exception as e:
                logger.warning(f"MCP server health check failed: {e}")
                return HealthResponse(
                    status="unhealthy",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    error=f"MCP server not available: {str(e)}"
                )
        
        @app.get("/mcp/capabilities")
        async def mcp_capabilities():
            """Get MCP server capabilities (tools, resources, prompts)"""
            try:
                # Get tools
                tools = await self.mcp_client.discover_mcp_tools()
                
                # Get resources
                try:
                    schema = await self.mcp_client.get_mcp_resource("database://schema")
                    resources = {"database://schema": "Available"}
                except:
                    resources = {"database://schema": "Not available"}
                
                # Get prompts (if available)
                try:
                    prompts = await self.mcp_client.get_mcp_resource("prompts://database")
                    prompts_info = {"prompts://database": "Available"}
                except:
                    prompts_info = {"prompts://database": "Not available"}
                
                return {
                    "tools": tools,
                    "resources": resources,
                    "prompts": prompts_info,
                    "tool_count": len(tools),
                    "resource_count": len(resources),
                    "prompt_count": len(prompts_info)
                }
                
            except Exception as e:
                logger.error(f"Error getting MCP capabilities: {e}")
                return {
                    "error": str(e),
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                    "tool_count": 0,
                    "resource_count": 0,
                    "prompt_count": 0
                }
