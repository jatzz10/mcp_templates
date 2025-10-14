# MCP Server Templates

Complete, production-ready templates for building Model Context Protocol (MCP) servers with integrated FastAPI clients and Gemini LLM support. Each template is self-contained and focused on a specific data source type.

## 🚀 Quick Start

### 1. Choose Your Template

| Template | Data Source | Resource URI | Description | FastAPI Client | LLM Support |
|----------|-------------|--------------|-------------|---------------|-------------|
| **db-mcp-server** | Database | `schema://database` | MySQL, PostgreSQL, SQLite support | ✅ | ✅ Gemini |
| **rest-api-mcp-server** | REST API | `endpoints://api` | HTTP API integration | ✅ | ✅ Gemini |
| **filesystem-mcp-server** | File System | `structure://filesystem` | File and directory access | ✅ | ✅ Gemini |
| **jira-mcp-server** | JIRA | `workflows://jira` | Project management | ✅ | ✅ Gemini |

### 2. Copy and Run

```bash
# Copy the template you need
cp -r templates/db-mcp-server/ my-database-server/
cd my-database-server/

# Configure environment
cp env.template .env
nano .env  # Set your credentials and GOOGLE_API_KEY

# Install and run
pip install -r requirements.txt

# Start MCP server
python mcp_server.py

# Start FastAPI client (in another terminal)
python mcp_client.py
```

## 📁 Template Structure

Each template is completely self-contained:

```
template-name/
├── mcp_server.py          # Complete, ready-to-run MCP server
├── mcp_client.py          # FastAPI client with /ask_llm endpoint
├── gemini_llm_wrapper.py  # Gemini LLM integration wrapper
├── requirements.txt       # All needed dependencies
├── env.template          # Environment variables template
├── README.md             # Template-specific documentation
├── test_template.py      # Template-specific tests
└── examples/             # Usage examples (optional)
```

## 🎯 Template Features

### **Self-Contained**
- ✅ **Copy and run** - No complex setup required
- ✅ **Focused dependencies** - Only what you need
- ✅ **Simple configuration** - Environment variables only
- ✅ **Complete documentation** - Everything in one place

### **Production Ready**
- ✅ **Security validation** - Query validation and path restrictions
- ✅ **Error handling** - Graceful degradation
- ✅ **Caching system** - File-based and memory caching
- ✅ **Health monitoring** - Built-in health checks
- ✅ **Logging** - Configurable logging levels

### **MCP Compliant**
- ✅ **Static data resources** - Proper resource URIs
- ✅ **MCP tools** - Query execution and cache management
- ✅ **Streamable HTTP** - Modern transport protocol
- ✅ **Standard interfaces** - Compatible with MCP clients

### **LLM Integration**
- ✅ **Gemini LLM Support** - Direct Google Generative AI integration
- ✅ **Natural Language Queries** - `/ask_llm` endpoint for all templates
- ✅ **Server-side Prompting** - Intelligent prompt generation
- ✅ **Generic Response Handling** - Graceful handling of non-domain queries
- ✅ **FastAPI Clients** - REST API endpoints for easy integration

## 📊 Template Details

### Database MCP Server (`db-mcp-server`)

**Supports:** MySQL, PostgreSQL, SQLite

**Features:**
- Database schema caching and auto-refresh
- SQL query execution with security validation
- Multiple database type support
- Connection pooling and error handling
- FastAPI client with `/ask_llm` endpoint
- Gemini LLM integration for natural language queries

**Quick Setup:**
```bash
cp -r templates/db-mcp-server/ my-db-server/
cd my-db-server/
cp env.template .env
# Edit .env with your database credentials and GOOGLE_API_KEY
pip install -r requirements.txt

# Start MCP server
python mcp_server.py

# Start FastAPI client (in another terminal)
python mcp_client.py
```

**Environment Variables:**
```bash
# Database Configuration
DB_TYPE=mysql                    # mysql, postgresql, sqlite
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=my_database

# LLM Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL_ID=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=600
```

**Test with Natural Language:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all users in the database"}'
```

### REST API MCP Server (`rest-api-mcp-server`)

**Supports:** Any REST API with authentication

**Features:**
- Multiple authentication methods (Bearer, Basic, API Key)
- Automatic endpoint discovery
- Rate limiting and retry logic
- Response caching
- FastAPI client with `/ask_llm` endpoint
- Gemini LLM integration for natural language API queries

**Quick Setup:**
```bash
cp -r templates/rest-api-mcp-server/ my-api-server/
cd my-api-server/
cp env.template .env
# Edit .env with your API credentials and GOOGLE_API_KEY
pip install -r requirements.txt

# Start MCP server
python mcp_server.py

# Start FastAPI client (in another terminal)
python mcp_client.py
```

**Environment Variables:**
```bash
# API Configuration
API_BASE_URL=https://api.example.com
API_AUTH_TYPE=bearer
API_AUTH_TOKEN=your_token

# LLM Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL_ID=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=600
```

**Test with Natural Language:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Get all users from the API"}'
```

### FileSystem MCP Server (`filesystem-mcp-server`)

**Supports:** Local file systems

**Features:**
- Directory traversal with depth limits
- File content reading and search
- Security path restrictions
- File type categorization
- FastAPI client with `/ask_llm` endpoint
- Gemini LLM integration for natural language file system queries

**Quick Setup:**
```bash
cp -r templates/filesystem-mcp-server/ my-fs-server/
cd my-fs-server/
cp env.template .env
# Edit .env with your file system path and GOOGLE_API_KEY
pip install -r requirements.txt

# Start MCP server
python mcp_server.py

# Start FastAPI client (in another terminal)
python mcp_client.py
```

**Environment Variables:**
```bash
# Filesystem Configuration
FILESYSTEM_ROOT_PATH=/path/to/directory
FILESYSTEM_MAX_DEPTH=5
FILESYSTEM_INCLUDE_HIDDEN=false

# LLM Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL_ID=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=600
```

**Test with Natural Language:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "List all Python files in the project"}'
```

### JIRA MCP Server (`jira-mcp-server`)

**Supports:** JIRA Cloud and Server

**Features:**
- Project and issue management
- Workflow and custom field access
- JQL query support
- User and permission information
- FastAPI client with `/ask_llm` endpoint
- Gemini LLM integration for natural language JIRA queries

**Quick Setup:**
```bash
cp -r templates/jira-mcp-server/ my-jira-server/
cd my-jira-server/
cp env.template .env
# Edit .env with your JIRA credentials and GOOGLE_API_KEY
pip install -r requirements.txt

# Start MCP server
python mcp_server.py

# Start FastAPI client (in another terminal)
python mcp_client.py
```

**Environment Variables:**
```bash
# JIRA Configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ

# LLM Configuration
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL_ID=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_TOKENS=600
```

**Test with Natural Language:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all open issues in the project"}'
```

## 🧪 Testing

Each template includes its own test suite:

```bash
# Test the MCP server
python test_template.py

# Test the FastAPI client
python mcp_client.py

# Test with natural language queries
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Your natural language question here"}'
```

### Test Examples

**Database Template:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all tables in the database"}'
```

**REST API Template:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Get the first 10 users from the API"}'
```

**Filesystem Template:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Find all Python files in the project"}'
```

**JIRA Template:**
```bash
curl -X POST "http://localhost:8001/ask_llm" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all high priority issues"}'
```

## 🔧 Customization

### Adding New Features

1. **Extend the server class** - Add new methods to the main server class
2. **Add new tools** - Register additional MCP tools
3. **Add new resources** - Register additional MCP resources
4. **Update configuration** - Add new environment variables

### Example: Adding Custom Tool

```python
@self.mcp.tool()
async def custom_tool(param1: str, param2: int = 100) -> str:
    """Custom tool description"""
    try:
        # Your custom logic here
        result = await self.custom_method(param1, param2)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
```

## 📚 Documentation

Each template includes:

- **README.md** - Complete setup and usage guide
- **env.template** - Environment variables template
- **mcp_server.py** - Complete MCP server implementation
- **mcp_client.py** - FastAPI client with `/ask_llm` endpoint
- **gemini_llm_wrapper.py** - Gemini LLM integration wrapper
- **test_template.py** - Test suite
- **examples/** - Usage examples

## 🆘 Support

### Common Issues

1. **Connection Failed**
   - Check credentials and network connectivity
   - Verify service is running
   - Check firewall settings

2. **Permission Denied**
   - Verify user permissions
   - Check file system access rights
   - Ensure proper authentication

3. **Configuration Error**
   - Verify environment variables
   - Check configuration file syntax
   - Validate data source settings

4. **LLM Integration Issues**
   - Ensure GOOGLE_API_KEY is set correctly
   - Check Gemini model availability
   - Verify network connectivity to Google APIs

### Getting Help

1. **Check template README** - Each template has specific documentation
2. **Review environment setup** - Ensure all required variables are set
3. **Test connectivity** - Use the test scripts to verify setup
4. **Check logs** - Enable debug logging for detailed information

## 🎉 Benefits

### **For Teams**
- ✅ **Faster adoption** - Copy and run in minutes
- ✅ **Focused learning** - Only relevant information
- ✅ **Easier maintenance** - Self-contained templates
- ✅ **Better testing** - Template-specific test suites

### **For Developers**
- ✅ **Clear structure** - Easy to understand and modify
- ✅ **Production ready** - Built-in security and error handling
- ✅ **Extensible** - Easy to add new features
- ✅ **Well documented** - Complete documentation and examples

## 🆕 What's New

### Latest Updates (v2.0)

- ✅ **Gemini LLM Integration** - Direct Google Generative AI support across all templates
- ✅ **FastAPI Clients** - REST API endpoints with `/ask_llm` for natural language queries
- ✅ **Server-side Prompting** - Intelligent prompt generation for better LLM responses
- ✅ **Generic Response Handling** - Graceful handling of non-domain specific queries
- ✅ **Modern Startup Process** - Updated FastAPI lifecycle management
- ✅ **Enhanced Error Handling** - Better JSON serialization and error recovery
- ✅ **MCP Metadata Caching** - Startup caching for improved performance
- ✅ **Comprehensive Testing** - Updated test suites with LLM integration testing

## 📄 License

These templates are provided as-is for teams to build upon. Customize and modify as needed for your specific use cases.

---

**Ready to get started?** Choose your template and follow the quick start guide! 🚀
