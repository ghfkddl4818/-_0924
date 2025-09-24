import sys
import threading
import time
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from modules.download_verifier import DownloadVerifier


def test_download_verifier_waits_for_stable_size(tmp_path):
    log_messages = []

    def logger(level: str, message: str) -> None:
        log_messages.append((level, message))

    settings = {
        "poll_interval": 0.05,
        "backoff_factor": 1.0,
        "max_interval": 0.05,
        "max_timeout": 2.0,
        "stable_checks": 2,
        "open_retry": 2,
        "open_backoff": 0.05,
    }

    verifier = DownloadVerifier(tmp_path, settings, logger)
    final_file = tmp_path / "report.xlsx"

    finished = threading.Event()

    def simulate_download() -> None:
        temp_file = tmp_path / "report.xlsx.crdownload"
        with temp_file.open("wb") as handle:
            handle.write(b"0" * 10)
        time.sleep(0.1)
        temp_file.rename(final_file)
        with final_file.open("wb") as handle:
            handle.write(b"0" * 32)
        time.sleep(0.1)
        with final_file.open("ab") as handle:
            handle.write(b"1" * 32)
        finished.set()

    worker = threading.Thread(target=simulate_download)
    worker.start()

    result = verifier.wait_for_completion(["xlsx"])

    worker.join(timeout=2.0)
    assert not worker.is_alive()
    assert result == final_file
    assert final_file.exists()
    assert finished.is_set()
    # 다운로드 완료 로그가 남았는지 확인 (안정 확인 후 기록됨)
    assert any("다운로드 완료" in msg for _, msg in log_messages)
