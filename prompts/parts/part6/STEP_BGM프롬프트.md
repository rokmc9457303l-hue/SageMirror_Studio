# Part 6 — STEP: BGM 큐시트

## 목적

112씬 전체에 BGM 레이어를 배정하고
각 구간별 음악 분위기/악기 편성을 확정한다.

## 입력

- p3_packet.scenes (씬 타입, 감정, 구간)
- p2_packet.emotion_curve (7단계 감정 곡선)

## 구간별 BGM 방향

| 구간 | 씬 | 감정 단계 | BGM | 악기 |
|------|----|-----------|-----|------|
| 도입 | 001~012 | 고독 | 잔잔한 피아노 솔로 | 피아노 |
| 상처 분석 | 013~036 | 상처·붕괴 | 첼로 + 피아노 | 현악 2중주 |
| 철학적 전환 | 037~064 | 붕괴·직면 | 낮은 스트링 | 현악 앙상블 |
| 거울 직면 | 065~088 | 직면·통찰 | 첼로 솔로 | 첼로 |
| 회복·여운 | 089~112 | 여운·회복 | 오르간/피아노 페이드 | 오르간+피아노 |

## 씬 타입별 볼륨

```
TALK:   BGM 15~25% (나레이션 우선)
PAUSE:  BGM 40~60% (감정 공간)
SILENT: BGM 80~100% 또는 완전 무음
ECHO:   BGM 20% + reverb 처리
```

## BGM 큐시트 출력 형식

```json
{
  "scene_id": "001",
  "bgm_track": "piano_solo_ambient_01",
  "bgm_volume": 20,
  "bgm_fade_in": 1.0,
  "bgm_fade_out": 0,
  "notes": "피아노 솔로, 느린 템포, C장조"
}
```

## 파일 출력

- `bgm_cuesheet.json` (112씬 전체 BGM 배정)
- `bgm_tracklist.md` (트랙별 분위기·사용 구간 요약)

## 무료 BGM 소스 원칙

```
우선순위:
1. YouTube Audio Library (저작권 무료)
2. Pixabay Music (CC0)
3. Free Music Archive (CC BY)
금지: 저작권 불명 트랙 사용 → [SOURCE: bgm_url] 반드시 기록
```

## p6_packet 구조

```json
{
  "part": 6,
  "narration_script": "narration_final.txt",
  "narration_meta": "narration_meta.json",
  "bgm_cuesheet": "bgm_cuesheet.json",
  "bgm_tracklist": "bgm_tracklist.md",
  "total_scenes": 112,
  "next_part": 7
}
```

## 다음 단계

→ p6_packet → Part 7 편집연결
