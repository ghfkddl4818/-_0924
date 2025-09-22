
import time, os
from pathlib import Path
from typing import Callable, List
import pyautogui

from .image_matcher import EnhancedImageMatcher
from .error_handler import ErrorHandler

class WebAutomation:
    def __init__(self, config: dict, log_callback: Callable, step_callback: Callable, done_callback: Callable):
        self.c = config; self.log = log_callback
        self.set_step = step_callback; self.on_item_done = done_callback
        self.matcher = EnhancedImageMatcher(config)
        self.err = ErrorHandler(config, log_callback)

    def reset_counts(self, total: int):
        self.total = total
        self.processed = 0

    def process_single_product(self, idx: int) -> bool:
        self.set_step("DETAIL", 0)
        if not self._click_detail(): return False
        self.set_step("CAPTURE", 20)
        if not self._fireshot_capture(): return False
        self.set_step("DOWNLOAD", 40)
        if not self._download_reviews(): return False
        self.set_step("ORGANIZE", 70)
        # 정리는 DataProcessor가 메인에서 호출 가능. 여기서는 스텁.
        self.set_step("EMAIL", 90)
        # 이메일 생성은 별도 모듈에서. 여기서는 성공으로 표기.
        self.set_step("DONE", 100)
        self.on_item_done()
        if self.c["web_automation"]["close_after_process"]:
            pyautogui.hotkey(*self.c["web_automation"]["buttons"]["navigation"]["close_tab"].split("+"))
            time.sleep(self.c["web_automation"]["tab_switch_delay"])
        else:
            pyautogui.hotkey(*self.c["web_automation"]["buttons"]["navigation"]["next_tab"].split("+"))
            time.sleep(self.c["web_automation"]["tab_switch_delay"])
        return True

    # ---- steps ----
    def _click_detail(self) -> bool:
        b = self.c["web_automation"]["buttons"]["detail"]
        ok = self.matcher.find_and_click(b["primary"], confidence=b["confidence"], retry=b["retry"],
                                         region=b.get("search_region"), wait_after=b["wait_after"])
        if not ok and b.get("alternative"):
            self.log("WARNING", "메인 실패 → 대체 이미지 시도")
            ok = self.matcher.find_and_click(b["alternative"], confidence=b["confidence"]*0.95, retry=3)
        if not ok:
            self.log("ERROR", "상세 버튼 클릭 실패")
        return ok

    def _fireshot_capture(self) -> bool:
        try:
            trig = self.c["web_automation"]["buttons"]["fireshot"]["trigger_key"]
            pyautogui.hotkey(*trig.split("+"))
            time.sleep(1.0)
            btn = self.c["web_automation"]["buttons"]["fireshot"]
            ok = self.matcher.find_and_click(btn["save_button"], confidence=btn["confidence"], timeout=btn["timeout"])
            if ok: time.sleep(btn["wait_after"])
            if not ok: self.log("ERROR", "Fireshot 저장 버튼을 찾지 못함")
            return ok
        except Exception as e:
            self.log("ERROR", f"Fireshot 실패: {e}")
            return False

    def _download_reviews(self) -> bool:
        btns = self.c["web_automation"]["buttons"]["analysis"]
        # 클릭 시작
        if not self.matcher.find_and_click(btns["start"], confidence=btns["confidence"]):
            self.log("ERROR", "분석 시작 버튼 실패"); return False
        time.sleep(btns["wait_between"])
        if not self.matcher.find_and_click(btns["excel"], confidence=btns["confidence"]):
            self.log("ERROR", "엑셀 다운로드 버튼 실패"); return False
        # 완료 검증기
        return self._wait_download_completion(["xlsx","xls"])

    # ---- download verifier ----
    def _wait_download_completion(self, extensions: List[str]) -> bool:
        folder = Path(self.c["paths"]["download_folder"])
        start_snapshot = {f.name for f in folder.glob("*")}
        deadline = time.time() + self.c["web_automation"]["buttons"]["analysis"]["download_timeout"]
        temp_exts = [".crdownload", ".part", ".tmp"]
        while time.time() < deadline:
            # temp 파일이 더 이상 없고, 새로운 최종 파일이 등장했는지
            current = list(folder.glob("*"))
            names = {f.name for f in current}
            new_files = [f for f in current if f.name not in start_snapshot]
            # temp가 남아있으면 계속 대기
            if any(f.suffix.lower() in temp_exts for f in new_files):
                time.sleep(0.5); continue
            # 확정 파일 찾기
            finals = [f for f in new_files if f.suffix.lower().lstrip(".") in extensions]
            if finals:
                # 파일 열기 가능한지 확인
                try:
                    with open(finals[0], "rb") as _:
                        pass
                    self.log("SUCCESS", f"다운로드 완료: {finals[0].name}")
                    return True
                except Exception as e:
                    self.log("WARNING", f"파일 열기 대기: {e}")
            time.sleep(0.5)
        self.log("ERROR", "다운로드 타임아웃")
        return False
