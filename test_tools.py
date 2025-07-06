#!/usr/bin/env python3
"""
Test script for tools/function calling functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_list_tools():
    """Test listing available tools"""
    print("🧪 Testing Tools Listing")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/tools")
        if response.status_code == 200:
            tools_data = response.json()
            print(f"✅ Found {tools_data['total_tools']} tools:")
            
            for tool in tools_data['tools']:
                print(f"\n🔧 {tool['name']}")
                print(f"   Description: {tool['description']}")
                print(f"   Parameters: {json.dumps(tool['parameters'], indent=2)}")
        else:
            print(f"❌ Failed to list tools: {response.text}")
    except Exception as e:
        print(f"❌ Error listing tools: {e}")

def test_individual_tools():
    """Test individual tools"""
    print("\n🧪 Testing Individual Tools")
    print("=" * 50)
    
    # Test current time
    print("\n1. Testing get_current_time...")
    try:
        response = requests.post(f"{BASE_URL}/tools/test", json={
            "tool_name": "get_current_time",
            "arguments": {"timezone": "UTC"}
        })
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['result']}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test calculator
    print("\n2. Testing calculate...")
    try:
        response = requests.post(f"{BASE_URL}/tools/test", json={
            "tool_name": "calculate",
            "arguments": {"expression": "2 + 2 * 3"}
        })
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['result']}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test weather
    print("\n3. Testing get_weather...")
    try:
        response = requests.post(f"{BASE_URL}/tools/test", json={
            "tool_name": "get_weather",
            "arguments": {"location": "New York"}
        })
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['result']}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_function_calling_with_session():
    """Test function calling with session management"""
    print("\n🧪 Testing Function Calling with Session")
    print("=" * 50)
    
    # Create a session
    print("1. Creating session...")
    try:
        response = requests.post(f"{BASE_URL}/session")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return
    
    # Test 1: Ask for current time
    print("\n2. Testing function calling - asking for current time...")
    message1 = {
        "prompt": "What is the current time?",
        "session_id": session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/stream", json=message1, stream=True)
        if response.status_code == 200:
            print("✅ Time request sent successfully")
            print("📝 Response:")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'chunk':
                            print(data['content'], end='', flush=True)
                        elif data.get('type') == 'tool_result':
                            print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                        elif data.get('type') == 'end':
                            print()
                            break
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(1)
    
    # Test 2: Ask for calculation
    print("\n3. Testing function calling - asking for calculation...")
    message2 = {
        "prompt": "Calculate 15 * 7 + 23",
        "session_id": session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/stream", json=message2, stream=True)
        if response.status_code == 200:
            print("✅ Calculation request sent successfully")
            print("📝 Response:")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'chunk':
                            print(data['content'], end='', flush=True)
                        elif data.get('type') == 'tool_result':
                            print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                        elif data.get('type') == 'end':
                            print()
                            break
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(1)
    
    # Test 3: Ask for session info
    print("\n4. Testing function calling - asking for session info...")
    message3 = {
        "prompt": "Tell me about our current conversation session",
        "session_id": session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/stream", json=message3, stream=True)
        if response.status_code == 200:
            print("✅ Session info request sent successfully")
            print("📝 Response:")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'chunk':
                            print(data['content'], end='', flush=True)
                        elif data.get('type') == 'tool_result':
                            print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                        elif data.get('type') == 'end':
                            print()
                            break
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Get session history to see tool results
    print("\n5. Checking session history...")
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Session history retrieved:")
            print(f"   - Message count: {history['message_count']}")
            
            print("\n   Messages:")
            for i, msg in enumerate(history['messages'], 1):
                print(f"   {i}. [{msg['role']}] {msg['content'][:100]}...")
        else:
            print(f"❌ Failed to retrieve history: {response.text}")
    except Exception as e:
        print(f"❌ Error retrieving history: {e}")
    
    # Clean up
    print("\n6. Cleaning up - deleting session...")
    try:
        response = requests.delete(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            print("✅ Session deleted successfully")
        else:
            print(f"❌ Failed to delete session: {response.text}")
    except Exception as e:
        print(f"❌ Error deleting session: {e}")

def test_complex_tool_usage():
    """Test more complex tool usage scenarios"""
    print("\n🧪 Testing Complex Tool Usage")
    print("=" * 50)
    
    # Create a session
    print("1. Creating session for complex testing...")
    try:
        response = requests.post(f"{BASE_URL}/session")
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
        else:
            print(f"❌ Failed to create session: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return
    
    # Test multiple tools in one request
    print("\n2. Testing multiple tools in one request...")
    message = {
        "prompt": "What's the current time, calculate 25 squared, and tell me about our conversation session",
        "session_id": session_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/stream", json=message, stream=True)
        if response.status_code == 200:
            print("✅ Complex request sent successfully")
            print("📝 Response:")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'chunk':
                            print(data['content'], end='', flush=True)
                        elif data.get('type') == 'tool_result':
                            print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                        elif data.get('type') == 'end':
                            print()
                            break
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Clean up
    print("\n3. Cleaning up...")
    try:
        response = requests.delete(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            print("✅ Session deleted successfully")
        else:
            print(f"❌ Failed to delete session: {response.text}")
    except Exception as e:
        print(f"❌ Error deleting session: {e}")

if __name__ == "__main__":
    print("🚀 PortfolioBackend Tools Test Client")
    print("=" * 50)
    
    try:
        # Test tools listing
        test_list_tools()
        
        # Test individual tools
        test_individual_tools()
        
        # Test function calling with session
        test_function_calling_with_session()
        
        # Test complex tool usage
        test_complex_tool_usage()
        
        print("\n" + "=" * 50)
        print("🎉 All tools tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 