import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Let's replace the whole _dynamic_css block
target = '''_dynamic_css = f\"\"\"
<style>
:root {{
    --v17-bg: {_bg_color};
    --v17-sidebar: {_sidebar_color};
    --v17-accent: {_accent_color};
    --v17-text: {_text_color};
}}

.stApp {{
    background-color: var(--v17-bg) !important;
    color: var(--v17-text) !important;
}}

section[data-testid="stSidebar"] {{
    background-color: var(--v17-sidebar) !important;
}}

section[data-testid="stSidebar"] * {{
    color: var(--v17-text);
}}

div.stButton > button {{
    border-color: var(--v17-accent) !important;
}}

div.stButton > button:hover {{
    color: var(--v17-accent) !important;
    border-color: var(--v17-accent) !important;
}}

h1, h2, h3, h4 {{
    color: var(--v17-text) !important;
}}
</style>
\"\"\"'''

replacement = '''# UI CSS Variables Setup
_sidebar_txt = _app_settings.get("sidebar_text_color", "#FFFFFF")
_btn_bg = _app_settings.get("button_background_color", "#111827")
_btn_txt = _app_settings.get("button_text_color", "#FFFFFF")
_card_bg = _app_settings.get("card_background_color", "#F5F5F5")
_card_txt = _app_settings.get("card_text_color", "#111111")

_dynamic_css = f\"\"\"
<style>
:root {{
    --v17-bg: {_bg_color};
    --v17-sidebar: {_sidebar_color};
    --v17-accent: {_accent_color};
    --v17-text: {_text_color};
    --v17-sidebar-txt: {_sidebar_txt};
    --v17-btn-bg: {_btn_bg};
    --v17-btn-txt: {_btn_txt};
    --v17-card-bg: {_card_bg};
    --v17-card-txt: {_card_txt};
}}

.stApp {{
    background-color: var(--v17-bg) !important;
}}

section[data-testid="stSidebar"] {{
    background-color: var(--v17-sidebar) !important;
}}

section[data-testid="stSidebar"] {{
    color: var(--v17-sidebar-txt);
}}

div.stButton > button {{
    background-color: var(--v17-btn-bg) !important;
    color: var(--v17-btn-txt) !important;
    border-color: var(--v17-accent) !important;
}}

div.stButton > button:hover {{
    border-color: var(--v17-accent) !important;
    opacity: 0.9;
}}

div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {{
    color: var(--v17-text) !important;
}}
</style>
\"\"\"'''

if '_dynamic_css = f"""' in content:
    content = content.replace(target, replacement)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Replaced CSS")
else:
    print("Target not found.")

