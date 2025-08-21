#!/usr/bin/env python3
"""Test AI vs Null provider generation"""

import asyncio
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

async def test_generation():
    print("🧪 Testing AI vs Null Provider Generation")
    print("=" * 60)
    
    # Load a simple API spec
    with open('examples/example1.json', 'r') as f:
        spec_content = f.read()
    
    spec = await load_openapi_spec(spec_content)
    normalized = normalize_openapi(spec)
    
    # Test with Null provider
    print("📊 Testing Null Provider...")
    null_provider = get_provider("null")
    null_cases = await null_provider.generate_cases(
        normalized.endpoints[0], 
        {"count": 3, "domain_hint": "testing"}
    )
    
    print(f"✅ Null provider generated {len(null_cases)} test cases")
    for i, case in enumerate(null_cases[:2]):
        print(f"  Case {i+1}: {case.name} - {case.test_type}")
        print(f"    Method: {case.method} {case.path}")
        print(f"    Expected: {case.expected_status}")
    
    # Test with AI provider (if available)
    print("\n🤖 Testing AI Provider...")
    ai_provider = get_provider()  # Auto-detect
    
    if ai_provider.__class__.__name__ != "NullProvider":
        print(f"✅ Using {ai_provider.__class__.__name__}")
        try:
            ai_cases = await ai_provider.generate_cases(
                normalized.endpoints[0],
                {"count": 3, "domain_hint": "testing"}
            )
            print(f"✅ AI provider generated {len(ai_cases)} test cases")
            for i, case in enumerate(ai_cases[:2]):
                print(f"  Case {i+1}: {case.name} - {case.test_type}")
                print(f"    Method: {case.method} {case.path}")
                print(f"    Expected: {case.expected_status}")
                if case.description:
                    print(f"    Description: {case.description[:50]}...")
        except Exception as e:
            print(f"❌ AI generation failed: {e}")
    else:
        print("❌ No AI provider available - check your API keys")

if __name__ == "__main__":
    asyncio.run(test_generation())
