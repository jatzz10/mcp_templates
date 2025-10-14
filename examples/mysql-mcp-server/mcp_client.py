#!/usr/bin/env python3
"""
Simplified Database MCP Client

A minimal FastAPI client with only 3 essential endpoints:
1. Natural language database queries using NailLLMLangchain
2. Client health check
3. MCP server connection check

Usage:
    uvicorn mcp_client:app --host 0.0.0.0 --port 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# Load environment variables from mcp.env file
try:
    from dotenv import load_dotenv
    # Load .env file from the same directory as this script
    env_path = Path(__file__).parent / 'mcp.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from: {env_path}")
    else:
        print(f"⚠️  Environment file not found: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Error loading environment file: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
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

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
CLIENT_HOST = os.getenv("CLIENT_HOST", "0.0.0.0")
CLIENT_PORT = int(os.getenv("CLIENT_PORT", "8001"))

# Debug: Print loaded environment variables
print(f"🔧 Configuration loaded:")
print(f"   MCP_SERVER_URL: {MCP_SERVER_URL}")
print(f"   CLIENT_HOST: {CLIENT_HOST}")
print(f"   CLIENT_PORT: {CLIENT_PORT}")
print(f"   GOOGLE_API_KEY: {'***' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
print(f"   GEMINI_MODEL_ID: {os.getenv('GEMINI_MODEL_ID', 'NOT SET')}")

# Global variables for cached MCP metadata
mcp_tools_cache: Optional[Dict[str, Any]] = None
mcp_schema_cache: Optional[str] = None

def _normalize_server_url(url: str) -> str:
    url = url.strip().rstrip("/")
    return url if url.endswith("/mcp") else url + "/mcp"


# Pydantic Models
class AskLLMRequest(BaseModel):
    """Natural language database query request"""
    question: str = Field(..., description="Natural language question about the database", example="Show me the top 5 users by registration date")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return", ge=1, le=1000)

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


# MCP Client Functions
async def call_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Call MCP tool on the server using FastMCP client"""
    server_url = _normalize_server_url(MCP_SERVER_URL)
    transport = StreamableHttpTransport(url=server_url)
    client = Client(transport)
    await client.__aenter__()
    try:
        result = await client.call_tool(tool_name, kwargs)
        # Extract common result shapes
        if hasattr(result, 'content') and result.content:
            text = result.content[0].text
            try:
                return json.loads(text)
            except Exception:
                return text  # plain text
        return {}
    finally:
        await client.__aexit__(None, None, None)

async def get_mcp_resource(resource_uri: str) -> Dict[str, Any]:
    """Get MCP resource from the server using FastMCP client"""
    server_url = _normalize_server_url(MCP_SERVER_URL)
    transport = StreamableHttpTransport(url=server_url)
    client = Client(transport)
    await client.__aenter__()
    try:
        resource = await client.read_resource(resource_uri)
        # FastMCP returns contents list
        if hasattr(resource, 'contents') and resource.contents:
            text = resource.contents[0].text
            try:
                return json.loads(text)
            except Exception:
                return text
        return {}
    finally:
        await client.__aexit__(None, None, None)

async def discover_mcp_tools() -> Dict[str, Any]:
    """Discover available MCP tools and resources from the server"""
    server_url = _normalize_server_url(MCP_SERVER_URL)
    transport = StreamableHttpTransport(url=server_url)
    client = Client(transport)
    await client.__aenter__()
    try:
        # Get available tools
        tools_result = await client.list_tools()
        tools = []
        if hasattr(tools_result, 'tools'):
            for tool in tools_result.tools:
                tools.append({
                    'name': tool.name,
                    'description': tool.description or '',
                    'input_schema': tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                })
        
        # Get available resources
        resources_result = await client.list_resources()
        resources = []
        if hasattr(resources_result, 'resources'):
            for resource in resources_result.resources:
                resources.append({
                    'uri': resource.uri,
                    'name': resource.name or resource.uri,
                    'description': resource.description or '',
                    'mime_type': resource.mimeType if hasattr(resource, 'mimeType') else 'text/plain'
                })
        
        return {
            'tools': tools,
            'resources': resources,
            'discovered_at': datetime.utcnow().isoformat()
        }
    finally:
        await client.__aexit__(None, None, None)

async def get_database_schema() -> str:
    """Get database schema for context"""
    try:
        schema_result = await get_mcp_resource("schema://database")
        if isinstance(schema_result, str):
            try:
                schema_data = json.loads(schema_result)
                return json.dumps(schema_data, indent=2)
            except:
                return schema_result
        return json.dumps(schema_result, indent=2)
    except Exception as e:
        logger.warning(f"Failed to get database schema: {e}")
        return "Database schema not available"

async def initialize_mcp_metadata():
    """Initialize MCP tools and schema cache at startup"""
    global mcp_tools_cache, mcp_schema_cache
    
    try:
        logger.info("Initializing MCP metadata cache...")
        
        # Discover MCP tools and resources
        mcp_tools_cache = await discover_mcp_tools()
        logger.info(f"Discovered {len(mcp_tools_cache.get('tools', []))} tools and {len(mcp_tools_cache.get('resources', []))} resources")
        
        # Get database schema
        mcp_schema_cache = await get_database_schema()
        logger.info(f"Cached database schema ({len(mcp_schema_cache)} characters)")
        
        logger.info("MCP metadata cache initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP metadata cache: {e}")
        mcp_tools_cache = {"tools": [], "resources": []}
        mcp_schema_cache = "Database schema not available"

async def get_cached_mcp_metadata() -> Dict[str, Any]:
    """Get cached MCP metadata"""
    global mcp_tools_cache, mcp_schema_cache
    
    if mcp_tools_cache is None or mcp_schema_cache is None:
        await initialize_mcp_metadata()
    
    return {
        "tools": mcp_tools_cache.get("tools", []) if mcp_tools_cache else [],
        "resources": mcp_tools_cache.get("resources", []) if mcp_tools_cache else [],
        "schema": mcp_schema_cache or "Database schema not available"
    }

# LLM Integration - Direct Gemini wrapper
try:
    from gemini_llm_wrapper import GeminiLLMWrapper
    
    HAS_GEMINI_LLM = True
    llm_instance: Optional[GeminiLLMWrapper] = None
except Exception as e:
    logger.warning(f"GeminiLLMWrapper import failed: {e}")
    HAS_GEMINI_LLM = False
    llm_instance = None

if HAS_GEMINI_LLM:
    try:
        llm_instance = GeminiLLMWrapper(
            model_id=os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-exp"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "600")),
            api_key=os.getenv("GOOGLE_API_KEY", ""),
        )
        logger.info("GeminiLLMWrapper initialized successfully")
    except Exception as e:
        logger.warning(f"GeminiLLMWrapper initialization failed: {e}")
        llm_instance = None

async def startup():
    """Initialize the MCP client"""
    logger.info(f"Simplified Database MCP Client starting on {CLIENT_HOST}:{CLIENT_PORT}")
    logger.info(f"Connected to MCP Server: {MCP_SERVER_URL}")
    
    if llm_instance:
        logger.info(f"LLM initialized: {llm_instance.get_model_info()}")
    else:
        logger.warning("LLM not initialized - set GOOGLE_API_KEY environment variable")
    
    # Initialize MCP metadata cache
    await initialize_mcp_metadata()
    logger.info("MCP Client startup completed successfully")

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Simplified Database MCP Client",
        "version": "1.0.0",
        "description": "Minimal FastAPI client for natural language database queries",
        "endpoints": {
            "ask_llm": "/ask_llm - Natural language database queries",
            "health": "/health - Client health check"
        },
        "docs": "/docs"
    }

@app.post("/ask_llm", response_model=AskLLMResponse)
async def ask_llm(request: AskLLMRequest):
    """
    Query the database using natural language with MCP server prompting.
    
    This endpoint uses the MCP server's built-in prompting capabilities
    to generate SQL queries from natural language questions.
    """
    start_time = datetime.utcnow()
    
    if llm_instance is None:
        return AskLLMResponse(
            success=False,
            question=request.question,
            error="LLM is not configured. Set GOOGLE_API_KEY environment variable.",
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )

    try:
        logger.info(f"Processing natural language question: {request.question}")
        
        # Step 1: Use MCP server's generate_sql_query prompt
        logger.info("Using MCP server's SQL generation prompt...")
        
        # Get the prompt from MCP server
        server_url = _normalize_server_url(MCP_SERVER_URL)
        transport = StreamableHttpTransport(url=server_url)
        client = Client(transport)
        await client.__aenter__()
        
        try:
            # Get the SQL generation prompt from MCP server
            prompt_messages = await client.get_prompt("generate_sql_query", {
                "question": request.question,
                "table_context": ""
            })
            
            # Convert MCP prompt to a single prompt string
            prompt_text = ""
            for message in prompt_messages.messages:
                if hasattr(message, 'content') and message.content:
                    prompt_text += f"{message.content}\n\n"
            
            logger.info(f"Generated prompt from MCP server ({len(prompt_text)} characters)")
            
        finally:
            await client.__aexit__(None, None, None)
        
        # Step 2: Invoke LLM with MCP server's prompt
        loop = asyncio.get_event_loop()
        llm_response = await loop.run_in_executor(None, llm_instance.invoke, prompt_text)
        logger.info(f"LLM generated SQL: {llm_response}")
        
        # Step 3: Clean and validate the SQL response
        sql_query = llm_response.strip()
        
        # Check if this is a generic response (not a SQL query)
        # Look for indicators that this is not a database-related query
        non_db_indicators = [
            "unable to provide",
            "unable to answer",
            "no information about",
            "not related to database",
            "I can only help with database queries",
            "weather information",
            "cooking",
            "recipe",
            "general knowledge"
        ]
        
        # Check if the response contains non-database indicators
        sql_query_lower = sql_query.lower()
        is_non_db_query = any(indicator in sql_query_lower for indicator in non_db_indicators)
        
        logger.info(f"Checking non-db indicators in: {sql_query_lower[:100]}...")
        logger.info(f"Found non-db indicators: {[ind for ind in non_db_indicators if ind in sql_query_lower]}")
        
        # Also check if it's mostly comments with minimal actual SQL
        comment_lines = [line for line in sql_query.split('\n') if line.strip().startswith('--')]
        sql_lines = [line for line in sql_query.split('\n') if line.strip() and not line.strip().startswith('--')]
        
        if is_non_db_query or (len(comment_lines) > len(sql_lines) and len(sql_lines) <= 2):
            logger.info(f"Detected non-database query, returning generic response")
            return AskLLMResponse(
                success=True,
                question=request.question,
                sql_query="N/A - Non-database query",
                data=[{"message": sql_query}],
                row_count=1,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                error=None
            )
        
        # Remove any markdown formatting or extra text
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Step 4: Execute the SQL query
        logger.info(f"Executing SQL: {sql_query}")
        query_result = await call_mcp_tool("query_database", 
                                          query=sql_query, 
                                          limit=request.max_results)
        
        # Step 5: Parse and format results
        if isinstance(query_result, str):
            try:
                data = json.loads(query_result)
                result_data = data if isinstance(data, list) else [data] if data else []
            except json.JSONDecodeError:
                result_data = [{"raw_result": query_result}]
        else:
            result_data = query_result if isinstance(query_result, list) else [query_result]
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return AskLLMResponse(
            success=True,
            question=request.question,
            sql_query=sql_query,
            data=result_data,
            row_count=len(result_data),
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error in /ask_llm endpoint: {e}")
        return AskLLMResponse(
            success=False,
            question=request.question,
            error=str(e),
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check client API service health
    
    Returns basic health information about the client service.
    """
    try:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )



async def main():
    """Main function to start the MCP client"""
    # Initialize the client
    await startup()
    
    # Start the FastAPI server
    import uvicorn
    logger.info(f"Starting FastAPI server on {CLIENT_HOST}:{CLIENT_PORT}")
    
    # Use uvicorn.run with proper configuration
    config = uvicorn.Config(app, host=CLIENT_HOST, port=CLIENT_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())