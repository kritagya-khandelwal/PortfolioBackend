from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import json
import time
import uuid
from typing import AsyncGenerator, List, Optional
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

def load_system_prompt() -> str:
    """
    Load system prompt from external files
    """
    try:
        # Load the system prompt instructions
        system_prompt_path = "./data/system_prompt.md"
        
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
    Stream response from OpenAI LLM with session support
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
        
        # Create streaming chat completion
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Collect full response for saving
        full_response = ""
        
        # Stream the response
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                timestamp = int(time.time() * 1000)  # Epoch milliseconds
                json_data = json.dumps({'content': content, 'type': 'chunk', 'timestamp': timestamp}, ensure_ascii=False)
                yield f"data: {json_data}\n\n"
        
        # Save assistant response to session
        if session_id and full_response:
            save_message(session_id, "assistant", full_response)
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 