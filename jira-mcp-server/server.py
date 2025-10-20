#!/usr/bin/env python3
"""
JIRA MCP Server Entry Point

This is the main entry point for the JIRA MCP Server.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.env_loader import load_environment
from utils.logging_config import setup_logging
from models.config import JiraConfig
from server import JiraMCPServer


def main():
    """Main entry point for the JIRA MCP Server"""
    try:
        # Load environment variables
        load_environment()
        
        # Setup logging
        setup_logging()
        
        # Load configuration
        config = JiraConfig()
        
        # Create and start server
        server = JiraMCPServer(config)
        server.print_server_info()
        server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
