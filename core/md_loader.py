# -*- coding: utf-8 -*-
"""
core/md_loader.py — MD 파일 로더

- mtime 기반 캐시: 파일 저장 즉시 반영 (TTL 대기 없음)
- 변수 치환: {{CHANNEL_NAME}} 등 템플릿 변수 즉시 렌더링
"""

from pathlib import Path

# mtime 기반 캐시: {str(path): (mtime_float, content_str)}
_md_cache: dict = {}


def load_md(path: str) -> str:
    """MD 파일 로드 (mtime 캐시 — 파일 변경 즉시 반영)"""
    try:
        p = Path(path)
        mtime = p.stat().st_mtime
        cached = _md_cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        content = p.read_text(encoding="utf-8")
        _md_cache[path] = (mtime, content)
        return content
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


def compose_system_prompt(part: int, step: str = "", variables: dict = None) -> str:
    """
    에이전트 실행용 시스템 프롬프트 조립 (AGENT_ORCHESTRATION.md 5절 순서).

    순서:
      1. ANTI_HALLUCINATION.md
      2. SOURCE_CITATION.md
      3. Part N AGENT_PROTOCOL.md
      4. Part N MAIN_PROMPT.md  (변수 치환)
      5. Part N STEP_{step}.md  (step 지정 시)
    """
    variables = variables or {}
    sections = []

    anti  = load_shared_md("ANTI_HALLUCINATION.md")
    cite  = load_shared_md("SOURCE_CITATION.md")
    proto = load_part_md(part, "AGENT_PROTOCOL.md")
    main  = load_part_md(part, "MAIN_PROMPT.md")

    if anti:  sections.append(anti)
    if cite:  sections.append(cite)
    if proto: sections.append(proto)
    if main:  sections.append(main)

    if step:
        step_md = load_part_md(part, f"STEP_{step}.md")
        if step_md:
            sections.append(step_md)

    full = "\n\n---\n\n".join(sections)

    # {{변수}} 치환
    for key, val in variables.items():
        full = full.replace("{{" + key + "}}", str(val))

    return full


def get_full_context(part: int, profile: dict = None) -> str:
    """
    Profile YAML 변수를 자동 주입한 완성된 시스템 컨텍스트 반환.
    에이전트 execute() 에서 self.call_ai() 호출 전 사용.
    """
    if profile is None:
        try:
            from core.profile_loader import load_current_profile
            profile = load_current_profile()
        except Exception:
            profile = {}

    variables = {
        "CHANNEL_NAME":          profile.get("channel_name", ""),
        "TARGET_AUDIENCE":       profile.get("target_audience", ""),
        "TONE":                  profile.get("tone", ""),
        "NARRATOR_STYLE":        profile.get("narrator_style", ""),
        "VISUAL_STYLE":          profile.get("visual_style", ""),
        "PHILOSOPHY_ANCHOR":     ", ".join(profile.get("philosophy_anchor", [])),
        "TYPICAL_CATEGORIES":    ", ".join(profile.get("typical_categories", [])),
        "TYPICAL_TOPICS":        ", ".join(profile.get("typical_topics", [])),
        "FORBIDDEN_EXPRESSIONS": ", ".join(profile.get("forbidden_expressions", [])),
        "PREFERRED_EXPRESSIONS": ", ".join(profile.get("preferred_expressions", [])),
        "CORE_SYMBOLS":          ", ".join(profile.get("core_symbols", [])),
        "COLOR_PALETTE":         profile.get("color_palette", ""),
    }

    return compose_system_prompt(part, variables=variables)


def save_md(path: str, content: str, backup: bool = True) -> str:
    """
    MD 파일 저장 (mtime 캐시 무효화 + 자동 백업).

    Returns:
        backup_path (str) if backup=True, else ""
    """
    import datetime, shutil
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    backup_path = ""
    if backup and p.exists():
        from core.config import PROMPTS_PATH
        bk_dir = PROMPTS_PATH / "_backup"
        bk_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bk_name = f"{p.stem}_{ts}{p.suffix}"
        backup_path = str(bk_dir / bk_name)
        shutil.copy2(str(p), backup_path)

    p.write_text(content, encoding="utf-8")
    _md_cache.pop(path, None)       # 해당 파일만 캐시 제거
    _md_cache.pop(str(p), None)     # str 형식도 제거
    return backup_path
