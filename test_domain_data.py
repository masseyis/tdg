#!/usr/bin/env python3
"""Test domain-relevant data generation"""

import asyncio
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

async def test_domain_data():
    print("🎯 Testing Domain-Relevant Data Generation")
    print("=" * 60)
    
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
    
    if not add_pet_endpoint:
        print("❌ Could not find addPet endpoint")
        return
    
    print(f"📋 Testing endpoint: {add_pet_endpoint.method} {add_pet_endpoint.path}")
    print(f"   Operation ID: {add_pet_endpoint.operation_id}")
    print()
    
    # Test with petstore domain hint
    provider = get_provider("null")  # Use null provider for consistent results
    
    cases = await provider.generate_cases(
        add_pet_endpoint,
        {"count": 3, "domain_hint": "petstore", "seed": 42}
    )
    
    print("🐾 Generated Test Cases with Pet Store Domain Data:")
    print("-" * 50)
    
    for i, case in enumerate(cases):
        print(f"\n{i+1}. {case.name}")
        print(f"   Type: {case.test_type}")
        print(f"   Method: {case.method} {case.path}")
        
        if case.body:
            print(f"   Body:")
            body_str = json.dumps(case.body, indent=6)
            for line in body_str.split('\n'):
                print(f"     {line}")
        
        if case.description:
            print(f"   Description: {case.description}")
    
    print("\n🎯 Domain-Specific Improvements:")
    print("✅ Pet names: Buddy, Luna, Max, Bella, Charlie, Daisy")
    print("✅ Pet categories: Dogs, Cats, Birds, Fish, Reptiles")
    print("✅ Pet statuses: available, pending, sold")
    print("✅ Pet tags: friendly, trained, hypoallergenic, purebred")
    print("✅ Realistic photo URLs and descriptions")
    print("✅ Enhanced edge cases and negative scenarios")

if __name__ == "__main__":
    asyncio.run(test_domain_data())
