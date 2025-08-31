from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from supabase import create_client
import os

# Charger les variables d'environnement
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

# -------------------------
# MODELES Pydantic
# -------------------------

class ModelInfo(BaseModel):
    name: str
    quantization: Optional[str] = None
    context_length: Optional[int] = None

class HardwareInfo(BaseModel):
    cpu: Optional[str] = None
    gpu: Optional[str] = None
    gpu_vram_gb: Optional[int] = None
    ram_gb: Optional[int] = None

class NetworkInfo(BaseModel):
    bandwidth_mbps: Optional[int] = None
    latency_ms: Optional[int] = None

class LimitsInfo(BaseModel):
    max_tokens_per_message: Optional[int] = None
    max_messages_per_minute: Optional[int] = None

class HostInfo(BaseModel):
    username: Optional[str] = None
    public_display: Optional[bool] = None

class HeartbeatPayload(BaseModel):
    node_id: str
    status: str
    uptime_seconds: int
    hardware: HardwareInfo
    network: NetworkInfo
    limits: LimitsInfo
    model: ModelInfo
    host_info: HostInfo
    planned_shutdown: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str

class RequestPayload(BaseModel):
    node_id: str
    request_id: str
    user_id: str
    model_name: str
    current_message: Message
    recent_history: List[Message]
    summarized_history: Optional[str] = ""
    hypervars: Dict[str, Any]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False

# -------------------------
# ROUTE HEARTBEAT
# -------------------------

@app.post("/heartbeat")
async def heartbeat(payload: HeartbeatPayload):
    data = payload.dict()
    data["last_heartbeat"] = datetime.now(timezone.utc).isoformat()

    supabase.table("community_models").upsert({
        "node_id": data["node_id"],
        "status": data["status"],
        "uptime_seconds": data["uptime_seconds"],
        "hardware": data["hardware"],
        "network": data["network"],
        "limits": data["limits"],
        "model": data["model"],
        "host_info": data["host_info"],
        "planned_shutdown": data["planned_shutdown"],
        "last_heartbeat": data["last_heartbeat"]
    }, on_conflict="node_id").execute()

    return {"status": "heartbeat_received"}

# -------------------------
# ROUTE REQUEST
# -------------------------

@app.post("/request")
async def receive_request(payload: RequestPayload):
    data = payload.dict()
    supabase.table("community_model_queue").insert({
        "node_id": data["node_id"],
        "request_id": data["request_id"],
        "user_id": data["user_id"],
        "model_name": data["model_name"],
        "current_message": data["current_message"],
        "recent_history": data["recent_history"],
        "summarized_history": data["summarized_history"],
        "hypervars": data["hypervars"],
        "temperature": data["temperature"],
        "max_tokens": data["max_tokens"],
        "stream": data["stream"]
    }).execute()

    return {"status": "request_stored"}

# -------------------------
# ROUTE NODES ACTIFS
# -------------------------

@app.get("/nodes")
async def list_active_nodes():
    # CM actifs = heartbeat < 60 sec
    res = supabase.table("community_models") \
        .select("*") \
        .gt("last_heartbeat", (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()) \
        .execute()
    return res.data
