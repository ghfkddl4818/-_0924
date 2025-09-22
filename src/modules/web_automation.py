
import time, os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import pyautogui

from .image_matcher import EnhancedImageMatcher
from .error_handler import ErrorHandler
from .data_processor import DataProcessor

class WebAutomation:
    def __init__(
        self,
        config: dict,
        log_callback: Callable,
        step_callback: Callable,
        done_callback: Callable,
        data_processor: Optional[DataProcessor] = None,
        payload_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.c = config
        self.log = log_callback
        self.set_step = step_callback
        self.on_item_done = done_callback
        self.matcher = EnhancedImageMatcher(config)
        self.err = ErrorHandler(config, log_callback)
        self.data_processor = data_processor
        self._payload_callback = payload_callback
        self._last_payload: Optional[Dict[str, Any]] = None
        self._startup_delay_done = False
        self._detail_stabilized = False

    def reset_counts(self, total: int):
        self.total = total
        self.processed = 0
        self._startup_delay_done = False
        self._detail_stabilized = False

    def process_single_product(self, idx: int, product_ctx: Optional[Dict[str, Any]] = None) -> bool:
        context = dict(product_ctx or {})
        context.setdefault("product_id", idx + 1)

        self.set_step("DETAIL", 0)
        if not self._click_detail(): return False
        self.set_step("CAPTURE", 20)
        if not self._fireshot_capture(): return False
        self.set_step("DOWNLOAD", 40)
        if not self._download_reviews(): return False

        self.set_step("ORGANIZE", 70)
        payload = self._post_download(idx, context)
        if payload is None: return False

        self.set_step("EMAIL", 90)
        self.set_step("DONE", 100)
        self.on_item_done()
        if self.c["web_automation"]["close_after_process"]:
            pyautogui.hotkey(*self.c["web_automation"]["buttons"]["navigation"]["close_tab"].split("+"))
            time.sleep(self.c["web_automation"]["tab_switch_delay"])
        else:
            pyautogui.hotkey(*self.c["web_automation"]["buttons"]["navigation"]["next_tab"].split("+"))
            time.sleep(self.c["web_automation"]["tab_switch_delay"])
        return True

    def _post_download(self, idx: int, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.data_processor:
            self.log("ERROR", "DataProcessor is not configured; skipping organization step.")
            return None
        try:
            payload = self.data_processor.process_product(idx, context)
            self._last_payload = payload
            self.log("INFO", f"Post-download processing finished (product_id={payload.get('product_id')})")
            if self._payload_callback:
                try:
                    self._payload_callback(payload)
                except Exception as exc:
                    self.log("ERROR", f"Post-processing callback failed: {exc}")
            return payload
        except Exception as exc:
            self.log("ERROR", f"Post-download processing failed: {exc}")
            return None


    # ---- steps ----
    def _click_detail(self) -> bool:
        buttons = self.c["web_automation"]["buttons"]["detail"]
        scrolling = self.c["web_automation"].get("scrolling", {})
        max_scrolls = int(scrolling.get("max_scrolls", 0))
        scroll_amount = abs(int(scrolling.get("amount", 0)))
        wait_between = float(scrolling.get("wait_between", 0.5))
        smooth_scroll = bool(scrolling.get("smooth_scroll", False))
        click_offset = tuple(buttons.get("click_offset", (0, 0)))
        button_timeout = float(buttons.get("timeout", 10.0))

        if not self._startup_delay_done:
            startup_delay = float(self.c["web_automation"].get("startup_delay", 5.0))
            if startup_delay > 0:
                self.log("INFO", f"자동화 시작 대기 중... {startup_delay:.1f}초")
                time.sleep(startup_delay)
            self._startup_delay_done = True

        def attempt_click(override_retry: int | None = None, timeout: float | None = None) -> bool:
            ok_primary = self.matcher.find_and_click(
                buttons["primary"],
                confidence=buttons["confidence"],
                retry=override_retry if override_retry is not None else buttons["retry"],
                region=buttons.get("search_region"),
                wait_after=buttons["wait_after"],
                timeout=timeout or button_timeout,
                click_offset=click_offset,
            )
            if ok_primary:
                return True
            if buttons.get("alternative"):
                self.log("WARNING", "메인 실패 → 대체 이미지 시도")
                return self.matcher.find_and_click(
                    buttons["alternative"],
                    confidence=buttons["confidence"] * 0.95,
                    retry=3,
                    region=buttons.get("search_region"),
                    wait_after=buttons["wait_after"],
                    timeout=timeout or button_timeout,
                    click_offset=click_offset,
                )
            return False

        if not self._detail_stabilized:
            initial_scrolls = int(scrolling.get("initial_scroll", 0))
            if initial_scrolls > 0 and scroll_amount > 0:
                for _ in range(initial_scrolls):
                    self._scroll_down(scroll_amount, smooth_scroll)
                    time.sleep(wait_between)
            settle_wait = float(buttons.get("initial_wait", wait_between))
            settle_attempts = max(1, int(buttons.get("initial_attempts", 2)))
            initial_timeout = float(buttons.get("initial_timeout", button_timeout))
            for attempt_idx in range(settle_attempts):
                if attempt_click(timeout=initial_timeout):
                    self._detail_stabilized = True
                    return True
                if attempt_idx < settle_attempts - 1:
                    time.sleep(settle_wait)
            self._detail_stabilized = True

        if attempt_click():
            return True

        for idx in range(max_scrolls):
            if scroll_amount <= 0:
                break
            self._scroll_down(scroll_amount, smooth_scroll)
            time.sleep(wait_between)
            if attempt_click():
                return True
        self.log("ERROR", "상세 버튼 클릭 실패")
        return False

    def _scroll_down(self, amount: int, smooth: bool) -> None:
        try:
            step = max(1, int(amount))
            if smooth and step > 100:
                increments = max(2, step // 100)
                chunk = max(1, step // increments)
                for _ in range(increments):
                    pyautogui.scroll(-chunk)
                    time.sleep(0.05)
            else:
                pyautogui.scroll(-step)
        except Exception as exc:  # pragma: no cover - defensive guard
            self.log("WARNING", f"스크롤 실행 실패: {exc}")

    def _fireshot_capture(self) -> bool:
        try:
            settings = self.c["web_automation"]["buttons"]["fireshot"]
            trig = settings["trigger_key"]
            pyautogui.hotkey(*trig.split("+"))
            time.sleep(settings.get("pre_wait", 1.0))
            ok = self.matcher.find_and_click(
                settings["save_button"],
                confidence=settings["confidence"],
                timeout=settings["timeout"],
            )
            if not ok:
                self.log("ERROR", "Fireshot 저장 버튼을 찾지 못함")
                return False
            completed = self._wait_fireshot_completion(settings)
            cleanup_ok = self._ensure_fireshot_tab_cleanup(settings)
            if not completed:
                self.log("WARNING", "Fireshot 캡처 완료 상태를 확인하지 못했습니다. 구성된 템플릿을 확인하세요.")
            if not cleanup_ok:
                self.log("ERROR", "Fireshot 저장 탭을 닫거나 상품 탭으로 복귀하지 못했습니다.")
                return False
            time.sleep(settings.get("wait_after", 0.0))
            return True
        except Exception as e:
            self.log("ERROR", f"Fireshot 실패: {e}")
            return False

    def _wait_fireshot_completion(self, settings: dict) -> bool:
        timeout = float(settings.get("post_wait_timeout", 15.0))
        interval = float(settings.get("post_wait_interval", 0.5))
        base_confidence = float(settings.get("post_wait_confidence", settings.get("confidence", 0.9) * 0.85))
        deadline = time.time() + timeout

        save_template = settings.get("save_button")
        progress_template = settings.get("progress_template")
        progress_region: Optional[List[int]] = settings.get("progress_region")
        progress_conf = float(settings.get("progress_confidence", base_confidence))
        completion_template = settings.get("completion_template")
        completion_region: Optional[List[int]] = settings.get("completion_region")
        completion_conf = float(settings.get("completion_confidence", base_confidence))
        treat_save_as_progress = bool(settings.get("treat_save_button_as_progress", True))

        while time.time() < deadline:
            in_progress = False
            if progress_template and self.matcher.exists(progress_template, progress_conf, region=progress_region):
                in_progress = True

            if not in_progress and treat_save_as_progress and save_template:
                in_progress = self.matcher.exists(save_template, base_confidence)

            if not in_progress:
                if completion_template:
                    if self.matcher.exists(completion_template, completion_conf, region=completion_region):
                        return True
                else:
                    return True

            time.sleep(interval)

        self.log("WARNING", "Fireshot 캡처 진행 상태를 확인하지 못했습니다. 다음 단계로 계속 진행합니다.")
        return False

    def _ensure_fireshot_tab_cleanup(self, settings: dict) -> bool:
        navigation = self.c["web_automation"]["buttons"].get("navigation", {})
        close_hotkey = navigation.get("close_tab")
        prev_hotkey = navigation.get("prev_tab")
        auto_close = bool(settings.get("auto_close_tab", True))
        wait_interval = float(settings.get("tab_poll_interval", 0.5))
        close_wait = float(settings.get("tab_close_wait", wait_interval))
        timeout = float(settings.get("tab_close_timeout", 10.0))

        save_tab_template = settings.get("save_tab_template")
        save_tab_region: Optional[List[int]] = settings.get("save_tab_region")
        save_tab_conf = float(settings.get("save_tab_confidence", settings.get("confidence", 0.9) * 0.9))
        product_template = settings.get("product_tab_template")
        product_region: Optional[List[int]] = settings.get("product_tab_region")
        product_conf = float(settings.get("product_tab_confidence", settings.get("confidence", 0.9)))

        if auto_close and close_hotkey:
            pyautogui.hotkey(*close_hotkey.split("+"))
            time.sleep(close_wait)

        if not save_tab_template and not product_template:
            return True

        deadline = time.time() + timeout
        last_prev_sent = 0.0

        while time.time() < deadline:
            save_tab_open = False
            if save_tab_template:
                save_tab_open = self.matcher.exists(save_tab_template, save_tab_conf, region=save_tab_region)
                if save_tab_open and auto_close and close_hotkey:
                    pyautogui.hotkey(*close_hotkey.split("+"))
                    time.sleep(close_wait)
                    continue

            if product_template and self.matcher.exists(product_template, product_conf, region=product_region):
                return True

            if not save_tab_open and not product_template:
                return True

            if not save_tab_open and product_template and prev_hotkey:
                now = time.time()
                if now - last_prev_sent >= close_wait:
                    pyautogui.hotkey(*prev_hotkey.split("+"))
                    last_prev_sent = now

            time.sleep(wait_interval)

        return False

    def _download_reviews(self) -> bool:
        btns = self.c["web_automation"]["buttons"]["analysis"]
        default_conf = float(btns.get("confidence", 0.85))
        default_retry = int(btns.get("default_retry", 5))
        default_timeout = float(btns.get("default_timeout", 30.0))
        default_wait = float(btns.get("wait_between", 0.5))

        def normalize_button(entry):
            if entry is None:
                return None
            if isinstance(entry, str):
                cfg = {"template": entry}
            else:
                cfg = dict(entry)
                cfg["template"] = cfg.get("template") or cfg.get("path") or cfg.get("image")
            template = cfg.get("template")
            if not template:
                return None
            cfg["confidence"] = float(cfg.get("confidence", default_conf))
            cfg["retry"] = int(cfg.get("retry", default_retry))
            cfg["timeout"] = float(cfg.get("timeout", default_timeout))
            cfg["wait_after"] = float(cfg.get("wait_after", default_wait))
            offset = cfg.get("click_offset", (0, 0))
            if isinstance(offset, (list, tuple)) and len(offset) >= 2:
                cfg["click_offset"] = (int(offset[0]), int(offset[1]))
            else:
                cfg["click_offset"] = (0, 0)
            return cfg

        sort_cfg = btns.get("sort_popup")
        if sort_cfg:
            trigger = sort_cfg.get("trigger_hotkey")
            if trigger:
                keys = [k.strip() for k in trigger.split("+") if k.strip()]
                if keys:
                    pyautogui.hotkey(*keys)
            wait_after_trigger = float(sort_cfg.get("wait_after_trigger", default_wait))
            if wait_after_trigger > 0:
                time.sleep(wait_after_trigger)
            detector = sort_cfg.get("detector")
            if detector:
                detector_conf = float(sort_cfg.get("confidence", default_conf))
                detector_timeout = float(sort_cfg.get("timeout", default_timeout))
                detector_region = sort_cfg.get("region")
                if not self.matcher.wait_until_visible(detector, detector_conf, timeout=detector_timeout, region=detector_region):
                    self.log("ERROR", "Sort popup did not appear in time")
                    return False

        steps = [
            ("review button", "review_button"),
            ("analysis start", "analysis_start"),
            ("excel download", "excel_download"),
            ("crawling tool", "crawling_tool"),
        ]

        button_cache = {}
        for label, key in steps:
            cfg = normalize_button(btns.get(key))
            if not cfg:
                self.log("ERROR", f"Missing configuration for {label}: {key}")
                return False
            if not self.matcher.find_and_click(
                cfg["template"],
                confidence=cfg["confidence"],
                retry=cfg["retry"],
                timeout=cfg["timeout"],
                wait_after=cfg["wait_after"],
                region=cfg.get("region"),
                click_offset=cfg.get("click_offset"),
            ):
                self.log("ERROR", f"Failed to click {label}")
                return False
            button_cache[key] = cfg
            if key == "analysis_start":
                excel_cfg = normalize_button(btns.get("excel_download"))
                if excel_cfg:
                    self.matcher.wait_until_visible(
                        excel_cfg["template"],
                        excel_cfg["confidence"],
                        timeout=excel_cfg["timeout"],
                        region=excel_cfg.get("region"),
                    )

        review_cfg = button_cache.get("review_button")
        disappear_cfg = btns.get("review_disappear_check", {})
        vanish_template = disappear_cfg.get("template") or (review_cfg["template"] if review_cfg else None)
        vanish_conf = float(disappear_cfg.get("confidence", review_cfg["confidence"] if review_cfg else default_conf))
        vanish_timeout = float(disappear_cfg.get("timeout", default_timeout))
        vanish_interval = float(disappear_cfg.get("poll_interval", 0.5))
        vanish_region = disappear_cfg.get("region") or (review_cfg.get("region") if review_cfg else None)
        if vanish_template and review_cfg:
            if not self.matcher.wait_until_missing(
                vanish_template,
                vanish_conf,
                timeout=vanish_timeout,
                interval=vanish_interval,
                region=vanish_region,
            ):
                self.log("ERROR", "Review button did not disappear after clicking crawling tool")
                return False

        return self._wait_download_completion(["xlsx", "xls"])

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
