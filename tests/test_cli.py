from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = PROJECT_ROOT / "src" / "pipeline" / "cli.py"

def _run_cli(arguments):
    result = subprocess.run(
        [sys.executable, str(CLI_PATH), *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result

def _first_payload(stdout: str):
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError("CLI produced no output")
    return json.loads(lines[0])

def test_pipeline_run_default_parses_and_composes():
    result = _run_cli(["run", "--limit", "1"])

    assert result.returncode == 0, result.stderr
    payload = _first_payload(result.stdout)
    assert payload["parse"]["company"] == "Acme Corp"
    assert payload["compose"]["meta"]["cta"] == "Schedule a discovery call"

def test_pipeline_range_excludes_parse_when_not_requested():
    result = _run_cli(["run", "--from", "normalize", "--to", "compose", "--limit", "1"])

    assert result.returncode == 0, result.stderr
    payload = _first_payload(result.stdout)
    assert "parse" not in payload
    assert payload["normalize"]["meta"]["quality"] == "complete"

def test_pipeline_rejects_invalid_stage_order():
    result = _run_cli(["run", "--from", "compose", "--to", "parse"])

    assert result.returncode != 0
    assert "--from stage must not come after --to stage" in result.stderr
