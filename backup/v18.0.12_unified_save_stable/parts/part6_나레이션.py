# -*- coding: utf-8 -*-
"""parts/part6_나레이션.py — Part 6: 나레이션·배경음악 (Voice)"""

import streamlit as st
from core.config import PART_NAMES
from core.state import get_state, set_state
from core.brain import call_model
from parts._template import (
    load_prompt, render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display
from core.version_control import render_action_buttons

PART_NUM = 6


def render_part6():
    st.markdown(f"## 📍 Part 6 — {PART_NAMES[6]} (Voice)")
    st.caption("TTS 감정 태그 + BGM 무드 매칭")
    
    prev_packet = get_state("p3_packet")
    if not prev_packet:
        st.warning("⚠️ Part 3 (대본작성) 을 먼저 완료하세요")
        return
    
    with st.expander("📥 Part 3 전달 패킷"):
        st.json(prev_packet)
    
    tabs = st.tabs(["🎙️ TTS 입력", "🎵 BGM 매칭", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]: render_tts_tab(prev_packet)
    with tabs[1]: render_bgm_tab(prev_packet)
    with tabs[2]: render_validation_tab(PART_NUM)
    with tabs[3]: render_packet_tab(PART_NUM)
    with tabs[4]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


def render_tts_tab(prev_packet):
    st.markdown("### 🎙️ TTS 감정 태그 자동 삽입")
    
    if st.button("🎙️ TTS 입력 생성", key="p6_tts_gen", type="primary", use_container_width=True):
        with st.spinner("TTS 감정 태그 삽입 중..."):
            result = generate_tts(prev_packet)
        if result:
            set_state("p6_tts_result", result)
            set_state("p6_result", result)
            st.success("✅ TTS 입력 완료")
    
    result = get_state("p6_tts_result")
    if result:
        result_display(result, title="TTS 입력 텍스트", height=400)


def render_bgm_tab(prev_packet):
    st.markdown("### 🎵 BGM 무드 매칭")
    
    if st.button("🎵 BGM 매칭", key="p6_bgm_gen", type="primary", use_container_width=True):
        with st.spinner("BGM 매칭 중..."):
            result = generate_bgm(prev_packet)
        if result:
            set_state("p6_bgm_result", result)
            st.success("✅ BGM 매칭 완료")
    
    result = get_state("p6_bgm_result")
    if result:
        result_display(result, title="BGM 매칭표", height=300)


def generate_tts(prev_packet) -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[대본 패킷]
{prev_packet}

위 대본에 TTS 감정 태그를 삽입하라.
EXPR-01 평온 / EXPR-02 깊은 침묵 / EXPR-03 슬픔
EXPR-04 통찰 / EXPR-05 회복 / EXPR-06 희망

침묵 구간은 (3초 침묵) 같은 마커로 표시.
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))


def generate_bgm(prev_packet) -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[대본 패킷]
{prev_packet}

각 씬별로 어울리는 BGM 무드를 추천하라.
형식: 씬 N | 무드 키워드 | 검색 키워드 (Pixabay/YouTube)
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))
