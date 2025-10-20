#!/usr/bin/env python3
"""
Simplified Database MCP Client - Class-based Implementation

A minimal FastAPI client with only 3 essential endpoints:
1. Natural language database queries using NailLLMLangchain
2. Client health check
3. MCP server connection check

Usage:
    uvicorn client:app --host 0.0.0.0 --port 8001
"""

import asyncio
import logging
import uvicorn

# Load environment variables
from utils.env_loader import load_environment
from utils.logging_config import setup_logging

# Import models and client classes
from models.config import MCPClientConfig
from client import FastAPIClient

# Load environment and setup logging
load_environment()
logger = setup_logging()

# Global configuration and app instance
config = MCPClientConfig()
fastapi_client = FastAPIClient(config)
app = fastapi_client.app


# Main function
async def main():
    """Main function to start the MCP client"""
    try:
        # Start the FastAPI server
        logger.info(f"Starting FastAPI server on {config.client_host}:{config.client_port}")
        
        # Use uvicorn.run with proper configuration
        uvicorn_config = uvicorn.Config(app, host=config.client_host, port=config.client_port, log_level="info")
        server = uvicorn.Server(uvicorn_config)
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
