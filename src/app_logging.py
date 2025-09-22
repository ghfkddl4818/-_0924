"""Structured logging utilities for the automation system."""
from __future__ import annotations

import json
import logging
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Iterator, Optional

_TRACE_ID_VAR: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON suitable for machine consumption."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "trace_id": _TRACE_ID_VAR.get(),
        }
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured to emit JSON log lines."""

    logger = logging.getLogger(name)
    if not any(getattr(handler, "_structured", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler._structured = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def get_trace_id() -> Optional[str]:
    """Return the current trace identifier if one is active."""

    return _TRACE_ID_VAR.get()


@contextmanager
def trace_context(trace_id: Optional[str]) -> Iterator[Optional[str]]:
    """Temporarily bind a trace identifier for structured logging."""

    token = _TRACE_ID_VAR.set(trace_id)
    try:
        yield trace_id
    finally:
        _TRACE_ID_VAR.reset(token)


def set_trace_id(trace_id: Optional[str]) -> None:
    """Bind a trace identifier without a context manager."""

    _TRACE_ID_VAR.set(trace_id)
