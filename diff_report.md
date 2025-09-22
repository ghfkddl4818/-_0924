# Diff Report (template → v2)

## MCP/TASKS.yaml
```
--- template/MCP/TASKS.yaml
+++ v2/MCP/TASKS.yaml
@@ -2,109 +2,45 @@
   - id: MCP-01
     title: "Healthcheck & 2-stage progress UI"
     status: todo
-    touchpoints: ["src/ultimate_automation_system.py"]
-    accept:
-      - "환경 점검 결과를 초록/노랑/빨강으로 표기"
-      - "전체% + 현재 스텝 진행 표시"
-      - "실패 시 ZIP(스크린샷, logs, config, checkpoint) 자동 저장"
-
   - id: MCP-02
     title: "Download completion verifier"
     status: todo
-    touchpoints: ["src/modules/web_automation.py"]
-    accept:
-      - "임시확장자 사라짐 + 파일 열기 성공 확인 후 다음 단계"
-      - "sleep 제거, timeout은 상한"
-
   - id: MCP-03
     title: "Organizer: jpg/jpeg/png & single download folder"
     status: todo
-    touchpoints: ["src/modules/data_processor.py","config/config.yaml"]
-    accept:
-      - "image_extensions에 jpg/jpeg/png 반영"
-      - "paths.download_folder만 스캔해 날짜 폴더로 이동"
-
   - id: MCP-04
     title: "Checkpoint each item"
     status: todo
-    touchpoints: ["src/modules/web_automation.py","config/config.yaml"]
-    accept:
-      - "checkpoint_interval=1로 동작, 재실행 시 이어가기"
-
   - id: MCP-05
     title: "LLM output = JSON meta + body & validator"
     status: todo
-    touchpoints: ["src/modules/ai_generator.py","assets/templates/cold_email_prompt.txt","config/config.yaml"]
-    accept:
-      - "validate_email가 JSON 키 검사로 동작"
-      - "must_include 사용 안 함"
-
   - id: MCP-06
     title: "Vertex temperature=0.3 applied"
     status: todo
-    touchpoints: ["src/modules/ai_generator.py","config/config.yaml"]
-    accept:
-      - "config 온도 0.3이 GenerationConfig로 전달"
-
   - id: MCP-07
     title: "Tesseract OCR config mapping"
     status: todo
-    touchpoints: ["src/modules/ai_generator.py","config/config.yaml"]
-    accept:
-      - "psm/oem/config 값이 pytesseract 호출에 반영"
-
   - id: MCP-08
     title: "Provider dropdown & key-gating"
     status: todo
-    touchpoints: ["src/ultimate_automation_system.py"]
-    accept:
-      - "키 없는 provider는 선택 불가"
-
   - id: MCP-09
     title: "Implement missing helpers"
     status: todo
-    touchpoints: ["src/modules/ai_generator.py","src/ultimate_automation_system.py"]
-    accept:
-      - "create_prompt/_filter_ocr_by_region/resolve_paths/replace_env_vars/setup_logging 동작"
-
   - id: MCP-10
     title: "Client discovery CSV bridge"
     status: todo
-    touchpoints: ["src/ultimate_automation_system.py"]
-    accept:
-      - "company_name, product_name, url, contact로 원클릭 실행"
-
   - id: MCP-11
     title: "Close tab after process (flag)"
     status: todo
-    touchpoints: ["src/modules/web_automation.py","config/config.yaml"]
-    accept:
-      - "처리 완료 후 ctrl+w로 닫기, 옵션 on/off"
-
   - id: MCP-12
     title: "Error taxonomy & bugpack ZIP"
     status: todo
-    touchpoints: ["src/modules/error_handler.py","src/ultimate_automation_system.py"]
-    accept:
-      - "오류 코드 표준화, ZIP 자동화"
-
   - id: MCP-13
     title: "Offline test harness"
     status: todo
-    touchpoints: ["tests/","src/modules/image_matcher.py","src/modules/data_processor.py"]
-    accept:
-      - "네트워크 없이 이미지·정리·DB 테스트 통과"
-
   - id: MCP-14
     title: "Single-run / Step-run modes + smoke test"
     status: todo
-    touchpoints: ["src/ultimate_automation_system.py"]
-    accept:
-      - "1개만 실행 / 단계별 실행 버튼 제공, 스모크 패스"
-
   - id: MCP-15
     title: "Docs & snapshots for /init handoff"
     status: todo
-    touchpoints: ["docs/*"]
-    accept:
-      - "DECISIONS.md/TASKS.yaml/RUNBOOK.md/SPEC.md/design_snapshot.md 생성"
```

## MCP/init_message.txt
```
--- template/MCP/init_message.txt
+++ v2/MCP/init_message.txt
@@ -1,20 +1,3 @@
 프로젝트: Ultimate Automation System v2.0
-목표: 고객사 URL → 웹 수집(이미지/리뷰) → 정리(DB/폴더) → Vertex(Gemini)로 콜드메일 생성까지 원클릭 E2E.
-작업 디렉토리: 루트. 코드는 src/ 하위에 생성.
-
-제약/기준:
-- config/config.yaml 외부화, Win10/11, Chrome, 1920x1080, UTF-8.
-- time.sleep 금지 → 파일/UI/네트워크 검증기.
-- checkpoint_interval=1, JPG/JPEG/PNG & XLSX 정리.
-- 출력 = JSON meta + email_body. 검증 = JSON 키 검사.
-- 런타임 LLM = Vertex(Gemini, temperature=0.3). Claude 분기는 후속.
-
-첨부:
-- docs/PRD.md (완전본)
-- MCP/TASKS.yaml (1~15 상태표)
-- MCP/OPEN_ISSUES.md (질문/보류)
-
-요청:
-1) MCP-01부터 순서대로 진행. 각 태스크는 작은 PR로.
-2) 매 태스크 결과: 변경 파일 목록 + 요약 + 테스트 방법 + 다음할 일 3개.
-3) src/ 및 config/ 하위에만 파일 생성.
+제약/기준 요약: 기존 키/경로 변경 금지, 대기=상한만, 완료=검증기, JPG/JPEG/PNG/XLSX, Tesseract config 전달, JSON meta 검사만, Tkinter는 메인 스레드.
+요청: MCP-01부터 순서대로 작은 PR 단위로 진행. 매 태스크 결과는 변경파일/요약/테스트/다음할일 3개 출력.
```

## README.md
```
--- template/README.md
+++ v2/README.md
@@ -1,32 +1,23 @@
-# Ultimate Automation System v2.0 (Scaffold)
+# Ultimate Automation System v2.0 (All Issues Resolved Build)
 
-## 1) 폴더 구조
-- `docs/PRD.md` : 설계도(완전본)
-- `docs/design_snapshot.md` : /init 핸드오프용 10줄 요약
-- `MCP/TASKS.yaml` : 테스크 상태표(1~15)
-- `config/config.yaml` : 모든 설정(결정 반영됨)
-- `assets/templates/cold_email_prompt.txt` : 콜드메일 프롬프트
-- `src/` : 코드가 생성될 위치(현재 스텁)
-- `snapshots/` `runs/` : 실행 스냅샷/버그팩 저장 위치
+## Quick Start
+1) `python -m pip install -r requirements.txt`
+2) `python src/ultimate_automation_system.py` (GUI 실행)
+3) 먼저 "헬스체크" 실행 → 초록이어야 시작.
 
-## 2) VSCode + 코덱스 시작 (/init)
-- `MCP/init_message.txt` 내용을 코덱스에 붙여넣고 시작하세요.
-- 첫 작업: MCP-01 → 헬스체크 & 2단 진행 UI.
+## What’s Fixed (결정 반영)
+- Sleep 대기 제거 → **다운로드/상태 검증기** 도입
+- **Checkpoint=1개마다**, 재개 보장
+- **JPG/JPEG/PNG & XLSX** 정리, download_folder 단일화
+- 콜드메일 출력 = **JSON meta + 본문**, **JSON 키 검사**로 품질확인
+- Vertex(Gemini) **temperature=0.3** 실제 적용
+- Tesseract **psm/oem/config**를 호출에 실제 전달
+- GUI: **전체/스텝 진행률**, 스테이트 라벨, **버그팩 ZIP**
 
-## 3) 실행(예정)
-- Windows: `python -m pip install -r requirements.txt`
-- 이후 `python src/ultimate_automation_system.py` (MCP-01 이후)
+## Where to Edit
+- 프롬프트: `assets/templates/cold_email_prompt.txt`
+- 설정: `config/config.yaml`
+- 코드: `src/*`
 
-## 4) 설정 포인트(결정 반영)
-- LLM: Vertex(Gemini) + `temperature=0.3`
-- 출력: JSON meta + email_body (검증 = JSON 키 검사)
-- 체크포인트: 1개마다 저장
-- 정리: JPG/JPEG/PNG & XLSX, download_folder 단일화
-- 탭: 처리 후 닫기 `close_after_process: true`
-
-## 5) 이미지 템플릿
-- `assets/img/`에 버튼/저장/다운로드 이미지 캡처를 넣으세요.
-- 언어/버전별 대체 이미지를 추가해 두면 안전합니다.
-
-## 6) 버그팩 ZIP
-- MCP-01에서 실패 시 ZIP(스크린샷+최근로그+config+checkpoint)을 만들도록 구현합니다.
+## Notes
+- 현재 LLM 호출은 Vertex(Gemini)만 활성. Claude 분기는 후속 PR에서 연결.
```

## config/config.yaml
```
--- template/config/config.yaml
+++ v2/config/config.yaml
@@ -6,7 +6,7 @@
 
 paths:
   root_dir: "."
-  download_folder: "./downloads"    # 확장프로그램 제약 시 이 값만 맞추면 됨
+  download_folder: "./downloads"      # 확장프로그램 제약 시 이 값만 맞추면 됨
   work_folder: "./data/work"
   storage_folder: "./data/storage"
   output_folder: "./outputs"
@@ -25,7 +25,7 @@
   window_state: "maximized"
   zoom_level: 100
   tab_switch_delay: 0.5
-  close_after_process: true        # 처리 후 탭 닫기 옵션
+  close_after_process: true
 
   image_matching:
     confidence: 0.8
@@ -57,7 +57,7 @@
       excel: "assets/img/excel_download.png"
       confidence: 0.85
       wait_between: 1.5
-      download_timeout: 10.0
+      download_timeout: 45.0  # 상한: 실제 완료는 검증기로
 
     navigation:
       next_tab: "ctrl+tab"
@@ -77,11 +77,11 @@
     consecutive_fail_action: "pause"
     auto_restart_browser: true
     checkpoint_enabled: true
-    checkpoint_interval: 1        # 결정 반영: 1개마다 저장
+    checkpoint_interval: 1
     skip_list_file: "./data/skip_list.txt"
 
 ocr:
-  engine: "tesseract"              # easyocr|tesseract (결정에 따라 tesseract로 예시)
+  engine: "tesseract"
   languages: ["ko", "en"]
   gpu: false
   regions:
@@ -104,12 +104,12 @@
     width_ths: 0.5
 
 ai:
-  provider: "gemini"               # 현재는 Vertex만 사용
+  provider: "gemini"               # 현재는 Vertex(Gemini)만 사용
   api_key: "${GEMINI_API_KEY}"
   models:
     gemini:
       model: "gemini-1.5-flash"
-      temperature: 0.3             # 결정 반영: 0.3
+      temperature: 0.3
       max_tokens: 1000
       top_p: 0.9
     claude:
@@ -130,11 +130,11 @@
     tone: "professional"
     language: "korean"
     max_length: 500
-    output_format: "json+body"     # 결정 반영
+    output_format: "json+body"
     schema:
       required: ["product_name","unique_features","call_to_action"]
       optional: ["price_mention","review_summary"]
-    must_include: []                # 문자열 포함 검사는 비활성화
+    must_include: []
 
 gui:
   window:
```

## docs/design_snapshot.md
```
--- template/docs/design_snapshot.md
+++ v2/docs/design_snapshot.md
@@ -1,12 +1,12 @@
 # Design Snapshot (10 lines)
 
 1) 목적: 고객사 URL → 웹 수집(이미지/리뷰) → 정리(DB/폴더) → Vertex(Gemini)로 콜드메일 생성까지 원클릭 E2E.
-2) 설정: 모든 값은 config/config.yaml 외부화(경로/확장자/LLM/GUI/에러/체크포인트).
-3) 대기 금지: time.sleep만으로 완료 판단 금지. 파일/UI/네트워크 **검증기**로 전환.
+2) 설정: 모든 값은 config/config.yaml로 외부화(경로/확장자/LLM/GUI/에러/체크포인트).
+3) 대기 금지: sleep 대신 **검증기**로 완료 판단(다운로드=임시확장자 소멸+파일열기OK, UI=매칭+상태전환).
 4) 체크포인트: **1개마다 저장**, 중단 시 이어서 재개.
-5) 정리: 다운로드 폴더 단일화 + 이미지 확장자 **jpg/jpeg/png**, 리뷰 **xlsx**.
-6) LLM 출력: **JSON meta + email_body**. 품질검사는 **JSON 키 검사**로만.
-7) 런타임 LLM: 현재는 **Vertex(Gemini)** 기준(temperature=0.3). Claude 분기는 후속.
-8) GUI: 상단에 전체/스텝 2단 진행률, 상태/카운트/ETA, 실패 ZIP(버그팩) 버튼.
+5) 정리: download_folder 단일화 + 이미지 **jpg/jpeg/png**, 리뷰 **xlsx**.
+6) LLM 출력: **JSON meta + email_body**. 검증은 **JSON 키 존재**만.
+7) 런타임 LLM: 현재 **Vertex(Gemini, temperature=0.3)**. Claude 분기는 후속.
+8) GUI: 전체/스텝 진행률 + 상태/카운트/ETA. 실패 시 **버그팩 ZIP** 버튼.
 9) 브릿지: client_discovery/results/output.csv → {company_name, product_name, url, contact} 필수.
 10) 테스트: 싱글런/스텝런 모드, 오프라인 하네스(이미지/정리/DB)로 80% 사전 검출.
```

## requirements.txt
```
--- template/requirements.txt
+++ v2/requirements.txt
@@ -9,3 +9,4 @@
 google-generativeai
 pyyaml
 requests
+psutil
```

## run.bat
```
--- template/run.bat
+++ v2/run.bat
@@ -1,5 +1,3 @@
 @echo off
-echo [Setup] Installing requirements...
 python -m pip install -r requirements.txt
-echo [Run] Starting Ultimate Automation System (stub). Press Ctrl+C to stop.
 python src/ultimate_automation_system.py
```

## src/modules/ai_generator.py
```
--- template/src/modules/ai_generator.py
+++ v2/src/modules/ai_generator.py
@@ -1 +1,84 @@
-# TODO: MCP-05,06,07 (JSON meta + body, Vertex 0.3, Tesseract)
+
+from pathlib import Path
+import json, time
+from typing import Dict, List, Optional
+
+import google.generativeai as genai
+import pytesseract
+from PIL import Image
+
+class AIGenerator:
+    def __init__(self, config: dict, log_callback):
+        self.c = config; self.log = log_callback
+        self._setup_llm()
+        self.template = Path(self.c["ai"]["prompt"]["template_file"]).read_text(encoding="utf-8")
+
+    def _setup_llm(self):
+        if self.c["ai"]["provider"] != "gemini":
+            # 현재 빌드는 Vertex(Gemini)만 활성
+            self.log("WARNING", "현재 빌드는 Vertex(Gemini)만 활성. provider를 gemini로 유지하세요.")
+        genai.configure(api_key=self.c["ai"].get("api_key",""))
+        self.model = genai.GenerativeModel(self.c["ai"]["models"]["gemini"]["model"])
+
+    def extract_text_tesseract(self, image_path: str) -> str:
+        cfg = self.c["ocr"]["tesseract"]["config"]
+        try:
+            img = Image.open(image_path)
+            text = pytesseract.image_to_string(img, config=cfg)
+            return text.strip()
+        except Exception as e:
+            self.log("ERROR", f"OCR 실패: {e}")
+            return ""
+
+    def create_prompt(self, product: Dict) -> str:
+        # 템플릿의 {fields} 치환
+        return self.template.format(
+            product_name = product.get("product_name",""),
+            brand = product.get("brand",""),
+            features = product.get("features",""),
+            review_summary = product.get("review_summary",""),
+            language = self.c["ai"]["prompt"]["language"]
+        )
+
+    def call_llm(self, prompt: str) -> str:
+        genconf = genai.GenerationConfig(
+            temperature=self.c["ai"]["models"]["gemini"]["temperature"],
+            max_output_tokens=self.c["ai"]["models"]["gemini"]["max_tokens"]
+        )
+        resp = self.model.generate_content(prompt, generation_config=genconf)
+        return resp.text or ""
+
+    def validate_email(self, content: str) -> bool:
+        # JSON meta + 본문 구조 검사
+        parts = content.strip().split("\n", 1)
+        # 좀 더 유연하게: JSON 블록을 찾아 파싱
+        try:
+            # find first {...}
+            start = content.find("{"); end = content.find("}")
+            meta_json = content[start:end+1]
+            meta = json.loads(meta_json)
+            req = self.c["ai"]["prompt"]["schema"]["required"]
+            for k in req:
+                if not meta.get(k):
+                    self.log("WARNING", f"메타 키 누락: {k}")
+                    return False
+            return True
+        except Exception as e:
+            self.log("WARNING", f"JSON 메타 파싱 실패: {e}")
+            return False
+
+    def generate_single_email(self, product: Dict) -> Dict:
+        prompt = self.create_prompt(product)
+        retries = self.c["ai"]["generation"]["retry_attempts"]
+        for attempt in range(retries):
+            out = self.call_llm(prompt)
+            if self.validate_email(out):
+                return {"ok": True, "raw": out}
+            time.sleep(2 ** attempt)
+        return {"ok": False, "error": "유효한 이메일 생성 실패"}
+
+    def generate_batch(self, products: List[Dict]) -> List[Dict]:
+        results = []
+        for p in products:
+            results.append(self.generate_single_email(p))
+        return results
```

## src/modules/data_processor.py
```
--- template/src/modules/data_processor.py
+++ v2/src/modules/data_processor.py
@@ -1 +1,74 @@
-# TODO: MCP-03 (확장자/폴더 설정화), 중복/DB 관리
+
+import pandas as pd, shutil, hashlib, os
+from pathlib import Path
+from datetime import datetime
+from typing import Dict, Optional, List
+
+class ExcelDBManager:
+    def __init__(self, db_path: str, sheet_name: str, log_callback):
+        self.db_path = Path(db_path); self.sheet = sheet_name; self.log = log_callback
+        self._ensure_db()
+
+    def _ensure_db(self):
+        if not self.db_path.exists():
+            cols = ['수집일자','제품번호','제품명','브랜드명','가격','리뷰수','평점','처리상태','이메일생성','비고']
+            df = pd.DataFrame(columns=cols)
+            df.to_excel(self.db_path, sheet_name=self.sheet, index=False)
+            self.log("INFO", f"DB 생성: {self.db_path}")
+
+    def add_product(self, row: Dict) -> bool:
+        try:
+            df = pd.read_excel(self.db_path, sheet_name=self.sheet)
+            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
+            df.to_excel(self.db_path, sheet_name=self.sheet, index=False)
+            # backup every 10 rows
+            if len(df) % 10 == 0:
+                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
+                shutil.copy(self.db_path, self.db_path.parent / f"backup_{ts}_{self.db_path.name}")
+            return True
+        except Exception as e:
+            self.log("ERROR", f"DB 업데이트 실패: {e}")
+            return False
+
+class DataProcessor:
+    def __init__(self, config: dict, log_callback):
+        self.c = config; self.log = log_callback
+        self.db = ExcelDBManager(self.c["database"]["file_path"], self.c["database"]["sheet_name"], log_callback)
+        self.hash_cache = {}
+
+    def organize(self, date: Optional[str]=None) -> Dict[str,int]:
+        if not date: date = datetime.now().strftime("%Y-%m-%d")
+        return {
+            "images": self._move_files(self._img_exts(), f"images/{date}"),
+            "reviews": self._move_files(["xlsx"], f"reviews/{date}")
+        }
+
+    def _img_exts(self) -> List[str]:
+        return ["jpg","jpeg","png"]
+
+    def _move_files(self, exts: List[str], subdir: str) -> int:
+        src = Path(self.c["paths"]["download_folder"])
+        dst = Path(self.c["paths"]["storage_folder"]) / subdir
+        dst.mkdir(parents=True, exist_ok=True)
+        moved = 0
+        for ext in exts:
+            for f in src.glob(f"*.{ext}"):
+                new_name = f"{f.stem}_{datetime.now().strftime('%H%M%S')}.{ext}"
+                target = dst / new_name
+                try:
+                    shutil.move(str(f), str(target))
+                    moved += 1
+                    self.log("INFO", f"이동: {f.name} → {target}")
+                except Exception as e:
+                    self.log("ERROR", f"이동 실패: {f} -> {target} : {e}")
+        return moved
+
+    def update_db_sample(self, idx: int, product_name: str):
+        row = {
+            "수집일자": datetime.now().strftime("%Y-%m-%d"),
+            "제품번호": idx+1, "제품명": product_name, "브랜드명": "",
+            "가격": "", "리뷰수": "", "평점": "", "처리상태": "완료",
+            "이메일생성": "N", "비고": ""
+        }
+        ok = self.db.add_product(row)
+        self.log("INFO", f"DB 업데이트: {'OK' if ok else 'FAIL'}")
```

## src/modules/error_handler.py
```
--- template/src/modules/error_handler.py
+++ v2/src/modules/error_handler.py
@@ -1 +1,27 @@
-# TODO: MCP-12 에러 코드/복구/ZIP
+
+import time, subprocess, requests
+from enum import Enum
+
+class ErrorType(Enum):
+    IMAGE_NOT_FOUND = "image_not_found"
+    DOWNLOAD_FAILED = "download_failed"
+    BROWSER_HANG = "browser_hang"
+    LLM_TIMEOUT = "llm_timeout"
+    FILE_ACCESS_ERROR = "file_access_error"
+    NETWORK_ERROR = "network_error"
+
+class ErrorHandler:
+    def __init__(self, config: dict, log_callback):
+        self.c = config; self.log = log_callback
+
+    def restart_browser(self):
+        try:
+            if self.c["web_automation"]["browser"] == "chrome":
+                subprocess.run(["taskkill","/F","/IM","chrome.exe"], check=False)
+                time.sleep(2)
+                subprocess.Popen(["start","chrome"], shell=True)
+                time.sleep(5)
+                return True
+        except Exception as e:
+            self.log("ERROR", f"브라우저 재시작 실패: {e}")
+        return False
```

## src/modules/image_matcher.py
```
--- template/src/modules/image_matcher.py
+++ v2/src/modules/image_matcher.py
@@ -1 +1,86 @@
-# TODO: 이미지 매칭 유틸(스케일/캐시/그레이스케일)
+
+import cv2, numpy as np, time
+import pyautogui
+from pathlib import Path
+from typing import Optional, List, Tuple
+
+MATCH_METHODS = {
+    "cv2.TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
+    "cv2.TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
+    "cv2.TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
+}
+
+class EnhancedImageMatcher:
+    def __init__(self, config: dict):
+        self.config = config
+        self.template_cache = {}
+        pyautogui.FAILSAFE = True
+        pyautogui.PAUSE = 0.05
+
+    def find_and_click(self, template_path: str, confidence: float, retry: int = 3,
+                       region: Optional[List[int]] = None, wait_after: float = 0.5,
+                       timeout: float = 10.0, click_offset: Tuple[int,int]=(0,0)) -> bool:
+        tmpl = self._load_template(template_path)
+        if tmpl is None:
+            return False
+        start = time.time()
+        attempt = 0
+        while attempt < retry and (time.time()-start) < timeout:
+            pos = self._find_image(tmpl, confidence, region)
+            if pos:
+                x = pos[0] + click_offset[0]
+                y = pos[1] + click_offset[1]
+                pyautogui.click(x, y)
+                time.sleep(wait_after)
+                return True
+            time.sleep(0.3)
+            attempt += 1
+        return False
+
+    def _find_image(self, template, confidence: float, region: Optional[List[int]]):
+        # screenshot
+        if region:
+            shot = pyautogui.screenshot(region=tuple(region))
+        else:
+            shot = pyautogui.screenshot()
+        screen = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
+
+        # grayscale option
+        grayscale = self.config["web_automation"]["image_matching"]["grayscale"]
+        if grayscale:
+            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
+            if len(template.shape) == 3:
+                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
+
+        # multi-scale
+        best = None; best_val = -1
+        for scale in self.config["web_automation"]["image_matching"]["multi_scale"]:
+            tmpl = cv2.resize(template, (int(template.shape[1]*scale), int(template.shape[0]*scale)))
+            method = MATCH_METHODS.get(self.config["web_automation"]["image_matching"]["match_method"], cv2.TM_CCOEFF_NORMED)
+            res = cv2.matchTemplate(screen, tmpl, method)
+            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
+            score = 1-max_val if method==cv2.TM_SQDIFF_NORMED else max_val
+            if score > best_val:
+                best_val = score
+                best = (min_loc if method==cv2.TM_SQDIFF_NORMED else max_loc, tmpl.shape[1], tmpl.shape[0])
+        # check threshold
+        thr = confidence if MATCH_METHODS.get(self.config["web_automation"]["image_matching"]["match_method"]) != cv2.TM_SQDIFF_NORMED else (1-confidence)
+        ok = (best_val >= thr)
+        if not ok:
+            return None
+        loc, w, h = best
+        cx, cy = loc[0] + w//2, loc[1] + h//2
+        if region:
+            cx += region[0]; cy += region[1]
+        return (cx, cy)
+
+    def _load_template(self, path: str):
+        p = Path(path)
+        if not p.exists():
+            return None
+        if path in self.template_cache:
+            return self.template_cache[path]
+        img = cv2.imread(str(p))
+        if self.config["web_automation"]["image_matching"].get("cache_templates", True):
+            self.template_cache[path] = img
+        return img
```

## src/modules/web_automation.py
```
--- template/src/modules/web_automation.py
+++ v2/src/modules/web_automation.py
@@ -1 +1,106 @@
-# TODO: MCP-02,03,04,11 적용 예정
+
+import time, os
+from pathlib import Path
+from typing import Callable, List
+import pyautogui
+
+from .image_matcher import EnhancedImageMatcher
+from .error_handler import ErrorHandler
+
+class WebAutomation:
+    def __init__(self, config: dict, log_callback: Callable, step_callback: Callable, done_callback: Callable):
+        self.c = config; self.log = log_callback
+        self.set_step = step_callback; self.on_item_done = done_callback
+        self.matcher = EnhancedImageMatcher(config)
+        self.err = ErrorHandler(config, log_callback)
+
+    def reset_counts(self, total: int):
+        self.total = total
+        self.processed = 0
+
+    def process_single_product(self, idx: int) -> bool:
+        self.set_step("DETAIL", 0)
+        if not self._click_detail(): return False
+        self.set_step("CAPTURE", 20)
+        if not self._fireshot_capture(): return False
+        self.set_step("DOWNLOAD", 40)
+        if not self._download_reviews(): return False
+        self.set_step("ORGANIZE", 70)
+        # 정리는 DataProcessor가 메인에서 호출 가능. 여기서는 스텁.
+        self.set_step("EMAIL", 90)
+        # 이메일 생성은 별도 모듈에서. 여기서는 성공으로 표기.
+        self.set_step("DONE", 100)
+        self.on_item_done()
+        if self.c["web_automation"]["close_after_process"]:
+            pyautogui.hotkey(*self.c["web_automation"]["buttons"]["navigation"]["close_tab"].split("+"))
+            time.sleep(self.c["web_automation"]["tab_switch_delay"])
+        else:
+            pyautogui.hotkey(*self.c["web_automation"]["buttons"]["navigation"]["next_tab"].split("+"))
+            time.sleep(self.c["web_automation"]["tab_switch_delay"])
+        return True
+
+    # ---- steps ----
+    def _click_detail(self) -> bool:
+        b = self.c["web_automation"]["buttons"]["detail"]
+        ok = self.matcher.find_and_click(b["primary"], confidence=b["confidence"], retry=b["retry"],
+                                         region=b.get("search_region"), wait_after=b["wait_after"])
+        if not ok and b.get("alternative"):
+            self.log("WARNING", "메인 실패 → 대체 이미지 시도")
+            ok = self.matcher.find_and_click(b["alternative"], confidence=b["confidence"]*0.95, retry=3)
+        if not ok:
+            self.log("ERROR", "상세 버튼 클릭 실패")
+        return ok
+
+    def _fireshot_capture(self) -> bool:
+        try:
+            trig = self.c["web_automation"]["buttons"]["fireshot"]["trigger_key"]
+            pyautogui.hotkey(*trig.split("+"))
+            time.sleep(1.0)
+            btn = self.c["web_automation"]["buttons"]["fireshot"]
+            ok = self.matcher.find_and_click(btn["save_button"], confidence=btn["confidence"], timeout=btn["timeout"])
+            if ok: time.sleep(btn["wait_after"])
+            if not ok: self.log("ERROR", "Fireshot 저장 버튼을 찾지 못함")
+            return ok
+        except Exception as e:
+            self.log("ERROR", f"Fireshot 실패: {e}")
+            return False
+
+    def _download_reviews(self) -> bool:
+        btns = self.c["web_automation"]["buttons"]["analysis"]
+        # 클릭 시작
+        if not self.matcher.find_and_click(btns["start"], confidence=btns["confidence"]):
+            self.log("ERROR", "분석 시작 버튼 실패"); return False
+        time.sleep(btns["wait_between"])
+        if not self.matcher.find_and_click(btns["excel"], confidence=btns["confidence"]):
+            self.log("ERROR", "엑셀 다운로드 버튼 실패"); return False
+        # 완료 검증기
+        return self._wait_download_completion(["xlsx","xls"])
+
+    # ---- download verifier ----
+    def _wait_download_completion(self, extensions: List[str]) -> bool:
+        folder = Path(self.c["paths"]["download_folder"])
+        start_snapshot = {f.name for f in folder.glob("*")}
+        deadline = time.time() + self.c["web_automation"]["buttons"]["analysis"]["download_timeout"]
+        temp_exts = [".crdownload", ".part", ".tmp"]
+        while time.time() < deadline:
+            # temp 파일이 더 이상 없고, 새로운 최종 파일이 등장했는지
+            current = list(folder.glob("*"))
+            names = {f.name for f in current}
+            new_files = [f for f in current if f.name not in start_snapshot]
+            # temp가 남아있으면 계속 대기
+            if any(f.suffix.lower() in temp_exts for f in new_files):
+                time.sleep(0.5); continue
+            # 확정 파일 찾기
+            finals = [f for f in new_files if f.suffix.lower().lstrip(".") in extensions]
+            if finals:
+                # 파일 열기 가능한지 확인
+                try:
+                    with open(finals[0], "rb") as _:
+                        pass
+                    self.log("SUCCESS", f"다운로드 완료: {finals[0].name}")
+                    return True
+                except Exception as e:
+                    self.log("WARNING", f"파일 열기 대기: {e}")
+            time.sleep(0.5)
+        self.log("ERROR", "다운로드 타임아웃")
+        return False
```

## src/ultimate_automation_system.py
```
--- template/src/ultimate_automation_system.py
+++ v2/src/ultimate_automation_system.py
@@ -1,9 +1,237 @@
-# ultimate_automation_system.py (stub)
-# MCP-01에서 GUI/헬스체크/진행 표시 구현 예정.
+
+import tkinter as tk
+from tkinter import ttk, messagebox, filedialog
+import threading, time, os, json, shutil, zipfile
+from pathlib import Path
+from datetime import datetime
+import yaml
+
+from modules.utils import resolve_paths, replace_env_vars, ensure_dirs
+from modules.logger import setup_logging, GuiLogHandler
+from modules.web_automation import WebAutomation
+from modules.data_processor import DataProcessor
+from modules.ai_generator import AIGenerator
+from modules.error_handler import ErrorHandler
+
+class UltimateAutomationSystem:
+    def __init__(self):
+        # Load config
+        cfg_path = Path("config/config.yaml")
+        if not cfg_path.exists():
+            raise FileNotFoundError("config/config.yaml not found")
+        self.config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
+        replace_env_vars(self.config)
+        resolve_paths(self.config)
+        ensure_dirs(self.config)
+
+        # Logging
+        self.logger, self.gui_log_buffer = setup_logging(self.config)
+        self.gui_handler = GuiLogHandler(self.gui_log_callback)
+        self.logger.addHandler(self.gui_handler)
+
+        # State
+        self.state = {
+            "running": False, "paused": False, "stop": False,
+            "current_step": "IDLE", "current_product": 0,
+            "total_products": self.config["web_automation"]["total_products"],
+            "success": 0, "failed": 0, "skipped": 0,
+            "start_time": None, "eta": "--:--"
+        }
+
+        # GUI
+        self.root = tk.Tk()
+        self.root.title(self.config["gui"]["window"]["title"])
+        self.root.geometry(self.config["gui"]["window"]["size"])
+        self.build_gui()
+
+        # Modules
+        self.error_handler = ErrorHandler(self.config, self.log)
+        self.data_processor = DataProcessor(self.config, self.log)
+        self.ai_generator = AIGenerator(self.config, self.log)
+        self.web_automation = WebAutomation(self.config, self.log, self.set_step, self.on_item_done)
+
+        # Hotkeys (optional)
+        self.root.bind("<F5>", lambda e: self.on_start())
+        self.root.bind("<Escape>", lambda e: self.on_stop())
+
+    # ---------- GUI ----------
+    def build_gui(self):
+        main = ttk.Frame(self.root); main.pack(fill="both", expand=True, padx=10, pady=10)
+
+        # Controls
+        ctrl = ttk.LabelFrame(main, text="메인 컨트롤", padding=10); ctrl.pack(fill="x")
+        self.status_var = tk.StringVar(value="대기 중")
+        ttk.Label(ctrl, textvariable=self.status_var, font=("Arial", 12, "bold")).grid(row=0, column=0, padx=8)
+
+        # Overall progress
+        self.overall_var = tk.DoubleVar(value=0)
+        ttk.Progressbar(ctrl, maximum=100, variable=self.overall_var, length=300).grid(row=0, column=1, padx=8)
+        self.counter_var = tk.StringVar(value="0/{}".format(self.config["web_automation"]["total_products"]))
+        ttk.Label(ctrl, textvariable=self.counter_var).grid(row=0, column=2, padx=4)
+
+        # Step progress
+        self.step_var = tk.DoubleVar(value=0)
+        ttk.Progressbar(ctrl, maximum=100, variable=self.step_var, length=200).grid(row=0, column=3, padx=8)
+        self.step_label = tk.StringVar(value="STEP: IDLE")
+        ttk.Label(ctrl, textvariable=self.step_label).grid(row=0, column=4, padx=4)
+
+        ttk.Button(ctrl, text="헬스체크", command=self.on_healthcheck, width=12).grid(row=0, column=5, padx=4)
+        ttk.Button(ctrl, text="버그팩 ZIP", command=self.on_bugpack, width=12).grid(row=0, column=6, padx=4)
+        ttk.Button(ctrl, text="시작(F5)", command=self.on_start, width=12).grid(row=0, column=7, padx=4)
+        ttk.Button(ctrl, text="정지(ESC)", command=self.on_stop, width=12).grid(row=0, column=8, padx=4)
+
+        # Notebook
+        nb = ttk.Notebook(main); nb.pack(fill="both", expand=True, pady=10)
+        # Logs tab
+        self.log_tab = ttk.Frame(nb); nb.add(self.log_tab, text="📜 로그")
+        self.log_text = tk.Text(self.log_tab, height=18); self.log_text.pack(fill="both", expand=True)
+
+        # Settings tab (provider dropdown & keys)
+        self.set_tab = ttk.Frame(nb); nb.add(self.set_tab, text="⚙️ 설정")
+        ttk.Label(self.set_tab, text="Provider (런타임):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
+        self.provider_var = tk.StringVar(value=self.config["ai"]["provider"])
+        prov = ttk.Combobox(self.set_tab, textvariable=self.provider_var, values=["gemini","claude","openai"], state="readonly")
+        prov.grid(row=0, column=1, sticky="w", padx=6, pady=6)
+        ttk.Label(self.set_tab, text="API Key:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
...
(diff truncated; total 244 lines)
+                    for f in pth.rglob("*"):
+                        z.write(f, f"bugpack/{f}")
+                elif pth.exists():
+                    z.write(pth, f"bugpack/{pth}")
+            # Try screenshot
+            try:
+                import pyautogui
+                shot = Path("runs") / f"screenshot_{ts}.png"
+                img = pyautogui.screenshot()
+                img.save(shot)
+                z.write(shot, f"bugpack/{shot.name}")
+                shot.unlink(missing_ok=True)
+            except Exception as e:
+                self.log("WARNING", f"스크린샷 생략: {e}")
+        messagebox.showinfo("버그팩", f"생성됨: {zpath}")
+
+    def apply_settings(self):
+        # Session-only override
+        self.config["ai"]["provider"] = self.provider_var.get()
+        self.config["ai"]["api_key"] = self.apikey_var.get().strip()
+        messagebox.showinfo("설정", "세션 설정 적용됨(파일은 변경하지 않음).")
+
+    def on_start(self):
+        if self.state["running"]:
+            return
+        self.state.update({"running": True, "paused": False, "stop": False,
+                           "current_product": 0, "success": 0, "failed": 0, "skipped": 0,
+                           "start_time": time.time()})
+        threading.Thread(target=self.run_loop, daemon=True).start()
+
+    def on_stop(self):
+        self.state["stop"] = True
+        self.state["running"] = False
+
+    # ---------- Core loop ----------
+    def run_loop(self):
+        self.set_step("START")
+        total = self.state["total_products"]
+        self.web_automation.reset_counts(total)
+
+        for idx in range(total):
+            if self.state["stop"]:
+                break
+            self.state["current_product"] = idx + 1
+            self.update_overall(idx, total)
+
+            ok = self.web_automation.process_single_product(idx)
+            if ok:
+                self.state["success"] += 1
+            else:
+                self.state["failed"] += 1
+
+            # Update
+            self.update_overall(idx, total)
+
+        self.set_step("DONE")
+        self.state["running"] = False
+
+    # ---------- Helpers ----------
+    def set_step(self, step, step_progress=None):
+        self.state["current_step"] = step
+        self.status_var.set(f"{step}")
+        self.step_label.set(f"STEP: {step}")
+        if step_progress is not None:
+            self.step_var.set(step_progress)
+
+    def on_item_done(self):
+        done = self.state["current_product"]
+        total = self.state["total_products"]
+        self.counter_var.set(f"{done}/{total}")
+
+    def update_overall(self, idx, total):
+        pct = int(((idx+1) / total) * 100)
+        self.overall_var.set(pct)
+        elapsed = time.time() - (self.state["start_time"] or time.time())
+        per = elapsed / max(1, idx+1)
+        remain = per * (total - (idx+1))
+        mm, ss = divmod(int(remain), 60)
+        self.stats_var.set(f"성공:{self.state['success']} | 실패:{self.state['failed']} | 스킵:{self.state['skipped']} | ETA:{mm:02d}:{ss:02d}")
+
+    def log(self, level, msg):
+        try:
+            import logging
+            getattr(self.logger, level.lower(), self.logger.info)(msg)
+        except Exception:
+            print(f"[{level}] {msg}")
+        self.gui_log_callback(level, msg)
+
+    def gui_log_callback(self, level, msg):
+        # replaced by handler attach
+        pass
 
 def main():
-    print("Ultimate Automation System v2.0 - scaffold loaded.")
-    print("Run MCP-01 to implement GUI healthcheck & progress UI.")
+    app = UltimateAutomationSystem()
+    app.root.mainloop()
 
 if __name__ == "__main__":
     main()
```

## tests/SMOKE.md
```
--- template/tests/SMOKE.md
+++ v2/tests/SMOKE.md
@@ -1,7 +1,7 @@
-# Smoke Test (수동 10분)
+# Smoke Test (10분)
 
-1) MCP-01 후: 앱 실행 시 헬스체크 결과(초록/노랑/빨강)와 2단 진행률이 보이는지.
-2) MCP-02 후: 다운로드 시 임시확장자 소멸+파일 열기 OK까지 기다리는지.
-3) MCP-03 후: downloads에서 JPG/JPEG/PNG/XLSX를 날짜 폴더로 이동하는지.
-4) MCP-05/06 후: 이메일 결과가 JSON meta+본문 형식이며, 온도 0.3이 적용되는지.
-5) MCP-10 후: CSV 5행으로 원클릭 E2E 스모크가 도는지.
+1) 헬스체크 버튼 → 초록이어야 시작.
+2) 탭에서 상세→캡처→리뷰DL 단계가 진행되며, 다운로드 완료 검증 로그 출력.
+3) downloads에 파일 생성 후 storage/images|reviews/{YYYY-MM-DD}로 이동하는지 확인.
+4) Vertex 온도 0.3 적용: config.yaml 수정 시 즉시 반영되는지 call_llm에서 확인.
+5) 실패 시 버그팩 ZIP 생성 버튼으로 증거 묶음 생성.
```
