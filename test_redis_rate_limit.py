#!/usr/bin/env python3
"""
Simple test to verify Redis rate limiting is working
"""

import requests
import redis
import time
import os

def test_rate_limit_creation():
    """Test that rate limit keys are created in Redis"""
    
    # Connect to Redis
    r = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True
    )
    
    print("🔍 Testing Rate Limit Creation")
    print("=" * 40)
    
    # Clear any existing rate limit keys
    rate_limit_keys = r.keys("slowapi:*")
    if rate_limit_keys:
        print(f"Clearing {len(rate_limit_keys)} existing rate limit keys...")
        for key in rate_limit_keys:
            r.delete(key)
    
    # Check initial state
    print("\n1. Initial Redis state:")
    all_keys = r.keys("*")
    print(f"   Total keys: {len(all_keys)}")
    rate_limit_keys = r.keys("slowapi:*")
    print(f"   Rate limit keys: {len(rate_limit_keys)}")
    
    # Make a request to trigger rate limiting
    print("\n2. Making API request to trigger rate limiting...")
    try:
        response = requests.post(
            "http://localhost:8000/stream",
            json={"prompt": "Hello, this is a test"},
            timeout=10
        )
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Request successful")
        elif response.status_code == 429:
            print("   ⚠️ Rate limited (expected if limit exceeded)")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Wait a moment for Redis to update
    time.sleep(1)
    
    # Check Redis after request
    print("\n3. Redis state after request:")
    all_keys = r.keys("*")
    print(f"   Total keys: {len(all_keys)}")
    rate_limit_keys = r.keys("slowapi:*")
    print(f"   Rate limit keys: {len(rate_limit_keys)}")
    
    if rate_limit_keys:
        print("\n4. Rate limit key details:")
        for key in rate_limit_keys:
            value = r.get(key)
            ttl = r.ttl(key)
            ip = key.replace("slowapi:", "")
            print(f"   IP: {ip}")
            print(f"   Value: {value}")
            print(f"   TTL: {ttl} seconds")
            print()
    else:
        print("\n❌ No rate limit keys found! Rate limiting may not be working.")
    
    # Test rate limit info endpoint
    print("\n5. Testing rate limit info endpoint:")
    try:
        info_response = requests.get("http://localhost:8000/rate-limit-info")
        print(f"   Status: {info_response.status_code}")
        if info_response.status_code == 200:
            info_data = info_response.json()
            print(f"   IP: {info_data.get('ip')}")
            print(f"   Current requests: {info_data.get('current_requests')}")
            print(f"   Limit: {info_data.get('limit')}")
        else:
            print(f"   Error: {info_response.text}")
    except Exception as e:
        print(f"   ❌ Rate limit info request failed: {e}")

if __name__ == "__main__":
    test_rate_limit_creation() 