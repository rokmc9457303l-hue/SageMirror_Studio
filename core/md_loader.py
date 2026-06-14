# -*- coding: utf-8 -*-
"""
core/md_loader.py — MD 파일 로더 (Task 34)

- 1분 TTL 캐시: 파일 편집 후 최대 1분 내 자동 반영 (앱 재시작 불필요)
- 변수 치환: {{CHANNEL_NAME}} 등 템플릿 변수 즉시 렌더링
"""

import streamlit as st
from pathlib import Path


@st.cache_data(ttl=60, show_spinner=False)
def load_md(path: str) -> str:
    """MD 파일 로드 (60초 캐시 — 편집 후 1분 내 자동 반영)"""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except Exception as e:
        return f"[MD 로드 오류: {e}]"


def render_md(path: str, variables: dict = None) -> str:
    """MD 로드 + {{변수}} 치환"""
    text = load_md(path)
    if not text or not variables:
        return text
    for key, val in variables.items():
        text = text.replace("{{" + key + "}}", str(val))
    return text


def load_channel_md(channel_key: str, filename: str) -> str:
    """prompts/channels/{channel_key}/{filename} 로드"""
    from core.config import PROMPTS_PATH
    path = PROMPTS_PATH / "channels" / channel_key / filename
    return load_md(str(path))


def load_part_md(part_num: int, filename: str) -> str:
    """prompts/parts/part{N}/{filename} 로드"""
    from core.config import PROMPTS_PATH
    path = PROMPTS_PATH / "parts" / f"part{part_num}" / filename
    return load_md(str(path))


def load_agent_md(agent_name: str) -> str:
    """prompts/agents/{AGENT_NAME}.md 로드"""
    from core.config import PROMPTS_PATH
    path = PROMPTS_PATH / "agents" / f"{agent_name.upper()}.md"
    return load_md(str(path))


def load_shared_md(filename: str) -> str:
    """prompts/shared/{filename} 로드"""
    from core.config import PROMPTS_PATH
    path = PROMPTS_PATH / "shared" / filename
    return load_md(str(path))


def list_channel_mds(channel_key: str) -> list:
    """채널 폴더 내 MD 파일 목록 반환 [{name, path, size}]"""
    from core.config import PROMPTS_PATH
    folder = PROMPTS_PATH / "channels" / channel_key
    if not folder.exists():
        return []
    files = []
    for f in sorted(folder.glob("*.md")):
        files.append({
            "name": f.name,
            "path": str(f),
            "size": f.stat().st_size,
        })
    return files


def list_all_prompts() -> dict:
    """편집 UI용: 모든 프롬프트 MD 파일 트리 반환"""
    from core.config import PROMPTS_PATH
    tree = {}
    for category in ("parts", "agents", "shared", "channels"):
        folder = PROMPTS_PATH / category
        if not folder.exists():
            continue
        files = []
        for f in sorted(folder.rglob("*.md")):
            rel = str(f.relative_to(PROMPTS_PATH))
            files.append({"name": f.name, "rel": rel, "path": str(f)})
        if files:
            tree[category] = files
    return tree


def save_md(path: str, content: str):
    """MD 파일 저장 후 캐시 무효화"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    load_md.clear()  # 캐시 즉시 클리어
