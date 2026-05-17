import asyncio
from router.load_balancer import load_balancer


class HealthChecker:
    def __init__(self, interval: int = 15):
        self.interval = interval
        self._task = None

    async def _run(self):
        while True:
            await asyncio.sleep(self.interval)
            await load_balancer.health_check_all()
            stats = load_balancer.get_worker_stats()
            for w in stats:
                status = "✓" if w["healthy"] else "✗"
                print(f"[HealthChecker] {status} {w['url']} | "
                      f"active={w['active_requests']} "
                      f"avg_latency={w['avg_latency_ms']}ms "
                      f"circuit={w['circuit_state']}")

    def start(self):
        self._task = asyncio.create_task(self._run())
        print(f"[HealthChecker] Started, interval={self.interval}s")

    def stop(self):
        if self._task:
            self._task.cancel()


health_checker = HealthChecker(interval=15)