from pydantic import BaseModel
from typing import Literal

class ChatMessege(BaseModel):
    role : Literal["user","assistant","system"]
    content : str
class ChatRequest(BaseModel):
    messeges:list[ChatMessege]
    
class ChatResponse(BaseModel):
    reply:str
    model:str