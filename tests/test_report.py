import json
import zipfile
from datetime import datetime, timedelta, timezone

import pytest

from src.observe.report import RunReport, render_markdown, write_run_report
from tools.failurepack import create_failure_pack


def test_write_run_report_creates_outputs(tmp_path):
    start = datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc)
    finish = start + timedelta(seconds=303)
    payload = {
        "run_id": "alpha-1",
        "status": "succeeded",
        "started_at": start,
        "finished_at": finish,
        "totals": {"processed": 10, "failed": 1},
        "failures": [{"step": "ingest", "reason": "timeout", "code": "TIMEOUT"}],
        "notes": ["Investigate ingest timeout"],
        "metadata": {"operator": "bot"},
    }

    json_path, markdown_path = write_run_report(payload, tmp_path)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["run_id"] == "alpha-1"
    assert data["duration_seconds"] == pytest.approx(303.0)
    assert data["failures"][0]["step"] == "ingest"

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Run Report `alpha-1`" in markdown
    assert "| processed | 10 |" in markdown
    assert "- Duration: 303.00 seconds" in markdown
    assert "Investigate ingest timeout" in markdown


def test_run_report_from_payload_supports_iso_strings():
    payload = {
        "run_id": "beta",
        "status": "running",
        "started_at": "2024-04-01T12:00:00Z",
        "notes": ["Pipeline still running"],
    }

    report = RunReport.from_payload(payload)

    assert report.finished_at is None
    assert report.duration_seconds is None

    markdown = render_markdown(report)
    assert "- Finished: N/A" in markdown
    assert "Pipeline still running" in markdown


def test_create_failure_pack_builds_archive_with_manifest(tmp_path):
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "config.json").write_text("{}\n", encoding="utf-8")

    intermediate_dir = tmp_path / "intermediate"
    intermediate_dir.mkdir()
    (intermediate_dir / "trace.log").write_text("trace\n", encoding="utf-8")

    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    (outputs_dir / "result.txt").write_text("result\n", encoding="utf-8")

    archive_target = tmp_path / "bundle.zip"
    timestamp = datetime(2024, 4, 1, 0, 0, tzinfo=timezone.utc)

    archive_path = create_failure_pack(
        inputs_dir,
        intermediate_dir,
        outputs_dir,
        archive_target,
        clock=lambda: timestamp,
    )

    assert archive_path == archive_target
    assert archive_path.exists()

    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

        assert manifest["generated_at"] == "2024-04-01T00:00:00+00:00"
        assert manifest["sections"]["inputs"] == ["inputs/config.json"]
        assert manifest["sections"]["intermediate"] == ["intermediate/trace.log"]
        assert manifest["sections"]["outputs"] == ["outputs/result.txt"]

        assert archive.read("outputs/result.txt").decode("utf-8") == "result\n"