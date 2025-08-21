"""Faker utilities for data generation"""
import random
from typing import Any, Dict, List, Optional
from faker import Faker
from datetime import datetime, timedelta

# Initialize faker
fake = Faker()


def set_seed(seed: Optional[int] = None):
    """Set random seed for reproducibility"""
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)


def generate_for_schema(schema: Dict[str, Any], domain_hint: Optional[str] = None) -> Any:
    """
    Generate fake data based on JSON schema
    
    Args:
        schema: JSON schema
        domain_hint: Domain context hint
        
    Returns:
        Generated data
    """
    if not schema:
        return None
    
    schema_type = schema.get("type")
    
    # Check for enum first
    if "enum" in schema:
        return random.choice(schema["enum"])
    
    # Check for examples
    if "examples" in schema and schema["examples"]:
        return random.choice(schema["examples"])
    
    # Generate based on type
    if schema_type == "string":
        return generate_string(schema, domain_hint)
    elif schema_type == "number":
        return generate_number(schema)
    elif schema_type == "integer":
        return generate_integer(schema)
    elif schema_type == "boolean":
        return fake.boolean()
    elif schema_type == "array":
        return generate_array(schema, domain_hint)
    elif schema_type == "object":
        return generate_object(schema, domain_hint)
    elif schema_type == "null":
        return None
    
    return None


def generate_string(schema: Dict[str, Any], domain_hint: Optional[str] = None) -> str:
    """Generate string based on schema and format"""
    format_type = schema.get("format")
    pattern = schema.get("pattern")
    min_length = schema.get("minLength", 0)
    max_length = schema.get("maxLength", 100)
    
    # Handle formats
    if format_type == "date":
        return fake.date()
    elif format_type == "date-time":
        return fake.iso8601()
    elif format_type == "time":
        return fake.time()
    elif format_type == "email":
        return fake.email()
    elif format_type == "hostname":
        return fake.hostname()
    elif format_type == "ipv4":
        return fake.ipv4()
    elif format_type == "ipv6":
        return fake.ipv6()
    elif format_type == "uri":
        return fake.uri()
    elif format_type == "uuid":
        return fake.uuid4()
    elif format_type == "password":
        return fake.password()
    
    # Handle pattern
    if pattern:
        return fake.bothify(pattern.replace("\\", ""))
    
    # Use domain hint
    if domain_hint:
        if "name" in schema.get("description", "").lower() or "name" in domain_hint.lower():
            return fake.name()
        elif "email" in schema.get("description", "").lower():
            return fake.email()
        elif "phone" in schema.get("description", "").lower():
            return fake.phone_number()
        elif "address" in schema.get("description", "").lower():
            return fake.address()
        elif "company" in schema.get("description", "").lower():
            return fake.company()
    
    # Default string
    text = fake.text(max_nb_chars=max_length)
    if len(text) < min_length:
        text = text + "x" * (min_length - len(text))
    return text[:max_length]


def generate_number(schema: Dict[str, Any]) -> float:
    """Generate number based on schema"""
    minimum = schema.get("minimum", 0)
    maximum = schema.get("maximum", 1000000)
    exclusive_min = schema.get("exclusiveMinimum", False)
    exclusive_max = schema.get("exclusiveMaximum", False)
    multiple_of = schema.get("multipleOf")
    
    if exclusive_min:
        minimum += 0.01
    if exclusive_max:
        maximum -= 0.01
    
    value = random.uniform(minimum, maximum)
    
    if multiple_of:
        value = round(value / multiple_of) * multiple_of
    
    return value


def generate_integer(schema: Dict[str, Any]) -> int:
    """Generate integer based on schema"""
    minimum = schema.get("minimum", 0)
    maximum = schema.get("maximum", 1000000)
    exclusive_min = schema.get("exclusiveMinimum", False)
    exclusive_max = schema.get("exclusiveMaximum", False)
    multiple_of = schema.get("multipleOf")
    
    if exclusive_min:
        minimum += 1
    if exclusive_max:
        maximum -= 1
    
    value = random.randint(minimum, maximum)
    
    if multiple_of:
        value = round(value / multiple_of) * multiple_of
    
    return int(value)


def generate_array(schema: Dict[str, Any], domain_hint: Optional[str] = None) -> List[Any]:
    """Generate array based on schema"""
    min_items = schema.get("minItems", 0)
    max_items = schema.get("maxItems", 10)
    unique_items = schema.get("uniqueItems", False)
    item_schema = schema.get("items", {})
    
    count = random.randint(min_items, max_items)
    items = []
    
    for _ in range(count):
        item = generate_for_schema(item_schema, domain_hint)
        if unique_items and item in items:
            continue
        items.append(item)
    
    return items


def generate_object(schema: Dict[str, Any], domain_hint: Optional[str] = None) -> Dict[str, Any]:
    """Generate object based on schema"""
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    additional_properties = schema.get("additionalProperties", True)
    
    obj = {}
    
    # Add required properties
    for prop in required:
        if prop in properties:
            obj[prop] = generate_for_schema(properties[prop], domain_hint)
    
    # Add optional properties (50% chance)
    for prop, prop_schema in properties.items():
        if prop not in obj and random.random() > 0.5:
            obj[prop] = generate_for_schema(prop_schema, domain_hint)
    
    # Add additional properties if allowed
    if additional_properties and random.random() > 0.7:
        for _ in range(random.randint(1, 3)):
            key = fake.word()
            if key not in obj:
                obj[key] = fake.word()
    
    return obj


def generate_boundary_value(schema: Dict[str, Any]) -> Any:
    """Generate boundary test values"""
    schema_type = schema.get("type")
    
    if schema_type == "string":
        min_len = schema.get("minLength", 0)
        max_len = schema.get("maxLength", 1000)
        
        # Return boundary length strings
        choice = random.choice(["min", "max", "empty"])
        if choice == "min" and min_len > 0:
            return "x" * min_len
        elif choice == "max":
            return "x" * max_len
        else:
            return ""
    
    elif schema_type in ["number", "integer"]:
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        
        if minimum is not None and maximum is not None:
            return random.choice([minimum, maximum])
        elif minimum is not None:
            return minimum
        elif maximum is not None:
            return maximum
    
    elif schema_type == "array":
        min_items = schema.get("minItems", 0)
        max_items = schema.get("maxItems", 100)
        item_schema = schema.get("items", {})
        
        # Return boundary size arrays
        count = random.choice([min_items, max_items])
        return [generate_for_schema(item_schema) for _ in range(count)]
    
    return generate_for_schema(schema)


def generate_negative_value(schema: Dict[str, Any]) -> Any:
    """Generate negative test values (invalid data)"""
    schema_type = schema.get("type")
    
    # Type mismatches
    type_mismatches = {
        "string": 123,
        "number": "not_a_number",
        "integer": 3.14,
        "boolean": "yes",
        "array": "not_an_array",
        "object": "not_an_object"
    }
    
    if random.random() > 0.5 and schema_type in type_mismatches:
        return type_mismatches[schema_type]
    
    # Constraint violations
    if schema_type == "string":
        if "enum" in schema:
            return "invalid_enum_value"
        if "pattern" in schema:
            return "does_not_match_pattern"
        if "minLength" in schema:
            return "x" * (schema["minLength"] - 1) if schema["minLength"] > 0 else ""
        if "maxLength" in schema:
            return "x" * (schema["maxLength"] + 1)
    
    elif schema_type in ["number", "integer"]:
        if "minimum" in schema:
            return schema["minimum"] - 1
        if "maximum" in schema:
            return schema["maximum"] + 1
        if "multipleOf" in schema:
            return schema["multipleOf"] + 0.5
    
    elif schema_type == "array":
        if "minItems" in schema and schema["minItems"] > 0:
            return []
        if "maxItems" in schema:
            item_schema = schema.get("items", {})
            return [generate_for_schema(item_schema) for _ in range(schema["maxItems"] + 1)]
    
    elif schema_type == "object":
        required = schema.get("required", [])
        if required:
            # Return object missing required field
            obj = generate_object(schema)
            if required:
                del obj[required[0]]
            return obj
    
    # Default: return None
    return None