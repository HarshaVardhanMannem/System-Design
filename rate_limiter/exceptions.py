"""Custom exceptions for the rate limiter."""


class RateLimitExceeded(Exception):
    """Raised when a request is rejected because the rate limit has been exceeded."""

    def __init__(self, identifier: str, message: str | None = None):
        self.identifier = identifier
        self.message = message or f"Rate limit exceeded for identifier: {identifier}"
        super().__init__(self.message)
