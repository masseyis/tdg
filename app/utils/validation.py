"""JSON Schema validation utilities"""

import json
import logging
from typing import Any, Dict

from jsonschema import Draft7Validator, ValidationError, validate

logger = logging.getLogger(__name__)


def validate_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate data against JSON schema

    Args:
        data: Data to validate
        schema: JSON schema

    Returns:
        True if valid, False otherwise
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        logger.debug(f"Validation error: {e.message}")
        return False


def fix_data_for_schema(data: Any, schema: Dict[str, Any]) -> Any:
    """
    Attempt to fix data to match schema

    Args:
        data: Data to fix
        schema: Target schema

    Returns:
        Fixed data
    """
    if not schema:
        return data

    schema_type = schema.get("type")

    # Handle null
    if data is None:
        if schema_type == "null" or "null" in schema.get("type", []):
            return None
        return get_default_for_type(schema_type)

    # Handle type coercion
    if schema_type == "string":
        return str(data)
    elif schema_type == "number":
        try:
            return float(data)
        except Exception:
            return 0.0
    elif schema_type == "integer":
        try:
            return int(data)
        except Exception:
            return 0
    elif schema_type == "boolean":
        return bool(data)
    elif schema_type == "array":
        if not isinstance(data, list):
            data = [data] if data else []
        item_schema = schema.get("items", {})
        return [fix_data_for_schema(item, item_schema) for item in data]
    elif schema_type == "object":
        if not isinstance(data, dict):
            data = {}

        fixed = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Fix existing properties
        for key, value in data.items():
            if key in properties:
                fixed[key] = fix_data_for_schema(value, properties[key])
            else:
                fixed[key] = value

        # Add missing required properties
        for prop in required:
            if prop not in fixed and prop in properties:
                fixed[prop] = get_default_for_type(properties[prop].get("type"))

        return fixed

    return data


def get_default_for_type(schema_type: str) -> Any:
    """Get default value for JSON schema type"""
    defaults = {
        "string": "",
        "number": 0.0,
        "integer": 0,
        "boolean": False,
        "array": [],
        "object": {},
        "null": None,
    }
    return defaults.get(schema_type, None)


def is_valid_json(text: str) -> bool:
    """Check if text is valid JSON"""
    try:
        json.loads(text)
        return True
    except Exception:
        return False
