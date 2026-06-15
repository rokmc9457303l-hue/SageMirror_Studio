# Part 7 — STEP: 숏폼 제목 생성

## 목적

숏폼 5편 각각의 제목, 설명란 첫 줄, 해시태그를 확정한다.

## 입력

- shorts_plan.json (5편 계획)
- p2_packet.title_candidates (본편 제목 후보)
- p1_packet.comment_insights (댓글 감정 패턴)

## 숏폼 제목 공식

```
공식 1: "[감정 한 단어]이라면 반드시 보세요"
공식 2: "왜 [현상]인가 — [철학/성경 인물] 이 대답했다"
공식 3: "[숫자]년을 [상황]한 사람이 말하는 것"
공식 4: "이 한 줄이 제 삶을 바꿨습니다"
공식 5: "[감정] 느끼는 당신에게"
```

## 제목 제약

- 최대 30자 (유튜브 숏폼 검색 최적화)
- {{FORBIDDEN_EXPRESSIONS}} 포함 금지
- 클릭베이트 금지: 과장·충격 어조 금지
- AI 냄새 어투 금지: "오늘", "함께", "알아보겠습니다"

## 설명란 첫 줄

```
숏폼 설명란 첫 3줄:
1줄: 핵심 감정 질문 (15자 이내)
2줄: 본편 유도 문구 ("전편 → [링크]")
3줄: 채널 구독 유도
```

## 해시태그

```
필수 (3개):
#철학 #위로 #{{CHANNEL_NAME}}

선택 (5~7개):
감정 키워드 태그 (댓글 comment_insights 기반)
금지: #힐링 #동기부여 #자기계발 (타겟 불일치)
```

## 출력

```json
{
  "short_id": "short_01",
  "title": "고독이라면 반드시 보세요",
  "title_formula": "공식 1",
  "description_line1": "혼자라는 것이 죄인가요?",
  "description_line2": "전편 영상 → [링크]",
  "hashtags": ["#철학", "#고독", "#위로", "#현자의거울"]
}
```

## p7_packet 구조

```json
{
  "part": 7,
  "shorts_plan": "shorts_plan.json",
  "shorts_narration": "shorts_narration.txt",
  "shorts_titles": [
    { "short_id": "short_01", "title": "...", "hashtags": [] },
    ...
  ],
  "next_part": 8
}
```

## 다음 단계

→ p7_packet → Part 8 최종완성
