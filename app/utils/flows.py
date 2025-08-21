"""Multi-step flow composition utilities"""
import re
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FlowStep:
    """Single step in a test flow"""
    name: str
    method: str
    path: str
    body: Optional[Dict[str, Any]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    extract: Dict[str, str] = field(default_factory=dict)  # var_name: json_path
    assertions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TestFlow:
    """Multi-step test flow"""
    name: str
    description: Optional[str] = None
    steps: List[FlowStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)


def create_basic_flows(endpoints: List[Any]) -> List[TestFlow]:
    """
    Create basic multi-step flows from endpoints
    
    Args:
        endpoints: List of normalized endpoints
        
    Returns:
        List of test flows
    """
    flows = []
    
    # Group endpoints by resource
    resource_groups = {}
    for endpoint in endpoints:
        # Extract resource name from path (e.g., /users/{id} -> users)
        parts = endpoint.path.strip("/").split("/")
        if parts:
            resource = parts[0]
            if resource not in resource_groups:
                resource_groups[resource] = []
            resource_groups[resource].append(endpoint)
    
    # Create CRUD flows for each resource
    for resource, group_endpoints in resource_groups.items():
        flow = create_crud_flow(resource, group_endpoints)
        if flow and len(flow.steps) > 1:
            flows.append(flow)
    
    return flows


def create_crud_flow(resource: str, endpoints: List[Any]) -> Optional[TestFlow]:
    """Create CRUD flow for a resource"""
    flow = TestFlow(
        name=f"{resource.title()} CRUD Flow",
        description=f"Create, Read, Update, Delete flow for {resource}"
    )
    
    # Find POST endpoint (Create)
    post_endpoints = [e for e in endpoints if e.method == "POST" and "{" not in e.path]
    if post_endpoints:
        post_ep = post_endpoints[0]
        step = FlowStep(
            name=f"Create {resource}",
            method="POST",
            path=post_ep.path,
            body={"name": f"Test {resource}", "description": "Created by test flow"},
            extract={"created_id": "$.id", "created_name": "$.name"}
        )
        flow.steps.append(step)
    
    # Find GET by ID endpoint (Read)
    get_endpoints = [e for e in endpoints if e.method == "GET" and "{id}" in e.path]
    if get_endpoints and flow.steps:
        get_ep = get_endpoints[0]
        step = FlowStep(
            name=f"Get {resource} by ID",
            method="GET",
            path=get_ep.path.replace("{id}", "${created_id}"),
            assertions=[
                {"field": "$.id", "equals": "${created_id}"},
                {"field": "$.name", "equals": "${created_name}"}
            ]
        )
        flow.steps.append(step)
    
    # Find PUT/PATCH endpoint (Update)
    update_endpoints = [e for e in endpoints if e.method in ["PUT", "PATCH"] and "{id}" in e.path]
    if update_endpoints and flow.steps:
        update_ep = update_endpoints[0]
        step = FlowStep(
            name=f"Update {resource}",
            method=update_ep.method,
            path=update_ep.path.replace("{id}", "${created_id}"),
            body={"name": f"Updated {resource}", "description": "Updated by test flow"}
        )
        flow.steps.append(step)
    
    # Find DELETE endpoint
    delete_endpoints = [e for e in endpoints if e.method == "DELETE" and "{id}" in e.path]
    if delete_endpoints and flow.steps:
        delete_ep = delete_endpoints[0]
        step = FlowStep(
            name=f"Delete {resource}",
            method="DELETE",
            path=delete_ep.path.replace("{id}", "${created_id}"),
            assertions=[
                {"statusCode": 204}
            ]
        )
        flow.steps.append(step)
    
    return flow if len(flow.steps) > 1 else None


def resolve_variables(text: str, variables: Dict[str, Any]) -> str:
    """
    Replace ${var_name} with actual values
    
    Args:
        text: Text with variable references
        variables: Variable values
        
    Returns:
        Text with variables resolved
    """
    def replacer(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    
    return re.sub(r'\$\{([^}]+)\}', replacer, text)


def extract_from_response(response: Dict[str, Any], json_path: str) -> Any:
    """
    Extract value from response using simple JSON path
    
    Args:
        response: Response data
        json_path: JSON path (e.g., $.data.id)
        
    Returns:
        Extracted value
    """
    if not json_path.startswith("$"):
        return None
    
    path_parts = json_path[1:].strip(".").split(".")
    current = response
    
    for part in path_parts:
        if not part:
            continue
        
        # Handle array index
        if "[" in part and "]" in part:
            field, index = part.split("[")
            index = int(index.rstrip("]"))
            current = current.get(field, [])[index]
        else:
            current = current.get(part)
        
        if current is None:
            break
    
    return current