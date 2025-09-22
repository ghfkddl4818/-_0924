
import pandas as pd, shutil, hashlib, os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

class ExcelDBManager:
    def __init__(self, db_path: str, sheet_name: str, log_callback):
        self.db_path = Path(db_path); self.sheet = sheet_name; self.log = log_callback
        self._ensure_db()

    def _ensure_db(self):
        if not self.db_path.exists():
            cols = ['수집일자','제품번호','제품명','브랜드명','가격','리뷰수','평점','처리상태','이메일생성','비고']
            df = pd.DataFrame(columns=cols)
            df.to_excel(self.db_path, sheet_name=self.sheet, index=False)
            self.log("INFO", f"DB 생성: {self.db_path}")

    def add_product(self, row: Dict) -> bool:
        try:
            df = pd.read_excel(self.db_path, sheet_name=self.sheet)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_excel(self.db_path, sheet_name=self.sheet, index=False)
            # backup every 10 rows
            if len(df) % 10 == 0:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                shutil.copy(self.db_path, self.db_path.parent / f"backup_{ts}_{self.db_path.name}")
            return True
        except Exception as e:
            self.log("ERROR", f"DB 업데이트 실패: {e}")
            return False

class DataProcessor:
    def __init__(self, config: dict, log_callback):
        self.c = config; self.log = log_callback
        self.db = ExcelDBManager(self.c["database"]["file_path"], self.c["database"]["sheet_name"], log_callback)
        self.hash_cache = {}

    def organize(self, date: Optional[str]=None) -> Dict[str,int]:
        if not date: date = datetime.now().strftime("%Y-%m-%d")
        return {
            "images": self._move_files(self._img_exts(), f"images/{date}"),
            "reviews": self._move_files(["xlsx"], f"reviews/{date}")
        }

    def _img_exts(self) -> List[str]:
        return ["jpg","jpeg","png"]

    def _move_files(self, exts: List[str], subdir: str) -> int:
        src = Path(self.c["paths"]["download_folder"])
        dst = Path(self.c["paths"]["storage_folder"]) / subdir
        dst.mkdir(parents=True, exist_ok=True)
        moved = 0
        for ext in exts:
            for f in src.glob(f"*.{ext}"):
                new_name = f"{f.stem}_{datetime.now().strftime('%H%M%S')}.{ext}"
                target = dst / new_name
                try:
                    shutil.move(str(f), str(target))
                    moved += 1
                    self.log("INFO", f"이동: {f.name} → {target}")
                except Exception as e:
                    self.log("ERROR", f"이동 실패: {f} -> {target} : {e}")
        return moved

    def update_db_sample(self, idx: int, product_name: str):
        row = {
            "수집일자": datetime.now().strftime("%Y-%m-%d"),
            "제품번호": idx+1, "제품명": product_name, "브랜드명": "",
            "가격": "", "리뷰수": "", "평점": "", "처리상태": "완료",
            "이메일생성": "N", "비고": ""
        }
        ok = self.db.add_product(row)
        self.log("INFO", f"DB 업데이트: {'OK' if ok else 'FAIL'}")
