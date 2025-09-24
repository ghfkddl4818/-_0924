# Ultimate Automation System v3

## 개요
Ultimate Automation System v3은 다중 에이전트 기반 자동화 파이프라인을 구축하기 위한 플랫폼입니다.
데이터 수집, 전처리, 추론, 생성 과정을 모듈화하여 반복 가능한 업무 자동화를 지원합니다.
환경 변수와 YAML 설정을 통해 시나리오별 세부 튜닝이 가능합니다.

## 설치
1. Python 3.11 이상을 설치하고 python, pip 실행 파일이 PATH에 포함되어 있는지 확인하세요.
2. (선택) python -m venv .venv로 가상 환경을 만들고 활성화하세요.
3. 의존성 설치: python -m pip install -r requirements.txt.
4. 기여자 작업을 준비하려면 scripts/dev.ps1 -Task bootstrap을 실행하세요.

### 구성 기본
- 기본 설정은 config/default.yaml에 있으며, 필요한 키만 선택해 config/local.yaml에 덮어쓰세요.
- config/local.yaml.example과 .env.example을 복사하면 로컬 오버라이드를 빠르게 작성할 수 있습니다.
- 환경 변수는 UAS_ 접두사와 __ 구분자를 사용합니다. 예: UAS_AI__TEMPERATURE=0.3.
- API 키와 같은 비밀 값은 환경 변수나 시크릿 매니저로 주입하고 저장소에 커밋하지 말아주세요.

### 설정 계층 (default→local→env→UI)
1. **default**: 저장소에 포함된 config/default.yaml이 기본값을 제공합니다.
2. **local**: config/local.yaml(존재할 경우)이 default 값을 덮어씁니다. 예시는 config/local.yaml.example을 참고하세요.
3. **env**: .env 또는 시스템 환경 변수(TESSERACT_CMD, GOOGLE_APPLICATION_CREDENTIALS, VERTEX_CREDENTIALS, UAS_*)가 YAML 값을 재정의합니다.
4. **UI**: 실행 중 GUI에서 변경한 값은 메모리에만 적용되며 종료 시 초기화됩니다.

## 5분 체험
1. examples/sample_request_basic.json 파일을 열어 요청 페이로드를 준비하세요.
2. 메인 엔트리 포인트 실행: python src/ultimate_automation_system.py --config config/local.yaml.
3. 콘솔 로깅으로 진행 상황을 확인하고 결과 아티팩트는 outputs/, logs/ 디렉토리에 생성됩니다.
4. outputs/latest_run/summary.md에서 생성된 요약이나 이메일 초안을 검토하세요.
5. 타깃 페르소나, 모델 온도 등 파라미터를 조정한 뒤 다시 실행해 차이를 확인하세요.

## 파이프라인 흐름
1. **수집** - data/, examples/에서 원본 요청과 문서를 블로와입니다.
2. **정규화** - 입력을 정제하고 메타데이터를 보강하며 스키마 유효성을 검사합니다.
3. **추론** - 설정된 LLM 또는 규칙 에이전트를 호출하여 구조화된 결론을 도출합니다.
4. **생성** - 이메일, 리포트, JSON 메타데이터 등 형식화된 결과물을 작성합니다.
5. **배포** - 최종 산출물을 저장하고 관련 JSON을 채낼며 다운로드 버드를 준비합니다.

각 단계는 YAML 설정과 CLI 플래그로 제어할 수 있으며, 시나리오에 따라 개별 에이전트를 켜거나 끄어 사용할 수 있습니다.

## 트러블슈팅
- **의존성 설치 실패**: python -m pip install --upgrade pip으로 pip를 업그레이드한 뒤 다시 시도하세요.
- **모델 연결 실패**: API 자격 증명과 네트워크 연결을 확인하고 --verbose 옵션으로 재실행하여 상세 로그를 확보하세요.
- **출력 인코딩 문제**: UTF-8을 지원하는 터미널인지 확인하고 logs/latest.log에서 디코딩 힌트를 확인하세요.
- **환경 설정이 적용되지 않음**: .env 파일이 로드되었는지, config/local.yaml이 기본 프로필을 상속하는지 검토하세요.
- **파이프라인 중단**: 실행 전 scripts/dev.ps1 -Task lint를 통해 검증 오류를 사전에 발견하세요.

## OS별 주의사항
- **Windows**: Tesseract 경로에 공백이 포함되면 환경 변수 TESSERACT_CMD에 전체 경로를 입력하고 따옴표는 제거하세요. GOOGLE_APPLICATION_CREDENTIALS에는 `C:/Users/you/service-account.json`처럼 정규화된 경로를 사용하세요.
- **macOS**: `brew install tesseract`로 설치한 후 `/opt/homebrew/bin`이 PATH에 포함되었는지 확인하고 필요 시 .env에 TESSERACT_CMD와 GOOGLE_APPLICATION_CREDENTIALS를 명시하세요.
- **Linux**: 패키지 관리자(`apt install tesseract-ocr` 등)로 설치 후 서비스 계정 키 파일 권한을 `chmod 600`으로 제한해 누출을 방지하세요. systemd 서비스에 등록하는 경우 EnvironmentFile 옵션으로 .env를 로드하세요.
