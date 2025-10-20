#!/bin/bash

# Database MCP Server Test Commands
# This file contains all the curl commands used to test the system

echo "🧪 Testing Database MCP Server with Natural Language Queries"
echo "=========================================================="

# Test 1: Basic Database Structure Query
echo "1. Testing database structure query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the structure of the database? Show me all tables and their columns"}' | jq

echo -e "\n"

# Test 2: Count Records Query
echo "2. Testing count records query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "How many records are in each table?"}' | jq

echo -e "\n"

# Test 3: Complex Aggregation Query
echo "3. Testing complex aggregation query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me summary statistics and aggregations from the database"}' | jq

echo -e "\n"

# Test 4: Very Complex Business Analysis Query
echo "4. Testing complex business analysis query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me a detailed analysis of the data with relationships between tables, counts, and any patterns you can find"}' | jq

echo -e "\n"

# Test 5: Vague Query
echo "5. Testing vague query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me stuff"}' | jq

echo -e "\n"

# Test 6: Non-Database Query - Weather
echo "6. Testing non-database query (weather)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the weather today?"}' | jq

echo -e "\n"

# Test 7: Non-Database Query - Cooking
echo "7. Testing non-database query (cooking)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I cook pasta?"}' | jq

echo -e "\n"

# Test 8: Non-Database Query - General Knowledge
echo "8. Testing non-database query (general knowledge)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the capital of France?"}' | jq

echo -e "\n"

# Test 9: SQL Injection Attempt
echo "9. Testing SQL injection protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me users where name = \"john\"; DROP TABLE users; --"}' | jq

echo -e "\n"

# Test 10: Dangerous Operation Attempt
echo "10. Testing dangerous operation protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Delete some records from the database"}' | jq

echo -e "\n"

# Test 11: Empty Query
echo "11. Testing empty query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": ""}' | jq

echo -e "\n"

# Test 12: Large Result Set Request
echo "12. Testing large result set request..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me all data from all tables without any limits", "max_results": 10000}' | jq

echo -e "\n"

# Test 13: Basic SHOW Tables Query
echo "13. Testing SHOW TABLES query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show tables"}' | jq

echo -e "\n"

# Test 14: Simple Data Query
echo "14. Testing simple data query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me the first 5 records from any table"}' | jq

echo -e "\n"

# Test 15: Health Check
echo "15. Testing health check endpoint..."
curl -X GET "http://localhost:8001/health" | jq

echo -e "\n"

# Test 16: MCP Server Health Check
echo "16. Testing MCP server health check..."
curl -X GET "http://localhost:8000/health" | jq

echo -e "\n"

# Test 17: Direct Query Endpoint
echo "17. Testing direct query endpoint..."
curl -X POST "http://localhost:8001/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "SELECT 1 as test", "limit": 10}' | jq

echo -e "\n"

# Test 18: Schema Endpoint
echo "18. Testing schema endpoint..."
curl -X GET "http://localhost:8001/schema" | jq

echo -e "\n"

echo "✅ All tests completed!"
echo "=========================================================="
echo "Summary of what was tested:"
echo "- Database structure queries"
echo "- Complex aggregations and joins"
echo "- Non-database query handling"
echo "- Security (SQL injection, dangerous operations)"
echo "- Edge cases (empty queries, large result sets)"
echo "- Basic CRUD operations"
echo "- Health checks"
echo "- Direct API endpoints"
echo "=========================================================="
