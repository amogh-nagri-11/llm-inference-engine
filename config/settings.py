import os
from dotenv import load_dotenv

load_dotenv()

# ── Gateway ────────────────────────────────────────────
GATEWAY_HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8000))
API_KEY      = os.getenv("API_KEY", "dev-key")

# ── Workers ────────────────────────────────────────────
_raw_urls   = os.getenv("WORKER_URLS", "http://localhost:11434")
WORKER_URLS = [u.strip() for u in _raw_urls.split(",") if u.strip()]

# ── Model ──────────────────────────────────────────────
DEFAULT_MODEL   = os.getenv("DEFAULT_MODEL", "llama3:latest")
MAX_TOKENS      = int(os.getenv("MAX_TOKENS", 2048))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 120))

# ── Routing ────────────────────────────────────────────
ROUTING_STRATEGY = os.getenv("ROUTING_STRATEGY", "round_robin")

# ── Redis ──────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB   = int(os.getenv("REDIS_DB", 0))

# ── Circuit Breaker ────────────────────────────────────
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", 5))
CIRCUIT_BREAKER_TIMEOUT   = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", 30))

# ── Observability ──────────────────────────────────────
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 9090))
GRAFANA_PORT    = int(os.getenv("GRAFANA_PORT", 3000))