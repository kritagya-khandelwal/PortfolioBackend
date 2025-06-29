#!/usr/bin/env python3
"""
Test script to verify rate limiting functionality
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def test_rate_limit_info():
    """Test the rate limit info endpoint"""
    url = "http://localhost:8000/rate-limit-info"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Rate Limit Info:")
            print(f"  IP: {data.get('ip', 'N/A')}")
            print(f"  Current Requests: {data.get('current_requests', 0)}")
            print(f"  Limit: {data.get('limit', 'N/A')}")
            print(f"  Reset Time: {data.get('reset_time', 'N/A')}")
            return data
        else:
            print(f"Error: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting rate limit info: {e}")
        return None

def make_stream_request(prompt, request_id):
    """Make a single streaming request"""
    url = "http://localhost:8000/stream"
    data = {"prompt": prompt}
    
    try:
        response = requests.post(url, json=data, stream=True, timeout=30)
        
        if response.status_code == 200:
            # Count chunks received
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            chunk = json.loads(line[6:])
                            if chunk['type'] == 'chunk':
                                chunk_count += 1
                            elif chunk['type'] == 'end':
                                break
                        except json.JSONDecodeError:
                            continue
            
            print(f"Request {request_id}: Success - {chunk_count} chunks received")
            return True
        elif response.status_code == 429:
            print(f"Request {request_id}: Rate limited (429)")
            return False
        else:
            print(f"Request {request_id}: Error - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Request {request_id}: Exception - {e}")
        return False

def test_rate_limiting():
    """Test rate limiting by making multiple requests"""
    print("Testing Rate Limiting")
    print("=" * 50)
    
    # Get initial rate limit info
    print("Initial rate limit info:")
    test_rate_limit_info()
    print()
    
    # Make multiple requests to test rate limiting
    print("Making 15 requests (limit is 10/day):")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(15):
            future = executor.submit(make_stream_request, f"Test request {i+1}", i+1)
            futures.append(future)
        
        # Wait for all requests to complete
        results = [future.result() for future in futures]
    
    print()
    print("Results:")
    successful = sum(results)
    rate_limited = len(results) - successful
    print(f"  Successful requests: {successful}")
    print(f"  Rate limited requests: {rate_limited}")
    
    # Get final rate limit info
    print()
    print("Final rate limit info:")
    test_rate_limit_info()

def test_health_check():
    """Test health check endpoint"""
    url = "http://localhost:8000/health"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Health Check:")
            print(f"  Status: {data.get('status', 'N/A')}")
            print(f"  Service: {data.get('service', 'N/A')}")
            print(f"  Redis: {data.get('redis', 'N/A')}")
            return data
        else:
            print(f"Health check failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Health check error: {e}")
        return None

if __name__ == "__main__":
    print("PortfolioBackend Rate Limiting Test")
    print("=" * 50)
    
    # Test health check first
    print("Testing health check...")
    test_health_check()
    print()
    
    # Test rate limiting
    test_rate_limiting() 