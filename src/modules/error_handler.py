
import time, subprocess, requests
from enum import Enum

class ErrorType(Enum):
    IMAGE_NOT_FOUND = "image_not_found"
    DOWNLOAD_FAILED = "download_failed"
    BROWSER_HANG = "browser_hang"
    LLM_TIMEOUT = "llm_timeout"
    FILE_ACCESS_ERROR = "file_access_error"
    NETWORK_ERROR = "network_error"

class ErrorHandler:
    def __init__(self, config: dict, log_callback):
        self.c = config; self.log = log_callback

    def restart_browser(self):
        try:
            if self.c["web_automation"]["browser"] == "chrome":
                subprocess.run(["taskkill","/F","/IM","chrome.exe"], check=False)
                time.sleep(2)
                subprocess.Popen(["start","chrome"], shell=True)
                time.sleep(5)
                return True
        except Exception as e:
            self.log("ERROR", f"브라우저 재시작 실패: {e}")
        return False
