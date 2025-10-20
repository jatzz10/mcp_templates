#!/bin/bash

# REST API MCP Server Test Commands
# This file contains all the curl commands used to test the system

echo "🧪 Testing REST API MCP Server with Natural Language Queries"
echo "============================================================"

# Test 1: Basic API Structure Query
echo "1. Testing API structure query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the structure of the REST API? Show me all available endpoints"}' | jq

echo -e "\n"

# Test 2: API Data Query
echo "2. Testing API data query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Get data from the users endpoint"}' | jq

echo -e "\n"

# Test 3: API Search Query
echo "3. Testing API search query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Search for items with specific criteria using the API"}' | jq

echo -e "\n"

# Test 4: API Statistics Query
echo "4. Testing API statistics query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me statistics and counts from the API data"}' | jq

echo -e "\n"

# Test 5: API Filtering Query
echo "5. Testing API filtering query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Filter the API data by specific parameters and show results"}' | jq

echo -e "\n"

# Test 6: Vague Query
echo "6. Testing vague query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me stuff"}' | jq

echo -e "\n"

# Test 7: Non-API Query - Weather
echo "7. Testing non-API query (weather)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the weather today?"}' | jq

echo -e "\n"

# Test 8: Non-API Query - Cooking
echo "8. Testing non-API query (cooking)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I cook pasta?"}' | jq

echo -e "\n"

# Test 9: API Injection Attempt
echo "9. Testing API injection protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Call API with malicious parameters: /api/users?admin=true&delete=all"}' | jq

echo -e "\n"

# Test 10: Dangerous Operation Attempt
echo "10. Testing dangerous operation protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Delete all data from the API"}' | jq

echo -e "\n"

# Test 11: Empty Query
echo "11. Testing empty query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": ""}' | jq

echo -e "\n"

# Test 12: Large Response Request
echo "12. Testing large response request..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Get all data from all endpoints without any limits", "max_results": 10000}' | jq

echo -e "\n"

# Test 13: HTTP Method Test
echo "13. Testing HTTP method usage..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Use POST method to create a new item"}' | jq

echo -e "\n"

# Test 14: API Error Handling
echo "14. Testing API error handling..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Call a non-existent API endpoint"}' | jq

echo -e "\n"

# Test 15: Health Check
echo "15. Testing health check endpoint..."
curl -X GET "http://localhost:8001/health" | jq

echo -e "\n"

# Test 16: MCP Server Health Check
echo "16. Testing MCP server health check..."
curl -X GET "http://localhost:8000/health" | jq

echo -e "\n"

# Test 17: Direct API Call
echo "17. Testing direct API call..."
curl -X POST "http://localhost:8001/call_api" \
     -H "Content-Type: application/json" \
     -d '{"endpoint": "/users", "method": "GET", "params": {"limit": 10}}' | jq

echo -e "\n"

# Test 18: API Schema
echo "18. Testing API schema..."
curl -X GET "http://localhost:8001/api_schema" | jq

echo -e "\n"

# Test 19: API Endpoints
echo "19. Testing API endpoints list..."
curl -X GET "http://localhost:8001/endpoints" | jq

echo -e "\n"

# Test 20: API Authentication Test
echo "20. Testing API authentication..."
curl -X POST "http://localhost:8001/test_auth" \
     -H "Content-Type: application/json" \
     -d '{}' | jq

echo -e "\n"

echo "✅ All tests completed!"
echo "============================================================"
echo "Summary of what was tested:"
echo "- REST API structure and endpoint queries"
echo "- API data retrieval and filtering"
echo "- API search and statistics"
echo "- Non-API query handling"
echo "- Security (API injection, dangerous operations)"
echo "- Edge cases (empty queries, large responses)"
echo "- HTTP method usage"
echo "- Error handling"
echo "- Health checks"
echo "- Direct API endpoints"
echo "============================================================"
