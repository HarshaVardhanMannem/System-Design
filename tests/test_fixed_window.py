"""Tests for FixedWindowLimiter."""

import pytest
from rate_limiter.exceptions import RateLimitExceeded
from rate_limiter.fixed_window import FixedWindowLimiter


class MockTime:
    def __init__(self):
        self._now = 0.0

    def set(self, t: float) -> None:
        self._now = t

    def advance(self, dt: float) -> float:
        self._now += dt
        return self._now

    def __call__(self) -> float:
        return self._now


def test_under_limit_all_allowed():
    t = MockTime()
    limiter = FixedWindowLimiter(limit=3, window_sec=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True


def test_at_limit_next_denied():
    t = MockTime()
    limiter = FixedWindowLimiter(limit=3, window_sec=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False


def test_after_window_reset_again_allowed():
    t = MockTime()
    limiter = FixedWindowLimiter(limit=2, window_sec=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False
    t.advance(1.0)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False


def test_per_identifier():
    t = MockTime()
    limiter = FixedWindowLimiter(limit=1, window_sec=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False
    assert limiter.allow("user2") is True
    assert limiter.allow("user2") is False


def test_raise_if_not_allowed():
    t = MockTime()
    limiter = FixedWindowLimiter(limit=1, window_sec=1.0, time_func=t)
    limiter.raise_if_not_allowed("user1")
    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.raise_if_not_allowed("user1")
    assert exc_info.value.identifier == "user1"


def test_invalid_args():
    with pytest.raises(ValueError):
        FixedWindowLimiter(limit=0, window_sec=1.0)
    with pytest.raises(ValueError):
        FixedWindowLimiter(limit=1, window_sec=0)
