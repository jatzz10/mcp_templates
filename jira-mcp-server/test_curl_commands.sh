#!/bin/bash

# Jira MCP Server Test Commands
# This file contains all the curl commands used to test the system

echo "🧪 Testing Jira MCP Server with Natural Language Queries"
echo "======================================================="

# Test 1: Basic Jira Structure Query
echo "1. Testing Jira structure query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the structure of the Jira instance? Show me all projects and issue types"}' | jq

echo -e "\n"

# Test 2: Issue Search Query
echo "2. Testing issue search query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Find all open issues assigned to me"}' | jq

echo -e "\n"

# Test 3: Project Analysis
echo "3. Testing project analysis..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me statistics about issues in the project: total issues, by status, by priority"}' | jq

echo -e "\n"

# Test 4: Issue Details Query
echo "4. Testing issue details query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me the details of the most recent issues created"}' | jq

echo -e "\n"

# Test 5: Sprint/Version Analysis
echo "5. Testing sprint/version analysis..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What issues are in the current sprint or latest version?"}' | jq

echo -e "\n"

# Test 6: Vague Query
echo "6. Testing vague query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me stuff"}' | jq

echo -e "\n"

# Test 7: Non-Jira Query - Weather
echo "7. Testing non-Jira query (weather)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the weather today?"}' | jq

echo -e "\n"

# Test 8: Non-Jira Query - Cooking
echo "8. Testing non-Jira query (cooking)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I cook pasta?"}' | jq

echo -e "\n"

# Test 9: JQL Injection Attempt
echo "9. Testing JQL injection protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me issues where summary = \"test\"; DELETE FROM issues; --"}' | jq

echo -e "\n"

# Test 10: Dangerous Operation Attempt
echo "10. Testing dangerous operation protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Delete some issues from the project"}' | jq

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
     -d '{"question": "Show me all issues in the project without any limits", "max_results": 10000}' | jq

echo -e "\n"

# Test 13: Issue Type Filter
echo "13. Testing issue type filter..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me all bugs and stories in the project"}' | jq

echo -e "\n"

# Test 14: Priority Analysis
echo "14. Testing priority analysis..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me all high priority issues and their assignees"}' | jq

echo -e "\n"

# Test 15: Health Check
echo "15. Testing health check endpoint..."
curl -X GET "http://localhost:8001/health" | jq

echo -e "\n"

# Test 16: MCP Server Health Check
echo "16. Testing MCP server health check..."
curl -X GET "http://localhost:8000/health" | jq

echo -e "\n"

# Test 17: Direct JQL Query
echo "17. Testing direct JQL query..."
curl -X POST "http://localhost:8001/query_jira" \
     -H "Content-Type: application/json" \
     -d '{"jql": "project = PROJ AND status = Open", "max_results": 10}' | jq

echo -e "\n"

# Test 18: Issue Details
echo "18. Testing issue details..."
curl -X POST "http://localhost:8001/get_issue" \
     -H "Content-Type: application/json" \
     -d '{"issue_key": "PROJ-1"}' | jq

echo -e "\n"

# Test 19: Project Information
echo "19. Testing project information..."
curl -X GET "http://localhost:8001/projects" | jq

echo -e "\n"

# Test 20: User Information
echo "20. Testing user information..."
curl -X POST "http://localhost:8001/get_user" \
     -H "Content-Type: application/json" \
     -d '{"username": "current_user"}' | jq

echo -e "\n"

echo "✅ All tests completed!"
echo "======================================================="
echo "Summary of what was tested:"
echo "- Jira structure and project queries"
echo "- Issue search and filtering"
echo "- Project analysis and statistics"
echo "- Non-Jira query handling"
echo "- Security (JQL injection, dangerous operations)"
echo "- Edge cases (empty queries, large result sets)"
echo "- Issue operations"
echo "- Health checks"
echo "- Direct API endpoints"
echo "======================================================="
