from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Pydantic models for OpenAI API compatibility
class ChatCompletionsRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stop: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None
    stream: Optional[bool] = False

class ChatCompletionsResponse(BaseModel):
    id: str
    model: str
    choices: List[Dict[str, Any]]
    created: int
    usage: Optional[Dict[str, Any]] = None
