# 출처 표기 표준

## 형식

```
[SOURCE: youtube_comment_id_xxx]       # 유튜브 댓글
[SOURCE: schema_id_SRC_xxx]            # 옵시디언 스키마
[SOURCE: tavily_url_https://...]       # 웹검색 결과
[SOURCE: book_제목_pXXX]              # 도서 인용
[SOURCE: user_input]                   # 사용자 직접 입력
[INFERENCE: 추론 근거 명시]            # AI 추론
[ESTIMATE]                             # 추정치 (근거 미상)
[NEED_VERIFY]                          # 검증 필요
```

## 규칙

1. 모든 수치·통계에는 [SOURCE:] 필수
2. 모든 인용구에는 [SOURCE:] 필수
3. 출처 미상 → [ESTIMATE] 또는 삭제
4. Critic 검사 시 [NEED_VERIFY] 있으면 자동 FAIL
5. [SOURCE:] ≥ 3개 있어야 Critic 통과
