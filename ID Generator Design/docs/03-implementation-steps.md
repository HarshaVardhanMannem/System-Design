# Implementation Steps: Snowflake-Style ID Generator

This document walks through what to build and in what order. You write the code; this gives the map.

---

## Step 1: Decide the bit layout

Pick how many bits for **timestamp**, **machine ID**, and **sequence**. Example (Snowflake default):

- **41 bits timestamp** — milliseconds since a custom epoch (e.g. 2020-01-01). Gives ~69 years.
- **10 bits machine ID** — 0–1023 machines.
- **12 bits sequence** — 0–4095 IDs per millisecond per machine.

Total: 41 + 10 + 12 = 63 bits (one bit reserved/sign). Use 64-bit unsigned if your language supports it.

**Your task:** Define constants for bit positions and masks (or bit lengths). You’ll use these to pack three numbers into one 64-bit integer.

---

## Step 2: Time source and epoch

IDs must increase over time. Use a fixed **epoch** (start time) and compute "milliseconds since epoch" for the current time.

**Your task:**

- Choose an epoch (e.g. Unix epoch or 2020-01-01 00:00:00 UTC) and store it as a constant.
- Write a helper that returns "current time in ms since epoch". Use `time.time()` or `time.time_ns() // 1_000_000` and subtract epoch ms.
- Make the time function injectable (e.g. parameter or dependency) so tests can use a fake clock.

---

## Step 3: Per-generator state

Each generator instance (or each machine) needs:

- **last_timestamp** — the last ms value you used.
- **sequence** — counter for the current ms (0 up to max sequence, e.g. 4095).

**Your task:** In your generator class, add fields for these. Initialize `sequence = 0`; `last_timestamp` can start at 0 or at "current time" from your time source.

---

## Step 4: Generate one ID (happy path)

Logic in words:

1. Get current timestamp in ms (since epoch).
2. If current ms **equals** last_timestamp: increment sequence. If sequence exceeds max (e.g. 4095), you’re in overflow — see Step 5.
3. If current ms **greater** than last_timestamp: reset sequence to 0, set last_timestamp = current ms.
4. Pack (timestamp, machine_id, sequence) into one 64-bit integer: shift and OR bits according to your layout.
5. Return the integer (or string if you prefer).

**Your task:** Implement this in a method like `generate()` or `next_id()`. Use bit shifts and masks to build the ID. No need to handle clock going backwards yet.

---

## Step 5: Sequence overflow (same millisecond, too many IDs)

If you’re still in the same millisecond and sequence hits max (e.g. 4096 values), you have two options:

- **Block:** Sleep until the next millisecond, then reset sequence and continue.
- **Spin / advance:** Treat "logical timestamp" as advancing (e.g. last_timestamp += 1) and reset sequence — IDs stay unique and roughly ordered.

**Your task:** Pick one policy, document it, and implement it. Call it from the same method where you increment sequence.

---

## Step 6: Clock going backwards

If the system clock moves backward, current_ms might be **less** than last_timestamp. Options:

- **Reject:** Raise an exception (e.g. "Clock moved backward").
- **Wait:** Block until real time catches up to last_timestamp (risky if clock is wrong).
- **Use last_timestamp + 1:** Keep generating with a logical advance (same as overflow); document that IDs may not reflect real time.

**Your task:** Choose one, document it in a docstring or in the docs, and add a branch in your generate logic.

---

## Step 7: Machine ID

For a single process, machine ID can be 0. For multiple processes/nodes, each needs a unique ID (0 to max_machine_id).

**Your task:** Add a constructor parameter (e.g. `machine_id: int = 0`). Validate it fits in the allocated bits. Use it when packing the ID.

---

## Step 8: Interface and packaging

- Expose a class (e.g. `SnowflakeIdGenerator(machine_id=0, epoch=..., time_func=...)`) with a method that returns the next ID (int or str).
- Put it in a module (e.g. `id_generator/snowflake.py`). Add an `exceptions` module if you raise custom errors (e.g. `ClockBackwardError`).
- Add a short README and link to `docs/01` and `docs/02` and this file.

---

## Suggested file layout

```
ID Generator Design/
  id_generator/
    __init__.py      # export SnowflakeIdGenerator, exceptions
    exceptions.py    # ClockBackwardError or similar
    snowflake.py     # your generator class and bit-packing
  docs/
    01-first-principles.md
    02-design-approaches.md
    03-implementation-steps.md
  tests/
    test_snowflake.py  # use fake time, assert uniqueness and ordering
  README.md
```

---

## Testing hints

- Use a **fake time function** that you control (e.g. returns 1000, then 1000, then 1001). Assert that two IDs in the same "ms" have the same timestamp part and different sequence; two IDs in different "ms" have different timestamp parts.
- Assert **uniqueness**: generate many IDs in a loop (same ms in tests), check all unique.
- Assert **ordering**: generate with increasing time, check IDs are strictly increasing.
- Test **sequence overflow**: fake time fixed at one ms, generate (max_sequence + 1) IDs; assert no duplicate and no crash.
- Test **clock backward**: fake time goes 1000 → 999; assert your chosen behavior (exception or advance).

Start with Step 1 (constants and layout); then Steps 2–4 (time, state, happy-path generate). Once that works, add overflow, clock-backward, and machine_id. If you share your bit layout and one or two methods (e.g. "how I pack bits" or "how I advance time"), we can refine the next step without giving full code.
