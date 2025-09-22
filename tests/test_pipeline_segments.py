from __future__ import annotations

import io
import json
from pathlib import Path

from src.pipeline.segment_cli import run_range, run_stage

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read_lines(buffer: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in buffer.getvalue().splitlines() if line]


def test_run_stage_parse_outputs_expected_company() -> None:
    buffer = io.StringIO()
    run_stage(
        "parse",
        input_path=FIXTURES,
        limit=1,
        language="en",
        stream=buffer,
    )
    lines = read_lines(buffer)
    assert len(lines) == 1
    assert lines[0]["parse"]["company"] == "Acme Corp"


def test_run_stage_normalize_outputs_quality() -> None:
    buffer = io.StringIO()
    run_stage(
        "normalize",
        input_path=FIXTURES,
        limit=1,
        language="en",
        stream=buffer,
    )
    lines = read_lines(buffer)
    assert len(lines) == 1
    assert lines[0]["normalize"]["meta"]["quality"] == "complete"


def test_run_stage_compose_exposes_meta() -> None:
    buffer = io.StringIO()
    run_stage(
        "compose",
        input_path=FIXTURES,
        limit=1,
        language="en",
        stream=buffer,
    )
    lines = read_lines(buffer)
    assert len(lines) == 1
    assert lines[0]["compose"]["meta"]["cta"] == "Schedule a discovery call"


def test_run_range_returns_full_record() -> None:
    buffer = io.StringIO()
    run_range(
        from_stage="parse",
        to_stage="compose",
        input_path=FIXTURES,
        limit=1,
        language="en",
        stream=buffer,
    )
    lines = read_lines(buffer)
    assert len(lines) == 1
    payload = lines[0]
    assert "parse" in payload and "compose" in payload
