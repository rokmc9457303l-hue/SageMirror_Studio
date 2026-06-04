# -*- coding: utf-8 -*-
"""parts/part3_대본작성.py — Part 3: 대본작성 (Writer)"""

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

PART_NUM = 3


def render_part3():
    st.markdown(f"## 📍 Part 3 — {PART_NAMES[3]} (Writer)")
    st.caption("씬별 분할 생성 → 나레이션·이미지 대본·CapCut 에셋")
    
    prev_packet = get_state("p2_packet")
    if not prev_packet:
        st.warning("⚠️ Part 2 (총괄기획) 을 먼저 완료하세요")
        return
    
    with st.expander("📥 Part 2 전달 패킷"):
        st.json(prev_packet)
    
    tabs = st.tabs(["🎬 대본 생성", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]: render_writing_tab(prev_packet)
    with tabs[1]: render_validation_tab(PART_NUM)
    with tabs[2]: render_packet_tab(PART_NUM)
    with tabs[3]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


def render_writing_tab(prev_packet):
    st.markdown("### ✍️ 씬별 대본 작성")
    
    st.info("⚠️ 씬마다 개별 생성 권장 (한 번에 전체 생성 시 일관성 붕괴 위험)")
    
    mode = st.radio(
        "생성 모드",
        ["씬별 개별 생성 (권장)", "전체 일괄 생성"],
        key="p3_mode",
    )
    
    additional = st.text_area("추가 지시", height=80, key="p3_addl")
    
    if mode.startswith("씬별"):
        scene_count = prev_packet.get("scene_count", 10) if isinstance(prev_packet, dict) else 10
        scene_num = st.number_input("씬 번호", 1, scene_count, 1, key="p3_scene_num")
        
        if st.button(f"✍️ 씬 {scene_num} 생성", key="p3_gen_scene", type="primary", use_container_width=True):
            with st.spinner(f"씬 {scene_num} 작성 중..."):
                result = generate_scene(prev_packet, scene_num, additional)
            if result:
                scenes = get_state("p3_scenes", {})
                scenes[scene_num] = result
                set_state("p3_scenes", scenes)
                st.success(f"✅ 씬 {scene_num} 완료")
        
        scenes = get_state("p3_scenes", {})
        if scenes:
            for sid in sorted(scenes.keys()):
                with st.expander(f"씬 {sid}"):
                    st.markdown(scenes[sid])
            
            if st.button("📋 전체 통합 → 최종 대본", key="p3_combine"):
                combined = "\n\n".join([f"━━━━ 씬 {sid} ━━━━\n{scenes[sid]}" for sid in sorted(scenes.keys())])
                set_state("p3_result", combined)
                st.success("✅ 통합 완료")
    else:
        if st.button("⚠️ 전체 일괄 생성", key="p3_gen_all", use_container_width=True):
            with st.spinner("전체 대본 생성 중 (오래 걸림)..."):
                result = generate_full_script(prev_packet, additional)
            if result:
                set_state("p3_result", result)
                st.success("✅ 전체 대본 완료")
    
    result = get_state("p3_result")
    if result:
        result_display(result, title="대본", height=500)


def generate_scene(prev_packet, scene_num: int, additional: str = "") -> str:
    rag = search_rag(f"대본 씬 {scene_num} 감정", max_files=3, max_chars=300)
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[기획안]
{prev_packet}

[옵시디언 RAG]
{rag[:800]}

[추가 지시]
{additional}

씬 {scene_num} 의 대본을 작성하라:
- 나레이션 (300~400자)
- 이미지 대본
- 감정 태그 (EXPR-01~06)
- 시간 (mm:ss)
- CapCut 에셋
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))


def generate_full_script(prev_packet, additional: str = "") -> str:
    rag = search_rag("대본 나레이션", max_files=5, max_chars=300)
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[기획안]
{prev_packet}

[옵시디언 RAG]
{rag[:1000]}

[추가 지시]
{additional}

전체 8~12씬 나레이션 대본을 작성하라.
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))
