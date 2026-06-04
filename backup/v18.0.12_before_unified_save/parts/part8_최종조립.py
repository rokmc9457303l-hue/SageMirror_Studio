# -*- coding: utf-8 -*-
"""parts/part8_최종조립.py — Part 8: 최종조립 (Final)"""

import streamlit as st
from core.config import PART_NAMES
from core.state import get_state, set_state
from core.brain import call_model
from parts._template import (
    load_prompt, render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display
from core.version_control import render_action_buttons, github_push

PART_NUM = 8


def render_part8():
    st.markdown(f"## 📍 Part 8 — {PART_NAMES[8]} (Final)")
    st.caption("제목·설명·태그·썸네일 + 업로드 패키지")
    
    all_packets = {f"p{i}": get_state(f"p{i}_packet") for i in range(1, 8)}
    missing = [k for k, v in all_packets.items() if not v]
    
    if missing:
        st.warning(f"⚠️ 미완료 파트: {', '.join(missing)}")
    
    with st.expander("📊 전체 파트 상태"):
        for i in range(1, 8):
            packet = all_packets[f"p{i}"]
            st.write(f"Part {i} ({PART_NAMES[i]}): {'✅' if packet else '❌'}")
    
    tabs = st.tabs(["🎬 업로드 패키지", "🔍 검증", "📤 최종 패킷", "📊 상태", "🚀 GitHub"])
    
    with tabs[0]: render_upload_tab(all_packets)
    with tabs[1]: render_validation_tab(PART_NUM)
    with tabs[2]: render_packet_tab(PART_NUM)
    with tabs[3]: render_status_tab(PART_NUM)
    with tabs[4]: render_github_tab()
    
    render_action_buttons(PART_NUM)


def render_upload_tab(all_packets):
    st.markdown("### 🎬 YouTube 업로드 패키지")
    
    if st.button("🚀 최종 패키지 생성", key="p8_gen", type="primary", use_container_width=True):
        with st.spinner("최종 패키지 생성 중..."):
            result = generate_final(all_packets)
        if result:
            set_state("p8_result", result)
            st.success("✅ 최종 패키지 완료")
    
    result = get_state("p8_result")
    if result:
        result_display(result, title="업로드 패키지", height=500)


def render_github_tab():
    st.markdown("### 🚀 GitHub 자동 백업")
    
    commit_msg = st.text_input(
        "커밋 메시지",
        value=f"Episode {get_state('current_episode')} 완료",
        key="p8_commit_msg",
    )
    
    if st.button("🚀 GitHub Push", key="p8_push", type="primary", use_container_width=True):
        github_push(commit_msg)


def generate_final(all_packets) -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[전체 파트 패킷]
{all_packets}

위 자료로 YouTube 업로드 패키지를 생성하라:
- 제목 3안 (감정·질문·통찰)
- 설명 본문
- 챕터 타임스탬프
- 16개 카테고리 태그
- 썸네일 텍스트 3안
- 해시태그
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))
