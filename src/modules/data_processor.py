from __future__ import annotations

import hashlib
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


def _slugify(text: str) -> str:
    slug = ''.join(ch if ch.isalnum() else '-' for ch in text)
    slug = slug.strip('-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.lower() or 'product'


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
    def __init__(self, config: dict, log_callback):
        self.c = config
        self.log = log_callback
        self.db = ExcelDBManager(
            self.c["database"]["file_path"],
            self.c["database"]["sheet_name"],
            log_callback,
        )
        self.hash_cache: Dict[str, str] = {}

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
        slug = metadata.get("slug") or _slugify(f"{product_name}-{product_id}")

        self.log(
            "INFO",
            f"사후 처리 시작: product_id={product_id}, name='{product_name}', slug='{slug}'",
        )

        assets = self.organize(product_slug=slug, date=collected_at)
        self.log(
            "INFO",
            f"파일 정리 완료: images={len(assets['images'])}, reviews={len(assets['reviews'])}",
        )

        db_row = self._build_db_row(
            date=collected_at,
            product_id=product_id,
            product_name=product_name,
            brand=brand,
            price=price,
            review_count=review_count,
            rating=rating,
            status="완료",
            email_status="대기",
            note=metadata.get("note", ""),
        )
        db_ok = self.db.add_product(db_row)
        if db_ok:
            self.log("INFO", f"DB 업데이트 완료: product_id={product_id}")
        else:
            self.log("ERROR", f"DB 업데이트 실패: product_id={product_id}")

        email_payload = self._build_email_payload(
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
        )
        self.log("INFO", f"콜드메일 페이로드 준비 완료: product_id={product_id}")

        return {
            "product_id": product_id,
            "product_name": product_name,
            "brand": brand,
            "price": price,
            "rating": rating,
            "review_count": review_count,
            "features": features,
            "review_summary": review_summary,
            "collected_at": collected_at,
            "slug": slug,
            "assets": assets,
            "db_row": db_row,
            "db_ok": db_ok,
            "email_payload": email_payload,
            "metadata": metadata,
        }

    def organize(self, product_slug: str, date: Optional[str] = None) -> Dict[str, Any]:
        date = date or datetime.now().strftime("%Y-%m-%d")
        storage_root = Path(self.c["paths"]["storage_folder"])
        base_dir = storage_root / date / product_slug
        images_dir = base_dir / "images"
        reviews_dir = base_dir / "reviews"

        images = self._move_files(self._img_exts(), images_dir)
        reviews = self._move_files(["xlsx", "xls"], reviews_dir)

        return {
            "base_dir": str(base_dir),
            "images": [str(p) for p in images],
            "reviews": [str(p) for p in reviews],
        }

    def _img_exts(self) -> List[str]:
        return ["jpg", "jpeg", "png"]

    def _move_files(self, exts: List[str], destination: Path) -> List[Path]:
        source = Path(self.c["paths"]["download_folder"])
        destination.mkdir(parents=True, exist_ok=True)
        moved: List[Path] = []
        for ext in exts:
            for file_path in sorted(source.glob(f"*.{ext}")):
                target = destination / self._build_unique_name(file_path)
                try:
                    shutil.move(str(file_path), str(target))
                    moved.append(target)
                    self.log("INFO", f"파일 이동: {file_path.name} -> {target}")
                except Exception as exc:
                    self.log("ERROR", f"파일 이동 실패: {file_path} -> {target}: {exc}")
        return moved

    def _build_unique_name(self, file_path: Path) -> str:
        digest = self._hash_file(file_path)
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{file_path.stem}_{timestamp}_{digest[:8]}{file_path.suffix.lower()}"

    def _hash_file(self, file_path: Path) -> str:
        cache_key = str(file_path.resolve())
        if cache_key in self.hash_cache:
            return self.hash_cache[cache_key]
        hasher = hashlib.sha256()
        with file_path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(8192), b''):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        self.hash_cache[cache_key] = digest
        return digest

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
            "source_metadata": metadata,
        }
        payload.update(extras)
        return payload

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
