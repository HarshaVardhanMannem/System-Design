# Python Rate Limiter

In-memory rate limiters in Python from first principles: **fixed window**, **sliding window**, and **token bucket**, with step-by-step documentation and flow diagrams.

## Install

From the project root:

```bash
pip install -e .
```

For running tests only:

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from rate_limiter import FixedWindowLimiter, RateLimitExceeded

limiter = FixedWindowLimiter(limit=5, window_sec=60)

if limiter.allow("user_123"):
    # handle request
    pass
else:
    # rate limited
    pass

# Or raise on limit:
limiter.raise_if_not_allowed("user_123")  # raises RateLimitExceeded if limited
```

Other limiters:

```python
from rate_limiter import SlidingWindowLimiter, TokenBucketLimiter

sliding = SlidingWindowLimiter(limit=10, window_sec=60)
token = TokenBucketLimiter(capacity=10, refill_rate=2.0)  # 2 tokens per second
```

## Documentation (First Principles)

Read in order for a step-by-step flow from concepts to code:

1. [docs/01-first-principles.md](docs/01-first-principles.md) — What problem rate limiting solves, core concepts (limit, window, identifier), allow vs deny.
2. [docs/02-algorithms-overview.md](docs/02-algorithms-overview.md) — Fixed window, sliding window, token bucket (and optional leaky bucket), with diagrams and trade-offs.
3. [docs/03-implementation-steps.md](docs/03-implementation-steps.md) — How each algorithm maps to the code and the flow of `allow(identifier)`.

## Tests

```bash
pytest tests/ -v
```

## License

MIT.
