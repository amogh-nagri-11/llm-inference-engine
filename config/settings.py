from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Gateway
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8000
    api_key: str = "dev-key"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Workers
    worker_urls: str = "http://localhost:11434"

    # Model
    default_model: str = "llama3.1:8b"
    max_tokens: int = 2048
    request_timeout: int = 120

    # Routing
    routing_strategy: str = "round_robin"  # round_robin | least_latency | queue_depth

    # Circuit Breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30

    def get_worker_urls(self) -> List[str]:
        return [url.strip() for url in self.worker_urls.split(",")]

    class Config:
        env_file = ".env"

settings = Settings()