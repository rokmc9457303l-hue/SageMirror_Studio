# -*- coding: utf-8 -*-
"""
panel/sentinel_daily_report.py — Sentinel 일일 정찰 보고서 (Task 51)

매일 첫 로그인 시 자동 표시.
떡상 영상 + 응용 주제 카드 UI.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta


def _get_today_report_path() -> Path:
    from core.config import OBSIDIAN_PATH
    date_str = datetime.now().strftime("%Y-%m-%d")
    return OBSIDIAN_PATH / "04_Sentinel" / "daily_reports" / f"{date_str}.md"


def _was_shown_today() -> bool:
    """오늘 이미 표시했으면 True"""
    key = f"sentinel_report_shown_{datetime.now().strftime('%Y-%m-%d')}"
    return st.session_state.get(key, False)


def _mark_shown():
    key = f"sentinel_report_shown_{datetime.now().strftime('%Y-%m-%d')}"
    st.session_state[key] = True


def render_sentinel_daily_report(force: bool = False):
    """
    일일 정찰 보고서 렌더링.

    Args:
        force: True 이면 이미 표시한 경우에도 다시 표시
    """
    if _was_shown_today() and not force:
        return

    report_path = _get_today_report_path()
    if not report_path.exists():
        # 보고서 없음 → 이전 날짜 확인 (최근 3일)
        for delta in range(1, 4):
            date_str = (datetime.now() - timedelta(days=delta)).strftime("%Y-%m-%d")
            from core.config import OBSIDIAN_PATH
            prev = OBSIDIAN_PATH / "04_Sentinel" / "daily_reports" / f"{date_str}.md"
            if prev.exists():
                report_path = prev
                break
        else:
            return  # 보고서 없으면 표시 생략

    content = report_path.read_text(encoding="utf-8")
    _mark_shown()

    # ── 보고서 모달 ──────────────────────────────────────────────────────
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    with st.container(border=True):
        col_title, col_close = st.columns([5, 1])
        col_title.markdown(f"### 🛰️ Sentinel 일일 정찰 보고서\n`{date_str}`")
        if col_close.button("✕ 닫기", key="sentinel_report_close"):
            _mark_shown()
            st.rerun()

        st.markdown(content[:3000])  # 최대 3000자

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛰️ 지금 정찰 실행", key="sr_patrol_now"):
                from core.agents.sentinel import SentinelAgent
                with st.spinner("정찰 중..."):
                    try:
                        s = SentinelAgent()
                        result = s.daily_patrol()
                        st.success(f"완료 — 신규 {result.get('new_videos', 0)}건")
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")
        with col2:
            if st.button("📋 채널 관리", key="sr_open_watchlist"):
                st.session_state["sentinel_watchlist_open"] = True
                st.rerun()


def maybe_show_daily_report():
    """app.py 최상단에서 호출 — 오늘 처음 접속 시 자동 표시"""
    render_sentinel_daily_report(force=False)
