# Design Snapshot (10 lines)

1) 목적: 고객사 URL → 웹 수집(이미지/리뷰) → 정리(DB/폴더) → Vertex(Gemini)로 콜드메일 생성까지 원클릭 E2E.
2) 설정: 모든 값은 config/config.yaml로 외부화(경로/확장자/LLM/GUI/에러/체크포인트).
3) 대기 금지: sleep 대신 **검증기**로 완료 판단(다운로드=임시확장자 소멸+파일열기OK, UI=매칭+상태전환).
4) 체크포인트: **1개마다 저장**, 중단 시 이어서 재개.
5) 정리: download_folder 단일화 + 이미지 **jpg/jpeg/png**, 리뷰 **xlsx**.
6) LLM 출력: **JSON meta + email_body**. 검증은 **JSON 키 존재**만.
7) 런타임 LLM: 현재 **Vertex(Gemini, temperature=0.3)**. Claude 분기는 후속.
8) GUI: 전체/스텝 진행률 + 상태/카운트/ETA. 실패 시 **버그팩 ZIP** 버튼.
9) 브릿지: client_discovery/results/output.csv → {company_name, product_name, url, contact} 필수.
10) 테스트: 싱글런/스텝런 모드, 오프라인 하네스(이미지/정리/DB)로 80% 사전 검출.