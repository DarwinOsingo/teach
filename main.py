from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import ollama
import uuid
import time
import logging

# ── Logging setup ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)s │ %(message)s"
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────
app = FastAPI(title="Local Chat API", version="1.0.0")

# ── CORS ───────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory stores ───────────────────────────────────────
sessions: dict = {}       # session_id → list of messages
rate_limits: dict = {}    # session_id → list of timestamps

# ── Config ─────────────────────────────────────────────────
RATE_LIMIT = 10           # max requests
RATE_WINDOW = 60          # per 60 seconds

# ── Models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    model: str = "qwen3:4b"
    session_id: Optional[str] = None
    system_prompt: Optional[str] = "You are a helpful assistant."

class ChatResponse(BaseModel):
    reply: str
    model: str
    session_id: str
    turn: int

# ── Rate limiter ───────────────────────────────────────────
def check_rate_limit(session_id: str):
    now = time.time()
    timestamps = rate_limits.get(session_id, [])
    timestamps = [t for t in timestamps if now - t < RATE_WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit hit. Max {RATE_LIMIT} requests per {RATE_WINDOW}s."
        )

    timestamps.append(now)
    rate_limits[session_id] = timestamps

# ── Middleware: request logger ─────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} │ {response.status_code} │ {duration}ms")
    return response

# ── Routes ─────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "sessions_active": len(sessions)}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # create or resume session
    session_id = request.session_id or str(uuid.uuid4())
    check_rate_limit(session_id)

    if session_id not in sessions:
        sessions[session_id] = [
            {"role": "system", "content": request.system_prompt}
        ]
        logger.info(f"New session: {session_id}")

    # append user message
    sessions[session_id].append({"role": "user", "content": request.message})

    try:
        response = ollama.chat(
            model=request.model,
            messages=sessions[session_id]
        )
        reply = response.message.content

    except Exception as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # append assistant reply
    sessions[session_id].append({"role": "assistant", "content": reply})

    turn = len([m for m in sessions[session_id] if m["role"] == "user"])

    return ChatResponse(
        reply=reply,
        model=request.model,
        session_id=session_id,
        turn=turn
    )

@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del sessions[session_id]
    rate_limits.pop(session_id, None)
    logger.info(f"Session cleared: {session_id}")
    return {"status": "cleared", "session_id": session_id}