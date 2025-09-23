# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Environment Setup
```bash
# Install dependencies
python -m pip install -r requirements.txt

# Setup development environment (Windows PowerShell)
scripts/dev.ps1 -Task bootstrap
```

### Development Workflow
```bash
# Run all quality checks
scripts/dev.ps1 -Task all

# Individual tasks
scripts/dev.ps1 -Task format    # Format code with ruff and black
scripts/dev.ps1 -Task lint      # Lint with ruff and mypy
scripts/dev.ps1 -Task test      # Run pytest

# Run main application
python src/ultimate_automation_system.py

# Run pipeline CLI
python src/pipeline/cli.py run --input tests/fixtures --limit 5
python src/pipeline/segment_cli.py run-stage parse --input tests/fixtures
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m pytest tests/test_parser.py
python -m pytest tests/test_data_processor.py

# Smoke test guidelines in tests/SMOKE.md
```

## High-Level Architecture

### Core System Design
This is a **dual-mode automation system** that operates in two distinct modes:

1. **GUI Mode**: Full automation system with web scraping, OCR, and AI email generation
2. **Pipeline Mode**: Standalone data processing pipeline for HTML analysis and email composition

### Main Components

#### GUI Mode (`src/ultimate_automation_system.py`)
- **UltimateAutomationSystem**: Main GUI application with tkinter interface
- **WebAutomation**: Browser automation using PyAutoGUI and image matching
- **DataProcessor**: File organization and Excel database management
- **AIGenerator**: OCR (Tesseract) + Vertex AI integration for content generation
- **ImageMatcher**: Enhanced template matching for UI elements

#### Pipeline Mode (`src/pipeline/`)
- **cli.py**: Standalone pipeline for HTML → structured data → email composition
- **segment_cli.py**: Individual stage execution and range processing
- Stages: `parse` → `normalize` → `compose`

### Key Integration Points

#### Configuration System
- **Primary config**: `config/config.yaml` - all system settings
- **Default config**: `config/default.yaml` - baseline configuration
- **Environment override**: UAS_ prefixed env vars (e.g., `UAS_AI__TEMPERATURE=0.3`)

#### Module Dependencies
```
UltimateAutomationSystem
├── WebAutomation (pyautogui + image matching)
│   ├── ImageMatcher (OpenCV template matching)
│   ├── ErrorHandler (retry logic + checkpointing)
│   └── DataProcessor (file organization)
├── AIGenerator (OCR + Vertex AI)
└── Pipeline components (independent processing)
```

#### File Organization Workflow
DataProcessor implements the Korean business workflow:
- Downloads → `E:/업무/03_데이터_수집/YYYYMMDD/스토어명/`
- Naming: `001 - 제품명 _ 스토어명.jpg` and corresponding `.txt` files
- Excel → TXT conversion for review data
- Database tracking in Excel format

### Technology Stack

#### Core Dependencies
- **GUI**: tkinter (Windows-focused)
- **Image Processing**: OpenCV, PIL, PyAutoGUI
- **OCR**: Tesseract + EasyOCR
- **AI**: Google Cloud Vertex AI (Gemini models)
- **Data**: pandas, openpyxl for Excel handling
- **Configuration**: PyYAML

#### File Structure Patterns
```
src/
├── modules/           # Reusable business logic
├── pipeline/          # Independent processing pipeline
├── crawler/           # Web scraping utilities
├── parser/            # HTML/content parsing
├── normalize/         # Data standardization
├── email/             # Email composition
└── validate/          # Data validation
```

## Development Guidelines

### Configuration Management
- All settings externalized to `config/config.yaml`
- Use environment variables for secrets (never commit credentials)
- Provider switching supported but currently only Vertex AI implemented

### Image Template System
Required template images in `assets/img/`:
- `detail_button.png`, `fireshot_save.png`, `review_button.png`
- `analysis_start.png`, `excel_download.png`, `crawling_tool.png`
- Alternative templates supported for UI variations

### Error Handling Patterns
- **ErrorHandler** provides retry logic with exponential backoff
- Checkpoint system for recovery after failures
- Skip lists for problematic items
- Graceful degradation when components fail

### Data Processing Workflow
1. **WebAutomation**: Browser interaction and file downloads
2. **DataProcessor**: File organization and database updates
3. **AIGenerator**: OCR + LLM processing for email generation
4. Integration through payload callbacks and structured data flow

### Testing Strategy
- Unit tests in `tests/` directory
- Smoke testing checklist in `tests/SMOKE.md`
- Pipeline integration tests with fixture data
- GUI component testing through automation

### Localization Notes
- Korean language support throughout (file paths, UI text)
- UTF-8 encoding required for all files
- OCR configured for Korean + English text recognition
- Business workflow aligned with Korean e-commerce practices