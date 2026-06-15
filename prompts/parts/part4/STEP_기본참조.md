# Part 4 — STEP: 기본 참조 에셋 (A1~A15)

## 목적

모든 영상에서 반복 사용하는 15개 기준 에셋을 정의하고 생성 프롬프트를 확정한다.

## 입력

- 채널 프로필: {{VISUAL_STYLE}}, {{COLOR_PALETTE}}, {{CORE_SYMBOLS}}
- p2_packet.persona (화자 외형 묘사)

## 에셋 목록

### A1~A4: @Protagonist (화자)

| ID | 앵글 | 표정 | 조명 |
|----|------|------|------|
| A1 | 정면 클로즈업 | 고요 | 촛불 측광 |
| A2 | 측면 3/4 | 사색 | 창문 역광 |
| A3 | 클로즈업 눈 | 무표정 | 저조도 |
| A4 | 전신 원거리 | 고독 | 실루엣 |

### A5~A8: 공간

| ID | 대상 | 분위기 |
|----|------|--------|
| A5 | 17세기 서재 전경 | 먼지·촛불·고서 |
| A6 | 서재 구석 의자 | 낡음·따뜻함 |
| A7 | 창문 + 빛줄기 | 새벽·안개 |
| A8 | 촛불 클로즈업 | 흔들림·고요 |

### A9: 거울

| ID | 대상 | 특징 |
|----|------|------|
| A9 | 전신 거울 | 낡은 금테·반사·아스라함 |

### A10~A15: 거울 속 아바타 (6감정)

| ID | 감정 | 시각 표현 |
|----|------|-----------|
| A10 | 슬픔 | 눈물·고개 숙임 |
| A11 | 고독 | 허공 응시·빈 눈 |
| A12 | 분노 | 입술 굳음·눈썹 수축 |
| A13 | 체념 | 눈 감음·축 늘어짐 |
| A14 | 깨달음 | 눈 열림·빛 반사 |
| A15 | 회복 | 작은 미소·조용한 숨 |

## 생성 프롬프트 기본 구조

```
[스타일] {{VISUAL_STYLE}}, cinematic, 35mm film grain, shallow depth of field
[색채] {{COLOR_PALETTE}}, desaturated warm tones, amber shadows
[화질] 8K, hyperrealistic, masterpiece
[금지] text, watermark, logo, anime, cartoon, bright colors
```

## 출력

- `asset_master_list.md` (전체 프롬프트 목록)
- `asset_mapping.json` (에셋 ID → 씬 매핑 준비)

## 다음 단계

→ STEP_파생참조.md (감정 파생 에셋)
→ STEP_본편장면.md (112씬 매핑)
