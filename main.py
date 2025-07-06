from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import json
import time
import uuid
import requests
import datetime
from typing import AsyncGenerator, List, Optional, Dict, Any
import dotenv
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from .env if present
dotenv.load_dotenv()

# Debug Redis connection settings
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

print(f"🔍 Redis connection settings:")
print(f"   Host: {redis_host}")
print(f"   Port: {redis_port}")
print(f"   DB: {redis_db}")

# Initialize Redis client
redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=redis_db,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="PortfolioBackend",
    description="A FastAPI service that streams responses from OpenAI LLM",
    version="1.0.0"
)

# Add rate limiting exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Request model
class PromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

# Initialize OpenAI client
client = openai.OpenAI()

# Tools definitions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'America/New_York')",
                        "default": "UTC"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates (e.g., 'New York', 'London', '40.7128,-74.0060')"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(45)')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_session_info",
            "description": "Get information about the current chat session",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to get info for"
                    }
                },
                "required": ["session_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Create a reminder for a specific time",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Reminder title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Reminder description"
                    },
                    "datetime": {
                        "type": "string",
                        "description": "Reminder datetime (ISO format: YYYY-MM-DDTHH:MM:SS)"
                    }
                },
                "required": ["title", "datetime"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The email address of this user"
                    },
                    "name": {
                        "type": "string",
                        "description": "The user's name, if they provided it"
                    }
                    ,
                    "notes": {
                        "type": "string",
                        "description": "Any additional information about the conversation that's worth recording to give context"
                    }
                },
                "required": ["email"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Use this tool to record that a user asked a question that I couldn't answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question that couldn't be answered"
                    }
                },
                "required": ["question"]
            }
        }
    }
]

# Tool functions

def push(message):
    """Push a message to Kritagya Khandelwal"""
    try:
        print(f"Push: {message}")
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        requests.post(pushover_url, data=payload)
    except Exception as e:
        print(f"Error pushing to Pushover: {e}")

def record_user_details(email, name="Name not provided", notes="not provided"):
    """Record user details"""
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return "Interest recorded"

def record_unknown_question(question):
    """Record unknown question"""
    push(f"Recording {question} asked that I couldn't answer")
    return "Question recorded"

def get_current_time(timezone: str = "UTC") -> str:
    """Get current date and time"""
    try:
        now = datetime.datetime.now()
        return f"Current time ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Error getting time: {str(e)}"

def get_weather(location: str) -> str:
    """Get weather information for a location"""
    try:
        # Using a free weather API (you might want to use a different one)
        # This is a mock implementation - replace with actual API
        return f"Weather for {location}: 72°F, Partly Cloudy (Mock data - replace with actual weather API)"
    except Exception as e:
        return f"Error getting weather: {str(e)}"

def calculate(expression: str) -> str:
    """Perform mathematical calculations"""
    try:
        # Safe evaluation of mathematical expressions
        allowed_names = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'len': len, 'pow': pow
        }
        
        # Remove any potentially dangerous characters
        expression = ''.join(c for c in expression if c.isalnum() or c in '+-*/.() ')
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

def web_search(query: str) -> str:
    """Search the web for information"""
    try:
        # This is a mock implementation - replace with actual search API
        return f"Search results for '{query}': (Mock data - replace with actual search API like Google Custom Search or DuckDuckGo)"
    except Exception as e:
        return f"Error searching: {str(e)}"

def get_session_info(session_id: str) -> str:
    """Get information about a chat session"""
    try:
        session_data = get_session(session_id)
        if session_data:
            message_count = len(session_data.get("messages", []))
            created_at = datetime.datetime.fromtimestamp(session_data["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            last_activity = datetime.datetime.fromtimestamp(session_data["last_activity"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            return f"Session Info:\n- Message count: {message_count}\n- Created: {created_at}\n- Last activity: {last_activity}"
        else:
            return f"Session {session_id} not found"
    except Exception as e:
        return f"Error getting session info: {str(e)}"

def create_reminder(title: str, datetime_str: str, description: str = "") -> str:
    """Create a reminder"""
    try:
        # Parse datetime
        reminder_time = datetime.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        now = datetime.datetime.now(reminder_time.tzinfo)
        
        if reminder_time > now:
            time_diff = reminder_time - now
            return f"Reminder created: '{title}' for {datetime_str}\nTime until reminder: {time_diff}"
        else:
            return f"Reminder created: '{title}' for {datetime_str}\nNote: This time has already passed"
    except Exception as e:
        return f"Error creating reminder: {str(e)}"

# Tool execution function
def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool function"""
    tool_functions = {
        "get_current_time": get_current_time,
        "get_weather": get_weather,
        "calculate": calculate,
        "web_search": web_search,
        "get_session_info": get_session_info,
        "create_reminder": create_reminder,
        "record_user_details": record_user_details,
        "record_unknown_question": record_unknown_question
    }
    
    if tool_name in tool_functions:
        try:
            return tool_functions[tool_name](**arguments)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    else:
        return f"Unknown tool: {tool_name}"

def load_system_prompt() -> str:
    """
    Load system prompt from external files
    """
    try:
        # Load the system prompt instructions
        system_prompt_path = "data/system_prompt.md"
        
        system_prompt = ""
        
        # Read system prompt if it exists
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
        
        if system_prompt:
            return f"{system_prompt}"
        else:
            raise FileNotFoundError("system_prompt.md not found")
            
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        # Fallback to a minimal prompt
        return "You are an AI assistant. Please respond to user queries."

# Load system prompt once at startup
SYSTEM_PROMPT = load_system_prompt()

# Session management functions
def create_session() -> str:
    """
    Create a new session and return session ID
    """
    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "created_at": int(time.time() * 1000),
        "last_activity": int(time.time() * 1000),
        "messages": []
    }
    
    # Store session in Redis with 24-hour TTL
    redis_client.setex(
        f"chat:session:{session_id}",
        86400,  # 24 hours in seconds
        json.dumps(session_data)
    )
    
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    """
    Retrieve session data from Redis
    """
    try:
        session_data = redis_client.get(f"chat:session:{session_id}")
        # print("session_data", session_data)
        if session_data:
            return json.loads(session_data)
        return None
    except Exception as e:
        print(f"Error retrieving session {session_id}: {e}")
        return None

def save_message(session_id: str, role: str, content: str):
    """
    Save a message to the session
    """
    try:
        session_data = get_session(session_id)
        if not session_data:
            return
        
        # Add new message
        message = {
            "role": role,
            "content": content,
            "timestamp": int(time.time() * 1000)
        }
        
        session_data["messages"].append(message)
        session_data["last_activity"] = int(time.time() * 1000)
        
        # Keep only last 20 messages
        if len(session_data["messages"]) > 20:
            session_data["messages"] = session_data["messages"][-20:]
        
        # Update session in Redis (refresh TTL)
        redis_client.setex(
            f"chat:session:{session_id}",
            86400,  # 24 hours in seconds
            json.dumps(session_data)
        )
        
    except Exception as e:
        print(f"Error saving message to session {session_id}: {e}")

def get_chat_history(session_id: str) -> List[dict]:
    """
    Get chat history for a session (last 20 messages)
    """
    session_data = get_session(session_id)
    if session_data:
        return session_data.get("messages", [])
    return []

async def stream_openai_response(prompt: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Stream response from OpenAI LLM with session support and function calling
    """
    try:
        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add chat history if session exists
        if session_id:
            chat_history = get_chat_history(session_id)
            messages.extend(chat_history)
        
        # Add current user message
        messages.append({"role": "user", "content": prompt})
        
        # Save user message to session
        if session_id:
            save_message(session_id, "user", prompt)
        
        # First, try to get a response with potential tool calls
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message
        messages.append(assistant_message)
        
        # Check if there are tool calls
        if assistant_message.tool_calls:
            print(f"🔧 Tool calls detected: {len(assistant_message.tool_calls)}")
            # Execute tool calls
            tool_results = []
            for tool_call in assistant_message.tool_calls:
                try:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 Executing tool: {function_name} with args: {arguments}")
                    
                    # Execute the tool
                    result = execute_tool(function_name, arguments)
                    
                    print(f"🔧 Tool result: {result}")
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": result
                    })
                    
                    # Send tool result as a special chunk
                    timestamp = int(time.time() * 1000)
                    tool_data = json.dumps({
                        'content': f"[Tool Result: {function_name}] {result}",
                        'type': 'tool_result',
                        'tool_name': function_name,
                        'result': result,
                        'timestamp': timestamp
                    }, ensure_ascii=False)
                    yield f"data: {tool_data}\n\n"
                    
                except Exception as e:
                    print(f"❌ Error executing tool {function_name}: {e}")
                    error_result = f"Error executing tool {function_name}: {str(e)}"
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": error_result
                    })
            
            # Add tool results to messages
            messages.extend(tool_results)
            
            # Get final response from OpenAI (streaming)
            final_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=500
            )
            
            # Stream the final response
            for chunk in final_response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    timestamp = int(time.time() * 1000)
                    json_data = json.dumps({'content': content, 'type': 'chunk', 'timestamp': timestamp}, ensure_ascii=False)
                    yield f"data: {json_data}\n\n"
            
            # Save the complete response
            if session_id:
                complete_response = assistant_message.content or ""
                if tool_results:
                    complete_response += "\n\n[Tool Results:]\n"
                    for result in tool_results:
                        complete_response += f"- {result['content']}\n"
                # Add the final response content
                complete_response += response.choices[0].message.content or ""
                save_message(session_id, "assistant", complete_response)
        else:
            print("📝 No tool calls detected")
            # No tool calls, stream the response directly
            for char in assistant_message.content or "":
                timestamp = int(time.time() * 1000)
                json_data = json.dumps({'content': char, 'type': 'chunk', 'timestamp': timestamp}, ensure_ascii=False)
                yield f"data: {json_data}\n\n"
            
            # Save the response
            if session_id and assistant_message.content:
                save_message(session_id, "assistant", assistant_message.content)
        
        # Send end signal
        end_data = json.dumps({'content': '', 'type': 'end', 'timestamp': int(time.time() * 1000)}, ensure_ascii=False)
        yield f"data: {end_data}\n\n"
        
    except Exception as e:
        # Send error signal
        error_data = json.dumps({'error': str(e), 'type': 'error', 'timestamp': int(time.time() * 1000)}, ensure_ascii=False)
        yield f"data: {error_data}\n\n"

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {"message": "PortfolioBackend", "status": "running"}

@app.post("/stream")
@limiter.limit("10/hour")  # Allow 10 requests per hour per IP
async def stream_llm_response(request: Request, prompt_request: PromptRequest):
    """
    Stream LLM response endpoint with rate limiting
    
    Args:
        request: FastAPI request object for rate limiting
        prompt_request: PromptRequest containing the prompt string
        
    Returns:
        StreamingResponse with the LLM response
    """

    print("prompt_request", prompt_request)

    if not prompt_request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    return StreamingResponse(
        stream_openai_response(prompt_request.prompt, prompt_request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }
    )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Check Redis connection
    try:
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy", 
        "service": "PortfolioBackend",
        "redis": redis_status
    }

@app.get("/rate-limit-info")
async def rate_limit_info(request: Request):
    """
    Get rate limit information for the current IP
    """
    try:
        # Get current rate limit info
        key = f"slowapi:{get_remote_address(request)}"
        current_requests = redis_client.get(key)
        
        return {
            "ip": get_remote_address(request),
            "current_requests": int(current_requests) if current_requests else 0,
            "limit": "10/hour",
            "reset_time": "Next hour"
        }
    except Exception as e:
        return {
            "ip": get_remote_address(request),
            "error": f"Could not retrieve rate limit info: {str(e)}"
        }

@app.post("/session")
async def create_new_session():
    """
    Create a new chat session
    """
    try:
        session_id = create_session()
        return {
            "session_id": session_id,
            "message": "Session created successfully",
            "ttl": "24 hours"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/session/{session_id}")
async def get_session_history(session_id: str):
    """
    Get chat history for a session
    """
    try:
        session_data = get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "created_at": session_data["created_at"],
            "last_activity": session_data["last_activity"],
            "message_count": len(session_data["messages"]),
            "messages": session_data["messages"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session
    """
    try:
        # Check if session exists
        session_data = get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session from Redis
        redis_client.delete(f"chat:session:{session_id}")
        
        return {
            "session_id": session_id,
            "message": "Session deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.get("/sessions")
async def list_sessions(request: Request):
    """
    List all active sessions for the current IP (for debugging/admin purposes)
    """
    try:
        # Get all session keys for this IP (using IP as prefix for organization)
        ip = get_remote_address(request)
        pattern = f"chat:session:*"
        session_keys = redis_client.keys(pattern)
        
        sessions = []
        for key in session_keys:
            session_data = redis_client.get(key)
            if session_data:
                session_info = json.loads(session_data)
                sessions.append({
                    "session_id": session_info["session_id"],
                    "created_at": session_info["created_at"],
                    "last_activity": session_info["last_activity"],
                    "message_count": len(session_info["messages"])
                })
        
        return {
            "ip": ip,
            "total_sessions": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.get("/tools")
async def list_tools():
    """
    List all available tools/functions
    """
    try:
        tools_info = []
        for tool in TOOLS:
            if tool["type"] == "function":
                func_info = tool["function"]
                tools_info.append({
                    "name": func_info["name"],
                    "description": func_info["description"],
                    "parameters": func_info["parameters"]
                })
        
        return {
            "total_tools": len(tools_info),
            "tools": tools_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.post("/tools/test")
async def test_tool(tool_request: dict):
    """
    Test a specific tool function
    """
    try:
        tool_name = tool_request.get("tool_name")
        arguments = tool_request.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        
        result = execute_tool(tool_name, arguments)
        
        return {
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test tool: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 