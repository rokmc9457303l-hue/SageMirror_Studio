# -*- coding: utf-8 -*-
import os

def main():
    target_file = r"C:\SageMirror_Production\app_v13_26.py"
    
    # 1. 파일 읽기 (UTF-8 인코딩)
    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    lines = content.splitlines()
    
    # "with tab_bench:"가 시작되는 인덱스 검색 (Part 1 영역)
    start_idx = -1
    for i, line in enumerate(lines):
        if "with tab_bench:" in line:
            if 1700 < i < 1900:
                start_idx = i
                break
                
    # "with tab_plan:"이 시작되는 인덱스 검색
    end_idx = -1
    for i, line in enumerate(lines):
        if "with tab_plan:" in line:
            if 1900 < i < 2100:
                end_idx = i
                break
                
    if start_idx == -1 or end_idx == -1:
        print(f"오류: 치환 영역을 찾을 수 없습니다. (start: {start_idx}, end: {end_idx})")
        return
        
    print(f"치환 영역 발견! 라인 {start_idx+1}부터 {end_idx}까지 교체합니다.")
    
    # 3. 새롭게 삽입할 3단 버튼 및 프롬프트 텍스트 영역 코드
    # (on_change= 제거, Streamlit 양방향 바인딩 준수)
    new_tabs_code = r"""    with tab_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 벤치마킹 분석")
            st.caption("주제 20개 추천 (추천사유, 효과, 반응)")
            
            st.session_state.p1_bench_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (벤치마킹)", 
                value=st.session_state.p1_bench_prompt, 
                height=100, 
                key="p1_bench_prompt_input",
                disabled=is_locked
            )
            
            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---
            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])
            with c_btn1:
                if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked, key="p1_bench_start_btn"):
                    if not st.session_state.p1_channel_url: 
                        st.error("[WARN] 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")
                    else:
                        # 시작 버튼 클릭 즉시 기존 결과물 및 백업 상태 클리어
                        st.session_state.p1_bench_raw = ""
                        st.session_state.p1_topics = []
                        st.session_state.p1_bench_tags = ""
                        st.session_state.p1_bench_saved = False
                        st.session_state.p1_bench_obsidian_saved = False
                        save_workspace_state()
                        
                        with st.spinner("채널 분석 중... (200개 댓글 공감 포인트 참조)"):
                            raw_res, parsed_topics = analyze_channel_to_topics_p1(
                                st.session_state.p1_channel_url,
                                st.session_state.p1_region, 
                                st.session_state.obsidian_rules, 
                                st.session_state.base_prompt_rules, 
                                st.session_state.p1_gemma_protocol,
                                st.session_state.p1_bench_prompt
                            )
                            st.session_state.p1_bench_raw = raw_res
                            st.session_state.p1_topics = parsed_topics
                            st.session_state.pipeline_state["topic_candidates"] = parsed_topics
                            st.session_state.p1_bench_saved = True
                            save_workspace_state()
                            
                            # 젬마가 키워드를 자동으로 세분화하여 추출
                            keywords = extract_keywords_via_gemma(raw_res, st.session_state.base_prompt_rules)
                            st.session_state.p1_bench_tags = keywords
                            
                            # 자동 옵시디언 RAG 백업 파일 조립 및 저장
                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                            
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            folder_name = "TopicMemory"
                            title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"
                            
                            val = f"## 📌 핵심 요약\n- 채널: {st.session_state.p1_channel_url}\n- 타겟 지역: {st.session_state.p1_region}\n\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"
                            val += f"## 📖 벤치마킹 상세 추천 리스트\n"
                            for t in parsed_topics:
                                val += f"### [[{t['title']}]]\n- **추천 사유(체험담 기반):** {t['reason']}\n- **예상 효과:** {t['effect']}\n- **예상 반응:** {t['audience_reaction']}\n\n"
                            val += f"\n## 🔗 원본 날것의 텍스트\n```text\n{raw_res}\n```\n"
                            
                            obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)
                            if obs_path:
                                lock_file_readonly(obs_path)
                                st.toast("💾 벤치마킹 결과 로컬 자동 저장 완료!", icon="💾")
                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                if success:
                                    st.session_state.p1_bench_obsidian_saved = True
                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                else:
                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                save_workspace_state()
                                st.rerun()
            
            with c_btn2:
                if st.session_state.get("p1_bench_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_bench_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_bench_local_waiting")
            
            with c_btn3:
                if st.session_state.get("p1_bench_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_bench_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_bench_obs_waiting")
            
            if st.session_state.p1_bench_raw:
                st.markdown("##### 📝 벤치마킹 분석 결과 원본 (수정 가능 — 수정 시 실시간 자동 파싱)")
                st.session_state.p1_bench_raw = st.text_area(
                    "벤치마킹 원본 텍스트", 
                    value=st.session_state.p1_bench_raw, 
                    height=300, 
                    key="p1_bench_raw_ta", 
                    disabled=is_locked
                )
                
                c_reparse, c_popup = st.columns(2)
                with c_reparse:
                    if st.button("🔄 수정 텍스트 기반 주제 재파싱", use_container_width=True, key="p1_reparse_btn"):
                        st.session_state.p1_topics = _parse_topics(st.session_state.p1_bench_raw)
                        st.success("수정된 텍스트에서 주제 20개가 재파싱되었습니다!")
                        save_workspace_state()
                        st.rerun()
                with c_popup:
                    if st.button("[SEARCH] 팝업에서 크게 보기", use_container_width=True, key="p1_bench_pop_btn"):
                        popup_edit_benchmarking()

            if st.session_state.p1_topics:
                st.markdown("<br>", unsafe_allow_html=True)
                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p1_topics)]
                st.session_state.p1_topic_selection = st.selectbox("📌 기획할 주제 1개 선정", topics_display, disabled=is_locked, key="p1_topic_selection_box")
                st.session_state.pipeline_state["selected_topic"] = st.session_state.p1_topic_selection
                save_workspace_state()

                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p1_bench_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_bench_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_bench_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 (예비용) 벤치마킹 수동 옵시디언 백업 실행", use_container_width=True, key="p1_bench_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_bench_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    folder_name = "TopicMemory"
                    title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"
                    
                    val = f"## 📌 핵심 요약\n- 채널: {st.session_state.p1_channel_url}\n- 타겟 지역: {st.session_state.p1_region}\n\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"
                    val += f"## 📖 벤치마킹 상세 추천 리스트\n"
                    for t in st.session_state.p1_topics:
                        val += f"### [[{t['title']}]]\n- **추천 사유(체험담 기반):** {t['reason']}\n- **예상 효과:** {t['effect']}\n- **예상 반응:** {t['audience_reaction']}\n\n"
                    val += f"\n## 🔗 원본 날것의 텍스트\n```text\n{st.session_state.p1_bench_raw}\n```\n"
                    
                    obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 벤치마킹 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p1_bench_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save (Locked): {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                        st.rerun()

    with tab_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 자료 조사 결과")
            st.caption("옵시디언/리서치 융합 기초 초안 작성 (출처 명기)")
            
            st.session_state.p1_research_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (자료 조사)", 
                value=st.session_state.p1_research_prompt, 
                height=100, 
                key="p1_research_prompt_input",
                disabled=is_locked
            )
            
            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---
            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])
            with c_btn1:
                if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p1_research_start_btn"):
                    if not st.session_state.p1_topic_selection:
                        st.error("[WARN] 먼저 좌측의 '벤치마킹 시작' 버튼을 눌러 분석을 완료하고 주제를 선택해 주세요.")
                    else:
                        # 시작 즉시 리셋
                        st.session_state.p1_research_result = ""
                        st.session_state.p1_research_tags = ""
                        st.session_state.p1_research_saved = False
                        st.session_state.p1_research_obsidian_saved = False
                        save_workspace_state()
                        
                        with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):
                            topic_str = st.session_state.p1_topic_selection
                            res = generate_research_draft_p1(
                                 st.session_state.p1_channel_url, 
                                 topic_str,
                                 st.session_state.p1_gemma_protocol, 
                                 st.session_state.base_prompt_rules,
                                 st.session_state.p1_research_prompt
                            )
                            st.session_state.p1_research_result = res
                            st.session_state.pipeline_state["research_result"] = res
                            st.session_state.p1_research_saved = True
                            save_workspace_state()
                            
                            # 젬마 키워드 자동 세분화
                            keywords = extract_keywords_via_gemma(res, st.session_state.base_prompt_rules)
                            st.session_state.p1_research_tags = keywords
                            
                            # 자동 옵시디언 백업 진행
                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                            
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            folder_name = "ResearchMemory"
                            topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                            title = f"자료조사 초안 - {topic_title}"
                            
                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                            val += f"## 📖 자료조사 및 초안 본문\n{res}\n\n"
                            
                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                            if obs_path:
                                lock_file_readonly(obs_path)
                                st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                if success:
                                    st.session_state.p1_research_obsidian_saved = True
                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                else:
                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                save_workspace_state()
                                st.rerun()
            
            with c_btn2:
                if st.session_state.get("p1_research_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_research_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_research_local_waiting")
            
            with c_btn3:
                if st.session_state.get("p1_research_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_research_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_research_obs_waiting")
            
            if st.session_state.p1_research_result:
                st.markdown("<br>", unsafe_allow_html=True)
                st.session_state.p1_research_result = st.text_area(
                    "자료 조사 결과 (수정 가능)", 
                    value=st.session_state.p1_research_result, 
                    height=350, 
                    key="p1_research_result_ta",
                    disabled=is_locked
                )
                
                if st.button("[SEARCH] 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_res_p1"):
                    popup_edit_research()
 
                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p1_research_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_research_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_research_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 (예비용) 자료조사 결과 수동 옵시디언 백업 실행", use_container_width=True, key="p1_research_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_research_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    folder_name = "ResearchMemory"
                    
                    topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                    title = f"자료조사 초안 - {topic_title}"
                    
                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                    val += f"## 📖 자료조사 및 초안 본문\n{st.session_state.p1_research_result}\n\n"
                    
                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 자료조사 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p1_research_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save (Locked): {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                        st.rerun()
"""
    
    # 개행 문자를 윈도우 스타일인 \r\n으로 명시하여 조인하여 개행 꼬임을 예방
    # 윈도우 인코딩 파일은 \r\n을 유지해주는 것이 좋습니다.
    # 또한 content가 \r\n을 사용하는지 \n을 사용하는지 파악하여 조인합니다.
    line_ending = "\r\n" if "\r\n" in content else "\n"
    updated_lines = lines[:start_idx] + [new_tabs_code] + lines[end_idx:]
    
    # 덮어쓰기
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(line_ending.join(updated_lines))
        
    print("SUCCESS: replace completed successfully.")

if __name__ == "__main__":
    main()
