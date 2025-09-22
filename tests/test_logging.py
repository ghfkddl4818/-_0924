import io
import json
import logging
from datetime import datetime

from src.app_logging import get_logger, get_trace_id, trace_context


def test_logger_emits_required_fields():
    logger = get_logger("test-json-logger")
    handler = logger.handlers[0]
    buffer = io.StringIO()
    handler.stream = buffer

    logger.info("structured hello")

    raw = buffer.getvalue().strip()
    data = json.loads(raw)

    assert set(data.keys()) == {"ts", "level", "module", "message", "trace_id"}
    assert data["module"] == "test-json-logger"
    assert data["message"] == "structured hello"
    assert data["level"] == "INFO"
    assert data["trace_id"] is None
    # Parse timestamp to ensure ISO8601 format with timezone.
    parsed_ts = datetime.fromisoformat(data["ts"])
    assert parsed_ts.tzinfo is not None


def test_trace_context_injects_trace_id_and_restores():
    logger = get_logger("test-trace-logger")
    handler = logger.handlers[0]
    buffer = io.StringIO()
    handler.stream = buffer

    assert get_trace_id() is None

    with trace_context("trace-123"):
        logger.warning("within trace context")
        assert get_trace_id() == "trace-123"

    assert get_trace_id() is None

    raw_lines = [line for line in buffer.getvalue().splitlines() if line]
    final_entry = json.loads(raw_lines[-1])
    assert final_entry["trace_id"] == "trace-123"
