import time
from enum import Enum
from config import settings


class CircuitState(Enum):
    CLOSED = "closed"       # healthy, traffic flowing
    OPEN = "open"           # too many failures, blocking traffic
    HALF_OPEN = "half_open" # cooldown passed, testing one request


class CircuitBreaker:
    def __init__(self, worker_url: str):
        self.worker_url = worker_url
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.threshold = settings.CIRCUIT_BREAKER_THRESHOLD
        self.timeout = settings.CIRCUIT_BREAKER_TIMEOUT

    def is_open(self) -> bool:
        if self.state == CircuitState.OPEN:
            # Check if cooldown has passed
            if time.monotonic() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                print(f"[CircuitBreaker] {self.worker_url} → HALF_OPEN, testing...")
                return False
            return True
        return False

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            print(f"[CircuitBreaker] {self.worker_url} → CLOSED, recovered")
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()

        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            print(f"[CircuitBreaker] {self.worker_url} → OPEN after {self.failure_count} failures")

    @property
    def status(self) -> str:
        return self.state.value