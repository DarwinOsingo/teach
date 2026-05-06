from fastapi import FastAPI
from model import ChatRequest, ChatResponse
import ollama_client

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    messages = [message.model_dump() for message in request.messages]
    reply = ollama_client.chat(messages)
    return ChatResponse(reply=reply, model="gemma3:4b")