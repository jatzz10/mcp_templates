"""
Schema Manager module

This module handles database schema caching and management.
"""

import json
import logging
from typing import Dict, Any, Optional
from cachetools import TTLCache
from datetime import datetime, timezone

from models.config import DatabaseConfig
from .database_operations import DatabaseOperations

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema caching and retrieval"""
    
    def __init__(self, config: DatabaseConfig, db_ops: DatabaseOperations):
        self.config = config
        self.db_ops = db_ops
        self.cache = TTLCache(maxsize=1000, ttl=config.schema_cache_ttl)
        self._schema_cache_key = "database_schema"
    
    def get_schema(self, force_refresh: bool = False) -> str:
        """Get database schema, using cache if available"""
        if not force_refresh and self._schema_cache_key in self.cache:
            logger.debug("Returning cached schema")
            return self.cache[self._schema_cache_key]
        
        try:
            logger.info("Fetching fresh database schema")
            schema_info = self.db_ops.get_schema_info()
            
            # Format schema as readable text
            schema_text = self._format_schema(schema_info)
            
            # Cache the result
            self.cache[self._schema_cache_key] = schema_text
            
            logger.info(f"Schema cached successfully ({len(schema_text)} characters)")
            return schema_text
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            # Return cached version if available, otherwise return error message
            if self._schema_cache_key in self.cache:
                logger.warning("Returning stale cached schema due to error")
                return self.cache[self._schema_cache_key]
            else:
                return f"Error retrieving database schema: {str(e)}"
    
    def refresh_schema(self) -> str:
        """Force refresh the database schema"""
        logger.info("Force refreshing database schema")
        return self.get_schema(force_refresh=True)
    
    def _format_schema(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information as readable text"""
        lines = []
        lines.append(f"Database: {schema_info['database_name']} ({schema_info['database_type']})")
        lines.append("=" * 50)
        lines.append("")
        
        for table_name, table_info in schema_info['tables'].items():
            lines.append(f"Table: {table_name}")
            lines.append("-" * 30)
            
            # Primary keys
            if table_info['primary_keys']:
                lines.append(f"Primary Keys: {', '.join(table_info['primary_keys'])}")
            
            # Columns
            lines.append("Columns:")
            for column in table_info['columns']:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                pk_marker = " (PK)" if column['primary_key'] else ""
                lines.append(f"  - {column['name']}: {column['type']} {nullable}{pk_marker}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def get_schema_json(self) -> Dict[str, Any]:
        """Get schema as JSON for API responses"""
        try:
            schema_info = self.db_ops.get_schema_info()
            return {
                "schema": schema_info,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "cache_ttl": self.config.schema_cache_ttl
            }
        except Exception as e:
            logger.error(f"Failed to get schema JSON: {e}")
            return {
                "error": str(e),
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
    
    def clear_cache(self) -> None:
        """Clear the schema cache"""
        self.cache.clear()
        logger.info("Schema cache cleared")
