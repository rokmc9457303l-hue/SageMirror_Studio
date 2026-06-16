import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Add import
if 'from ui.research_campus import render_research_campus' not in content:
    content = content.replace('import streamlit as st', 'import streamlit as st\nfrom ui.research_campus import render_research_campus')

# 2. Add button in sidebar
# Find where settings_modal button is and add the campus button BEFORE the settings modal button.
sidebar_btn_target = '''    if st.button("⚙️ 설정 열기", use_container_width=True, key="open_settings_modal_button"):
        st.session_state["show_settings_modal"] = True'''

sidebar_btn_replacement = '''    if st.button("🏫 등교 / 학교 연구기관", use_container_width=True, key="open_campus_btn"):
        st.session_state["current_view"] = "research_campus"
        st.session_state["show_settings_modal"] = False
        st.rerun()

    if st.button("⚙️ 설정 열기", use_container_width=True, key="open_settings_modal_button"):
        st.session_state["show_settings_modal"] = True'''

if sidebar_btn_target in content:
    content = content.replace(sidebar_btn_target, sidebar_btn_replacement)
else:
    print("Could not find the sidebar settings button to inject campus button.")

# 3. Add Part navigation hook to clear current_view
# Find:
#     st.session_state.sidebar_part = part
# Replace with:
#     st.session_state.sidebar_part = part
#     st.session_state["current_view"] = "part"
part_nav_target = '''    st.session_state.sidebar_part = part'''
part_nav_replacement = '''    st.session_state.sidebar_part = part
    if st.session_state.get("current_view") == "research_campus":
        st.session_state["current_view"] = "part"
        st.rerun()'''

if part_nav_target in content:
    content = content.replace(part_nav_target, part_nav_replacement)
else:
    print("Could not find part nav target.")

# 4. Add rendering logic for the campus view
# Find where Part 1 is rendered, usually something like cur_p == "파트 1: 벤치마킹 & 자료조사"
# Since we need to intercept rendering entirely if current_view is research_campus, we can inject it right after the sidebar block ends.
# The sidebar usually ends around line 5120 where @st.dialog or def main(): or similar continues.
# Let's search for the start of the right conversation layout.
# Right column and left column usually start with col_main, col_chat = st.columns([7, 3]) or similar.
# Let's just find with st.sidebar: and find where it ends or inject at the beginning of the main layout.

# A safer approach is to inject right before if cur_p.startswith("파트 1"): or similar.
render_target = '''# =====================================================================
# 9. 메인 화면 렌더링 (Part 1 ~ 8)
# ====================================================================='''

render_replacement = '''# =====================================================================
# 8.5 학교 연구기관 렌더링
# =====================================================================
if st.session_state.get("current_view") == "research_campus":
    render_research_campus()
    st.stop()

# =====================================================================
# 9. 메인 화면 렌더링 (Part 1 ~ 8)
# ====================================================================='''

if render_target in content:
    content = content.replace(render_target, render_replacement)
else:
    print("Could not find render target.")

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)

print("Updated app_v17_2_4.py")
