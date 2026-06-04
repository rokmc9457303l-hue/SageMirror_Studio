# -*- coding: utf-8 -*-
"""parts/part4_이미지생성.py — Part 4: 이미지생성 (Image)"""

import streamlit as st
from core.config import PART_NAMES
from core.state import get_state, set_state
from core.brain import call_model
from parts._template import (
    load_prompt, render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display
from core.version_control import render_action_buttons

PART_NUM = 4


def render_part4():
    st.markdown(f"## 📍 Part 4 — {PART_NAMES[4]} (Image)")
    st.caption("Auto Flow + Nano Banana 2 호환 프롬프트 생성")
    
    prev_packet = get_state("p3_packet")
    if not prev_packet:
        st.warning("⚠️ Part 3 (대본작성) 을 먼저 완료하세요")
        return
    
    with st.expander("📥 Part 3 전달 패킷"):
        st.json(prev_packet)
    
    tabs = st.tabs(["🎨 마스터 에셋", "🖼️ 씬별 프롬프트", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]: render_master_tab(prev_packet)
    with tabs[1]: render_scene_tab(prev_packet)
    with tabs[2]: render_validation_tab(PART_NUM)
    with tabs[3]: render_packet_tab(PART_NUM)
    with tabs[4]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


def render_master_tab(prev_packet):
    st.markdown("### 🎨 마스터 에셋 8장 프롬프트")
    st.info("@P @M @A @B @C @K @W @R — 8개 마스터 이미지용")
    
    additional = st.text_area("추가 지시", height=60, key="p4_master_addl")
    
    if st.button("🎨 마스터 8장 생성", key="p4_master_gen", type="primary", use_container_width=True):
        with st.spinner("마스터 프롬프트 생성 중..."):
            result = generate_master_assets(prev_packet, additional)
        if result:
            set_state("p4_master_prompts", result)
            st.success("✅ 마스터 8장 완료")
    
    result = get_state("p4_master_prompts")
    if result:
        result_display(result, title="마스터 에셋 프롬프트", height=400)


def render_scene_tab(prev_packet):
    st.markdown("### 🖼️ 씬별 프롬프트 (한/영)")
    
    additional = st.text_area("추가 지시", height=60, key="p4_scene_addl")
    
    if st.button("🖼️ 씬별 프롬프트 생성", key="p4_scene_gen", type="primary", use_container_width=True):
        with st.spinner("씬별 프롬프트 생성 중..."):
            result = generate_scene_prompts(prev_packet, additional)
        if result:
            set_state("p4_scene_prompts", result)
            set_state("p4_result", result)
            st.success("✅ 씬별 프롬프트 완료")
    
    result = get_state("p4_scene_prompts")
    if result:
        result_display(result, title="씬별 프롬프트", height=500)


def generate_master_assets(prev_packet, additional: str = "") -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[대본 패킷]
{prev_packet}

[추가 지시]
{additional}

마스터 에셋 8장(@P @M @A @B @C @K @W @R)의 프롬프트를 생성하라.
각각 한국어/영어 두 버전.
Rembrandt chiaroscuro, 17세기 서재, burgundy·gold·deep brown 팔레트.
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))


def generate_scene_prompts(prev_packet, additional: str = "") -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[대본 패킷]
{prev_packet}

[추가 지시]
{additional}

각 씬별로 이미지 프롬프트를 한국어/영어 두 버전으로 생성하라.
사용 에셋(@P @B 등) 명시.
일관성 규칙 적용.
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))
