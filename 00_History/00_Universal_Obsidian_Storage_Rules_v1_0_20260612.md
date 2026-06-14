# 범용 옵시디언 저장 규칙서 v1.0
# Universal Obsidian Storage Rules
# 2026-06-12 | Sage Mirror Studio V17

---

## 1. 적용 범위

이 규칙은 아래 모든 도구가 `00_Obsidian` Vault에 자료를 저장할 때 공통으로 적용된다.

- Sage Mirror Studio V17 (Streamlit 앱)
- Claude Code / Antigravity
- 기타 자동화 스크립트

---

## 2. Vault 구조

```
C:\SageMirror_Production\00_Obsidian\
├── 00_Raw/              # 원본 자료 보존
│   └── Conversations/   # 대화 원문 (물리 원본 없는 자료)
│       └── YYYY/MM/     # 연/월 단위
├── 01_Wiki/             # Markdown 지식 노트
│   └── <범용카테고리>/   # 내용 기반 분류
├── 02_Schema/           # JSON 구조화 메타데이터
│   └── Items/           # 개별 항목
├── 03_Logs/             # 저장 로그
│   ├── Import/          # 성공 로그 (YYYY-MM-DD.jsonl)
│   ├── Errors/          # 실패 로그
│   └── Duplicates/      # 중복 감지 로그
```

---

## 3. Raw — 원본 보존

### 원칙
- 원본 자료를 **변경하지 않고** 보존한다
- PDF는 PDF 그대로, DOCX는 DOCX 그대로 저장한다
- TXT, MD, CSV, JSON, HTML도 원본 그대로 저장한다
- 웹 검색, AI 대화처럼 물리적 원본이 없는 자료만 원문 MD 또는 JSON으로 저장한다
- 요약, 분류, 해석을 Raw 원본에 삽입하지 않는다
- 기존 원본을 덮어쓰지 않는다

### 중복 방지
- 저장 전 SHA256 해시로 기존 파일과 비교한다
- 동일 해시가 존재하면 파일을 생성하지 않고 `03_Logs/Duplicates`에 기록한다

### 파일명 규칙
```
원본대화_YYYYMMDD_HHMMSS_<해시앞8자>.md
```

---

## 4. Wiki — 지식 노트

### 형식: Markdown

```markdown
# <제목>

## 핵심 요약
- (한두 문장)

## 핵심 내용
(본문에서 추출한 주요 내용)

## 주요 주장
- (본문의 핵심 주장 목록)

## 범용 카테고리
- <내용 기반 카테고리>

## 태그
[[태그1]] [[태그2]] [[태그3]]

## 키워드
#키워드1 #키워드2 #키워드3

## 관련 개념
[[개념1]] [[개념2]]

## 출처
- 소스 유형: <AI 대화 / 웹 검색 / 파일 업로드>
- 모델: <사용된 모델명>
- Raw 원본: [[00_Raw/경로/파일명]]

## 메타
- 생성일: YYYY-MM-DD HH:MM:SS
- 수정일: YYYY-MM-DD HH:MM:SS
```

### 분류 원칙
- 카테고리, 태그, 키워드는 **원문 내용에서 추출**한다
- 특정 프로젝트 규칙으로 강제 분류하지 않는다

---

## 5. Schema — 구조화 메타데이터

### 형식: JSON

```json
{
  "source_id": "고유식별자",
  "title": "제목",
  "source_type": "AI대화 | 웹검색 | 파일업로드 | 수동입력",
  "categories": ["범용카테고리1", "범용카테고리2"],
  "tags": ["태그1", "태그2"],
  "keywords": ["키워드1", "키워드2"],
  "language": "ko",
  "raw_path": "00_Raw/.../파일명",
  "wiki_path": "01_Wiki/.../파일명",
  "content_hash": "SHA256 해시",
  "original_url": "",
  "index_status": "indexed",
  "created_by": "v17_right_research",
  "created_at": "YYYY-MM-DD HH:MM:SS",
  "updated_at": "YYYY-MM-DD HH:MM:SS"
}
```

### 필드 설명
- `created_by`: 어떤 도구가 저장했는지 기록용. 검색 제한 조건으로 사용하지 않는다.
- `content_hash`: 중복 탐지용 SHA256 해시
- `categories`: 원문 내용 기반 범용 카테고리

---

## 6. 범용 카테고리

자료 내용에 따라 아래에서 선택한다. 복수 선택 가능.

| 카테고리 | 설명 |
|---------|------|
| 심리학 | 심리, 자존감, 트라우마, 인지, 행동 |
| 철학 | 쇼펜하우어, 스토아, 실존주의, 동양철학 |
| 종교 | 성경, 불교, 신앙, 영성 |
| 역사 | 인물, 사건, 시대, 문명 |
| 과학 | 물리, 화학, 생물, 수학, 천문 |
| 기술 | AI, 프로그래밍, 소프트웨어, 하드웨어 |
| 경제·비즈니스 | 투자, 창업, 시장, 재무 |
| 사회 | 정치, 문화, 인구, 도시 |
| 교육 | 학습, 교수법, 자기계발, 독서 |
| 건강 | 의학, 운동, 영양, 수면, 노화 |
| 예술·문학 | 소설, 시, 영화, 음악, 미술 |
| 미디어·콘텐츠 | 유튜브, 블로그, 팟캐스트, SNS |
| 법률 | 법, 규제, 계약, 지적재산 |
| 환경 | 기후, 생태, 에너지, 지속가능 |
| 기타 | 위 카테고리에 해당하지 않는 자료 |

필요하면 새 범용 카테고리를 추가할 수 있다.

---

## 7. 금지 사항

다음 내용을 **모든 자료에 강제로 삽입하지 않는다**:

- 현자의 거울
- @Protagonist
- Part 1~8
- 4070
- 쇼펜하우어 (자료가 실제로 쇼펜하우어를 다룰 때만)
- 성경 (자료가 실제로 성경을 다룰 때만)
- 유튜브 대본

자료가 실제로 해당 주제를 다룰 때만 카테고리·태그·키워드로 추가한다.

---

## 8. 로그

### Import 로그 (성공)
```json
{"timestamp": "...", "action": "import", "raw_path": "...", "wiki_path": "...", "schema_path": "...", "content_hash": "...", "created_by": "..."}
```

### Duplicates 로그 (중복)
```json
{"timestamp": "...", "action": "duplicate_skip", "content_hash": "...", "existing_path": "...", "created_by": "..."}
```

### Errors 로그 (실패)
```json
{"timestamp": "...", "action": "error", "error": "...", "created_by": "..."}
```

---

## 9. 버전

- v1.0 — 2026-06-12 — 최초 생성
