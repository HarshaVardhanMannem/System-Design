"""Custom exceptions for the ID generator."""


class ClockBackwardError(Exception):
    """
    Raised when the system clock has moved backward relative to the last
    timestamp used for ID generation. Generating would risk duplicate or
    out-of-order IDs, so we fail fast instead.
    """

    def __init__(self, last_ms: int, current_ms: int, message: str | None = None):
        self.last_ms = last_ms
        self.current_ms = current_ms
        self.message = (
            message
            or f"Clock moved backward: last_timestamp_ms={last_ms}, current_ms={current_ms}"
        )
        super().__init__(self.message)
