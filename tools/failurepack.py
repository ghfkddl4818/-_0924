from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable
from zipfile import ZIP_DEFLATED, ZipFile

ArchiveFactory = Callable[[Path], ZipFile]
Clock = Callable[[], datetime]


def create_failure_pack(
    inputs: Path | str | None,
    intermediates: Path | str | None,
    outputs: Path | str | None,
    destination: Path | str,
    *,
    zip_factory: ArchiveFactory | None = None,
    clock: Clock | None = None,
) -> Path:
    """Bundle inputs, intermediates, and outputs into a single archive."""

    archive_path = Path(destination)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    factory = zip_factory or _default_zip_factory
    now = clock or (lambda: datetime.now(timezone.utc))

    sections = [
        ("inputs", _optional_path(inputs)),
        ("intermediate", _optional_path(intermediates)),
        ("outputs", _optional_path(outputs)),
    ]

    manifest: dict[str, object] = {
        "generated_at": now().isoformat(),
        "sections": {},
    }

    with factory(archive_path) as archive:
        for name, root in sections:
            archived_files = []
            if root is not None and root.exists():
                for file_path in _iter_files(root):
                    arcname = Path(name) / file_path.relative_to(root)
                    archive.write(file_path, arcname.as_posix())
                    archived_files.append(arcname.as_posix())
            manifest["sections"][name] = archived_files
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

    return archive_path


def _iter_files(root: Path) -> Iterable[Path]:
    for candidate in sorted(root.rglob("*")):
        if candidate.is_file():
            yield candidate


def _optional_path(value: Path | str | None) -> Path | None:
    if value is None:
        return None
    return Path(value)


def _default_zip_factory(path: Path) -> ZipFile:
    return ZipFile(path, mode="w", compression=ZIP_DEFLATED)


__all__ = ["create_failure_pack"]