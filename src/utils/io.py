from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

PathLike = Union[str, Path]

__all__ = ["read_text", "write_text", "append_text", "append_jsonl"]


def _ensure_parent(path: Path) -> Path:
    parent = path.parent
    anchor_path = Path(parent.anchor) if parent.anchor else Path(".")
    if parent and parent != anchor_path:
        parent.mkdir(parents=True, exist_ok=True)
    return path


def read_text(path: PathLike) -> str:
    """Read UTF-8 text from *path*."""
    return Path(path).read_text(encoding="utf-8")


def write_text(path: PathLike, content: str) -> None:
    """Write *content* to *path* using UTF-8 encoding."""
    target = _ensure_parent(Path(path))
    target.write_text(content, encoding="utf-8")


def append_text(path: PathLike, content: str) -> None:
    """Append *content* to *path* using UTF-8 encoding."""
    target = _ensure_parent(Path(path))
    with target.open("a", encoding="utf-8") as handle:
        handle.write(content)


def append_jsonl(path: PathLike, record: Any) -> None:
    """Append *record* as a JSON object on a new line in *path*."""
    target = _ensure_parent(Path(path))
    line = json.dumps(record, separators=(",", ":"))
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
