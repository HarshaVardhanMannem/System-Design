"""Fixed-window counter rate limiter."""

import time
from typing import Any

from rate_limiter.base import RateLimiter


class FixedWindowLimiter(RateLimiter):
    """
    Rate limiter using a fixed time window. Each window has a fixed start time;
    the counter resets when a new window begins.
    """

    def __init__(self, limit: int, window_sec: float, time_func: Any = None):
        """
        :param limit: Maximum number of requests allowed per window.
        :param window_sec: Length of each window in seconds.
        :param time_func: Optional function returning current time (default: time.monotonic).
        """
        if limit < 1 or window_sec <= 0:
            raise ValueError("limit must be >= 1 and window_sec must be > 0")
        self._limit = limit
        self._window_sec = window_sec
        self._time = time_func or time.monotonic
        self._state: dict[str, tuple[float, int]] = {}

    def allow(self, identifier: str) -> bool:
        now = self._time()
        if identifier not in self._state:
            self._state[identifier] = (now, 0)
        window_start, count = self._state[identifier]
        if now >= window_start + self._window_sec:
            window_start = now
            count = 0
        if count >= self._limit:
            return False
        self._state[identifier] = (window_start, count + 1)
        return True
