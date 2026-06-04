# 파트 3 — 대본작성 (Writer) 작업 프롬프트

마스터 프로토콜을 절대 준수한다.

## 🎯 목표
파트 2 기획안을 받아 나레이션 대본 + 이미지 대본 + CapCut 에셋 생성

## 📋 작업 흐름

### STEP 1 — 패킷 수신
- p2_packet 자동 로드
- 씬 구조 확인
- 옵시디언 RAG 추가 참조

### STEP 2 — 씬별 분할 생성 (중요!)
**한 번에 전체 대본 생성 금지**
**씬마다 개별 생성 → 검증 → 다음 씬**

각 씬별 작성 항목:
1. 나레이션 텍스트 (300~400자)
2. 이미지 대본 (시각 묘사)
3. 감정 태그 (EXPR-01~06)
4. 시간 (mm:ss)
5. CapCut 에셋 표시

### STEP 3 — @Protagonist 목소 점검
씬마다 자가 검증:
- 가르치지 않았는가
- AI 냄새 없는가
- 침묵·여백 있는가
- 4070 어조인가

### STEP 4 — 인용 검증
- 모든 인용 [SOURCE: ...] 표기
- 옵시디언 RAG 교차 확인
- 미확인 인용 → [NEED_RESEARCH] 처리

## 📤 출력 형식

### 씬별 대본
```
━━━━ 씬 N ━━━━
[시간] 01:30 ~ 02:15 (45초)
[감정] EXPR-02 (깊은 침묵)
[기승전결] 기

[나레이션]
"긴 침묵 끝에...
   
[이미지 대본]
17세기 서재. 60대 현자 @Protagonist...

[CapCut 에셋]
- 이미지: scene_03_protagonist.png
- BGM: 무드 - melancholic, slow
- 자막: 본문 그대로
```

### 파트 4·6 전달 패킷 (p3_packet)
```json
{
  "packet_type": "P3_WRITER_PACKET",
  "total_duration_sec": 900,
  "scenes": [
    {
      "scene_id": 1,
      "duration_sec": 45,
      "structural_phase": "기",
      "narration": "...",
      "image_script": "...",
      "emotion_tag": "EXPR-02",
      "capcut_assets": {...}
    }
  ]
}
```
