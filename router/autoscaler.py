import asyncio
import docker
import redis.asyncio as aioredis
from config import settings


class Autoscaler:
    def __init__(
        self,
        min_workers: int = 1,
        max_workers: int = 4,
        scale_up_threshold: int = 3,    # queue depth to trigger scale up
        scale_down_threshold: int = 0,  # queue depth to trigger scale down
        check_interval: int = 10,       # seconds between checks
        cooldown: int = 30,             # seconds between scaling actions
    ):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.check_interval = check_interval
        self.cooldown = cooldown

        self.redis = None
        self.docker_client = None
        self._task = None
        self._last_scale_time = 0.0
        self._worker_containers: list[str] = []  # container IDs we've spawned
        self.queue_key = "llm:request_queue"

    async def connect(self):
        self.redis = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            decode_responses=True
        )
        try:
            self.docker_client = docker.from_env()
            print("[Autoscaler] Connected to Docker")
        except Exception as e:
            print(f"[Autoscaler] Docker not available: {e}")
        print("[Autoscaler] Connected to Redis")

    async def _queue_depth(self) -> int:
        return await self.redis.llen(self.queue_key)

    def _running_worker_count(self) -> int:
        if not self.docker_client:
            return 1  # assume the base Ollama is running
        try:
            containers = self.docker_client.containers.list(
                filters={"name": "llm-worker-dynamic"}
            )
            return len(containers) + 1  # +1 for the base Ollama
        except Exception:
            return 1

    def _in_cooldown(self) -> bool:
        import time
        return (time.monotonic() - self._last_scale_time) < self.cooldown

    async def _scale_up(self):
        if not self.docker_client:
            print("[Autoscaler] Skipping scale up — Docker not available")
            return

        import time
        current = self._running_worker_count()
        if current >= self.max_workers:
            print(f"[Autoscaler] Already at max workers ({self.max_workers}), skipping scale up")
            return

        print(f"[Autoscaler] Scaling UP — spawning worker {current + 1}")
        try:
            # Find an available port starting at 11435
            port = 11434 + current
            container = self.docker_client.containers.run(
                "ollama/ollama:latest",
                detach=True,
                name=f"llm-worker-dynamic-{port}",
                ports={f"11434/tcp": port},
                volumes={"ollama_data": {"bind": "/root/.ollama", "mode": "rw"}},
            )
            self._worker_containers.append(container.id)
            self._last_scale_time = time.monotonic()
            print(f"[Autoscaler] Worker spawned on port {port} | container={container.short_id}")
        except Exception as e:
            print(f"[Autoscaler] Failed to scale up: {e}")

    async def _scale_down(self):
        if not self.docker_client or not self._worker_containers:
            return

        import time
        current = self._running_worker_count()
        if current <= self.min_workers:
            print(f"[Autoscaler] Already at min workers ({self.min_workers}), skipping scale down")
            return

        container_id = self._worker_containers.pop()
        print(f"[Autoscaler] Scaling DOWN — removing container {container_id[:12]}")
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
            self._last_scale_time = time.monotonic()
            print(f"[Autoscaler] Worker removed")
        except Exception as e:
            print(f"[Autoscaler] Failed to scale down: {e}")

    async def _run(self):
        print("[Autoscaler] Monitoring loop started")
        while True:
            try:
                await asyncio.sleep(self.check_interval)

                depth = await self._queue_depth()
                workers = self._running_worker_count()
                print(f"[Autoscaler] queue_depth={depth} | workers={workers}")

                if self._in_cooldown():
                    continue

                if depth >= self.scale_up_threshold:
                    await self._scale_up()
                elif depth <= self.scale_down_threshold and workers > self.min_workers:
                    await self._scale_down()

            except Exception as e:
                print(f"[Autoscaler] Error: {e}")
                await asyncio.sleep(5)

    def start(self):
        self._task = asyncio.create_task(self._run())
        print("[Autoscaler] Started")

    def stop(self):
        if self._task:
            self._task.cancel()


autoscaler = Autoscaler(
    min_workers=1,
    max_workers=4,
    scale_up_threshold=3,
    scale_down_threshold=0,
    check_interval=10,
    cooldown=30,
)