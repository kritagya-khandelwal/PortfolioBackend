#!/usr/bin/env python3
"""
Script to check Redis values and connection status
"""

import redis
import os
import json
from datetime import datetime

def check_redis_connection():
    """Check Redis connection and basic info"""
    try:
        # Try to connect to Redis
        r = redis.Redis(
            host="localhost",
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # Test connection
        r.ping()
        print("✅ Redis connection successful!")
        
        # Get Redis info
        info = r.info()
        print(f"Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"Connected Clients: {info.get('connected_clients', 'Unknown')}")
        print(f"Used Memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"Total Keys: {info.get('db0', {}).get('keys', 'Unknown')}")
        
        return r
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return None

def check_rate_limit_keys(redis_client):
    """Check rate limiting keys in Redis"""
    if not redis_client:
        return
    
    print("\n🔍 Checking Rate Limit Keys:")
    print("=" * 40)
    
    # Get all keys
    all_keys = redis_client.keys("*")
    print(f"Total keys in Redis: {len(all_keys)}")
    
    # Filter rate limit keys
    rate_limit_keys = [key for key in all_keys if key.startswith("slowapi:")]
    
    if not rate_limit_keys:
        print("No rate limit keys found.")
        return
    
    print(f"Rate limit keys found: {len(rate_limit_keys)}")
    
    for key in rate_limit_keys:
        try:
            value = redis_client.get(key)
            ttl = redis_client.ttl(key)
            
            # Parse the key to get IP
            ip = key.replace("slowapi:", "")
            
            print(f"\nIP: {ip}")
            print(f"  Current requests: {value}")
            print(f"  TTL (seconds): {ttl}")
            
            if ttl > 0:
                # Calculate reset time
                reset_time = datetime.now().timestamp() + ttl
                reset_datetime = datetime.fromtimestamp(reset_time)
                print(f"  Reset time: {reset_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"Error reading key {key}: {e}")

def check_all_keys(redis_client):
    """Check all keys in Redis"""
    if not redis_client:
        return
    
    print("\n🔍 All Redis Keys:")
    print("=" * 40)
    
    all_keys = redis_client.keys("*")
    
    if not all_keys:
        print("No keys found in Redis.")
        return
    
    for key in all_keys:
        try:
            value = redis_client.get(key)
            ttl = redis_client.ttl(key)
            
            print(f"Key: {key}")
            print(f"  Value: {value}")
            print(f"  TTL: {ttl} seconds")
            print()
            
        except Exception as e:
            print(f"Error reading key {key}: {e}")

def clear_rate_limits(redis_client):
    """Clear all rate limit keys"""
    if not redis_client:
        return
    
    print("\n🗑️ Clearing Rate Limit Keys:")
    print("=" * 40)
    
    rate_limit_keys = redis_client.keys("slowapi:*")
    
    if not rate_limit_keys:
        print("No rate limit keys to clear.")
        return
    
    deleted = 0
    for key in rate_limit_keys:
        try:
            redis_client.delete(key)
            deleted += 1
            print(f"Deleted: {key}")
        except Exception as e:
            print(f"Error deleting {key}: {e}")
    
    print(f"\n✅ Deleted {deleted} rate limit keys.")

def main():
    """Main function"""
    print("Redis Checker for PortfolioBackend")
    print("=" * 50)
    
    # Check connection
    redis_client = check_redis_connection()
    
    if not redis_client:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure Redis is running:")
        print("   - Docker: docker run -d -p 6379:6379 redis:7-alpine")
        print("   - Local: brew install redis && redis-server")
        print("2. Check your .env file has correct Redis settings")
        print("3. If using Docker Compose, run: docker-compose up")
        return
    
    # Check rate limit keys
    check_rate_limit_keys(redis_client)
    
    # Check all keys (optional)
    print("\n" + "=" * 50)
    show_all = input("Show all Redis keys? (y/n): ").lower().strip()
    if show_all == 'y':
        check_all_keys(redis_client)
    
    # Option to clear rate limits
    print("\n" + "=" * 50)
    clear_limits = input("Clear all rate limits? (y/n): ").lower().strip()
    if clear_limits == 'y':
        clear_rate_limits(redis_client)

if __name__ == "__main__":
    main() 