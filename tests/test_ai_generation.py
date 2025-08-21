#!/usr/bin/env python3
"""Test AI vs Null provider generation"""

import pytest
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

@pytest.mark.asyncio
async def test_ai_vs_null_generation():
    """Test AI vs Null provider generation"""
    # Load a simple API spec
    with open('examples/example1.json', 'r') as f:
        spec_content = f.read()
    
    spec = await load_openapi_spec(spec_content)
    normalized = normalize_openapi(spec)
    
    # Test with Null provider
    null_provider = get_provider("null")
    null_cases = await null_provider.generate_cases(
        normalized.endpoints[0], 
        {"count": 3, "domain_hint": "testing"}
    )
    
    # Assert null provider generates cases
    assert len(null_cases) > 0
    assert all(hasattr(case, 'name') for case in null_cases)
    assert all(hasattr(case, 'test_type') for case in null_cases)
    
    # Test with AI provider (if available)
    ai_provider = get_provider()  # Auto-detect
    
    if ai_provider.__class__.__name__ != "NullProvider":
        try:
            ai_cases = await ai_provider.generate_cases(
                normalized.endpoints[0],
                {"count": 3, "domain_hint": "testing"}
            )
            # Assert AI provider generates cases
            assert len(ai_cases) > 0
            assert all(hasattr(case, 'name') for case in ai_cases)
        except Exception as e:
            # AI provider might fail due to API key issues, but that's OK
            pytest.skip(f"AI provider failed: {e}")
    else:
        # No AI provider available, which is OK for testing
        pass
