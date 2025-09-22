from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import pytesseract
from PIL import Image

import vertexai
from google.oauth2 import service_account
from vertexai.preview.generative_models import GenerationConfig, GenerativeModel


class AIGenerator:
    def __init__(self, config: dict, log_callback):
        self.c = config
        self.log = log_callback
        self._model: GenerativeModel | None = None
        self._generation_config: GenerationConfig | None = None
        self._generation_kwargs: Dict[str, Any] = {}
        self._configure_tesseract()
        self._setup_llm()
        self.template = Path(self.c["ai"]["prompt"]["template_file"]).read_text(encoding="utf-8")

    def _configure_tesseract(self) -> None:
        try:
            cmd = self.c.get("ocr", {}).get("tesseract", {}).get("command")
        except AttributeError:
            cmd = None
        if not cmd:
            return
        path = Path(cmd).expanduser()
        if path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(path)
        else:
            self.log("WARNING", f"Tesseract 실행 파일을 찾지 못했습니다: {path}")

    def _setup_llm(self) -> None:
        ai_conf = self.c.get("ai", {})
        provider = ai_conf.get("provider")
        if provider not in {"vertex", "vertex_ai", "gemini"}:
            self.log("WARNING", "현재는 Vertex AI Gemini만 지원합니다. provider 값을 'vertex'로 설정해주세요.")

        vertex_conf = ai_conf.get("vertex") or {}
        project_id = vertex_conf.get("project_id")
        location = vertex_conf.get("location")
        model_conf = vertex_conf.get("model") or {}
        model_name = model_conf.get("name")

        missing = [
            label
            for label, value in (
                ("project_id", project_id),
                ("location", location),
                ("model.name", model_name),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Vertex AI 설정값이 누락되었습니다: {', '.join(missing)}")

        credentials = None
        credentials_path = vertex_conf.get("credentials_path")
        if credentials_path:
            cred_path = Path(credentials_path).expanduser()
            if cred_path.exists():
                credentials = service_account.Credentials.from_service_account_file(str(cred_path))
            else:
                self.log("WARNING", f"서비스 계정 키 파일을 찾을 수 없습니다: {cred_path}")

        try:
            vertexai.init(project=project_id, location=location, credentials=credentials)
        except Exception as exc:  # pragma: no cover - defensive guard
            self.log("ERROR", f"Vertex AI 초기화에 실패했습니다: {exc}")
            raise

        self._model = GenerativeModel(model_name)
        self._generation_config = self._build_generation_config(model_conf)

    def _build_generation_config(self, model_conf: Dict[str, Any]) -> GenerationConfig:
        temperature = model_conf.get("temperature", 0.3)
        try:
            temperature_value = float(temperature)
        except (TypeError, ValueError) as exc:
            raise ValueError("temperature 값은 숫자여야 합니다") from exc

        max_tokens = (
            model_conf.get("max_output_tokens")
            or model_conf.get("max_tokens")
            or 1024
        )
        try:
            max_token_value = int(max_tokens)
        except (TypeError, ValueError) as exc:
            raise ValueError("max_output_tokens 값은 정수여야 합니다") from exc

        config_kwargs: Dict[str, Any] = {
            "temperature": temperature_value,
            "max_output_tokens": max_token_value,
        }
        top_p = model_conf.get("top_p")
        if top_p is not None:
            try:
                config_kwargs["top_p"] = float(top_p)
            except (TypeError, ValueError) as exc:
                raise ValueError("top_p 값은 숫자여야 합니다") from exc
        top_k = model_conf.get("top_k")
        if top_k is not None:
            try:
                config_kwargs["top_k"] = int(top_k)
            except (TypeError, ValueError) as exc:
                raise ValueError("top_k 값은 정수여야 합니다") from exc
        self._generation_kwargs = dict(config_kwargs)
        return GenerationConfig(**config_kwargs)

    def extract_text_tesseract(self, image_path: str) -> str:
        cfg = self.c["ocr"]["tesseract"]["config"]
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, config=cfg)
            return text.strip()
        except Exception as e:  # pragma: no cover - hardware dependency
            self.log("ERROR", f"OCR 처리 실패: {e}")
            return ""

    def create_prompt(self, product: Dict[str, Any]) -> str:
        return self.template.format(
            product_name=product.get("product_name", ""),
            brand=product.get("brand", ""),
            features=product.get("features", ""),
            review_summary=product.get("review_summary", ""),
            language=self.c["ai"]["prompt"]["language"],
        )

    def _extract_text(self, response: Any) -> str:
        text = getattr(response, "text", None)
        if text:
            return str(text)
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return ""
        first = candidates[0]
        content = getattr(first, "content", None)
        if content is None:
            return ""
        parts = getattr(content, "parts", None)
        if parts is None:
            return ""
        chunks: List[str] = []
        for part in parts:
            value = getattr(part, "text", part)
            if isinstance(value, str):
                chunks.append(value)
        return "".join(chunks)

    def call_llm(self, prompt: str) -> str:
        if not self._model or not self._generation_config:
            raise RuntimeError("Vertex AI 모델이 초기화되지 않았습니다.")
        try:
            response = self._model.generate_content(
                prompt,
                generation_config=self._generation_config,
            )
        except Exception as exc:  # pragma: no cover - network dependency
            self.log("ERROR", f"Vertex AI 호출 실패: {exc}")
            raise
        return self._extract_text(response)

    def validate_email(self, content: str) -> bool:
        try:
            start = content.find("{")
            end = content.find("}")
            meta_json = content[start : end + 1]
            meta = json.loads(meta_json)
            req = self.c["ai"]["prompt"]["schema"]["required"]
            for k in req:
                if not meta.get(k):
                    self.log("WARNING", f"필수 메타키 누락: {k}")
                    return False
            return True
        except Exception as e:
            self.log("WARNING", f"JSON 메타 파싱 실패: {e}")
            return False

    def generate_single_email(self, product: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.create_prompt(product)
        retries = self.c["ai"]["generation"]["retry_attempts"]
        for attempt in range(retries):
            out = self.call_llm(prompt)
            if self.validate_email(out):
                return {"ok": True, "raw": out}
            time.sleep(2 ** attempt)
        return {"ok": False, "error": "유효한 이메일 생성 실패"}

    def generate_batch(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.generate_single_email(p) for p in products]
