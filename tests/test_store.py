from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.store import local


def test_save_and_load_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    records = [
        {"id": 1, "name": "alpha"},
        {"id": 2, "name": "beta", "meta": {"active": True}},
    ]
    snapshot_dir = tmp_path / "snapshots"
    monkeypatch.setattr(local, "SNAPSHOT_DIR", snapshot_dir)

    version = local.save_snapshot(records, version="v1234567890")

    assert version == "v1234567890"
    snapshot_path = snapshot_dir / "v1234567890.jsonl"
    assert snapshot_path.exists()
    assert snapshot_path.read_text(encoding="utf-8").count("\n") == len(records)

    loaded = local.load_snapshot("v1234567890")
    assert loaded == records


def test_load_snapshot_json_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local, "SNAPSHOT_DIR", tmp_path)

    payload = {"foo": "bar"}
    json_path = tmp_path / "v987654321.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")

    assert local.load_snapshot("v987654321") == payload


def test_load_snapshot_missing_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local, "SNAPSHOT_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        local.load_snapshot("v000000000")
