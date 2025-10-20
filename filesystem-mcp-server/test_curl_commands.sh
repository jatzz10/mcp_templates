#!/bin/bash

# FileSystem MCP Server Test Commands
# This file contains all the curl commands used to test the system

echo "🧪 Testing FileSystem MCP Server with Natural Language Queries"
echo "============================================================="

# Test 1: Basic File System Structure Query
echo "1. Testing file system structure query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the structure of the file system? Show me the directory tree"}' | jq

echo -e "\n"

# Test 2: File Search Query
echo "2. Testing file search query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Find all Python files in the directory"}' | jq

echo -e "\n"

# Test 3: File Content Search
echo "3. Testing file content search..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Search for files containing the word \"function\" or \"class\""}' | jq

echo -e "\n"

# Test 4: File Information Query
echo "4. Testing file information query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me information about the largest files in the directory"}' | jq

echo -e "\n"

# Test 5: Directory Analysis
echo "5. Testing directory analysis..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Analyze the directory structure and show me file type distribution"}' | jq

echo -e "\n"

# Test 6: Vague Query
echo "6. Testing vague query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me stuff"}' | jq

echo -e "\n"

# Test 7: Non-FileSystem Query - Weather
echo "7. Testing non-filesystem query (weather)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the weather today?"}' | jq

echo -e "\n"

# Test 8: Non-FileSystem Query - Cooking
echo "8. Testing non-filesystem query (cooking)..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "How do I cook pasta?"}' | jq

echo -e "\n"

# Test 9: Path Traversal Attempt
echo "9. Testing path traversal protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me files from ../../../etc/passwd"}' | jq

echo -e "\n"

# Test 10: Dangerous Operation Attempt
echo "10. Testing dangerous operation protection..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Delete some files from the directory"}' | jq

echo -e "\n"

# Test 11: Empty Query
echo "11. Testing empty query..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": ""}' | jq

echo -e "\n"

# Test 12: Large File Request
echo "12. Testing large file request..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me the content of the largest file in the directory"}' | jq

echo -e "\n"

# Test 13: File Extension Filter
echo "13. Testing file extension filter..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me all text files and markdown files"}' | jq

echo -e "\n"

# Test 14: Directory Listing
echo "14. Testing directory listing..."
curl -X POST "http://localhost:8001/ask_llm" \
     -H "Content-Type: application/json" \
     -d '{"question": "List all directories and subdirectories"}' | jq

echo -e "\n"

# Test 15: Health Check
echo "15. Testing health check endpoint..."
curl -X GET "http://localhost:8001/health" | jq

echo -e "\n"

# Test 16: MCP Server Health Check
echo "16. Testing MCP server health check..."
curl -X GET "http://localhost:8000/health" | jq

echo -e "\n"

# Test 17: Direct File Read
echo "17. Testing direct file read..."
curl -X POST "http://localhost:8001/read_file" \
     -H "Content-Type: application/json" \
     -d '{"file_path": "README.md"}' | jq

echo -e "\n"

# Test 18: File Search
echo "18. Testing file search..."
curl -X POST "http://localhost:8001/search_files" \
     -H "Content-Type: application/json" \
     -d '{"pattern": "*.py", "max_results": 10}' | jq

echo -e "\n"

# Test 19: Directory Structure
echo "19. Testing directory structure..."
curl -X GET "http://localhost:8001/directory_structure" | jq

echo -e "\n"

echo "✅ All tests completed!"
echo "============================================================="
echo "Summary of what was tested:"
echo "- File system structure queries"
echo "- File search and content search"
echo "- Directory analysis"
echo "- Non-filesystem query handling"
echo "- Security (path traversal, dangerous operations)"
echo "- Edge cases (empty queries, large files)"
echo "- File operations"
echo "- Health checks"
echo "- Direct API endpoints"
echo "============================================================="
