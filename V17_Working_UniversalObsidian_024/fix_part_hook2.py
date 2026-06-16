import codecs

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

target = '''    part = st.radio("이동할 파트", part_options, index=part_idx, label_visibility="collapsed")
    st.session_state.sidebar_part = part
    if st.session_state.get("current_view") == "research_campus":
        st.session_state["current_view"] = "part"
        st.rerun()'''

replacement = '''    part = st.radio("이동할 파트", part_options, index=part_idx, label_visibility="collapsed")
    if st.session_state.get("sidebar_part") != part:
        st.session_state.sidebar_part = part
        if st.session_state.get("current_view") == "research_campus":
            st.session_state["current_view"] = "part"
            st.rerun()'''

if target in content:
    content = content.replace(target, replacement)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed part navigation hook logic.")
else:
    print("Target not found. Doing line-by-line replacement...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'part = st.radio("이동할 파트"' in line:
            # We found it
            lines[i+1] = '    if st.session_state.get("sidebar_part") != part:'
            lines[i+2] = '        st.session_state.sidebar_part = part'
            lines[i+3] = '        if st.session_state.get("current_view") == "research_campus":'
            lines[i+4] = '            st.session_state["current_view"] = "part"'
            lines[i+5] = '            st.rerun()'
            break
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write('\n'.join(lines))
    print("Replaced line by line.")

