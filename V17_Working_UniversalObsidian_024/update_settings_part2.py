import codecs

with codecs.open('sage_popups_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

# Remove the bad cols[1] block
bad_block = '''            st.rerun()
            
    with cols[1]:
        if st.button("닫기", use_container_width=True):
            st.session_state.show_settings_modal = False
            st.rerun()
    with c1:'''

good_block = '''            st.rerun()

    with st.expander("🛠 고급 기능", expanded=False):
        st.markdown("### 저장소 / 연동 상태")
        st.write("Obsidian Vault:", st.session_state.get("path_obsidian", "미설정"))
        st.write("GitHub Repo:", st.session_state.get("github_repo_url", "미설정"))

        st.markdown("### Agent School")
        st.write("Agent School 상태:", st.session_state.get("agent_school", {}).get("status", "미설정"))
        st.write("Packet Queue:", len(st.session_state.get("agent_school", {}).get("packet_queue", [])))

        st.markdown("### 다음 단계 예정")
        st.write("- API Key 보안 분리")
        st.write("- Provider 설정")
        st.write("- Prompt MD 편집")
        st.write("- Agent ON/OFF 설정")

    with c1:'''

if bad_block in content:
    content = content.replace(bad_block, good_block)
    with codecs.open('sage_popups_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Fixed sage_popups_v17_2_4.py")
else:
    print("Could not find bad block")

# 4단계: app_v17_2_4.py fallback 정리
with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    app_content = f.read()

old_fallback = '''if st.session_state.get("show_settings_modal", False):
    try:
        popup_settings_modal()
    except Exception as e:
        st.error(f"설정창 표시 오류: {e}")
        with st.container(border=True):
            st.subheader("⚙️ 설정")
            st.write("설정창 모달 호출에 실패하여 임시 설정 패널을 표시합니다.")
            if st.button("설정창 닫기", key="settings_fallback_close"):
                st.session_state["show_settings_modal"] = False
                st.rerun()'''

new_fallback = '''if st.session_state.get("show_settings_modal", False):
    try:
        popup_settings_modal()
    except Exception as e:
        st.error(f"설정창 표시 오류: {e}")
        with st.container(border=True):
            st.subheader("⚙️ 설정창 임시 패널")
            st.write("모달 호출에 실패하여 임시 설정 패널을 표시합니다.")
            if st.button("설정창 닫기", key="settings_fallback_close"):
                st.session_state["show_settings_modal"] = False
                st.rerun()'''

if old_fallback in app_content:
    app_content = app_content.replace(old_fallback, new_fallback)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(app_content)
    print("Fixed app_v17_2_4.py fallback")
else:
    print("Could not find old fallback")

