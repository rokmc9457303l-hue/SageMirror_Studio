# Part 8 — STEP: 파일 매칭 검수

## 목적

Part 4~6에서 생성된 이미지/영상/오디오/자막 파일이
112씬 전부에 존재하는지 검증하고 누락을 보고한다.

## 입력

- p4_packet (asset_master_list.md, scene_image_plan.csv)
- p5_packet (opal_prompts_day1.json, opal_prompts_day2.json)
- p6_packet (narration_meta.json, bgm_cuesheet.json)

## 파일명 규칙 (CLAUDE.md 기준)

```
이미지:   scene_001.png ~ scene_112.png
영상:     video_001.mp4 ~ video_112.mp4
오디오:   audio_001.wav ~ audio_112.wav
자막:     subtitle_001.srt ~ subtitle_112.srt
숏폼:     short_01.mp4 ~ short_05.mp4
최종:     final_episode.mp4
패킷:     final_packet.json
```

## 검수 체크리스트

### 씬별 (112씬 × 4항목)

| 씬 | 이미지 | 영상 | 오디오 | 자막 |
|----|--------|------|--------|------|
| 001 | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ |
| ... | | | | |

### 숏폼 (5편)

| 파일 | 존재 여부 |
|------|-----------|
| short_01.mp4 | ✅/❌ |
| ... | |

## 출력 형식

```json
{
  "total_scenes": 112,
  "complete_scenes": 0,
  "missing_items": [
    {
      "scene_id": "007",
      "missing": ["video", "audio"]
    }
  ],
  "shorts_status": {
    "short_01": true,
    "short_02": false
  },
  "ready_for_assembly": false
}
```

## 판단 기준

```
ready_for_assembly = true 조건:
- complete_scenes = 112
- 숏폼 5편 모두 존재
- final_packet.json 생성 완료
```

## 다음 단계

→ STEP_CSV생성.md (조립 순서표)
→ STEP_검수.md (최종 검수)
