"""Sliding-window log rate limiter."""

import time
from collections import deque
from typing import Any

from rate_limiter.base import RateLimiter


class SlidingWindowLimiter(RateLimiter):
    """
    Rate limiter using a sliding window: only requests within the last
    window_sec seconds count toward the limit.
    """

    def __init__(self, limit: int, window_sec: float, time_func: Any = None):
        """
        :param limit: Maximum number of requests allowed in the sliding window.
        :param window_sec: Length of the sliding window in seconds.
        :param time_func: Optional function returning current time (default: time.monotonic).
        """
        if limit < 1 or window_sec <= 0:
            raise ValueError("limit must be >= 1 and window_sec must be > 0")
        self._limit = limit
        self._window_sec = window_sec
        self._time = time_func or time.monotonic
        self._state: dict[str, deque[float]] = {}

    def allow(self, identifier: str) -> bool:
        now = self._time()
        if identifier not in self._state:
            self._state[identifier] = deque()
        timestamps = self._state[identifier]
        cutoff = now - self._window_sec
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= self._limit:
            return False
        timestamps.append(now)
        return True
