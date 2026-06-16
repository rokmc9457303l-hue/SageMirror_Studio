import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Add import
if 'from ui.research_campus import render_research_campus' not in content:
    content = content.replace('import streamlit as st', 'import streamlit as st\nfrom ui.research_campus import render_research_campus', 1)

# 2. Add button in sidebar
sidebar_btn_target = '''    if st.button("⚙️ 설정 열기", use_container_width=True, key="open_settings_modal_button"):'''
sidebar_btn_replacement = '''    if st.button("🏫 등교 / 학교 연구기관", use_container_width=True, key="open_campus_btn"):
        st.session_state["current_view"] = "research_campus"
        st.session_state["show_settings_modal"] = False
        st.rerun()

    if st.button("⚙️ 설정 열기", use_container_width=True, key="open_settings_modal_button"):'''

if '🏫 등교 / 학교 연구기관' not in content:
    content = content.replace(sidebar_btn_target, sidebar_btn_replacement)

# 3. Add Part navigation hook
part_nav_target = '''    part = st.radio("이동할 파트", part_options, index=part_idx, label_visibility="collapsed")
    st.session_state.sidebar_part = part'''
part_nav_replacement = '''    part = st.radio("이동할 파트", part_options, index=part_idx, label_visibility="collapsed")
    st.session_state.sidebar_part = part
    if st.session_state.get("current_view") == "research_campus":
        st.session_state["current_view"] = "part"
        st.rerun()'''

if 'st.session_state["current_view"] = "part"' not in content:
    content = content.replace(part_nav_target, part_nav_replacement)

# 4. Add render logic before main_col
render_target = '''# =====================================================================

    part = "파트 1: 벤치마킹 & 자료조사"'''
render_replacement = '''# =====================================================================
# 8.5 학교 연구기관 렌더링
# =====================================================================
if st.session_state.get("current_view") == "research_campus":
    render_research_campus()
    st.stop()

# =====================================================================

    part = "파트 1: 벤치마킹 & 자료조사"'''

if 'render_research_campus()' not in content:
    # We will use regex if literal fails because the 'part = ...' might be indented differently or not exist like that.
    # Actually the code was:
    # # =====================================================================
    #
    #     part = "파트 1: 벤치마킹 & 자료조사"
    # main_col, right_col = st.columns([7.2, 2.8], gap="large")
    content = content.replace('''# =====================================================================\n\n    part = "파트 1: 벤치마킹 & 자료조사"\n\nmain_col, right_col = st.columns([7.2, 2.8], gap="large")''', '''# =====================================================================\n\nif st.session_state.get("current_view") == "research_campus":\n    render_research_campus()\n    st.stop()\n\n    part = "파트 1: 벤치마킹 & 자료조사"\n\nmain_col, right_col = st.columns([7.2, 2.8], gap="large")''')

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)

print("Updated app_v17_2_4.py with all replacements.")
