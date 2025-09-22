from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_REPORT_BASENAME = "run_report"


@dataclass(slots=True)
class RunReport:
    """In-memory representation of a single automation run."""

    run_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    totals: dict[str, int] = field(default_factory=dict)
    failures: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.totals = dict(self.totals)
        self.failures = tuple(dict(item) for item in self.failures)
        self.notes = tuple(str(note) for note in self.notes)
        self.metadata = dict(self.metadata)

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None
        try:
            delta = self.finished_at - self.started_at
        except TypeError as exc:
            raise TypeError(
                "started_at and finished_at must share timezone awareness"
            ) from exc
        return max(0.0, delta.total_seconds())

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "started_at": _isoformat(self.started_at),
            "finished_at": _isoformat(self.finished_at),
            "duration_seconds": self.duration_seconds,
            "totals": dict(self.totals),
            "failures": [dict(item) for item in self.failures],
            "notes": list(self.notes),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "RunReport":
        started_at = _parse_datetime(payload["started_at"])
        finished_at = _parse_datetime(payload.get("finished_at"))
        totals = payload.get("totals") or {}
        failures = payload.get("failures") or []
        notes = payload.get("notes") or []
        metadata = payload.get("metadata") or {}
        return cls(
            run_id=str(payload["run_id"]),
            status=str(payload["status"]),
            started_at=started_at,
            finished_at=finished_at,
            totals=dict(totals),
            failures=tuple(dict(item) for item in failures),
            notes=tuple(str(note) for note in notes),
            metadata=dict(metadata),
        )


def render_markdown(report: RunReport) -> str:
    data = report.to_json_dict()
    lines: list[str] = []

    lines.append(f"# Run Report `{report.run_id}`")
    lines.extend(["", "## Overview", ""])
    lines.append(f"- Status: **{report.status.upper()}**")
    lines.append(f"- Started: {data['started_at']}")
    if data["finished_at"]:
        lines.append(f"- Finished: {data['finished_at']}")
    else:
        lines.append("- Finished: N/A")
    if data["duration_seconds"] is not None:
        lines.append(f"- Duration: {data['duration_seconds']:.2f} seconds")

    totals = data["totals"]
    if totals:
        lines.extend(["", "## Totals", "", "| Metric | Value |", "| --- | ---: |"])
        for key in sorted(totals):
            lines.append(f"| {key} | {totals[key]} |")

    failures = data["failures"]
    if failures:
        lines.extend(["", "## Failures"])
        for idx, failure in enumerate(failures, start=1):
            title = (
                failure.get("title")
                or failure.get("name")
                or failure.get("step")
                or f"Failure {idx}"
            )
            lines.extend(["", f"### {idx}. {title}"])
            if failure.get("reason"):
                lines.append(f"- Reason: {failure['reason']}")
            extras = {
                key: value
                for key, value in failure.items()
                if key not in {"title", "name", "step", "reason"}
            }
            if extras:
                lines.extend(["", "```json", json.dumps(extras, indent=2, ensure_ascii=False), "```"])

    notes = data["notes"]
    if notes:
        lines.extend(["", "## Notes", ""])
        for note in notes:
            lines.append(f"- {note}")

    metadata = data["metadata"]
    if metadata:
        lines.extend(["", "## Metadata", "", "```json", json.dumps(metadata, indent=2, ensure_ascii=False), "```"])

    return "\n".join(lines) + "\n"


def write_run_report(report: RunReport | dict[str, Any], output_dir: str | Path) -> tuple[Path, Path]:
    if not isinstance(report, RunReport):
        report = RunReport.from_payload(dict(report))

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / f"{DEFAULT_REPORT_BASENAME}.json"
    markdown_path = output_path / f"{DEFAULT_REPORT_BASENAME}.md"

    json_payload = report.to_json_dict()
    json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    return json_path, markdown_path


def generate_run_report(payload: dict[str, Any], output_dir: str | Path | None = None) -> tuple[Path, Path]:
    if output_dir is None:
        output_dir = Path("reports")
    return write_run_report(payload, output_dir)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(f"Unsupported datetime format: {value!r}") from exc
    raise TypeError(f"Unsupported datetime value: {value!r}")


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


__all__ = [
    "RunReport",
    "generate_run_report",
    "render_markdown",
    "write_run_report",
]