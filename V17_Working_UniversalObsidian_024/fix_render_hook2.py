import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Remove old hook
old_hook = '''# =====================================================================
# 8.5 학교 연구기관 렌더링
# =====================================================================
if st.session_state.get("current_view") == "research_campus":
    render_research_campus()
    st.stop()

'''
content = content.replace(old_hook, '')

# Add new hook inside main_col
target_main_col = '''with main_col:
    if part.startswith("파트 1"):'''

new_main_col = '''with main_col:
    if st.session_state.get("current_view") == "research_campus":
        render_research_campus()
    elif part.startswith("파트 1"):'''

if target_main_col in content:
    content = content.replace(target_main_col, new_main_col)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed render hook location.")
else:
    print("Target not found.")

