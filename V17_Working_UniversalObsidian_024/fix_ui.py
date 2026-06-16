import codecs

with codecs.open('ui/research_campus.py', 'r', 'utf-8') as f:
    content = f.read()

target = 'st.title("🏫 현자의 거울 학교 연구기관")'
replacement = '''if st.button("← 학교 나가기 / Part 화면으로 복귀", use_container_width=True):
        st.session_state["current_view"] = "part"
        st.session_state["show_settings_modal"] = False
        st.rerun()
        
    st.title("🏫 현자의 거울 학교 연구기관")'''

if target in content:
    content = content.replace(target, replacement)
    with codecs.open('ui/research_campus.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Added close button to ui/research_campus.py")
else:
    print("Target not found.")

