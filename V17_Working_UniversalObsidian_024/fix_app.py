import os

filepath = r"C:\SageMirror_Production\V17_Working_UniversalObsidian_024\app_v17_2_4.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 3968 근처 잘못 들어간 코드 제거
bad_code = """    write_to_both("03_Script", "Narration_Script.md", p34_narration)
    write_to_both("03_Script", "Image_Script.md", p34_image)

    _app_settings = st.session_state.get("app_settings", {})
    project_name = _app_settings.get("project_name", st.session_state.get("project_name", "기본 프로젝트"))
    channel_name = _app_settings.get("channel_name", st.session_state.get("channel_name", "현자의 거울"))
    profile_name = _app_settings.get("profile_name", st.session_state.get("selected_profile", st.session_state.get("profile_name", "기본 Profile")))

    import json"""

good_code = """    write_to_both("03_Script", "Narration_Script.md", p34_narration)
    write_to_both("03_Script", "Image_Script.md", p34_image)

    import json"""

content = content.replace(bad_code, good_code)

# 2. 5408 render_top_panel 로직 교체
old_top_panel = """    project_name = st.session_state.get("project_name", "기본 프로젝트")
    profile_name = st.session_state.get("selected_profile", st.session_state.get("profile_name", "기본 Profile"))
    current_step = st.session_state.get("current_step", "파트 1: 벤치마킹 & 자료조사")"""

new_top_panel = """    _app_settings = st.session_state.get("app_settings", {})
    project_name = _app_settings.get("project_name", st.session_state.get("project_name", "기본 프로젝트"))
    channel_name = _app_settings.get("channel_name", st.session_state.get("channel_name", "현자의 거울"))
    profile_name = _app_settings.get("profile_name", st.session_state.get("selected_profile", st.session_state.get("profile_name", "기본 Profile")))
    current_step = st.session_state.get("current_step", "파트 1: 벤치마킹 & 자료조사")"""

content = content.replace(old_top_panel, new_top_panel)

# 3. HTML div 교체
old_div = """<div style="font-size: 0.85em; color: #94a3b8; margin-bottom: 8px;">Project: <b>{project_name}</b> &nbsp;|&nbsp; Profile: <b>{profile_name}</b></div>"""
new_div = """<div style="font-size: 0.85em; color: #94a3b8; margin-bottom: 8px;">Project: <b>{project_name}</b> &nbsp;|&nbsp; Channel: <b>{channel_name}</b> &nbsp;|&nbsp; Profile: <b>{profile_name}</b></div>"""

content = content.replace(old_div, new_div)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement script executed.")
