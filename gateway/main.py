from fastapi import FastAPI
from gateway.routes import router
from contextlib import asynccontextmanager
from router.load_balancer import load_balancer
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup — check all workers
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
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "LLM Inference Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }