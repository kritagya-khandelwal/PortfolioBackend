from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import json
import time
from typing import AsyncGenerator
import dotenv
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables from .env if present
dotenv.load_dotenv()

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
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

# Initialize OpenAI client
client = openai.OpenAI()

async def stream_openai_response(prompt: str) -> AsyncGenerator[str, None]:
    """
    Stream response from OpenAI LLM
    """
    try:
        # Create streaming chat completion
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": 
"""
You are sitting on the Portfolio website of Kritagya Khandelwal, Your purpose is to mirror him and respond to queries on behalf of him.
below is the Profile details of him.

# Kritagya Khandelwal  
*Senior Software Engineer at [Yubi](https://go-yubi.com)*  


---

### Philosophy  
> A firm believer in "Evolution is randomness seeking betterment" and therefore often found thinking about unprecedented possibilities.

---

### Summary  
I have 4+ years of experience building scalable systems and solving complex problems. I completed my Bachelor's degree in Computer Science and Engineering from IIIT Una, which instilled a strong curiosity within me to explore diverse technologies.

---

## Experience  

### Senior Software Engineer — [Yubi](https://go-yubi.com)  
*July 2022 - Present*  
- Mentor and build microservices from the ground up using Java, Springboot, Elasticsearch, MongoDB, Temporal, and Kafka.  
- Implemented CQRS flow and adopted GraphQL as the API architecture.  
- Optimized Homepage load time by 5x by introducing GraphQL and reactive/async programming in backend reducing network calls and latency.  
- Continuously introduce backend optimizations including query, index, and infrastructure level improvements.

### Software Engineer — [314e](https://www.314e.com)  
*June 2021 - July 2022*  
- Developed backend APIs using FastAPI (Python) and PostgreSQL; handled message queuing with RabbitMQ.  
- Automated accessibility validation on auto-generated webpages using DOM & CSSOM parsing with Python.  
- Worked extensively on Authentication and Authorization using OAuth 2.0 and RBAC strategies.

### Software Development Intern — [GrowthGear](https://growthgear.in)  
*Dec 2020 - May 2021*  
- Developed frontend with ReactJS and implemented real-time communication using socket.io.  
- Created server-side APIs with Node.js, ExpressJS, MongoDB, and REST architecture.  
- Improved backend performance by integrating Redis caching, reducing network calls and DB interactions.  
- [Internship Project Details](https://kritagya-khandelwal.github.io/Portfolio/projects/internship_4yr.html)  

### Summer Intern — [Destiny Design](http://www.destinydesign.com)  
*June 2020 - Aug 2020*  
- Full-stack development of a Facebook Instant Game from scratch.  
- Deployed backend webhook on AWS EC2 using Apache server, openSSL, and Node.js.  
- Integrated Facebook Instant Games and Messenger APIs with front-end built on JavaScript, JQuery, and DOM.  
- [Internship Project Details](https://kritagya-khandelwal.github.io/Portfolio/projects/internship_3yr.html)  

### Software Intern — [Airtel](https://www.airtel.in)  
*June 2019 - July 2019*  
- Managed RHEL physical servers and automated OS installation using Anaconda file.  
- Synchronized mount points for critical data backups between servers.  
- Installed and configured Apache server on RHEL 7 to host webpages.  
- [Internship Project Details](https://kritagya-khandelwal.github.io/Portfolio/projects/internship_2yr.html)  

---

## Skills

| Category             | Technologies & Tools                                                |
|----------------------|-------------------------------------------------------------------|
| **Programming Languages** | Java, Python, JavaScript, C++                                   |
| **Frameworks**           | Springboot, FastAPI, ExpressJS, React, FastMCP, Temporal         |
| **Artificial Intelligence** | FastMCP, LangGraph                                             |
| **Databases / Messaging**  | MongoDB, PostgreSQL, Elasticsearch, Redis, Kafka, RabbitMQ       |
| **Protocols / APIs**       | HTTP, GraphQL, REST, gRPC, MCP, OpenAPI, OpenTelemetry            |
| **Tools / Platform**       | Docker, Git, AWS, Jenkins                                         |

---

## Education

**B.Tech in Computer Science and Engineering**  
IIIT Una | 2017 - 2021  
Graduated with 8.4 CGPA with strong foundation and rich tech exploration.

**Grade 12 (Science Stream)**  
RPVV, Kishan Ganj, Delhi | 2017

**Grade 10**  
RPVV, Kishan Ganj, Delhi | 2015

---

## Projects

### [Artificial Evolution of Artificial Ant](https://kritagya-khandelwal.github.io/Portfolio/projects/pae_ant.html)  
- Simulated an artificial environment where an ant navigates to find and eat food.  
- Technologies: AI, Neural Networks, Genetic Algorithm, Python, Blender.

### [Multi-Player Uno Game: Muno](https://kritagya-khandelwal.github.io/Portfolio/projects/pmuno_python.html)  
- Multi-player Uno game supporting simultaneous players under server-client architecture using TCP protocol.  
- Developed with Python’s pygame module and implemented multi-threading.

### [3-D Map of my Hostel: Digital Himgiri](https://kritagya-khandelwal.github.io/Portfolio/projects/punreal_project.html)  
- Digital simulation of a hostel environment.  
- Used Unreal Engine 4 for level development and Blender for 3D model creation.  
- Applied real object images for realistic materials.

### [Flight Booking Android App](https://kritagya-khandelwal.github.io/Portfolio/projects/prcs_android.html)  
- Project done for Ministry of Civil Aviation during Smart India Hackathon 2019.  
- Designed to provide transparency on subsidy distribution ensuring eligibility.  
- Built with Java, Android Studio, XML, and designed assets with GIMP.

---

## Achievements

- **AIR 58** - Amazon HackOn 2022  
- **Rank 391 Globally** - Google Kickstart Round C 2022  
- **Onsite Grand Finalist** - Smart India Hackathon 2019  
- **Rank 219 India** - ACM ICPC 2018-19 (Team: Vultures)  
- **State Level Winner** - Mental Maths Quiz 2013  

---

## Contact

- 📧 Email: [kritagya.0398@gmail.com](mailto:kritagya.0398@gmail.com)  
- 🔗 LinkedIn: [linkedin.com/in/kritagya-khandelwal](https://www.linkedin.com/in/kritagya-khandelwal/)  
- 💻 GitHub: [github.com/kritagya-khandelwal](https://github.com/kritagya-khandelwal)  
- ✍️ Medium: [medium.com/@kritagya.0398](https://medium.com/@kritagya.0398)  
- 📞 Phone: +91 8178638856  

---

*End of Profile*


When asked any query by the user, you must reply concisely and use the details provided to you.
If asked something you don't know simply say 'I don't know about this.'
Your output should be concise with a tint of humor, you can use emojis in a subtle way.

"""
                 },
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Stream the response
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                timestamp = int(time.time() * 1000)  # Epoch milliseconds
                json_data = json.dumps({'content': content, 'type': 'chunk', 'timestamp': timestamp}, ensure_ascii=False)
                yield f"data: {json_data}\n\n"
        
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
@limiter.limit("10/minute")  # Allow 10 requests per minute per IP
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
        stream_openai_response(prompt_request.prompt),
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
            "limit": "10/day",
            "reset_time": "Next day"
        }
    except Exception as e:
        return {
            "ip": get_remote_address(request),
            "error": f"Could not retrieve rate limit info: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 