# SAGE Studio V18 — 마스터 지침서
> 범용 유튜브 영상 제작 운영체제 · 에이전트 기반 자동화
> 작성: 2026-06-14 | 버전: v19.0.0 (설계 기준)
> 위치: `C:\SageMirror_Studio_v18\` · 포트 8506

---

# 0. 이 문서의 정체

이 문서는 SAGE Studio V18 앱의 **단일 진실 공급원(Single Source of Truth)**이다. 클로드 코드, 본 채팅 Claude, 다른 AI 도구가 모두 이 문서를 기준으로 작동한다.

이 문서가 코드와 다르면 → 코드를 이 문서에 맞춘다.

---

# 1. 앱 정체성

## 1.1 한 문장 정의

> **SAGE Studio는 어떤 채널, 어떤 주제든 가져오면 유튜브에서 떡상할 수 있는 영상을 자동 제작하는 운영체제다.**

## 1.2 핵심 원칙

```
1. 범용성 — 현자의 거울 전용이 아니다. 모든 채널에 사용 가능.
2. 자동화 — 사용자는 최소 입력 + 검수 + 승인만 한다.
3. 에이전트 운영 — 각 파트는 독립 에이전트가 담당.
4. 검수 루프 — AI 결과는 초안. 반드시 검수·승인 후 다음 단계로.
5. 데이터 보존 — Raw / Wiki / Schema / Logs 4중 저장.
6. 떡상 지향 — 댓글 분석 기반 실제 시청자 고통 추출이 핵심.
```

## 1.3 사용자 역할

```
✅ 사용자가 하는 것:
  - 주제 / 채널 방향 입력
  - 결과물 검수
  - 승인 또는 재생성 지시
  - 최종 출시 판단

❌ 사용자가 하지 않는 것:
  - 매 단계 버튼 클릭
  - 프롬프트 직접 작성
  - 파일명 관리
  - 옵시디언 저장 경로 지정
```

---

# 2. 아키텍처 — Core + Profile + Agents

## 2.1 3층 구조

```
┌──────────────────────────────────────┐
│   Channel Profile (YAML)             │  ← 채널별 스타일 / 톤 / 상징
├──────────────────────────────────────┤
│   Agent Layer (11개 에이전트)         │  ← 실제 작업 수행
├──────────────────────────────────────┤
│   Core Engine (Streamlit 앱)         │  ← Part 흐름, Packet, 상태 관리
└──────────────────────────────────────┘
```

## 2.2 Channel Profile 시스템

채널마다 별도 YAML 파일로 분리.

**파일 위치:** `profiles/{channel_name}.yaml`

**예시: `profiles/sage_mirror.yaml`**
```yaml
channel_name: 현자의 거울
target_audience: 40~70대
tone: 차분하고 깊은 감정 해부형
narrator_age: 65세 철학자
narrator_style: 렘브란트풍 시네마틱
core_symbols: [거울, 촛불, 서재]
visual_style: 17세기 키아로스쿠로
philosophy_anchor: [쇼펜하우어, 프랭클, 성경]
forbidden_expressions: [욕설, 과도한 자극, 음모론]
preferred_expressions: [성찰, 회한, 자기 직면]
typical_topics: [후회, 관계 상처, 노년의 외로움, 인생의 의미]
```

**예시: `profiles/cooking.yaml`**
```yaml
channel_name: 우리 엄마 요리
target_audience: 30~50대 주부
tone: 따뜻하고 친근한 부엌 수다
narrator_age: 50대 어머니
narrator_style: 일상 부엌 다큐
core_symbols: [엄마 손, 도마, 김 오르는 솥]
visual_style: 따뜻한 자연광
philosophy_anchor: [가족, 추억, 정성]
typical_topics: [엄마 레시피, 추억의 음식, 가족 식탁]
```

## 2.3 Channel Profile 사용 흐름

```
앱 시작 → 사이드바에서 채널 선택 → Profile YAML 로드
       → 모든 에이전트가 이 Profile을 참조하며 작업
       → 옵시디언 저장 시 채널명 자동 적용
```

---

# 3. 에이전트 시스템 (11개)

## 3.1 에이전트 구조

```
┌──────────────────────────────────────────────────────┐
│  🎼 Conductor (지휘자)                                │
│  전체 흐름 조율 · Part 간 전환 · 사용자 응답 통합     │
└──────────────────────────────────────────────────────┘
        │
        ├─ 📚 Librarian   (Part 1: 자료수집·발굴)
        ├─ 🏗️ Architect  (Part 2: 총괄기획)
        ├─ ✍️ Writer      (Part 3: 대본설계)
        ├─ 🎨 Artist      (Part 4: 이미지생성)
        ├─ 🎬 Director    (Part 5: 영상제작)
        ├─ 🎙️ Composer   (Part 6: 오디오제작)
        ├─ ✂️ Editor      (Part 7: 숏폼파생)
        └─ 🚀 Assembler   (Part 8: 최종조립)

        │ (보조 에이전트 — 모든 Part에서 호출 가능)
        │
        ├─ 🔍 Critic      (검수)
        ├─ 📦 Curator     (옵시디언 관리)
        └─ 🛰️ Scout       (자료 보강)
```

## 3.2 각 에이전트 정의

### 🎼 Conductor (지휘자)
```
역할: 전체 흐름 통제, Part 전환 결정, 사용자 입력 라우팅
모델: Gemma 4 e2b (가벼움)
호출 시점: 사용자가 우측 대화창 입력할 때마다
주요 결정: "이 메시지는 어느 Part로 보낼지", "검수가 필요한지"
```

### 📚 Librarian (Part 1)
```
역할: 채널 분석 · 댓글 추출 · 주제 후보 10개 이상 생성
모델: Gemma 4 e4b (심층 분석) + Gemini Flash (선택)
도구: YouTube Data API + Tavily + Obsidian RAG
출력: Channel Analysis Packet + Comment Topic Packet
```

### 🏗️ Architect (Part 2)
```
역할: 총괄 기획안 작성 · 제목 / 썸네일 기법 / 감정 흐름 설계
모델: Gemma 4 e4b
입력: Part 1 Packet + 사용자가 선택한 주제 · 제목 후보
출력: Planning Packet
```

### ✍️ Writer (Part 3)
```
역할: 장면별 대본 (S001, S002...) · 자막용 · 나레이션용 분할
모델: Gemma 4 e4b
출력: Script Packet (순번 기반)
```

### 🎨 Artist (Part 4)
```
역할: 인물 8방향, 배경 4패널, 본편 장면 이미지 프롬프트
모델: Gemma 4 e4b
출력: Image Packet (영어 프롬프트 + 순번 매핑)
```

### 🎬 Director (Part 5)
```
역할: Opal 8초 클립 JSON 프롬프트 · 8계정 운영표
모델: Gemma 4 e4b
출력: Video Clip Packet (날짜 · 계정 · 순번 매핑)
```

### 🎙️ Composer (Part 6)
```
역할: 나레이션 텍스트 · BGM 프롬프트 · 휴먼터치 토큰
모델: Gemma 4 e4b
출력: Audio Packet (TTS 도구별 입력 + BGM 배치표)
```

### ✂️ Editor (Part 7)
```
역할: 60초 이내 숏폼 2~3개 파생 (롱폼 → 숏폼)
모델: Gemma 4 e4b
출력: Shortform Packet
```

### 🚀 Assembler (Part 8)
```
역할: 완성 파일 매칭 · CSV → JSON 변환 · CapCut 자동배치 패키지
모델: Gemma 4 e2b (단순 매칭)
출력: Final Assembly Package
```

### 🔍 Critic (보조)
```
역할: 모든 Part 결과물 자동 검수
모델: Gemma 4 e4b (다른 인스턴스)
호출: 각 Part 결과 생성 직후 자동
검수 항목:
  - 자료 근거 존재 여부
  - 논리 흐름
  - 채널 Profile 부합도
  - 복제 위험
  - 다음 Part 사용 가능성
출력: 검수 보고서 (PASS / NEEDS_DATA / NEEDS_FIX)
```

### 📦 Curator (보조)
```
역할: 옵시디언 Raw / Wiki / Schema 자동 저장 및 검색
모델: Gemma 4 e2b
호출: 모든 자료 입력 / 결과 생성 시
기능:
  - 카테고리 자동 분류
  - 키워드 / 태그 자동 추출
  - Schema JSON 자동 생성
  - 중복 감지
```

### 🛰️ Scout (보조)
```
역할: 자료 부족 시 자동 보강
모델: Gemma 4 e2b (판단) + Tavily (검색)
호출: Critic이 NEEDS_DATA 판정 시 자동
기능:
  - Tavily 웹 검색
  - YouTube 댓글 추가 수집
  - 옵시디언 자동 저장
```

## 3.3 에이전트 협업 흐름

```
사용자 입력
   ↓
Conductor 라우팅 결정
   ↓
해당 Part 에이전트 작업 시작
   ↓ (자료 부족 시)
   ├→ Curator: 옵시디언 검색
   └→ Scout: 부족하면 자동 보강
   ↓
Part 에이전트 결과 생성
   ↓
Critic 자동 검수
   ↓
   ├─ PASS → 사용자에게 표시 + 승인 대기
   ├─ NEEDS_DATA → Scout 호출 → 재작성
   └─ NEEDS_FIX → Part 에이전트 재작성
   ↓
사용자 승인 / 재생성 요청
   ↓
승인 시 → Curator가 Obsidian 저장 → Packet 다음 Part로 전달
```

---

# 4. 옵시디언 통합 구조 (확정)

## 4.1 공식 경로

```
C:\SageMirror_Production\00_Obsidian\
├── 00_Raw_Data\          ← 원본 (PDF, DOCX, TXT, 웹스냅샷, 댓글로그)
│   ├── 채널_{채널명}\    ← 채널별 분리
│   └── 99_과거_아카이브_통합\
├── 01_Wiki\              ← 사람이 읽는 정제 노트 (카테고리 / 키워드 / 태그)
│   ├── 감정\
│   ├── 철학\
│   ├── 심리학\
│   ├── 성경·신앙\
│   ├── 유튜브전략\
│   ├── 채널운영\
│   └── 제작자료\
├── 02_Schema\            ← 기계 읽는 JSON 메타데이터
└── 03_Logs\              ← 저장/오류/검수/승인 기록
```

> ⚠️ 기존 폴더 (`01_Raw_Data`)는 호환성 유지를 위해 별칭(symlink) 또는 마이그레이션 처리.

## 4.2 저장 규칙

| 파일 종류 | 저장 위치 |
|---|---|
| 사용자 업로드 원본 | `00_Raw_Data/채널_{채널명}/` |
| 댓글 로그 | `00_Raw_Data/채널_{채널명}/comments/` |
| 정제된 지식 노트 | `01_Wiki/{카테고리}/` |
| Schema JSON | `02_Schema/{source_id}.json` |
| 로그 | `03_Logs/{yyyy-mm-dd}.log` |

## 4.3 Schema JSON 표준

```json
{
  "source_id": "SRC_0001",
  "source_type": "youtube_video | pdf | docx | web | comment_log",
  "title": "",
  "channel_name": "",
  "categories": ["감정", "관계"],
  "tags": ["배신감", "후회"],
  "keywords": ["참다", "떠나다", "조용히"],
  "raw_path": "00_Raw_Data/채널_현자의거울/...",
  "wiki_path": "01_Wiki/감정/...",
  "hash": "sha256:...",
  "created_at": "2026-06-14T10:00:00",
  "updated_at": "2026-06-14T10:00:00",
  "part": "Part1",
  "status": "indexed",
  "channel_relevance": 0.85,
  "related_parts": [1, 2, 3]
}
```

## 4.4 채널 동적 경로 함수

```python
# core/obsidian.py
def get_channel_raw_path():
    """현재 선택된 채널의 Raw 경로 반환"""
    channel = get_state("current_channel", "default")
    return OBSIDIAN_PATH / "00_Raw_Data" / f"채널_{channel}"

def get_wiki_path(category: str):
    """카테고리별 Wiki 경로 반환"""
    return OBSIDIAN_PATH / "01_Wiki" / category

def get_schema_path():
    return OBSIDIAN_PATH / "02_Schema"
```

> ⚠️ 채널명, 카테고리 하드코딩 금지. 모든 경로는 함수 호출로.

---

# 5. Packet 시스템

## 5.1 표준 Packet 구조

```json
{
  "packet_type": "channel_analysis | planning | script | image | video | audio | shortform | assembly",
  "source_part": "Part1",
  "target_part": "Part2",
  "version": "v001",
  "status": "DRAFT | REVIEW | APPROVED | LOCKED | PUSHED",
  "created_at": "2026-06-14T10:00:00",
  "approved_by_user": false,
  "channel_profile": "sage_mirror",
  "input_summary": "",
  "output_summary": "",
  "raw_path": "",
  "wiki_path": "",
  "schema_path": "",
  "payload": { /* Part별 고유 데이터 */ }
}
```

## 5.2 Packet 원칙

```
1. Part는 자기 결과를 다음 Part에 직접 던지지 않는다.
2. Packet으로 포장해 전달한다.
3. 승인본만 전달한다. DRAFT는 절대 PUSH 금지.
4. 재생성 시 새 버전(v002)으로 저장. 기존 덮어쓰기 금지.
5. 모든 Packet은 03_Logs에 자동 기록.
```

---

# 6. 상태 관리 (State Machine)

## 6.1 9개 상태

```
DRAFT          → 초안 생성
REVIEW         → 검수 중 (Critic 검토)
NEEDS_DATA     → 자료 부족 (Scout 호출)
NEEDS_FIX      → 수정 필요
RESEARCHED     → 자료 보강 완료
REWRITTEN      → 재작성 완료
APPROVED       → 사용자 승인
LOCKED         → 잠금
PUSHED         → 다음 Part 전달 완료
```

## 6.2 상태 전이 규칙

```
DRAFT → REVIEW → (PASS → APPROVED) or (FAIL → NEEDS_DATA/NEEDS_FIX)
NEEDS_DATA → RESEARCHED → REWRITTEN → REVIEW
NEEDS_FIX → REWRITTEN → REVIEW
APPROVED → LOCKED (사용자 잠금) → PUSHED (다음 Part 진입)
```

## 6.3 잠금 규칙

```
✅ APPROVED 상태에서만 LOCKED 가능
✅ LOCKED 상태에서만 PUSHED 가능
❌ APPROVED 없이 PUSHED 금지 — 시스템 강제 차단
```

---

# 7. 8파트 상세 사양

## 7.1 Part 1 — 자료수집·발굴 (Librarian)

### 역할
1. 벤치마킹할 채널·영상 발굴
2. 경쟁 채널 댓글 분석
3. 댓글 기반 주제·제목 후보 **최소 10개** 생성

### 입력
```
- 사용자 주제 또는 키워드
- Channel Profile (현재 선택된 채널)
- 타깃 시청자
- 언어
```

### 내부 처리 흐름
```
사용자 입력 → 키워드 추출 → 카테고리 분류
   ↓
YouTube Data API 검색 (국내) + Tavily (국외) → 채널 후보 5개
   ↓
조회수/구독자 비율 · 댓글 밀도 · 업로드 주기 분석
   ↓
대표 영상 선정 → 댓글 200개 수집
   ↓
댓글 감정 분석 → 반복 고통 / 실제 경험 문장 추출
   ↓
주제 후보 10개 + 제목 후보 + 댓글 근거 + 예상 반응
   ↓
Raw / Wiki / Schema 자동 저장
```

### 출력 (Comment Topic Packet)
```json
{
  "topic_id": "T001",
  "topic": "오래 참은 사람이 어느 날 조용히 떠나는 이유",
  "title_candidate": "착한 사람이 갑자기 차가워지는 진짜 이유",
  "comment_basis": "관계에서 계속 참고 양보하다가 결국 아무 말 없이 떠났다는 댓글 다수",
  "recommendation_reason": "관계·가족·직장에서 반복되는 감정",
  "expected_reaction": "'내 이야기 같다' '나도 저랬다' 자기 고백형 댓글 예상",
  "expected_effect": "공감 댓글 증가, 체류 시간 증가",
  "emotions": ["서운함", "분노", "체념", "외로움"],
  "risk_notes": "",
  "planning_hint": "Part 2 감정 흐름: 참음 → 무시 → 침묵 → 이별 → 자기 회복"
}
```

### 대표 버튼
```
🔎 채널 찾기 & 주제 발굴
```

### 시스템 프롬프트 (Librarian)
```
당신은 유튜브 채널 분석 전문가입니다.
당신의 역할:
1. 실제 검색 결과의 채널·영상만 분석합니다. 창작 금지.
2. 댓글에서 실제 시청자의 고통·후회·외로움·관계 상처를 발견합니다.
3. 댓글을 근거로 시청자가 "내 이야기 같다"고 느낄 주제 10개 이상 생성합니다.

금지:
- 댓글 근거 없는 추상적 주제
- 일반론·교과서 같은 주제
- 채널명·URL 창작
- 수치 임의 작성 (조회수, 구독자 등 — 실제 값만)

채널 Profile: {channel_profile}
타깃: {target_audience}
주제 후보 최소 개수: 10
출력 형식: Comment Topic Packet JSON
```

---

## 7.2 Part 2 — 총괄기획 (Architect)

### 역할
Part 1 결과를 받아 영상 전체 기획안 작성.

### 입력
```
- Channel Analysis Packet
- Comment Topic Packet (사용자가 선택한 1개)
- 사용자 제목 / 썸네일 기법 (선택)
- Channel Profile
```

### 핵심 원칙
```
주제 = 무엇을 말할 것인가
제목 = 어떤 감정으로 클릭하게 만들 것인가
썸네일 기법 = 어떤 시각적/문장적 충격으로 멈추게 할 것인가

→ 셋이 함께 작용해야 한다. 주제만 보고 기획하면 안 됨.
```

### 출력 (Planning Packet)
```
- 영상 제목 최종안 + 후보 3개
- 썸네일 기법 적용안
- 핵심 메시지
- 감정 흐름 (도입 → 전개 → 절정 → 결말)
- 구성안 (장면 단위)
- 도입 훅 (첫 5초)
- 이미지 방향
- 나레이션 방향
- BGM 방향
- 숏폼 파생 포인트
```

### 시스템 프롬프트 (Architect)
```
당신은 유튜브 떡상 영상 기획자입니다.

핵심 원칙:
- 첫 5초가 가장 중요합니다. 시청자가 멈추지 않으면 떡상은 없습니다.
- 감정의 곡선이 있어야 합니다. 평탄한 영상은 죽습니다.
- 시청자가 자기 이야기로 느껴야 합니다.
- 댓글에서 추출한 실제 고통을 반드시 영상에 녹여야 합니다.

채널 Profile: {channel_profile}
주제: {selected_topic}
댓글 근거: {comment_basis}

출력: Planning Packet
```

---

## 7.3 Part 3 — 대본설계 (Writer)

### 역할
승인된 기획안을 받아 장면별 대본 작성.

### 핵심 원칙
```
대본은 모든 것을 만들지 않는다.
대본은 대본만 만든다.
이미지 프롬프트, 영상 JSON, TTS는 각 Part가 담당.
```

### 출력
```
- 전체 대본
- 장면별 대본 (S001, S002, S003...)
- 도입 / 전개 / 절정 / 결말
- 자막용 분할 문장
- 나레이션용 문장 (호흡 표시)
- 감정 흐름표
- Part 4/5/6용 Packet 분할
```

### 순번 규칙
```
S001, S002, S003... ← 모든 후속 Part의 중심키
```

### 시스템 프롬프트 (Writer)
```
당신은 4070세대 감정을 글로 풀어내는 작가입니다.

원칙:
- 한 장면 = 1~3문장. 호흡 단위로 끊는다.
- 대화체와 내레이션을 자연스럽게 섞는다.
- 감정 절정 직전에 침묵(...)을 넣는다.
- 클리셰 금지. 진부한 표현 금지.
- 시청자가 "이거 내 이야기야" 느낄 디테일을 넣는다.

채널 Profile: {channel_profile}
기획안: {planning_packet}

출력: 장면별 대본 (S001 ~ Snn)
```

---

## 7.4 Part 4 — 이미지생성 (Artist)

### 역할
대본 Packet을 받아 이미지 생성 자료 작성.

### 3단 구조

```
A. 기본 참조
   - 인물 8방향 (정면/측면/후면 × 2각도)
   - 배경 4패널 (시간대별)
   - 아이템 4패널

B. 파생 참조
   - 의상 변화
   - 시간대 변화
   - 감정 변화
   - 상태 변화

C. 본편 장면
   - 순번별 영어 이미지 프롬프트
   - 참조 이미지 호출 정보
```

### 출력
```
- A/B/C 영어 프롬프트
- 이미지 파일명 규칙: S001_scene_01.png, S001_ref_character.png
- 순번별 이미지 매핑표
- Part 5용 Image Packet
```

### 시스템 프롬프트 (Artist)
```
당신은 영상 이미지 프롬프트 전문가입니다.

원칙:
- 영어로 생성합니다.
- 시각 스타일은 채널 Profile의 visual_style을 따릅니다.
- 인물 일관성을 위해 참조 이미지 호출을 명시합니다.
- 장면별 감정을 시각에 반영합니다.

채널 Profile: {channel_profile}
visual_style: {visual_style}
대본: {script_packet}

출력: Image Packet (영어 프롬프트 + 순번 매핑)
```

---

## 7.5 Part 5 — 영상제작 (Director)

### 역할
**Opal 작업 운영표** 생성. (단순 영상 프롬프트 아님)

### 핵심 기준
```
1 JSON Prompt = 1 영상 클립 = 기본 8초
```

### 8계정 운영 구조

```
날짜 → 계정 → 순번 → 대본 → 이미지 → JSON 프롬프트 → 생성 상태
```

기본은 균등 배분. 사용자가 수정 가능.

### 상태값
```
READY → GENERATING → DONE / FAILED → RETRY_PENDING → REGENERATED → MERGED
```

### 출력
```
- 순번별 영상 JSON 프롬프트
- 계정별 작업표
- 날짜별 작업표
- 실패/재시도 목록
- Part 8용 Video Clip Packet
```

---

## 7.6 Part 6 — 오디오제작 (Composer)

### 역할
나레이션 텍스트 생성 + BGM 프롬프트 + 휴먼터치 설계.

### 핵심: TTS 도구 비종속

```
나레이션 도구는 선택형:
- ChatTTS-ui (후보)
- Google AI Studio TTS
- CapCut TTS
- ElevenLabs
- 기타 로컬 TTS
```

Part 6은 도구 입력 패키지만 생성. 실제 음성 생성은 외부.

### 휴먼터치 토큰
```
- 호흡 (sigh, breath)
- 미세한 떨림
- 침묵 (...)
- 자연스러운 구어체 억양
- 과하지 않은 숨 고르기
```

### 파일명 규칙
```
S001_voice.wav
S002_voice.wav
...
```

### BGM
```
- 파일명, 분위기, 시작/종료, 볼륨, 페이드, 반복 여부
- 장면별 감정 연결
```

### 출력
```
- 순번별 나레이션 텍스트
- TTS 도구별 입력 CSV/TXT
- BGM 프롬프트 + 매핑표
- Part 8용 Audio Packet
```

---

## 7.7 Part 7 — 숏폼파생 (Editor)

### 역할
롱폼에서 숏폼 2~3개 파생.

### 기준
```
60초 이내 숏폼 2~3개
(15/30/60 다중 생성 아님)
```

### 구조
```
훅 → 감정 자극 → 반전/핵심 문장 → 롱폼 연결
```

### 출력
```
- 숏폼 1, 2, 3 대본
- 숏폼 제목 후보
- 숏폼 자막
- 숏폼 영상 클립 후보 (롱폼에서 추출)
- 숏폼 나레이션
- CapCut 배치용 Packet
```

---

## 7.8 Part 8 — 최종조립 (Assembler)

### 역할
완성 파일들을 순번 기준으로 매칭 → CSV → JSON → 기존 CapCut 자동배치 프로그램으로 전달.

### 핵심: 순번이 중심키

```
S001_script.txt
S001_voice.wav
S001_clip.mp4
S001_subtitle.srt
S001_image_prompt.txt
```

### CSV 예시
```csv
scene_id,script_path,voice_path,video_path,subtitle_path,bgm_path,start_time,duration,status
S001,script/S001.txt,voice/S001.wav,video/S001.mp4,subtitle/S001.srt,bgm/main.mp3,0,8,READY
S002,script/S002.txt,voice/S002.wav,video/S002.mp4,subtitle/S002.srt,bgm/main.mp3,8,8,READY
```

### JSON 변환
```json
{
  "project_title": "",
  "channel_profile": "",
  "timeline": [
    { "scene_id": "S001", "script_path": "...", "voice_path": "...", "video_path": "...", "subtitle_path": "...", "bgm_path": "...", "start_time": 0, "duration": 8, "status": "READY" }
  ]
}
```

### 검수 항목
```
- 순번 누락 / 중복
- 대본 / 나레이션 / 영상 / 자막 / BGM 파일 누락
- 파일 경로 오류
- 영상/나레이션 길이 오류
- 배치 가능 여부
```

### 대표 버튼
```
🎞️ CapCut 자동 배치 패키지 생성
```

---

# 8. UI 구조

## 8.1 화면 레이아웃 (7:3)

```
┌──────────────────────────────────────┬───────────────────────┐
│  좌측 (70%) — 메인 작업 영역          │  우측 (30%) — SAGE 브레인 │
│                                       │  (보조 참모 대화창)        │
│  - Part 1~8 탭                        │                       │
│  - RAG 자료 상태 박스                  │  - 검수 / 보강 / 질문   │
│  - 결과물 표시 (크게)                 │  - + 메뉴 (파일/드라이브 등) │
│  - 검수 / 승인 / 재생성 버튼          │  - 입력창 (하단 고정)    │
│                                       │                       │
└──────────────────────────────────────┴───────────────────────┘
```

## 8.2 상단 구조

```
┌──────────────────────────────────────────────┐
│  좌측 접힘: 📖 Part 작업 매뉴얼              │
│  우측 접힘: 🤖 Part 전체 실행 프롬프트       │
└──────────────────────────────────────────────┘
※ 기본은 접힌 상태
```

## 8.3 본문 구조

```
1. 입력창 (한 줄)
2. 대표 실행 버튼 ([🔎 채널 찾기] 등 큰 버튼 1개)
3. 진행 상태 표시
4. 결과 요약
5. Step 목록 (각 Step → 큰 팝업으로 확장)
```

## 8.4 Step 결과 = 큰 팝업

작은 결과창 금지.

**큰 팝업 구성:**
```
- Step 목표
- 입력값
- 생성 결과 (st.text_area 또는 st.data_editor)
- 검수 결과 (Critic 보고서)
- 수정 가능한 텍스트 영역
- [복사] [다시 생성] [저장] [승인] [다음 단계 전달]
```

## 8.5 우측 SAGE 브레인 (참모)

```
역할:
✅ 검수 / 보강 자료 수집 / 부족 자료 지적
✅ 파일 가져오기 (+ 메뉴)
✅ 사용자 질문 대응

금지:
❌ 중앙 결과 직접 덮어쓰기
❌ 승인 없이 다음 Part로 PUSH
❌ 중앙 상태 강제 변경

+ 메뉴:
📁 로컬 자료 가져오기
☁️ Google Drive · Docs 연결
📓 NotebookLM 자료 폴더 연결
🎬 YouTube/영상 분석
🧹 우측 대화 초기화
```

## 8.6 대화창 고정 (CSS)

```css
/* Streamlit 한계 — sticky로 화면 비율 맞춤 */
대화창 높이: calc(100vh - 280px)
입력창: position sticky bottom 0
```

---

# 9. 검수 루프 (모든 Part 공통)

```
Gemma 초안 생성
   ↓
Critic 자동 검수 (모델 분리된 별도 인스턴스)
   ↓
   ├─ PASS → 사용자에게 표시
   ├─ NEEDS_DATA → Scout 호출 (Tavily/RAG 보강) → Raw/Wiki/Schema 저장 → 재참조 → 재작성
   └─ NEEDS_FIX → Part 에이전트 재작성
   ↓
사용자 검수
   ↓
   ├─ 승인 → APPROVED → LOCKED → PUSHED (다음 Part 진입)
   └─ 재생성 → v002 새 버전 (기존 덮어쓰기 금지)
```

## 9.1 검수 기준

```
□ 자료 근거가 있는가
□ 헛소리가 없는가
□ 논리 흐름이 맞는가
□ 사용자 의도와 맞는가
□ 채널 Profile과 맞는가
□ 복제 위험이 없는가
□ 다음 Part가 사용할 수 있는가
□ 파일이 저장되었는가
□ 순번이 맞는가
```

---

# 10. 재생성 규칙

```
✅ 새 버전(v001 → v002 → v003)으로 저장
✅ 재생성 입력에 다음 포함:
   - 기존 입력
   - 기존 결과
   - 사용자 불만 이유
   - 검수 실패 이유
   - 보강 자료
   - 선택한 개선 방향
❌ 기존 결과 덮어쓰기 금지
```

---

# 11. MCP / 스킬 활용

## 11.1 활용 가능한 MCP

| MCP | 용도 |
|---|---|
| Google Drive | 자료 자동 동기화 / 백업 |
| Google Docs | 대본 / 기획안 외부 작성 |
| Gmail | 작업 완료 알림 |
| Notion | 프로젝트 진행 관리 |
| Canva | 썸네일 디자인 (옵션) |

## 11.2 스킬 활용

```
- pdf 스킬: 사용자가 업로드한 PDF 자동 파싱 → Raw 저장
- docx 스킬: 대본 외부 편집 후 재import
- xlsx 스킬: Part 5 운영표 / Part 8 CSV 생성
- pptx 스킬: 기획안 외부 공유용
```

## 11.3 사용자 정의 스킬 (향후)

```
- 자료수집 스킬: Part 1 자동화
- 대본 검수 스킬: Critic 강화
- 옵시디언 정리 스킬: Curator 강화
```

---

# 12. 개발 규칙

## 12.1 절대 규칙

```
1. 백업 필수 (수정 전 git tag + 파일 복사)
2. 원본 덮어쓰기 금지 — 새 버전 파일에서만 작업
3. py_compile 검증 필수
4. 채널명 / URL 창작 절대 금지 — 실제 데이터만
5. 수치는 실제 확인된 값만 사용
6. 작업 완료 후 버전 보고 필수
7. 채널명 하드코딩 금지 — get_channel_path() 함수 사용
8. Part 단위로만 수정 — 한 번에 전체 수정 금지
```

## 12.2 작업 순서

```
1. 현재 정상본 확인
2. git tag backup-YYYYMMDD
3. 새 버전 파일 생성
4. 새 버전에서만 수정
5. python -m py_compile 검증
6. Streamlit 실행 확인
7. 화면 정상 작동 확인
8. git commit + push
```

## 12.3 작업 분담

```
본 채팅 Claude — 설계 / 방향 / 검토 / 지침서 작성 (토큰 절약 위해)
Claude Code   — 실제 코드 수정 / 컴파일 / 검증
사용자        — 결과 확인 / 승인 / 방향 결정
```

---

# 13. 버전 관리

```python
APP_VERSION = "v19.0.0"  # 메이저 리모델링

규칙:
v19.0.X — 마이너 수정 / 버그 픽스
v19.X.0 — 파트 완성 단위
v20.0.0 — 다음 메이저 리모델링
```

---

# 14. 현재 작업 우선순위

## 14.1 즉시 (이번 주)
```
1. Channel Profile YAML 시스템 구축
   - profiles/ 폴더 생성
   - profiles/sage_mirror.yaml 작성
   - 사이드바에 채널 선택 드롭다운
2. 옵시디언 경로 통일 (00_Raw_Data, 01_Wiki, 02_Schema, 03_Logs)
3. Conductor / Critic / Curator / Scout 4개 보조 에이전트 구축
4. Part 1 Librarian 에이전트 리팩토링
   - 댓글 분석 모듈 강화
   - 주제 후보 10개 보장
```

## 14.2 다음 (이달)
```
5. Part 2 Architect 구축
6. Part 3 Writer 구축
7. 검수 루프 전면 적용
8. Packet 시스템 표준화
```

## 14.3 그 다음 (다음 달)
```
9. Part 4~6
10. Part 7 숏폼
11. Part 8 CapCut 자동배치 연동
12. 다채널 테스트 (현자의 거울 외 1개 채널 추가)
```

---

# 15. 최종 한 문장

```
SAGE Studio V18은 사용자가 주제만 입력하면
11개 에이전트가 협업하여 유튜브 떡상 영상을 자동 제작하는,
모든 채널·모든 주제에 사용 가능한 범용 영상 제작 운영체제다.
```

---

**문서 끝 — 의문 발생 시 이 문서가 최우선 권위.**
