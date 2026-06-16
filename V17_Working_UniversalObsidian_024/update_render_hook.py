import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

target = 'main_col, right_col = st.columns([7.2, 2.8], gap="large")'
replacement = '''# =====================================================================
# 8.5 학교 연구기관 렌더링
# =====================================================================
if st.session_state.get("current_view") == "research_campus":
    render_research_campus()
    st.stop()

main_col, right_col = st.columns([7.2, 2.8], gap="large")'''

if target in content and 'render_research_campus()' not in content:
    content = content.replace(target, replacement)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Injected campus render hook.")
else:
    print("Target not found or already injected.")
