import codecs

file_path = r'C:\SageMirror_Production\V17_Working_UniversalObsidian_023\app_v17_2_4.py'

with codecs.open(file_path, 'r', 'utf-8-sig') as f:
    lines = f.readlines()

new_lines = []
skip = False

import_added = False

for i, line in enumerate(lines):
    if 'import streamlit as st' in line and not import_added:
        new_lines.append(line)
        new_lines.append('import sys, os\n')
        new_lines.append('sys.path.append(os.path.join(os.path.dirname(__file__), "core"))\n')
        new_lines.append('try:\n')
        new_lines.append('    from agent_school import ensure_agent_school_state, get_school_status_summary, get_total_agent_count, get_packet_queue_summary, get_part_agents\n')
        new_lines.append('except Exception as e:\n')
        new_lines.append('    print(f"Agent school load error: {e}")\n')
        import_added = True
        continue
        
    if line.startswith('with st.sidebar:'):
        skip = True
        
        # Insert the new sidebar logic
        sidebar_code = '''with st.sidebar:
    try:
        ensure_agent_school_state(st.session_state)
    except NameError:
        pass
    
    project_name = st.session_state.get("app_settings", {}).get("project_name", "기본 프로젝트")
    channel_name = st.session_state.get("channel_name", st.session_state.get("app_settings", {}).get("channel_name", "현자의 거울"))
    profile_name = st.session_state.get("selected_profile", st.session_state.get("profile_name", "기본 Profile"))
    
    part_options = [
        "파트 1: 벤치마킹 & 자료조사",
        "파트 2: 총괄기획",
        "파트 3: 대본 작성",
        "파트 4: 이미지 생성",
        "파트 5: 영상 생성",
        "파트 6: 나레이션 & 배경음악",
        "파트 7: 숏폼 생성",
        "파트 8: 캡컷 최종 조립"
    ]
    cur_p = st.session_state.get("sidebar_part", part_options[0])
    
    st.markdown(f"### 🏢 {project_name}")
    st.markdown(f"**채널:** {channel_name}")
    st.markdown(f"**Profile:** {profile_name}")
    st.markdown(f"**현재:** {cur_p.split(':')[0]}")
    st.divider()

    st.markdown("#### 🏫 Agent School 상태")
    try:
        school_status = get_school_status_summary(st.session_state)
        total_agents = get_total_agent_count(st.session_state)
        queue_summary = get_packet_queue_summary(st.session_state)
        
        # Determine part_id from cur_p
        part_idx = part_options.index(cur_p) if cur_p in part_options else 0
        part_id = f"part{part_idx + 1}"
        part_agents_count = len(get_part_agents(st.session_state, part_id))
    except NameError:
        school_status = "모듈 로드 실패"
        total_agents = 0
        queue_summary = "알 수 없음"
        part_agents_count = 0
    
    last_cmd = st.session_state.get("agent_school", {}).get("last_command", "없음")
    
    st.write(f"- **상태:** {school_status}")
    st.write(f"- **총 Agent:** {total_agents}명")
    st.write(f"- **현재 Part Agent:** {part_agents_count}명")
    st.write(f"- **Packet Queue:** {queue_summary}")
    st.write(f"- **최근 명령:** {last_cmd}")
    st.divider()

    st.markdown("#### 🔄 Part 이동")
    part_idx = part_options.index(cur_p) if cur_p in part_options else 0
    part = st.radio("이동할 파트", part_options, index=part_idx, label_visibility="collapsed")
    st.session_state.sidebar_part = part
    st.divider()
    
    if st.button("⚙️ 설정 열기", use_container_width=True):
        st.session_state.show_settings_modal = True
        st.rerun()
        
    with st.expander("🛠 고급 정보 보기", expanded=False):
        st.write("**옵시디언 아카이브**")
        st.code(st.session_state.get("path_obsidian", "경로 미설정"))
        st.write("**GitHub Repo**")
        st.code(st.session_state.get("github_repo_url", "미설정"))
        
        if st.button("상태 수동 저장", use_container_width=True):
            save_workspace_state()
            st.success("저장 완료")
        if st.button("🔒 로그아웃", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

'''
        new_lines.append(sidebar_code)
        continue

    if skip:
        # Check if we hit the end of the sidebar section. We want to resume right before popup logic.
        if line.startswith('# =====================================================================') and '팝업 로직' in lines[i+2] if i+2 < len(lines) else False:
            skip = False
            new_lines.append(line)
        elif line.startswith('# =====================================================================') and i > 5120:
            skip = False
            new_lines.append(line)
        continue
        
    new_lines.append(line)

with codecs.open(file_path, 'w', 'utf-8-sig') as f:
    f.writelines(new_lines)

print("Sidebar updated successfully.")
