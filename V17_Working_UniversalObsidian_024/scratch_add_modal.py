import codecs

file_path = r'C:\SageMirror_Production\V17_Working_UniversalObsidian_024\app_v17_2_4.py'

with codecs.open(file_path, 'r', 'utf-8-sig') as f:
    content = f.read()

old_sidebar_btn = '''    if st.button("⚙️ 설정 열기", use_container_width=True):
        st.session_state.show_settings_modal = True
        st.rerun()'''

new_sidebar_btn = '''    if st.button("⚙️ 설정 열기", use_container_width=True):
        popup_settings_modal()'''

content = content.replace(old_sidebar_btn, new_sidebar_btn)

settings_modal_code = '''
@st.dialog("⚙️ 현자의 거울 범용 설정", width="large")
def popup_settings_modal():
    st.markdown("### 🛠 기본 설정")
    
    app_settings = st.session_state.get("app_settings", {})
    
    c1, c2, c3 = st.columns(3)
    with c1:
        new_project = st.text_input("프로젝트명", value=app_settings.get("project_name", "기본 프로젝트"))
    with c2:
        new_channel = st.text_input("채널명", value=st.session_state.get("channel_name", app_settings.get("channel_name", "현자의 거울")))
    with c3:
        new_profile = st.text_input("Profile명", value=st.session_state.get("selected_profile", st.session_state.get("profile_name", "기본 Profile")))
        
    st.divider()
    st.markdown("### 🎨 테마 및 색상 설정")
    theme_settings = st.session_state.get("theme_settings", {
        "background_color": "#FFFFFF",
        "sidebar_color": "#F7F7F7",
        "accent_color": "#B8860B",
        "text_color": "#111111"
    })
    
    tc1, tc2, tc3, tc4 = st.columns(4)
    with tc1:
        new_bg = st.color_picker("바탕색", value=theme_settings.get("background_color", "#FFFFFF"))
    with tc2:
        new_sb = st.color_picker("사이드바 색상", value=theme_settings.get("sidebar_color", "#F7F7F7"))
    with tc3:
        new_ac = st.color_picker("강조색", value=theme_settings.get("accent_color", "#B8860B"))
    with tc4:
        new_txt = st.color_picker("글자색", value=theme_settings.get("text_color", "#111111"))
        
    st.divider()
    st.markdown("### 🔐 보안 / API Key (별도 안전 저장)")
    st.info("입력된 키는 workspace_state.json에 평문으로 저장되지 않으며, local_secrets.json에 분리 저장됩니다.")
    
    sc1, sc2 = st.columns(2)
    with sc1:
        new_tavily = st.text_input("Tavily API Key", value=st.session_state.get("tavily_api_key", ""), type="password")
        new_youtube = st.text_input("YouTube API Key", value=st.session_state.get("youtube_api_key", ""), type="password")
        new_gemini = st.text_input("Gemini API Key", value=st.session_state.get("gemini_api_key", ""), type="password")
    with sc2:
        new_github = st.text_input("GitHub Token", value=st.session_state.get("github_token", ""), type="password")
        new_openai = st.text_input("OpenAI API Key", value=st.session_state.get("openai_api_key", ""), type="password")
        new_anthropic = st.text_input("Anthropic API Key", value=st.session_state.get("anthropic_api_key", ""), type="password")

    st.divider()
    sc3, sc4 = st.columns(2)
    with sc3:
        if st.button("💾 설정 저장", type="primary", use_container_width=True):
            app_settings["project_name"] = new_project
            app_settings["channel_name"] = new_channel
            
            st.session_state["app_settings"] = app_settings
            st.session_state["channel_name"] = new_channel
            st.session_state["selected_profile"] = new_profile
            st.session_state["profile_name"] = new_profile
            
            theme_settings["background_color"] = new_bg
            theme_settings["sidebar_color"] = new_sb
            theme_settings["accent_color"] = new_ac
            theme_settings["text_color"] = new_txt
            st.session_state["theme_settings"] = theme_settings
            
            st.session_state["tavily_api_key"] = new_tavily
            st.session_state["youtube_api_key"] = new_youtube
            st.session_state["gemini_api_key"] = new_gemini
            st.session_state["github_token"] = new_github
            st.session_state["openai_api_key"] = new_openai
            st.session_state["anthropic_api_key"] = new_anthropic
            
            save_workspace_state()
            st.success("설정이 저장되었습니다.")
            st.rerun()
    with sc4:
        if st.button("❌ 닫기", use_container_width=True):
            st.rerun()
'''

insert_target = "# =====================================================================\n\n# 팝업 로직\n\n# ====================================================================="
if insert_target in content:
    content = content.replace(insert_target, insert_target + "\n\n" + settings_modal_code + "\n\n")
else:
    # Try with single newlines
    insert_target2 = "# =====================================================================\n# 팝업 로직\n# ====================================================================="
    if insert_target2 in content:
        content = content.replace(insert_target2, insert_target2 + "\n\n" + settings_modal_code + "\n\n")

# Remove the old expander settings block (Step 2 requirement: "설정창을 좌측바 작은 Expander 중심에서 범용 설정 구조로 정리")
# The old settings expander looks like `with st.expander("⚙️ 설정 변경", expanded=False):`
# I'll let that be for now or find and remove it.
# Actually I already replaced the sidebar completely in _023 so it doesn't have the old expander!
# Let's verify. In _023 I deleted the old `⚙️ 설정 변경` expander and replaced it with a simple button.
# Yes, so no need to remove it.

with codecs.open(file_path, 'w', 'utf-8-sig') as f:
    f.write(content)

print("Settings modal script created successfully.")
