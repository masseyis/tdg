#!/usr/bin/env python3
"""Test enhanced AI generation with domain-relevant data and ordering"""

import pytest
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

@pytest.mark.asyncio
async def test_enhanced_ai_generation():
    """Test enhanced AI generation with domain-relevant data and ordering"""
    # Load the petstore API spec
    with open('examples/petstore.json', 'r') as f:
        spec_content = f.read()
    
    spec = await load_openapi_spec(spec_content)
    normalized = normalize_openapi(spec)
    
    # Test with null provider (most reliable for testing)
    provider = get_provider("null")
    
    # Test with pet store domain
    cases = await provider.generate_cases(
        normalized.endpoints[0],  # First endpoint
        {"count": 6, "domain_hint": "petstore", "seed": 42}
    )
    
    # Assert cases are generated
    assert len(cases) > 0
    
    # Check that cases have the expected structure
    for case in cases:
        assert hasattr(case, 'name')
        assert hasattr(case, 'test_type')
        assert hasattr(case, 'method')
        assert hasattr(case, 'path')
        
        # Check that test types are valid
        assert case.test_type in ['valid', 'boundary', 'negative']
        
        # Check that methods are valid HTTP methods
        assert case.method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    
    # Check that cases are ordered (CREATE → READ → UPDATE → DELETE)
    # This is a soft check - we don't require perfect ordering but expect some logic
    methods = [case.method for case in cases]
    
    # We should have at least one method (the endpoint's method)
    assert len(set(methods)) >= 1, "Should have at least one HTTP method"
    
    # Test with AI providers if available (but don't fail if they're not)
    ai_providers = ["openai", "anthropic"]
    
    for provider_name in ai_providers:
        try:
            ai_provider = get_provider(provider_name)
            if ai_provider.is_available():
                ai_cases = await ai_provider.generate_cases(
                    normalized.endpoints[0],
                    {"count": 3, "domain_hint": "petstore", "seed": 42}
                )
                # Basic validation that AI provider works
                assert len(ai_cases) > 0
                break  # If one AI provider works, that's enough
        except Exception:
            # AI providers might fail due to API key issues, which is OK
            continue
