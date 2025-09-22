from __future__ import annotations

import itertools

import pytest

from src.utils.retry import retry


class TransientError(RuntimeError):
    """Custom exception used for testing."""


def test_retry_retries_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_durations: list[float] = []
    monkeypatch.setattr("src.utils.retry.time.sleep", sleep_durations.append)

    attempts: list[int] = []

    @retry(TransientError, max_attempts=5, initial_delay=0.1, backoff_factor=2.0)
    def flaky() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise TransientError("transient failure")
        return "ok"

    assert flaky() == "ok"
    assert len(attempts) == 3
    assert sleep_durations == [0.1, 0.2]


def test_retry_raises_after_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.utils.retry.time.sleep", lambda *_: None)

    attempts = {"count": 0}

    @retry(TransientError, max_attempts=3, initial_delay=0)
    def always_fail() -> None:
        attempts["count"] += 1
        raise TransientError("permanent failure")

    with pytest.raises(TransientError):
        always_fail()

    assert attempts["count"] == 3


def test_retry_honors_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    times = itertools.chain([0.0, 0.4, 0.9], itertools.repeat(0.9))
    monkeypatch.setattr("src.utils.retry.time.monotonic", lambda: next(times))

    sleep_durations: list[float] = []
    monkeypatch.setattr("src.utils.retry.time.sleep", sleep_durations.append)

    attempts = {"count": 0}

    @retry(TransientError, max_attempts=5, timeout=0.5, initial_delay=0.3)
    def flaky() -> None:
        attempts["count"] += 1
        raise TransientError("timeout trigger")

    with pytest.raises(TransientError):
        flaky()

    assert attempts["count"] == 2
    assert sleep_durations == [0.1]
