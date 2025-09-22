# Smoke Test (10분)

1) 헬스체크 버튼 → 초록이어야 시작.
2) 탭에서 상세→캡처→리뷰DL 단계가 진행되며, 다운로드 완료 검증 로그 출력.
3) downloads에 파일 생성 후 storage/images|reviews/{YYYY-MM-DD}로 이동하는지 확인.
4) Vertex 온도 0.3 적용: config.yaml 수정 시 즉시 반영되는지 call_llm에서 확인.
5) 실패 시 버그팩 ZIP 생성 버튼으로 증거 묶음 생성.