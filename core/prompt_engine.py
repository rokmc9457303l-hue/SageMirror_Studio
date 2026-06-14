# -*- coding: utf-8 -*-
"""
core/prompt_engine.py — 프롬프트 엔진 (Task 27)

원칙: 시스템 코드는 채널/주제를 모른다.
모든 채널/주제 결정은 MD 파일에서만.
이 엔진은 MD 파일을 읽어 실행하는 엔진.
"""

from pathlib import Path
from core.md_loader import load_md, render_md, load_part_md, load_agent_md, load_shared_md, load_channel_md
from core.config import PROMPTS_PATH


def _get_current_channel_key() -> str:
    try:
        import streamlit as st
        return st.session_state.get("current_channel_profile", "")
    except Exception:
        return ""


def _load_channel_context(channel_key: str = None) -> dict:
    """현재 채널 Profile → 치환 변수 딕셔너리"""
    try:
        from core.profile_loader import load_profile, load_current_profile
        p = load_profile(channel_key) if channel_key else load_current_profile()
        return {
            "CHANNEL_NAME":          p.get("channel_name", ""),
            "TARGET_AUDIENCE":       p.get("target_audience", ""),
            "TONE":                  p.get("tone", ""),
            "VISUAL_STYLE":          p.get("visual_style", ""),
            "TYPICAL_CATEGORIES":    ", ".join(p.get("typical_categories", [])),
            "FORBIDDEN_EXPRESSIONS": ", ".join(p.get("forbidden_expressions", [])),
            "PREFERRED_EXPRESSIONS": ", ".join(p.get("preferred_expressions", [])),
            "PHILOSOPHY_ANCHOR":     ", ".join(p.get("philosophy_anchor", [])),
            "NARRATOR_STYLE":        p.get("narrator_style", ""),
            "CORE_SYMBOLS":          ", ".join(p.get("core_symbols", [])),
        }
    except Exception:
        return {}


def compose_system_prompt(part_num: int, channel_key: str = None) -> str:
    """
    Part N의 시스템 프롬프트 조립:
    채널 IDENTITY.md + AGENT_PROTOCOL.md + shared 규칙 + MAIN_PROMPT.md
    """
    channel_key = channel_key or _get_current_channel_key()
    ctx = _load_channel_context(channel_key)

    parts = []

    # 1. 채널 정체성
    identity = render_md(
        str(PROMPTS_PATH / "channels" / channel_key / "IDENTITY.md"),
        ctx
    ) if channel_key else ""
    if identity:
        parts.append(f"# 채널 정체성\n{identity}")

    # 2. 공통 규칙 (anti-hallucination, source-citation)
    for fname in ("ANTI_HALLUCINATION.md", "SOURCE_CITATION.md", "OUTPUT_FORMAT.md",
                  "CHANNEL_IDENTITY.md", "SYSTEM_PRINCIPLES.md"):
        shared = load_shared_md(fname)
        if shared:
            parts.append(shared)

    # 3. 에이전트 프로토콜
    protocol = load_part_md(part_num, "AGENT_PROTOCOL.md")
    if protocol:
        parts.append(render_md_text(protocol, ctx))

    # 4. 메인 프롬프트
    main_p = load_part_md(part_num, "MAIN_PROMPT.md")
    if main_p:
        parts.append(render_md_text(main_p, ctx))

    # 5. 레거시 프롬프트 파일 (기존 part{N}_*.md)
    legacy_files = list(PROMPTS_PATH.glob(f"part{part_num}_*.md"))
    for lf in legacy_files:
        try:
            legacy = lf.read_text(encoding="utf-8")
            if legacy:
                parts.append(legacy)
        except Exception:
            pass

    return "\n\n---\n\n".join(p for p in parts if p.strip())


def render_md_text(text: str, variables: dict) -> str:
    """텍스트 내 {{변수}} 치환"""
    if not variables:
        return text
    for key, val in variables.items():
        text = text.replace("{{" + key + "}}", str(val))
    return text


def execute_step(part_num: int, step: str, channel_key: str = None, ctx: dict = None) -> str:
    """
    특정 스텝 실행:
    prompts/parts/part{N}/STEP_{step}.md 로드 → 변수 치환 → 반환
    """
    channel_key = channel_key or _get_current_channel_key()
    variables = _load_channel_context(channel_key)
    if ctx:
        variables.update(ctx)

    step_path = PROMPTS_PATH / "parts" / f"part{part_num}" / f"STEP_{step}.md"
    step_md = load_md(str(step_path))
    if not step_md:
        return f"[스텝 없음: part{part_num}/STEP_{step}.md]"
    return render_md_text(step_md, variables)


def get_available_steps(part_num: int) -> list:
    """Part N의 사용 가능한 스텝 목록 [{name, path}]"""
    folder = PROMPTS_PATH / "parts" / f"part{part_num}"
    if not folder.exists():
        return []
    steps = []
    for f in sorted(folder.glob("STEP_*.md")):
        step_name = f.stem.replace("STEP_", "")
        steps.append({"name": step_name, "path": str(f)})
    return steps


def get_agent_prompt(agent_name: str, channel_key: str = None, extra: dict = None) -> str:
    """에이전트 MD 로드 + 채널 컨텍스트 주입"""
    channel_key = channel_key or _get_current_channel_key()
    variables = _load_channel_context(channel_key)
    if extra:
        variables.update(extra)
    agent_md = load_agent_md(agent_name)
    if not agent_md:
        return ""
    return render_md_text(agent_md, variables)


def execute_part(part_num: int, user_input: str, channel_key: str = None) -> str:
    """
    Part 전체 실행 (AI 호출):
    시스템 프롬프트 조립 → AI 호출 → 결과 반환
    """
    from core.brain import call_model
    system_prompt = compose_system_prompt(part_num, channel_key)
    if not system_prompt:
        return f"[Part {part_num} 프롬프트 없음]"
    return call_model(user_input, system_prompt=system_prompt)
