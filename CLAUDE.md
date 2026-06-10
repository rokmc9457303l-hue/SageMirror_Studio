# 현자의 거울 스튜디오 v18 — CLAUDE.md

> Claude Code 새 세션 시 이 파일을 자동 참조한다.
> 모든 작업 전 이 문서를 우선 확인한다.

---

## 1. 절대 작업 규칙

```
1. 에러/문제 발생 시 → 코드 정밀진단 → 원인확정 → 수정
2. API 직접 호출 테스트 금지 (쿼터 소모)
3. 코드 읽기/분석만으로 진단
4. 실제 테스트는 현자가 앱에서 직접
5. 모든 수정: git tag backup → 새 브랜치 → 복사본에서만 → py_compile → 현자 확인 → push
6. 덮어쓰기 절대 금지
7. 사소한 수정도 위 규칙 100% 준수
8. 추측 금지, 토큰 낭비 금지
```

---

## 2. 현재 상태

```
버전: v18.0.24
GitHub: v18-studio 브랜치
경로: C:\SageMirror_Studio_v18\
포트: 8506
Python: 3.14
모델: Gemma 4 e2b (로컬), Gemini 2.0 Flash (원격)
```

### 핵심 수정 이력
- think:False (Gemma thinking 비활성화)
- max_tokens: 512 → 8192
- 위젯 key 저장 제외 (sb_, req_, btn_, refresh_, show_, display_)
- bool 타입 저장 제외 (버튼 상태 영구 차단)
- secrets.toml API 키 자동 로드
- Gemini SDK 신버전(google.genai) 적용

---

## 3. 콘텐츠 정체성

```
채널명: 현자의 거울 (@Ethan Cinematic Video)
타겟: 한국 40~70대 (4070)
영상 분량: 약 15분 (112씬 × 8초)
숏폼: 60초
```

### @Protagonist 화자
```
- 60대 중후반 서양 철학을 체화한 현자
- 낮고 조용한 중저음
- 가르치지 않음
- 쉽게 위로하지 않음
- 함께 바라봄
```

### 핵심 감정
```
고독, 후회, 상실, 공허
인간관계 상처, 가족 단절
의미 상실, 정체성 상실, 은퇴 후 공허
```

### 지식 조합
```
성경 / 쇼펜하우어 / 빅터 프랭클 / 칼 융
몽테뉴 / 스토아 / 다크심리학 / 명언
시청자 실제 댓글 / 역사적 사실
```

### 금지 표현
```
힘내세요 / 응원합니다 / 함께 나아가요
긍정적으로 / 할 수 있어요 / 포기하지 마세요
요약하자면 / 결론적으로 / 도움이 되었기를
자기계발 강사 말투 / 1020 감성 / 밈 표현
```

---

## 4. 전체 8파트 구조

### Part 1 — 자료수집 (Librarian)

**상단:** RAG 자료 상태 카드 (총 자료 수, 채널/시스템 자료, 범용 카테고리, 보완 요청)

**하단 6개 탭:**
1. **벤치마킹** — 채널 6개 항목 분석
2. **주제 추천** — 3대 소스 결합
3. **자료조사** — 점수화 평가
4. **검증** — 출처/톤/AI 냄새 검증
5. **전달 패킷** — p1_packet 생성
6. **상태** — 작업 상태 표시

#### 벤치마킹 6개 항목
```
1. 채널 구조 (업로드주기, 시리즈, 영상길이)
2. 후킹 기법 (첫 5초/30초, 오프닝, 감정자극)
3. 썸네일 기법 (색상, 폰트, 클릭유도)
4. 스크립트 구조 (기승전결, 인용, 감정곡선)
5. 태그/키워드 (주요태그, 알고리즘 유입)
6. 댓글 분석 (체험/공감/해결 → 주제추천 전달)
```

#### 채널 발굴 시스템 (우측 SAGE 브레인)
```
조건: 구독자 1만↓ + 조회수 10만↑ + 바이럴 지수 상위
Gemini Flash 웹검색 → YouTube API 검증 → TOP 5
→ Gemini 종합 분석 → 최종 추천 1개
→ [벤치마킹 적용] 자동 입력
```

#### 주제 추천 3대 소스
```
소스 1: 댓글 (체험/공감/해결 - ⭐⭐⭐ 최우선)
소스 2: 옵시디언 RAG (성경/철학/심리)
소스 3: Tavily 트렌드 (유튜브 인기 키워드)
```

#### 주제당 6개 항목
```
1. 제목
2. 핵심 주제
3. 추천 사유
4. 핵심 키워드
5. 시청자 예상 반응
6. 시청자 예상 효과
```

#### 댓글 선별 기준
```
⭐⭐⭐ 최우선: 직접 체험 + 문제 해결 + 삶의 전환점
⭐⭐ 우선: 감정 폭발 공감 + 관계/가족/외로움 깊은 반응
⭐ 참조: 일반 긍정 반응
❌ 제외: 광고 / 스팸 / 1020 밈
```

#### 자료 충분도 점수화 (18점 만점)
```
1. 관련성 (0~3점)
2. 출처성 (0~3점)
3. 깊이 (0~3점)
4. 균형 (성경+철학+심리+감정, 0~3점)
5. 제작 활용성 (0~3점)
6. 최신성 (0~3점)

판정:
15~18점: 충분
10~14점: 보완 필요
0~9점: 부족
```

#### p1_packet 구조
```json
{
  "part": 1,
  "topic": "",
  "core_emotion": "",
  "audience_pain": "",
  "benchmark_summary": "",
  "comment_insights": [],
  "research_sources": [],
  "title_candidates": [],
  "thumbnail_direction": "",
  "knowledge_score": {},
  "next_part": 2
}
```

---

### Part 2 — 총괄기획 (Alchemist)

**입력:** p1_packet

**생성:**
- 최종 주제 / 한 줄 핵심 메시지
- 제목 후보 5개 / 썸네일 문구 후보 5개
- 시청자 페르소나 / 감정 곡선
- 기승전결 구조
- 성경/철학/심리 연결
- 대본 금지/필수 방향

#### 감정 곡선 기본형
```
고독 → 상처 자각 → 내면 붕괴 → 거울 직면
→ 철학적 통찰 → 성경적 여운 → 조용한 회복
```

---

### Part 3 — 대본작성 (Script)

**입력:** p2_packet

#### 영상 구조 표준
```
112씬 × 8초 = 896초 ≈ 14분 56초
(Google Opal 영상 8초 고정 기준)
```

#### 장면 타입 4종
```
TALK    : 일반 나레이션 장면 (70~78씬)
PAUSE   : 1~2초 짧은 침묵 (12~16씬)
SILENT  : 무음 또는 BGM only (10~14씬)
ECHO    : 거울 아바타 속삭임 (8~12씬)
```

#### 구간 설계
```
scene 001~012: 도입 / 강한 후킹 / 상처 호출
scene 013~036: 상처 분석 / 현실 사례 / 감정 해부
scene 037~064: 철학적 해석 / 고독과 욕망
scene 065~088: 성경적 연결 / 거울 직면 / 감정 심화
scene 089~112: 회복 / 침묵 / 여운 / 마무리
```

#### 거울 아바타 감정 7종
```
슬픔 / 고독 / 외로움 / 분노
체념 / 깨달음 / 회복
```

---

### Part 4 — 이미지생성 (Image)

**입력:** p3_packet

#### 에셋 구조

**A. 기준 에셋 (15개)**
```
A1~A4: @Protagonist (정면/측면/클로즈업/전신)
A5~A8: 17세기 서재 / 거울 / 촛불
A9: 거울 단독
A10~A15: 거울 속 아바타 6감정
```

**B. 파생 에셋:** 핵심 감정만 생성
**C. 장면별 프롬프트:** 112씬 매핑

#### 생성 파일
```
asset_master_list.md
asset_mapping.json
scene_image_plan.csv
auto_flow_batch_prompts.txt
retry_image_list.md
```

---

### Part 5 — 영상생성 (Video)

**입력:** p3_packet + p4_packet

#### 기본 원칙
```
모든 영상: 8초 고정
112씬 = 112개 영상 클립
8계정 분산 + 2일 작업
```

#### 계정 분배
```
Account 1: scene 001~014
Account 2: scene 015~028
Account 3: scene 029~042
Account 4: scene 043~056
Account 5: scene 057~070
Account 6: scene 071~084
Account 7: scene 085~098
Account 8: scene 099~112
```

#### 2일 운영
```
Day 1: Account 1~4 (scene 001~056)
Day 2: Account 5~8 (scene 057~112) + Day 1 실패분
```

---

### Part 6 — 나레이션·배경음악 (Audio)

**입력:** p3_packet + p5_packet

#### 보이스 기준
```
50대 후반~60대 남성
낮고 묵직한 중저음
느린 속도 / 절제된 감정
강의 X / 고백 O
```

#### BGM 큐시트
```
도입: 잔잔한 피아노
고독 심화: 첼로
붕괴: 낮은 스트링
무음 장면: BGM only 또는 complete silence
결말: 오르간/피아노 여운
```

---

### Part 7 — 숏폼 (Shorts)

**입력:** p3_packet + p6_packet

#### 60초 5단계 구조
```
0~1초:   훅
1~10초:  상처 제시
10~35초: 심리/철학 해석
35~50초: 반전
50~60초: 롱폼 유도
```

---

### Part 8 — 최종조립 (Final)

**입력:** p1~p7 모든 packet

#### 생성물
```
CapCut JSON
전체 조립 순서표
파일명 검수표
업로드 제목 / 설명란 초안 / 해시태그
출처 정리 / AI 사용 표시
최종 검수 리포트
```

#### 설명란 초안 구조
```
[제작자 노트]
- 이 영상을 만들게 된 계기
- 나도 비슷한 경험
- 시청자에게 전하고 싶은 것

[오늘의 묵상]
- 성경 또는 철학 인용 1줄
- 현자의 해석 1~2줄
- "오늘 하루, 이 한 줄과 함께하세요."

[출처]
[해시태그]
```

---

## 5. 데이터 흐름 — packet 시스템

```
Part 1 → p1_packet → Part 2
Part 2 → p2_packet → Part 3
Part 3 → p3_packet → Part 4
Part 4 → p4_packet → Part 5
Part 5 → p5_packet → Part 6
Part 6 → p6_packet → Part 7
Part 7 → p7_packet → Part 8
Part 8 → final_packet (완료)
```

**원칙:**
- 각 Part는 이전 Part의 packet만 읽음
- 다른 Part 결과물 임의 덮어쓰기 금지
- 우측 패널은 packet 직접 수정 금지 (제안만)

---

## 6. 옵시디언 다채널 저장 구조

```
00_Obsidian_Archive/
├── 00_Raw/              (원본 그대로)
│   ├── _Inbox
│   ├── YouTube
│   ├── WebResearch
│   ├── GeminiResearch
│   ├── TavilyResearch
│   ├── UserUploads
│   └── GoogleDrive
│
├── 01_Wiki/             (정리된 지식)
│   ├── Bible
│   ├── Philosophy
│   ├── Psychology
│   ├── Emotion
│   ├── YouTubeStrategy
│   └── Production
│
├── 02_Schema/           (구조화 JSON)
│   ├── Packets
│   ├── ScenePlans
│   ├── AssetMaps
│   └── CapCutJson
│
├── 03_Channels/         (채널별 제작물)
│   ├── SageMirror       (현자의 거울)
│   ├── Channel_002      (향후 확장)
│   └── Channel_003
│
├── 04_References/       (참고 자료)
├── 05_Assets/           (이미지/영상/오디오)
└── 99_Logs/             (로그)
```

### 저장 시 필수 메타데이터
```
channel_id, project_id, episode_id, part_id
content_type, source_type, source_url
category, tags, keywords
usable_parts, trust_level, created_at
```

---

## 7. 우측 SAGE 브레인 패널

**역할:** 보조 참모만 수행 (중앙 결과물 덮어쓰기 금지)

**기능:**
- 현재 Part 상태 표시
- RAG 자료 충분도 검사
- 부족 자료 진단
- Gemini/Tavily 리서치 질문 생성
- 수동 리서치 입력 받기
- Raw/Wiki/Schema 저장
- 중앙 Part 반영 제안 (사용자 승인 후 적용)

---

## 8. 파일명 규칙

```
scene_001.png ~ scene_112.png
video_001.mp4 ~ video_112.mp4
audio_001.wav ~ audio_112.wav
subtitle_001.srt ~ subtitle_112.srt
short_01.mp4 ~ short_05.mp4
final_episode.mp4
final_packet.json
```

---

## 9. 상태 관리

각 scene 상태값:
```
pending / working / done / failed / retry
```

각 scene 상태:
```json
{
  "scene_id": "001",
  "image_status": "pending",
  "video_status": "pending",
  "audio_status": "pending",
  "subtitle_status": "pending",
  "final_status": "pending"
}
```

---

## 10. 무료 운영 전략

```
✅ 로컬 Gemma 우선 (Ollama)
✅ 옵시디언 RAG 우선
✅ 외부 자료는 수동/반자동 보완
✅ Google Flow 무료 한도 고려
✅ Google Opal 8계정 분산 운영
✅ Gemini Flash 무료 등급
✅ Tavily 월 1,000회 무료
```

---

## 11. 보안 규칙

GitHub 절대 업로드 금지:
```
.streamlit/secrets.toml
google_token.json
credentials.json
client_secret.json
.env
*.token
*.key
*.pem
data/drive_sync_state.json
data/workspace_state.json
```

---

## 12. 완료 기준

```
✅ 앱이 켜진다
✅ Part 1~8 이동된다
✅ 각 Part 결과물이 생성된다
✅ 각 Part packet이 저장된다
✅ packet이 다음 Part로 전달된다
✅ 앱 재실행 후 상태 복원
✅ 옵시디언 Raw/Wiki/Schema 저장
✅ 자료 부족 판단 점수 작동
✅ 외부 리서치 보완 후 점수 상승
✅ 112씬 대본 생성
✅ 이미지 운영 패키지 생성
✅ Opal 8계정 분배 JSON 생성
✅ TTS/BGM 큐시트 생성
✅ 숏폼 생성
✅ CapCut/업로드 패키지 생성
```

---

## 13. 핵심 철학

```
코드는 가볍게
흐름은 단단하게
자료는 축적되게
대본은 깊게
이미지는 일관되게
영상은 분배되게
소리는 절제되게
숏폼은 유입되게
최종 결과물은 실제 제작 가능하게
```

**현자의 거울은 생성형 앱이 아니라 기억형 제작 시스템이다.**

```
생성 → 저장 → 연결 → 진화 → 재사용
```
