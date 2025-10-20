"""
Database Operations module

This module handles database connections and operations.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, date, time
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
                # Split query into individual statements if it contains semicolons
                if ';' in query:
                    statements = self._split_sql_statements(query)
                else:
                    statements = [query.strip()]
                
                all_data = []
                all_columns = set()
                executed_queries = []
                
                for i, statement in enumerate(statements):
                    if not statement:
                        continue
                    
                    logger.info(f"Executing statement {i+1}: {statement[:100]}...")
                    
                    # Add LIMIT clause only for SELECT statements, not for SHOW/DESCRIBE
                    if (limit and limit > 0 and 
                        "LIMIT" not in statement.upper() and 
                        statement.upper().strip().startswith("SELECT")):
                        statement = f"{statement.rstrip(';')} LIMIT {limit}"
                    
                    executed_queries.append(statement)
                    
                    try:
                        result = conn.execute(text(statement))
                        
                        # Get column names
                        columns = list(result.keys())
                        all_columns.update(columns)
                        
                        # Fetch all rows
                        rows = result.fetchall()
                        
                        logger.info(f"Statement {i+1} returned {len(rows)} rows with columns: {columns}")
                        
                        # Convert to list of dictionaries and handle serialization
                        statement_data = []
                        for row in rows:
                            row_dict = {}
                            for col, val in zip(columns, row):
                                # Convert various types for JSON serialization
                                if isinstance(val, Decimal):
                                    row_dict[col] = float(val)
                                elif isinstance(val, (datetime, date)):
                                    row_dict[col] = val.isoformat()
                                elif isinstance(val, time):
                                    row_dict[col] = val.isoformat()
                                else:
                                    row_dict[col] = val
                            statement_data.append(row_dict)
                        all_data.extend(statement_data)
                        
                        logger.info(f"Statement {i+1} data: {statement_data[:2] if statement_data else 'No data'}")
                        
                    except SQLAlchemyError as e:
                        logger.error(f"Statement {i+1} execution failed: {e}")
                        logger.error(f"Failed statement: {statement}")
                        # Continue with other statements
                        continue
                
                return {
                    "data": all_data,
                    "row_count": len(all_data),
                    "columns": list(all_columns),
                    "query": ";\n".join(executed_queries)
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _split_sql_statements(self, query: str) -> List[str]:
        """Split SQL query into individual statements, handling string literals properly"""
        statements = []
        current_statement = ""
        in_string = False
        string_char = None
        i = 0
        
        while i < len(query):
            char = query[i]
            
            if not in_string:
                if char in ["'", '"', '`']:
                    in_string = True
                    string_char = char
                    current_statement += char
                elif char == ';':
                    # End of statement
                    if current_statement.strip():
                        statements.append(current_statement.strip())
                    current_statement = ""
                else:
                    current_statement += char
            else:
                current_statement += char
                if char == string_char:
                    # Check for escaped quotes
                    if i + 1 < len(query) and query[i + 1] == string_char:
                        current_statement += query[i + 1]
                        i += 1  # Skip the next quote
                    else:
                        in_string = False
                        string_char = None
            
            i += 1
        
        # Add the last statement if it exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
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
