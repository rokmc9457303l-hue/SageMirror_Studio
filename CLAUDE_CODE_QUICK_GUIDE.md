# CLAUDE_CODE_QUICK_GUIDE.md
> Claude Code 전용 빠른 작업 지침서
> 항상 이 파일을 먼저 읽고 작업 시작

---

## 🎯 이 앱의 정체

SAGE Studio V18 = **범용 유튜브 영상 제작 OS**

- 위치: `C:\SageMirror_Studio_v18\`
- 포트: 8506
- 버전: v19.0.0 (대대적 리모델링 진행 중)
- 마스터 지침서: `SAGE_V18_MASTER.md`

---

## ❗ 절대 규칙 (위반 즉시 중단)

```
1. 수정 전 백업 (git tag + 파일 복사)
2. 새 버전 파일에서만 작업 (원본 덮어쓰기 금지)
3. python -m py_compile 검증 필수
4. 채널명 / URL 창작 절대 금지
5. 채널명 하드코딩 금지 → get_channel_path() 함수 사용
6. 수치는 실제 확인된 값만 사용
7. Part 단위로만 수정 (한 번에 전체 수정 금지)
8. 작업 완료 후 버전 보고 필수
```

---

## 📁 핵심 파일 위치

| 파일 | 역할 |
|---|---|
| `app.py` | 메인 진입점 |
| `core/config.py` | 설정 · APP_VERSION · OBSIDIAN 경로 |
| `core/brain.py` | AI 라우팅 (Gemini / Gemma) |
| `core/obsidian.py` | Raw / Wiki / Schema 저장 |
| `core/state.py` | 세션 상태 |
| `core/agents/` | **신규** — 에이전트 시스템 (구축 필요) |
| `profiles/` | **신규** — Channel Profile YAML |
| `panel/right_panel.py` | 우측 SAGE 브레인 대화창 |
| `parts/part1~8` | 각 Part 모듈 |
| `.streamlit/secrets.toml` | API 키 |

---

## 🤖 11개 에이전트 (구축 목표)

### 메인 (8개)
1. **🎼 Conductor** — 전체 흐름 조율 (Gemma 4 e2b)
2. **📚 Librarian** — Part 1 자료수집 (Gemma 4 e4b)
3. **🏗️ Architect** — Part 2 기획 (Gemma 4 e4b)
4. **✍️ Writer** — Part 3 대본 (Gemma 4 e4b)
5. **🎨 Artist** — Part 4 이미지 (Gemma 4 e4b)
6. **🎬 Director** — Part 5 영상 (Gemma 4 e4b)
7. **🎙️ Composer** — Part 6 오디오 (Gemma 4 e4b)
8. **✂️ Editor** — Part 7 숏폼 (Gemma 4 e4b)
9. **🚀 Assembler** — Part 8 최종조립 (Gemma 4 e2b)

### 보조 (3개)
10. **🔍 Critic** — 검수 (Gemma 4 e4b, 별도 인스턴스)
11. **📦 Curator** — 옵시디언 관리 (Gemma 4 e2b)
12. **🛰️ Scout** — 자료 보강 (Gemma 4 e2b + Tavily)

---

## 📂 옵시디언 통일 경로 (확정)

```
C:\SageMirror_Production\00_Obsidian\
├── 00_Raw_Data\          ← 원본
│   ├── 채널_{채널명}\    ← 채널별 동적 경로
│   └── 99_과거_아카이브_통합\
├── 01_Wiki\              ← 카테고리별 정제 노트
├── 02_Schema\            ← JSON 메타데이터
└── 03_Logs\              ← 저장/오류/검수 기록
```

### 동적 경로 함수 (필수)
```python
def get_channel_raw_path():
    channel = get_state("current_channel", "default")
    return OBSIDIAN_PATH / "00_Raw_Data" / f"채널_{channel}"

def get_wiki_path(category: str):
    return OBSIDIAN_PATH / "01_Wiki" / category
```

> ⚠️ 채널명 하드코딩 발견 시 즉시 수정.

---

## 🎭 Channel Profile 시스템

### 위치
```
profiles/
├── sage_mirror.yaml       ← 현자의 거울
├── cooking.yaml           ← 요리 채널 (예시)
└── _template.yaml         ← 새 채널 생성 템플릿
```

### 표준 구조
```yaml
channel_name: ""
target_audience: ""
tone: ""
narrator_age: ""
narrator_style: ""
core_symbols: []
visual_style: ""
philosophy_anchor: []
forbidden_expressions: []
preferred_expressions: []
typical_topics: []
```

### 로드 시점
```
앱 시작 → 사이드바 채널 드롭다운 → Profile YAML 로드 →
   get_state("channel_profile") 에 저장 →
   모든 에이전트가 호출
```

---

## 📦 Packet 시스템

### 모든 Part 결과는 Packet으로 전달

```json
{
  "packet_type": "channel_analysis | planning | script | ...",
  "source_part": "Part1",
  "target_part": "Part2",
  "version": "v001",
  "status": "DRAFT | APPROVED | LOCKED | PUSHED",
  "channel_profile": "sage_mirror",
  "approved_by_user": false,
  "payload": { /* 데이터 */ },
  "raw_path": "",
  "wiki_path": "",
  "schema_path": ""
}
```

### 원칙
```
✅ 승인본만 다음 Part로 PUSH
✅ 재생성 시 v002 새 버전
❌ APPROVED 없이 PUSH 금지 (시스템 차단)
❌ 기존 Packet 덮어쓰기 금지
```

---

## 🔄 상태 머신 (9개)

```
DRAFT → REVIEW → (PASS or NEEDS_DATA / NEEDS_FIX)
NEEDS_DATA → Scout 호출 → RESEARCHED → REWRITTEN → REVIEW
APPROVED → LOCKED → PUSHED
```

---

## 🔍 검수 루프 (모든 Part 공통)

```
1. Gemma 초안 생성
2. Critic 자동 검수 (별도 인스턴스)
3. NEEDS_DATA → Scout 호출 → Tavily 보강 → 옵시디언 저장
4. NEEDS_FIX → 재작성
5. PASS → 사용자에게 표시
6. 사용자 승인 → LOCKED → PUSHED
```

---

## 🛠️ 작업 흐름 표준

### 모든 수정 시
```bash
# 1. 백업
git tag backup-YYYYMMDD-{작업명}
copy {파일} {파일}_v{version}_backup.py

# 2. 수정 (새 버전 파일)

# 3. 컴파일 검증
python -m py_compile {파일}
echo "OK"

# 4. 앱 실행 확인
cd C:\SageMirror_Studio_v18
python -m streamlit run app.py --server.port 8506

# 5. 화면 확인 후 git commit
```

---

## 📋 작업 분담

| 역할 | 담당 |
|---|---|
| 설계 / 방향 / 검토 / 지침서 | 본 채팅 Claude |
| **실제 코드 수정 / 컴파일** | **Claude Code (당신)** |
| 결과 확인 / 승인 | 사용자 (현자님) |

---

## 🎬 Part별 핵심 요약

### Part 1 — 자료수집·발굴
```
입력: 사용자 주제 + Channel Profile
처리: YouTube/Tavily 검색 → 댓글 200개 → 감정 분석 → 주제 10개
출력: Channel Analysis Packet + Comment Topic Packet
대표 버튼: 🔎 채널 찾기 & 주제 발굴
```

### Part 2 — 총괄기획
```
원칙: 주제 + 제목 + 썸네일 기법을 함께 설계
입력: Part 1 Packet + 사용자 선택 주제
출력: Planning Packet (제목/썸네일/감정흐름/구성안)
```

### Part 3 — 대본설계
```
원칙: 대본만 만든다 (이미지/영상/TTS는 각 Part 담당)
순번: S001, S002, S003... ← 모든 후속 Part 중심키
출력: 장면별 대본 + 자막용 + 나레이션용 분할
```

### Part 4 — 이미지생성
```
3단 구조: A 기본참조 / B 파생참조 / C 본편장면
출력: 영어 프롬프트 + 순번 매핑 + 파일명 규칙
```

### Part 5 — 영상제작
```
기준: 1 JSON = 1 클립 = 8초
8계정 운영표 (날짜/계정/순번/대본/이미지/JSON/상태)
```

### Part 6 — 오디오제작
```
TTS 도구 비종속 — Composer는 입력 패키지만 생성
파일명: S001_voice.wav
BGM: 파일명/분위기/시작/종료/볼륨/페이드/매핑표
```

### Part 7 — 숏폼파생
```
60초 이내 2~3개 (15/30/60 다중 아님)
구조: 훅 → 감정자극 → 반전 → 롱폼연결
```

### Part 8 — 최종조립
```
순번 기준 매칭 → CSV → JSON → 기존 CapCut 자동배치 프로그램
검수: 누락/중복/경로/길이/배치가능 여부
대표 버튼: 🎞️ CapCut 자동 배치 패키지 생성
```

---

## 🚨 가장 흔한 실수 (체크리스트)

```
□ 채널명을 하드코딩하지 않았는가? → get_channel_path() 사용
□ 백업을 만들었는가? → git tag + 파일 복사
□ py_compile 검증했는가?
□ Streamlit 실행 확인했는가?
□ 사용자에게 보고했는가?
□ APPROVED 없이 PUSH하지 않았는가?
□ 기존 Packet을 덮어쓰지 않았는가?
□ 수치를 임의로 작성하지 않았는가?
□ Profile YAML을 참조했는가?
```

---

## 🎯 현재 작업 우선순위

### 즉시 (이번 주)
```
1. profiles/ 폴더 + sage_mirror.yaml 작성
2. core/agents/ 폴더 + Conductor / Critic / Curator / Scout 4개 보조 에이전트
3. 옵시디언 경로 통일 (00_Raw_Data 변경 + 03_Logs 추가)
4. Part 1 Librarian 에이전트 리팩토링
   - 댓글 200개 수집
   - 주제 10개 보장
   - Comment Topic Packet 출력
```

### 다음 (이달)
```
5. Part 2 Architect
6. Part 3 Writer
7. 검수 루프 전면 적용
8. Packet 시스템 표준화
```

---

## 📞 보고 형식

작업 완료 시 다음 형식으로 보고:

```
## 작업 완료 보고

| 항목 | 결과 |
|---|---|
| 수정 파일 | {파일명} |
| 백업 위치 | {백업파일} |
| py_compile | OK / FAIL |
| 변경 내용 | {요약} |
| 다음 작업 | {제안} |
```

---

## 🔗 참조 문서

- **마스터 지침서**: `SAGE_V18_MASTER.md` ← 모든 의문 시 최우선
- **이 파일**: `CLAUDE_CODE_QUICK_GUIDE.md` ← 작업 시작 시 첫 참조

---

**파일 끝 — 항상 이 파일과 SAGE_V18_MASTER.md를 먼저 읽고 작업.**
