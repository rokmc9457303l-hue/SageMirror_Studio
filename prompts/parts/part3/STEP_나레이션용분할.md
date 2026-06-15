# Part 3 — STEP: 나레이션용 분할

## 목적

112씬 대본을 TTS/녹음 작업에 최적화된 나레이션 텍스트로 재가공한다.
발음 지시, 호흡 포인트, 속도 태그를 삽입한다.

## 입력

- p3_packet.scenes (scene_id, type, narration, emotion_tag)
- p2_packet.narrator_profile ({{TONE}}, {{NARRATOR_STYLE}})

## 처리 규칙

### 씬 타입별 지시

| 타입 | 나레이션 처리 |
|------|--------------|
| TALK | 원문 유지 + 속도/호흡 태그 삽입 |
| PAUSE | `[PAUSE 2초]` 또는 `[PAUSE 1초]` |
| SILENT | `[BGM ONLY — {duration}초]` |
| ECHO | `[ECHO: 속삭임 — 텍스트]` |

### 속도 태그 기준

```
[SLOW]   — 감정 고조, 고독, 상실 씬
[NORMAL] — 일반 나레이션
[FAST]   — 현실 묘사, 사례 설명
[BREATH] — 줄 끝 호흡 표기 (자연스러운 쉼)
```

### 발음 특이사항

- 한자어 혼동 단어: 한글로 표기 + `(한자)` 병기
- 외국어 인명: 발음기호 괄호 추가  
  예: `빅터 프랭클 (Viktor Frankl)`
- 숫자: 읽기 형식으로 변환  
  예: `1965년` → `천구백육십오 년`

## 출력 형식

```
[씬 001 | TALK | 감정: 고독 | SLOW]
당신은 혼자입니까. [BREATH]
아니면, 혼자라고 느낍니까. [BREATH]

[씬 002 | PAUSE]
[PAUSE 2초]

[씬 015 | ECHO | 감정: 회복]
[ECHO: 속삭임] 그 문은 아직 닫히지 않았습니다.
```

## 파일 출력

- `narration_script.txt` — 전체 TTS용 대본
- `narration_cue.json` — 씬별 메타 (timing, speed, emotion)

```json
{
  "scene_id": "001",
  "type": "TALK",
  "speed": "SLOW",
  "emotion": "고독",
  "text": "당신은 혼자입니까. 아니면, 혼자라고 느낍니까.",
  "estimated_duration": 7.5
}
```

## 품질 기준

- TALK 씬 나레이션 예상 발화 시간: 6~7.5초 (8초 영상 기준)
- SLOW 씬: 분당 120~140음절 목표
- NORMAL 씬: 분당 160~180음절 목표

## 다음 단계

→ p3_packet.narration_plan 에 저장
→ Part 6 TTS 작업에 직접 전달
