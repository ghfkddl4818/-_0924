# Ultimate Automation System v3

## Overview
Ultimate Automation System v3 orchestrates data collection, reasoning, and message generation across automation agents.
It provides a repeatable pipeline for drafting outreach, extracting structured insights, and exporting clean artifacts.
The project ships with opinionated defaults while staying configurable through environment variables and YAML profiles.

## Installation
1. Install Python 3.11 or later and ensure python and pip are on your PATH.
2. (Optional) Create a fresh virtual environment: python -m venv .venv and activate it.
3. Install dependencies: python -m pip install -r requirements.txt.
4. Run the bootstrap helpers if you plan to contribute: scripts/dev.ps1 -Task bootstrap.

### Configuration Basics
- Default settings live in config/default.yaml; copy it to config/local.yaml to customize.
- Environment variables use the UAS_ prefix with __ to denote nesting (example: UAS_AI__TEMPERATURE=0.3).
- Secret values such as API keys should be injected via environment variables or a secrets manager, never committed.

## 5-Minute Experience
1. Prepare an input payload inside examples/sample_request_basic.json.
2. Run the main entry point: python src/ultimate_automation_system.py --config config/local.yaml.
3. Watch the console for progress updates; artifacts are written under outputs/ and logs/.
4. Review the generated summary or email draft in outputs/latest_run/summary.md.
5. Adjust parameters such as the target persona or model temperature and rerun for another iteration.

## Pipeline Walkthrough
1. **Ingest** - Load raw requests, documents, or prompts from data/ and examples/.
2. **Normalize** - Clean inputs, enrich metadata, and validate schema definitions.
3. **Reason** - Invoke the configured LLM or rule engine for structured reasoning.
4. **Generate** - Produce formatted deliverables such as emails, reports, and JSON metadata.
5. **Export** - Store final assets, attach supporting JSON, and prepare download bundles.

Each stage is configurable through YAML or CLI flags, and individual agents can be enabled or disabled per use case.

## Troubleshooting
- **Dependencies fail to install**: upgrade pip with python -m pip install --upgrade pip and retry.
- **Models cannot be reached**: confirm API credentials and network access, then rerun with --verbose for detailed traces.
- **Outputs look garbled**: ensure your console supports UTF-8 and review logs/latest.log for decoding hints.
- **Configuration overrides ignored**: verify environment variable spelling and that config/local.yaml inherits from the default profile.
- **Pipeline stops early**: run scripts/dev.ps1 -Task lint to catch validation errors before execution.
