# -*- coding: utf-8 -*-
"""
panel/md_editor.py — MD 프롬프트 편집 UI (Task F)

기능:
  - 파일 트리 (parts/shared/agents)
  - 코드 에디터 (st.text_area)
  - 실시간 미리보기 (st.markdown)
  - 저장 → 자동 백업 + mtime 캐시 무효화
  - 변수 보호: {{VAR}} 삭제 시 경고
"""

import re
import streamlit as st
from pathlib import Path

from core.md_loader import load_md, save_md, list_all_prompts
from panel.md_validator import validate_md


def _get_session(key, default=None):
    return st.session_state.get(key, default)


def _set_session(key, val):
    st.session_state[key] = val


def render_md_editor():
    """MD 편집 패널 렌더링 (사이드바 또는 풀스크린 모달로 호출)"""
    st.subheader("📝 프롬프트 MD 편집기")

    tree = list_all_prompts()
    if not tree:
        st.info("prompts/ 폴더에 MD 파일이 없습니다.")
        return

    # ── 파일 선택 ──────────────────────────────────────────
    options = []
    for category, files in tree.items():
        for f in files:
            options.append((f["rel"], f["path"]))

    labels = [o[0] for o in options]
    selected_label = st.selectbox(
        "파일 선택",
        labels,
        index=labels.index(_get_session("md_editor_selected", labels[0]))
        if _get_session("md_editor_selected", labels[0]) in labels
        else 0,
        key="md_editor_file_select",
    )

    selected_path = dict(options)[selected_label]
    _set_session("md_editor_selected", selected_label)

    # ── 현재 내용 로드 ─────────────────────────────────────
    original = load_md(selected_path)

    # ── 탭: 편집 / 미리보기 ───────────────────────────────
    tab_edit, tab_preview = st.tabs(["✏️ 편집", "👁️ 미리보기"])

    with tab_edit:
        new_content = st.text_area(
            "내용",
            value=_get_session(f"md_draft_{selected_label}", original),
            height=500,
            key=f"md_editor_area_{selected_label}",
        )
        _set_session(f"md_draft_{selected_label}", new_content)

        col_save, col_reset, col_info = st.columns([2, 1, 3])

        with col_save:
            if st.button("💾 저장", use_container_width=True):
                _do_save(selected_path, original, new_content, selected_label)

        with col_reset:
            if st.button("↩ 초기화"):
                _set_session(f"md_draft_{selected_label}", original)
                st.rerun()

        with col_info:
            # 변경 감지
            if new_content != original:
                st.caption(f"변경됨 — {len(new_content)}자")
            else:
                st.caption(f"변경 없음 — {len(original)}자")

    with tab_preview:
        if new_content.strip():
            st.markdown(new_content, unsafe_allow_html=False)
        else:
            st.info("내용이 없습니다.")

    # ── 백업 목록 ──────────────────────────────────────────
    with st.expander("🗂️ 백업 파일", expanded=False):
        _render_backups(selected_path)


def _do_save(path: str, original: str, new_content: str, label: str):
    """저장 전 검증 → 백업 → 저장"""
    # 1. 변수 보호 검사
    orig_vars = set(re.findall(r"\{\{(\w+)\}\}", original))
    new_vars = set(re.findall(r"\{\{(\w+)\}\}", new_content))
    removed = orig_vars - new_vars
    if removed:
        st.warning(
            f"⚠️ 다음 변수가 제거되었습니다: {', '.join('{{' + v + '}}' for v in removed)}\n"
            "변수를 제거하려면 의도적으로 삭제하세요. 계속하려면 다시 [저장]을 누르세요."
        )
        _set_session(f"md_var_warn_{label}", True)
        if not _get_session(f"md_var_warn_{label}_confirmed", False):
            return
    _set_session(f"md_var_warn_{label}", False)
    _set_session(f"md_var_warn_{label}_confirmed", False)

    # 2. MD 검증
    issues = validate_md(new_content, path)
    if issues:
        st.error("❌ 검증 실패:\n" + "\n".join(f"- {i}" for i in issues))
        return

    # 3. 저장 (자동 백업)
    backup_path = save_md(path, new_content, backup=True)
    _set_session(f"md_draft_{label}", new_content)

    if backup_path:
        st.success(f"✅ 저장 완료 (백업: {Path(backup_path).name})")
    else:
        st.success("✅ 저장 완료")


def _render_backups(original_path: str):
    """백업 파일 목록 + 복원 버튼"""
    try:
        from core.config import PROMPTS_PATH
        bk_dir = PROMPTS_PATH / "_backup"
        stem = Path(original_path).stem
        backups = sorted(bk_dir.glob(f"{stem}_*.md"), reverse=True)[:10]
    except Exception:
        backups = []

    if not backups:
        st.caption("백업 없음")
        return

    for bk in backups:
        col_name, col_restore = st.columns([4, 1])
        col_name.caption(bk.name)
        if col_restore.button("복원", key=f"restore_{bk.name}"):
            content = bk.read_text(encoding="utf-8")
            _set_session(f"md_draft_{Path(original_path).name}", content)
            st.success(f"복원됨: {bk.name}")
            st.rerun()
