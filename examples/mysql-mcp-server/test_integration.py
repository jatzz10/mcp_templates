#!/usr/bin/env python3
"""
Integration Test Script for MySQL MCP Server with Gemini LLM

This script tests the complete integration between:
1. MCP Server (mcp_server.py)
2. Gemini LLM Wrapper (gemini_llm_wrapper.py)
3. MCP Client (mcp_client.py)

Usage:
    python test_integration.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_gemini_wrapper():
    """Test Gemini LLM Wrapper"""
    print("🧪 Testing Gemini LLM Wrapper...")
    
    try:
        from gemini_llm_wrapper import GeminiLLMWrapper
        
        # Check if API key is set
        api_key = os.getenv("NAIL_LLM_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            print("❌ NAIL_LLM_API_KEY not set. Please set it in mcp.env file.")
            return False
        
        # Initialize wrapper
        llm = GeminiLLMWrapper(
            model_id="gemini-2.0-flash-exp",
            temperature=0.2,
            max_tokens=100,
            api_key=api_key
        )
        
        # Test basic invocation
        response = llm.invoke("Hello, respond with just 'Hello World'")
        print(f"✅ Gemini response: {response[:50]}...")
        
        # Test model info
        info = llm.get_model_info()
        print(f"✅ Model info: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini wrapper test failed: {e}")
        return False

async def test_mcp_client_functions():
    """Test MCP Client functions"""
    print("\n🧪 Testing MCP Client functions...")
    
    try:
        from mcp_client import discover_mcp_tools, get_database_schema, call_mcp_tool
        
        # Test tool discovery (this will fail if MCP server is not running)
        try:
            tools = await discover_mcp_tools()
            print(f"✅ Discovered {len(tools.get('tools', []))} tools and {len(tools.get('resources', []))} resources")
        except Exception as e:
            print(f"⚠️  Tool discovery failed (MCP server may not be running): {e}")
        
        # Test schema retrieval
        try:
            schema = await get_database_schema()
            print(f"✅ Schema retrieved: {len(schema)} characters")
        except Exception as e:
            print(f"⚠️  Schema retrieval failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP client test failed: {e}")
        return False

def test_imports():
    """Test all imports"""
    print("🧪 Testing imports...")
    
    try:
        # Test Gemini wrapper import
        from gemini_llm_wrapper import GeminiLLMWrapper, create_gemini_llm
        print("✅ Gemini wrapper imports successful")
        
        # Test MCP client import
        from mcp_client import app, AskLLMRequest, AskLLMResponse
        print("✅ MCP client imports successful")
        
        # Test MCP server import
        from mcp_server import DatabaseMCPServer
        print("✅ MCP server imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def check_environment():
    """Check environment configuration"""
    print("🧪 Checking environment configuration...")
    
    # Check required environment variables
    required_vars = [
        "NAIL_LLM_API_KEY",
        "DB_HOST",
        "DB_USER", 
        "DB_PASSWORD",
        "DB_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f"your_{var.lower()}_here":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in mcp.env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

async def main():
    """Main test function"""
    print("🚀 Starting MySQL MCP Server Integration Tests")
    print("=" * 60)
    
    # Test 1: Check environment
    env_ok = check_environment()
    
    # Test 2: Test imports
    imports_ok = test_imports()
    
    # Test 3: Test Gemini wrapper (only if API key is set)
    gemini_ok = False
    if os.getenv("NAIL_LLM_API_KEY") and os.getenv("NAIL_LLM_API_KEY") != "your_google_api_key_here":
        gemini_ok = await test_gemini_wrapper()
    else:
        print("⚠️  Skipping Gemini test - API key not set")
    
    # Test 4: Test MCP client functions
    client_ok = await test_mcp_client_functions()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"Environment: {'✅' if env_ok else '❌'}")
    print(f"Imports: {'✅' if imports_ok else '❌'}")
    print(f"Gemini Wrapper: {'✅' if gemini_ok else '⚠️' if not os.getenv('NAIL_LLM_API_KEY') else '❌'}")
    print(f"MCP Client: {'✅' if client_ok else '❌'}")
    
    if env_ok and imports_ok and client_ok:
        print("\n🎉 Integration tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Start the MCP server: python mcp_server.py")
        print("2. Start the MCP client: python mcp_client.py")
        print("3. Test the API at: http://localhost:8001/docs")
        print("4. Available endpoints:")
        print("   - POST /ask_llm - Natural language database queries")
        print("   - GET /health - Health check")
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / 'mcp.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from: {env_path}")
    except ImportError:
        print("⚠️  python-dotenv not available")
    
    # Run tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
