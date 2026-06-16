def render_top_panel():
    db_ok = os.path.exists(WORKSPACE_STATE_FILE)
    sync_req = st.session_state.get("sync_required", False)
    
    project_name = st.session_state.get("project_name", "Universal Obsidian Studio")
    profile_name = st.session_state.get("profile_name", "Gemma-2-9b-it")
    current_step = st.session_state.get("current_step", "초기화")
    
    # 우측 패널 상태 수집
    right_auto_save = st.session_state.get("right_auto_save_status", "대기")
    right_rag_queue = len(st.session_state.get("right_research_inbox", []))

    # 시스템 오류 상태 점검 (간단한 예시)
    errors = []
    if not db_ok: errors.append("DB 없음")
    if sync_req: errors.append("동기화 필요")
    
    auto_status = "자동화 정상" if not errors else "자동화 경고"
    save_status = "저장 정상" if right_auto_save in ["대기", "저장 완료", "저장 완료(중복)"] else "저장 오류"
    error_text = "오류 없음" if not errors else " | ".join(errors)

    st.markdown(f"""
    <div style="background: rgba(30,41,59,0.45); border: 1.5px solid rgba(212,175,106,0.3); border-radius: 12px; padding: 14px 20px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        <div style="font-size: 0.85em; color: #94a3b8; margin-bottom: 8px;">Project: <b>{{project_name}}</b> &nbsp;|&nbsp; Profile: <b>{{profile_name}}</b></div>
        <div style="font-size: 0.9em; color: #f5e9d3; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            {'<span style="color:#10B981;">🟢</span>' if not errors else '<span style="color:#F59E0B;">🟠</span>'}
            <span>{auto_status} | {save_status} | RAG 대기 {right_rag_queue}건 | {error_text}</span>
        </div>
        <div style="font-size: 0.9em; color: #f5e9d3;">현재 단계: <b>{{current_step}}</b></div>
    </div>
    """, unsafe_allow_html=True)

    with st.popover("연동 내역 및 고급 동기화", use_container_width=True):
        st.markdown("**고급 동기화 제어**")
        if st.button("전체 세션 강제 동기화", key="top_force_sync_btn", use_container_width=True):
            save_workspace_state()
            st.session_state.sync_required = False
            st.success("전체 동기화 완료!")
            st.rerun()
            
        st.divider()
        st.markdown("**리서치 내역**")
        base_dir = _get_obsidian_studio_dir()
        research_dir = os.path.join(base_dir, "01_Research_Data")
        try:
            if os.path.exists(research_dir):
                files = os.listdir(research_dir)
                md_files = [f for f in files if f.endswith(".md")]
                if md_files:
                    r_files = []
                    for f in md_files:
                        p = os.path.join(research_dir, f)
                        r_files.append((os.path.getmtime(p), f))
                    r_files.sort(key=lambda x: x[0], reverse=True)
                    for mtime, fname in r_files[:5]:
                        ts = datetime.datetime.fromtimestamp(mtime).strftime("%m/%d %H:%M")
                        st.markdown(f"- `{ts}` {fname.replace('.md', '')}")
                else:
                    st.info("저장된 리서치 내역이 없습니다.")
            else:
                st.info("리서치 폴더가 생성되지 않았습니다.")
        except Exception as e:
            st.error(f"내역 확인 오류: {e}")

    with st.expander("파트별 진행 상황", expanded=False):
        def _dot_cls(flag):
            return "🟢" if flag else "⚪"
            
        nodes = [
            (st.session_state.get("p1_topic_selection", ""), "주제"),
            (st.session_state.get("p2_planning_result", ""), "기획안"),
            (st.session_state.get("p34_image_script", ""), "대본"),
            (st.session_state.get("p5_c_rows", []), "C-1 분할"),
            (st.session_state.get("p6_opal_df", None) is not None, "Opal 배분"),
            (st.session_state.get("p7_capcut_df", None) is not None, "CapCut 조립")
        ]
        
        pipe_str = []
        for flag, label in nodes:
            pipe_str.append(f"{'🟢' if flag else '⚪'} {label}")
        st.markdown(" > ".join(pipe_str))

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 파트별 마스터 프롬프트", expanded=False):
        import traceback
        
        part_mapping = {
            "part1": ("base_prompt_rules",       "📚 파트 1 Librarian 전역 마스터 프롬프트"),
            "part2": ("part2_master_prompt",     "📚 파트 2 Director 전역 마스터 프롬프트"),
            "part3": ("part3_master_prompt",     "📚 파트 3/4 Producer 전역 마스터 프롬프트"),
            "part4": ("image_part_master_prompt","📚 파트 5 Image 전역 마스터 프롬프트"),
            "part5": ("video_part_master_prompt","📚 파트 6 Video 전역 마스터 프롬프트"),
            "part6": ("opal_master_prompt",      "📚 파트 6 Opal 전역 마스터 프롬프트"),
            "part7": ("capcut_master_prompt",    "📚 파트 7 CapCut 전역 마스터 프롬프트"),
            "part8": ("dashboard_master_prompt", "📚 파트 8 Dashboard 전역 마스터 프롬프트"),
        }
        
        current_part = "part1"
        for i in range(1, 9):
            if f"파트 {i}" in st.session_state.get("current_step", ""):
                current_part = f"part{i}"
                break
                
        prompt_key, prompt_title = part_mapping.get(current_part, part_mapping["part1"])
        prompt_widget_key = f"{prompt_key}_widget_top"
        
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown('<div class="sage-subtitle">옵시디언 전역 규칙 (Obsidian Rules)</div>', unsafe_allow_html=True)
            obsidian_val = st.session_state.get("obsidian_rules", "")
            if prompt_widget_key + "_obs" not in st.session_state:
                st.session_state[prompt_widget_key + "_obs"] = obsidian_val
            st.text_area("옵시디언 규칙서", height=180, key=prompt_widget_key + "_obs", label_visibility="collapsed")
            
            obs_btn_cols = st.columns(2)
            with obs_btn_cols[0]:
                if st.button("📝 편집", key="obs_edit_btn", use_container_width=True):
                    popup_edit_text_value("obsidian_rules", "옵시디언 전역 규칙서")
            with obs_btn_cols[1]:
                if st.button("💾 규칙서 저장", key="obs_save_btn", use_container_width=True):
                    st.session_state.obsidian_rules = st.session_state.get(prompt_widget_key + "_obs", "")
                    save_workspace_state()
                    st.toast("✅ 규칙서 저장 완료", icon="💾")
                    st.rerun()
                    
        with c2:
            st.markdown(f'<div class="sage-subtitle">{prompt_title}</div>', unsafe_allow_html=True)
            prompt_val = st.session_state.get(prompt_key, "")
            if prompt_widget_key not in st.session_state:
                st.session_state[prompt_widget_key] = prompt_val
            st.text_area("파트 마스터 프롬프트", height=180, key=prompt_widget_key, label_visibility="collapsed")

            pr_btn_cols = st.columns(2)
            with pr_btn_cols[0]:
                if st.button("📝 편집", key=f"pr_btn_{prompt_key}", use_container_width=True):
                    popup_edit_text_value(prompt_key, prompt_title)
            with pr_btn_cols[1]:
                if st.button("💾 마스터 프롬프트 저장", key=f"pr_save_btn_{prompt_key}", use_container_width=True):
                    st.session_state[prompt_key] = st.session_state.get(prompt_widget_key, "")
                    save_workspace_state()
                    st.toast("✅ 마스터 프롬프트 저장 완료", icon="💾")
                    st.rerun()
