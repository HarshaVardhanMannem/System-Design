"""Tests for TokenBucketLimiter."""

import pytest
from rate_limiter.exceptions import RateLimitExceeded
from rate_limiter.token_bucket import TokenBucketLimiter


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


def test_under_capacity_all_allowed():
    t = MockTime()
    limiter = TokenBucketLimiter(capacity=3, refill_rate=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True


def test_exhausted_then_denied():
    t = MockTime()
    limiter = TokenBucketLimiter(capacity=2, refill_rate=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False


def test_refill_after_time_again_allowed():
    t = MockTime()
    limiter = TokenBucketLimiter(capacity=1, refill_rate=10.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False
    t.advance(0.2)
    assert limiter.allow("user1") is True


def test_per_identifier():
    t = MockTime()
    limiter = TokenBucketLimiter(capacity=1, refill_rate=1.0, time_func=t)
    assert limiter.allow("user1") is True
    assert limiter.allow("user1") is False
    assert limiter.allow("user2") is True
    assert limiter.allow("user2") is False


def test_raise_if_not_allowed():
    t = MockTime()
    limiter = TokenBucketLimiter(capacity=1, refill_rate=1.0, time_func=t)
    limiter.raise_if_not_allowed("user1")
    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.raise_if_not_allowed("user1")
    assert exc_info.value.identifier == "user1"


def test_invalid_args():
    with pytest.raises(ValueError):
        TokenBucketLimiter(capacity=0, refill_rate=1.0)
    with pytest.raises(ValueError):
        TokenBucketLimiter(capacity=1, refill_rate=0)
