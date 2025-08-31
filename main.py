from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI()

# Stockage en mémoire (MVP)
requests_store = []

# Modèles Pydantic pour valider le JSON
class Message(BaseModel):
    role: str
    content: str

class RequestPayload(BaseModel):
    request_id: str
    user_id: str
    model: str
    current_message: Message
    recent_history: List[Message]
    summarized_history: str
    hypervars: Dict[str, Any]
    temperature: float
    max_tokens: int
    stream: bool

@app.post("/request")
async def receive_request(payload: RequestPayload):
    # Ajoute un horodatage
    data = payload.dict()
    data["received_at"] = datetime.utcnow().isoformat()
    requests_store.append(data)
    return {"status": "ok", "stored_count": len(requests_store)}

@app.get("/requests")
async def list_requests():
    return requests_store
