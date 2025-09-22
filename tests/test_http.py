from __future__ import annotations

import pytest
import requests

from src.crawler.http import (
    GET,
    HttpClientError,
    HttpConnectionError,
    HttpNetworkError,
    HttpServerError,
    HttpTimeoutError,
    HttpUnexpectedStatusError,
    RetryConfig,
)


def _response_with_status(status_code: int, url: str = "https://example.com") -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = b""  # type: ignore[attr-defined]
    response.url = url
    return response


def test_get_returns_response(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _response_with_status(200)
    captured = {}

    def fake_get(url: str, timeout: float, headers: dict[str, str] | None) -> requests.Response:
        captured["url"] = url
        captured["timeout"] = timeout
        captured["headers"] = headers
        return response

    monkeypatch.setattr("src.crawler.http.requests.get", fake_get)

    result = GET("https://example.com/api", timeout=5.0, headers={"X-Test": "1"})

    assert result is response
    assert captured["url"] == "https://example.com/api"
    assert captured["timeout"] == 5.0
    assert captured["headers"] == {"X-Test": "1"}


def test_get_maps_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _response_with_status(404)

    monkeypatch.setattr("src.crawler.http.requests.get", lambda *_, **__: response)

    with pytest.raises(HttpClientError) as excinfo:
        GET("https://example.com/missing", timeout=2.0)

    err = excinfo.value
    assert err.status_code == 404
    assert err.response is response
    assert err.url == "https://example.com/missing"


def test_get_maps_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _response_with_status(503)

    monkeypatch.setattr("src.crawler.http.requests.get", lambda *_, **__: response)

    with pytest.raises(HttpServerError) as excinfo:
        GET("https://example.com/service", timeout=1.0)

    err = excinfo.value
    assert err.status_code == 503
    assert err.response is response


def test_get_maps_unexpected_status(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _response_with_status(302)

    monkeypatch.setattr("src.crawler.http.requests.get", lambda *_, **__: response)

    with pytest.raises(HttpUnexpectedStatusError) as excinfo:
        GET("https://example.com/redirect", timeout=1.0)

    assert excinfo.value.status_code == 302


def test_get_maps_timeout_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_timeout(*_: object, **__: object) -> None:
        raise requests.exceptions.Timeout("boom")

    monkeypatch.setattr("src.crawler.http.requests.get", raise_timeout)

    with pytest.raises(HttpTimeoutError) as excinfo:
        GET("https://example.com/slow", timeout=1.5)

    err = excinfo.value
    assert err.timeout == 1.5
    assert isinstance(err.original, requests.exceptions.Timeout)


def test_get_maps_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    exc = requests.exceptions.ConnectionError("disconnected")

    def raise_connection(*_: object, **__: object) -> None:
        raise exc

    monkeypatch.setattr("src.crawler.http.requests.get", raise_connection)

    with pytest.raises(HttpConnectionError) as excinfo:
        GET("https://example.com/socket", timeout=1.0)

    assert excinfo.value.original is exc


def test_get_maps_generic_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    exc = requests.exceptions.RequestException("generic failure")

    def raise_generic(*_: object, **__: object) -> None:
        raise exc

    monkeypatch.setattr("src.crawler.http.requests.get", raise_generic)

    with pytest.raises(HttpNetworkError) as excinfo:
        GET("https://example.com/errors", timeout=1.0)

    assert excinfo.value.original is exc


def test_get_retries_on_configured_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts: list[int] = []
    response = _response_with_status(200)

    def flaky_get(*_: object, **__: object) -> requests.Response:
        attempts.append(1)
        if len(attempts) < 3:
            raise requests.exceptions.ConnectionError("temporary failure")
        return response

    monkeypatch.setattr("src.crawler.http.requests.get", flaky_get)
    monkeypatch.setattr("src.utils.retry.time.sleep", lambda _: None)

    config = RetryConfig(max_attempts=3, initial_delay=0, backoff_factor=1.0, retry_on=(HttpNetworkError,))

    result = GET("https://example.com/flaky", timeout=2.0, retry=config)

    assert result is response
    assert len(attempts) == 3


def test_get_does_not_retry_on_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts: list[int] = []

    def always_404(*_: object, **__: object) -> requests.Response:
        attempts.append(1)
        return _response_with_status(429)

    monkeypatch.setattr("src.crawler.http.requests.get", always_404)
    monkeypatch.setattr("src.utils.retry.time.sleep", lambda _: None)

    config = RetryConfig(max_attempts=5, retry_on=(HttpNetworkError,))

    with pytest.raises(HttpClientError):
        GET("https://example.com/rate-limited", timeout=1.0, retry=config)

    assert len(attempts) == 1