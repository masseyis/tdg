"""OpenAPI parsing tests"""
import pytest
import yaml
import json
from app.utils.openapi_loader import load_openapi_spec, parse_spec_content
from app.utils.openapi_normalizer import normalize_openapi


def test_parse_yaml_spec():
    """Test parsing YAML OpenAPI spec"""
    yaml_content = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: Success
"""
    spec = parse_spec_content(yaml_content)
    assert spec["info"]["title"] == "Test API"
    assert "/users" in spec["paths"]


def test_parse_json_spec():
    """Test parsing JSON OpenAPI spec"""
    json_content = json.dumps({
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    })
    spec = parse_spec_content(json_content)
    assert spec["info"]["title"] == "Test API"
    assert "/users" in spec["paths"]


def test_normalize_openapi():
    """Test OpenAPI normalization"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store",
            "version": "1.0.0"
        },
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": "createPet",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Created"}
                    }
                }
            }
        }
    }
    
    normalized = normalize_openapi(spec)
    
    assert normalized.title == "Pet Store"
    assert len(normalized.endpoints) == 2
    
    get_endpoint = [e for e in normalized.endpoints if e.method == "GET"][0]
    assert get_endpoint.path == "/pets"
    assert get_endpoint.operation_id == "listPets"
    
    post_endpoint = [e for e in normalized.endpoints if e.method == "POST"][0]
    assert post_endpoint.request_body is not None
    assert "name" in post_endpoint.request_body.get("required", [])