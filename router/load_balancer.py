import asyncio
from typing import List
from workers.ollama_client import OllamaClient
from router.circuit_breaker import CircuitBreaker
from config import settings


class LoadBalancer:
    def __init__(self, worker_urls: List[str]):
        self.workers = [OllamaClient(url) for url in worker_urls]
        self.breakers = {url: CircuitBreaker(url) for url in worker_urls}
        self._rr_index = 0

    def _available_workers(self) -> List[OllamaClient]:
        return [
            w for w in self.workers
            if w.stats.is_healthy and not self.breakers[w.stats.url].is_open()
        ]

    def pick_worker(self) -> OllamaClient:
        available = self._available_workers()
        if not available:
            raise RuntimeError("No available workers — all are unhealthy or circuit open")

        strategy = settings.ROUTING_STRATEGY

        if strategy == "round_robin":
            worker = available[self._rr_index % len(available)]
            self._rr_index += 1
            return worker

        elif strategy == "least_latency":
            return min(available, key=lambda w: w.stats.avg_latency)

        elif strategy == "queue_depth":
            return min(available, key=lambda w: w.stats.active_requests)

        return available[0]

    def record_success(self, worker_url: str):
        self.breakers[worker_url].record_success()

    def record_failure(self, worker_url: str):
        self.breakers[worker_url].record_failure()

    async def health_check_all(self):
        await asyncio.gather(*[w.health_check() for w in self.workers])

    def get_worker_stats(self) -> list:
        return [
            {
                "url": w.stats.url,
                "healthy": w.stats.is_healthy,
                "active_requests": w.stats.active_requests,
                "total_requests": w.stats.total_requests,
                "avg_latency_ms": round(w.stats.avg_latency * 1000, 2),
                "failures": w.stats.failures,
                "circuit_state": self.breakers[w.stats.url].status,
            }
            for w in self.workers
        ]


load_balancer = LoadBalancer(settings.WORKER_URLS)