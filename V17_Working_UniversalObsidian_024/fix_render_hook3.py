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

# Inject it inside main_col line by line
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'with main_col:' in line:
        lines.insert(i+1, '    if st.session_state.get("current_view") == "research_campus":')
        lines.insert(i+2, '        render_research_campus()')
        lines.insert(i+3, '        st.markdown("---")')
        break

# Now we must change if part.startswith("파트 1"): to elif part.startswith("파트 1"):
for i, line in enumerate(lines):
    if 'if part.startswith("파트 1"):' in line:
        lines[i] = line.replace('if', 'elif')
        break

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write('\n'.join(lines))
print("Fixed render hook location.")
