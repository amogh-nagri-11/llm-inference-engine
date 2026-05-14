# LLM Inference Engine

A distributed inference engine that sits between your application and LLM models — managing load balancing, request batching, autoscaling, and observability at production scale.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  API Gateway                     │
│              (FastAPI - Port 8000)               │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              Request Router                      │
│   (least-latency / round-robin / queue-depth)    │
└───────┬──────────────┬──────────────┬────────────┘
        │              │              │
┌───────▼──┐    ┌──────▼───┐   ┌─────▼────┐
│ Worker 1 │    │ Worker 2 │   │ Worker N │
│ (Ollama) │    │ (Ollama) │   │ (Ollama) │
└───────┬──┘    └──────┬───┘   └─────┬────┘
        └──────────────┴─────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│        Observability (Prometheus + Grafana)      │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| API Gateway | FastAPI, Python 3.11 |
| Queue | Redis |
| Inference Workers | Ollama |
| Observability | Prometheus, Grafana |
| Orchestration | Docker Compose → Kubernetes |
| Autoscaling | KEDA |

## Project Structure

```
llm-inference-engine/
├── gateway/         # FastAPI entry point, auth, rate limiting
├── router/          # Load balancing, circuit breaker, routing logic
├── workers/         # Ollama worker wrapper, health checks
├── observability/   # Prometheus config, Grafana dashboards
├── config/          # Environment configs, model configs
├── scripts/         # Dev setup, deployment scripts
└── docs/            # Architecture diagrams, API docs
```

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/llm-inference-engine.git
cd llm-inference-engine

# 2. Copy env file and fill in values
cp .env.example .env

# 3. Start the stack
docker compose up --build
```

## Phases

- [x] Phase 1 — Gateway + basic routing to Ollama workers
- [ ] Phase 2 — Redis queue, health checks, circuit breaker
- [ ] Phase 3 — Prometheus + Grafana observability
- [ ] Phase 4 — Autoscaling + continuous batching
- [ ] Phase 5 — Kubernetes + cloud deploy
