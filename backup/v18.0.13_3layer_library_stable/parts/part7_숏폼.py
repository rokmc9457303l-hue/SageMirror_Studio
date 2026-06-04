# -*- coding: utf-8 -*-
"""parts/part7_숏폼.py — Part 7: 숏폼생성 (Shorts)"""

import streamlit as st
from core.config import PART_NAMES
from core.state import get_state, set_state
from core.brain import call_model
from parts._template import (
    load_prompt, render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display
from core.version_control import render_action_buttons

PART_NUM = 7


def render_part7():
    st.markdown(f"## 📍 Part 7 — {PART_NAMES[7]} (Shorts)")
    st.caption("베스트 30~60초 추출 + 후킹 3안 + CapCut 타임코드")
    
    p3 = get_state("p3_packet")
    p5 = get_state("p5_packet")
    p6 = get_state("p6_packet")
    
    if not p3:
        st.warning("⚠️ Part 3 (대본작성) 을 먼저 완료하세요")
        return
    
    with st.expander("📥 종합 입력 (Part 3·5·6)"):
        st.write(f"Part 3: {'✅' if p3 else '❌'}")
        st.write(f"Part 5: {'✅' if p5 else '❌'}")
        st.write(f"Part 6: {'✅' if p6 else '❌'}")
    
    tabs = st.tabs(["📱 숏폼 추출", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]: render_shorts_tab(p3, p5, p6)
    with tabs[1]: render_validation_tab(PART_NUM)
    with tabs[2]: render_packet_tab(PART_NUM)
    with tabs[3]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


def render_shorts_tab(p3, p5, p6):
    st.markdown("### 📱 숏폼 3개 추출")
    
    if st.button("📱 숏폼 3개 생성", key="p7_gen", type="primary", use_container_width=True):
        with st.spinner("베스트 모먼트 추출 중..."):
            result = generate_shorts(p3, p5, p6)
        if result:
            set_state("p7_result", result)
            st.success("✅ 숏폼 3개 완료")
    
    result = get_state("p7_result")
    if result:
        result_display(result, title="숏폼 추출 결과", height=500)


def generate_shorts(p3, p5, p6) -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[대본]
{p3}

[영상]
{p5}

[음성·BGM]
{p6}

베스트 30~60초 구간 3개를 추출하라.
각각 후킹 변형 3안 + CapCut 타임코드 + 세로 변환 가이드.
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))
