#!/usr/bin/env python3
"""
Database MCP Client

A FastAPI-based MCP client specifically designed for database operations.
Uses fastmcp library to connect to the MCP server via streamable-http transport.

Features:
- SQL query execution with validation
- Database schema access
- Health monitoring
- Error handling and logging
- Database-specific response models

Usage:
    uvicorn mcp_client:app --host 0.0.0.0 --port 8001

Environment Variables:
    MCP_SERVER_URL=http://localhost:8000
    CLIENT_HOST=0.0.0.0
    CLIENT_PORT=8001
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
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

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from the same directory as this script
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from: {env_path}")
    else:
        print(f"⚠️  Environment file not found: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Error loading environment file: {e}")

# LLM Integration - Direct Gemini wrapper (generic)
try:
    from gemini_llm_wrapper import GeminiLLMWrapper
    
    HAS_GEMINI_LLM = True
    llm_instance: Optional[GeminiLLMWrapper] = None
except Exception as e:
    print(f"⚠️  GeminiLLMWrapper import failed: {e}")
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
        print("✅ GeminiLLMWrapper initialized successfully")
    except Exception as e:
        print(f"⚠️  GeminiLLMWrapper initialization failed: {e}")
        llm_instance = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Database MCP Client",
    description="FastAPI client for Database MCP Server",
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
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
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

# MCP Client helpers
def _normalize_server_url(url: str) -> str:
    url = url.strip().rstrip("/")
    return url if url.endswith("/mcp") else url + "/mcp"

async def discover_mcp_tools() -> Dict[str, Any]:
    """Discover available MCP tools and resources"""
    try:
        server_url = _normalize_server_url(MCP_SERVER_URL)
        transport = StreamableHttpTransport(url=server_url)
        client = Client(transport)
        await client.__aenter__()
        
        try:
            # Get tools and resources
            tools = await client.list_tools()
            resources = await client.list_resources()
            
            return {
                "tools": [{"name": tool.name, "description": tool.description} for tool in tools.tools],
                "resources": [{"uri": resource.uri, "name": resource.name, "description": resource.description} for resource in resources.resources]
            }
        finally:
            await client.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Failed to discover MCP tools: {e}")
        return {"tools": [], "resources": []}

async def get_database_schema() -> str:
    """Get database schema from MCP server"""
    try:
        server_url = _normalize_server_url(MCP_SERVER_URL)
        transport = StreamableHttpTransport(url=server_url)
        client = Client(transport)
        await client.__aenter__()
        
        try:
            # Get schema resource
            schema_resource = await client.read_resource("schema://database")
            return schema_resource.contents[0].text if schema_resource.contents else "Schema not available"
        finally:
            await client.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Failed to get database schema: {e}")
        return "Schema not available"

async def initialize_mcp_metadata():
    """Initialize MCP metadata cache"""
    global mcp_tools_cache, mcp_schema_cache
    
    logger.info("Initializing MCP metadata cache...")
    mcp_tools_cache = await discover_mcp_tools()
    mcp_schema_cache = await get_database_schema()
    logger.info(f"Discovered {len(mcp_tools_cache.get('tools', []))} tools and {len(mcp_tools_cache.get('resources', []))} resources")

# Pydantic Models
class DatabaseQuery(BaseModel):
    """Database query request model"""
    query: str = Field(..., description="SQL query to execute", example="SELECT * FROM users LIMIT 10")
    limit: Optional[int] = Field(100, description="Maximum number of results", ge=1, le=1000)

class DatabaseResponse(BaseModel):
    """Database query response model"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    row_count: Optional[int] = None

class SchemaResponse(BaseModel):
    """Database schema response model"""
    success: bool
    schema: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generated_at: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    database_type: Optional[str] = None
    connected: Optional[bool] = None
    timestamp: str
    error: Optional[str] = None

class AskLLMRequest(BaseModel):
    """Natural language query request model"""
    question: str = Field(..., description="Natural language question about the database", example="Show me all users")
    max_results: Optional[int] = Field(100, description="Maximum number of results", ge=1, le=1000)

class AskLLMResponse(BaseModel):
    """Natural language query response model"""
    success: bool
    question: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None

class RefreshResponse(BaseModel):
    """Schema refresh response model"""
    success: bool
    message: str
    generated_at: Optional[str] = None
    total_tables: Optional[int] = None
    error: Optional[str] = None


# Startup function
async def startup():
    """Initialize the MCP client"""
    logger.info(f"Generic Database MCP Client starting on {CLIENT_HOST}:{CLIENT_PORT}")
    logger.info(f"Connected to MCP Server: {MCP_SERVER_URL}")
    
    if llm_instance:
        logger.info(f"LLM initialized: {llm_instance.get_model_info()}")
    else:
        logger.warning("LLM not initialized - set GOOGLE_API_KEY environment variable")
    
    # Initialize MCP metadata cache
    await initialize_mcp_metadata()
    logger.info("MCP Client startup completed successfully")

# /call_prompt models
class CallPromptRequest(BaseModel):
    """Request model for MCP prompt invocation"""
    prompt_name: str = Field(..., description="Name of the MCP prompt to call")
    args: Optional[Dict[str, Any]] = Field(default={}, description="Arguments for the prompt")

class CallPromptResponse(BaseModel):
    """Response model for MCP prompt invocation"""
    success: bool
    prompt_messages: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

# MCP Client Functions
async def call_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Call MCP tool on the server"""
    try:
        server_url = _normalize_server_url(MCP_SERVER_URL)
        transport = StreamableHttpTransport(url=server_url)
        client = Client(transport)
        await client.__aenter__()
        try:
            result = await client.call_tool(tool_name, kwargs)
            if hasattr(result, 'content') and result.content:
                text = result.content[0].text
                try:
                    return json.loads(text)
                except Exception:
                    return text
            return {}
        finally:
            await client.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"MCP tool call failed: {e}")
        raise

async def get_mcp_resource(resource_uri: str) -> Dict[str, Any]:
    """Get MCP resource from the server"""
    try:
        server_url = _normalize_server_url(MCP_SERVER_URL)
        transport = StreamableHttpTransport(url=server_url)
        client = Client(transport)
        await client.__aenter__()
        try:
            res = await client.read_resource(resource_uri)
            if hasattr(res, 'contents') and res.contents:
                text = res.contents[0].text
                try:
                    return json.loads(text)
                except Exception:
                    return text
            return {}
        finally:
            await client.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"MCP resource call failed: {e}")
        raise

async def call_mcp_prompt(prompt_name: str, **kwargs) -> List[Dict[str, Any]]:
    """Call MCP prompt on the server"""
    try:
        server_url = _normalize_server_url(MCP_SERVER_URL)
        transport = StreamableHttpTransport(url=server_url)
        client = Client(transport)
        await client.__aenter__()
        try:
            result = await client.call_prompt(prompt_name, **kwargs)
            return result
        finally:
            await client.__aexit__(None, None, None)
    except Exception as e:
        logger.error(f"Error calling MCP prompt {prompt_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to call prompt: {str(e)}")


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Database MCP Client",
        "version": "1.0.0",
        "description": "FastAPI client for Database MCP Server",
        "mcp_server_url": MCP_SERVER_URL,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.post("/query", response_model=DatabaseResponse)
async def query_database(query_data: DatabaseQuery):
    """
    Execute SQL query against the database
    
    - **query**: SQL query to execute (SELECT only)
    - **limit**: Maximum number of results (1-1000)
    
    Returns query results with execution metadata.
    """
    start_time = datetime.utcnow()
    
    try:
        # Call MCP tool
        result = await call_mcp_tool("query_database", query=query_data.query, limit=query_data.limit)
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Parse result
        if isinstance(result, str):
            try:
                data = json.loads(result)
                if isinstance(data, list):
                    return DatabaseResponse(
                        success=True,
                        data=data,
                        execution_time=execution_time,
                        row_count=len(data)
                    )
                else:
                    return DatabaseResponse(
                        success=True,
                        data=[data] if data else [],
                        execution_time=execution_time,
                        row_count=1 if data else 0
                    )
            except json.JSONDecodeError:
                return DatabaseResponse(
                    success=False,
                    error=f"Invalid JSON response: {result}",
                    execution_time=execution_time
                )
        else:
            return DatabaseResponse(
                success=True,
                data=result if isinstance(result, list) else [result],
                execution_time=execution_time,
                row_count=len(result) if isinstance(result, list) else 1
            )
                
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Database query error: {e}")
        return DatabaseResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@app.get("/schema", response_model=SchemaResponse)
async def get_database_schema():
    """
    Get complete database schema
    
    Returns database schema including tables, columns, indexes, and relationships.
    """
    try:
        # Get MCP resource
        schema = await get_mcp_resource("schema://database")
        
        return SchemaResponse(
            success=True,
            schema=schema,
            generated_at=schema.get("metadata", {}).get("generated_at") if isinstance(schema, dict) else None
        )
        
    except Exception as e:
        logger.error(f"Schema retrieval error: {e}")
        return SchemaResponse(
            success=False,
            error=str(e)
        )


@app.post("/refresh-schema", response_model=RefreshResponse)
async def refresh_schema(background_tasks: BackgroundTasks):
    """
    Refresh database schema cache
    
    Triggers a background refresh of the database schema cache.
    """
    try:
        # Call MCP tool
        result = await call_mcp_tool("refresh_schema")
        
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return RefreshResponse(
                    success=False,
                    error=f"Invalid JSON response: {result}"
                )
        
        if result.get("status") == "success":
            return RefreshResponse(
                success=True,
                message="Schema refreshed successfully",
                generated_at=result.get("generated_at"),
                total_tables=result.get("total_tables")
            )
        else:
            return RefreshResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
                
    except Exception as e:
        logger.error(f"Schema refresh error: {e}")
        return RefreshResponse(
            success=False,
            error=str(e)
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check database health
    
    Returns database connection status and health information.
    """
    try:
        # Call MCP tool
        health = await call_mcp_tool("health_check")
        
        if isinstance(health, str):
            try:
                health = json.loads(health)
            except json.JSONDecodeError:
                return HealthResponse(
                    status="error",
                    error=f"Invalid JSON response: {health}",
                    timestamp=datetime.utcnow().isoformat()
                )
        
        return HealthResponse(
            status=health.get("status", "unknown"),
            database_type=health.get("database_type"),
            connected=health.get("connected"),
            timestamp=health.get("timestamp", datetime.utcnow().isoformat()),
            error=health.get("error")
        )
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="error",
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )




@app.post("/ask_llm", response_model=AskLLMResponse)
async def ask_llm(request: AskLLMRequest):
    """
    Natural language database query endpoint.
    
    Takes a natural language question and uses the LLM to generate SQL queries
    to fetch data from the database via the MCP server.
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
        
        # Step 5: Parse and return results
        if query_result.get("success"):
            data = query_result.get("data", [])
            return AskLLMResponse(
                success=True,
                question=request.question,
                sql_query=sql_query,
                data=data,
                row_count=len(data),
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                error=None
            )
        else:
            return AskLLMResponse(
                success=False,
                question=request.question,
                sql_query=sql_query,
                data=[{"error": query_result.get("error", "Unknown error")}],
                row_count=1,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                error=query_result.get("error", "Query execution failed")
            )
            
    except Exception as e:
        logger.error(f"Error in ask_llm: {e}")
        return AskLLMResponse(
            success=False,
            question=request.question,
            error=f"Internal error: {str(e)}",
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )

@app.post("/call_prompt", response_model=CallPromptResponse)
async def call_prompt(request: CallPromptRequest):
    """
    Call an MCP prompt on the server.
    
    This endpoint invokes a specific MCP prompt with the provided arguments
    and returns the structured prompt messages.
    """
    start_time = datetime.utcnow()
    
    try:
        # Call the MCP prompt
        prompt_messages = await call_mcp_prompt(request.prompt_name, **request.args)
        
        return CallPromptResponse(
            success=True,
            prompt_messages=prompt_messages,
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )
        
    except Exception as e:
        logger.error(f"Error in /call_prompt endpoint: {e}")
        return CallPromptResponse(
            success=False,
            error=str(e),
            execution_time=(datetime.utcnow() - start_time).total_seconds()
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
