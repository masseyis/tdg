"""Test case generation tests"""
import pytest
from app.ai.null_provider import NullProvider
from app.utils.openapi_normalizer import Endpoint, Parameter
from app.utils.faker_utils import set_seed


@pytest.mark.asyncio
async def test_null_provider_generation():
    """Test null provider generates cases"""
    provider = NullProvider()
    
    endpoint = Endpoint(
        path="/users/{id}",
        method="GET",
        operation_id="getUser",
        parameters=[
            Parameter(
                name="id",
                location="path",
                required=True,
                schema={"type": "integer"}
            )
        ]
    )
    
    options = {
        "count": 10,
        "seed": 42
    }
    
    cases = await provider.generate_cases(endpoint, options)
    
    assert len(cases) == 10
    assert any(c.test_type == "valid" for c in cases)
    assert any(c.test_type == "boundary" for c in cases)
    assert any(c.test_type == "negative" for c in cases)


def test_faker_with_seed():
    """Test faker generates reproducible data with seed"""
    from app.utils.faker_utils import generate_for_schema, set_seed
    
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 120}
        }
    }
    
    set_seed(42)
    data1 = generate_for_schema(schema)
    
    set_seed(42)
    data2 = generate_for_schema(schema)
    
    assert data1 == data2


def test_boundary_value_generation():
    """Test boundary value generation"""
    from app.utils.faker_utils import generate_boundary_value
    
    schema = {
        "type": "string",
        "minLength": 5,
        "maxLength": 10
    }
    
    for _ in range(10):
        value = generate_boundary_value(schema)
        assert len(value) in [0, 5, 10]


def test_negative_value_generation():
    """Test negative value generation"""
    from app.utils.faker_utils import generate_negative_value
    
    schema = {
        "type": "integer",
        "minimum": 0,
        "maximum": 100
    }
    
    value = generate_negative_value(schema)
    assert value is None or value < 0 or value > 100 or not isinstance(value, int)