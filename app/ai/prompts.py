"""Prompt templates for AI providers"""
import json
from typing import Dict, Any


def get_test_generation_prompt(endpoint: Any, options: Dict[str, Any]) -> str:
    """
    Generate prompt for test case generation
    
    Args:
        endpoint: Normalized endpoint
        options: Generation options
        
    Returns:
        Formatted prompt
    """
    count = options.get("count", 10)
    domain_hint = options.get("domain_hint", "")
    
    # Build endpoint description
    endpoint_desc = {
        "method": endpoint.method,
        "path": endpoint.path,
        "operation_id": endpoint.operation_id,
        "description": endpoint.description,
        "parameters": [
            {
                "name": p.name,
                "in": p.location,
                "required": p.required,
                "schema": p.schema
            }
            for p in endpoint.parameters
        ],
        "request_body": endpoint.request_body,
        "responses": endpoint.responses
    }
    
    prompt = f"""Generate {count} test cases for the following API endpoint.

Endpoint Details:
{json.dumps(endpoint_desc, indent=2)}

Domain Context: {domain_hint or "General API"}

Requirements:
1. Generate a mix of test types:
   - Valid cases (at least {count // 2}): Normal, expected inputs
   - Boundary cases ({count // 3}): Edge values like min/max lengths, limits
   - Negative cases (remaining): Invalid inputs, missing required fields, type mismatches

2. For each test case, provide:
   - name: Descriptive test name
   - description: What the test validates
   - headers: HTTP headers (include Content-Type if needed)
   - query_params: Query parameters (if any)
   - path_params: Path parameters (if any)
   - body: Request body (if applicable)
   - expected_status: Expected HTTP status code
   - test_type: "valid", "boundary", or "negative"

3. Ensure variety in test data:
   - Use realistic values based on the domain context
   - Include different combinations of optional parameters
   - Test various error scenarios

Return the test cases as a JSON object with a "cases" array.

Example format:
{{
  "cases": [
    {{
      "name": "create_valid_user",
      "description": "Test creating a user with valid data",
      "headers": {{"Content-Type": "application/json"}},
      "query_params": {{}},
      "path_params": {{}},
      "body": {{"name": "John Doe", "email": "john@example.com"}},
      "expected_status": 201,
      "test_type": "valid"
    }}
  ]
}}

Generate the test cases now:
"""
    
    return prompt