# Part 8 — STEP: 전체 조립 순서표 (CSV)

## 목적

112씬 + 숏폼 5편의 조립 순서, 파일 경로, 타임코드를
CapCut JSON + 업로드 작업에 필요한 CSV로 생성한다.

## 입력

- 파일 매칭 검수 결과 (STEP_파일매칭.md 출력)
- p6_packet (bgm_cuesheet.json, narration_meta.json)
- p7_packet (shorts_plan.json)

## CSV 구조 (본편)

```
scene_id, type, image_file, video_file, audio_file, subtitle_file,
bgm_track, bgm_volume, narration_speed, emotion_tag,
start_timecode, end_timecode, transition
```

예시:
```
001, TALK, scene_001.png, video_001.mp4, audio_001.wav, subtitle_001.srt,
piano_solo_01, 20, SLOW, 고독,
00:00:00:00, 00:00:08:00, cut
```

## 타임코드 계산

```
씬당 8초 = 00:00:08:00
씬 N 시작 = (N-1) × 8초
예: 씬 013 시작 = 12 × 8 = 96초 = 00:01:36:00
```

## CapCut JSON 출력 구조

```json
{
  "project_name": "{{CHANNEL_NAME}}_EP{episode_id}",
  "resolution": "1920x1080",
  "fps": 24,
  "total_duration": 896,
  "tracks": {
    "video": [...],
    "audio_narration": [...],
    "audio_bgm": [...],
    "subtitle": [...]
  }
}
```

## 숏폼 CSV (별도)

```
short_id, selected_scenes, title, hashtags, total_duration
short_01, "001;013;037;065;089;109", "제목", "#철학;#고독", 56
```

## 파일 출력

- `assembly_order.csv` (본편 조립 순서)
- `capcut_project.json` (CapCut 자동 조립용)
- `shorts_assembly.csv` (숏폼 조립 순서)

## 다음 단계

→ STEP_검수.md (최종 검수 리포트)
