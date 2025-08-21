import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Authentication types"""
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "apiKey"
    OAUTH2 = "oauth2"

@dataclass

class Parameter:
    """API parameter"""
    name: str
    location: str  # path, query, header, cookie
    required: bool = False
    schema: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

@dataclass

class Endpoint:
    """Normalized endpoint"""
    path: str
    method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    auth: AuthType = AuthType.NONE
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

@dataclass

class NormalizedAPI:
    """Normalized OpenAPI specification"""
    title: str
    version: str
    description: Optional[str] = None
    servers: List[str] = field(default_factory=list)
    endpoints: List[Endpoint] = field(default_factory=list)
    components: Dict[str, Any] = field(default_factory=dict)


def normalize_openapi(spec: Dict[str, Any]) -> NormalizedAPI:
    """
    Normalize OpenAPI spec to internal model

    Args:
        spec: Raw OpenAPI specification

    Returns:
        Normalized API model
    """
    # Extract basic info
    info = spec.get("info", {})
    normalized = NormalizedAPI(
        title=info.get("title", "API"),
        version=info.get("version", "1.0.0"),
        description=info.get("description"),
        servers=[s.get("url") for s in spec.get("servers", [])],
        components=spec.get("components", {})
    )

    # Parse paths
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        # Handle path-level parameters
        path_params = path_item.get("parameters", [])

        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            if method not in path_item:
                continue

            operation = path_item[method]

            # Create endpoint
            endpoint = Endpoint(
                path=path,
                method=method.upper(),
                operation_id=operation.get("operationId"),
                summary=operation.get("summary"),
                description=operation.get("description"),
                tags=operation.get("tags", [])
            )

            # Parse parameters
            all_params = path_params + operation.get("parameters", [])
            for param in all_params:
                # Handle $ref
                if "$ref" in param:
                    param = resolve_ref(spec, param["$ref"])

                endpoint.parameters.append(Parameter(
                    name=param.get("name"),
                    location=param.get("in"),
                    required=param.get("required", False),
                    schema=param.get("schema", {}),
                    description=param.get("description")
                ))

            # Parse request body
            if "requestBody" in operation:
                req_body = operation["requestBody"]
                if "$ref" in req_body:
                    req_body = resolve_ref(spec, req_body["$ref"])

                content = req_body.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    # Resolve all $ref references in schema
                    endpoint.request_body = resolve_schema_refs(spec, schema)

            # Parse responses
            for status, response in operation.get("responses", {}).items():
                if "$ref" in response:
                    response = resolve_ref(spec, response["$ref"])

                content = response.get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    endpoint.responses[status] = resolve_schema_refs(spec, schema)

            # Detect auth
            endpoint.auth = detect_auth(operation, spec)

            normalized.endpoints.append(endpoint)

    return normalized


def resolve_ref(spec: Dict[str, Any], ref: str) -> Dict[str, Any]:
    """Resolve $ref pointer"""
    if not ref.startswith("  # /"):
        return {}

    parts = ref[2:].split("/")
    result = spec
    for part in parts:
        result = result.get(part, {})
    return result


def resolve_schema_refs(spec: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively resolve all $ref references in a schema"""
    if not isinstance(schema, dict):
        return schema

    # Handle direct $ref
    if "$ref" in schema:
        resolved = resolve_ref(spec, schema["$ref"])
        return resolve_schema_refs(spec, resolved)

    # Handle nested $ref in properties
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            schema["properties"][prop_name] = resolve_schema_refs(spec, prop_schema)

    # Handle nested $ref in items (for arrays)
    if "items" in schema:
        schema["items"] = resolve_schema_refs(spec, schema["items"])

    # Handle nested $ref in allOf, anyOf, oneOf
    for key in ["allOf", "anyOf", "oneOf"]:
        if key in schema:
            schema[key] = [resolve_schema_refs(spec, item) for item in schema[key]]

    return schema


def detect_auth(operation: Dict[str, Any], spec: Dict[str, Any]) -> AuthType:
    """Detect authentication type for operation"""
    security = operation.get("security", spec.get("security", []))
    if not security:
        return AuthType.NONE

    # Check first security requirement
    if security and security[0]:
        scheme_name = list(security[0].keys())[0]
        components = spec.get("components", {}).get("securitySchemes", {})
        scheme = components.get(scheme_name, {})

        if scheme.get("type") == "http":
            if scheme.get("scheme") == "bearer":
                return AuthType.BEARER
            elif scheme.get("scheme") == "basic":
                return AuthType.BASIC
        elif scheme.get("type") == "apiKey":
            return AuthType.API_KEY
        elif scheme.get("type") == "oauth2":
            return AuthType.OAUTH2

    return AuthType.NONE
