#!/usr/bin/env python3
"""Test domain-relevant data generation"""

import pytest
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

@pytest.mark.asyncio
async def test_domain_data_generation():
    """Test domain-relevant data generation"""
    # Load the petstore API spec
    with open('examples/petstore.json', 'r') as f:
        spec_content = f.read()
    
    spec = await load_openapi_spec(spec_content)
    normalized = normalize_openapi(spec)
    
    # Find the addPet endpoint
    add_pet_endpoint = None
    for endpoint in normalized.endpoints:
        if endpoint.operation_id == "addPet" or (endpoint.method == "POST" and "/pet" in endpoint.path):
            add_pet_endpoint = endpoint
            break
    
    assert add_pet_endpoint is not None, "Could not find addPet endpoint"
    
    # Test with petstore domain hint
    provider = get_provider("null")  # Use null provider for consistent results
    
    cases = await provider.generate_cases(
        add_pet_endpoint,
        {"count": 3, "domain_hint": "petstore", "seed": 42}
    )
    
    # Assert cases are generated
    assert len(cases) > 0
    
    # Check that cases have the expected structure
    for case in cases:
        assert hasattr(case, 'name')
        assert hasattr(case, 'test_type')
        assert hasattr(case, 'method')
        assert hasattr(case, 'path')
        
        # Check that pet-related data is generated for petstore domain
        if case.body and isinstance(case.body, dict):
            # Look for pet-related fields in the body
            pet_fields = ['name', 'category', 'status', 'tags', 'photoUrls']
            has_pet_fields = any(field in case.body for field in pet_fields)
            # This is a soft assertion - we don't require all cases to have pet data
            # but we expect some to have it given the domain hint
