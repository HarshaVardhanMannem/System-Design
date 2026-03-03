# System Design — From First Principles

A collection of production-grade system design components implemented in Python, built from first principles with step-by-step documentation and thorough test coverage.

Each project lives in its own directory, contains a focused `README.md`, design docs, implementation, and tests.

---

## Projects

| Project | Description | Algorithms / Approaches |
|---------|-------------|------------------------|
| [ID Generator Design](ID%20Generator%20Design/) | Distributed 64-bit unique ID generation with no central database | Snowflake (timestamp + machine ID + sequence) |
| [Ratelimiter Design](Ratelimiter%20Design/) | In-memory per-key rate limiting | Fixed Window, Sliding Window, Token Bucket |

---

## Repository Structure

```
System-Design/
├── README.md                        ← you are here
│
├── ID Generator Design/
│   ├── README.md                    ← install, quick-start, docs index
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── id_generator/
│   │   ├── snowflake.py             ← Snowflake-style ID generator
│   │   └── exceptions.py
│   ├── docs/
│   │   ├── 01-first-principles.md   ← Why unique IDs? requirements
│   │   ├── 02-design-approaches.md  ← UUID vs Snowflake vs Segment
│   │   └── 03-implementation-steps.md
│   └── tests/
│       └── test_snowflake.py
│
└── Ratelimiter Design/
    ├── README.md                    ← install, quick-start, docs index
    ├── pyproject.toml
    ├── requirements.txt
    ├── rate_limiter/
    │   ├── fixed_window.py          ← Fixed Window limiter
    │   ├── sliding_window.py        ← Sliding Window limiter
    │   ├── token_bucket.py          ← Token Bucket limiter
    │   ├── base.py
    │   └── exceptions.py
    ├── docs/
    │   ├── 01-first-principles.md   ← What is rate limiting?
    │   ├── 02-algorithms-overview.md ← Algorithm comparison & diagrams
    │   └── 03-implementation-steps.md
    └── tests/
        ├── test_fixed_window.py
        ├── test_sliding_window.py
        └── test_token_bucket.py
```

---

## 1. ID Generator Design

> **Goal:** Generate unique, time-sortable 64-bit IDs across distributed nodes with no central database.

### How it works — Snowflake layout

```
 63       22      12      0
 |        |        |      |
 [timestamp 41b][machine 10b][sequence 12b]
```

- **41 bits** — milliseconds since a custom epoch (~69 years of range).
- **10 bits** — machine / worker ID (up to 1,024 nodes).
- **12 bits** — sequence counter within the same millisecond (up to 4,096 IDs/ms/node).

IDs are **strictly increasing** within a node and **roughly increasing** across nodes, making them B-tree friendly.

### Quick start

```bash
cd "ID Generator Design"
pip install -e .
pip install -r requirements.txt
```

```python
from id_generator import SnowflakeIdGenerator

gen = SnowflakeIdGenerator(machine_id=1)
id1 = gen.generate()
id2 = gen.generate()
assert id1 < id2   # time-sortable
```

With a custom epoch and injectable clock (useful for tests):

```python
gen = SnowflakeIdGenerator(
    machine_id=0,
    epoch_ms=1_577_836_800_000,   # 2020-01-01 00:00:00 UTC
    time_func=my_time_ms,
)
```

### Key properties

| Property | Value |
|----------|-------|
| ID width | 64 bits (fits in a `BIGINT`) |
| Max nodes | 1,024 (10-bit machine ID) |
| Max IDs / ms / node | 4,096 |
| Time span | ~69 years from epoch |
| Sortable | ✅ (time-ordered leading bits) |
| Central DB needed | ❌ |

### Design docs

1. [01-first-principles.md](ID%20Generator%20Design/docs/01-first-principles.md) — Why we need unique IDs, requirements.
2. [02-design-approaches.md](ID%20Generator%20Design/docs/02-design-approaches.md) — UUID vs Snowflake vs Segment; trade-offs.
3. [03-implementation-steps.md](ID%20Generator%20Design/docs/03-implementation-steps.md) — Step-by-step: bit layout, clock handling, overflow, tests.

### Run tests

```bash
cd "ID Generator Design"
pytest tests/ -v
```

---

## 2. Ratelimiter Design

> **Goal:** Cap how many requests a given client can make in a defined period, keeping systems stable and fair.

### Algorithms

#### Fixed Window

Divide time into fixed intervals (e.g. 0–60 s, 60–120 s). Keep one counter per key per interval; reset on each new window.

- **Pros:** Simple, O(1) memory per key.
- **Cons:** Burst possible at window boundaries (up to 2× the limit within a 2-second span).

#### Sliding Window

The "window" is always *the last N seconds from now*. Stores request timestamps per key and drops those older than the window.

- **Pros:** Accurate, no boundary bursts.
- **Cons:** Higher memory (list of timestamps per key).

#### Token Bucket

Each key owns a bucket with a configurable **capacity**. Tokens are added at a fixed **refill rate**; each request consumes one token.

- **Pros:** Allows controlled bursts up to capacity; smooths traffic over time.
- **Cons:** Different semantics than "N requests per window" — it is a *rate + burst* cap.

### Algorithm comparison

| Algorithm      | Boundary burst | Memory  | Accuracy   | Burst control |
|----------------|---------------|---------|------------|---------------|
| Fixed Window   | ✅ Yes         | Low     | Coarse     | No            |
| Sliding Window | ❌ No          | Higher  | High       | No            |
| Token Bucket   | ❌ No          | Low     | Rate-based | ✅ Yes         |

### Quick start

```bash
cd "Ratelimiter Design"
pip install -e .
pip install -r requirements.txt
```

```python
from rate_limiter import FixedWindowLimiter, SlidingWindowLimiter, TokenBucketLimiter, RateLimitExceeded

# Fixed window: 5 requests per 60 seconds
fixed = FixedWindowLimiter(limit=5, window_sec=60)
if fixed.allow("user_123"):
    pass  # handle request
else:
    pass  # rate limited — return HTTP 429

# Or raise on limit:
fixed.raise_if_not_allowed("user_123")  # raises RateLimitExceeded if over limit

# Sliding window: 10 requests in the last 60 seconds
sliding = SlidingWindowLimiter(limit=10, window_sec=60)

# Token bucket: capacity 10, refill 2 tokens/second
token = TokenBucketLimiter(capacity=10, refill_rate=2.0)
```

### Design docs

1. [01-first-principles.md](Ratelimiter%20Design/docs/01-first-principles.md) — What problem rate limiting solves; core concepts.
2. [02-algorithms-overview.md](Ratelimiter%20Design/docs/02-algorithms-overview.md) — Algorithm comparison with flow diagrams.
3. [03-implementation-steps.md](Ratelimiter%20Design/docs/03-implementation-steps.md) — How each algorithm maps to code.

### Run tests

```bash
cd "Ratelimiter Design"
pytest tests/ -v
```

---

## Running All Tests

```bash
# ID Generator
cd "ID Generator Design" && pip install -e . -q && pytest tests/ -v
cd ..

# Rate Limiter
cd "Ratelimiter Design" && pip install -e . -q && pytest tests/ -v
cd ..
```

---

## Design Philosophy

Each project follows the same structure:

1. **First principles** — understand *why* the component is needed before writing any code.
2. **Approach comparison** — evaluate multiple designs and trade-offs before committing to one.
3. **Incremental implementation** — build the simplest correct version first, then extend.
4. **Tests as specification** — tests codify expected behaviour and edge cases (clock skew, sequence overflow, boundary bursts, etc.).

---

## License

MIT.
