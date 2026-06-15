# Part 6 — STEP: 나레이션 텍스트 준비

## 목적

p3_packet.narration_plan 을 TTS 또는 실제 녹음에 즉시 투입 가능한
최종 나레이션 텍스트로 정제한다.

## 입력

- p3_packet.narration_plan (씬별 속도·호흡 태그 포함 대본)
- p2_packet.narrator_profile ({{TONE}}, {{NARRATOR_STYLE}})

## 정제 기준

### 발음 정제

| 원문 | 변환 |
|------|------|
| 숫자 | 한글 읽기 형식 |
| 영문 인명 | 한글 표기 + 원문 괄호 |
| 한자 혼동 | 한글 + (한자) |
| 줄임말 | 완전 형태로 복원 |

### 호흡 최적화

- 마침표 → `[BREATH 0.5초]`
- 쉼표 → `[BREATH 0.3초]`
- 단락 구분 → `[BREATH 1초]`
- PAUSE 씬 → `[SILENCE {n}초]`

### 감정 지시어 삽입

```
[감정: 고독] [속도: SLOW] [볼륨: 70%]
당신은 혼자입니까. [BREATH 0.5초]
[감정: 상처] [속도: SLOW]
아니면, 혼자라고 느낍니까. [BREATH 1초]
```

## 보이스 기준 ({{NARRATOR_STYLE}})

```
성별: 남성
연령대: {{TONE}} 기준
음역: 중저음
속도 기본: 분당 150음절
감정 표현: 절제 — 과장 금지
강의 어투 금지: 고백·독백 형식만
```

## 출력

### 파일 1: `narration_final.txt`
```
씬번호 | 속도 | 감정 | 텍스트 (호흡 태그 포함)
001 | SLOW | 고독 | 당신은 혼자입니까. [BREATH 0.5초] ...
```

### 파일 2: `narration_meta.json`
```json
{
  "scene_id": "001",
  "speed": "SLOW",
  "emotion": "고독",
  "volume": 70,
  "text_clean": "당신은 혼자입니까. 아니면, 혼자라고 느낍니까.",
  "text_tagged": "당신은 혼자입니까. [BREATH 0.5초] 아니면, ...",
  "estimated_seconds": 7.2
}
```

## 품질 검증

- 총 TALK 씬 예상 발화 시간: 씬당 6~7.5초
- 금지 표현({{FORBIDDEN_EXPRESSIONS}}) 최종 점검
- AI 냄새 표현 제거: "물론", "그렇기 때문에", "중요한 점은"

## 다음 단계

→ STEP_BGM프롬프트.md
→ p6_packet 에 포함
