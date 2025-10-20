#!/usr/bin/env python3
"""
REST API MCP Server Entry Point

This is the main entry point for the REST API MCP Server.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.env_loader import load_environment
from utils.logging_config import setup_logging
from models.config import RestApiConfig
from server import RestApiMCPServer


def main():
    """Main entry point for the REST API MCP Server"""
    try:
        # Load environment variables
        load_environment()
        
        # Setup logging
        setup_logging()
        
        # Load configuration
        config = RestApiConfig()
        
        # Create and start server
        server = RestApiMCPServer(config)
        server.print_server_info()
        server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
