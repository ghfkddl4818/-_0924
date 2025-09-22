# Ultimate Automation System v2.0 (Scaffold)

## 1) 폴더 구조
- `docs/PRD.md` : 설계도(완전본)
- `docs/design_snapshot.md` : /init 핸드오프용 10줄 요약
- `MCP/TASKS.yaml` : 테스크 상태표(1~15)
- `config/config.yaml` : 모든 설정(결정 반영됨)
- `assets/templates/cold_email_prompt.txt` : 콜드메일 프롬프트
- `src/` : 코드가 생성될 위치(현재 스텁)
- `snapshots/` `runs/` : 실행 스냅샷/버그팩 저장 위치

## 2) VSCode + 코덱스 시작 (/init)
- `MCP/init_message.txt` 내용을 코덱스에 붙여넣고 시작하세요.
- 첫 작업: MCP-01 → 헬스체크 & 2단 진행 UI.

## 3) 실행(예정)
- Windows: `python -m pip install -r requirements.txt`
- 이후 `python src/ultimate_automation_system.py` (MCP-01 이후)

## 4) 설정 포인트(결정 반영)
- LLM: Vertex(Gemini) + `temperature=0.3`
- 출력: JSON meta + email_body (검증 = JSON 키 검사)
- 체크포인트: 1개마다 저장
- 정리: JPG/JPEG/PNG & XLSX, download_folder 단일화
- 탭: 처리 후 닫기 `close_after_process: true`

## 5) 이미지 템플릿
- `assets/img/`에 버튼/저장/다운로드 이미지 캡처를 넣으세요.
- 언어/버전별 대체 이미지를 추가해 두면 안전합니다.

## 6) 버그팩 ZIP
- MCP-01에서 실패 시 ZIP(스크린샷+최근로그+config+checkpoint)을 만들도록 구현합니다.