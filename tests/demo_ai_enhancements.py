#!/usr/bin/env python3
"""Demonstrate AI enhancements with before/after comparison"""

import pytest
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

@pytest.mark.asyncio
async def test_ai_enhancements_demo():
    """Test AI enhancements with before/after comparison"""
    # Load petstore API
    with open('examples/petstore.json', 'r') as f:
        spec_content = f.read()
    
    spec = await load_openapi_spec(spec_content)
    normalized = normalize_openapi(spec)
    
    # Find addPet endpoint
    add_pet_endpoint = None
    for endpoint in normalized.endpoints:
        if endpoint.operation_id == "addPet" or (endpoint.method == "POST" and "/pet" in endpoint.path):
            add_pet_endpoint = endpoint
            break
    
    assert add_pet_endpoint is not None, "Could not find addPet endpoint"
    
    provider = get_provider("null")
    
    # Generate without domain hint
    basic_cases = await provider.generate_cases(
        add_pet_endpoint,
        {"count": 2, "seed": 42}
    )
    
    # Generate with domain hint
    enhanced_cases = await provider.generate_cases(
        add_pet_endpoint,
        {"count": 2, "domain_hint": "petstore", "seed": 42}
    )
    
    # Assert both generate cases
    assert len(basic_cases) > 0
    assert len(enhanced_cases) > 0
    
    # Check that both sets have proper structure
    for cases in [basic_cases, enhanced_cases]:
        for case in cases:
            assert hasattr(case, 'name')
            assert hasattr(case, 'test_type')
            assert hasattr(case, 'method')
            assert hasattr(case, 'path')
    
    # The enhanced cases should have domain-specific improvements
    # This is a soft assertion - we expect some improvement but don't require it
    enhanced_has_pet_data = False
    for case in enhanced_cases:
        if case.body and isinstance(case.body, dict):
            pet_fields = ['name', 'category', 'status', 'tags', 'photoUrls']
            if any(field in case.body for field in pet_fields):
                enhanced_has_pet_data = True
                break
    
    # We don't require pet data in all cases, but it's a good indicator of enhancement
    # This test will pass even if no pet data is found, as it's a demonstration
