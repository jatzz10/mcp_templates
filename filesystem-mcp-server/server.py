#!/usr/bin/env python3
"""
Generic Database MCP Server - Implementation

A complete, production-ready MCP server that connects to various database types.
Supports MySQL, PostgreSQL, SQLite, and other SQL databases.

Features:
- Multiple database type support (MySQL, PostgreSQL, SQLite)
- Database schema caching and auto-refresh
- Query execution with security validation
- Static data resources (database schema)
- Health monitoring
- Configurable via environment variables

Usage:
    python server.py

Environment Variables:
    DB_TYPE=mysql                    # mysql, postgresql, sqlite
    DB_HOST=localhost               # Database host
    DB_PORT=3306                    # Database port
    DB_USER=root                    # Database user
    DB_PASSWORD=password            # Database password
    DB_NAME=my_database             # Database name
    DB_PATH=/path/to/database.db    # For SQLite
"""

# Load environment variables
from utils.env_loader import load_environment
from utils.logging_config import setup_logging

# Import server components
from models.config import DatabaseConfig
from server import DatabaseMCPServer

# Load environment and setup logging
load_environment()
logger = setup_logging()


def main():
    """Main function to start the MCP server"""
    try:
        # Create configuration
        config = DatabaseConfig()
        
        # Create and start server
        server = DatabaseMCPServer(config)
        
        # Print server information
        server.print_server_info()
        
        # Start the server
        server.start()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise


if __name__ == "__main__":
    main()
