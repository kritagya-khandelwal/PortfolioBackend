#!/usr/bin/env python3
"""
Simple demonstration of tools/function calling functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def demo_tools():
    """Demonstrate tools functionality"""
    print("🚀 PortfolioBackend Tools Demo")
    print("=" * 50)
    
    # Create a session
    print("1. Creating session...")
    response = requests.post(f"{BASE_URL}/session")
    session_id = response.json()["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Demo questions that will trigger different tools
    demo_questions = [
        "What is the current time?",
        "Calculate 15 * 7 + 23",
        "Tell me about our conversation session",
        "What's the weather like in New York?"
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{i}. Asking: {question}")
        print("-" * 30)
        
        response = requests.post(f"{BASE_URL}/stream", 
                               json={"prompt": question, "session_id": session_id},
                               stream=True)
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8')[6:])  # Remove 'data: ' prefix
                if data.get('type') == 'chunk':
                    print(data['content'], end='', flush=True)
                elif data.get('type') == 'tool_result':
                    print(f"\n🔧 [Tool: {data['tool_name']}] {data['result']}")
                elif data.get('type') == 'end':
                    print()
                    break
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed! The LLM used various tools to answer your questions.")

if __name__ == "__main__":
    try:
        demo_tools()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Demo failed with error: {e}") 