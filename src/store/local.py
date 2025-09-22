from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Any

SNAPSHOT_DIR = Path("var") / "snapshots"
JSONL_SUFFIX = ".jsonl"
JSON_SUFFIX = ".json"


def _normalise_version(version: str | None) -> str:
    if version is None:
        version = f"v{int(time.time())}"
    if not version:
        raise ValueError("Snapshot version must be a non-empty string.")
    if not version.startswith("v"):
        raise ValueError("Snapshot version must start with 'v'.")
    return version


def _snapshot_path(version: str, suffix: str = JSONL_SUFFIX) -> Path:
    return SNAPSHOT_DIR / f"{version}{suffix}"


def save_snapshot(records: Iterable[Any], version: str | None = None) -> str:
    """Persist *records* to disk as JSON Lines and return the snapshot version."""
    resolved_version = _normalise_version(version)
    target = _snapshot_path(resolved_version)
    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")

    return resolved_version


def load_snapshot(version: str) -> Any:
    """Load snapshot *version* from disk.

    The loader prefers JSON Lines snapshots, but will fall back to JSON if present.
    """
    resolved_version = _normalise_version(version)

    jsonl_path = _snapshot_path(resolved_version, JSONL_SUFFIX)
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    json_path = _snapshot_path(resolved_version, JSON_SUFFIX)
    if json_path.exists():
        with json_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    raise FileNotFoundError(f"Snapshot '{resolved_version}' not found.")
