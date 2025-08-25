"""Postman collection renderer"""

import json
import uuid
from typing import Any, Dict, List


def render(cases: List[Any], api: Any, flows: List[Any] = None) -> Dict[str, Any]:
    """
    Render Postman collection

    Returns:
        Postman collection v2.1 format
    """
    collection = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": api.title,
            "description": api.description or "Generated test collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": api.servers[0] if api.servers else "http://localhost:8080",
                "type": "string",
            },
            {"key": "authToken", "value": "", "type": "string"},
        ],
    }

    # Group cases by endpoint
    endpoint_groups = {}
    for case in cases:
        key = f"{case.method} {case.path}"
        if key not in endpoint_groups:
            endpoint_groups[key] = {"name": key, "item": []}

        # Create request item
        item = _create_request_item(case)
        endpoint_groups[key]["item"].append(item)

    # Add endpoint groups to collection
    collection["item"].extend(endpoint_groups.values())

    # Add flows as separate folder
    if flows:
        flow_folder = {"name": "Test Flows", "item": []}

        for flow in flows:
            flow_item = _create_flow_item(flow)
            flow_folder["item"].append(flow_item)

        collection["item"].append(flow_folder)

    return collection


def _create_request_item(case: Any) -> Dict[str, Any]:
    """Create Postman request item"""
    # Build URL
    url = {
        "raw": "{{baseUrl}}" + case.path,
        "host": ["{{baseUrl}}"],
        "path": case.path.strip("/").split("/"),
        "query": [],
    }

    # Add query parameters
    for key, value in case.query_params.items():
        url["query"].append({"key": key, "value": str(value)})

    # Build request
    request = {"method": case.method, "header": [], "url": url}

    # Add headers
    for key, value in case.headers.items():
        request["header"].append({"key": key, "value": value})

    # Add body if present
    if case.body:
        request["body"] = {
            "mode": "raw",
            "raw": json.dumps(case.body, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    # Create test script
    test_script = f"""
pm.test("Status code is {case.expected_status}", function () {{
    pm.response.to.have.status({case.expected_status});
}});

pm.test("Response time is less than 1000ms", function () {{
    pm.expect(pm.response.responseTime).to.be.below(1000);
}});

if (pm.response.code === 200 || pm.response.code === 201) {{
    pm.test("Response has valid JSON", function () {{
        pm.response.to.be.json;
    }});

    // Store ID if present for chaining
    var jsonData = pm.response.json();
    if (jsonData.id) {{
        pm.collectionVariables.set("lastCreatedId", jsonData.id);
    }}
}}
"""

    return {
        "name": case.name,
        "request": request,
        "response": [],
        "event": [
            {
                "listen": "test",
                "script": {"exec": test_script.strip().split("\n"), "type": "text/javascript"},
            }
        ],
    }


def _create_flow_item(flow: Any) -> Dict[str, Any]:
    """Create Postman flow item"""
    flow_item = {"name": flow.name, "description": flow.description, "item": []}

    for step in flow.steps:
        # Build URL with variable substitution
        url_path = step.path
        for var in flow.variables:
            url_path = url_path.replace(f"${{{var}}}", f"{{{{lastCreatedId}}}}")

        request = {
            "name": step.name,
            "request": {
                "method": step.method,
                "header": [{"key": k, "value": v} for k, v in step.headers.items()],
                "url": {
                    "raw": "{{baseUrl}}" + url_path,
                    "host": ["{{baseUrl}}"],
                    "path": url_path.strip("/").split("/"),
                },
            },
        }

        if step.body:
            request["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(step.body, indent=2),
                "options": {"raw": {"language": "json"}},
            }

        flow_item["item"].append(request)

    return flow_item
