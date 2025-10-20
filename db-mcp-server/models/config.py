"""
Configuration models for MCP Client and Server

This module contains all configuration classes used across the application.
"""

import os
from typing import Optional


class MCPClientConfig:
    """Configuration class for MCP Client"""
    


class DatabaseConfig:
    """Configuration class for Database MCP Server"""
    
    def __init__(self):
        # Db configuration
        self.server_host = os.getenv("SERVER_HOST", "127.0.0.1")
        self.server_port = int(os.getenv("SERVER_PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Debug: Print loaded configuration
        self._print_config()
    
    def _print_config(self):
        """Print configuration for debugging"""
        print(f"🔧 Database MCP Server Configuration loaded:")
        print(f"   SERVER_HOST: {self.server_host}")
        print(f"   SERVER_PORT: {self.server_port}")
        print(f"   LOG_LEVEL: {self.log_level}")
