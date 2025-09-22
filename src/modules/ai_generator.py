
from pathlib import Path
import json, time
from typing import Dict, List, Optional

import google.generativeai as genai
import pytesseract
from PIL import Image

class AIGenerator:
    def __init__(self, config: dict, log_callback):
        self.c = config; self.log = log_callback
        self._setup_llm()
        self.template = Path(self.c["ai"]["prompt"]["template_file"]).read_text(encoding="utf-8")

    def _setup_llm(self):
        if self.c["ai"]["provider"] != "gemini":
            # 현재 빌드는 Vertex(Gemini)만 활성
            self.log("WARNING", "현재 빌드는 Vertex(Gemini)만 활성. provider를 gemini로 유지하세요.")
        genai.configure(api_key=self.c["ai"].get("api_key",""))
        self.model = genai.GenerativeModel(self.c["ai"]["models"]["gemini"]["model"])

    def extract_text_tesseract(self, image_path: str) -> str:
        cfg = self.c["ocr"]["tesseract"]["config"]
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, config=cfg)
            return text.strip()
        except Exception as e:
            self.log("ERROR", f"OCR 실패: {e}")
            return ""

    def create_prompt(self, product: Dict) -> str:
        # 템플릿의 {fields} 치환
        return self.template.format(
            product_name = product.get("product_name",""),
            brand = product.get("brand",""),
            features = product.get("features",""),
            review_summary = product.get("review_summary",""),
            language = self.c["ai"]["prompt"]["language"]
        )

    def call_llm(self, prompt: str) -> str:
        genconf = genai.GenerationConfig(
            temperature=self.c["ai"]["models"]["gemini"]["temperature"],
            max_output_tokens=self.c["ai"]["models"]["gemini"]["max_tokens"]
        )
        resp = self.model.generate_content(prompt, generation_config=genconf)
        return resp.text or ""

    def validate_email(self, content: str) -> bool:
        # JSON meta + 본문 구조 검사
        parts = content.strip().split("\n", 1)
        # 좀 더 유연하게: JSON 블록을 찾아 파싱
        try:
            # find first {...}
            start = content.find("{"); end = content.find("}")
            meta_json = content[start:end+1]
            meta = json.loads(meta_json)
            req = self.c["ai"]["prompt"]["schema"]["required"]
            for k in req:
                if not meta.get(k):
                    self.log("WARNING", f"메타 키 누락: {k}")
                    return False
            return True
        except Exception as e:
            self.log("WARNING", f"JSON 메타 파싱 실패: {e}")
            return False

    def generate_single_email(self, product: Dict) -> Dict:
        prompt = self.create_prompt(product)
        retries = self.c["ai"]["generation"]["retry_attempts"]
        for attempt in range(retries):
            out = self.call_llm(prompt)
            if self.validate_email(out):
                return {"ok": True, "raw": out}
            time.sleep(2 ** attempt)
        return {"ok": False, "error": "유효한 이메일 생성 실패"}

    def generate_batch(self, products: List[Dict]) -> List[Dict]:
        results = []
        for p in products:
            results.append(self.generate_single_email(p))
        return results
