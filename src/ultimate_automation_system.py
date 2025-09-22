from __future__ import annotations

import threading
import time
import os
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
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
        ttk.Label(self.set_tab, text="Provider (런타임):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.provider_var = tk.StringVar(value=self.config["ai"]["provider"])
        prov = ttk.Combobox(self.set_tab, textvariable=self.provider_var, values=["gemini","claude","openai"], state="readonly")
        prov.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(self.set_tab, text="API Key:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.apikey_var = tk.StringVar(value=self.config["ai"].get("api_key",""))
        ttk.Entry(self.set_tab, textvariable=self.apikey_var, width=60, show="•").grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Button(self.set_tab, text="적용", command=self.apply_settings).grid(row=1, column=2, padx=6, pady=6)

        # Stats
        self.stats_var = tk.StringVar(value="성공:0 | 실패:0 | 스킵:0 | ETA:--:--")
        ttk.Label(main, textvariable=self.stats_var).pack(anchor="w")

    def gui_log_callback(self, level, msg):
        self.log_text.insert("end", f"[{level}] {msg}\n")
        self.log_text.see("end")

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
        key = self.apikey_var.get().strip()
        if prov != "gemini":
            issues.append("현재 빌드는 Vertex(Gemini)만 활성. Claude/OpenAI는 후속.")
        if not key:
            issues.append("API Key 미설정(설정 탭에서 입력).")
        if missing:
            issues.append(f"템플릿 이미지 없음: {missing}")
        color = "초록(정상)" if not issues else "빨강(문제)"
        messagebox.showinfo("헬스체크", f"결과: {color}\n" + ("\n".join(issues) if issues else "문제 없음"))

    def on_bugpack(self):
        # Collect logs/config/checkpoint/screenshot (optional)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zpath = Path("runs") / f"bugpack_{ts}.zip"
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
        self.config["ai"]["provider"] = self.provider_var.get()
        self.config["ai"]["api_key"] = self.apikey_var.get().strip()
        messagebox.showinfo("설정", "세션 설정 적용됨(파일은 변경하지 않음).")

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

    def gui_log_callback(self, level, msg):
        # replaced by handler attach
        pass

def main():
    app = UltimateAutomationSystem()
    app.root.mainloop()

if __name__ == "__main__":
    main()
