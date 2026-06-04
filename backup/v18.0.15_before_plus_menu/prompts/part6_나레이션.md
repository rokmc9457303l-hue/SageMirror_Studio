# 파트 6 — 나레이션·배경음악 (Voice) 작업 프롬프트

마스터 프로토콜을 절대 준수한다.

## 🎯 목표
파트 3 대본을 받아 TTS 호환 포맷 + BGM 무드 매칭

## 📋 작업 흐름

### STEP 1 — TTS 감정 태그 자동 삽입
EXPR-01 평온
EXPR-02 깊은 침묵
EXPR-03 슬픔
EXPR-04 통찰
EXPR-05 회복
EXPR-06 희망

### STEP 2 — 씬별 BGM 무드 매칭
- 기 씬: melancholic, slow, deep
- 승 씬: contemplative, building
- 전 씬: hopeful turn, lifting
- 결 씬: serene, warm, light

### STEP 3 — 무료 BGM 소스 추천
- YouTube Audio Library
- Pixabay Music
- 키워드 + 검색 URL

## 📤 출력 형식

### TTS 입력 텍스트
```
[EXPR-02]
긴 침묵 끝에 그는 생각했다...
(3초 침묵)
이것이 정말 내가 원했던 삶인가...
[EXPR-04]
```

### BGM 매칭표
```
씬 1 | melancholic_slow | "ambient melancholy piano"
씬 2 | contemplative | "thoughtful strings minimal"
...
```

### 파트 7 전달 패킷 (p6_audio_package)
[TTS 입력 + BGM 매핑]
