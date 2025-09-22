"""Command-line helpers to run individual pipeline stages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.cli import STAGES, PipelineRunner


StageName = str


def _stage_bounds(stage: StageName) -> tuple[str, str, str]:
    if stage == "parse":
        return ("parse", "parse", "parse")
    if stage == "normalize":
        return ("parse", "normalize", "normalize")
    if stage == "compose":
        return ("parse", "compose", "compose")
    raise ValueError(f"Unknown stage: {stage}")


def run_stage(
    stage: StageName,
    *,
    input_path: Path,
    limit: int | None,
    language: str,
    stream: TextIO,
) -> int:
    from_stage, to_stage, key = _stage_bounds(stage)
    runner = PipelineRunner(input_path=input_path, language=language)
    emitted = 0
    for record in runner.execute(from_stage, to_stage, limit=limit):
        payload = {"source": record.get("source"), stage: record.get(key)}
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        emitted += 1
    return emitted


def run_range(
    *,
    from_stage: StageName,
    to_stage: StageName,
    input_path: Path,
    limit: int | None,
    language: str,
    stream: TextIO,
) -> int:
    runner = PipelineRunner(input_path=input_path, language=language)
    emitted = 0
    for record in runner.execute(from_stage, to_stage, limit=limit):
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        emitted += 1
    return emitted


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "tests" / "fixtures",
        help="Directory or file with HTML documents. Defaults to tests/fixtures.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of documents to process.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language hint for composed output.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipeline-segment",
        description="Run individual or ranged pipeline stages.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for stage in ("parse", "normalize", "compose"):
        stage_parser = subparsers.add_parser(stage, help=f"Run only the {stage} stage")
        _common_options(stage_parser)

    range_parser = subparsers.add_parser(
        "range",
        help="Run a custom range of stages (e.g. --from parse --to compose)",
    )
    _common_options(range_parser)
    range_parser.add_argument("--from", dest="from_stage", choices=STAGES, required=True)
    range_parser.add_argument("--to", dest="to_stage", choices=STAGES, required=True)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    stream: TextIO = sys.stdout

    if args.command in {"parse", "normalize", "compose"}:
        run_stage(
            args.command,
            input_path=args.input,
            limit=args.limit,
            language=args.language,
            stream=stream,
        )
        return 0

    run_range(
        from_stage=args.from_stage,
        to_stage=args.to_stage,
        input_path=args.input,
        limit=args.limit,
        language=args.language,
        stream=stream,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

