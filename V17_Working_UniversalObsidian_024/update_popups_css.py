import codecs

with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Replace the single '테마 / 화면 스타일' with the expanded one.
old_theme_block = '''    st.divider()
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
    )'''

new_theme_block = '''    st.divider()
    st.subheader("테마 / 화면 스타일")

    with st.expander("🎨 세부 UI 색상", expanded=False):
        st.markdown("#### 1. 기본 화면 색상")
        background_color = st.color_picker("바탕색 (Background)", value=app_settings.get("background_color", "#FFFFFF"), key="settings_background_color_input")
        sidebar_color = st.color_picker("사이드바 색상 (Sidebar)", value=app_settings.get("sidebar_color", "#F7F7F7"), key="settings_sidebar_color_input")
        accent_color = st.color_picker("강조색 (Accent)", value=app_settings.get("accent_color", "#B8860B"), key="settings_accent_color_input")
        text_color = st.color_picker("글자색 (Text)", value=app_settings.get("text_color", "#111111"), key="settings_text_color_input")

        st.markdown("#### 2. 버튼 색상")
        button_background_color = st.color_picker("기본 버튼 배경색", value=app_settings.get("button_background_color", "transparent"), key="settings_btn_bg_color")
        button_text_color = st.color_picker("기본 버튼 글자색", value=app_settings.get("button_text_color", "#B8860B"), key="settings_btn_txt_color")
        button_border_color = st.color_picker("기본 버튼 테두리색", value=app_settings.get("button_border_color", "rgba(184, 134, 11, 0.4)"), key="settings_btn_brd_color")
        edit_button_background_color = st.color_picker("편집 버튼 배경색", value=app_settings.get("edit_button_background_color", "#1E293B"), key="settings_btn_edit_bg")
        save_button_background_color = st.color_picker("저장 버튼 배경색", value=app_settings.get("save_button_background_color", "#B8860B"), key="settings_btn_save_bg")
        send_button_background_color = st.color_picker("전송 버튼 배경색", value=app_settings.get("send_button_background_color", "#059669"), key="settings_btn_send_bg")

        st.markdown("#### 3. 입력창 / 카드 색상")
        card_background_color = st.color_picker("본문 카드 배경색", value=app_settings.get("card_background_color", "rgba(30,41,59,0.45)"), key="settings_card_bg_color")
        input_background_color = st.color_picker("입력창 배경색", value=app_settings.get("input_background_color", "rgba(15,23,42,0.6)"), key="settings_inp_bg_color")
        input_text_color = st.color_picker("입력창 글자색", value=app_settings.get("input_text_color", "#F5E9D3"), key="settings_inp_txt_color")

        st.markdown("#### 4. 팝업 색상")
        popup_background_color = st.color_picker("팝업 배경색", value=app_settings.get("popup_background_color", "#1E293B"), key="settings_pop_bg_color")
        popup_text_color = st.color_picker("팝업 글자색", value=app_settings.get("popup_text_color", "#F5E9D3"), key="settings_pop_txt_color")'''

old_save_block = '''            app_settings["sidebar_color"] = sidebar_color
            app_settings["accent_color"] = accent_color
            app_settings["text_color"] = text_color'''

new_save_block = '''            app_settings["sidebar_color"] = sidebar_color
            app_settings["accent_color"] = accent_color
            app_settings["text_color"] = text_color
            app_settings["button_background_color"] = button_background_color
            app_settings["button_text_color"] = button_text_color
            app_settings["button_border_color"] = button_border_color
            app_settings["edit_button_background_color"] = edit_button_background_color
            app_settings["save_button_background_color"] = save_button_background_color
            app_settings["send_button_background_color"] = send_button_background_color
            app_settings["card_background_color"] = card_background_color
            app_settings["input_background_color"] = input_background_color
            app_settings["input_text_color"] = input_text_color
            app_settings["popup_background_color"] = popup_background_color
            app_settings["popup_text_color"] = popup_text_color'''

if old_theme_block in content:
    content = content.replace(old_theme_block, new_theme_block)
    content = content.replace(old_save_block, new_save_block)
    with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Updated sage_popups_v17_2_4.py successfully.")
else:
    print("Could not find theme block in sage_popups_v17_2_4.py")

