# -*- coding: utf-8 -*-
"""
panel/sentinel_watchlist_ui.py — Sentinel 감시 채널 관리 UI (Tasks 50)
"""

import streamlit as st
from datetime import datetime


def _get_sentinel():
    if "sentinel_agent" not in st.session_state:
        from core.agents.sentinel import SentinelAgent
        st.session_state["sentinel_agent"] = SentinelAgent()
    return st.session_state["sentinel_agent"]


def render_sentinel_watchlist():
    """감시 채널 관리 메인 UI"""
    st.subheader("🛰️ Sentinel 감시 채널 관리")

    sentinel = _get_sentinel()
    watchlist = sentinel.watchlist

    # ── 새 채널 추가 ────────────────────────────────────────────────────
    with st.expander("📡 새 채널 추적 추가", expanded=not watchlist):
        name       = st.text_input("채널 이름", placeholder="채널 A")
        url        = st.text_input("YouTube URL", placeholder="https://youtube.com/@channel")
        channel_id = st.text_input("Channel ID", placeholder="UCxxxx (선택)")
        priority   = st.selectbox("우선순위", ["high", "medium", "low"])
        interval   = st.selectbox("추적 주기", ["daily", "weekly"])

        if st.button("➕ 채널 추가", use_container_width=True):
            if not name.strip() or not url.strip():
                st.error("채널 이름과 URL은 필수입니다.")
            elif any(c.get("url") == url.strip() for c in watchlist):
                st.warning("이미 등록된 URL입니다.")
            else:
                new_entry = {
                    "name": name.strip(),
                    "url": url.strip(),
                    "channel_id": channel_id.strip(),
                    "added_date": datetime.now().strftime("%Y-%m-%d"),
                    "priority": priority,
                    "track_interval": interval,
                }
                watchlist.append(new_entry)
                sentinel.save_watchlist(watchlist)
                st.success(f"✅ '{name}' 추가 완료")
                st.rerun()

    # ── 현재 감시 채널 목록 ─────────────────────────────────────────────
    st.markdown(f"**현재 감시 중: {len(watchlist)}개 채널**")
    st.markdown("━" * 30)

    if not watchlist:
        st.info("추적 중인 채널이 없습니다. 위에서 채널을 추가하세요.")
    else:
        _priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for i, ch in enumerate(watchlist):
            with st.container(border=True):
                col_info, col_btns = st.columns([4, 1])
                with col_info:
                    icon = _priority_icon.get(ch.get("priority", "medium"), "⚪")
                    st.markdown(f"**{icon} {i+1}. {ch.get('name', '?')}**")
                    st.caption(
                        f"우선순위: {ch.get('priority', '')} | "
                        f"주기: {ch.get('track_interval', '')} | "
                        f"등록일: {ch.get('added_date', '')}"
                    )
                with col_btns:
                    if st.button("🗑️", key=f"del_ch_{i}", help="삭제"):
                        watchlist.pop(i)
                        sentinel.save_watchlist(watchlist)
                        st.rerun()

    # ── 전체 통계 ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("**📊 전체 감시 통계**")
    col1, col2, col3 = st.columns(3)
    col1.metric("추적 채널", f"{len(watchlist)}개")
    col2.metric("HIGH 우선순위", f"{sum(1 for c in watchlist if c.get('priority')=='high')}개")
    col3.metric("DAILY 체크", f"{sum(1 for c in watchlist if c.get('track_interval')=='daily')}개")

    # ── 수동 정찰 실행 ─────────────────────────────────────────────────
    st.divider()
    col_patrol, col_trend = st.columns(2)
    with col_patrol:
        if st.button("🛰️ 지금 정찰 실행", use_container_width=True):
            with st.spinner("정찰 중..."):
                try:
                    result = sentinel.daily_patrol()
                    st.success(f"정찰 완료 — 신규 영상: {result.get('new_videos', 0)}건")
                    with st.expander("보고서"):
                        st.text(result.get("report", ""))
                except Exception as e:
                    st.error(f"정찰 오류: {e}")
    with col_trend:
        if st.button("📈 트렌드 감지", use_container_width=True):
            with st.spinner("트렌드 분석 중..."):
                try:
                    trends = sentinel.detect_trend_explosion(days=7)
                    if trends:
                        for t in trends[:3]:
                            st.markdown(
                                f"**🔥 {t['trend']}** — {t['total_views']:,}뷰 "
                                f"| 긴급도: {t['urgency']}"
                            )
                            st.caption(t.get("recommendation", ""))
                    else:
                        st.info("현재 동시 폭발 트렌드 없음")
                except Exception as e:
                    st.error(f"트렌드 감지 오류: {e}")
