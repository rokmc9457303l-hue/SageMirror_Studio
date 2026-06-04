# -*- coding: utf-8 -*-
"""parts/part2_총괄기획.py — Part 2: 총괄기획 (Alchemist)"""

import streamlit as st
from core.config import PART_NAMES
from core.state import get_state, set_state
from core.brain import call_model
from core.obsidian import search_rag
from parts._template import (
    load_prompt, render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display
from core.version_control import render_action_buttons

PART_NUM = 2


def render_part2():
    st.markdown(f"## 📍 Part 2 — {PART_NAMES[2]} (Alchemist)")
    st.caption("철학·성경·심리·문학 4원 융합 → 기획안")
    
    prev_packet = get_state("p1_packet")
    if not prev_packet:
        st.warning("⚠️ Part 1 (자료수집) 을 먼저 완료하세요")
        return
    
    with st.expander("📥 Part 1 전달 패킷"):
        st.json(prev_packet)
    
    tabs = st.tabs(["🎬 기획 생성", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]: render_planning_tab(prev_packet)
    with tabs[1]: render_validation_tab(PART_NUM)
    with tabs[2]: render_packet_tab(PART_NUM)
    with tabs[3]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


def render_planning_tab(prev_packet):
    st.markdown("### 🎬 기승전결 기획안 생성")
    
    additional = st.text_area(
        "추가 지시 (선택)",
        placeholder="예: 결 부분 성경 비중 강조 / 다크심리학 부분 축소",
        height=80,
        key="p2_addl",
    )
    
    if st.button("🚀 기획안 생성", key="p2_gen", type="primary", use_container_width=True):
        with st.spinner("⚙️ 4원 융합 기획 중..."):
            result = generate_planning(prev_packet, additional)
        if result:
            set_state("p2_result", result)
            st.success("✅ 기획안 완료")
    
    result = get_state("p2_result")
    if result:
        result_display(result, title="기획안", height=500)


def generate_planning(prev_packet, additional: str = "") -> str:
    topic = prev_packet.get("topic", "") if isinstance(prev_packet, dict) else ""
    rag = search_rag(f"{topic} 철학 성경 심리", max_files=5, max_chars=400)
    prompt = load_prompt(PART_NUM)
    
    user_query = f"""
[Part 1 전달 패킷]
{prev_packet}

[옵시디언 RAG]
{rag[:1200]}

[추가 지시]
{additional}

위 자료로 기승전결 4원 융합 기획안을 생성하라.
- 제목 후보 3개
- 로그라인 1줄
- 기승전결 매핑
- 씬 구조 (8~12개)
- 감정 곡선
- 핵심 인용 후보 [SOURCE: ...] 필수
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))
