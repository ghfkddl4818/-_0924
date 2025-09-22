
import cv2, numpy as np, time
import pyautogui
from pathlib import Path
from typing import Optional, List, Tuple

MATCH_METHODS = {
    "cv2.TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
    "cv2.TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
    "cv2.TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
}

class EnhancedImageMatcher:
    def __init__(self, config: dict):
        self.config = config
        self.template_cache = {}
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    def find_and_click(self, template_path: str, confidence: float, retry: int = 3,
                       region: Optional[List[int]] = None, wait_after: float = 0.5,
                       timeout: float = 10.0, click_offset: Tuple[int,int]=(0,0)) -> bool:
        tmpl = self._load_template(template_path)
        if tmpl is None:
            return False
        start = time.time()
        attempt = 0
        while attempt < retry and (time.time()-start) < timeout:
            pos = self._find_image(tmpl, confidence, region)
            if pos:
                x = pos[0] + click_offset[0]
                y = pos[1] + click_offset[1]
                pyautogui.click(x, y)
                time.sleep(wait_after)
                return True
            time.sleep(0.3)
            attempt += 1
        return False

    def _find_image(self, template, confidence: float, region: Optional[List[int]]):
        # screenshot
        if region:
            shot = pyautogui.screenshot(region=tuple(region))
        else:
            shot = pyautogui.screenshot()
        screen = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)

        # grayscale option
        grayscale = self.config["web_automation"]["image_matching"]["grayscale"]
        if grayscale:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            if len(template.shape) == 3:
                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # multi-scale
        best = None; best_val = -1
        for scale in self.config["web_automation"]["image_matching"]["multi_scale"]:
            tmpl = cv2.resize(template, (int(template.shape[1]*scale), int(template.shape[0]*scale)))
            method = MATCH_METHODS.get(self.config["web_automation"]["image_matching"]["match_method"], cv2.TM_CCOEFF_NORMED)
            res = cv2.matchTemplate(screen, tmpl, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            score = 1-max_val if method==cv2.TM_SQDIFF_NORMED else max_val
            if score > best_val:
                best_val = score
                best = (min_loc if method==cv2.TM_SQDIFF_NORMED else max_loc, tmpl.shape[1], tmpl.shape[0])
        # check threshold
        thr = confidence if MATCH_METHODS.get(self.config["web_automation"]["image_matching"]["match_method"]) != cv2.TM_SQDIFF_NORMED else (1-confidence)
        ok = (best_val >= thr)
        if not ok:
            return None
        loc, w, h = best
        cx, cy = loc[0] + w//2, loc[1] + h//2
        if region:
            cx += region[0]; cy += region[1]
        return (cx, cy)

    def _load_template(self, path: str):
        p = Path(path)
        if not p.exists():
            return None
        if path in self.template_cache:
            return self.template_cache[path]
        img = cv2.imread(str(p))
        if self.config["web_automation"]["image_matching"].get("cache_templates", True):
            self.template_cache[path] = img
        return img
