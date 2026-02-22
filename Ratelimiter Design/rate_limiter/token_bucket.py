"""Token bucket rate limiter."""

import time
from typing import Any

from rate_limiter.base import RateLimiter


class TokenBucketLimiter(RateLimiter):
    """
    Rate limiter using a token bucket. Tokens are added at a fixed rate;
    each request consumes one token. Allows bursts up to bucket capacity.
    """

    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        time_func: Any = None,
    ):
        """
        :param capacity: Maximum number of tokens the bucket can hold.
        :param refill_rate: Tokens added per second.
        :param time_func: Optional function returning current time (default: time.monotonic).
        """
        if capacity < 1 or refill_rate <= 0:
            raise ValueError("capacity must be >= 1 and refill_rate must be > 0")
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._time = time_func or time.monotonic
        self._state: dict[str, tuple[float, float]] = {}

    def allow(self, identifier: str) -> bool:
        now = self._time()
        if identifier not in self._state:
            self._state[identifier] = (self._capacity, now)
        tokens, last_refill = self._state[identifier]
        elapsed = now - last_refill
        tokens = min(self._capacity, tokens + elapsed * self._refill_rate)
        if tokens < 1:
            self._state[identifier] = (tokens, now)
            return False
        self._state[identifier] = (tokens - 1, now)
        return True
