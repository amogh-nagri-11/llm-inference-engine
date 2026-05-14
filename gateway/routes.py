from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from router.load_balancer import load_balancer
from config.settings import settings

router = APIRouter()


# ── Request Models ────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    stream: bool = False

class Message(BaseModel):
    role: str   # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None


# ── Auth helper ───────────────────────────────────────────

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ── Routes ────────────────────────────────────────────────

@router.get("/health")
async def health():
    await load_balancer.health_check_all()
    return {
        "status": "ok",
        "workers": load_balancer.get_worker_stats()
    }


@router.post("/generate")
async def generate(req: GenerateRequest, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)

    model = req.model or settings.default_model
    worker = load_balancer.pick_worker()

    try:
        result = await worker.generate(model=model, prompt=req.prompt)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/chat")
async def chat(req: ChatRequest, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)

    model = req.model or settings.default_model
    worker = load_balancer.pick_worker()

    try:
        messages = [m.model_dump() for m in req.messages]
        result = await worker.chat(model=model, messages=messages)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/workers")
async def workers(x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    await load_balancer.health_check_all()
    return load_balancer.get_worker_stats()