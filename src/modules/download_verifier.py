"""Utilities to validate browser downloads using file system heuristics."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional


class DownloadVerifier:
    """Verify that a browser download finished successfully."""

    def __init__(self, folder: Path, settings: Optional[Dict[str, Any]], logger: Callable[[str, str], None]):
        self.folder = folder
        self.settings = settings or {}
        self.log = logger

    def wait_for_completion(self, extensions: Iterable[str], baseline: Optional[Iterable[str]] = None) -> Optional[Path]:
        """Wait until a new file with one of the expected extensions is stable.

        Parameters
        ----------
        extensions:
            Iterable of file extensions (with or without leading dots) to accept.
        baseline:
            Optional iterable of filenames that should be treated as pre-existing.
        """
        allowed_exts = {self._normalize_ext(ext) for ext in extensions}
        temp_exts = {self._normalize_ext(ext) for ext in self.settings.get(
            "temporary_extensions", [".crdownload", ".part", ".tmp"]
        )}

        stable_checks = max(1, int(self.settings.get("stable_checks", 3)))
        poll_interval = max(0.05, float(self.settings.get("poll_interval", 0.5)))
        backoff_factor = max(1.0, float(self.settings.get("backoff_factor", 1.5)))
        max_interval = max(poll_interval, float(self.settings.get("max_interval", poll_interval * 4)))
        max_timeout = max(0.0, float(self.settings.get("max_timeout", 60.0)))
        max_attempts = max(0, int(self.settings.get("max_attempts", 0)))

        open_retry = max(1, int(self.settings.get("open_retry", 3)))
        open_backoff = max(0.05, float(self.settings.get("open_backoff", 0.75)))

        baseline_names = set(baseline or [f.name for f in self.folder.glob("*")])
        tracked: Dict[str, Dict[str, Any]] = {}
        attempt_counter = 0
        interval = poll_interval
        start_time = time.time()
        deadline = start_time + max_timeout if max_timeout > 0 else None

        while True:
            now = time.time()
            if deadline and now >= deadline:
                self.log("ERROR", f"다운로드 검증 타임아웃 ({max_timeout:.1f}s)")
                return None
            if max_attempts and attempt_counter >= max_attempts:
                self.log("ERROR", f"다운로드 검증 최대 반복 초과 ({max_attempts})")
                return None

            attempt_counter += 1
            current_files = {f.name: f for f in self.folder.glob("*")}
            progress_made = False

            # purge tracked entries for files that vanished (e.g., renamed temp files)
            for name in list(tracked.keys()):
                if name not in current_files:
                    del tracked[name]

            # detect new files
            new_entries = [name for name in current_files if name not in baseline_names]
            for name in new_entries:
                baseline_names.add(name)
                progress_made = True
                fpath = current_files[name]
                if fpath.suffix.lower() in temp_exts:
                    tracked[name] = {"path": fpath, "type": "temp"}
                elif fpath.suffix.lower() in allowed_exts:
                    tracked[name] = {
                        "path": fpath,
                        "type": "final",
                        "stable": 1,
                        "size": fpath.stat().st_size if fpath.exists() else 0,
                    }

            # detect overwritten files that existed before the baseline snapshot
            for name, fpath in current_files.items():
                if name in tracked:
                    continue
                try:
                    modified_after_start = fpath.stat().st_mtime >= start_time
                except OSError:
                    continue
                if not modified_after_start:
                    continue
                suffix = fpath.suffix.lower()
                if suffix in temp_exts:
                    tracked[name] = {"path": fpath, "type": "temp"}
                    progress_made = True
                elif suffix in allowed_exts:
                    tracked[name] = {
                        "path": fpath,
                        "type": "final",
                        "stable": 1,
                        "size": fpath.stat().st_size if fpath.exists() else 0,
                    }
                    progress_made = True

            # check for temp files
            temp_active = any(entry.get("type") == "temp" for entry in tracked.values())
            if temp_active:
                self.log("DEBUG", "임시 다운로드 파일 감지 - 안정화 대기")
            else:
                for name, entry in list(tracked.items()):
                    if entry.get("type") != "final":
                        continue
                    fpath: Path = entry["path"]
                    if not fpath.exists():
                        # File removed before stabilizing; drop tracker
                        del tracked[name]
                        continue
                    try:
                        size = fpath.stat().st_size
                    except OSError as exc:
                        self.log("WARNING", f"파일 크기 확인 실패({fpath.name}): {exc}")
                        continue

                    if size == entry["size"]:
                        entry["stable"] += 1
                    else:
                        entry["stable"] = 1
                        entry["size"] = size
                        progress_made = True
                        self.log("DEBUG", f"파일 크기 변동 감지({fpath.name}): {size} bytes")

                    if entry["stable"] >= stable_checks:
                        if self._wait_openable(fpath, open_retry, open_backoff, deadline):
                            self.log("SUCCESS", f"다운로드 완료: {fpath.name}")
                            return fpath
                        self.log("ERROR", f"파일 핸들을 열 수 없습니다: {fpath.name}")
                        return None

            if progress_made:
                interval = poll_interval
            time.sleep(interval)
            interval = min(interval * backoff_factor, max_interval)

    def _wait_openable(
        self,
        path: Path,
        retries: int,
        backoff: float,
        deadline: Optional[float],
    ) -> bool:
        """Ensure the file handle can be opened within the deadline."""
        wait_time = backoff
        for attempt in range(1, retries + 1):
            if deadline and time.time() >= deadline:
                return False
            try:
                with path.open("rb"):
                    return True
            except OSError as exc:
                self.log("WARNING", f"파일 열기 대기({attempt}/{retries}): {exc}")
                if attempt >= retries:
                    break
                time.sleep(wait_time)
                wait_time *= 1.5
        return False

    @staticmethod
    def _normalize_ext(ext: str) -> str:
        ext = ext.strip()
        if not ext:
            return ""
        ext = ext.lower()
        return ext if ext.startswith(".") else f".{ext}"
