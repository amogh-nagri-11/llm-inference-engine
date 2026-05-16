from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from gateway.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_REQUESTS
)
from fastapi import Request, Response
import time

# ── Middleware ─────────────────────────────────────────────

async def prometheus_middleware(request: Request, call_next):
    start = time.monotonic()
    ACTIVE_REQUESTS.inc()

    response = await call_next(request)

    latency = time.monotonic() - start
    ACTIVE_REQUESTS.dec()

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.url.path
    ).observe(latency)

    return response


# ── /metrics endpoint ──────────────────────────────────────

async def metrics_endpoint(request: Request):
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

async def metrics_middleware(request: Request, call_next):
    start = time.monotonic()
    ACTIVE_REQUESTS.inc()

    response = await call_next(request)

    latency = time.monotonic() - start
    ACTIVE_REQUESTS.dec()

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        endpoint=request.url.path
    ).observe(latency)

    return response