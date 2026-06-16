import codecs

file_path = r'C:\SageMirror_Production\V17_Working_UniversalObsidian_024\app_v17_2_4.py'

with codecs.open(file_path, 'r', 'utf-8-sig') as f:
    content = f.read()

dynamic_css = '''
# ── Dynamic Theme CSS Injection ──
theme = st.session_state.get("theme_settings", {
    "background_color": "#FFFFFF",
    "sidebar_color": "#F7F7F7",
    "accent_color": "#B8860B",
    "text_color": "#111111"
})
st.markdown(f"""
<style>
/* Main Background */
.stApp {{
    background-color: {theme.get('background_color', '#FFFFFF')} !important;
    color: {theme.get('text_color', '#111111')} !important;
}}
/* Sidebar Background */
[data-testid="stSidebar"] {{
    background-color: {theme.get('sidebar_color', '#F7F7F7')} !important;
}}
/* Global Text Color overrides for markdown */
.stMarkdown {{
    color: {theme.get('text_color', '#111111')} !important;
}}
/* Accent Elements */
.stButton button[kind="primary"] {{
    background-color: {theme.get('accent_color', '#B8860B')} !important;
    border-color: {theme.get('accent_color', '#B8860B')} !important;
    color: #FFFFFF !important;
}}
.sage-header {{
    border-left: 4px solid {theme.get('accent_color', '#B8860B')} !important;
    color: {theme.get('accent_color', '#B8860B')} !important;
}}
</style>
""", unsafe_allow_html=True)
'''

target = 'st.markdown(GLOBAL_CSS, unsafe_allow_html=True)'
if target in content:
    content = content.replace(target, target + '\n' + dynamic_css)
else:
    print('GLOBAL_CSS not found in app_v17_2_4.py!')
    
with codecs.open(file_path, 'w', 'utf-8-sig') as f:
    f.write(content)

print('Dynamic CSS injected.')
