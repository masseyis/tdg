#!/usr/bin/env python3
"""
Convert shared JSON test data to Postman collection.

This demonstrates how the generated test-data.json can be converted 
to a Postman collection for API testing.
"""

import json
import sys
from typing import Dict, Any, List


def convert_to_postman(test_data: Dict[str, Any], base_url: str = "{{base_url}}") -> Dict[str, Any]:
    """
    Convert test data JSON to Postman collection format.
    
    Args:
        test_data: Test data from JSON file
        base_url: Base URL for the API (can use Postman variables)
        
    Returns:
        Postman collection dictionary
    """
    collection = {
        "info": {
            "name": f"API Tests - {test_data['metadata']['generator']}",
            "description": f"Generated test collection with {test_data['metadata']['total_cases']} test cases",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "base_url",
                "value": base_url,
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Group test cases by endpoint
    endpoints = {}
    for test_case in test_data['test_cases']:
        endpoint_key = f"{test_case['method']} {test_case['path']}"
        if endpoint_key not in endpoints:
            endpoints[endpoint_key] = []
        endpoints[endpoint_key].append(test_case)
    
    # Create Postman items
    for endpoint_key, cases in endpoints.items():
        method, path = endpoint_key.split(' ', 1)
        
        # Create folder for this endpoint
        folder = {
            "name": f"{method.upper()} {path}",
            "item": []
        }
        
        for test_case in cases:
            # Convert test case to Postman request
            request_item = {
                "name": test_case['name'],
                "request": {
                    "method": test_case['method'].upper(),
                    "header": [],
                    "url": {
                        "raw": f"{{{{base_url}}}}{test_case['path']}",
                        "host": ["{{base_url}}"],
                        "path": test_case['path'].split('/')[1:] if test_case['path'].startswith('/') else test_case['path'].split('/')
                    }
                },
                "response": []
            }
            
            # Add headers
            if test_case.get('headers'):
                for key, value in test_case['headers'].items():
                    request_item['request']['header'].append({
                        "key": key,
                        "value": str(value),
                        "type": "text"
                    })
            
            # Add query parameters
            if test_case.get('query_params'):
                request_item['request']['url']['query'] = []
                for key, value in test_case['query_params'].items():
                    request_item['request']['url']['query'].append({
                        "key": key,
                        "value": str(value)
                    })
            
            # Add path variables
            if test_case.get('path_params'):
                request_item['request']['url']['variable'] = []
                for key, value in test_case['path_params'].items():
                    request_item['request']['url']['variable'].append({
                        "key": key,
                        "value": str(value)
                    })
            
            # Add body
            if test_case.get('body'):
                request_item['request']['body'] = {
                    "mode": "raw",
                    "raw": json.dumps(test_case['body'], indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            # Add test script to check status code
            request_item['event'] = [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            f"pm.test('Status code is {test_case['expected_status']}', function () {{",
                            f"    pm.response.to.have.status({test_case['expected_status']});",
                            "});",
                            "",
                            f"pm.test('Test type: {test_case.get('test_type', 'unknown')}', function () {{",
                            "    // This test documents the test type",
                            "    pm.expect(true).to.be.true;",
                            "});"
                        ],
                        "type": "text/javascript"
                    }
                }
            ]
            
            folder['item'].append(request_item)
        
        collection['item'].append(folder)
    
    return collection


def main():
    """Convert JSON test data to Postman collection."""
    if len(sys.argv) < 2:
        print("Usage: python postman_from_json.py <test-data.json> [base_url] [output_file]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "{{base_url}}"
    output_file = sys.argv[3] if len(sys.argv) > 3 else "generated_postman_collection.json"
    
    # Load test data
    try:
        with open(json_file, 'r') as f:
            test_data = json.load(f)
    except Exception as e:
        print(f"Error loading test data: {e}")
        sys.exit(1)
    
    # Convert to Postman format
    postman_collection = convert_to_postman(test_data, base_url)
    
    # Save Postman collection
    try:
        with open(output_file, 'w') as f:
            json.dump(postman_collection, f, indent=2)
        print(f"✅ Postman collection saved to: {output_file}")
        print(f"📊 {len(postman_collection['item'])} endpoint folders created")
        print(f"🧪 {test_data['metadata']['total_cases']} test cases converted")
    except Exception as e:
        print(f"Error saving Postman collection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
