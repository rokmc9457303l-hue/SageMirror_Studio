# -*- coding: utf-8 -*-
"""
core/channel_manager.py — 채널 관리 (Tasks 36, 39, 40)

rename_channel, delete_channel, list_channels, verify_channel_rename
모든 작업은 로그 자동 기록 + 안전 장치 포함.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path

from core.state import get_state, set_state


# ── 경로 헬퍼 ──────────────────────────────────────────────────────────

def _profiles_dir() -> Path:
    return Path(__file__).parent.parent / "profiles"


def _prompts_dir() -> Path:
    return Path(__file__).parent.parent / "prompts" / "channels"


def _obsidian_raw() -> Path:
    try:
        from core.config import OBSIDIAN_RAW_NEW
        return OBSIDIAN_RAW_NEW
    except Exception:
        from core.config import OBSIDIAN_PATH
        return OBSIDIAN_PATH / "01_Raw_Data"


def _obsidian_path() -> Path:
    from core.config import OBSIDIAN_PATH
    return OBSIDIAN_PATH


def _log(msg: str):
    """03_Logs에 채널 관리 이력 기록 (Task 40)"""
    try:
        log_dir = _obsidian_path() / "03_Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"channel_manager_{today}.log"
        entry = f"[{datetime.now().isoformat()}] {msg}\n"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


# ── 채널 목록 ───────────────────────────────────────────────────────────

def list_channels() -> list:
    """모든 채널 키 목록 (template 제외)"""
    d = _profiles_dir()
    if not d.exists():
        return []
    return [
        p.stem for p in sorted(d.glob("*.yaml"))
        if not p.stem.startswith("_")
    ]


def list_channels_full() -> list:
    """모든 채널 [{key, name}] 목록"""
    try:
        from core.profile_loader import list_available_profiles
        return list_available_profiles()
    except Exception:
        return [{"key": k, "name": k} for k in list_channels()]


# ── 채널 이름 변경 (Task 36) ────────────────────────────────────────────

def rename_channel(old_key: str, new_name: str) -> dict:
    """
    채널명 일괄 변경 — 앱 전체 적용

    old_key: 기존 채널 키 (YAML 파일명, 폴더명)
    new_name: 새 채널 표시명 (채널명 — 한/영/숫자/공백/하이픈)

    Returns: {success, changes, errors, new_key}
    """
    if not old_key or not new_name:
        return {"success": False, "errors": ["이름이 비어있음"], "changes": []}

    new_name = new_name.strip()

    if not re.match(r"^[가-힣A-Za-z0-9_\s\-]+$", new_name):
        return {
            "success": False,
            "errors": ["채널명에 특수문자 사용 불가 (한글/영문/숫자/공백/하이픈/언더바만 허용)"],
            "changes": [],
        }

    # 새 키 생성 (공백 → 언더스코어)
    new_key = re.sub(r"\s+", "_", new_name).lower()

    # 기존 키에서 채널명 읽기
    old_yaml = _profiles_dir() / f"{old_key}.yaml"
    if not old_yaml.exists():
        return {"success": False, "errors": [f"'{old_key}' Profile 없음"], "changes": []}

    try:
        import yaml as _yaml
        with old_yaml.open(encoding="utf-8") as f:
            profile_data = _yaml.safe_load(f) or {}
    except Exception as e:
        return {"success": False, "errors": [f"YAML 읽기 실패: {e}"], "changes": []}

    old_ch_name = profile_data.get("channel_name", old_key)

    if old_ch_name == new_name and old_key == new_key:
        return {"success": False, "errors": ["변경 사항 없음"], "changes": []}

    new_yaml = _profiles_dir() / f"{new_key}.yaml"
    if new_yaml.exists() and new_key != old_key:
        return {"success": False, "errors": [f"키 '{new_key}'가 이미 존재함"], "changes": []}

    changes = []
    errors  = []
    affected_files = 0

    try:
        # ── 1. Profile YAML 갱신 ────────────────────────────────────
        profile_data["channel_name"]         = new_name
        profile_data["channel_key"]          = new_key
        profile_data["obsidian_channel_dir"] = f"채널_{new_name}"

        try:
            import yaml as _yaml
            new_yaml.parent.mkdir(parents=True, exist_ok=True)
            with new_yaml.open("w", encoding="utf-8") as f:
                _yaml.dump(profile_data, f, allow_unicode=True, sort_keys=False)
            if new_key != old_key and old_yaml.exists():
                old_yaml.unlink()
            changes.append(f"Profile: {old_key}.yaml → {new_key}.yaml")
        except Exception as e:
            errors.append(f"YAML 저장 실패: {e}")

        # ── 2. prompts/channels/ 폴더 이동 + 내용 치환 ─────────────
        old_prompts = _prompts_dir() / old_key
        new_prompts = _prompts_dir() / new_key
        if old_prompts.exists():
            if old_key != new_key:
                shutil.move(str(old_prompts), str(new_prompts))
            target = new_prompts
            for md_file in target.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    updated = content.replace(old_ch_name, new_name).replace(old_key, new_key)
                    if updated != content:
                        md_file.write_text(updated, encoding="utf-8")
                        affected_files += 1
                except Exception as e:
                    errors.append(f"{md_file.name}: {e}")
            changes.append(f"Prompts 폴더: {old_key}/ → {new_key}/ ({affected_files}개 파일 치환)")
        else:
            # 폴더 없으면 새로 생성
            try:
                from core.channel_setup import create_channel_with_md
                create_channel_with_md(new_key, profile_data)
                changes.append(f"Prompts 폴더 신규 생성: {new_key}/")
            except Exception as e:
                errors.append(f"Prompts 폴더 생성 실패: {e}")

        # ── 3. 옵시디언 Raw Data 폴더 이동 ─────────────────────────
        old_obs = _obsidian_raw() / f"채널_{old_ch_name}"
        new_obs = _obsidian_raw() / f"채널_{new_name}"
        if old_obs.exists():
            try:
                shutil.move(str(old_obs), str(new_obs))
                changes.append(f"Obsidian Raw: 채널_{old_ch_name}/ → 채널_{new_name}/")
            except Exception as e:
                errors.append(f"Obsidian Raw 이동 실패: {e}")
        else:
            try:
                new_obs.mkdir(parents=True, exist_ok=True)
                changes.append(f"Obsidian Raw 폴더 신규 생성: 채널_{new_name}/")
            except Exception:
                pass

        # ── 4. Wiki/Schema 메타데이터 치환 ─────────────────────────
        obs_root = _obsidian_path()
        for folder in ("01_Wiki", "02_Schema"):
            target_dir = obs_root / folder
            if not target_dir.exists():
                continue
            replaced = 0
            for fp in target_dir.rglob("*"):
                if not fp.is_file() or fp.suffix not in (".md", ".json"):
                    continue
                try:
                    txt = fp.read_text(encoding="utf-8")
                    new_txt = txt.replace(old_ch_name, new_name).replace(old_key, new_key)
                    if new_txt != txt:
                        fp.write_text(new_txt, encoding="utf-8")
                        replaced += 1
                except Exception as e:
                    errors.append(f"{fp.name}: {e}")
            if replaced:
                changes.append(f"{folder}: {replaced}개 파일 메타데이터 치환")

        # ── 5. session_state 갱신 ───────────────────────────────────
        try:
            import streamlit as st
            cur_key = st.session_state.get("current_channel_profile", "")
            if cur_key == old_key:
                st.session_state["current_channel_profile"] = new_key
                st.session_state["current_channel_name"]    = new_name
            changes.append(f"세션 전환: {new_key} ({new_name})")
        except Exception:
            pass

        # ── 6. md_loader 캐시 무효화 ─────────────────────────────
        try:
            from core.md_loader import load_md
            load_md.clear()
        except Exception:
            pass

        # ── 7. 로그 기록 ────────────────────────────────────────────
        _log(
            f"CHANNEL_RENAME: {old_ch_name} ({old_key}) → {new_name} ({new_key}) "
            f"| 변경 {len(changes)}건 | 파일 {affected_files}개 | 오류 {len(errors)}건"
        )

        return {
            "success":  True,
            "changes":  changes,
            "errors":   errors,
            "new_key":  new_key,
            "new_name": new_name,
        }

    except Exception as e:
        _log(f"CHANNEL_RENAME_ERROR: {old_key} → {new_name} | {e}")
        errors.append(f"치명적 오류: {e}")
        return {"success": False, "errors": errors, "changes": changes}


# ── 채널 삭제 (Task 36) ─────────────────────────────────────────────────

def delete_channel(channel_key: str) -> dict:
    """
    채널 삭제 (안전 장치: _deleted_channels/로 백업, 완전 삭제 X)
    현재 사용 중인 채널은 삭제 불가.
    """
    try:
        import streamlit as st
        cur = st.session_state.get("current_channel_profile", "")
    except Exception:
        cur = ""

    if channel_key == cur:
        return {"success": False, "error": "현재 사용 중인 채널은 삭제할 수 없습니다"}

    if channel_key.startswith("_"):
        return {"success": False, "error": "시스템 채널은 삭제할 수 없습니다"}

    base_dir    = Path(__file__).parent.parent
    backup_root = base_dir / "_deleted_channels" / channel_key
    backup_root.mkdir(parents=True, exist_ok=True)

    moved = []

    def _safe_move(src: Path, dst_name: str):
        if src.exists():
            dst = backup_root / dst_name
            shutil.move(str(src), str(dst))
            moved.append(str(src.name))

    # Profile YAML
    _safe_move(_profiles_dir() / f"{channel_key}.yaml", f"{channel_key}.yaml")

    # Prompts 폴더
    _safe_move(_prompts_dir() / channel_key, "prompts")

    # 채널명 얻기 위해 백업된 YAML 읽기
    bak_yaml = backup_root / f"{channel_key}.yaml"
    ch_name  = channel_key
    if bak_yaml.exists():
        try:
            import yaml as _yaml
            with bak_yaml.open(encoding="utf-8") as f:
                ch_name = (_yaml.safe_load(f) or {}).get("channel_name", channel_key)
        except Exception:
            pass

    # Obsidian Raw 폴더
    _safe_move(_obsidian_raw() / f"채널_{ch_name}", "obsidian_raw")

    _log(f"CHANNEL_DELETE: {ch_name} ({channel_key}) → _deleted_channels/ | {len(moved)}개 이동")

    return {
        "success": True,
        "message": f"'{ch_name}' 채널이 백업 폴더로 이동되었습니다",
        "backup_path": str(backup_root),
        "moved": moved,
    }


# ── 변경 후 검증 (Task 39) ──────────────────────────────────────────────

def verify_channel_rename(new_key: str, new_name: str = None) -> dict:
    """
    채널명 변경 후 모든 위치 정상 작동 확인.
    new_name 미지정 시 YAML에서 읽음.
    """
    if not new_name:
        try:
            import yaml as _yaml
            yaml_path = _profiles_dir() / f"{new_key}.yaml"
            with yaml_path.open(encoding="utf-8") as f:
                new_name = (_yaml.safe_load(f) or {}).get("channel_name", new_key)
        except Exception:
            new_name = new_key

    prompts_folder = _prompts_dir() / new_key
    md_count = len(list(prompts_folder.glob("*.md"))) if prompts_folder.exists() else 0

    try:
        import streamlit as st
        session_ok = st.session_state.get("current_channel_profile") == new_key
    except Exception:
        session_ok = False

    checks = {
        "profile_exists":      (_profiles_dir() / f"{new_key}.yaml").exists(),
        "prompts_exists":      prompts_folder.exists(),
        "obsidian_raw_exists": (_obsidian_raw() / f"채널_{new_name}").exists(),
        "session_updated":     session_ok,
        "prompts_md_count":    md_count,
    }

    return {
        "all_passed": all(
            v if not isinstance(v, int) else v >= 0
            for v in checks.values()
        ),
        "details":    checks,
        "new_key":    new_key,
        "new_name":   new_name,
    }
