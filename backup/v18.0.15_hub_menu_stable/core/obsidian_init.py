# -*- coding: utf-8 -*-
"""
core/obsidian_init.py — 옵시디언 폴더 구조 자동 초기화

3층 도서관 구조 자동 생성:
- 00_Raw    : 원본 보존
- 10_Wiki   : 정제 지식
- 20_Schema : 구조화 DB
"""

from pathlib import Path
from core.config import OBSIDIAN_SYSTEM, OBSIDIAN_CHANNEL, OBSIDIAN_UNIVERSAL


# ── 3층 폴더 구조 정의 ────────────────────────────
RAW_SUBFOLDERS = [
    "PDF",
    "YouTube_스크립트",
    "웹페이지",
    "이미지_OCR",
    "영상_전사",
    "GoogleDrive",
    "GoogleDocs",
    "외부리서치",
    "파일_업로드",
    "URL_가져오기",
]

WIKI_SUBFOLDERS = [
    "인물",          # 쇼펜하우어·니체·융·프랭클·몽테뉴
    "개념",          # 그림자자아·로고테라피·기승전결
    "작품",          # 의지와표상·죽음의수용소·데미안
    "인용",          # 검증된 명언 모음
    "주제",          # 고독·후회·상실·공허
    "성경",          # 시편·잠언·전도서·욥기
    "심리학",        # 자존감·애착·번아웃
    "문학",          # 고전소설·에세이·한국문학
    "철학",          # 학파·시대·계보
    "유튜브",        # 채널 분석·전략
]

SCHEMA_FILES = {
    "인용DB.md":     "검증된 인용문 데이터베이스",
    "출처DB.md":     "책·논문·영상 출처 메타",
    "키워드맵.md":   "개념 간 관계 맵",
    "벤치마킹DB.md": "유튜브 스크립트 분석 DB",
    "인물DB.md":     "인물 정보 데이터베이스",
    "에피소드DB.md": "제작한 영상 에피소드 기록",
}


# ── 폴더 자동 생성 ────────────────────────────────
def initialize_obsidian_structure() -> dict:
    """옵시디언 전체 폴더 구조 자동 생성"""
    
    created = {"raw": [], "wiki": [], "schema": [], "skipped": []}
    
    # 1. 00_Raw 폴더 (원본 보존)
    raw_base = OBSIDIAN_SYSTEM / "00_Raw"
    raw_base.mkdir(parents=True, exist_ok=True)
    
    for sub in RAW_SUBFOLDERS:
        folder = raw_base / sub
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            _create_readme(folder, "원본 자료 보존", sub)
            created["raw"].append(sub)
        else:
            created["skipped"].append(f"Raw/{sub}")
    
    # 2. 10_Wiki 폴더 (정제 노트)
    wiki_base = OBSIDIAN_SYSTEM / "10_Wiki"
    wiki_base.mkdir(parents=True, exist_ok=True)
    
    for sub in WIKI_SUBFOLDERS:
        folder = wiki_base / sub
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            _create_wiki_index(folder, sub)
            created["wiki"].append(sub)
        else:
            created["skipped"].append(f"Wiki/{sub}")
    
    # 3. 20_Schema 폴더 (구조화 DB)
    schema_base = OBSIDIAN_SYSTEM / "20_Schema"
    schema_base.mkdir(parents=True, exist_ok=True)
    
    for filename, description in SCHEMA_FILES.items():
        file_path = schema_base / filename
        if not file_path.exists():
            _create_schema_template(file_path, filename, description)
            created["schema"].append(filename)
        else:
            created["skipped"].append(f"Schema/{filename}")
    
    # 4. 기타 시스템 폴더
    for sub in ["Chat", "Logs", "References", "WikiNotes"]:
        folder = OBSIDIAN_SYSTEM / sub
        folder.mkdir(parents=True, exist_ok=True)
    
    return created


def _create_readme(folder: Path, purpose: str, category: str):
    """폴더에 README 자동 생성"""
    readme = folder / "_README.md"
    content = f"""# {category} 폴더

## 목적
{purpose}

## 저장 형식
원본 그대로 보존 (가공 없음)

## 자동 저장
앱이 자동으로 이곳에 자료를 저장합니다.
- 형식: Markdown (.md)
- 메타: YAML frontmatter
- 명명: 시각_제목.md

## 카테고리
{category}
"""
    readme.write_text(content, encoding="utf-8")


def _create_wiki_index(folder: Path, category: str):
    """Wiki 폴더에 인덱스 생성"""
    index = folder / "_인덱스.md"
    content = f"""# {category} 위키 인덱스

## 개요
{category} 카테고리의 정제된 지식 노트 모음

## 위키 노트 형식
- [[위키링크]]로 다른 노트와 연결
- 핵심 요약 + 출처 표기
- 관련 개념 자동 연결

## 자동 진화
앱이 외부 자료에서 핵심 추출하여
이 폴더의 위키 노트를 자동 생성·업데이트합니다.
"""
    index.write_text(content, encoding="utf-8")


def _create_schema_template(file_path: Path, filename: str, description: str):
    """Schema DB 템플릿 생성"""
    
    if filename == "인용DB.md":
        content = """---
type: 인용DB
fields: [인용문, 출처, 페이지, 저자, 검증여부, 카테고리, 키워드]
---

# 인용 데이터베이스

검증된 인용문 모음. YAML frontmatter로 구조화됨.

## 신규 인용 추가 형식

```yaml
- 인용문: "이것은 인용문입니다"
  출처: 책제목
  페이지: 123
  저자: 저자이름
  검증여부: true
  카테고리: 철학
  키워드: [고독, 의지]
```

## 자동 추가
앱이 외부 자료에서 인용문 발견 시 자동 추가.
검증 통과한 것만 등재.
"""
    
    elif filename == "출처DB.md":
        content = """---
type: 출처DB
fields: [제목, 저자, 출판년도, 종류, ISBN_URL, 검증]
---

# 출처 데이터베이스

책·논문·영상 등 모든 출처 메타데이터.

## 자동 추가
인용 발견 시 출처도 자동 등재.
"""
    
    elif filename == "키워드맵.md":
        content = """---
type: 키워드맵
fields: [개념, 상위개념, 하위개념, 관련개념, 연관강도]
---

# 키워드 관계 맵

개념 간 의미적 관계 구조화.

## 예시
```yaml
- 개념: 고독
  상위개념: 감정
  관련개념: [후회, 상실, 공허]
  연관강도: 0.85
```
"""
    
    elif filename == "벤치마킹DB.md":
        content = """---
type: 벤치마킹DB
fields: [채널명, URL, 영상제목, 조회수, 후킹방식, 구조패턴, 핵심키워드, 감정곡선]
---

# YouTube 벤치마킹 데이터베이스

분석한 유튜브 영상들의 구조·전략 DB.

## 자동 추가
우측 작업창에서 유튜브 URL 입력 시 자동 분석·등재.
"""
    
    else:
        content = f"""---
type: {filename.replace('.md', '')}
description: {description}
---

# {filename.replace('.md', '')}

{description}

자동으로 업데이트되는 구조화 데이터베이스입니다.
"""
    
    file_path.write_text(content, encoding="utf-8")


# ── 상태 조회 ─────────────────────────────────────
def get_structure_status() -> dict:
    """현재 옵시디언 구조 상태"""
    status = {
        "raw":    {"exists": False, "subfolders": 0, "files": 0},
        "wiki":   {"exists": False, "subfolders": 0, "files": 0},
        "schema": {"exists": False, "files": 0},
    }
    
    raw_base = OBSIDIAN_SYSTEM / "00_Raw"
    if raw_base.exists():
        status["raw"]["exists"] = True
        status["raw"]["subfolders"] = len([d for d in raw_base.iterdir() if d.is_dir()])
        status["raw"]["files"] = sum(1 for _ in raw_base.rglob("*.md"))
    
    wiki_base = OBSIDIAN_SYSTEM / "10_Wiki"
    if wiki_base.exists():
        status["wiki"]["exists"] = True
        status["wiki"]["subfolders"] = len([d for d in wiki_base.iterdir() if d.is_dir()])
        status["wiki"]["files"] = sum(1 for _ in wiki_base.rglob("*.md"))
    
    schema_base = OBSIDIAN_SYSTEM / "20_Schema"
    if schema_base.exists():
        status["schema"]["exists"] = True
        status["schema"]["files"] = len(list(schema_base.glob("*.md")))
    
    return status
