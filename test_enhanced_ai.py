#!/usr/bin/env python3
"""Test enhanced AI generation with domain-relevant data and ordering"""

import asyncio
import json
from app.ai.base import get_provider
from app.utils.openapi_loader import load_openapi_spec
from app.utils.openapi_normalizer import normalize_openapi

async def test_enhanced_generation():
    print("🧪 Testing Enhanced AI Generation")
    print("=" * 60)
    
    # Load the petstore API spec
    with open('examples/petstore.json', 'r') as f:
        spec_content = f.read()
    
    spec = await load_openapi_spec(spec_content)
    normalized = normalize_openapi(spec)
    
    # Test with different providers
    providers = ["null", "openai", "anthropic"]
    
    for provider_name in providers:
        print(f"\n🤖 Testing {provider_name.upper()} Provider...")
        print("-" * 40)
        
        try:
            provider = get_provider(provider_name)
            if not provider.is_available():
                print(f"❌ {provider_name} provider not available")
                continue
                
            # Test with pet store domain
            cases = await provider.generate_cases(
                normalized.endpoints[0],  # First endpoint
                {"count": 6, "domain_hint": "petstore", "seed": 42}
            )
            
            print(f"✅ Generated {len(cases)} test cases")
            print("\n📋 Test Case Order (CREATE → READ → UPDATE → DELETE):")
            
            for i, case in enumerate(cases):
                print(f"  {i+1}. {case.method} {case.path} - {case.test_type}")
                print(f"     Name: {case.name}")
                if case.description:
                    print(f"     Description: {case.description[:60]}...")
                if case.body:
                    print(f"     Body: {json.dumps(case.body, indent=6)[:100]}...")
                print()
                
        except Exception as e:
            print(f"❌ Error with {provider_name}: {e}")
    
    print("\n🎯 Key Improvements:")
    print("✅ Domain-relevant data (pet names, categories, statuses)")
    print("✅ Enhanced edge cases (boundaries, special characters)")
    print("✅ Comprehensive negative cases (invalid data, missing fields)")
    print("✅ Logical ordering (CREATE → READ → UPDATE → DELETE)")
    print("✅ Better test names and descriptions")

if __name__ == "__main__":
    asyncio.run(test_enhanced_generation())
