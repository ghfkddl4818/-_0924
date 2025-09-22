from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.normalize.company import canonical_company_name, normalize_company_name
from src.normalize.contact import contact_dedup_key, normalize_email, normalize_phone
from src.parser.extract import Parser

STAGES: tuple[str, ...] = ("parse", "normalize", "compose")
_STAGE_INDEX = {stage: idx for idx, stage in enumerate(STAGES)}

SENDER_NAME = "Jamie from Ultimate Automation System"
SENDER_ROLE = "Automation Specialist"
DEFAULT_PRODUCT_VALUE = "automation co-pilot that accelerates go-to-market execution"
DEFAULT_PRODUCT_PROOF = "Teams report 30% faster launches after two weeks"


def _positive_int(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline", description="Run the offline automation pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute pipeline stages for HTML sources.")
    run_parser.add_argument(
        "--input",
        type=Path,
        default=Path("tests/fixtures"),
        help="Directory or file with HTML documents. Defaults to tests/fixtures.",
    )
    run_parser.add_argument(
        "--from",
        dest="from_stage",
        choices=STAGES,
        default="parse",
        help="First stage to include in the output.",
    )
    run_parser.add_argument(
        "--to",
        dest="to_stage",
        choices=STAGES,
        default="compose",
        help="Last stage to include in the output.",
    )
    run_parser.add_argument(
        "--limit",
        type=_positive_int,
        help="Maximum number of documents to process.",
    )
    run_parser.add_argument(
        "--language",
        default="en",
        help="Language hint for composed outreach.",
    )
    run_parser.set_defaults(handler=_handle_run, parser=run_parser)

    return parser


class PipelineRunner:
    def __init__(self, *, input_path: Path, language: str = "en") -> None:
        self._input_path = input_path
        self._language = language
        self._parser = Parser()

    def execute(self, from_stage: str, to_stage: str, limit: int | None = None) -> Iterator[dict[str, object]]:
        stage_start = _STAGE_INDEX[from_stage]
        stage_end = _STAGE_INDEX[to_stage]

        inputs = self._collect_inputs()
        processed = 0

        for html_path in inputs:
            if limit is not None and processed >= limit:
                break

            html = html_path.read_text(encoding="utf-8")
            parsed = self._parser.parse(html)
            record: dict[str, object] = {"source": str(html_path)}

            if stage_start <= _STAGE_INDEX["parse"] <= stage_end:
                record["parse"] = parsed

            if stage_end >= _STAGE_INDEX["normalize"]:
                normalized = _normalize_record(parsed)
            else:
                normalized = None
            if normalized is not None and stage_start <= _STAGE_INDEX["normalize"] <= stage_end:
                record["normalize"] = normalized

            if stage_end >= _STAGE_INDEX["compose"]:
                composed = _compose_email(normalized or _normalize_record(parsed), language=self._language)
            else:
                composed = None
            if composed is not None and stage_start <= _STAGE_INDEX["compose"] <= stage_end:
                record["compose"] = composed

            yield record
            processed += 1

    def _collect_inputs(self) -> Sequence[Path]:
        path = self._input_path
        if path.is_file():
            return [path]
        if not path.exists():
            return []
        html_files = [candidate for candidate in path.iterdir() if candidate.suffix.lower() in {".html", ".htm"} and candidate.is_file()]
        html_files.sort(key=lambda item: item.name)
        return html_files


def _normalize_record(parsed: dict[str, object]) -> dict[str, object]:
    company_raw = parsed.get("company") if isinstance(parsed, dict) else None
    services_raw = parsed.get("services") if isinstance(parsed, dict) else None
    contact_raw = parsed.get("contact") if isinstance(parsed, dict) else None
    summary_raw = parsed.get("summary") if isinstance(parsed, dict) else None
    meta_raw = parsed.get("meta") if isinstance(parsed, dict) else None

    services = [service.strip() for service in services_raw or [] if isinstance(service, str) and service.strip()]

    email_raw = contact_raw.get("email") if isinstance(contact_raw, dict) else None
    phone_raw = contact_raw.get("phone") if isinstance(contact_raw, dict) else None
    role_raw = contact_raw.get("role") if isinstance(contact_raw, dict) else None

    email = normalize_email(email_raw)
    phone = normalize_phone(phone_raw)
    first_name = _infer_first_name(email)

    company_name = normalize_company_name(company_raw) if isinstance(company_raw, str) else None
    canonical = canonical_company_name(company_raw) if isinstance(company_raw, str) else None
    summary = summary_raw.strip() if isinstance(summary_raw, str) else None

    missing = list(meta_raw.get("missing", [])) if isinstance(meta_raw, dict) else []

    insights = {
        "service_summary": _summarize_services(services),
        "service_count": len(services),
        "primary_service": services[0] if services else None,
        "missing_fields": missing,
    }

    contact = {
        "email": email,
        "phone": phone,
        "first_name": first_name,
        "role": role_raw or "Operations Lead",
        "dedupe_key": contact_dedup_key(email, phone),
    }

    company = {
        "raw": company_raw,
        "name": company_name,
        "canonical": canonical,
    }

    quality = "complete" if not missing else "needs_attention"

    return {
        "company": company,
        "contact": contact,
        "services": services,
        "summary": summary,
        "insights": insights,
        "meta": {
            "missing": missing,
            "quality": quality,
        },
    }


def _compose_email(normalized: dict[str, object], *, language: str) -> dict[str, object]:
    company_info = normalized.get("company") if isinstance(normalized, dict) else {}
    contact_info = normalized.get("contact") if isinstance(normalized, dict) else {}
    insights = normalized.get("insights") if isinstance(normalized, dict) else {}
    meta = normalized.get("meta") if isinstance(normalized, dict) else {}

    company_name = None
    if isinstance(company_info, dict):
        company_name = company_info.get("name") or company_info.get("raw")
    contact_name = None
    if isinstance(contact_info, dict):
        contact_name = contact_info.get("first_name")

    service_summary = None
    if isinstance(insights, dict):
        service_summary = insights.get("service_summary")
    missing = []
    if isinstance(meta, dict):
        missing = meta.get("missing", [])

    company_label = company_name or "your team"
    contact_label = contact_name or "there"
    service_label = service_summary or "new automation initiatives"

    if missing:
        completeness = f"We noticed a few missing fields: {', '.join(missing)}."
    else:
        completeness = "Everything we reviewed looked complete on your public profile."

    subject = f"{company_label}: automation ideas for your team"
    pitch = (
        f"Hi {contact_label},\n\n"
        f"I'm {SENDER_NAME}. We help teams like {company_label} deliver {DEFAULT_PRODUCT_VALUE}.\n"
        f"Your focus on {service_label} stood out, and it lines up with the workflows we ship with ready-to-run playbooks.\n"
        f"{DEFAULT_PRODUCT_PROOF}. {completeness}\n"
        f"Would it be a bad idea to set up a 20 minute call next week? I'm happy to share a pilot plan tailored to {company_label}.\n\n"
        "Best,\n"
        f"{SENDER_NAME}\n"
        f"{SENDER_ROLE}"
    )

    return {
        "meta": {
            "subject": subject,
            "cta": "Schedule a discovery call",
            "language": language,
            "tone": "warm",
        },
        "body": pitch,
        "insights": {
            "service_summary": service_label,
            "missing_fields": missing,
        },
    }


def _infer_first_name(email: str | None) -> str | None:
    if not email:
        return None
    local = email.split("@", 1)[0]
    simplified = re.sub(r"[^a-zA-Z]+", " ", local)
    tokens = [token for token in simplified.split() if token]
    if not tokens:
        return None
    candidate = tokens[0].title()
    if candidate.lower() in {"info", "sales", "team", "contact", "support", "hello"}:
        return None
    return candidate


def _summarize_services(services: Sequence[str]) -> str:
    if not services:
        return "new automation initiatives"
    if len(services) == 1:
        return services[0]
    if len(services) == 2:
        return " and ".join(services)
    head = ", ".join(services[:-1])
    return f"{head}, and {services[-1]}"


def _handle_run(args: argparse.Namespace) -> int:
    parser: argparse.ArgumentParser = args.parser
    from_stage = args.from_stage
    to_stage = args.to_stage

    if _STAGE_INDEX[from_stage] > _STAGE_INDEX[to_stage]:
        parser.error("--from stage must not come after --to stage")

    input_path = args.input.expanduser().resolve()
    runner = PipelineRunner(input_path=input_path, language=args.language)

    emitted = 0
    for record in runner.execute(from_stage, to_stage, limit=args.limit):
        print(json.dumps(record, ensure_ascii=False))
        emitted += 1

    if emitted == 0:
        print(f"No HTML inputs found at {input_path}", file=sys.stderr)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
