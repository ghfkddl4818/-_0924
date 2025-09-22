from __future__ import annotations

import functools
import time
from typing import Callable, Iterable, Optional, Tuple, Type, TypeVar, Union, cast

T = TypeVar("T")
ExceptionTypes = Union[Type[BaseException], Iterable[Type[BaseException]]]
RetryCallback = Optional[Callable[[int, BaseException, float], None]]

__all__ = ["retry"]


def _normalize_exceptions(exceptions: ExceptionTypes) -> Tuple[Type[BaseException], ...]:
    """Return a tuple of exception types from the provided input."""
    if isinstance(exceptions, type) and issubclass(exceptions, BaseException):
        return (exceptions,)

    if isinstance(exceptions, Iterable):
        try:
            candidates = tuple(exceptions)
        except TypeError as error:  # pragma: no cover - defensive branch
            raise TypeError("exceptions iterable could not be materialised") from error

        if not candidates:
            raise ValueError("exceptions iterable cannot be empty")

        for candidate in candidates:
            if not isinstance(candidate, type) or not issubclass(candidate, BaseException):
                raise TypeError("exceptions iterable must contain only exception types")

        return cast(Tuple[Type[BaseException], ...], candidates)

    raise TypeError("exceptions must be an exception type or an iterable of exception types")


def _validate_parameters(
    max_attempts: int,
    timeout: Optional[float],
    initial_delay: float,
    backoff_factor: float,
    max_delay: Optional[float],
) -> None:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if timeout is not None and timeout <= 0:
        raise ValueError("timeout must be greater than 0 when provided")
    if initial_delay < 0:
        raise ValueError("initial_delay cannot be negative")
    if backoff_factor <= 0:
        raise ValueError("backoff_factor must be greater than 0")
    if max_delay is not None and max_delay <= 0:
        raise ValueError("max_delay must be greater than 0 when provided")


def _next_delay(current_delay: float, backoff_factor: float, max_delay: Optional[float]) -> float:
    next_delay = current_delay * backoff_factor if current_delay > 0 else 0.0
    if max_delay is not None:
        return min(next_delay, max_delay)
    return next_delay


def retry(
    exceptions: ExceptionTypes,
    *,
    max_attempts: int = 3,
    timeout: Optional[float] = None,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    max_delay: Optional[float] = None,
    on_retry: RetryCallback = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a callable with exponential backoff for whitelisted exceptions."""

    exc_types = _normalize_exceptions(exceptions)
    _validate_parameters(max_attempts, timeout, initial_delay, backoff_factor, max_delay)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempts = 1
            delay = initial_delay
            start_time = time.monotonic()

            while True:
                try:
                    return func(*args, **kwargs)
                except exc_types as exc:  # type: ignore[misc]
                    if attempts >= max_attempts:
                        raise

                    now = time.monotonic()
                    elapsed = now - start_time
                    if timeout is not None and elapsed >= timeout:
                        raise

                    sleep_for = delay
                    if timeout is not None:
                        remaining = timeout - elapsed
                        if remaining <= 0:
                            raise
                        sleep_for = min(sleep_for, remaining)

                    sleep_for = max(0.0, round(sleep_for, 6))

                    if on_retry is not None:
                        on_retry(attempts, exc, sleep_for)

                    if sleep_for > 0:
                        time.sleep(sleep_for)

                    attempts += 1
                    delay = _next_delay(delay, backoff_factor, max_delay)

        return wrapper

    return decorator
