#!/usr/bin/env python3
"""
Simple test client for the PortfolioBackend API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_basic_streaming():
    """Test basic streaming without session"""
    print("🧪 Testing Basic Streaming (No Session)")
    print("=" * 50)
    
    url = f"{BASE_URL}/stream"
    data = {"prompt": "Tell me a short story about a robot in exactly 2 sentences."}
    
    print(f"Sending request to {url}")
    print(f"Prompt: {data['prompt']}")
    print("\nResponse:")
    
    try:
        response = requests.post(url, json=data, stream=True)
        
        if response.status_code == 200:
            print("✅ Stream started successfully")
            print("📝 Content:")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        json_str = line[6:]  # Remove 'data: ' prefix
                        try:
                            chunk = json.loads(json_str)
                            if chunk['type'] == 'chunk':
                                print(chunk['content'], end='', flush=True)
                            elif chunk['type'] == 'end':
                                print()  # New line at end
                                break
                            elif chunk['type'] == 'error':
                                print(f"\n❌ Error: {chunk['error']}")
                                break
                        except json.JSONDecodeError:
                            continue
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_session_streaming():
    """Test streaming with session management"""
    print("\n🧪 Testing Session Management")
    print("=" * 50)
    
    # Step 1: Create a new session
    print("1. Creating new session...")
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
    
    # Step 2: Send first message with session
    print("\n2. Sending first message with session...")
    url = f"{BASE_URL}/stream"
    data = {
        "prompt": "Hello! My name is Alice. What's your name?",
        "session_id": session_id
    }
    
    print(f"Prompt: {data['prompt']}")
    print("Response:")
    
    try:
        response = requests.post(url, json=data, stream=True)
        
        if response.status_code == 200:
            print("✅ First message sent successfully")
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        json_str = line[6:]
                        try:
                            chunk = json.loads(json_str)
                            if chunk['type'] == 'chunk':
                                content = chunk['content']
                                print(content, end='', flush=True)
                                full_response += content
                            elif chunk['type'] == 'end':
                                print()
                                break
                            elif chunk['type'] == 'error':
                                print(f"\n❌ Error: {chunk['error']}")
                                break
                        except json.JSONDecodeError:
                            continue
        else:
            print(f"❌ First message failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error sending first message: {e}")
        return
    
    # Step 3: Send second message (should remember context)
    print("\n3. Sending second message (testing context)...")
    data = {
        "prompt": "Can you remember my name from our previous conversation?",
        "session_id": session_id
    }
    
    print(f"Prompt: {data['prompt']}")
    print("Response:")
    
    try:
        response = requests.post(url, json=data, stream=True)
        
        if response.status_code == 200:
            print("✅ Second message sent successfully")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        json_str = line[6:]
                        try:
                            chunk = json.loads(json_str)
                            if chunk['type'] == 'chunk':
                                print(chunk['content'], end='', flush=True)
                            elif chunk['type'] == 'end':
                                print()
                                break
                            elif chunk['type'] == 'error':
                                print(f"\n❌ Error: {chunk['error']}")
                                break
                        except json.JSONDecodeError:
                            continue
        else:
            print(f"❌ Second message failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending second message: {e}")
    
    # Step 4: Get session history
    print("\n4. Retrieving session history...")
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Session history retrieved:")
            print(f"   - Message count: {history['message_count']}")
            print(f"   - Created at: {history['created_at']}")
            print(f"   - Last activity: {history['last_activity']}")
            
            print("\n   Messages:")
            for i, msg in enumerate(history['messages'], 1):
                print(f"   {i}. [{msg['role']}] {msg['content'][:50]}...")
        else:
            print(f"❌ Failed to retrieve history: {response.text}")
    except Exception as e:
        print(f"❌ Error retrieving history: {e}")
    
    # Step 5: Clean up - delete session
    print("\n5. Cleaning up - deleting session...")
    try:
        response = requests.delete(f"{BASE_URL}/session/{session_id}")
        if response.status_code == 200:
            print("✅ Session deleted successfully")
        else:
            print(f"❌ Failed to delete session: {response.text}")
    except Exception as e:
        print(f"❌ Error deleting session: {e}")

def test_health_and_rate_limits():
    """Test health check and rate limit info"""
    print("\n🧪 Testing Health and Rate Limits")
    print("=" * 50)
    
    # Health check
    print("1. Health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health: {health['status']}")
            print(f"   Redis: {health['redis']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking health: {e}")
    
    # Rate limit info
    print("\n2. Rate limit info...")
    try:
        response = requests.get(f"{BASE_URL}/rate-limit-info")
        if response.status_code == 200:
            rate_info = response.json()
            print(f"✅ Rate limit info:")
            print(f"   IP: {rate_info['ip']}")
            print(f"   Current requests: {rate_info['current_requests']}")
            print(f"   Limit: {rate_info['limit']}")
        else:
            print(f"❌ Rate limit info failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting rate limit info: {e}")

if __name__ == "__main__":
    print("🚀 PortfolioBackend Test Client")
    print("=" * 50)
    
    # Test basic functionality
    test_basic_streaming()
    
    # Test session management
    test_session_streaming()
    
    # Test health and rate limits
    test_health_and_rate_limits()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!") 