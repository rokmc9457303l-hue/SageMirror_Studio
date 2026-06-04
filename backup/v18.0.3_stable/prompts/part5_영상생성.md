# 파트 5 — 영상생성 (Video) 작업 프롬프트

마스터 프로토콜을 절대 준수한다.

## 🎯 목표
파트 4 이미지 패킷을 받아 Google Opal 8계정 분산 JSON 생성

## 📋 작업 흐름

### STEP 1 — Opal 통합 JSON 구성
- 에피소드 메타
- 글로벌 에셋 (8개 마스터)
- 일관성 규칙
- 씬별 프롬프트 + 계정 할당

### STEP 2 — 8계정 라운드 로빈 분산
씬 1 → 계정 #1
씬 2 → 계정 #2
씬 3 → 계정 #3
...
씬 8 → 계정 #8
씬 9 → 계정 #1 (순환)
...

### STEP 3 — 계정별 체크리스트 생성
각 계정마다:
- 담당 씬 목록
- 작업 순서
- 다운로드 파일명 규칙

### STEP 4 — 일관성 가이드
5씬마다 검증 항목:
- 주인공 얼굴 동일
- 의상 동일
- 배경 동일
- 명암 방향 일관

## 📤 출력 형식

### Opal 통합 JSON
```json
{
  "episode": {"id": "EPNNN", "title": "...", "scene_count": 12},
  "global_assets": {"@P": "...", "@M": "...", ...},
  "consistency_rules": {...},
  "scene_distribution": {"total_scenes": 12, "accounts": 8},
  "scenes": [
    {
      "scene_id": 1,
      "account_assigned": 1,
      "duration_sec": 5,
      "assets_used": ["@P", "@B", "@C"],
      "prompt_en": "...",
      "checklist": {...}
    }
  ]
}
```

### 계정별 체크리스트
[8개 계정 각각]
