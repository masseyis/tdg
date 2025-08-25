"""WireMock stub renderer"""

import json
import uuid
from typing import Any, Dict, List


def render(cases: List[Any], api: Any) -> List[Dict[str, Any]]:
    """
    Render WireMock stub mappings

    Returns:
        List of WireMock mapping objects
    """
    mappings = []

    # Create stubs for valid cases only
    valid_cases = [c for c in cases if c.test_type == "valid"]

    for case in valid_cases:
        mapping = _create_stub_mapping(case)
        mappings.append(mapping)

    return mappings


def _create_stub_mapping(case: Any) -> Dict[str, Any]:
    """Create WireMock stub mapping"""
    mapping = {
        "id": str(uuid.uuid4()),
        "name": case.name,
        "request": {"method": case.method, "urlPattern": _path_to_pattern(case.path)},
        "response": {
            "status": case.expected_status,
            "headers": {"Content-Type": "application/json"},
        },
    }

    # Add request body matcher if present
    if case.body:
        mapping["request"]["bodyPatterns"] = [
            {
                "equalToJson": json.dumps(case.body),
                "ignoreArrayOrder": True,
                "ignoreExtraElements": True,
            }
        ]

    # Add query parameter matchers
    if case.query_params:
        mapping["request"]["queryParameters"] = {}
        for key, value in case.query_params.items():
            mapping["request"]["queryParameters"][key] = {"equalTo": str(value)}

    # Add response body
    if case.expected_response:
        mapping["response"]["body"] = json.dumps(case.expected_response)
    else:
        # Generate default response
        mapping["response"]["body"] = json.dumps(
            {
                "id": "{{randomValue type='UUID'}}",
                "status": "success",
                "message": f"Mocked response for {case.name}",
            }
        )

    return mapping


def _path_to_pattern(path: str) -> str:
    """Convert path with params to regex pattern"""
    import re

    # Convert {param} to regex
    pattern = re.sub(r"\{([^}]+)\}", r"[^/]+", path)
    return pattern
