import codecs
import re

# 1. Update app_v17_2_4.py
with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    app_content = f.read()

top_level_code = '''
# =====================================================================
# 1.5 팝업 초기화
# =====================================================================
if "show_settings_modal" not in st.session_state:
    st.session_state["show_settings_modal"] = False

if st.session_state.get("show_settings_modal", False):
    try:
        popup_settings_modal()
    except Exception as e:
        st.error(f"설정창 표시 오류: {e}")
        with st.container(border=True):
            st.subheader("⚙️ 설정")
            st.write("설정창 모달 호출에 실패하여 임시 설정 패널을 표시합니다.")
            if st.button("설정창 닫기", key="settings_fallback_close"):
                st.session_state["show_settings_modal"] = False
                st.rerun()
'''

app_content = app_content.replace('st.markdown(GLOBAL_CSS, unsafe_allow_html=True)', 'st.markdown(GLOBAL_CSS, unsafe_allow_html=True)\n' + top_level_code)

old_button = '''    if st.button("⚙️ 설정 열기", use_container_width=True):
        st.session_state.show_settings_modal = True
        st.rerun()'''

new_button = '''    if st.button("⚙️ 설정 열기", use_container_width=True, key="open_settings_modal_button"):
        st.session_state["show_settings_modal"] = True
        st.rerun()'''

app_content = app_content.replace(old_button, new_button)

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(app_content)

# 2. Update sage_popups_v17_2_4.py
with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    popups_content = f.read()

old_modal = re.search(r'@st\.dialog\("⚙️ 현자의 거울 설정".*?st\.rerun\(\)', popups_content, re.DOTALL)

new_modal = '''@st.dialog("⚙️ 설정")
def popup_settings_modal():
    st.subheader("기본 프로젝트 / 채널 / Profile")

    app_settings = st.session_state.setdefault("app_settings", {})

    project_name = st.text_input(
        "프로젝트명",
        value=app_settings.get("project_name", "기본 프로젝트"),
        key="settings_project_name_input"
    )

    channel_name = st.text_input(
        "채널명",
        value=app_settings.get("channel_name", st.session_state.get("channel_name", "현자의 거울")),
        key="settings_channel_name_input"
    )

    profile_name = st.text_input(
        "Profile명",
        value=app_settings.get("profile_name", "기본 Profile"),
        key="settings_profile_name_input"
    )

    st.divider()
    st.subheader("테마 / 화면 스타일")

    background_color = st.color_picker(
        "바탕색",
        value=app_settings.get("background_color", "#FFFFFF"),
        key="settings_background_color_input"
    )

    sidebar_color = st.color_picker(
        "사이드바 색상",
        value=app_settings.get("sidebar_color", "#F7F7F7"),
        key="settings_sidebar_color_input"
    )

    accent_color = st.color_picker(
        "강조색",
        value=app_settings.get("accent_color", "#B8860B"),
        key="settings_accent_color_input"
    )

    text_color = st.color_picker(
        "글자색",
        value=app_settings.get("text_color", "#111111"),
        key="settings_text_color_input"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("저장", use_container_width=True, key="settings_save_button"):
            app_settings["project_name"] = project_name
            app_settings["channel_name"] = channel_name
            app_settings["profile_name"] = profile_name
            app_settings["background_color"] = background_color
            app_settings["sidebar_color"] = sidebar_color
            app_settings["accent_color"] = accent_color
            app_settings["text_color"] = text_color

            st.session_state["app_settings"] = app_settings
            st.session_state["channel_name"] = channel_name
            st.session_state["profile_name"] = profile_name
            st.session_state["show_settings_modal"] = False

            if "save_workspace_state" in globals():
                save_workspace_state()

            st.rerun()

    with col2:
        if st.button("닫기", use_container_width=True, key="settings_close_button"):
            st.session_state["show_settings_modal"] = False
            st.rerun()'''

if old_modal:
    popups_content = popups_content.replace(old_modal.group(0), new_modal)
else:
    print("Could not find old modal in sage_popups_v17_2_4.py")

with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(popups_content)

print("Done")
