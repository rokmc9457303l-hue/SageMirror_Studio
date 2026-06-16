import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Add the variable definitions right after _text_color
insert_vars = '''
_btn_bg = _app_settings.get("button_background_color", "transparent")
_btn_txt = _app_settings.get("button_text_color", _accent_color)
_btn_brd = _app_settings.get("button_border_color", "rgba(184, 134, 11, 0.4)")
_btn_edit = _app_settings.get("edit_button_background_color", "#1E293B")
_btn_save = _app_settings.get("save_button_background_color", "#B8860B")
_btn_send = _app_settings.get("send_button_background_color", "#059669")
_card_bg = _app_settings.get("card_background_color", "rgba(30,41,59,0.45)")
_inp_bg = _app_settings.get("input_background_color", "rgba(15,23,42,0.6)")
_inp_txt = _app_settings.get("input_text_color", "#F5E9D3")
_pop_bg = _app_settings.get("popup_background_color", "#1E293B")
_pop_txt = _app_settings.get("popup_text_color", "#F5E9D3")
'''

content = re.sub(r'(_text_color\s*=\s*_app_settings\.get\("text_color",\s*"#111111"\))', r'\1\n' + insert_vars, content)

# Update the :root block
old_root = '''<style>
:root {
    --v17-bg: {_bg_color};
    --v17-sidebar: {_sidebar_color};
    --v17-accent: {_accent_color};
    --v17-text: {_text_color};
}'''

new_root = '''<style>
:root {
    --v17-bg: {_bg_color};
    --v17-sidebar: {_sidebar_color};
    --v17-accent: {_accent_color};
    --v17-text: {_text_color};
    --v17-btn-bg: {_btn_bg};
    --v17-btn-txt: {_btn_txt};
    --v17-btn-brd: {_btn_brd};
    --v17-btn-edit: {_btn_edit};
    --v17-btn-save: {_btn_save};
    --v17-btn-send: {_btn_send};
    --v17-card-bg: {_card_bg};
    --v17-inp-bg: {_inp_bg};
    --v17-inp-txt: {_inp_txt};
    --v17-pop-bg: {_pop_bg};
    --v17-pop-txt: {_pop_txt};
}'''

content = content.replace(old_root, new_root)

# Update the CSS rules block at the end of _dynamic_css
new_css_rules = '''
/* CSS Overrides for New UI Colors */

/* 본문 카드 */
div[data-testid="stVerticalBlock"] > div > div[style*="border-radius"] {
    background-color: var(--v17-card-bg) !important;
}

/* 입력창 */
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
    background-color: var(--v17-inp-bg) !important;
    color: var(--v17-inp-txt) !important;
}

/* 기본 버튼 */
div.stButton > button {
    background-color: var(--v17-btn-bg) !important;
    color: var(--v17-btn-txt) !important;
    border-color: var(--v17-btn-brd) !important;
}

/* Primary 버튼 (저장 등) */
div.stButton > button[kind="primary"] {
    background-color: var(--v17-btn-save) !important;
    color: #ffffff !important;
    border-color: var(--v17-btn-save) !important;
}

/* 모달/다이얼로그 (팝업) */
div[data-testid="stDialog"] div[role="dialog"] {
    background-color: var(--v17-pop-bg) !important;
    color: var(--v17-pop-txt) !important;
}

div[data-testid="stDialog"] div[role="dialog"] * {
    color: var(--v17-pop-txt);
}

/* Sidebar Click Block Fix */
section[data-testid="stSidebar"] {
    pointer-events: auto !important;
    z-index: 10 !important;
}

section[data-testid="stSidebar"] * {
    pointer-events: auto !important;
}

div[data-testid="stSidebarContent"] {
    pointer-events: auto !important;
}

.stRadio, .stButton, .stExpander {
    pointer-events: auto !important;
}

</style>
"""'''

content = content.replace('</style>\n"""', new_css_rules)

# Add show_settings_modal guard near part move
guard_block = '''    st.markdown("#### 🔄 Part 이동")
    if "show_settings_modal" not in st.session_state:
        st.session_state["show_settings_modal"] = False
    part_idx = part_options.index(cur_p) if cur_p in part_options else 0'''

content = content.replace('''    st.markdown("#### 🔄 Part 이동")
    part_idx = part_options.index(cur_p) if cur_p in part_options else 0''', guard_block)

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)
print("Updated app_v17_2_4.py via python script successfully.")
