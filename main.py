from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "qwen3:4b"

class ChatResponse(BaseModel):
    reply: str
    model: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    return ChatResponse(reply=f"You said: {request.message}", model=request.model)