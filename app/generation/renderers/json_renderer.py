"""JSON renderer for test data"""
import json
from typing import List, Any, Dict


def render(cases: List[Any]) -> List[Dict[str, Any]]:
    """
    Render test cases as JSON
    
    Returns:
        List of test case dictionaries
    """
    result = []
    
    for case in cases:
        case_dict = {
            "name": case.name,
            "description": case.description,
            "method": case.method,
            "path": case.path,
            "headers": case.headers,
            "queryParams": case.query_params,
            "pathParams": case.path_params,
            "body": case.body,
            "expectedStatus": case.expected_status,
            "expectedResponse": case.expected_response,
            "testType": case.test_type
        }
        result.append(case_dict)
    
    return result