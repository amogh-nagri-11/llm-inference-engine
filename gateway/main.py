from fastapi import FastAPI
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from gateway.routes import router
from gateway.middleware import metrics_middleware
from router.load_balancer import load_balancer
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting LLM Inference Engine...")
    await load_balancer.health_check_all()
    stats = load_balancer.get_worker_stats()
    healthy = sum(1 for w in stats if w["healthy"])
    print(f"Workers online: {healthy}/{len(stats)}")
    yield
    print("Shutting down...")


app = FastAPI(
    title="LLM Inference Engine",
    description="Distributed inference gateway for Ollama workers",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(BaseHTTPMiddleware, dispatch=metrics_middleware)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "LLM Inference Engine",
        "version": "0.2.0",
        "docs": "/docs",
        "metrics": "/metrics",
    }


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )