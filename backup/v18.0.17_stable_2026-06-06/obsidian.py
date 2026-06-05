# -*- coding: utf-8 -*-
"""
core/obsidian.py — 옵시디언 듀얼 엔진 (RAG + 듀얼 저장)
"""

from pathlib import Path
from datetime import datetime
from core.config import (
    OBSIDIAN_PATH, OBSIDIAN_CHANNEL, OBSIDIAN_UNIVERSAL,
    OBSIDIAN_SYSTEM, UNIVERSAL_CATEGORIES, PART_NAMES,
)


# ── 1. 범용 태그 자동 분류 ────────────────────────
TAG_KEYWORDS = {
    "감정":       ["고독","외로움","후회","불안","상실","슬픔","공허","두려움","희망","용기","분노"],
    "철학":       ["쇼펜하우어","니체","스토아","칸트","소크라테스","하이데거","실존주의","몽테뉴","파스칼"],
    "다크심리학": ["나르시시즘","가스라이팅","조종","트라우마","학습된 무기력","그림자자아"],
    "성경·신앙":  ["시편","잠언","전도서","욥기","이사야","로마서","기도","회복","은혜"],
    "심리학":     ["자존감","애착","번아웃","회복탄력성","로고테라피","실존적공허","프랭클","융"],
    "문학·에세이":["수상록","에세이","팡세","명상록","세네카","에픽테토스"],
    "고전소설":   ["도스토옙스키","톨스토이","헤세","카뮈","카프카","죄와벌","데미안","이방인"],
    "한국문학":   ["황석영","이청준","박경리","토지","윤동주","이상"],
    "인생단계":   ["은퇴","노년","중년","빈둥지","자녀독립","죽음준비","노후","4050","6070"],
    "역사·인물":  ["역사","인물","위인","문명","사건","시대","전쟁","리더십"],
    "경제·비즈니스":["경제","투자","은퇴","부업","재테크","창업","직업"],
    "건강·생활":  ["수면","운동","건강","노년","라이프","식습관","마음챙김"],
    "유튜브전략": ["제목","썸네일","후킹","알고리즘","시청지속","조회수","구독","shorts"],
    "채널운영":   ["채널","타겟","콘텐츠","포맷","페르소나","기획","벤치마킹"],
    "제작자료":   ["이미지","영상","나레이션","BGM","대본","프롬프트","CapCut","씬"],
    "출처자료":   ["논문","책","기사","PDF","연구","출처","웹","인용"],
}


def classify_tags(content: str, title: str = "") -> dict:
    text = (content + " " + title).lower()
    detected = {}
    for category, keywords in TAG_KEYWORDS.items():
        hits = [kw for kw in keywords if kw.lower() in text]
        if hits:
            detected[category] = hits[:6]
    return detected


# ── 2. 듀얼 저장 (규칙서 + 범용) ──────────────────
def save_dual(content: str, title: str, part_num: int = None,
              source_type: str = "결과물") -> dict:
    """규칙서 + 범용 2가지 형식 동시 저장"""
    saved_paths = {"규칙서": None, "범용": []}
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe  = "".join(c for c in title[:40] if c.isalnum() or c in " -_[]").strip()

    # 규칙서 형식 저장
    if part_num and part_num in PART_NAMES:
        folder = OBSIDIAN_CHANNEL / f"Part{part_num}_{PART_NAMES[part_num]}"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{safe}_{ts}.md"
        md = _build_rules_format(title, content, part_num, today, source_type)
        path.write_text(md, encoding="utf-8")
        saved_paths["규칙서"] = str(path)

    # 범용 형식 저장 (해당 카테고리들에)
    tags = classify_tags(content, title)
    for category, keywords in tags.items():
        folder = OBSIDIAN_UNIVERSAL / category
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{safe}_{ts}.md"
        md = _build_universal_format(title, content, category, keywords, today, part_num)
        path.write_text(md, encoding="utf-8")
        saved_paths["범용"].append(str(path))

    return saved_paths


def _build_rules_format(title, content, part_num, today, source_type):
    return f"""# [[{title}]]

## 📌 핵심 요약
(작성 필요)

## 🎯 핵심 감정
(작성 필요)

## 📖 핵심 내용

{content}

## 💡 대본 활용 포인트
(작성 필요)

## 🔗 연결 개념
(자동 추출)

## 📚 출처
[SOURCE: Part {part_num} {PART_NAMES.get(part_num, '')}]

## 다음 파트 전달 메모
(자동 생성)

## 생성일
{today}
"""


def _build_universal_format(title, content, category, keywords, today, part_num):
    hashtags = " ".join([f"#{kw.replace(' ', '_')}" for kw in keywords])
    wiki_links = " ".join([f"[[{kw}]]" for kw in keywords])
    return f"""# {title}

## 메타 정보
- **카테고리**: {category}
- **출처 파트**: Part {part_num or '?'} {PART_NAMES.get(part_num, '')}
- **생성일**: {today}

## 본문

{content}

## 키워드 링크
{wiki_links}

## 해시 태그
{hashtags}
"""


# ── 3. RAG 검색 ───────────────────────────────────
def search_rag(query: str, max_files: int = 5, max_chars: int = 500,
               search_folders: list = None) -> str:
    """옵시디언 키워드 검색 → RAG 컨텍스트 반환"""
    if not OBSIDIAN_PATH.exists():
        return ""
    
    search_paths = []
    if search_folders:
        for folder in search_folders:
            search_paths.append(OBSIDIAN_PATH / folder)
    else:
        search_paths = [OBSIDIAN_CHANNEL, OBSIDIAN_UNIVERSAL]

    keywords = [w for w in query.lower().split() if len(w) > 1][:8]
    if not keywords:
        return ""

    scored = []
    for base_path in search_paths:
        if not base_path.exists(): continue
        for md_file in base_path.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
                score = sum(text.lower().count(kw) for kw in keywords)
                if score > 0:
                    scored.append((score, md_file, text))
            except Exception:
                continue

    scored.sort(key=lambda x: x[0], reverse=True)
    parts = []
    for _, path, text in scored[:max_files]:
        parts.append(f"[{path.parent.name}/{path.stem}]\n{text[:max_chars]}")
    return "\n\n".join(parts)



# ═══════════════════════════════════════════════════════════
# v18.0.17 — 3계층 분류 시스템 (universal + channel + production)
# JSON 키워드 사전: prompts/channel_keywords/*.json
# ═══════════════════════════════════════════════════════════

from pathlib import Path as _Path
import json as _json
from functools import lru_cache as _lru_cache

_KEYWORDS_DIR = _Path(__file__).parent.parent / "prompts" / "channel_keywords"


@_lru_cache(maxsize=1)
def load_keywords_v2():
    """3계층 키워드 사전 로드. JSON 파일이 바뀌면 reload_keywords_v2() 호출."""
    result = {"universal": {}, "production": {}, "channels": {}}
    if not _KEYWORDS_DIR.exists():
        return result
    for path in _KEYWORDS_DIR.glob("*.json"):
        try:
            data = _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        scope = data.get("scope")
        if scope == "universal":
            result["universal"] = data.get("categories", {})
        elif scope == "production":
            result["production"] = data.get("categories", {})
        elif scope == "channel":
            if not data.get("enabled"):
                continue
            ch_id = data.get("channel_id")
            if not ch_id:
                continue
            result["channels"][ch_id] = {
                "concept": data.get("concept", ""),
                "drive_folder": data.get("drive_folder"),
                "domains": data.get("domains", {}),
            }
    return result


def reload_keywords_v2():
    """키워드 캐시 무효화. JSON 파일을 외부에서 수정한 후 호출."""
    load_keywords_v2.cache_clear()


def classify_3layer(content, title="", channel_id=None):
    """3계층 분류. Returns {universal, channel, production} dict-of-dicts."""
    text = (str(content or "") + " " + str(title or "")).lower()
    kw = load_keywords_v2()
    out = {"universal": {}, "channel": {}, "production": {}}

    for cat, kws in kw["universal"].items():
        hits = [k for k in kws if k.lower() in text]
        if hits:
            out["universal"][cat] = hits[:6]

    if channel_id and channel_id in kw["channels"]:
        for cat, kws in kw["channels"][channel_id]["domains"].items():
            hits = [k for k in kws if k.lower() in text]
            if hits:
                out["channel"][cat] = hits[:6]

    for cat, kws in kw["production"].items():
        hits = [k for k in kws if k.lower() in text]
        if hits:
            out["production"][cat] = hits[:6]

    return out


def get_channel_by_drive_folder(folder_name):
    """Google Drive 폴더명으로 channel_id 찾기. 없으면 None."""
    if not folder_name:
        return None
    kw = load_keywords_v2()
    for ch_id, info in kw["channels"].items():
        if info.get("drive_folder") == folder_name:
            return ch_id
    return None


def list_active_channels():
    """현재 활성화된 채널 목록. [{channel_id, drive_folder, concept}, ...]"""
    kw = load_keywords_v2()
    return [
        {
            "channel_id": cid,
            "drive_folder": info.get("drive_folder"),
            "concept": info.get("concept", ""),
        }
        for cid, info in kw["channels"].items()
    ]


def format_tags_3layer(classification, channel_id=None):
    """3계층 분류 결과를 markdown 섹션 문자열로 포맷."""
    def _fmt(d):
        if not d:
            return "(없음)"
        parts = []
        for cat, kws in d.items():
            tag_cat = cat.replace(" ", "_").replace("·", "_")
            tag_kws = "_".join([k.replace(" ", "_") for k in kws[:2]])
            parts.append(f"#{tag_cat}/{tag_kws}")
        return " ".join(parts)

    u = classification.get("universal", {})
    c = classification.get("channel", {})
    p = classification.get("production", {})

    if not (u or c or p):
        u = {"미분류": ["미분류"]}

    return (
        f"### 범용 카테고리\n{_fmt(u)}\n\n"
        f"### 채널 도메인 ({channel_id or '미지정'})\n{_fmt(c)}\n\n"
        f"### 제작 메타\n{_fmt(p)}"
    )
