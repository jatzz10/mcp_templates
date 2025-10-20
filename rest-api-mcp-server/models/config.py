"""
Configuration models for MCP Client and Server

This module contains all configuration classes used across the application.
"""

import os
from typing import Optional


class MCPClientConfig:
    """Configuration class for MCP Client"""
    
    def __init__(self):
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
        self.client_host = os.getenv("CLIENT_HOST", "0.0.0.0")
        self.client_port = int(os.getenv("CLIENT_PORT", "8001"))
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_model_id = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash-exp")
        self.nail_model_id = os.getenv("NAIL_MODEL_ID", "claude-3.5")
        self.nail_temperature = float(os.getenv("NAIL_TEMPERATURE", "0.1"))
        self.nail_max_tokens = int(os.getenv("NAIL_MAX_TOKENS", "300"))
        
        # Debug: Print loaded configuration
        self._print_config()
    
    def _print_config(self):
        """Print configuration for debugging"""
        print(f"🔧 Configuration loaded:")
        print(f"   MCP_SERVER_URL: {self.mcp_server_url}")
        print(f"   CLIENT_HOST: {self.client_host}")
        print(f"   CLIENT_PORT: {self.client_port}")
        print(f"   GOOGLE_API_KEY: {'***' if self.google_api_key else 'NOT SET'}")
        print(f"   GEMINI_MODEL_ID: {self.gemini_model_id}")
        print(f"   NAIL_MODEL_ID: {self.nail_model_id}")
        print(f"   NAIL_TEMPERATURE: {self.nail_temperature}")
        print(f"   NAIL_MAX_TOKENS: {self.nail_max_tokens}")
    
    def normalize_server_url(self, url: str) -> str:
        """Normalize MCP server URL"""
        url = url.strip().rstrip("/")
        return url if url.endswith("/mcp") else url + "/mcp"


class DatabaseConfig:
    """Configuration class for Database MCP Server"""
    
    def __init__(self):
        self.db_type = os.getenv("DB_TYPE", "mysql").lower()
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "3306"))
        self.db_user = os.getenv("DB_USER", "root")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "test_db")
        self.db_path = os.getenv("DB_PATH", "")
        
        # Server configuration
        self.server_host = os.getenv("SERVER_HOST", "127.0.0.1")
        self.server_port = int(os.getenv("SERVER_PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Cache configuration
        self.schema_cache_ttl = int(os.getenv("SCHEMA_CACHE_TTL", "3600"))
        self.query_cache_ttl = int(os.getenv("QUERY_CACHE_TTL", "300"))
        self.max_query_limit = int(os.getenv("MAX_QUERY_LIMIT", "1000"))
        
        # Debug: Print loaded configuration
        self._print_config()
    
    def _print_config(self):
        """Print configuration for debugging"""
        print(f"🔧 Database Configuration loaded:")
        print(f"   DB_TYPE: {self.db_type}")
        print(f"   DB_HOST: {self.db_host}")
        print(f"   DB_PORT: {self.db_port}")
        print(f"   DB_USER: {self.db_user}")
        print(f"   DB_NAME: {self.db_name}")
        print(f"   SERVER_HOST: {self.server_host}")
        print(f"   SERVER_PORT: {self.server_port}")
        print(f"   LOG_LEVEL: {self.log_level}")
    
    def get_connection_string(self) -> str:
        """Get database connection string based on type"""
        if self.db_type == "mysql":
            return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type == "postgresql":
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{self.db_path or ':memory:'}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
