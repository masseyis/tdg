#!/usr/bin/env python3
"""Demonstrate AI enhancements with before/after comparison"""

import asyncio
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

async def demo_enhancements():
    print("🚀 AI Test Generation Enhancements Demo")
    print("=" * 60)
    
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
    
    if not add_pet_endpoint:
        print("❌ Could not find addPet endpoint")
        return
    
    provider = get_provider("null")
    
    print("📊 BEFORE: Basic test generation (no domain hint)")
    print("-" * 50)
    
    # Generate without domain hint
    basic_cases = await provider.generate_cases(
        add_pet_endpoint,
        {"count": 2, "seed": 42}
    )
    
    for i, case in enumerate(basic_cases):
        print(f"{i+1}. {case.name}")
        if case.body:
            print(f"   Body: {json.dumps(case.body, indent=4)}")
        print()
    
    print("🎯 AFTER: Enhanced test generation (with petstore domain)")
    print("-" * 50)
    
    # Generate with domain hint
    enhanced_cases = await provider.generate_cases(
        add_pet_endpoint,
        {"count": 2, "domain_hint": "petstore", "seed": 42}
    )
    
    for i, case in enumerate(enhanced_cases):
        print(f"{i+1}. {case.name}")
        if case.body:
            print(f"   Body: {json.dumps(case.body, indent=4)}")
        print()
    
    print("🔍 Key Improvements:")
    print("✅ Domain-relevant pet names and categories")
    print("✅ Realistic pet statuses and tags")
    print("✅ Better test case ordering (CREATE → READ → UPDATE → DELETE)")
    print("✅ Enhanced edge cases and negative scenarios")
    print("✅ More descriptive test names and descriptions")
    
    print("\n🎯 Test Case Ordering:")
    print("1. POST (CREATE) operations")
    print("2. GET (READ) operations")
    print("3. PUT/PATCH (UPDATE) operations")
    print("4. DELETE operations")
    print("   Within each: Valid → Boundary → Negative")

if __name__ == "__main__":
    asyncio.run(demo_enhancements())
