#!/usr/bin/env python3
"""
FileSystem MCP Client

A FastAPI-based MCP client specifically designed for file system operations.
Uses fastmcp library to connect to the MCP server via streamable-http transport.

Features:
- File system query execution with validation
- Directory structure access
- File search and content reading
- Health monitoring
- Error handling and logging
- File system-specific response models

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
from fastmcp import FastMCP
from dotenv import load_dotenv
from gemini_llm_wrapper import GeminiLLMWrapper

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="FileSystem MCP Client",
    description="FastAPI client for FileSystem MCP Server",
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

# MCP Client
mcp_client = FastMCP("filesystem-mcp-client")

# Global variables for caching
mcp_tools_cache = None
mcp_schema_cache = None
llm_instance = None

# Initialize LLM
def initialize_llm():
    """Initialize the Gemini LLM wrapper"""
    global llm_instance
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        model_id = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-exp")
        temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
        max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", "600"))
        
        if not api_key or api_key == "your_google_api_key_here":
            logger.warning("Google API key not configured. LLM features will be disabled.")
            return None
        
        llm_instance = GeminiLLMWrapper(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
        logger.info(f"LLM initialized: {llm_instance.get_model_info()}")
        return llm_instance
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        return None

# MCP metadata caching functions
async def discover_mcp_tools():
    """Discover available MCP tools from the server"""
    global mcp_tools_cache
    try:
        await mcp_client.connect(MCP_SERVER_URL, transport="streamable-http")
        tools = await mcp_client.list_tools()
        await mcp_client.disconnect()
        mcp_tools_cache = tools
        logger.info(f"Discovered {len(tools)} MCP tools")
        return tools
    except Exception as e:
        logger.error(f"Failed to discover MCP tools: {e}")
        return []

async def get_filesystem_structure():
    """Get filesystem structure from the server"""
    global mcp_schema_cache
    try:
        await mcp_client.connect(MCP_SERVER_URL, transport="streamable-http")
        structure = await mcp_client.get_resource("structure://filesystem")
        await mcp_client.disconnect()
        mcp_schema_cache = structure
        logger.info("Retrieved filesystem structure")
        return structure
    except Exception as e:
        logger.error(f"Failed to get filesystem structure: {e}")
        return {}

async def initialize_mcp_metadata():
    """Initialize MCP metadata cache"""
    logger.info("Initializing MCP metadata cache...")
    await discover_mcp_tools()
    await get_filesystem_structure()
    logger.info("MCP metadata cache initialized")

# Pydantic Models
class FileSystemQuery(BaseModel):
    """File system query request model"""
    query_type: str = Field(..., description="Query type: list, search, read, info", example="list")
    path: Optional[str] = Field("", description="File or directory path")
    search_term: Optional[str] = Field("", description="Search term for file search")
    extension: Optional[str] = Field("", description="File extension filter")
    limit: Optional[int] = Field(100, description="Maximum number of results", ge=1, le=1000)

class FileSystemResponse(BaseModel):
    """File system query response model"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    result_count: Optional[int] = None

class StructureResponse(BaseModel):
    """File system structure response model"""
    success: bool
    structure: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generated_at: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    root_path: Optional[str] = None
    read_access: Optional[bool] = None
    timestamp: str
    error: Optional[str] = None

class RefreshResponse(BaseModel):
    """Structure refresh response model"""
    success: bool
    message: str
    generated_at: Optional[str] = None
    root_path: Optional[str] = None
    error: Optional[str] = None


# /ask_llm models
class AskLLMRequest(BaseModel):
    question: str

class AskLLMResponse(BaseModel):
    success: bool
    action: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None

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
        # Connect to MCP server
        await mcp_client.connect(MCP_SERVER_URL, transport="streamable-http")
        
        # Call the tool
        result = await mcp_client.call_tool(tool_name, **kwargs)
        
        # Disconnect
        await mcp_client.disconnect()
        
        return result
    except Exception as e:
        logger.error(f"MCP tool call failed: {e}")
        raise

async def get_mcp_resource(resource_uri: str) -> Dict[str, Any]:
    """Get MCP resource from the server"""
    try:
        # Connect to MCP server
        await mcp_client.connect(MCP_SERVER_URL, transport="streamable-http")
        
        # Get the resource
        result = await mcp_client.get_resource(resource_uri)
        
        # Disconnect
        await mcp_client.disconnect()
        
        return result
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
        "name": "FileSystem MCP Client",
        "version": "1.0.0",
        "description": "FastAPI client for FileSystem MCP Server",
        "mcp_server_url": MCP_SERVER_URL,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.post("/query", response_model=FileSystemResponse)
async def query_filesystem(query_data: FileSystemQuery):
    """
    Execute file system query
    
    - **query_type**: Type of query (list, search, read, info)
    - **path**: File or directory path
    - **search_term**: Search term for file search
    - **extension**: File extension filter
    - **limit**: Maximum number of results (1-1000)
    
    Returns file system query results with execution metadata.
    """
    start_time = datetime.utcnow()
    
    try:
        # Call MCP tool
        result = await call_mcp_tool(
            "query_filesystem",
            query_type=query_data.query_type,
            path=query_data.path,
            search_term=query_data.search_term,
            extension=query_data.extension,
            limit=query_data.limit
        )
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Parse result
        if isinstance(result, str):
            try:
                data = json.loads(result)
                if isinstance(data, list):
                    return FileSystemResponse(
                        success=True,
                        data=data,
                        execution_time=execution_time,
                        result_count=len(data)
                    )
                else:
                    return FileSystemResponse(
                        success=True,
                        data=[data] if data else [],
                        execution_time=execution_time,
                        result_count=1 if data else 0
                    )
            except json.JSONDecodeError:
                return FileSystemResponse(
                    success=False,
                    error=f"Invalid JSON response: {result}",
                    execution_time=execution_time
                )
        else:
            return FileSystemResponse(
                success=True,
                data=result if isinstance(result, list) else [result],
                execution_time=execution_time,
                result_count=len(result) if isinstance(result, list) else 1
            )
                
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"File system query error: {e}")
        return FileSystemResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@app.get("/structure", response_model=StructureResponse)
async def get_filesystem_structure():
    """
    Get file system structure
    
    Returns the complete file system structure including directories and files.
    """
    try:
        # Get MCP resource
        structure = await get_mcp_resource("structure://filesystem")
        
        return StructureResponse(
            success=True,
            structure=structure,
            generated_at=structure.get("metadata", {}).get("generated_at") if isinstance(structure, dict) else None
        )
        
    except Exception as e:
        logger.error(f"Structure retrieval error: {e}")
        return StructureResponse(
            success=False,
            error=str(e)
        )


@app.post("/refresh-structure", response_model=RefreshResponse)
async def refresh_structure(background_tasks: BackgroundTasks):
    """
    Refresh file system structure cache
    
    Triggers a background refresh of the file system structure cache.
    """
    try:
        # Call MCP tool
        result = await call_mcp_tool("refresh_structure")
        
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
                message="Structure refreshed successfully",
                generated_at=result.get("generated_at"),
                root_path=result.get("root_path")
            )
        else:
            return RefreshResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
                
    except Exception as e:
        logger.error(f"Structure refresh error: {e}")
        return RefreshResponse(
            success=False,
            error=str(e)
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check file system health
    
    Returns file system access status and health information.
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
            root_path=health.get("root_path"),
            read_access=health.get("read_access"),
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
async def ask_llm(payload: AskLLMRequest):
    """Ask LLM to generate filesystem query from natural language"""
    global llm_instance
    
    if llm_instance is None:
        return AskLLMResponse(success=False, error="LLM is not configured. Set GOOGLE_API_KEY environment variable.")
    
    try:
        # Get the prompt from the MCP server
        await mcp_client.connect(MCP_SERVER_URL, transport="streamable-http")
        prompt_messages = await mcp_client.call_prompt("generate_filesystem_query", user_question=payload.question)
        await mcp_client.disconnect()
        
        # Compose the final prompt
        system_message = prompt_messages[0]["content"]
        user_message = prompt_messages[1]["content"]
        final_prompt = f"{system_message}\n\n{user_message}"
        
        # Invoke the LLM
        llm_response = llm_instance.invoke(final_prompt)
        
        # Parse the LLM response
        try:
            query_params = json.loads(llm_response)
        except json.JSONDecodeError:
            return AskLLMResponse(success=False, error="LLM did not return valid JSON", result=llm_response)
        
        # Check if it's a generic response (non-filesystem question)
        if "i can only help with" in query_params.get("query_type", "").lower():
            return AskLLMResponse(
                success=True, 
                result=[{"message": query_params["query_type"], "type": "generic_response"}]
            )
        
        # Execute the filesystem query
        result = await call_mcp_tool(
            "query_filesystem",
            query_type=query_params.get("query_type", "list"),
            path=query_params.get("path", ""),
            search_term=query_params.get("search_term", ""),
            extension=query_params.get("extension", ""),
            limit=query_params.get("limit", 100)
        )
        
        # Parse and return the result
        if isinstance(result, str):
            try:
                data = json.loads(result)
                return AskLLMResponse(success=True, result=data)
            except json.JSONDecodeError:
                return AskLLMResponse(success=True, result=[{"raw_result": result}])
        else:
            return AskLLMResponse(success=True, result=result)
            
    except Exception as e:
        logger.exception("/ask_llm error")
        return AskLLMResponse(success=False, error=str(e))

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

async def startup():
    """Initialize the application"""
    logger.info(f"FileSystem MCP Client starting on {CLIENT_HOST}:{CLIENT_PORT}")
    logger.info(f"Connected to MCP Server: {MCP_SERVER_URL}")
    
    # Initialize LLM
    initialize_llm()
    
    # Initialize MCP metadata cache
    await initialize_mcp_metadata()

async def main():
    """Main entry point"""
    await startup()
    
    import uvicorn
    config = uvicorn.Config(app, host=CLIENT_HOST, port=CLIENT_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
