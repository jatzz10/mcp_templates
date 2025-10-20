"""
Database Operations module

This module handles database connections and operations.
"""

import logging
from typing import Dict, Any, Optional, List
import sqlalchemy
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from models.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Handles database connections and operations"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[Engine] = None
        self.connection = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            connection_string = self.config.get_connection_string()
            self.engine = create_engine(connection_string, echo=False)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Connected to {self.config.db_type} database: {self.config.db_name}")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, limit: int = 1000) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        try:
            with self.engine.connect() as conn:
                # Add LIMIT clause if not present and limit is specified
                if limit and limit > 0 and "LIMIT" not in query.upper():
                    query = f"{query.rstrip(';')} LIMIT {limit}"
                
                result = conn.execute(text(query))
                
                # Get column names
                columns = list(result.keys())
                
                # Fetch all rows
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "data": data,
                    "row_count": len(data),
                    "columns": columns,
                    "query": query
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            schema_info = {
                "tables": {},
                "database_type": self.config.db_type,
                "database_name": self.config.db_name
            }
            
            for table_name, table in metadata.tables.items():
                columns = []
                for column in table.columns:
                    columns.append({
                        "name": column.name,
                        "type": str(column.type),
                        "nullable": column.nullable,
                        "primary_key": column.primary_key
                    })
                
                schema_info["tables"][table_name] = {
                    "columns": columns,
                    "primary_keys": [col.name for col in table.primary_key.columns]
                }
            
            return schema_info
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get schema info: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        if not self.engine:
            return {"status": "disconnected", "error": "No database connection"}
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    return {"status": "healthy", "database": self.config.db_name}
                else:
                    return {"status": "unhealthy", "error": "Health check query failed"}
                    
        except SQLAlchemyError as e:
            return {"status": "unhealthy", "error": str(e)}
