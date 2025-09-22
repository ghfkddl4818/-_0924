# CHANGELOG_v3

Date: 2025-09-21

## Summary
- Restored missing **MCP/OPEN_ISSUES.md** from original template.
- Rebuilt **MCP/init_message.txt** by taking the full original content and appending v2's summary line(s) under *'v2 추가(요약)'*.
- Merged **MCP/TASKS.yaml**: kept v2 ordering/titles/status while restoring missing fields from the template (e.g., `touchpoints`, `accept`). See `diff_report.md` for the full diff of template→v2.
- Added **README_full.md** (original README) alongside v2 README to avoid loss of reference docs.
- No code files were removed; v2-only modules (`src/modules/logger.py`, `src/modules/utils.py`) are kept.

## Rationale
Goal was '누락된 부분 없이' while preserving v2 improvements. Where auto-merge was ambiguous (unstructured text like README), we included the full original as a separate file.

