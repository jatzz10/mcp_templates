#!/usr/bin/env python3
"""
REST API MCP Server

A complete, production-ready MCP server that connects to REST APIs.

Features:
- Multiple authentication methods (Bearer, Basic, API Key)
- Automatic endpoint discovery
- Rate limiting and retry logic
- Response caching
- Static data resources (API endpoints)
- Health monitoring
- Configurable via environment variables

Usage:
    python mcp_server.py

Environment Variables:
    API_BASE_URL=https://api.example.com
    API_AUTH_TYPE=bearer
    API_AUTH_TOKEN=your_token
    API_TIMEOUT=30
    API_RATE_LIMIT=100
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

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class RestAPIMCPServer:
    """
    REST API MCP Server implementation.
    
    This server provides:
    - API endpoints as MCP resource (endpoints://api)
    - API query tool (query_api)
    - Endpoint refresh tool (refresh_endpoints)
    - Health monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_config()
        self.mcp = FastMCP(name=self.config.get('server_name', 'rest-api-mcp-server'))
        self.session = None
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
        self._rate_limit_tracker = []
        
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("rest_api_mcp_server")
        
        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'server_name': os.getenv('SERVER_NAME', 'rest-api-mcp-server'),
            'server_host': os.getenv('SERVER_HOST', '127.0.0.1'),
            'server_port': int(os.getenv('SERVER_PORT', '8000')),
            'api_base_url': os.getenv('API_BASE_URL', 'https://api.example.com'),
            'api_auth_type': os.getenv('API_AUTH_TYPE', 'none'),
            'api_auth_token': os.getenv('API_AUTH_TOKEN', ''),
            'api_username': os.getenv('API_USERNAME', ''),
            'api_password': os.getenv('API_PASSWORD', ''),
            'api_timeout': int(os.getenv('API_TIMEOUT', '30')),
            'api_rate_limit': int(os.getenv('API_RATE_LIMIT', '100')),
            'api_retry_attempts': int(os.getenv('API_RETRY_ATTEMPTS', '3')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'endpoints_cache_ttl': int(os.getenv('ENDPOINTS_CACHE_TTL', '3600')),
            'query_cache_ttl': int(os.getenv('QUERY_CACHE_TTL', '300')),
            'max_query_limit': int(os.getenv('MAX_QUERY_LIMIT', '1000'))
        }
    
    async def connect(self) -> bool:
        """Initialize HTTP session"""
        try:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=self.config['api_timeout'])
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._get_auth_headers()
            )
            
            self.logger.info(f"Connected to REST API: {self.config['api_base_url']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to REST API: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close HTTP session"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            self.logger.info("Disconnected from REST API")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from REST API: {e}")
            return False
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {'Content-Type': 'application/json'}
        
        auth_type = self.config['api_auth_type'].lower()
        if auth_type == 'bearer' and self.config['api_auth_token']:
            headers['Authorization'] = f"Bearer {self.config['api_auth_token']}"
        elif auth_type == 'api_key' and self.config['api_auth_token']:
            headers['X-API-Key'] = self.config['api_auth_token']
        
        return headers
    
    def _get_auth(self) -> Optional[aiohttp.BasicAuth]:
        """Get basic auth if configured"""
        auth_type = self.config['api_auth_type'].lower()
        if auth_type == 'basic' and self.config['api_username'] and self.config['api_password']:
            return aiohttp.BasicAuth(self.config['api_username'], self.config['api_password'])
        return None
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retries"""
        if not self.session:
            await self.connect()
        
        url = f"{self.config['api_base_url'].rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Rate limiting
        await self._check_rate_limit()
        
        # Add auth
        auth = self._get_auth()
        if auth:
            kwargs['auth'] = auth
        
        # Retry logic
        last_exception = None
        for attempt in range(self.config['api_retry_attempts']):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            except Exception as e:
                last_exception = e
                if attempt < self.config['api_retry_attempts'] - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise last_exception
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        current_time = datetime.utcnow()
        
        # Remove old requests (older than 1 minute)
        self._rate_limit_tracker = [
            req_time for req_time in self._rate_limit_tracker
            if (current_time - req_time).total_seconds() < 60
        ]
        
        # Check if we're at the limit
        if len(self._rate_limit_tracker) >= self.config['api_rate_limit']:
            sleep_time = 60 - (current_time - self._rate_limit_tracker[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Add current request
        self._rate_limit_tracker.append(current_time)
    
    async def get_endpoints(self) -> Dict[str, Any]:
        """Generate API endpoints information"""
        if not self.session:
            await self.connect()
        
        try:
            # Try to get endpoints from discovery endpoint
            try:
                discovery_data = await self._make_request('GET', '/discovery')
                endpoints = discovery_data.get('endpoints', [])
            except Exception:
                # Fallback: create basic schema from common endpoints
                endpoints = await self._discover_common_endpoints()
            
            return {
                "metadata": {
                    "api_name": self.config['server_name'],
                    "base_url": self.config['api_base_url'],
                    "total_endpoints": len(endpoints),
                    "generated_at": datetime.utcnow().isoformat(),
                    "cache_ttl": self.config['endpoints_cache_ttl'],
                    "auth_type": self.config['api_auth_type']
                },
                "endpoints": endpoints,
                "authentication": {
                    "type": self.config['api_auth_type'],
                    "required": self.config['api_auth_type'] != 'none'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating API endpoints: {e}")
            raise
    
    async def _discover_common_endpoints(self) -> list:
        """Discover common REST API endpoints"""
        common_paths = [
            '/users', '/products', '/orders', '/items', '/data',
            '/api/v1/users', '/api/v1/products', '/api/v1/orders'
        ]
        
        discovered_endpoints = []
        
        for path in common_paths:
            try:
                response = await self._make_request('GET', path)
                if isinstance(response, (list, dict)):
                    discovered_endpoints.append({
                        "path": path,
                        "method": "GET",
                        "description": f"Get {path.split('/')[-1]} data",
                        "response_type": "array" if isinstance(response, list) else "object",
                        "sample_response": response[:3] if isinstance(response, list) else response
                    })
            except Exception:
                continue
        
        return discovered_endpoints
    
    async def execute_query(self, endpoint: str, method: str = 'GET', params: dict = None, limit: int = 100) -> list:
        """Execute API query"""
        if not self.session:
            await self.connect()
        
        try:
            # Check for generic LLM responses (non-API related queries)
            if endpoint and any(phrase in endpoint.lower() for phrase in [
                "i can only help with", "i can only assist with", "i can only provide",
                "i'm designed to help with", "i'm designed to assist with"
            ]):
                return [{"message": endpoint, "type": "generic_response"}]
            
            # Validate query
            if not await self.validate_query(endpoint, method, limit):
                raise ValueError("Invalid query parameters")
            
            # Add limit parameter if not present
            if params is None:
                params = {}
            if 'limit' not in params and limit < 1000:
                params['limit'] = limit
            
            response = await self._make_request(method, endpoint, params=params)
            
            # Ensure response is a list
            if isinstance(response, dict):
                # Try to find array data in common keys
                for key in ['data', 'items', 'results', 'records']:
                    if key in response and isinstance(response[key], list):
                        return response[key][:limit]
                # If no array found, wrap the dict
                return [response]
            elif isinstance(response, list):
                return response[:limit]
            else:
                return [{"data": response}]
                
        except Exception as e:
            self.logger.error(f"API query error: {e}")
            raise
    
    async def validate_query(self, endpoint: str, method: str, limit: int) -> bool:
        """Validate API query parameters"""
        # Basic validation
        if not endpoint:
            return False
        
        # Only allow safe methods
        if method.upper() not in ['GET', 'HEAD', 'OPTIONS']:
            return False
        
        # Check limit
        if limit > self.config['max_query_limit']:
            return False
        
        # Validate endpoint format
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        # Basic path validation (prevent directory traversal)
        if '..' in endpoint or '//' in endpoint:
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform API health check"""
        try:
            if not self.session:
                await self.connect()
            
            # Try a simple request to check connectivity
            await self._make_request('GET', '/health')
            
            return {
                "status": "healthy",
                "api_base_url": self.config['api_base_url'],
                "auth_type": self.config['api_auth_type'],
                "connected": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_base_url": self.config['api_base_url'],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _register_tools(self) -> None:
        """Register MCP tools"""
        
        @self.mcp.tool()
        async def query_api(endpoint: str, method: str = 'GET', params: str = '{}', limit: int = 100) -> str:
            """Execute API query
            
            This tool allows you to query REST APIs using various HTTP methods.
            
            Examples:
            - query_api("/users", "GET", "{}", 10) - Get 10 users
            - query_api("/orders", "GET", '{"status": "completed"}', 50) - Get completed orders
            - query_api("/products", "HEAD", "{}", 0) - Check if products endpoint exists
            
            Supported Methods: GET, HEAD, OPTIONS (read-only for security)
            Performance: Results are cached for 5 minutes for optimal performance.
            """
            try:
                # Check cache
                cache_key = f"api:{endpoint}:{method}:{hash(str(params))}:{limit}"
                if cache_key in self.cache:
                    return self.cache[cache_key]
                
                # Parse params
                try:
                    params_dict = json.loads(params) if params else {}
                except json.JSONDecodeError:
                    params_dict = {}
                
                # Execute query
                results = await self.execute_query(endpoint, method, params_dict, limit)
                
                # Cache result
                result_json = json.dumps(results, indent=2)
                self.cache[cache_key] = result_json
                
                return result_json
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def refresh_endpoints() -> str:
            """Refresh API endpoints cache"""
            try:
                endpoints = await self.get_endpoints()
                return json.dumps({
                    "status": "success",
                    "generated_at": endpoints["metadata"]["generated_at"],
                    "total_endpoints": endpoints["metadata"]["total_endpoints"]
                })
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.tool()
        async def health_check() -> str:
            """Check API health"""
            health = await self.health_check()
            return json.dumps(health, indent=2)
    
    def _register_resources(self) -> None:
        """Register MCP resources"""
        
        @self.mcp.resource("endpoints://api")
        async def api_endpoints():
            """Get API endpoints
            
            This resource provides comprehensive API endpoint documentation including:
            - Available endpoints and their HTTP methods
            - Request/response schemas and examples
            - Authentication requirements
            - Rate limiting information
            - Parameter descriptions and types
            
            The endpoints are automatically discovered and cached for performance.
            Use this resource to understand the API structure before making queries.
            """
            try:
                endpoints = await self.get_endpoints()
                return json.dumps(endpoints, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.resource("server://info")
        async def server_info():
            """Get server information"""
            return json.dumps({
                "name": self.config['server_name'],
                "api_base_url": self.config['api_base_url'],
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        @self.mcp.resource("prompts://rest-api")
        async def rest_api_prompts():
            """Get REST API-specific prompting templates and rules
            
            This resource provides LLM prompting templates specifically designed for REST API operations.
            Includes action schemas, safety constraints, and API-specific guidance.
            """
            try:
                prompts = {
                    "action_schema": self.build_action_schema_prompt(),
                    "domain_rules": self.build_domain_prompt({}),
                    "fallback_prompt": self.build_fallback_prompt(),
                    "examples": [
                        {
                            "question": "Get the first 10 users from the API",
                            "expected_action": {
                                "action": "call_tool",
                                "tool": "query_api",
                                "args": {
                                    "endpoint": "/users",
                                    "method": "GET",
                                    "params": "{}",
                                    "limit": 10
                                }
                            }
                        },
                        {
                            "question": "What API endpoints are available?",
                            "expected_action": {
                                "action": "read_resource",
                                "uri": "endpoints://api"
                            }
                        }
                    ]
                }
                return json.dumps(prompts, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.prompt("generate_rest_api_query")
        async def generate_rest_api_query(user_question: str) -> list[dict]:
            """Generate REST API query from natural language question
            
            Args:
                user_question: Natural language question about REST API operations
            
            Returns:
                List of messages for LLM to generate REST API query
            """
            try:
                endpoints = await self.get_endpoints()
                base_url = self.config['api_base_url']
                auth_type = self.config['api_auth_type']
                
                return [
                    {
                        "role": "system",
                        "content": f"""You are a REST API assistant that can help with API queries and endpoint operations.

API Base URL: {base_url}
Authentication: {auth_type}

API Endpoints and Documentation:
{json.dumps(endpoints, indent=2)[:6000]}

Available Operations:
- GET: Retrieve data from endpoints
- HEAD: Check if resource exists without getting content
- OPTIONS: Discover available methods for an endpoint

Rules:
- Only read operations are allowed (no POST, PUT, DELETE, PATCH)
- Use proper HTTP methods and respect API constraints
- Include appropriate query parameters for filtering
- Respect rate limits and use pagination when needed
- Handle authentication headers appropriately

For non-API related questions (like weather, general knowledge, etc.), respond with:
"I can only help with REST API operations. Please ask me about API endpoints, data queries, or API documentation."

Output Format:
Return a JSON object with:
{{
    "endpoint": "/path/to/endpoint",
    "method": "GET",
    "params": {{"key": "value"}},
    "limit": 100
}}

Or for non-API questions, return:
{{
    "endpoint": "I can only help with REST API operations. Please ask me about API endpoints, data queries, or API documentation.",
    "method": "",
    "params": {{}},
    "limit": 0
}}"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a REST API query for: {user_question}"
                    }
                ]
            except Exception as e:
                return [
                    {
                        "role": "system",
                        "content": "You are a REST API assistant. Generate API queries for data retrieval operations."
                    },
                    {
                        "role": "user",
                        "content": f"Generate a REST API query for: {user_question}"
                    }
                ]

        @self.mcp.prompt("generate_api_request")
        async def generate_api_request(endpoint_description: str, method: str = "GET") -> list[dict]:
            """Generate API request from description
            
            Args:
                endpoint_description: Natural language description of what data to retrieve
                method: HTTP method to use (GET, HEAD, OPTIONS only)
            
            Returns:
                List of messages for LLM to generate API request
            """
            try:
                endpoints = await self.get_endpoints()
                base_url = self.config['api_base_url']
                
                return [
                    {
                        "role": "system",
                        "content": f"""You are an API request generator for {base_url}.

Available Endpoints:
{json.dumps(endpoints, indent=2)[:6000]}

Authentication: {self.config['api_auth_type']}
Rate Limit: {self.config['api_rate_limit']} requests per minute

Rules:
- Only use GET, HEAD, OPTIONS methods (read-only operations)
- Include proper query parameters for filtering
- Respect rate limits and use pagination when needed
- Handle authentication headers appropriately
- Include proper Content-Type headers
- Use appropriate timeout settings

Output Format:
Return a JSON object with:
{{
    "endpoint": "/path/to/endpoint",
    "method": "GET",
    "params": {{"key": "value"}},
    "headers": {{"Header": "Value"}},
    "limit": 100
}}"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate a {method} API request for: {endpoint_description}"
                    }
                ]
            except Exception as e:
                return [
                    {
                        "role": "system",
                        "content": "You are an API request generator. Generate GET requests only."
                    },
                    {
                        "role": "user",
                        "content": f"Generate a {method} API request for: {endpoint_description}"
                    }
                ]
    
    # Prompting Methods for LLM Integration
    def build_action_schema_prompt(self) -> str:
        """Get the strict JSON action schema for REST API operations"""
        return (
            "You must respond with a single-line minified JSON object with this exact structure:\n\n"
            "For tool calls:\n"
            "{\"action\": \"call_tool\", \"tool\": \"query_api\", \"args\": {\"endpoint\": \"/path\", \"method\": \"GET\", \"params\": \"{}\", \"limit\": 100}}\n\n"
            "For resource access:\n"
            "{\"action\": \"read_resource\", \"uri\": \"endpoints://api\"}\n\n"
            "Valid tools: query_api, refresh_endpoints, health_check\n"
            "Valid resources: endpoints://api, server://info, prompts://rest-api\n"
            "Valid methods: GET, HEAD, OPTIONS (read-only). No POST, PUT, DELETE, PATCH."
        )
    
    def build_domain_prompt(self, context: Dict[str, Any] = None) -> str:
        """Get REST API-specific domain rules and guidance"""
        context = context or {}
        api_base_url = self.config.get('api_base_url', 'https://api.example.com')
        auth_type = self.config.get('api_auth_type', 'none')
        
        return (
            f"REST API Domain Rules for {api_base_url}:\n\n"
            
            "SAFETY CONSTRAINTS:\n"
            "- Only read operations are allowed (GET, HEAD, OPTIONS)\n"
            "- No write operations (POST, PUT, DELETE, PATCH)\n"
            "- No authentication token manipulation\n"
            "- No system configuration changes\n"
            "- Always use appropriate rate limiting\n"
            "- Respect API quotas and limits\n\n"
            
            "HTTP METHOD GUIDELINES:\n"
            "- GET: Retrieve data from endpoints\n"
            "- HEAD: Check if resource exists without getting content\n"
            "- OPTIONS: Discover available methods for an endpoint\n"
            "- Never use POST, PUT, DELETE, PATCH for data modification\n\n"
            
            "ENDPOINT PATTERNS:\n"
            "- Collection endpoints: /users, /products, /orders\n"
            "- Resource endpoints: /users/{id}, /products/{id}\n"
            "- Search endpoints: /search?q=term, /users?name=john\n"
            "- Pagination: /users?page=1&limit=10\n"
            "- Filtering: /users?status=active&role=admin\n\n"
            
            "QUERY PARAMETERS:\n"
            "- Use JSON format for params: '{\"key\": \"value\"}'\n"
            "- Common params: limit, offset, page, sort, filter\n"
            "- URL encoding handled automatically\n"
            "- Boolean values: true/false (not 1/0)\n\n"
            
            f"AUTHENTICATION:\n"
            f"- Type: {auth_type}\n"
            f"- Handled automatically by the server\n"
            f"- No need to include auth headers in requests\n\n"
            
            "ERROR HANDLING:\n"
            "- If endpoint doesn't exist, suggest checking available endpoints\n"
            "- If parameters are invalid, suggest valid parameter formats\n"
            "- If rate limited, suggest reducing request frequency\n"
            "- Always validate endpoint paths against available endpoints"
        )
    
    def build_fallback_prompt(self) -> str:
        """Get fallback prompt for when LLM response isn't valid JSON"""
        return (
            "If the LLM response is not valid JSON or doesn't follow the action schema:\n\n"
            "1. Try to extract an endpoint path from the response\n"
            "2. If no valid endpoint found, ask user to rephrase\n"
            "3. Suggest using /endpoints to check available API endpoints\n"
            "4. Provide example API calls based on available endpoints\n\n"
            "Common fallback patterns:\n"
            "- 'GET /users' for user data\n"
            "- 'GET /products' for product listings\n"
            "- 'HEAD /health' for health checks\n"
            "- 'OPTIONS /endpoint' for method discovery\n"
            "- Use limit parameter for large datasets"
        )

    async def start(self) -> None:
        """Start the MCP server"""
        self.logger.info(f"Starting REST API MCP Server: {self.config['server_name']}")
        
        # Connect to API
        await self.connect()
        
        # Start server
        host = self.config['server_host']
        port = self.config['server_port']
        
        self.logger.info(f"Server ready on {host}:{port} with streamable-http transport")
        self.mcp.run(transport="streamable-http", host=host, port=port)
    
    async def stop(self) -> None:
        """Stop the MCP server"""
        self.logger.info(f"Stopping REST API MCP Server: {self.config['server_name']}")
        await self.disconnect()
    
    def print_server_info(self) -> None:
        """Print server information"""
        print("\n" + "="*60)
        print("🚀 REST API MCP Server")
        print("="*60)
        print(f"📊 API Base URL: {self.config['api_base_url']}")
        print(f"🔗 Resource: endpoints://api")
        print(f"🛠️  Tools: query_api, refresh_endpoints, health_check")
        print(f"🌐 Transport: streamable-http")
        
        print(f"\n📡 Server Endpoint:")
        print(f"   http://{self.config['server_host']}:{self.config['server_port']}/mcp")
        
        print(f"\n🌐 API Connection:")
        print(f"   Base URL: {self.config['api_base_url']}")
        print(f"   Auth Type: {self.config['api_auth_type']}")
        print(f"   Timeout: {self.config['api_timeout']}s")
        print(f"   Rate Limit: {self.config['api_rate_limit']} req/min")
        
        print(f"\n📋 Available MCP Resources:")
        print(f"   • endpoints://api - Complete API endpoint documentation")
        
        print(f"\n🔧 Available MCP Tools:")
        print(f"   • query_api - Execute API queries")
        print(f"   • refresh_endpoints - Refresh endpoint cache")
        print(f"   • health_check - Check API health")
        
        print("\n" + "="*60)


async def main():
    """Main entry point"""
    try:
        # Create and start server
        server = RestAPIMCPServer()
        
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
