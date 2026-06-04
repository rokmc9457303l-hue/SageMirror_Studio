# -*- coding: utf-8 -*-
"""parts/part5_영상생성.py — Part 5: 영상생성 (Video — Opal 8계정 분산)"""

import streamlit as st
import json
from datetime import datetime
from core.config import PART_NAMES
from core.state import get_state, set_state
from core.brain import call_model
from parts._template import (
    load_prompt, render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display
from core.version_control import render_action_buttons

PART_NUM = 5


def render_part5():
    st.markdown(f"## 📍 Part 5 — {PART_NAMES[5]} (Video)")
    st.caption("Google Opal 8계정 라운드 로빈 분산 JSON 생성")
    
    prev_packet = get_state("p4_packet")
    if not prev_packet:
        st.warning("⚠️ Part 4 (이미지생성) 을 먼저 완료하세요")
        return
    
    with st.expander("📥 Part 4 전달 패킷"):
        st.json(prev_packet)
    
    tabs = st.tabs(["📦 Opal JSON", "🔢 8계정 분산", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]: render_opal_tab(prev_packet)
    with tabs[1]: render_distribution_tab()
    with tabs[2]: render_validation_tab(PART_NUM)
    with tabs[3]: render_packet_tab(PART_NUM)
    with tabs[4]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


def render_opal_tab(prev_packet):
    st.markdown("### 📦 Opal 통합 JSON 생성")
    
    scene_count = st.number_input("씬 개수", 1, 30, 12, key="p5_scene_count")
    
    if st.button("📦 Opal JSON 생성", key="p5_opal_gen", type="primary", use_container_width=True):
        with st.spinner("Opal JSON 생성 중..."):
            result = generate_opal_json(prev_packet, scene_count)
        if result:
            set_state("p5_opal_json", result)
            set_state("p5_result", result)
            st.success("✅ Opal JSON 완료")
    
    result = get_state("p5_opal_json")
    if result:
        st.code(result, language="json")
        st.download_button(
            "📥 JSON 다운로드",
            result,
            file_name=f"opal_package_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )


def render_distribution_tab():
    st.markdown("### 🔢 8계정 라운드 로빈 분산")
    
    scene_count = get_state("p5_scene_count", 12)
    
    distribution = []
    for i in range(1, scene_count + 1):
        account = ((i - 1) % 8) + 1
        distribution.append({"scene": i, "account": account})
    
    set_state("p5_account_mapping", distribution)
    
    st.markdown("**계정별 담당 씬**")
    for acc in range(1, 9):
        scenes = [d["scene"] for d in distribution if d["account"] == acc]
        if scenes:
            st.write(f"📧 계정 #{acc}: 씬 {', '.join(map(str, scenes))} (총 {len(scenes)}개)")
    
    if st.button("📥 계정별 체크리스트 다운로드", key="p5_dist_dl"):
        checklist = build_account_checklists(distribution)
        st.download_button(
            "체크리스트 다운로드",
            checklist,
            file_name=f"account_checklists_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )


def generate_opal_json(prev_packet, scene_count: int) -> str:
    prompt = load_prompt(PART_NUM)
    user_query = f"""
[이미지 패킷]
{prev_packet}

[씬 개수] {scene_count}

위 자료로 Opal 통합 JSON을 생성하라.
- episode 메타
- global_assets (8개 마스터)
- consistency_rules
- scenes (씬별 prompt_en, assets_used, account_assigned, duration_sec)

8계정 라운드 로빈 분산:
씬 1→계정1, 씬 2→계정2, ..., 씬 9→계정1 (순환)

순수 JSON만 출력하라.
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))


def build_account_checklists(distribution: list) -> str:
    md = "# Opal 8계정 작업 체크리스트\n\n"
    for acc in range(1, 9):
        scenes = [d["scene"] for d in distribution if d["account"] == acc]
        if not scenes: continue
        md += f"\n## 계정 #{acc}\n\n"
        md += f"담당 씬: {', '.join(map(str, scenes))}\n\n"
        md += "체크리스트:\n"
        md += "- [ ] Opal 로그인\n"
        md += "- [ ] 마스터 에셋 8장 업로드\n"
        for s in scenes:
            md += f"- [ ] 씬 {s} 생성 → 다운로드\n"
        md += "- [ ] 로그아웃\n"
    return md
