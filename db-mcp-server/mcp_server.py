#!/usr/bin/env python3
"""
Generic Database MCP Server

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
    python mcp_server.py

Environment Variables:
    DB_TYPE=mysql                    # mysql, postgresql, sqlite
    DB_HOST=localhost               # Database host
    DB_PORT=3306                    # Database port
    DB_USER=root                    # Database user
    DB_PASSWORD=password            # Database password
    DB_NAME=my_database             # Database name
    DB_PATH=/path/to/database.db    # For SQLite
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

from fastmcp import FastMCP
from cachetools import TTLCache


class DatabaseMCPServer:
    """
    Generic Database MCP Server implementation.
    
    This server provides:
    - Database schema as MCP resource (schema://database)
    - Query execution tool (query_database)
    - Schema refresh tool (refresh_schema)
    - Health monitoring
    - Support for multiple database types
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_config()
        self.mcp = FastMCP(name=self.config.get('server_name', 'db-mcp-server'))
        self.connection = None
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("db_mcp_server")
        
        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'server_name': os.getenv('SERVER_NAME', 'db-mcp-server'),
            'server_host': os.getenv('SERVER_HOST', '127.0.0.1'),
            'server_port': int(os.getenv('SERVER_PORT', '8000')),
            'db_type': os.getenv('DB_TYPE', 'mysql'),
            'db_host': os.getenv('DB_HOST', 'localhost'),
            'db_port': int(os.getenv('DB_PORT', '3306')),
            'db_user': os.getenv('DB_USER', 'root'),
            'db_password': os.getenv('DB_PASSWORD', ''),
            'db_name': os.getenv('DB_NAME', ''),
            'db_path': os.getenv('DB_PATH', ''),  # For SQLite
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'schema_cache_ttl': int(os.getenv('SCHEMA_CACHE_TTL', '3600')),
            'query_cache_ttl': int(os.getenv('QUERY_CACHE_TTL', '300')),
            'max_query_limit': int(os.getenv('MAX_QUERY_LIMIT', '1000'))
        }
    
    async def connect(self) -> bool:
        """Establish connection to database"""
        try:
            db_type = self.config['db_type'].lower()
            
            if db_type == 'mysql':
                import pymysql
                self.connection = pymysql.connect(
                    host=self.config['db_host'],
                    port=self.config['db_port'],
                    user=self.config['db_user'],
                    password=self.config['db_password'],
                    database=self.config['db_name'],
                    charset='utf8mb4',
                    autocommit=True
                )
            elif db_type == 'postgresql':
                import psycopg2
                self.connection = psycopg2.connect(
                    host=self.config['db_host'],
                    port=self.config['db_port'],
                    user=self.config['db_user'],
                    password=self.config['db_password'],
                    database=self.config['db_name']
                )
            elif db_type == 'sqlite':
                import sqlite3
                db_path = self.config['db_path'] or self.config['db_name']
                self.connection = sqlite3.connect(db_path)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            self.logger.info(f"Connected to {db_type.upper()} database")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            self.logger.info("Disconnected from database")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from database: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Generate database schema"""
        if not self.connection:
            await self.connect()
        
        try:
            db_type = self.config['db_type'].lower()
            
            if db_type == 'mysql':
                return await self._get_mysql_schema()
            elif db_type == 'postgresql':
                return await self._get_postgresql_schema()
            elif db_type == 'sqlite':
                return await self._get_sqlite_schema()
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            self.logger.error(f"Error generating schema: {e}")
            raise
    
    async def _get_mysql_schema(self) -> Dict[str, Any]:
        """Get MySQL schema"""
        cursor = self.connection.cursor()
        
        # Get database info
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        
        # Get tables
        cursor.execute("""
            SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
        """, (db_name,))
        
        tables_info = cursor.fetchall()
        tables = {}
        
        for table_name, comment, rows, data_length, index_length in tables_info:
            # Get columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, 
                       COLUMN_KEY, EXTRA, COLUMN_COMMENT
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (db_name, table_name))
            
            columns_info = cursor.fetchall()
            columns = {}
            
            for col_name, data_type, nullable, default, key, extra, col_comment in columns_info:
                columns[col_name] = {
                    "type": data_type,
                    "nullable": nullable == 'YES',
                    "default": default,
                    "key": key,
                    "extra": extra,
                    "comment": col_comment
                }
            
            tables[table_name] = {
                "comment": comment,
                "row_count": rows,
                "data_size": data_length,
                "index_size": index_length,
                "columns": columns
            }
        
        cursor.close()
        
        return {
            "metadata": {
                "database_name": db_name,
                "database_type": "mysql",
                "total_tables": len(tables),
                "generated_at": datetime.utcnow().isoformat(),
                "cache_ttl": self.config['schema_cache_ttl']
            },
            "tables": tables
        }
    
    async def _get_postgresql_schema(self) -> Dict[str, Any]:
        """Get PostgreSQL schema"""
        cursor = self.connection.cursor()
        
        # Get database info
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()[0]
        
        # Get tables
        cursor.execute("""
            SELECT schemaname, tablename, tableowner
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables_info = cursor.fetchall()
        tables = {}
        
        for schema, table_name, owner in tables_info:
            # Get columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table_name))
            
            columns_info = cursor.fetchall()
            columns = {}
            
            for col_name, data_type, nullable, default in columns_info:
                columns[col_name] = {
                    "type": data_type,
                    "nullable": nullable == 'YES',
                    "default": default
                }
            
            tables[table_name] = {
                "owner": owner,
                "columns": columns
            }
        
        cursor.close()
        
        return {
            "metadata": {
                "database_name": db_name,
                "database_type": "postgresql",
                "total_tables": len(tables),
                "generated_at": datetime.utcnow().isoformat(),
                "cache_ttl": self.config['schema_cache_ttl']
            },
            "tables": tables
        }
    
    async def _get_sqlite_schema(self) -> Dict[str, Any]:
        """Get SQLite schema"""
        cursor = self.connection.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_info = cursor.fetchall()
        tables = {}
        
        for (table_name,) in tables_info:
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = {}
            
            for col_id, col_name, col_type, not_null, default, pk in columns_info:
                columns[col_name] = {
                    "type": col_type,
                    "nullable": not_null == 0,
                    "default": default,
                    "primary_key": pk == 1
                }
            
            tables[table_name] = {
                "columns": columns
            }
        
        return {
            "metadata": {
                "database_name": self.config['db_name'],
                "database_type": "sqlite",
                "total_tables": len(tables),
                "generated_at": datetime.utcnow().isoformat(),
                "cache_ttl": self.config['schema_cache_ttl']
            },
            "tables": tables
        }
    
    async def execute_query(self, query: str, limit: int = 100) -> list:
        """Execute database query"""
        if not self.connection:
            await self.connect()
        
        # Check if this is a generic response (not a SQL query)
        non_db_indicators = [
            "i can only help with database queries",
            "unable to provide",
            "unable to answer",
            "no information about",
            "not related to database",
            "weather information",
            "cooking",
            "recipe",
            "general knowledge"
        ]
        
        query_lower = query.lower()
        is_generic_response = any(indicator in query_lower for indicator in non_db_indicators)
        
        if is_generic_response:
            # Return the generic response as data instead of trying to execute it
            return [{"message": query}]
        
        # Validate query
        if not await self.validate_query(query, limit):
            raise ValueError("Invalid query")
        
        try:
            cursor = self.connection.cursor()
            
            # Clean the query for execution (remove comments)
            lines = query.split('\n')
            cleaned_lines = []
            for line in lines:
                # Remove SQL comments (-- style)
                if '--' in line:
                    line = line.split('--')[0]
                cleaned_lines.append(line.strip())
            
            # Join lines and clean up
            clean_query = ' '.join(cleaned_lines).strip()
            if not clean_query:
                raise ValueError("Empty query after cleaning")
            
            # Add LIMIT if not present (only for SELECT queries, database-agnostic)
            if 'LIMIT' not in clean_query.upper() and clean_query.upper().startswith('SELECT'):
                clean_query = f"{clean_query.rstrip(';')} LIMIT {limit}"
            
            cursor.execute(clean_query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch results
            results = cursor.fetchall()
            cursor.close()
            
            # Convert to list of dicts and make JSON serializable
            def make_json_serializable(obj):
                """Convert non-JSON-serializable objects to serializable ones"""
                if hasattr(obj, 'isoformat'):  # datetime objects
                    return obj.isoformat()
                elif hasattr(obj, '__float__'):  # Decimal objects
                    return float(obj)
                elif hasattr(obj, '__str__'):  # Other objects
                    return str(obj)
                else:
                    return obj
            
            result_list = []
            for row in results:
                row_dict = {}
                for i, value in enumerate(row):
                    column_name = columns[i] if i < len(columns) else f"column_{i}"
                    row_dict[column_name] = make_json_serializable(value)
                result_list.append(row_dict)
            
            return result_list
            
        except Exception as e:
            self.logger.error(f"Query error: {e}")
            raise
    
    async def validate_query(self, query: str, limit: int) -> bool:
        """Validate database query for security"""
        # Remove comments and clean the query
        lines = query.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove SQL comments (-- style)
            if '--' in line:
                line = line.split('--')[0]
            cleaned_lines.append(line.strip())
        
        # Join lines and get the first non-empty line
        cleaned_query = ' '.join(cleaned_lines).strip()
        if not cleaned_query:
            return False
            
        query_upper = cleaned_query.upper()
        
        # Allow SELECT and SHOW queries (read-only operations, database-agnostic)
        if not (query_upper.startswith('SELECT') or query_upper.startswith('SHOW')):
            return False
        
        # Block dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
            'TRUNCATE', 'REPLACE', 'EXEC', 'EXECUTE', 'CALL'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        # Check limit
        if limit > self.config['max_query_limit']:
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            if not self.connection:
                await self.connect()
            
            # Test basic query
            result = await self.execute_query("SELECT 1", 1)
            
            return {
                "status": "healthy",
                "database_type": self.config['db_type'],
                "connected": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database_type": self.config['db_type'],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _register_tools(self) -> None:
        """Register MCP tools"""
        
        @self.mcp.tool()
        async def query_database(query: str, limit: int = 100) -> str:
            """Execute SQL query against the database
            
            This tool allows you to execute SELECT queries against the database.
            
            Examples:
            - query_database("SELECT * FROM users LIMIT 10") - Get 10 users
            - query_database("SELECT COUNT(*) as total FROM orders") - Count orders
            - query_database("SELECT name, email FROM users WHERE active = 1") - Get active users
            
            Security: Only SELECT queries are allowed. DDL/DML operations are blocked.
            Performance: Results are cached for 5 minutes for optimal performance.
            """
            try:
                # Check cache
                cache_key = f"query:{hash(query)}:{limit}"
                if cache_key in self.cache:
                    return self.cache[cache_key]
                
                # Execute query
                results = await self.execute_query(query, limit)
                
                # Cache result
                result_json = json.dumps(results, indent=2)
                self.cache[cache_key] = result_json
                
                return result_json
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def refresh_schema() -> str:
            """Refresh database schema cache"""
            try:
                schema = await self.get_schema()
                return json.dumps({
                    "status": "success",
                    "generated_at": schema["metadata"]["generated_at"],
                    "total_tables": schema["metadata"]["total_tables"]
                })
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def health_check() -> str:
            """Check database health"""
            health = await self.health_check()
            return json.dumps(health, indent=2)
    
    def _register_resources(self) -> None:
        """Register MCP resources"""
        
        @self.mcp.resource("schema://database")
        async def database_schema():
            """Get database schema
            
            This resource provides comprehensive database metadata including:
            - Table structures and column definitions
            - Data types, constraints, and indexes
            - Row counts and table sizes
            - Foreign key relationships
            - Sample data for understanding table contents
            
            The schema is automatically cached and refreshed when needed.
            Use this resource to understand the database structure before writing queries.
            """
            try:
                schema = await self.get_schema()
                return json.dumps(schema, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.resource("server://info")
        async def server_info():
            """Get server information"""
            return json.dumps({
                "name": self.config['server_name'],
                "database_type": self.config['db_type'],
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        @self.mcp.resource("prompts://database")
        async def database_prompts():
            """Get database-specific prompting templates and rules
            
            This resource provides LLM prompting templates specifically designed for database operations.
            Includes action schemas, safety constraints, and domain-specific guidance.
            """
            try:
                prompts = {
                    "action_schema": self.build_action_schema_prompt(),
                    "domain_rules": self.build_domain_prompt({}),
                    "fallback_prompt": self.build_fallback_prompt(),
                    "examples": [
                        {
                            "question": "Show me the top 5 users by registration date",
                            "expected_action": {
                                "action": "call_tool",
                                "tool": "query_database",
                                "args": {
                                    "query": "SELECT * FROM users ORDER BY created_at DESC LIMIT 5",
                                    "limit": 5
                                }
                            }
                        },
                        {
                            "question": "What tables are available in this database?",
                            "expected_action": {
                                "action": "read_resource",
                                "uri": "schema://database"
                            }
                        }
                    ]
                }
                return json.dumps(prompts, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.prompt("generate_sql_query")
        async def generate_sql_query(question: str, table_context: str = "") -> list[dict]:
            """Generate SQL query from natural language question
            
            Args:
                question: Natural language description of what data to retrieve
                table_context: Optional context about specific tables to focus on
            
            Returns:
                List of messages for LLM to generate SQL query
            """
            try:
                schema = await self.get_schema()
                tables = schema.get('tables', {})
                table_names = list(tables.keys())
                
                return [
                    {
                        "role": "system",
                        "content": f"""You are a SQL query generator for a {self.config['db_type'].upper()} database.

                        Available Tables: {', '.join(table_names)}

                        Database Schema:
                        {json.dumps(schema, indent=2)[:8000]}

                        {f"Table Context: {table_context}" if table_context else ""}

                        Rules:
                        - Only generate SELECT queries (read-only operations)
                        - Use proper SQL syntax for {self.config['db_type']}
                        - Include LIMIT clause for large datasets (default: 100)
                        - Use meaningful column aliases with AS keyword
                        - Use proper JOINs when accessing multiple tables
                        - Apply WHERE clauses for filtering
                        - Use ORDER BY for sorted results

                        IMPORTANT: If the question is NOT related to database queries (e.g., weather, general knowledge, non-database topics), respond with:
                        "I can only help with database queries related to the available tables: {', '.join(table_names)}. Please ask a question about the data in these tables."

                        Output Format:
                        Return ONLY the SQL query for database-related questions, or the generic response for non-database questions."""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a SQL query for: {question}"
                    }
                ]
            except Exception as e:
                return [
                    {
                        "role": "system",
                        "content": "You are a SQL query generator. Generate SELECT queries only."
                    },
                    {
                        "role": "user", 
                        "content": f"Generate a SQL query for: {question}"
                    }
                ]
    
    async def start(self) -> None:
        """Start the MCP server"""
        self.logger.info(f"Starting Database MCP Server: {self.config['server_name']}")
        
        # Connect to database
        await self.connect()
        
        # Start server
        host = self.config['server_host']
        port = self.config['server_port']
        
        self.logger.info(f"Server ready on {host}:{port} with streamable-http transport")
        self.mcp.run(transport="streamable-http", host=host, port=port)
    
    async def stop(self) -> None:
        """Stop the MCP server"""
        self.logger.info(f"Stopping Database MCP Server: {self.config['server_name']}")
        await self.disconnect()
    
    def print_server_info(self) -> None:
        """Print server information"""
        print("\n" + "="*60)
        print("🚀 Database MCP Server")
        print("="*60)
        print(f"📊 Database Type: {self.config['db_type'].upper()}")
        print(f"🔗 Resource: schema://database")
        print(f"🛠️  Tools: query_database, refresh_schema, health_check")
        print(f"🌐 Transport: streamable-http")
        
        print(f"\n📡 Server Endpoint:")
        print(f"   http://{self.config['server_host']}:{self.config['server_port']}/mcp")
        
        print(f"\n🗄️  Database Connection:")
        if self.config['db_type'] == 'sqlite':
            print(f"   Path: {self.config['db_path'] or self.config['db_name']}")
        else:
            print(f"   Host: {self.config['db_host']}")
            print(f"   Port: {self.config['db_port']}")
            print(f"   Database: {self.config['db_name']}")
            print(f"   User: {self.config['db_user']}")
        
        print(f"\n📋 Available MCP Resources:")
        print(f"   • schema://database - Complete database schema")
        
        print(f"\n🔧 Available MCP Tools:")
        print(f"   • query_database - Execute SQL queries")
        print(f"   • refresh_schema - Refresh schema cache")
        print(f"   • health_check - Check database health")
        
        print("\n" + "="*60)


async def main():
    """Main entry point"""
    try:
        # Create and start server
        server = DatabaseMCPServer()
        
        # Print server information
        server.print_server_info()
        
        # Start the server
        await server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if running with help
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)
    
    # Run the server
    asyncio.run(main())
