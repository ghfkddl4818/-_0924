from __future__ import annotations

import io
import json
import os
import shutil
import threading
import time
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from typing import NoReturn

import yaml

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ModuleNotFoundError as exc:  # pragma: no cover - platform-specific guard
    def _missing_tkinter() -> NoReturn:
        message = (
            "tkinter 모듈을 불러올 수 없습니다. GUI 실행을 위해 Python 설치 옵션에서 "
            "Tcl/Tk를 포함하거나, Windows용 설치 관리자에서 'tcl/tk and IDLE' 구성요소를 켜 주세요."
        )
        print(f"[Ultimate Automation System] {message}")
        raise SystemExit(1) from exc

    _missing_tkinter()


from modules.utils import resolve_paths, replace_env_vars, ensure_dirs
from modules.logger import setup_logging, GuiLogHandler
from modules.web_automation import WebAutomation
from modules.data_processor import DataProcessor
from modules.ai_generator import AIGenerator
from modules.error_handler import ErrorHandler
from pipeline.cli import STAGES
from pipeline.segment_cli import run_range, run_stage

class UltimateAutomationSystem:
    def __init__(self):
        # Load config
        cfg_path = Path("config/config.yaml")
        if not cfg_path.exists():
            raise FileNotFoundError("config/config.yaml not found")
        self.config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        replace_env_vars(self.config)
        resolve_paths(self.config)
        ensure_dirs(self.config)

        # Logging
        self.logger, self.gui_log_buffer = setup_logging(self.config)
        self.gui_handler = GuiLogHandler(self.gui_log_callback)
        self.logger.addHandler(self.gui_handler)

        # State
        self.state = {
            "running": False, "paused": False, "stop": False,
            "current_step": "IDLE", "current_product": 0,
            "total_products": self.config["web_automation"]["total_products"],
            "success": 0, "failed": 0, "skipped": 0,
            "start_time": None, "eta": "--:--"
        }

        # GUI
        self.root = tk.Tk()
        self.root.title(self.config["gui"]["window"]["title"])
        self.root.geometry(self.config["gui"]["window"]["size"])
        self.build_gui()

        # Modules
        self.error_handler = ErrorHandler(self.config, self.log)
        self.data_processor = DataProcessor(self.config, self.log)
        self.ai_generator = AIGenerator(self.config, self.log)
        self.web_automation = WebAutomation(self.config, self.log, self.set_step, self.on_item_done)

        # Hotkeys (optional)
        self.root.bind("<F5>", lambda e: self.on_start())
        self.root.bind("<Escape>", lambda e: self.on_stop())

    # ---------- GUI ----------
    def build_gui(self):
        main = ttk.Frame(self.root); main.pack(fill="both", expand=True, padx=10, pady=10)

        # Controls
        ctrl = ttk.LabelFrame(main, text="메인 컨트롤", padding=10); ctrl.pack(fill="x")
        self.status_var = tk.StringVar(value="대기 중")
        ttk.Label(ctrl, textvariable=self.status_var, font=("Arial", 12, "bold")).grid(row=0, column=0, padx=8)

        # Overall progress
        self.overall_var = tk.DoubleVar(value=0)
        ttk.Progressbar(ctrl, maximum=100, variable=self.overall_var, length=300).grid(row=0, column=1, padx=8)
        self.counter_var = tk.StringVar(value="0/{}".format(self.config["web_automation"]["total_products"]))
        ttk.Label(ctrl, textvariable=self.counter_var).grid(row=0, column=2, padx=4)

        # Step progress
        self.step_var = tk.DoubleVar(value=0)
        ttk.Progressbar(ctrl, maximum=100, variable=self.step_var, length=200).grid(row=0, column=3, padx=8)
        self.step_label = tk.StringVar(value="STEP: IDLE")
        ttk.Label(ctrl, textvariable=self.step_label).grid(row=0, column=4, padx=4)

        ttk.Button(ctrl, text="헬스체크", command=self.on_healthcheck, width=12).grid(row=0, column=5, padx=4)
        ttk.Button(ctrl, text="버그팩 ZIP", command=self.on_bugpack, width=12).grid(row=0, column=6, padx=4)
        ttk.Button(ctrl, text="시작(F5)", command=self.on_start, width=12).grid(row=0, column=7, padx=4)
        ttk.Button(ctrl, text="정지(ESC)", command=self.on_stop, width=12).grid(row=0, column=8, padx=4)

        # Notebook
        nb = ttk.Notebook(main); nb.pack(fill="both", expand=True, pady=10)
        # Logs tab
        self.log_tab = ttk.Frame(nb); nb.add(self.log_tab, text="📜 로그")
        self.log_text = tk.Text(self.log_tab, height=18); self.log_text.pack(fill="both", expand=True)

        # Settings tab (provider dropdown & keys)
        self.set_tab = ttk.Frame(nb); nb.add(self.set_tab, text="⚙️ 설정")
        ttk.Label(self.set_tab, text="Provider (Vertex AI):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.provider_var = tk.StringVar(value=self.config.get("ai", {}).get("provider", "vertex"))
        prov = ttk.Combobox(self.set_tab, textvariable=self.provider_var, values=["vertex"], state="readonly")
        prov.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(self.set_tab, text="Project ID:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.project_var = tk.StringVar(value=self.config.get("ai", {}).get("vertex", {}).get("project_id", ""))
        ttk.Entry(self.set_tab, textvariable=self.project_var, width=60).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(self.set_tab, text="Location:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.location_var = tk.StringVar(value=self.config.get("ai", {}).get("vertex", {}).get("location", ""))
        ttk.Entry(self.set_tab, textvariable=self.location_var, width=60).grid(row=2, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(self.set_tab, text="Model name:").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.model_name_var = tk.StringVar(value=self.config.get("ai", {}).get("vertex", {}).get("model", {}).get("name", ""))
        ttk.Entry(self.set_tab, textvariable=self.model_name_var, width=60).grid(row=3, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(self.set_tab, text="Credentials path:").grid(row=4, column=0, sticky="e", padx=6, pady=6)
        self.credentials_path_var = tk.StringVar(value=self.config.get("ai", {}).get("vertex", {}).get("credentials_path", ""))
        ttk.Entry(self.set_tab, textvariable=self.credentials_path_var, width=60).grid(row=4, column=1, sticky="w", padx=6, pady=6)
        ttk.Button(self.set_tab, text="적용", command=self.apply_settings).grid(row=4, column=2, padx=6, pady=6)

        # Pipeline tab
        self.pipeline_tab = ttk.Frame(nb); nb.add(self.pipeline_tab, text="Pipeline")
        self._build_pipeline_tab(self.pipeline_tab)

        # Stats
        self.stats_var = tk.StringVar(value="성공:0 | 실패:0 | 스킵:0 | ETA:--:--")
        ttk.Label(main, textvariable=self.stats_var).pack(anchor="w")

    def gui_log_callback(self, level, msg):
        self.log_text.insert("end", f"[{level}] {msg}\n")
        self.log_text.see("end")

    # ---------- Pipeline controls ----------
    def _build_pipeline_tab(self, parent):
        controls = ttk.LabelFrame(parent, text="파이프라인 실행", padding=10)
        controls.pack(fill="x", padx=6, pady=6)

        default_input = (Path("tests/fixtures").resolve())
        self.pipeline_input_var = tk.StringVar(value=str(default_input))
        ttk.Label(controls, text="입력 경로").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        ttk.Entry(controls, textvariable=self.pipeline_input_var, width=60).grid(row=0, column=1, columnspan=4, sticky="we", padx=4, pady=4)
        ttk.Button(controls, text="파일 선택", command=self.on_pipeline_browse_file, width=12).grid(row=0, column=5, padx=4)
        ttk.Button(controls, text="폴더 선택", command=self.on_pipeline_browse_dir, width=14).grid(row=0, column=6, padx=4)

        ttk.Label(controls, text="처리 개수").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.pipeline_limit_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.pipeline_limit_var, width=10).grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(controls, text="언어").grid(row=1, column=2, sticky="e", padx=4, pady=4)
        self.pipeline_language_var = tk.StringVar(value="en")
        ttk.Entry(controls, textvariable=self.pipeline_language_var, width=10).grid(row=1, column=3, sticky="w", padx=4, pady=4)

        stage_frame = ttk.LabelFrame(parent, text="단일 단계 실행", padding=10)
        stage_frame.pack(fill="x", padx=6, pady=6)
        self.pipeline_stage_var = tk.StringVar(value=STAGES[0])
        ttk.Label(stage_frame, text="단계").grid(row=0, column=0, padx=4, pady=4)
        ttk.Combobox(stage_frame, textvariable=self.pipeline_stage_var, values=list(STAGES), state="readonly", width=15).grid(row=0, column=1, padx=4, pady=4)
        self.pipeline_stage_status = tk.StringVar(value="대기 중")
        self.pipeline_stage_button = ttk.Button(stage_frame, text="Run 단계", command=self.on_pipeline_run_stage, width=14)
        self.pipeline_stage_button.grid(row=0, column=2, padx=6, pady=4)
        ttk.Label(stage_frame, textvariable=self.pipeline_stage_status).grid(row=0, column=3, padx=4, pady=4)

        range_frame = ttk.LabelFrame(parent, text="단계 Range", padding=10)
        range_frame.pack(fill="x", padx=6, pady=6)
        self.pipeline_from_var = tk.StringVar(value=STAGES[0])
        self.pipeline_to_var = tk.StringVar(value=STAGES[-1])
        ttk.Label(range_frame, text="시작 단계").grid(row=0, column=0, padx=4, pady=4)
        ttk.Combobox(range_frame, textvariable=self.pipeline_from_var, values=list(STAGES), state="readonly", width=15).grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(range_frame, text="마지막 단계").grid(row=0, column=2, padx=4, pady=4)
        ttk.Combobox(range_frame, textvariable=self.pipeline_to_var, values=list(STAGES), state="readonly", width=15).grid(row=0, column=3, padx=4, pady=4)
        self.pipeline_range_status = tk.StringVar(value="대기 중")
        self.pipeline_range_button = ttk.Button(range_frame, text="구간 실행", command=self.on_pipeline_run_range, width=14)
        self.pipeline_range_button.grid(row=0, column=4, padx=6, pady=4)
        ttk.Label(range_frame, textvariable=self.pipeline_range_status).grid(row=0, column=5, padx=4, pady=4)

        output_frame = ttk.LabelFrame(parent, text="실행 결과", padding=10)
        output_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self.pipeline_output = tk.Text(output_frame, height=16)
        self.pipeline_output.pack(fill="both", expand=True)

    def on_pipeline_browse_file(self):
        selection = filedialog.askopenfilename(title="Select HTML file", filetypes=[("HTML", "*.html;*.htm"), ("All", "*.*")])
        if selection:
            self.pipeline_input_var.set(selection)

    def on_pipeline_browse_dir(self):
        selection = filedialog.askdirectory(title="Select input folder")
        if selection:
            self.pipeline_input_var.set(selection)

    def on_pipeline_run_stage(self):
        ok, limit = self._parse_pipeline_limit()
        if not ok:
            return
        stage = self.pipeline_stage_var.get()
        self._kickoff_pipeline(mode="stage", stage=stage, from_stage=None, to_stage=None, limit=limit)

    def on_pipeline_run_range(self):
        ok, limit = self._parse_pipeline_limit()
        if not ok:
            return
        from_stage = self.pipeline_from_var.get()
        to_stage = self.pipeline_to_var.get()
        if STAGES.index(from_stage) > STAGES.index(to_stage):
            messagebox.showerror("Pipeline", "시작 단계가 종료 단계보다 뒤에 있을 수 없습니다.")
            return
        self._kickoff_pipeline(mode="range", stage=None, from_stage=from_stage, to_stage=to_stage, limit=limit)

    def _parse_pipeline_limit(self):
        raw = (self.pipeline_limit_var.get() or "").strip()
        if not raw:
            return True, None
        try:
            value = int(raw, 10)
        except ValueError:
            messagebox.showerror("Pipeline", "처리 개수는 숫자여야 합니다.")
            return False, None
        if value <= 0:
            messagebox.showerror("Pipeline", "처리 개수는 1 이상 입력해야 합니다.")
            return False, None
        return True, value

    def _kickoff_pipeline(self, *, mode: str, stage: str | None, from_stage: str | None, to_stage: str | None, limit: int | None):
        input_path = Path(self.pipeline_input_var.get()).expanduser()
        if not input_path.exists():
            messagebox.showerror("Pipeline", f"입력 경로를 찾을 수 없습니다: {input_path}")
            return
        language = (self.pipeline_language_var.get() or "en").strip() or "en"

        self.pipeline_output.delete("1.0", "end")
        self.pipeline_output.insert("end", "실행 중...\n")
        self.pipeline_stage_button.config(state="disabled")
        self.pipeline_range_button.config(state="disabled")
        self.pipeline_stage_status.set("실행 중")
        self.pipeline_range_status.set("실행 중")

        def worker():
            buffer = io.StringIO()
            status = ""
            try:
                if mode == "stage" and stage:
                    count = run_stage(
                        stage,
                        input_path=input_path,
                        limit=limit,
                        language=language,
                        stream=buffer,
                    )
                    status = f"단계 실행 완료 ({count}건)"
                elif mode == "range" and from_stage and to_stage:
                    count = run_range(
                        from_stage=from_stage,
                        to_stage=to_stage,
                        input_path=input_path,
                        limit=limit,
                        language=language,
                        stream=buffer,
                    )
                    status = f"구간 실행 완료 ({count}건)"
                else:
                    raise ValueError("잘못된 실행 모드")
                output = buffer.getvalue().strip() or "결과가 없습니다."
            except Exception as exc:
                output = f"[오류] {exc}\n{traceback.format_exc()}"
                status = "실패"

            def finalize():
                self.pipeline_output.delete("1.0", "end")
                self.pipeline_output.insert("end", output + "\n")
                self.pipeline_output.see("end")
                if mode == "stage":
                    self.pipeline_stage_status.set(status)
                else:
                    self.pipeline_stage_status.set("대기 중")
                if mode == "range":
                    self.pipeline_range_status.set(status)
                else:
                    self.pipeline_range_status.set("대기 중")
                self.pipeline_stage_button.config(state="normal")
                self.pipeline_range_button.config(state="normal")

            self.root.after(0, finalize)

        threading.Thread(target=worker, daemon=True).start()

    # ---------- Actions ----------
    def on_healthcheck(self):
        issues = []
        # folders
        for key in ["download_folder","storage_folder","output_folder","log_folder","checkpoint_folder"]:
            p = Path(self.config["paths"][key]); p.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                issues.append(f"경로 생성 실패: {p}")
        # images
        required = ["assets/img/detail_button.png","assets/img/fireshot_save.png",
                    "assets/img/analysis_start.png","assets/img/excel_download.png"]
        missing = [x for x in required if not Path(x).exists()]
        # provider gating
        prov = self.provider_var.get()
        project = self.project_var.get().strip()
        location = self.location_var.get().strip()
        model_name = self.model_name_var.get().strip()
        credentials_input = self.credentials_path_var.get().strip()
        credential_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if prov != "vertex":
            issues.append("현재 빌드는 Vertex AI Gemini만 지원합니다.")
        if not project:
            issues.append("프로젝트 ID를 입력해주세요.")
        if not location:
            issues.append("리전을 입력해주세요.")
        if not model_name:
            issues.append("모델 이름을 입력해주세요.")
        if credentials_input:
            cred_path = Path(credentials_input)
            if not cred_path.exists():
                issues.append(f"서비스 계정 키 파일을 찾을 수 없습니다: {cred_path}")
        elif not credential_env:
            issues.append("서비스 계정 키 경로를 입력하거나 GOOGLE_APPLICATION_CREDENTIALS 환경변수를 설정해주세요.")
        if missing:
            issues.append(f"템플릿 이미지 없음: {missing}")
        color = "초록(정상)" if not issues else "빨강(문제)"
        messagebox.showinfo("헬스체크", f"결과: {color}\n" + ("\n".join(issues) if issues else "문제 없음"))

    def on_bugpack(self):
        # Collect logs/config/checkpoint/screenshot (optional)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        runs_dir = Path("runs")
        runs_dir.mkdir(parents=True, exist_ok=True)
        zpath = runs_dir / f"bugpack_{ts}.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in ["logs", "config/config.yaml", "data/checkpoint"]:
                pth = Path(p)
                if pth.is_dir():
                    for f in pth.rglob("*"):
                        z.write(f, f"bugpack/{f}")
                elif pth.exists():
                    z.write(pth, f"bugpack/{pth}")
            # Try screenshot
            try:
                import pyautogui
                shot = Path("runs") / f"screenshot_{ts}.png"
                img = pyautogui.screenshot()
                img.save(shot)
                z.write(shot, f"bugpack/{shot.name}")
                shot.unlink(missing_ok=True)
            except Exception as e:
                self.log("WARNING", f"스크린샷 생략: {e}")
        messagebox.showinfo("버그팩", f"생성됨: {zpath}")

    def apply_settings(self):
        # Session-only override
        ai_conf = self.config.setdefault("ai", {})
        ai_conf["provider"] = self.provider_var.get()
        vertex_conf = ai_conf.setdefault("vertex", {})
        vertex_conf["project_id"] = self.project_var.get().strip()
        vertex_conf["location"] = self.location_var.get().strip() or "us-central1"
        vertex_conf["credentials_path"] = self.credentials_path_var.get().strip()
        model_conf = vertex_conf.setdefault("model", {})
        model_conf["name"] = self.model_name_var.get().strip() or model_conf.get("name", "")
        messagebox.showinfo(
            "설정",
            "지금 실행에만 적용돼요. 파일에도 반영하려면 config/config.yaml을 직접 수정해주세요.",
        )
        messagebox.showinfo("설정", "설정이 메모리에 반영되었습니다 (파일에는 자동 저장되지 않음).")

    def on_start(self):
        if self.state["running"]:
            return
        self.state.update({"running": True, "paused": False, "stop": False,
                           "current_product": 0, "success": 0, "failed": 0, "skipped": 0,
                           "start_time": time.time()})
        threading.Thread(target=self.run_loop, daemon=True).start()

    def on_stop(self):
        self.state["stop"] = True
        self.state["running"] = False

    # ---------- Core loop ----------
    def run_loop(self):
        self.set_step("START")
        total = self.state["total_products"]
        self.web_automation.reset_counts(total)

        for idx in range(total):
            if self.state["stop"]:
                break
            self.state["current_product"] = idx + 1
            self.update_overall(idx, total)

            ok = self.web_automation.process_single_product(idx)
            if ok:
                self.state["success"] += 1
            else:
                self.state["failed"] += 1

            # Update
            self.update_overall(idx, total)

        self.set_step("DONE")
        self.state["running"] = False

    # ---------- Helpers ----------
    def set_step(self, step, step_progress=None):
        self.state["current_step"] = step
        self.status_var.set(f"{step}")
        self.step_label.set(f"STEP: {step}")
        if step_progress is not None:
            self.step_var.set(step_progress)

    def on_item_done(self):
        done = self.state["current_product"]
        total = self.state["total_products"]
        self.counter_var.set(f"{done}/{total}")

    def update_overall(self, idx, total):
        pct = int(((idx+1) / total) * 100)
        self.overall_var.set(pct)
        elapsed = time.time() - (self.state["start_time"] or time.time())
        per = elapsed / max(1, idx+1)
        remain = per * (total - (idx+1))
        mm, ss = divmod(int(remain), 60)
        self.stats_var.set(f"성공:{self.state['success']} | 실패:{self.state['failed']} | 스킵:{self.state['skipped']} | ETA:{mm:02d}:{ss:02d}")

    def log(self, level, msg):
        try:
            import logging
            getattr(self.logger, level.lower(), self.logger.info)(msg)
        except Exception:
            print(f"[{level}] {msg}")
        self.gui_log_callback(level, msg)

def main():
    app = UltimateAutomationSystem()
    app.root.mainloop()

if __name__ == "__main__":
    main()
