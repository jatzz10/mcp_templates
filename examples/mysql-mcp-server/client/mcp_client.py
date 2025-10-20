"""
MCP Client module

This module contains the MCPClient class for handling MCP operations.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from models.config import MCPClientConfig
from .llm_integration import LLMIntegration

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client class to handle all MCP operations and LLM interactions"""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.mcp_client_instance: Optional[Client] = None
        self.mcp_tools_cache: Optional[Dict[str, Any]] = None
        self.mcp_schema_cache: Optional[str] = None
        self.llm_integration = LLMIntegration(config)
        
    async def startup(self):
        """Initialize MCP client and LLM instance"""
        try:
            logger.info("Starting MCP Client initialization...")
            
            # Initialize LLM
            await self.llm_integration.initialize()
            
            # Don't initialize MCP client during startup - do it lazily when needed
            logger.info("MCP Client startup completed successfully (MCP connection will be established on first use)")
            
        except Exception as e:
            logger.error(f"Failed to start MCP Client: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup MCP client connections"""
        try:
            if self.mcp_client_instance is not None:
                await self.mcp_client_instance.__aexit__(None, None, None)
                self.mcp_client_instance = None
                logger.info("Closed persistent MCP client connection")
        except Exception as e:
            logger.error(f"Error during MCP Client shutdown: {e}")
    
    async def _initialize_mcp_client(self):
        """Initialize MCP client connection"""
        try:
            server_url = self.config.normalize_server_url(self.config.mcp_server_url)
            transport = StreamableHttpTransport(url=server_url)
            self.mcp_client_instance = Client(transport)
            await self.mcp_client_instance.__aenter__()
            logger.info(f"Created persistent MCP client connection to {server_url}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            logger.warning("MCP server may not be running. Some features will be unavailable.")
            raise
    
    async def get_mcp_client(self) -> Client:
        """Get MCP client instance"""
        if self.mcp_client_instance is None:
            await self._initialize_mcp_client()
        return self.mcp_client_instance
    
    async def call_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call MCP tool on the server using persistent FastMCP client"""
        try:
            client = await self.get_mcp_client()
            result = await client.call_tool(tool_name, kwargs)
            
            logger.debug(f"MCP tool {tool_name} raw result: {result}")
            logger.debug(f"Result type: {type(result)}")
            
            # Extract common result shapes
            if hasattr(result, 'content') and result.content:
                text = result.content[0].text
                logger.debug(f"MCP tool {tool_name} content text: {text}")
                try:
                    # Handle MCP-compliant response format
                    parsed = json.loads(text)
                    logger.debug(f"MCP tool {tool_name} parsed: {parsed}")
                    logger.debug(f"Parsed type: {type(parsed)}")
                    
                    if isinstance(parsed, dict) and 'result' in parsed:
                        return parsed['result'].get('content', parsed['result'])
                    elif isinstance(parsed, dict) and 'error' in parsed:
                        raise Exception(f"MCP Error: {parsed['error'].get('message', 'Unknown error')}")
                    else:
                        return parsed
                except json.JSONDecodeError:
                    logger.debug(f"MCP tool {tool_name} JSON decode failed, returning as text")
                    return {"content": text}
            else:
                logger.debug(f"MCP tool {tool_name} no content, returning string result")
                return {"content": str(result)}
                
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            raise
    
    async def get_mcp_resource(self, uri: str) -> str:
        """Get MCP resource from the server"""
        try:
            client = await self.get_mcp_client()
            result = await client.read_resource(uri)
            
            if hasattr(result, 'contents') and result.contents:
                return result.contents[0].text
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error getting MCP resource {uri}: {e}")
            raise
    
    async def discover_mcp_tools(self) -> Dict[str, Any]:
        """Discover available MCP tools from the server"""
        try:
            client = await self.get_mcp_client()
            result = await client.list_tools()
            
            if hasattr(result, 'tools'):
                tools = {}
                for tool in result.tools:
                    tools[tool.name] = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                return tools
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error discovering MCP tools: {e}")
            return {}
    
    async def ask_llm(self, question: str, max_results: int = 100) -> Dict[str, Any]:
        """Process natural language question using LLM and MCP tools"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Debug logging
            logger.info(f"LLM instance status: {self.llm_integration.is_initialized}")
            logger.info(f"HAS_NAIL_LLM: {self.llm_integration.has_nail_llm}")
            logger.info(f"LLM instance type: {type(self.llm_integration.llm_instance)}")
            
            if not self.llm_integration.is_initialized:
                raise HTTPException(status_code=500, detail="LLM is not configured")
            
            # Get database schema
            if self.mcp_schema_cache is None:
                self.mcp_schema_cache = await self.get_mcp_resource("database://schema")
            
            # Create prompt for LLM
            prompt = f"""
            Database Schema:
            {self.mcp_schema_cache}
            
            Question: {question}
            
            Please generate a SQL query to answer this question. Return only the SQL query, no explanations.
            """
            
            # Get SQL query from LLM
            sql_query = self.llm_integration.invoke(prompt).strip()
            
            # Clean up SQL query (remove markdown formatting if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()
            
            # Execute SQL query using MCP tool
            result = await self.call_mcp_tool("query_database", query=sql_query, limit=max_results)
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Handle different result formats
            if isinstance(result, dict):
                data = result.get("data", [])
                row_count = result.get("row_count", len(data) if isinstance(data, list) else 0)
            elif isinstance(result, list):
                data = result
                row_count = len(result)
            else:
                data = [{"result": str(result)}]
                row_count = 1
            
            return {
                "success": True,
                "question": question,
                "sql_query": sql_query,
                "data": data,
                "row_count": row_count,
                "execution_time": execution_time,
                "error": None
            }
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Error processing question '{question}': {e}")
            
            return {
                "success": False,
                "question": question,
                "sql_query": None,
                "data": None,
                "row_count": None,
                "execution_time": execution_time,
                "error": str(e)
            }
