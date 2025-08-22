#!/usr/bin/env python3
"""
Simple load test script to demonstrate concurrent request handling
"""
import asyncio
import aiohttp
import time
from pathlib import Path

async def test_concurrent_requests(base_url: str, num_requests: int = 10):
    """Test concurrent request handling"""
    print(f"🚀 Testing {num_requests} concurrent requests to {base_url}")
    
    async def make_request(session, request_id):
        start_time = time.time()
        try:
            # Test the status endpoint (lightweight)
            async with session.get(f"{base_url}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    duration = time.time() - start_time
                    print(f"✅ Request {request_id}: {duration:.2f}s - {data['concurrent_requests']} active")
                    return True
                else:
                    print(f"❌ Request {request_id}: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Request {request_id}: Error - {e}")
            return False
    
    async with aiohttp.ClientSession() as session:
        # Create concurrent tasks
        tasks = [make_request(session, i) for i in range(num_requests)]
        
        # Execute all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Count successes
        successes = sum(1 for r in results if r is True)
        
        print(f"\n📊 Results:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Successful requests: {successes}/{num_requests}")
        print(f"   Average time per request: {total_time/num_requests:.2f}s")
        print(f"   Requests per second: {num_requests/total_time:.2f}")

async def test_generation_endpoint(base_url: str, num_requests: int = 3):
    """Test concurrent generation requests (heavier load)"""
    print(f"\n🔥 Testing {num_requests} concurrent generation requests")
    
    # Simple test spec
    test_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {"responses": {"200": {"description": "OK"}}}
            }
        }
    }
    
    import json
    import base64
    spec_content = base64.b64encode(json.dumps(test_spec).encode()).decode()
    
    async def make_generation_request(session, request_id):
        start_time = time.time()
        try:
            payload = {
                "openapi": spec_content,
                "casesPerEndpoint": 5,
                "outputs": ["json"],
                "aiSpeed": "fast"
            }
            
            async with session.post(f"{base_url}/api/generate", json=payload) as response:
                if response.status == 200:
                    duration = time.time() - start_time
                    print(f"✅ Generation {request_id}: {duration:.2f}s")
                    return True
                else:
                    print(f"❌ Generation {request_id}: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Generation {request_id}: Error - {e}")
            return False
    
    async with aiohttp.ClientSession() as session:
        tasks = [make_generation_request(session, i) for i in range(num_requests)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successes = sum(1 for r in results if r is True)
        
        print(f"\n📊 Generation Results:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Successful generations: {successes}/{num_requests}")
        print(f"   Average time per generation: {total_time/num_requests:.2f}s")

async def main():
    """Main test function"""
    base_url = "http://localhost:8080"  # Change to your deployed URL
    
    print("🧪 Concurrency Load Test")
    print("=" * 50)
    
    # Test 1: Lightweight concurrent requests
    await test_concurrent_requests(base_url, num_requests=20)
    
    # Test 2: Heavy generation requests
    await test_generation_endpoint(base_url, num_requests=5)
    
    print("\n🎉 Load test completed!")

if __name__ == "__main__":
    asyncio.run(main())
