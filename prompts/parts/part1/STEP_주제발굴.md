# Part 1 — STEP: 주제 발굴

## 주제 후보 생성 기준

댓글 분석 + RAG 자료 기반으로 {{CHANNEL_NAME}} 채널 적합 주제 10개:

각 주제에 포함:
1. 제목 (감정 자극 + {{TARGET_AUDIENCE}} 어필)
2. 핵심 주제 (한 문장)
3. 추천 사유 (댓글 근거 포함)
4. 핵심 키워드 (5개)
5. 시청자 예상 반응
6. 시청자 예상 효과

## 필터

- {{TARGET_AUDIENCE}}이 공감할 수 있는가
- 댓글 근거가 있는가 ([SOURCE: comment_id_xxx])
- {{TYPICAL_CATEGORIES}} 범위 내인가
- {{FORBIDDEN_EXPRESSIONS}} 포함 금지
- 이전 영상과 중복 금지

## 출력

10개 이상 주제, 각 [SOURCE: ...] 태그 필수
