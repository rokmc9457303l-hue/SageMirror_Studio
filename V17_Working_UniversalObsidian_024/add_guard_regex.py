import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

guard = '''
    if "show_settings_modal" not in st.session_state:
        st.session_state["show_settings_modal"] = False
'''
content = re.sub(r'(st\.markdown\("#### 🔄 Part 이동"\))', r'\1' + guard, content)

with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
    f.write(content)
print("Added guard via regex")

