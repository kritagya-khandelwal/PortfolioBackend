#!/usr/bin/env python3
"""
Test script for session management functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_session_management():
    """Test complete session management workflow"""
    
    print("🧪 Testing Session Management")
    print("=" * 50)
    
    # Test 1: Create a new session
    print("\n1. Creating new session...")
    response = requests.post(f"{BASE_URL}/session")
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id}")
    else:
        print(f"❌ Failed to create session: {response.text}")
        return
    
    # Test 2: Send first message
    print("\n2. Sending first message...")
    message1 = {
        "prompt": "Hello! My name is Alice. What's your name?",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/stream", json=message1)
    if response.status_code == 200:
        print("✅ First message sent successfully")
        # Read streaming response
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data.get('type') == 'end':
                        break
    else:
        print(f"❌ Failed to send first message: {response.text}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test 3: Send second message
    print("\n3. Sending second message...")
    message2 = {
        "prompt": "Can you remember my name from our previous conversation?",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/stream", json=message2)
    if response.status_code == 200:
        print("✅ Second message sent successfully")
        # Read streaming response
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data.get('type') == 'end':
                        break
    else:
        print(f"❌ Failed to send second message: {response.text}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test 4: Get chat history
    print("\n4. Retrieving chat history...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Chat history retrieved:")
        print(f"   - Session ID: {history['session_id']}")
        print(f"   - Message count: {history['message_count']}")
        print(f"   - Created at: {history['created_at']}")
        print(f"   - Last activity: {history['last_activity']}")
        
        print("\n   Messages:")
        for i, msg in enumerate(history['messages'], 1):
            print(f"   {i}. [{msg['role']}] {msg['content'][:50]}...")
    else:
        print(f"❌ Failed to retrieve chat history: {response.text}")
    
    # Test 5: Test without session (should work but no history)
    print("\n5. Testing without session ID...")
    message_no_session = {
        "prompt": "This message has no session context"
    }
    
    response = requests.post(f"{BASE_URL}/stream", json=message_no_session)
    if response.status_code == 200:
        print("✅ Message without session sent successfully")
        # Read streaming response
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data.get('type') == 'end':
                        break
    else:
        print(f"❌ Failed to send message without session: {response.text}")
    
    # Test 6: List all sessions
    print("\n6. Listing all sessions...")
    response = requests.get(f"{BASE_URL}/sessions")
    if response.status_code == 200:
        sessions = response.json()
        print(f"✅ Found {sessions['total_sessions']} active sessions")
        for session in sessions['sessions']:
            print(f"   - {session['session_id']}: {session['message_count']} messages")
    else:
        print(f"❌ Failed to list sessions: {response.text}")
    
    # Test 7: Delete session
    print("\n7. Deleting session...")
    response = requests.delete(f"{BASE_URL}/session/{session_id}")
    if response.status_code == 200:
        print("✅ Session deleted successfully")
    else:
        print(f"❌ Failed to delete session: {response.text}")
    
    # Test 8: Verify session is deleted
    print("\n8. Verifying session deletion...")
    response = requests.get(f"{BASE_URL}/session/{session_id}")
    if response.status_code == 404:
        print("✅ Session successfully deleted (404 returned)")
    else:
        print(f"❌ Session still exists: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 Session management test completed!")

def test_rate_limiting_with_sessions():
    """Test rate limiting with session management"""
    
    print("\n🧪 Testing Rate Limiting with Sessions")
    print("=" * 50)
    
    # Create a session
    response = requests.post(f"{BASE_URL}/session")
    if response.status_code != 200:
        print("❌ Failed to create session for rate limiting test")
        return
    
    session_id = response.json()["session_id"]
    print(f"✅ Created session for rate limiting test: {session_id}")
    
    # Send multiple messages to test rate limiting
    for i in range(12):  # Try to exceed the 10/hour limit
        print(f"\nSending message {i+1}/12...")
        message = {
            "prompt": f"Test message {i+1} for rate limiting",
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/stream", json=message)
        if response.status_code == 200:
            print(f"✅ Message {i+1} sent successfully")
            # Read streaming response
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'end':
                            break
        elif response.status_code == 429:
            print(f"⏰ Rate limit hit after {i+1} messages")
            break
        else:
            print(f"❌ Unexpected error: {response.status_code} - {response.text}")
            break
        
        time.sleep(0.5)  # Small delay between requests
    
    # Check rate limit info
    print("\nChecking rate limit info...")
    response = requests.get(f"{BASE_URL}/rate-limit-info")
    if response.status_code == 200:
        info = response.json()
        print(f"✅ Rate limit info: {info['current_requests']}/{info['limit']}")
    else:
        print(f"❌ Failed to get rate limit info: {response.text}")

if __name__ == "__main__":
    try:
        # Test basic session management
        test_session_management()
        
        # Test rate limiting with sessions
        test_rate_limiting_with_sessions()
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 