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

    # Domain-specific guidance
    domain_guidance = _get_domain_guidance(domain_hint)
    
    prompt = f"""Generate {count} comprehensive test cases for the following API endpoint.

Endpoint Details:
{json.dumps(endpoint_desc, indent=2)}

Domain Context: {domain_hint or "General API"}

{domain_guidance}

Requirements:
1. Generate a mix of test types:
   - Valid cases (at least {count // 2}): Normal, expected inputs with realistic domain data
   - Boundary cases ({count // 3}): Edge values, limits, and boundary conditions
   - Negative cases (remaining): Invalid inputs, missing required fields, type mismatches, and error scenarios

2. For each test case, provide:
   - name: Descriptive test name that clearly indicates the test purpose
   - description: Detailed explanation of what the test validates and why
   - headers: HTTP headers (include Content-Type if needed)
   - query_params: Query parameters (if any)
   - path_params: Path parameters (if any)
   - body: Request body with realistic, domain-relevant data (if applicable)
   - expected_status: Expected HTTP status code
   - test_type: "valid", "boundary", or "negative"

3. Domain-Relevant Data Requirements:
   - Use realistic, contextually appropriate values based on the domain
   - For e-commerce: realistic product names, prices, categories
   - For pet stores: realistic pet names, breeds, statuses
   - For user management: realistic names, emails, phone numbers
   - For financial: realistic amounts, currencies, account numbers
   - For healthcare: realistic patient data, medical terms
   - For social media: realistic usernames, posts, content

4. Enhanced Edge Cases:
   - Test minimum and maximum field lengths
   - Test boundary values (0, 1, max_int, max_string_length)
   - Test special characters and Unicode
   - Test empty strings vs null values
   - Test date boundaries (past, present, future, leap years)
   - Test numeric boundaries (negative, zero, very large numbers)
   - Test array boundaries (empty, single item, max items)

5. Comprehensive Negative Cases:
   - Missing required fields
   - Invalid data types (string where number expected)
   - Invalid formats (malformed emails, dates, URLs)
   - Invalid enum values
   - Invalid ranges (negative prices, future birth dates)
   - Malformed JSON
   - SQL injection attempts
   - XSS attempts
   - Extremely long inputs
   - Invalid authentication scenarios

6. Test Case Ordering:
   - Order test cases logically: CREATE → READ → UPDATE → DELETE
   - For CRUD operations, ensure dependencies are respected
   - Group related test cases together
   - Start with basic valid cases, then edge cases, then negative cases

Return the test cases as a JSON object with a "cases" array.

Example format:
{{
  "cases": [
    {{
      "name": "create_valid_user_with_complete_data",
      "description": "Test creating a user with all required and optional fields using realistic domain data",
      "headers": {{"Content-Type": "application/json"}},
      "query_params": {{}},
      "path_params": {{}},
      "body": {{"name": "Sarah Johnson", "email": "sarah.johnson@example.com", "phone": "+1-555-0123"}},
      "expected_status": 201,
      "test_type": "valid"
    }}
  ]
}}

Generate the test cases now:
"""

    return prompt


def _get_domain_guidance(domain_hint: str) -> str:
    """Get domain-specific guidance for test generation"""
    domain_hint_lower = domain_hint.lower() if domain_hint else ""
    
    if "pet" in domain_hint_lower or "animal" in domain_hint_lower:
        return """Pet Store Domain Guidance:
- Use realistic pet names: Buddy, Luna, Max, Bella, Charlie, Daisy
- Use realistic pet categories: Dogs, Cats, Birds, Fish, Reptiles
- Use realistic pet statuses: available, pending, sold
- Use realistic pet tags: friendly, trained, hypoallergenic, purebred
- Use realistic photo URLs and descriptions
- Test pet-specific edge cases: very long pet names, special characters in names
- Test invalid pet data: negative ages, invalid statuses, malformed photo URLs"""

    elif "ecommerce" in domain_hint_lower or "shop" in domain_hint_lower or "store" in domain_hint_lower:
        return """E-commerce Domain Guidance:
- Use realistic product names: iPhone 15 Pro, Nike Air Max, Samsung TV
- Use realistic prices: $999.99, €299.50, £149.99
- Use realistic categories: Electronics, Clothing, Home & Garden
- Use realistic SKUs, barcodes, and product codes
- Test price boundaries: $0.01, $999999.99, negative prices
- Test inventory scenarios: in stock, out of stock, low stock
- Test discount and promotion scenarios"""

    elif "user" in domain_hint_lower or "auth" in domain_hint_lower:
        return """User Management Domain Guidance:
- Use realistic names: John Smith, Maria Garcia, David Chen
- Use realistic emails: john.smith@company.com, maria.garcia@gmail.com
- Use realistic phone numbers: +1-555-0123, +44-20-7946-0958
- Use realistic usernames: johnsmith, maria_garcia, david.chen
- Test password complexity requirements
- Test email validation and format checking
- Test username uniqueness and format rules
- Test authentication scenarios: valid/invalid credentials"""

    elif "financial" in domain_hint_lower or "bank" in domain_hint_lower or "payment" in domain_hint_lower:
        return """Financial Domain Guidance:
- Use realistic amounts: $1,234.56, €999.99, £2,500.00
- Use realistic currencies: USD, EUR, GBP, JPY, CAD
- Use realistic account numbers and routing numbers
- Use realistic transaction IDs and reference numbers
- Test monetary boundaries: $0.01, $999,999.99, negative amounts
- Test currency conversion scenarios
- Test payment method validation"""

    elif "healthcare" in domain_hint_lower or "medical" in domain_hint_lower:
        return """Healthcare Domain Guidance:
- Use realistic patient names: Dr. Sarah Johnson, Patient John Smith
- Use realistic medical terms and diagnoses
- Use realistic dates: birth dates, appointment dates
- Use realistic medical record numbers and IDs
- Test HIPAA compliance scenarios
- Test medical data validation
- Test appointment scheduling edge cases"""

    elif "social" in domain_hint_lower or "media" in domain_hint_lower:
        return """Social Media Domain Guidance:
- Use realistic usernames: @johnsmith, @maria_garcia, @david.chen
- Use realistic post content and hashtags
- Use realistic profile information
- Test content moderation scenarios
- Test username uniqueness and format rules
- Test post length limits and content validation"""

    else:
        return """General API Domain Guidance:
- Use realistic, contextually appropriate data for the domain
- Ensure data consistency across related test cases
- Test both happy path and error scenarios
- Include comprehensive edge case testing
- Validate business logic and constraints"""


def order_test_cases(cases: list) -> list:
    """
    Order test cases logically: CREATE → READ → UPDATE → DELETE
    
    Args:
        cases: List of test cases
        
    Returns:
        Ordered list of test cases
    """
    # Define operation priorities
    operation_priority = {
        "POST": 1,    # CREATE
        "GET": 2,     # READ
        "PUT": 3,     # UPDATE
        "PATCH": 3,   # UPDATE
        "DELETE": 4   # DELETE
    }
    
    # Define test type priorities within each operation
    test_type_priority = {
        "valid": 1,
        "boundary": 2,
        "negative": 3
    }
    
    def get_case_priority(case):
        """Calculate priority for a test case"""
        method_priority = operation_priority.get(case.method, 5)
        type_priority = test_type_priority.get(case.test_type, 4)
        
        # Additional ordering within same method/type
        # Prefer cases without path parameters (more general) first
        path_param_priority = 0 if not case.path_params else 1
        
        return (method_priority, type_priority, path_param_priority)
    
    # Sort cases by priority
    ordered_cases = sorted(cases, key=get_case_priority)
    
    return ordered_cases
