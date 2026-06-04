# 파트 4 — 이미지생성 (Image) 작업 프롬프트

마스터 프로토콜을 절대 준수한다.

## 🎯 목표
파트 3 이미지 대본을 받아 Auto Flow + Nano Banana 2 호환 프롬프트 생성

## 📋 작업 흐름

### STEP 1 — 마스터 에셋 8장 프롬프트
필수 마스터 이미지:
1. @P (A_Protagonist) - 60대 현자
2. @M (B_Mirror) - 거울
3. @A (C_MirrorAvatar) - 거울 속 아바타
4. @B (D_Study_Background) - 17세기 서재
5. @C (E_Candle) - 촛불
6. @K (F_Book) - 책
7. @W (G_WindowLight) - 창문 빛
8. @R (H_RembrandtLight) - 명암 레이어

### STEP 2 — 씬별 프롬프트 생성
각 씬마다:
- 한국어 프롬프트
- 영어 프롬프트 (Auto Flow용)
- 사용 에셋 명시 (@P @B @C 등)
- 카메라/조명/구도 지시

### STEP 3 — 일관성 규칙 명시
모든 프롬프트 공통:
- Rembrandt chiaroscuro
- 17세기 유럽 서재
- burgundy·gold·deep brown 팔레트
- 단일 광원 (촛불/창)

## 📤 출력 형식

### 마스터 에셋 프롬프트 (8개)
[각 마스터별 한/영 프롬프트]

### 씬별 프롬프트
```
━━━━ 씬 N 이미지 ━━━━
[사용 에셋] @P @B @C

[프롬프트 KR]
17세기 서재에서 60대 현자 @P 가 의자에 앉아...

[프롬프트 EN]
A 60-year-old sage @P sits in a 17th-century study...

[일관성 체크]
✓ Rembrandt 명암
✓ 색감 팔레트
✓ 캐릭터 일관성
```

### 파트 5 전달 패킷 (p4_autoflow_package)
```json
{
  "packet_type": "P4_IMAGE_PACKET",
  "master_assets": [...],
  "scene_prompts": [...],
  "consistency_rules": {...},
  "autoflow_ready": true
}
```
