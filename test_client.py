#!/usr/bin/env python3
"""
Test client for the PortfolioBackend API
This script demonstrates how to consume the streaming endpoint

Note: Make sure to install requests with: uv add requests
"""

import requests
import json
import sys

def test_streaming_api(prompt: str, base_url: str = "http://localhost:8000"):
    """
    Test the streaming API endpoint
    
    Args:
        prompt: The prompt to send to the LLM
        base_url: Base URL of the API server
    """
    url = f"{base_url}/stream"
    
    print(f"Sending prompt: '{prompt}'")
    print("=" * 50)
    
    try:
        # Make streaming request
        response = requests.post(
            url,
            json={"prompt": prompt},
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        # Process streaming response
        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        # Remove 'data: ' prefix and parse JSON
                        json_str = line[6:]
                        chunk = json.loads(json_str)
                        
                        if chunk['type'] == 'chunk':
                            content = chunk['content']
                            print(content, end='', flush=True)
                            full_response += content
                        elif chunk['type'] == 'end':
                            print("\n" + "=" * 50)
                            print("Stream completed successfully!")
                            break
                        elif chunk['type'] == 'error':
                            print(f"\nError: {chunk['error']}")
                            break
                            
                    except json.JSONDecodeError:
                        continue
        
        print(f"\nFull response length: {len(full_response)} characters")
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except KeyboardInterrupt:
        print("\nRequest interrupted by user")

def test_health_check(base_url: str = "http://localhost:8000"):
    """
    Test the health check endpoint
    
    Args:
        base_url: Base URL of the API server
    """
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")

def main():
    """Main function to run tests"""
    print("PortfolioBackend - Test Client")
    print("=" * 50)
    
    # Test health check first
    print("Testing health check...")
    test_health_check()
    print()
    
    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Write a short story about a robot learning to paint"
    
    # Test streaming API
    test_streaming_api(prompt)

if __name__ == "__main__":
    main() 