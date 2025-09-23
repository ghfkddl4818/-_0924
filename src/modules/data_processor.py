from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


_DB_COLUMNS: List[str] = [
    "수집일자",
    "제품번호",
    "제품명",
    "브랜드명",
    "가격",
    "리뷰수",
    "평점",
    "처리상태",
    "이메일생성",
    "비고",
]


class ExcelDBManager:
    def __init__(self, db_path: str, sheet_name: str, log_callback):
        self.db_path = Path(db_path)
        self.sheet = sheet_name
        self.log = log_callback
        self.columns: List[str] = list(_DB_COLUMNS)
        self._ensure_db()
        self.columns = self._load_columns() or list(_DB_COLUMNS)

    def _ensure_db(self) -> None:
        if self.db_path.exists():
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(columns=_DB_COLUMNS)
        df.to_excel(self.db_path, sheet_name=self.sheet, index=False)
        self.log("INFO", f"DB 생성: {self.db_path}")

    def _load_columns(self) -> List[str]:
        try:
            df = pd.read_excel(self.db_path, sheet_name=self.sheet)
            cols = list(df.columns)
            if cols:
                return cols
        except Exception as exc:
            self.log("ERROR", f"DB 컬럼 로드 실패: {exc}")
        return list(_DB_COLUMNS)

    def add_product(self, row: Dict[str, Any]) -> bool:
        try:
            df = pd.read_excel(self.db_path, sheet_name=self.sheet)
        except Exception as exc:
            self.log("ERROR", f"DB 로드 실패: {exc}")
            return False

        columns = self.columns or list(df.columns)
        ordered_row = {col: row.get(col, "") for col in columns}
        df = pd.concat([df, pd.DataFrame([ordered_row])], ignore_index=True)
        try:
            df.to_excel(self.db_path, sheet_name=self.sheet, index=False)
        except Exception as exc:
            self.log("ERROR", f"DB 저장 실패: {exc}")
            return False

        if len(df) % 10 == 0:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.db_path.parent / f"backup_{ts}_{self.db_path.name}"
            try:
                shutil.copy(self.db_path, backup)
            except Exception as exc:
                self.log("WARNING", f"DB 백업 실패: {exc}")
        return True


class DataProcessor:
    _INVALID_CHARS = '<>:"/\\|?*'

    def __init__(self, config: dict, log_callback):
        self.c = config
        self.log = log_callback
        self.db = ExcelDBManager(
            self.c["database"]["file_path"],
            self.c["database"]["sheet_name"],
            log_callback,
        )

    def process_product(self, idx: int, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metadata = metadata or {}
        product_id = metadata.get("product_id") or idx + 1
        product_name = (
            metadata.get("product_name")
            or metadata.get("name")
            or f"Product {product_id:03d}"
        )
        brand = metadata.get("brand") or metadata.get("brand_name") or ""
        price = metadata.get("price") or metadata.get("amount") or ""
        review_count = metadata.get("review_count") or metadata.get("reviews") or ""
        rating = metadata.get("rating") or metadata.get("score") or ""
        features = metadata.get("features") or metadata.get("highlights") or ""
        review_summary = metadata.get("review_summary") or metadata.get("summary") or ""
        collected_at = metadata.get("collected_at") or datetime.now().strftime("%Y-%m-%d")
        store_name = self._determine_store_name(metadata)

        self.log(
            "INFO",
            f"사후 처리 시작: product_id={product_id}, name='{product_name}', store='{store_name}'",
        )

        assets = self.organize(
            product_id=product_id,
            product_name=product_name,
            store_name=store_name,
            date=collected_at,
        )
        images_count = len(assets.get("images", []))
        texts_count = len(assets.get("review_texts", []))
        self.log(
            "INFO",
            f"파일 정리 완료: images={images_count}, texts={texts_count}, base='{assets.get('base_dir', '')}'",
        )
        if images_count or texts_count:
            self.log("SUCCESS", f"정리 성공: product_id={product_id}, store='{store_name}'")
        else:
            self.log("WARNING", f"이동할 파일이 없습니다: product_id={product_id}, store='{store_name}'")

        db_row = self._build_db_row(
            date=self._normalize_date_for_db(collected_at),
            product_id=product_id,
            product_name=product_name,
            brand=brand,
            price=price,
            review_count=review_count,
            rating=rating,
            status=metadata.get("status", "완료"),
            email_status=metadata.get("email_status", "N"),
            note=metadata.get("note", ""),
        )
        if self.db.add_product(db_row):
            self.log("INFO", "DB 업데이트 완료")
        else:
            self.log("ERROR", "DB 업데이트 실패")

        payload = self._build_email_payload(
            product_id=product_id,
            product_name=product_name,
            brand=brand,
            price=price,
            rating=rating,
            review_count=review_count,
            features=features,
            review_summary=review_summary,
            assets=assets,
            metadata=metadata,
            collected_at=collected_at,
            store_name=store_name,
        )
        payload["store_name"] = store_name
        payload["collection_directory"] = assets.get("base_dir", "")
        return payload

    def organize(
        self,
        *,
        product_id: int,
        product_name: str,
        store_name: str,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        date_folder = self._normalize_date(date)
        store_dir = self._sanitize_component(store_name, default="UnknownStore")
        base_dir = self._collection_root() / date_folder / store_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        base_filename = self._build_base_filename(product_id, product_name, store_name)

        download_dir = Path(self.c["paths"]["download_folder"])
        if not download_dir.exists():
            self.log("ERROR", f"다운로드 폴더를 찾을 수 없습니다: {download_dir}")
            return {
                "base_dir": str(base_dir),
                "images": [],
                "reviews": [],
                "review_texts": [],
                "review_excels": [],
            }

        image_sources = self._collect_files(download_dir, self._img_exts())
        excel_sources = self._collect_files(download_dir, ["xlsx", "xls"])

        moved_images = self._move_files_with_base(image_sources, base_dir, base_filename, "IMAGE")
        moved_excels = self._move_files_with_base(excel_sources, base_dir, base_filename, "EXCEL")

        txt_files: List[Path] = []
        for excel_path in moved_excels:
            txt_path = excel_path.with_suffix('.txt')
            if self._convert_excel_to_txt(excel_path, txt_path):
                txt_files.append(txt_path)

        return {
            "base_dir": str(base_dir),
            "images": [str(p) for p in moved_images],
            "reviews": [str(p) for p in txt_files],
            "review_texts": [str(p) for p in txt_files],
            "review_excels": [str(p) for p in moved_excels],
        }

    def _img_exts(self) -> List[str]:
        return ["jpg", "jpeg", "png"]

    def _collect_files(self, folder: Path, extensions: List[str]) -> List[Path]:
        allowed = {f'.{ext.lower()}' for ext in extensions}
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in allowed]
        return sorted(files)

    def _move_files_with_base(
        self,
        files: List[Path],
        destination: Path,
        base_name: str,
        category: str,
    ) -> List[Path]:
        moved: List[Path] = []
        for index, source in enumerate(files, start=1):
            suffix = source.suffix.lower()
            name = base_name if index == 1 else f"{base_name}_{index}"
            target = destination / f"{name}{suffix}"
            target = self._resolve_conflict(target)
            try:
                shutil.move(str(source), str(target))
                moved.append(target)
                self.log("SUCCESS", f"{category} 파일 이동: {source.name} -> {target}")
            except Exception as exc:
                self.log("ERROR", f"{category} 파일 이동 실패: {source} -> {target}: {exc}")
        return moved

    def _resolve_conflict(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        counter = 2
        while True:
            candidate = path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def _convert_excel_to_txt(self, source: Path, target: Path) -> bool:
        try:
            df = pd.read_excel(source)
        except Exception as exc:
            self.log("ERROR", f"엑셀 로드 실패: {source.name}: {exc}")
            return False
        try:
            df = df.fillna("")
            df.to_csv(target, sep='	', index=False, encoding='utf-8-sig')
            self.log("SUCCESS", f"TXT 변환 완료: {target.name}")
            return True
        except Exception as exc:
            self.log("ERROR", f"TXT 저장 실패: {target.name}: {exc}")
            return False

    def _collection_root(self) -> Path:
        root = self.c.get("paths", {}).get("collection_root")
        if not root:
            root = r"E:/업무/03_데이터_수집"
        return Path(root)

    def _build_base_filename(self, product_id: int, product_name: str, store_name: str) -> str:
        product_part = self._sanitize_component(product_name, default="제품")
        store_part = self._sanitize_component(store_name, default="스토어")
        return f"{product_id:03d} - {product_part} _ {store_part}"

    def _sanitize_component(self, text: str, *, default: str) -> str:
        if not text:
            return default
        cleaned = []
        for ch in str(text):
            if ch in self._INVALID_CHARS or ord(ch) < 32:
                cleaned.append(' ')
            else:
                cleaned.append(ch)
        normalized = ' '.join(''.join(cleaned).replace('\r', ' ').replace('\n', ' ').split())
        normalized = normalized.strip().strip('.')
        return normalized or default

    def _normalize_date(self, value: Optional[str]) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y%m%d")
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y%m%d")
                except ValueError:
                    continue
        return datetime.now().strftime("%Y%m%d")

    def _normalize_date_for_db(self, value: str) -> str:
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"):
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return datetime.now().strftime("%Y-%m-%d")

    def _determine_store_name(self, metadata: Dict[str, Any]) -> str:
        for key in ("store_name", "store", "seller", "seller_name", "mall_name", "vendor"):
            value = metadata.get(key)
            if value:
                return str(value)
        return "UnknownStore"

    def _build_db_row(
        self,
        *,
        date: str,
        product_id: int,
        product_name: str,
        brand: str,
        price: Any,
        review_count: Any,
        rating: Any,
        status: str,
        email_status: str,
        note: str,
    ) -> Dict[str, Any]:
        row = {col: "" for col in self.db.columns}
        mapping = {
            "수집일자": date,
            "제품번호": product_id,
            "제품명": product_name,
            "브랜드명": brand,
            "가격": price,
            "리뷰수": review_count,
            "평점": rating,
            "처리상태": status,
            "이메일생성": email_status,
            "비고": note,
        }
        for key, value in mapping.items():
            if key in row:
                row[key] = value
        return row

    def _build_email_payload(
        self,
        *,
        product_id: int,
        product_name: str,
        brand: str,
        price: Any,
        rating: Any,
        review_count: Any,
        features: Any,
        review_summary: Any,
        assets: Dict[str, Any],
        metadata: Dict[str, Any],
        collected_at: str,
        store_name: str,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "product_id": product_id,
            "product_name": product_name,
            "brand": brand,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "features": features,
            "review_summary": review_summary,
            "collected_at": collected_at,
            "assets": assets,
        }
        extras = {
            "image_paths": assets.get("images", []),
            "review_files": assets.get("reviews", []),
            "review_excels": assets.get("review_excels", []),
            "review_texts": assets.get("review_texts", []),
            "store_name": store_name,
            "source_metadata": metadata,
        }
        payload.update(extras)
        return payload

    def save_cold_email(self, payload: Dict[str, Any], email_content: str) -> Optional[str]:
        """생성된 콜드메일을 적절한 폴더에 저장"""
        try:
            product_id = payload.get("product_id", 1)
            product_name = payload.get("product_name", "Unknown")
            store_name = payload.get("store_name", "UnknownStore")
            collected_at = payload.get("collected_at") or datetime.now().strftime("%Y-%m-%d")

            # 날짜 폴더와 스토어 폴더 구조 사용
            date_folder = self._normalize_date(collected_at)
            store_dir = self._sanitize_component(store_name, default="UnknownStore")
            base_dir = self._collection_root() / date_folder / store_dir
            base_dir.mkdir(parents=True, exist_ok=True)

            # 파일명 생성 (기존 패턴과 일치)
            base_filename = self._build_base_filename(product_id, product_name, store_name)
            email_file = base_dir / f"{base_filename}_cold_email.txt"

            # 중복 파일명 처리
            email_file = self._resolve_conflict(email_file)

            # 콜드메일 저장
            email_file.write_text(email_content, encoding="utf-8")

            self.log("SUCCESS", f"콜드메일 저장 완료: {email_file}")
            return str(email_file)

        except Exception as exc:
            self.log("ERROR", f"콜드메일 저장 실패: {exc}")
            return None

    def update_db_sample(self, idx: int, product_name: str) -> bool:
        row = self._build_db_row(
            date=datetime.now().strftime("%Y-%m-%d"),
            product_id=idx + 1,
            product_name=product_name,
            brand="",
            price="",
            review_count="",
            rating="",
            status="완료",
            email_status="N",
            note="",
        )
        ok = self.db.add_product(row)
        self.log("INFO", f"DB 샘플 업데이트: {'OK' if ok else 'FAIL'}")
        return ok