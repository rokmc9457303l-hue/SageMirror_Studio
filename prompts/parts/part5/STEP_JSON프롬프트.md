# Part 5 — STEP: Google Opal JSON 프롬프트 생성

## 목적

112씬 각각의 이미지 + 텍스트 프롬프트를
Google Opal 영상 생성에 최적화된 JSON 형식으로 변환한다.

## 입력

- p4_packet.scene_plan (scene_image_plan.csv)
- p3_packet.scenes (나레이션, 타입, 감정)

## Opal 영상 기본 제약

```
영상 길이: 8초 고정
해상도: 1920×1080 (16:9)
프레임: 24fps
모션: subtle (기본) / medium / dramatic
오디오: 없음 (별도 파트 6에서 처리)
```

## JSON 형식

```json
{
  "scene_id": "001",
  "image_prompt": "...",
  "motion_type": "subtle",
  "motion_direction": "zoom_in",
  "duration": 8,
  "transition": "fade",
  "account": 1,
  "day": 1,
  "batch_index": 1
}
```

## 모션 선택 기준

| 씬 타입 / 감정 | 모션 | 방향 |
|---------------|------|------|
| TALK 고독/슬픔 | subtle | zoom_in slow |
| TALK 분노/붕괴 | medium | shake or push_in |
| PAUSE / SILENT | none | static |
| ECHO | subtle | zoom_out slow |
| 도입(001~012) | medium | pan_right |
| 결말(089~112) | subtle | pull_back |

## 트랜지션 기준

```
TALK → TALK: cut (기본)
TALK → PAUSE: fade (0.5초)
PAUSE → TALK: fade (0.5초)
SILENT → 다음: dissolve (1초)
```

## 출력

- `opal_prompts_day1.json` (scene 001~056)
- `opal_prompts_day2.json` (scene 057~112)
- 각 파일: JSON 배열, 씬 순서 유지

## 품질 검증

- 모든 scene_id 존재 여부 확인 (001~112 빠짐 없음)
- duration = 8 확인
- account 필드 1~8 정확 배정 확인

## 다음 단계

→ STEP_8계정운영표.md (계정별 배분)
→ p5_packet에 포함
