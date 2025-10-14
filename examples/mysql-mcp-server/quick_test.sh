#!/bin/bash

# Quick Test Commands for MySQL MCP Server
# Essential tests to verify system functionality

echo "🚀 Quick MySQL MCP Server Tests"
echo "================================"

# Test 1: Basic Database Query
echo "1. Basic user query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me the first 3 users"}' | jq

echo -e "\n"

# Test 2: Non-Database Query
echo "2. Non-database query (should return generic response)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the weather today?"}' | jq

echo -e "\n"

# Test 3: Complex Query
echo "3. Complex aggregation query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the total revenue and average order value?"}' | jq

echo -e "\n"

# Test 4: Health Check
echo "4. Health check..."
curl -X GET "http://localhost:8001/health" | jq

echo -e "\n"
echo "✅ Quick tests completed!"
