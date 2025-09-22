from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple, Type

import requests
from requests import Response
from requests import exceptions as requests_exceptions

from src.utils.retry import retry as retry_call

Headers = Mapping[str, str]


class HttpError(RuntimeError):
    """Base exception for HTTP-related failures."""

    def __init__(self, message: str, *, url: str) -> None:
        super().__init__(message)
        self.url = url


class HttpStatusError(HttpError):
    """Base exception for HTTP errors derived from response status codes."""

    def __init__(self, message: str, *, url: str, status_code: int, response: Response) -> None:
        super().__init__(message, url=url)
        self.status_code = status_code
        self.response = response


class HttpClientError(HttpStatusError):
    """Raised when a 4xx client error response is received."""


class HttpServerError(HttpStatusError):
    """Raised when a 5xx server error response is received."""


class HttpUnexpectedStatusError(HttpStatusError):
    """Raised for non-successful status codes outside of 4xx and 5xx."""


class HttpNetworkError(HttpError):
    """Base exception for network-level request failures."""

    def __init__(self, message: str, *, url: str, original: BaseException | None = None) -> None:
        super().__init__(message, url=url)
        self.original = original


class HttpTimeoutError(HttpNetworkError):
    """Raised when a request exceeds the provided timeout."""

    def __init__(self, *, url: str, timeout: float, original: BaseException | None = None) -> None:
        super().__init__(f"Request to {url} timed out after {timeout} seconds", url=url, original=original)
        self.timeout = timeout


class HttpConnectionError(HttpNetworkError):
    """Raised when the client cannot establish a connection to the host."""

    def __init__(self, *, url: str, original: BaseException | None = None) -> None:
        super().__init__(f"Failed to connect to {url}", url=url, original=original)


@dataclass(frozen=True)
class RetryConfig:
    """Configuration describing how GET should retry transient failures."""

    max_attempts: int = 3
    timeout: float | None = None
    initial_delay: float = 0.1
    backoff_factor: float = 2.0
    max_delay: float | None = None
    retry_on: Tuple[Type[BaseException], ...] = (HttpNetworkError, HttpServerError)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if not self.retry_on:
            raise ValueError("retry_on must contain at least one exception type")


def _coerce_headers(headers: Mapping[str, str] | None) -> Mapping[str, str] | None:
    if headers is None:
        return None
    if isinstance(headers, dict):
        return headers
    return dict(headers)


def _normalise_response(response: Response, *, url: str) -> Response:
    status = response.status_code
    if 200 <= status < 300:
        return response
    if 400 <= status < 500:
        raise HttpClientError(
            f"HTTP {status} returned for {url}", url=url, status_code=status, response=response
        )
    if 500 <= status < 600:
        raise HttpServerError(
            f"HTTP {status} returned for {url}", url=url, status_code=status, response=response
        )
    raise HttpUnexpectedStatusError(
        f"Unexpected HTTP status {status} returned for {url}",
        url=url,
        status_code=status,
        response=response,
    )


def _request_once(url: str, *, timeout: float, headers: Mapping[str, str] | None) -> Response:
    try:
        response = requests.get(url, timeout=timeout, headers=_coerce_headers(headers))
    except requests_exceptions.Timeout as exc:
        raise HttpTimeoutError(url=url, timeout=timeout, original=exc) from exc
    except requests_exceptions.ConnectionError as exc:
        raise HttpConnectionError(url=url, original=exc) from exc
    except requests_exceptions.RequestException as exc:
        raise HttpNetworkError(f"Request to {url} failed: {exc}", url=url, original=exc) from exc

    if response.url is None:
        response.url = url  # type: ignore[assignment]

    return _normalise_response(response, url=url)


def GET(
    url: str,
    *,
    timeout: float,
    headers: Mapping[str, str] | None = None,
    retry: RetryConfig | None = None,
) -> Response:
    """Perform a GET request with consistent error mapping."""

    config = retry if retry is not None else RetryConfig(max_attempts=1, retry_on=(HttpNetworkError, HttpServerError))

    if config.max_attempts <= 1:
        return _request_once(url, timeout=timeout, headers=headers)

    wrapped = retry_call(
        config.retry_on,
        max_attempts=config.max_attempts,
        timeout=config.timeout,
        initial_delay=config.initial_delay,
        backoff_factor=config.backoff_factor,
        max_delay=config.max_delay,
    )(_request_once)

    return wrapped(url, timeout=timeout, headers=headers)