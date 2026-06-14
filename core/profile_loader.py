# -*- coding: utf-8 -*-
"""
core/profile_loader.py — Channel Profile YAML 로더

흐름: 사이드바 채널 선택 → current_channel_profile 세션 저장 →
     profile_loader가 profiles/{key}.yaml 로드 →
     모든 에이전트가 이 Profile 참조
"""

from pathlib import Path
from core.state import get_state, set_state

PROFILES_DIR = Path(__file__).parent.parent / "profiles"


def _load_yaml(path: Path) -> dict:
    """YAML 파일 로드 (PyYAML 없으면 간이 파서)"""
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return _simple_yaml_parse(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _simple_yaml_parse(text: str) -> dict:
    """PyYAML 없을 때 단순 key: value 파싱 (리스트 지원)"""
    result = {}
    current_key = None
    current_list = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            if current_key and current_list is not None:
                current_list.append(stripped[2:].strip())
            continue

        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()

            if current_list is not None and current_key:
                result[current_key] = current_list

            if val == "" or val == "[]":
                current_key = key
                current_list = [] if val == "[]" else None
                if val == "[]":
                    result[key] = []
            else:
                current_key = None
                current_list = None
                result[key] = val

    if current_list is not None and current_key:
        result[current_key] = current_list

    return result


def save_yaml(path: Path, data: dict):
    """dict → YAML 파일 저장"""
    try:
        import yaml
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    except ImportError:
        lines = []
        for k, v in data.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{k}: {v}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_profile(channel_key: str) -> dict:
    """channel_key(파일 스텀)로 Profile 로드. 없으면 template 반환."""
    if not channel_key:
        return load_template()
    path = PROFILES_DIR / f"{channel_key}.yaml"
    if not path.exists():
        return load_template()
    return _load_yaml(path)


def load_current_profile() -> dict:
    """현재 세션의 Channel Profile 반환"""
    key = get_state("current_channel_profile", "sage_mirror")
    profile = load_profile(key)
    if not profile:
        return load_template()
    return profile


def load_template() -> dict:
    """빈 템플릿 반환"""
    path = PROFILES_DIR / "_template.yaml"
    if path.exists():
        return _load_yaml(path)
    return {}


def list_available_profiles() -> list:
    """사용 가능한 Profile 목록 [{key, name}, ...]"""
    if not PROFILES_DIR.exists():
        return [{"key": "sage_mirror", "name": "현자의거울"}]
    result = []
    for p in sorted(PROFILES_DIR.glob("*.yaml")):
        if p.stem.startswith("_"):
            continue
        data = _load_yaml(p)
        result.append({
            "key": p.stem,
            "name": data.get("channel_name", p.stem),
        })
    return result


def select_profile(channel_key: str):
    """프로필 선택 → 세션 상태 업데이트"""
    profile = load_profile(channel_key)
    set_state("current_channel_profile", channel_key)
    set_state("current_channel_name", profile.get("channel_name", channel_key))
    return profile


def save_new_profile(channel_key: str, profile_data: dict):
    """새 채널 Profile 저장"""
    PROFILES_DIR.mkdir(exist_ok=True)
    path = PROFILES_DIR / f"{channel_key}.yaml"
    save_yaml(path, profile_data)
    return str(path)
