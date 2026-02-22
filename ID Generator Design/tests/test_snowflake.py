"""Tests for SnowflakeIdGenerator using a fake time source."""

import pytest
from id_generator import ClockBackwardError, SnowflakeIdGenerator
from id_generator.snowflake import MAX_SEQUENCE


class MockTimeMs:
    """Fake time in milliseconds for deterministic tests."""

    def __init__(self):
        self._ms = 0

    def set(self, ms: int) -> None:
        self._ms = ms

    def advance(self, delta_ms: int = 1) -> int:
        self._ms += delta_ms
        return self._ms

    def __call__(self) -> int:
        return self._ms


# Use a fixed epoch so "ms since epoch" is just our mock value when we set mock to return epoch + x
MOCK_EPOCH_MS = 1000000000000  # arbitrary base


def test_uniqueness_same_millisecond():
    """Multiple IDs in the same ms must have different sequence values → all unique."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS + 1000)  # one logical ms
    gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    ids = [gen.generate() for _ in range(100)]
    assert len(ids) == len(set(ids))


def test_ordering_across_milliseconds():
    """IDs must increase when time advances."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS)
    gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    id1 = gen.generate()
    t.advance(1)
    id2 = gen.generate()
    t.advance(1)
    id3 = gen.generate()
    assert id1 < id2 < id3


def test_same_ms_same_timestamp_bits_different_sequence():
    """Two IDs in same ms share timestamp part; sequence part differs."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS + 5000)
    gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    id1 = gen.generate()
    id2 = gen.generate()
    # Timestamp is high bits; sequence is low 12 bits. So id2 - id1 == 1 (sequence 0 vs 1)
    assert id2 - id1 == 1


def test_different_machine_id_different_ids():
    """Same logical time and sequence but different machine_id → different IDs."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS + 100)
    gen0 = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    gen1 = SnowflakeIdGenerator(machine_id=1, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    id0 = gen0.generate()
    id1 = gen1.generate()
    assert id0 != id1
    # Machine 1's ID is 1 << 12 higher in the middle bits
    assert id1 - id0 == 1 << 12


def test_sequence_overflow_advances_logical_time():
    """Generate more than 4096 IDs in one ms; no duplicate, no crash."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS + 2000)  # fixed ms
    gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    ids = [gen.generate() for _ in range(MAX_SEQUENCE + 2)]  # 4097 IDs
    assert len(ids) == len(set(ids))
    assert ids[-1] > ids[0]


def test_clock_backward_raises():
    """If time goes backward, generator raises ClockBackwardError."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS + 3000)
    gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    gen.generate()
    t.set(MOCK_EPOCH_MS + 2999)  # backward
    with pytest.raises(ClockBackwardError) as exc_info:
        gen.generate()
    assert exc_info.value.last_ms == 3000
    assert exc_info.value.current_ms == 2999


def test_machine_id_validation():
    """machine_id must be in [0, 1023]."""
    with pytest.raises(ValueError):
        SnowflakeIdGenerator(machine_id=-1)
    with pytest.raises(ValueError):
        SnowflakeIdGenerator(machine_id=1024)


def test_next_id_alias():
    """next_id() is an alias for generate()."""
    t = MockTimeMs()
    t.set(MOCK_EPOCH_MS + 100)
    gen = SnowflakeIdGenerator(machine_id=0, epoch_ms=MOCK_EPOCH_MS, time_func=t)
    a = gen.generate()
    b = gen.next_id()
    assert b > a
