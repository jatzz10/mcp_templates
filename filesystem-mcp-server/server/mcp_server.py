"""
Database MCP Server module

This module contains the main DatabaseMCPServer class.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastmcp import FastMCP

from models.config import DatabaseConfig
from .database_operations import DatabaseOperations
from .schema_manager import SchemaManager

logger = logging.getLogger(__name__)


class DatabaseMCPServer:
    """
    Generic Database MCP Server implementation.
    
    This server provides:
    - Database schema as MCP resource (database://schema)
    - Query execution tool (query_database)
    - Schema refresh tool (refresh_schema)
    - Health monitoring
    - Support for multiple database types
    - MCP-compliant lifecycle management
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.mcp = FastMCP(name="mysql-mcp-server")
        self.request_id = 0  # For MCP request correlation
        
        # Initialize components
        self.db_ops = DatabaseOperations(self.config)
        self.schema_manager = SchemaManager(self.config, self.db_ops)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("db_mcp_server")
        
        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()
        self._register_lifecycle_handlers()
    
    def create_mcp_response(self, content: Any, error: str = None, request_id: str = None) -> dict:
        """Create MCP-compliant response format"""
        self.request_id += 1
        response_id = request_id or str(self.request_id)
        
        if error:
            return {
                "jsonrpc": "2.0",
                "id": response_id,
                "error": {
                    "code": -32603,  # Internal error
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
        async def query_database(query: str, limit: int = 1000) -> str:
            """Execute a SQL query on the database"""
            try:
                self.logger.info(f"Executing query: {query[:100]}...")
                
                # Connect if not already connected
                if not self.db_ops.engine:
                    self.db_ops.connect()
                
                # Execute query
                result = self.db_ops.execute_query(query, limit)
                
                # Create MCP response
                response = self.create_mcp_response({
                    "data": result["data"],
                    "row_count": result["row_count"],
                    "columns": result["columns"],
                    "query": result["query"]
                })
                
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Query execution failed: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
        
        @self.mcp.tool()
        async def refresh_schema() -> str:
            """Refresh the database schema cache"""
            try:
                self.logger.info("Refreshing database schema")
                
                # Connect if not already connected
                if not self.db_ops.engine:
                    self.db_ops.connect()
                
                # Refresh schema
                schema = self.schema_manager.refresh_schema()
                
                response = self.create_mcp_response({
                    "message": "Schema refreshed successfully",
                    "schema_length": len(schema),
                    "cached_at": datetime.now(timezone.utc).isoformat()
                })
                
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Schema refresh failed: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
        
        @self.mcp.tool()
        async def health_check() -> str:
            """Check database connection health"""
            try:
                # Connect if not already connected
                if not self.db_ops.engine:
                    self.db_ops.connect()
                
                # Perform health check
                health = self.db_ops.health_check()
                
                response = self.create_mcp_response({
                    "status": health["status"],
                    "database": self.config.db_name,
                    "database_type": self.config.db_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": health.get("error")
                })
                
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
    
    def _register_resources(self):
        """Register MCP resources"""
        
        @self.mcp.resource("database://schema")
        async def get_database_schema() -> str:
            """Get the database schema"""
            try:
                schema = self.schema_manager.get_schema()
                return schema
            except Exception as e:
                self.logger.error(f"Failed to get schema: {e}")
                return f"Error retrieving database schema: {str(e)}"
        
        @self.mcp.resource("server://info")
        async def get_server_info() -> str:
            """Get server information"""
            try:
                info = {
                    "name": "Database MCP Server",
                    "version": "1.0.0",
                    "database_type": self.config.db_type,
                    "database_name": self.config.db_name,
                    "server_host": self.config.server_host,
                    "server_port": self.config.server_port,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                return json.dumps(info, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to get server info: {e}")
                return f"Error retrieving server info: {str(e)}"
        
        @self.mcp.resource("prompts://database")
        async def get_database_prompts() -> str:
            """Get database-related prompts"""
            try:
                prompts = {
                    "generate_sql_query": {
                        "description": "Generate SQL query from natural language",
                        "template": "Given the database schema and question, generate a SQL query.\n\nSchema:\n{schema}\n\nQuestion: {question}\n\nSQL Query:"
                    },
                    "explain_query": {
                        "description": "Explain what a SQL query does",
                        "template": "Explain what the following SQL query does:\n\n{query}\n\nExplanation:"
                    }
                }
                return json.dumps(prompts, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to get prompts: {e}")
                return f"Error retrieving prompts: {str(e)}"
    
    def _register_lifecycle_handlers(self):
        """Register MCP lifecycle handlers"""
        
        @self.mcp.tool()
        async def list_tools() -> str:
            """List available MCP tools"""
            try:
                tools = {
                    "query_database": {
                        "name": "query_database",
                        "description": "Execute SQL queries on the database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "SQL query to execute"},
                                "limit": {"type": "integer", "description": "Maximum number of rows to return", "default": 1000}
                            },
                            "required": ["query"]
                        }
                    },
                    "refresh_schema": {
                        "name": "refresh_schema",
                        "description": "Refresh the database schema cache",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    "health_check": {
                        "name": "health_check",
                        "description": "Check database connection health",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
                
                response = self.create_mcp_response(tools)
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Failed to list tools: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
        
        @self.mcp.tool()
        async def list_resources() -> str:
            """List available MCP resources"""
            try:
                resources = {
                    "database://schema": {
                        "uri": "database://schema",
                        "name": "Database Schema",
                        "description": "Current database schema information",
                        "mimeType": "text/plain"
                    },
                    "server://info": {
                        "uri": "server://info",
                        "name": "Server Information",
                        "description": "MCP server information and status",
                        "mimeType": "application/json"
                    },
                    "prompts://database": {
                        "uri": "prompts://database",
                        "name": "Database Prompts",
                        "description": "Available database-related prompts",
                        "mimeType": "application/json"
                    }
                }
                
                response = self.create_mcp_response(resources)
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Failed to list resources: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
        
        @self.mcp.tool()
        async def list_prompts() -> str:
            """List available MCP prompts"""
            try:
                prompts = {
                    "generate_sql_query": {
                        "name": "generate_sql_query",
                        "description": "Generate SQL query from natural language question",
                        "arguments": [
                            {"name": "question", "description": "Natural language question about the database", "required": True},
                            {"name": "table_context", "description": "Additional table context", "required": False}
                        ]
                    },
                    "explain_query": {
                        "name": "explain_query",
                        "description": "Explain what a SQL query does",
                        "arguments": [
                            {"name": "query", "description": "SQL query to explain", "required": True}
                        ]
                    }
                }
                
                response = self.create_mcp_response(prompts)
                return json.dumps(response)
                
            except Exception as e:
                self.logger.error(f"Failed to list prompts: {e}")
                error_response = self.create_mcp_response(None, str(e))
                return json.dumps(error_response)
    
    def start(self):
        """Start the MCP server"""
        try:
            self.logger.info("Starting Database MCP Server...")
            
            # Connect to database
            self.db_ops.connect()
            
            # Start MCP server with streamable-http transport
            self.mcp.run(
                transport="streamable-http",
                host=self.config.server_host,
                port=self.config.server_port
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server"""
        try:
            self.logger.info("Stopping Database MCP Server...")
            
            # Disconnect from database
            self.db_ops.disconnect()
            
            self.logger.info("Server stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
    
    def print_server_info(self):
        """Print server information"""
        print("\n" + "="*60)
        print("🗄️  Database MCP Server")
        print("="*60)
        print(f"📊 Database: {self.config.db_type.upper()} - {self.config.db_name}")
        print(f"🌐 Server: {self.config.server_host}:{self.config.server_port}")
        print(f"📋 MCP Endpoint: http://{self.config.server_host}:{self.config.server_port}/mcp")
        print("\n🔧 Available Tools:")
        print("  • query_database - Execute SQL queries")
        print("  • refresh_schema - Refresh database schema cache")
        print("  • health_check - Check database connection health")
        print("\n📚 Available Resources:")
        print("  • database://schema - Database schema information")
        print("  • server://info - Server information")
        print("  • prompts://database - Database-related prompts")
        print("\n🚀 Server is ready to accept connections!")
        print("="*60)
