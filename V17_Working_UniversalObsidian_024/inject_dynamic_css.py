import codecs

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

dynamic_css_code = '''
# =====================================================================
# 1.1 동적 테마 CSS 주입
# =====================================================================
_app_settings = st.session_state.get("app_settings", {})
_bg_color = _app_settings.get("background_color", "#0e1117")
_sidebar_color = _app_settings.get("sidebar_color", "#262730")
_accent_color = _app_settings.get("accent_color", "#B8860B")
_text_color = _app_settings.get("text_color", "#fafafa")

_dynamic_css = f"""
<style>
    .stApp {{ background-color: {_bg_color} !important; color: {_text_color} !important; }}
    [data-testid="stSidebar"] {{ background-color: {_sidebar_color} !important; }}
    .stButton>button {{ border-color: {_accent_color} !important; color: {_accent_color} !important; }}
    .stButton>button:hover {{ background-color: {_accent_color} !important; color: #ffffff !important; }}
    .stButton>button[kind="primary"] {{ background-color: {_accent_color} !important; color: #ffffff !important; }}
    a {{ color: {_accent_color} !important; }}
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown span {{ color: {_text_color} !important; }}
</style>
"""
st.markdown(_dynamic_css, unsafe_allow_html=True)
'''

target_str = 'st.markdown(GLOBAL_CSS, unsafe_allow_html=True)'

if target_str in content:
    content = content.replace(target_str, target_str + '\n' + dynamic_css_code)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Injected dynamic CSS successfully.")
else:
    print("Could not find target string for CSS injection.")

