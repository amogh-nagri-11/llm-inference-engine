from typing import List, Optional
from workers.ollama_client import OllamaClient
from config import settings
import asyncio


class LoadBalancer:
    def __init__(self, worker_urls: List[str]):
        self.workers = [OllamaClient(url) for url in worker_urls]
        self._rr_index = 0

    def _healthy_workers(self) -> List[OllamaClient]:
        return [w for w in self.workers if w.stats.is_healthy]

    def pick_worker(self) -> OllamaClient:
        healthy = self._healthy_workers()
        if not healthy:
            raise RuntimeError("No healthy workers available")

        strategy = settings.ROUTING_STRATEGY

        if strategy == "round_robin":
            worker = healthy[self._rr_index % len(healthy)]
            self._rr_index += 1
            return worker

        elif strategy == "least_latency":
            return min(healthy, key=lambda w: w.stats.avg_latency)

        elif strategy == "queue_depth":
            return min(healthy, key=lambda w: w.stats.active_requests)

        # Default fallback
        return healthy[0]

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
            }
            for w in self.workers
        ]


# Singleton — imported across the app
load_balancer = LoadBalancer(settings.WORKER_URLS)