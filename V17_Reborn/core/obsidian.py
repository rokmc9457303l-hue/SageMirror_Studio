# -*- coding: utf-8 -*-
"""
core/obsidian.py
V17 Reborn 전용 옵시디언 저장 엔진
"""

import json
from datetime import datetime
from core.config import OBSIDIAN_BASE


def ensure_obsidian_dirs():
    folders = [
        "00_Raw",
        "01_Wiki",
        "02_Schema",
        "TopicMemory",
        "ResearchMemory",
        "PlanningMemory",
        "ScriptDrafts",
        "References",
        "Assets",
        "Episodes",
        "Logs",
    ]

    for folder in folders:
        (OBSIDIAN_BASE / folder).mkdir(parents=True, exist_ok=True)


def safe_filename(title: str) -> str:
    cleaned = "".join(
        c for c in title
        if c.isalnum() or c in " _-[]()"
    ).strip()
    return cleaned[:60] if cleaned else "untitled"


def save_raw(title: str, content: str, source: str = "V17 Reborn"):
    ensure_obsidian_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_filename(title)}_{ts}.md"
    path = OBSIDIAN_BASE / "00_Raw" / filename

    md = f"""# [RAW] {title}

## 메타
- 소스: {source}
- 저장시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 원본

{content}
"""

    path.write_text(md, encoding="utf-8")
    return str(path)


def save_wiki(title: str, content: str, tags=None, source: str = "V17 Reborn"):
    ensure_obsidian_dirs()
    tags = tags or []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_filename(title)}_{ts}.md"
    path = OBSIDIAN_BASE / "01_Wiki" / filename

    wiki_links = " ".join([f"[[{tag}]]" for tag in tags])

    md = f"""# [[{title}]]

## 핵심 요약
{content[:500]}

## 연결 개념
{wiki_links}

## 출처
[SOURCE: {source}]

## 생성일
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    path.write_text(md, encoding="utf-8")
    return str(path)


def save_schema(title: str, data: dict, folder: str = "02_Schema"):
    ensure_obsidian_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_filename(title)}_{ts}.json"
    path = OBSIDIAN_BASE / folder / filename

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def save_all(title: str, content: str, packet: dict = None, tags=None, source: str = "V17 Reborn"):
    raw_path = save_raw(title, content, source=source)
    wiki_path = save_wiki(title, content, tags=tags, source=source)

    schema_path = None
    if packet is not None:
        schema_path = save_schema(title, packet)

    return {
        "raw": raw_path,
        "wiki": wiki_path,
        "schema": schema_path,
    }