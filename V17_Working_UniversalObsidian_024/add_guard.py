import codecs

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

target = '''    st.markdown("#### 🔄 Part 이동")
    part_idx = part_options.index(cur_p) if cur_p in part_options else 0'''

replacement = '''    st.markdown("#### 🔄 Part 이동")
    if "show_settings_modal" not in st.session_state:
        st.session_state["show_settings_modal"] = False
    part_idx = part_options.index(cur_p) if cur_p in part_options else 0'''

if target in content:
    content = content.replace(target, replacement)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Added guard for show_settings_modal")
else:
    print("Could not find the target string")

