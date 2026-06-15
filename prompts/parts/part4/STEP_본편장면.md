# Part 4 — STEP: 본편 장면 이미지 계획

## 목적

112씬 각각에 사용할 에셋(기본/파생)을 확정하고
새로 생성이 필요한 씬별 프롬프트를 작성한다.

## 입력

- p3_packet.scenes (112씬 타입/감정/나레이션)
- asset_master_list.md (A+B 시리즈)

## 씬-에셋 매핑 규칙

| 씬 타입 | 기본 에셋 | 파생 선택 기준 |
|---------|-----------|----------------|
| TALK | 화자(A1~A4) + 공간(A5~A8) 조합 | 감정 태그로 파생 선택 |
| PAUSE | 공간 단독 (A5, A6, A7) | 저채도·흐림 처리 |
| SILENT | A8 촛불 or 빈 공간 | 최소 오브젝트 |
| ECHO | 거울(A9) + 아바타(A10~A15) | 감정 매칭 |

## 매핑 출력 형식

```json
{
  "scene_id": "001",
  "type": "TALK",
  "emotion": "고독",
  "asset_id": "A1",
  "variant": "B1",
  "custom_prompt": "",
  "generation_needed": false
}
```

## 신규 생성 판단

```
generation_needed = true 조건:
- 기존 에셋으로 감정 재현 불가
- 씬 나레이션 특수 배경 필요 (예: 병원, 묘지)
- 화자 동작 변화 (앉음 → 걸음)
```

## 신규 씬 프롬프트 작성

기본 스타일 + 씬 특이사항 추가:
```
[기본] {{VISUAL_STYLE}}, {{COLOR_PALETTE}}, cinematic, 35mm grain
[추가] {씬 나레이션 핵심 오브젝트}, {감정 키워드}, {조명 변화}
```

## 출력 파일

- `scene_image_plan.csv` (112행: scene_id, asset_id, variant, custom_prompt, generation_needed)
- `auto_flow_batch_prompts.txt` (신규 생성 필요 씬 프롬프트만)
- `retry_image_list.md` (초기값 = 빈 목록, 실패 시 추가)

## p4_packet 구조

```json
{
  "part": 4,
  "asset_master": "asset_master_list.md",
  "scene_plan": "scene_image_plan.csv",
  "batch_prompts": "auto_flow_batch_prompts.txt",
  "retry_list": "retry_image_list.md",
  "total_scenes": 112,
  "generation_needed_count": 0,
  "next_part": 5
}
```

## 다음 단계

→ p4_packet → Part 5 영상제작
