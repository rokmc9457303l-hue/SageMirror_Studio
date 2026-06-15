# -*- coding: utf-8 -*-
"""
panel/result_with_md_link.py — 에이전트 결과 표시 + MD 수정 링크 (Task H)

결과 패널 하단에 "📝 프롬프트 수정" 버튼을 추가한다.
버튼 클릭 시 md_editor 패널이 열리고 해당 Part MD 파일로 이동한다.
"""

import streamlit as st
from pathlib import Path

from core.md_loader import list_all_prompts


def render_result_with_md_link(
    result: dict,
    part_num: int,
    label: str = "",
    show_raw: bool = False,
):
    """
    에이전트 결과 + MD 수정 링크 렌더링.

    Args:
        result:   에이전트 .execute() 반환 dict
        part_num: Part 번호 (1~8)
        label:    결과 표시 제목
        show_raw: JSON 원문 토글
    """
    title = label or f"Part {part_num} 결과"
    with st.container(border=True):
        st.markdown(f"**{title}**")

        # ── 결과 표시 ──────────────────────────────────────
        _render_result_body(result, part_num)

        # ── 구분선 + 버튼 행 ───────────────────────────────
        st.divider()
        col_md, col_raw, col_copy = st.columns([2, 1, 1])

        with col_md:
            if st.button(
                "📝 프롬프트 수정",
                key=f"open_md_editor_p{part_num}_{id(result)}",
                help=f"Part {part_num} MD 파일 편집 창을 엽니다.",
            ):
                st.session_state["md_editor_open"] = True
                st.session_state["md_editor_target_part"] = part_num
                st.rerun()

        with col_raw:
            if show_raw:
                with st.expander("JSON"):
                    st.json(result)

        with col_copy:
            text_out = _extract_text(result)
            if text_out and st.button("📋 복사", key=f"copy_p{part_num}_{id(result)}"):
                st.code(text_out, language="")


def _render_result_body(result: dict, part_num: int):
    """Part별 결과 표시 로직"""
    if not result:
        st.warning("결과 없음")
        return

    error = result.get("error") or result.get("err")
    if error:
        st.error(f"오류: {error}")
        return

    # 공통: message 필드
    msg = result.get("message") or result.get("summary") or ""
    if msg:
        st.info(msg)

    # Part 1: 주제 목록
    if part_num == 1:
        topics = result.get("topics") or result.get("topic_candidates") or []
        for i, t in enumerate(topics[:5], 1):
            if isinstance(t, dict):
                st.markdown(f"**{i}. {t.get('title', '')}**")
                if t.get("core_emotion"):
                    st.caption(f"감정: {t['core_emotion']}")
            else:
                st.markdown(f"{i}. {t}")

    # Part 2: 기획안 요약
    elif part_num == 2:
        for key in ("final_topic", "core_message", "title_candidates"):
            val = result.get(key)
            if val:
                st.markdown(f"**{key}:** {val if isinstance(val, str) else ', '.join(val)}")

    # Part 3~8: 텍스트 출력
    else:
        text = _extract_text(result)
        if text:
            st.markdown(text[:2000] + ("..." if len(text) > 2000 else ""))
        else:
            st.json(result)


def _extract_text(result: dict) -> str:
    for key in ("text", "content", "output", "narration", "script", "message", "summary"):
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""
