# ID Generator Design

Distributed unique ID generator from first principles: **Snowflake-style** (timestamp + machine ID + sequence) with step-by-step documentation. No central DB required; 64-bit, sortable IDs.

## Install

From this directory:

```bash
pip install -e .
pip install -r requirements.txt
```

## Quick start

```python
from id_generator import SnowflakeIdGenerator

gen = SnowflakeIdGenerator(machine_id=0)
id1 = gen.generate()   # or gen.next_id()
id2 = gen.generate()
# id1 < id2; both unique 64-bit ints
```

With custom epoch and injectable time (e.g. for tests):

```python
gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=1577836800000, time_func=my_time_ms)
```

## Docs (read in order)

1. [docs/01-first-principles.md](docs/01-first-principles.md) — Why we need unique IDs, requirements (uniqueness, ordering, no bottleneck).
2. [docs/02-design-approaches.md](docs/02-design-approaches.md) — UUID vs Snowflake vs segment; trade-offs and bit layout.
3. [docs/03-implementation-steps.md](docs/03-implementation-steps.md) — Step-by-step implementation: layout, time, state, generate, overflow, clock backward, machine ID, tests.

## Tests

```bash
pytest tests/ -v
```
