"""Test case generation functionality"""

import pytest
from app.ai.null_provider import NullProvider
from app.generation.cases import create_test_data_json
from app.ai.base import TestCase


@pytest.mark.asyncio
async def test_null_provider_generation():
    """Test null provider generates valid test cases"""
    provider = NullProvider()
    
    # Create a mock endpoint
    from types import SimpleNamespace
    endpoint = SimpleNamespace()
    endpoint.method = "POST"
    endpoint.path = "/pets"
    endpoint.operation_id = "createPet"
    endpoint.parameters = []
    endpoint.request_body = {"type": "object", "properties": {"name": {"type": "string"}}}
    
    options = {"count": 3, "domain_hint": "petstore"}
    cases = await provider.generate_cases(endpoint, options)
    
    # The null provider generates valid, boundary, and negative cases
    # The exact count may vary based on the distribution logic
    assert len(cases) >= 3
    for case in cases:
        assert case.method == "POST"
        assert case.path == "/pets"
        assert case.test_type in ["valid", "boundary", "negative"]


def test_create_test_data_json():
    """Test create_test_data_json function with TestCase objects"""
    # Create test cases
    cases = [
        TestCase(
            name="Test case 1",
            description="A test case",
            method="POST",
            path="/pets",
            headers={"Content-Type": "application/json"},
            query_params={},
            path_params={},
            body={"name": "Fluffy"},
            expected_status=201,
            expected_response=None,
            test_type="valid"
        ),
        TestCase(
            name="Test case 2", 
            description="Another test case",
            method="GET",
            path="/pets/{id}",
            headers={},
            query_params={},
            path_params={"id": "123"},
            body=None,
            expected_status=200,
            expected_response=None,
            test_type="valid"
        )
    ]
    
    # Test the function that was failing
    test_data = create_test_data_json(cases)
    
    assert len(test_data) == 2
    assert test_data[0]["method"] == "POST"
    assert test_data[0]["path"] == "/pets"  # This should work now
    assert test_data[0]["body"] == {"name": "Fluffy"}
    assert test_data[1]["method"] == "GET"
    assert test_data[1]["path"] == "/pets/{id}"


@pytest.mark.asyncio
async def test_faker_with_seed():
    """Test faker generates consistent data with seed"""
    provider = NullProvider()
    
    from types import SimpleNamespace
    endpoint = SimpleNamespace()
    endpoint.method = "POST"
    endpoint.path = "/users"
    endpoint.operation_id = "createUser"
    endpoint.parameters = []
    endpoint.request_body = {"type": "object", "properties": {"name": {"type": "string"}}}
    
    # Generate with seed
    options = {"count": 2, "seed": 42}
    cases1 = await provider.generate_cases(endpoint, options)
    
    # Generate again with same seed
    cases2 = await provider.generate_cases(endpoint, options)
    
    # Should be identical
    assert len(cases1) == len(cases2)
    for c1, c2 in zip(cases1, cases2):
        assert c1.body == c2.body


@pytest.mark.asyncio
async def test_boundary_value_generation():
    """Test boundary value generation"""
    provider = NullProvider()
    
    from types import SimpleNamespace
    endpoint = SimpleNamespace()
    endpoint.method = "POST"
    endpoint.path = "/numbers"
    endpoint.operation_id = "createNumber"
    endpoint.parameters = []
    endpoint.request_body = {"type": "object", "properties": {"value": {"type": "integer", "minimum": 0, "maximum": 100}}}
    
    options = {"count": 5, "domain_hint": "numbers"}
    cases = await provider.generate_cases(endpoint, options)
    
    # Should have some boundary cases
    boundary_cases = [c for c in cases if c.test_type == "boundary"]
    assert len(boundary_cases) > 0


@pytest.mark.asyncio
async def test_negative_value_generation():
    """Test negative value generation"""
    provider = NullProvider()
    
    from types import SimpleNamespace
    endpoint = SimpleNamespace()
    endpoint.method = "POST"
    endpoint.path = "/users"
    endpoint.operation_id = "createUser"
    endpoint.parameters = []
    endpoint.request_body = {"type": "object", "properties": {"email": {"type": "string", "format": "email"}}}
    
    options = {"count": 5, "domain_hint": "users"}
    cases = await provider.generate_cases(endpoint, options)
    
    # Should have some negative cases
    negative_cases = [c for c in cases if c.test_type == "negative"]
    assert len(negative_cases) > 0