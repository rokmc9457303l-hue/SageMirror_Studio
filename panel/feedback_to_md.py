# -*- coding: utf-8 -*-
"""
panel/feedback_to_md.py — 사용자 피드백 → MD 파일 반영 (Task I)

결과물에 대한 피드백을 수집하여 해당 Part MD의 피드백 섹션에 자동 추가한다.
누적된 피드백은 다음 실행 시 Gemma가 자동으로 참조한다.
"""

import datetime
import streamlit as st
from pathlib import Path

from core.md_loader import load_md, save_md


_FEEDBACK_SECTION = "\n\n---\n## 📝 사용자 피드백 누적\n\n"
_FEEDBACK_ITEM = "- [{ts}] {rating} {text}\n"


def render_feedback_box(part_num: int, result_id: str = ""):
    """
    에이전트 결과 하단 피드백 입력 박스 렌더링.

    Args:
        part_num:  Part 번호 (1~8)
        result_id: 결과 고유 ID (중복 방지용)
    """
    key_prefix = f"fb_p{part_num}_{result_id}"

    with st.expander("💬 피드백 남기기 (MD 자동 반영)", expanded=False):
        rating = st.radio(
            "결과 평가",
            ["⭐ 미흡", "⭐⭐ 보통", "⭐⭐⭐ 좋음", "⭐⭐⭐⭐ 훌륭"],
            horizontal=True,
            key=f"{key_prefix}_rating",
        )
        text = st.text_area(
            "구체적 피드백 (선택)",
            placeholder="어떤 부분이 부족했나요? 다음에 어떻게 개선되면 좋을까요?",
            key=f"{key_prefix}_text",
            height=100,
        )
        if st.button("📨 피드백 저장 및 MD 반영", key=f"{key_prefix}_submit"):
            _append_feedback_to_md(part_num, rating, text.strip())


def _append_feedback_to_md(part_num: int, rating: str, text: str):
    """피드백을 Part MD MAIN_PROMPT.md의 피드백 섹션에 추가"""
    try:
        from core.config import PROMPTS_PATH
        target = PROMPTS_PATH / "parts" / f"part{part_num}" / "MAIN_PROMPT.md"

        if not target.exists():
            st.warning(f"Part {part_num} MAIN_PROMPT.md 없음 — 피드백 저장 불가")
            return

        current = load_md(str(target))
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = _FEEDBACK_ITEM.format(ts=ts, rating=rating, text=text or "(텍스트 없음)")

        if _FEEDBACK_SECTION.strip() in current:
            new_content = current + entry
        else:
            new_content = current + _FEEDBACK_SECTION + entry

        # 백업 없이 저장 (피드백은 추가 전용, 파괴 없음)
        save_md(str(target), new_content, backup=False)
        st.success(f"✅ 피드백 저장 완료 → Part {part_num} MAIN_PROMPT.md")

    except Exception as e:
        st.error(f"피드백 저장 오류: {e}")


def get_feedback_history(part_num: int) -> list:
    """해당 Part MD에 저장된 피드백 항목 목록 반환"""
    try:
        from core.config import PROMPTS_PATH
        target = PROMPTS_PATH / "parts" / f"part{part_num}" / "MAIN_PROMPT.md"
        content = load_md(str(target))
        if _FEEDBACK_SECTION.strip() not in content:
            return []
        section = content.split(_FEEDBACK_SECTION.strip(), 1)[1]
        lines = [l.strip() for l in section.splitlines() if l.strip().startswith("- [")]
        return lines
    except Exception:
        return []
