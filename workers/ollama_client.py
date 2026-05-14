import httpx
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator

@dataclass
class WorkerStats:
    url: str
    active_requests: int = 0
    total_requests: int = 0
    total_latency: float = 0.0
    failures: int = 0
    is_healthy: bool = True

    @property
    def avg_latency(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests


class OllamaClient:
    def __init__(self, base_url: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.stats = WorkerStats(url=base_url)

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self.stats.is_healthy = response.status_code == 200
                return self.stats.is_healthy
        except Exception:
            self.stats.is_healthy = False
            return False

    async def generate(self, model: str, prompt: str, stream: bool = False) -> dict:
        start = time.monotonic()
        self.stats.active_requests += 1

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                response.raise_for_status()
                result = response.json()

                # Update stats
                latency = time.monotonic() - start
                self.stats.total_requests += 1
                self.stats.total_latency += latency
                self.stats.failures = 0  # reset on success

                return {
                    "response": result.get("response", ""),
                    "model": result.get("model"),
                    "worker_url": self.base_url,
                    "latency_ms": round(latency * 1000, 2),
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                }
        except Exception as e:
            self.stats.failures += 1
            raise RuntimeError(f"Worker {self.base_url} failed: {str(e)}")
        finally:
            self.stats.active_requests -= 1

    async def chat(self, model: str, messages: list) -> dict:
        start = time.monotonic()
        self.stats.active_requests += 1

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                    }
                )
                response.raise_for_status()
                result = response.json()

                latency = time.monotonic() - start
                self.stats.total_requests += 1
                self.stats.total_latency += latency
                self.stats.failures = 0

                return {
                    "message": result.get("message", {}),
                    "model": result.get("model"),
                    "worker_url": self.base_url,
                    "latency_ms": round(latency * 1000, 2),
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                }
        except Exception as e:
            self.stats.failures += 1
            raise RuntimeError(f"Worker {self.base_url} failed: {str(e)}")
        finally:
            self.stats.active_requests -= 1