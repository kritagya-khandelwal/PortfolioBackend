#!/usr/bin/env python3
"""
Test script to verify streaming functionality
"""

import requests
import json
import time

def test_streaming():
    """Test the streaming endpoint"""
    url = "http://localhost:8000/stream"
    data = {"prompt": "Tell me a story about a robot learning to paint. Make it at least 200 words."}
    
    print("Testing streaming endpoint...")
    print("=" * 50)
    
    try:
        # Make streaming request
        response = requests.post(
            url,
            json=data,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        print("Response headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()
        
        # Process streaming response
        chunk_count = 0
        start_time = time.time()
        full_response = ""
        
        print("Receiving chunks:")
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        json_str = line[6:]  # Remove 'data: ' prefix
                        chunk = json.loads(json_str)
                        
                        if chunk['type'] == 'chunk':
                            content = chunk['content']
                            print(f"Chunk {chunk_count + 1}: '{content}' (length: {len(content)})")
                            full_response += content
                            chunk_count += 1
                        elif chunk['type'] == 'end':
                            print(f"\nEnd signal received after {chunk_count} chunks")
                            break
                        elif chunk['type'] == 'error':
                            print(f"Error: {chunk['error']}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw line: {line}")
                        continue
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print(f"Total chunks received: {chunk_count}")
        print(f"Total response length: {len(full_response)} characters")
        print(f"Total time: {duration:.2f} seconds")
        print(f"Average time per chunk: {duration/chunk_count:.3f} seconds" if chunk_count > 0 else "No chunks received")
        
        if chunk_count > 1:
            print("✅ Streaming appears to be working!")
        else:
            print("❌ Streaming may not be working - only one chunk received")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except KeyboardInterrupt:
        print("\nRequest interrupted by user")

if __name__ == "__main__":
    test_streaming() 