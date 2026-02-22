"""Abstract base interface for rate limiters."""

from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Abstract base class for all rate limiter implementations."""

    @abstractmethod
    def allow(self, identifier: str) -> bool:
        """
        Check whether a request from the given identifier should be allowed.

        :param identifier: A string identifying the client (e.g. user ID, IP address).
        :return: True if the request is allowed, False if rate limited.
        """
        pass

    def raise_if_not_allowed(self, identifier: str) -> None:
        """
        If the request is not allowed, raise RateLimitExceeded.
        Convenience method for allow-then-raise usage.

        :param identifier: A string identifying the client.
        :raises RateLimitExceeded: When the request is rate limited.
        """
        if not self.allow(identifier):
            from rate_limiter.exceptions import RateLimitExceeded

            raise RateLimitExceeded(identifier)
