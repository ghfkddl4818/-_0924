from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pytesseract
from PIL import Image

import vertexai
from google.oauth2 import service_account
from vertexai.preview.generative_models import GenerationConfig, GenerativeModel
from pydantic import ValidationError

from .email_schema import ColdEmailMeta, REQUIRED_EMAIL_META_KEYS


class AIGenerator:
    def __init__(self, config: dict, log_callback):
        self.c = config
        self.log = log_callback
        self._model: GenerativeModel | None = None
        self._generation_config: GenerationConfig | None = None
        self._generation_kwargs: Dict[str, Any] = {}
        self._api_call_count = 0
        self._max_api_calls = self.c.get("ai", {}).get("generation", {}).get("max_api_calls", 50)
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
            with Image.open(image_path) as img:  # 메모리 누수 방지를 위한 context manager 사용
                text = pytesseract.image_to_string(img, config=cfg)
                return text.strip()
        except Exception as e:  # pragma: no cover - hardware dependency
            self.log("ERROR", f"OCR 처리 실패: {e}")
            return ""

    def _format_unique_features(self, value: Any) -> str:
        items: Iterable[str]
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, Iterable):
            items = [str(v) for v in value]
        else:
            items = [str(value)]

        cleaned = [item.strip() for item in items if str(item).strip()]
        if not cleaned:
            return ""
        return "\n".join(f"- {item}" for item in cleaned)

    def create_prompt(self, product: Dict[str, Any]) -> str:
        unique_features = self._format_unique_features(product.get("unique_features", []))
        prompt = self.template.format(
            product_name=product.get("product_name", ""),
            unique_features=unique_features,
            call_to_action=product.get("call_to_action", ""),
        )
        language = self.c.get("ai", {}).get("prompt", {}).get("language")
        if language:
            prompt += f"\n\n[LANGUAGE]\n- 출력 언어: {language}"
        return prompt

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

    def _parse_json_meta(self, content: str) -> tuple[Dict[str, Any], str]:
        start = content.find("{")
        if start == -1:
            raise ValueError("응답에서 JSON 메타 정보를 찾지 못했습니다.")
        decoder = json.JSONDecoder()
        try:
            parsed, consumed = decoder.raw_decode(content[start:])
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"JSON 메타 구문 오류: {exc.msg}") from exc
        end = start + consumed
        body = content[end:].lstrip("\n")
        if not isinstance(parsed, dict):
            raise ValueError("JSON 메타 구조가 객체 형태가 아닙니다.")
        return parsed, body

    def _format_validation_error(
        self, error: Exception | str, missing_keys: Iterable[str] | None = None
    ) -> str:
        missing = sorted({str(key) for key in (missing_keys or []) if str(key)})
        if isinstance(error, ValidationError):
            missing.extend(
                {
                    str(err["loc"][0])
                    for err in error.errors()
                    if err.get("type") == "missing"
                }
            )
            detail = "; ".join(err.get("msg", "") for err in error.errors())
        else:
            detail = str(error)
        missing = sorted(set(missing))
        guidance = "생성된 응답이 필수 메타 키와 일치하지 않습니다."
        if missing:
            guidance += f" 누락된 키: {', '.join(missing)}."
        guidance += (
            " JSON 메타가 "
            + ", ".join(REQUIRED_EMAIL_META_KEYS)
            + " 값을 모두 포함하도록 입력 데이터를 확인하거나 프롬프트를 조정한 뒤 다시 시도해주세요."
        )
        if detail:
            guidance += f" (세부: {detail})"
        return guidance

    def _request_missing_keys(
        self,
        product: Dict[str, Any],
        missing_keys: Iterable[str],
        partial_meta: Dict[str, Any],
        body: str,
    ) -> Dict[str, Any]:
        missing_list = sorted({str(key) for key in missing_keys if str(key)})
        if not missing_list:
            return {}
        self.log("INFO", f"누락된 키 보정 시도: {', '.join(missing_list)}")
        features_for_prompt = self._format_unique_features(product.get("unique_features", []))
        known_values = [
            f"- {key}: {json.dumps(partial_meta.get(key), ensure_ascii=False)}"
            for key in REQUIRED_EMAIL_META_KEYS
            if partial_meta.get(key)
        ]
        sections = [
            "이전 이메일 생성 결과에서 필수 JSON 키가 누락되었습니다.",
            f"누락된 키: {', '.join(missing_list)}",
            "초기 입력 요약:",
            f"- 제품명: {product.get('product_name', '')}",
            f"- 핵심 특징:\n{features_for_prompt}",
            f"- 원하는 행동: {product.get('call_to_action', '')}",
        ]
        if known_values:
            sections.append("현재 확보된 값:")
            sections.extend(known_values)
        if body:
            sections.append("이전 본문:")
            sections.append(body)
        sections.append("누락된 키만 포함하는 JSON 객체를 한 줄로 출력하세요.")
        repair_prompt = "\n".join(sections)
        try:
            response = self.call_llm(repair_prompt)
        except Exception:  # pragma: no cover - network dependency
            return {}
        try:
            repaired_meta, _ = self._parse_json_meta(response)
        except ValueError as exc:
            self.log("WARNING", f"보정 응답 파싱 실패: {exc}")
            return {}
        fixes = {key: repaired_meta.get(key) for key in missing_list if repaired_meta.get(key)}
        if fixes:
            self.log("INFO", f"보정 키 확보: {', '.join(fixes.keys())}")
        else:
            self.log("WARNING", "보정 응답에 필요한 키가 포함되지 않았습니다.")
        return fixes

    def call_llm(self, prompt: str) -> str:
        if self._api_call_count >= self._max_api_calls:
            raise RuntimeError(f"API 호출 한도 초과: {self._api_call_count}/{self._max_api_calls}")

        if not self._model or not self._generation_config:
            raise RuntimeError("Vertex AI 모델이 초기화되지 않았습니다.")

        self._api_call_count += 1
        self.log("INFO", f"API 호출 {self._api_call_count}/{self._max_api_calls}")

        try:
            response = self._model.generate_content(
                prompt,
                generation_config=self._generation_config,
            )
        except Exception as exc:  # pragma: no cover - network dependency
            self.log("ERROR", f"Vertex AI 호출 실패: {exc}")
            raise
        return self._extract_text(response)

    def validate_email(
        self, content: str
    ) -> tuple[
        bool,
        ColdEmailMeta | None,
        str,
        Dict[str, Any],
        set[str],
        str,
    ]:
        try:
            meta_dict, body = self._parse_json_meta(content)
        except ValueError as exc:
            message = self._format_validation_error(str(exc))
            self.log("WARNING", message)
            return False, None, "", {}, set(), message

        try:
            validated = ColdEmailMeta.model_validate(meta_dict)
        except ValidationError as exc:
            missing = {
                str(err["loc"][0])
                for err in exc.errors()
                if err.get("type") == "missing"
            }
            message = self._format_validation_error(exc, missing)
            self.log("WARNING", message)
            return False, None, body, dict(meta_dict), missing, message

        return True, validated, body, dict(meta_dict), set(), ""

    def generate_single_email(self, product: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.create_prompt(product)
        retries = self.c["ai"]["generation"]["retry_attempts"]
        repair_attempted = False
        last_error = "유효한 이메일 생성 실패"

        for attempt in range(retries):
            out = self.call_llm(prompt)
            is_valid, meta, body, partial_meta, missing_keys, message = self.validate_email(out)

            if is_valid and meta:
                serialised = json.dumps(meta.model_dump(), ensure_ascii=False)
                if body:
                    serialised += f"\n\n{body}"
                return {"ok": True, "raw": serialised, "meta": meta.model_dump(), "body": body}

            if missing_keys and not repair_attempted:
                repair_attempted = True
                fixes = self._request_missing_keys(product, missing_keys, partial_meta, body)
                if fixes:
                    partial_meta.update(fixes)
                    try:
                        repaired_meta = ColdEmailMeta.model_validate(partial_meta)
                    except ValidationError as exc:
                        message = self._format_validation_error(exc)
                    else:
                        serialised = json.dumps(repaired_meta.model_dump(), ensure_ascii=False)
                        if body:
                            serialised += f"\n\n{body}"
                        self.log("INFO", "누락된 키 보정 결과를 반환합니다.")
                        return {
                            "ok": True,
                            "raw": serialised,
                            "meta": repaired_meta.model_dump(),
                            "body": body,
                        }
                else:
                    message = self._format_validation_error(
                        "누락된 키에 대한 보정 응답을 받지 못했습니다.", missing_keys
                    )

            last_error = message or last_error
            time.sleep(2 ** attempt)

        return {"ok": False, "error": last_error}

    def generate_batch(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.generate_single_email(p) for p in products]

    def generate_cold_email_from_assets(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """OCR 텍스트와 리뷰 데이터를 기반으로 콜드메일 생성"""
        try:
            # OCR 텍스트 추출 (이미지 파일들에서)
            ocr_texts = []
            image_paths = payload.get("image_paths", [])
            for img_path in image_paths:
                if Path(img_path).exists():
                    ocr_text = self.extract_text_tesseract(img_path)
                    if ocr_text:
                        ocr_texts.append(ocr_text)

            # 리뷰 텍스트 로드
            review_texts = []
            review_files = payload.get("review_texts", [])
            for review_file in review_files:
                if Path(review_file).exists():
                    try:
                        review_content = Path(review_file).read_text(encoding="utf-8")
                        review_texts.append(review_content)
                    except Exception as exc:
                        self.log("WARNING", f"리뷰 파일 읽기 실패: {review_file}: {exc}")

            # 콜드메일 생성용 데이터 구성
            combined_ocr = "\n\n".join(ocr_texts) if ocr_texts else ""
            combined_reviews = "\n\n".join(review_texts) if review_texts else ""

            unique_features: List[str] = []
            if combined_ocr:
                unique_features.append(f"OCR 추출 정보:\n{combined_ocr}")
            if combined_reviews:
                unique_features.append(
                    f"리뷰 데이터 요약:\n{combined_reviews[:1000]}..."
                )
            if not unique_features:
                unique_features.append("제품의 차별점을 추가로 수집하지 못했습니다.")

            email_payload = {
                "product_name": payload.get("product_name", ""),
                "unique_features": unique_features,
                "call_to_action": payload.get("call_to_action")
                or "추가 논의를 위해 회신 부탁드립니다.",
            }

            # 콜드메일 생성
            result = self.generate_single_email(email_payload)

            if result.get("ok"):
                self.log("SUCCESS", f"콜드메일 생성 완료: product_id={payload.get('product_id')}")
            else:
                self.log("ERROR", f"콜드메일 생성 실패: {result.get('error', 'Unknown error')}")

            return result

        except Exception as exc:
            self.log("ERROR", f"콜드메일 생성 중 오류: {exc}")
            return {"ok": False, "error": str(exc)}
