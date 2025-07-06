#!/usr/bin/env python3
"""
Focused test for function calling functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_function_calling():
    """Test function calling specifically"""
    print("🧪 Testing Function Calling")
    print("=" * 50)
    
    # Test 1: Simple calculation that should trigger a tool
    print("\n1. Testing calculation tool...")
    try:
        response = requests.post(f"{BASE_URL}/stream", 
                               json={"prompt": "Calculate 2 + 2 * 3"},
                               stream=True)
        
        if response.status_code == 200:
            print("✅ Request sent successfully")
            print("📝 Response:")
            
            tool_results = []
            content_chunks = []
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('type') == 'chunk':
                                content_chunks.append(data['content'])
                                print(data['content'], end='', flush=True)
                            elif data.get('type') == 'tool_result':
                                tool_results.append(data)
                                print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                            elif data.get('type') == 'end':
                                print()
                                break
                            elif data.get('type') == 'error':
                                print(f"\n❌ Error: {data['error']}")
                                break
                        except json.JSONDecodeError as e:
                            print(f"\n❌ JSON decode error: {e}")
                            print(f"Raw line: {line}")
                            continue
            
            print(f"\n📊 Summary:")
            print(f"   Content chunks: {len(content_chunks)}")
            print(f"   Tool results: {len(tool_results)}")
            
            if tool_results:
                print("✅ Function calling worked!")
            else:
                print("❌ No tool results found")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Current time request
    print("\n2. Testing time tool...")
    try:
        response = requests.post(f"{BASE_URL}/stream", 
                               json={"prompt": "What is the current time?"},
                               stream=True)
        
        if response.status_code == 200:
            print("✅ Request sent successfully")
            print("📝 Response:")
            
            tool_results = []
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('type') == 'chunk':
                                print(data['content'], end='', flush=True)
                            elif data.get('type') == 'tool_result':
                                tool_results.append(data)
                                print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                            elif data.get('type') == 'end':
                                print()
                                break
                        except json.JSONDecodeError:
                            continue
            
            if tool_results:
                print("✅ Time tool worked!")
            else:
                print("❌ No time tool results found")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test individual tool
    print("\n3. Testing individual tool execution...")
    try:
        response = requests.post(f"{BASE_URL}/tools/test", json={
            "tool_name": "calculate",
            "arguments": {"expression": "5 * 5"}
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Individual tool test: {result['result']}")
        else:
            print(f"❌ Individual tool test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: List available tools
    print("\n4. Listing available tools...")
    try:
        response = requests.get(f"{BASE_URL}/tools")
        
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ Found {tools['total_tools']} tools:")
            for tool in tools['tools']:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Failed to list tools: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        test_function_calling()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 