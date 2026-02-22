"""
Snowflake-style unique ID generator.

Produces 64-bit IDs from: timestamp (ms since epoch) + machine ID + sequence.
IDs are unique per generator (and across generators if machine_id differs),
roughly time-ordered, and do not require a central database.
"""

import time
from typing import Callable

from id_generator.exceptions import ClockBackwardError


# -----------------------------------------------------------------------------
# Step 1: Bit layout constants (Snowflake default)
# -----------------------------------------------------------------------------
# We use 63 bits total to stay in positive 64-bit signed range if needed.
# Layout: [timestamp: 41 bits][machine_id: 10 bits][sequence: 12 bits]
#
# - 41 bits timestamp: milliseconds since epoch → ~69 years of range.
# - 10 bits machine_id: 0..1023 distinct machines/processes.
# - 12 bits sequence: 0..4095 IDs per millisecond per machine.
# -----------------------------------------------------------------------------

BITS_TIMESTAMP = 41
BITS_MACHINE_ID = 10
BITS_SEQUENCE = 12

# Maximum value each field can hold (inclusive max for sequence is 4095)
MAX_SEQUENCE = (1 << BITS_SEQUENCE) - 1  # 4095
MAX_MACHINE_ID = (1 << BITS_MACHINE_ID) - 1  # 1023

# Bit positions: we pack timestamp in the high bits, then machine, then sequence.
# ID = (timestamp << (BITS_MACHINE_ID + BITS_SEQUENCE)) | (machine_id << BITS_SEQUENCE) | sequence
SHIFT_TIMESTAMP = BITS_MACHINE_ID + BITS_SEQUENCE  # 22
SHIFT_MACHINE_ID = BITS_SEQUENCE  # 12


# Default epoch: 2020-01-01 00:00:00 UTC (gives more headroom than Unix epoch)
# We store epoch in milliseconds for direct use in "ms since epoch" math.
DEFAULT_EPOCH_MS = 1577836800000  # 2020-01-01 00:00:00.000 UTC in ms


def _default_time_ms() -> int:
    """
    Step 2: Time source.
    Returns current time in milliseconds since Unix epoch.
    We subtract our custom epoch in the generator so IDs use "ms since DEFAULT_EPOCH_MS".
    """
    return int(time.time() * 1000)


class SnowflakeIdGenerator:
    """
    Generates unique 64-bit IDs using the Snowflake layout:
    timestamp (41 bits) + machine_id (10 bits) + sequence (12 bits).

    - Uniqueness: same machine + same ms → sequence differs; different machines → machine_id differs.
    - Ordering: IDs increase over time because timestamp occupies the high bits.
    - Clock backward: we raise ClockBackwardError (no silent duplicates).
    - Sequence overflow: if we need more than 4096 IDs in one ms, we advance the logical
      timestamp by 1 ms and reset sequence (IDs stay unique and ordered).
    """

    def __init__(
        self,
        machine_id: int = 0,
        epoch_ms: int = DEFAULT_EPOCH_MS,
        time_func: Callable[[], int] | None = None,
    ):
        """
        :param machine_id: Unique ID for this process/node (0..1023). Must be same for
            all calls from this process, different across processes.
        :param epoch_ms: Start of our time range in ms (Unix time). IDs store "ms since epoch_ms".
        :param time_func: Optional function returning current time in ms (Unix). Used for tests.
        """
        if not 0 <= machine_id <= MAX_MACHINE_ID:
            raise ValueError(f"machine_id must be in [0, {MAX_MACHINE_ID}], got {machine_id}")
        self._machine_id = machine_id
        self._epoch_ms = epoch_ms
        # Step 2: Injectable time so tests can use a fake clock.
        self._time_ms = time_func if time_func is not None else _default_time_ms

        # Step 3: Per-generator state
        # last_timestamp_ms is in "ms since epoch" (our custom epoch).
        self._last_timestamp_ms: int = 0
        self._sequence: int = 0

    def generate(self) -> int:
        """
        Generate the next unique ID.

        :return: 64-bit integer ID (timestamp in high bits, then machine_id, then sequence).
        :raises ClockBackwardError: If the clock moved backward since the last generation.
        """
        # Step 2: Get current time and convert to "ms since our epoch"
        current_ms = self._time_ms() - self._epoch_ms
        if current_ms < 0:
            raise ValueError(
                f"Current time is before epoch. epoch_ms={self._epoch_ms}, time_ms={self._time_ms()}"
            )

        # Step 6: Clock moved backward — reject to avoid duplicates or ordering issues
        if current_ms < self._last_timestamp_ms:
            raise ClockBackwardError(
                last_ms=self._last_timestamp_ms,
                current_ms=current_ms,
            )

        # Step 4 & 5: Advance state
        if current_ms == self._last_timestamp_ms:
            # Same millisecond: increment sequence
            self._sequence += 1
            # Step 5: Sequence overflow — advance logical timestamp and reset sequence
            if self._sequence > MAX_SEQUENCE:
                self._last_timestamp_ms += 1
                self._sequence = 0
        else:
            # New millisecond: reset sequence
            self._last_timestamp_ms = current_ms
            self._sequence = 0

        # Step 4: Pack (timestamp, machine_id, sequence) into one 64-bit integer
        # High bits = timestamp (so IDs sort by time), then machine_id, then sequence.
        id_value = (
            (self._last_timestamp_ms << SHIFT_TIMESTAMP)
            | (self._machine_id << SHIFT_MACHINE_ID)
            | self._sequence
        )
        return id_value

    def next_id(self) -> int:
        """Alias for generate() for API familiarity."""
        return self.generate()
