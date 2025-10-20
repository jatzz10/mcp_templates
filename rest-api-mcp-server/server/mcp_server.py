"""
REST API MCP Server module

This module contains the main RestApiMCPServer class.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastmcp import FastMCP

from models.config import RestApiConfig
from .rest_operations import RestApiOperations

logger = logging.getLogger(__name__)


class RestApiMCPServer:
    """
    REST API MCP Server implementation.
    
    This server provides:
    - REST API operations and endpoint management
    - Health monitoring
    - MCP-compliant lifecycle management
    """
    
    def __init__(self, config: Optional[RestApiConfig] = None):
        self.config = config or RestApiConfig()
        self.mcp = FastMCP(name="rest-api-mcp-server")
        self.request_id = 0
        
        # Initialize components
        self.operations = RestApiOperations(self.config)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("rest_mcp_server")
        
        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()
    
    def create_mcp_response(self, content: Any, error: str = None, request_id: str = None) -> dict:
        """Create MCP-compliant response format"""
        self.request_id += 1
        response_id = request_id or str(self.request_id)
        
        if error:
            return {
                "jsonrpc": "2.0",
                "id": response_id,
                "error": {
                    "code": -32603,
                    "message": error,
                    "data": {"type": "InternalError"}
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": response_id,
                "result": {
                    "content": content
                }
            }
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.mcp.tool()
        async def health_check() -> str:
            """Check rest access health"""
            try:
                health = self.operations.health_check()
                
                response = self.create_mcp_response({
                    "status": health["status"],
                    "type": "rest",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.mcp.resource("server://info")
        async def get_server_info() -> str:
            """Get server information"""
            try:
                info = {
                    "name": "REST API MCP Server",
                    "version": "1.0.0",
                    "type": "rest",
                    "server_host": self.config.server_host,
                    "server_port": self.config.server_port,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                return json.dumps(info, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to get server info: {e}")
                return f"Error retrieving server info: {str(e)}"
    
    def start(self):
        """Start the MCP server"""
        try:
            self.logger.info("Starting REST API MCP Server...")
            
            self.mcp.run(
                transport="streamable-http",
                host=self.config.server_host,
                port=self.config.server_port
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    def print_server_info(self):
        """Print server information"""
        print("\n" + "="*60)
        print(f"🔧 REST API MCP Server")
        print("="*60)
        print(f"🌐 Server: {self.config.server_host}:{self.config.server_port}")
        print(f"📋 MCP Endpoint: http://{self.config.server_host}:{self.config.server_port}/mcp")
        print("\n🚀 Server is ready to accept connections!")
        print("="*60)
