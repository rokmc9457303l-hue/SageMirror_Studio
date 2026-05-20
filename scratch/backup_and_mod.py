# -*- coding: utf-8 -*-
import os
import shutil
import re

def main():
    src_file = r"C:\SageMirror_Production\app_v13_25.py"
    backup_dir = r"C:\SageMirror_Production\00_History"
    backup_file = os.path.join(backup_dir, "app_v13_25_v13.25_20260521_0840.py")
    dest_file = r"C:\SageMirror_Production\app_v13_26.py"

    print("Step 1: Create backup folder and backup file...")
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy(src_file, backup_file)
    print(f"Backup created: {backup_file}")

    print("Step 2: Verify line count...")
    with open(src_file, "r", encoding="utf-8") as f:
        src_lines = f.readlines()
    with open(backup_file, "r", encoding="utf-8") as f:
        bak_lines = f.readlines()
    print(f"Source lines: {len(src_lines)}, Backup lines: {len(bak_lines)}")
    if len(src_lines) != len(bak_lines):
        print("Error: Line count mismatch!")
        return

    content = "".join(src_lines)

    # 3.14 호환성 고려하여 코드 수정 진행
    print("Step 3: App Version Update in header comment...")
    content = content.replace("Master App v13.16.1", "Master App v13.26")
    content = content.replace("[v13.16.1 업데이트 사항: 2026-05-19]", "[v13.26 업데이트 사항: 2026-05-21]\n- Part 1 Librarian 3단 분석 엔진 영속성 보존 및 전자동 RAG 백업 시스템 구현\n- 시작 즉시 상태 초기화, 로컬/옵시디언 자동 저장 인디케이터 나란히 배치")

    # Add helper function for automatic keyword extraction via gemma
    print("Step 4: Inject extract_keywords_via_gemma function...")
    helper_code = """
# ── RAG 키워드 자동 세분화 추출 헬퍼 ──
def extract_keywords_via_gemma(content, base_rules):
    prompt = f\"\"\"[SYSTEM]: 너는 입력된 텍스트에서 옵시디언 RAG 지식 구조화 연동을 위한 핵심 키워드 4~5개를 세분화하여 추출하는 전문 분석기다.
너의 임무는 입력 텍스트의 핵심 주제, 철학적 맥락, 성경적 모티브, 시청자 감정 결핍 상태 등을 관통하는 고유 키워드 4~5개를 쉼표(,)로 구분된 단어로만 출력하는 것이다.
반드시 단어 이외의 설명, 서론, 결론, 특수문자, 따옴표는 일절 출력하지 마라.
예시 출력: 외로움, 고독, 존재의미, 쇼펜하우어, 자아정체성

[USER_INPUT]:
{content}

[KEYWORDS]:\"\"\"
    try:
        res = call_gemma(prompt, base_rules)
        cleaned = res.replace("#", "").replace("[", "").replace("]", "").replace("`", "").strip()
        keywords = [k.strip() for k in cleaned.split(",") if k.strip()]
        return ", ".join(keywords[:5])
    except Exception as e:
        return "심리치유, 현자의거울, 자아성찰"
"""
    # Insert helper_code after the import block or near safe_makedirs definitions
    content = content.replace("from sage_popups import (\n    popup_edit_obsidian, popup_edit_prompt, popup_assistant,\n)", 
                              "from sage_popups import (\n    popup_edit_obsidian, popup_edit_prompt, popup_assistant,\n)\n" + helper_code)

    # Update init_session_state
    print("Step 5: Update session state initialization...")
    init_state_changes = """        "p1_bench_raw": "",
        "p1_bench_tags": "",
        "p1_research_tags": "",
        "p1_plan_tags": "",
        "p1_bench_saved": False,
        "p1_bench_obsidian_saved": False,
        "p1_research_saved": False,
        "p1_research_obsidian_saved": False,
        "p1_plan_saved": False,
        "p1_plan_obsidian_saved": False,"""
    content = content.replace('        "p1_bench_raw": "",\n        "p1_bench_tags": "",\n        "p1_research_tags": "",\n        "p1_plan_tags": "",', init_state_changes)

    # Update save_workspace_state keys_to_save
    print("Step 6: Update workspace state keys list...")
    keys_changes = """        "p1_bench_raw", "p1_bench_tags", "p1_research_tags", "p1_plan_tags",
        "p1_bench_saved", "p1_bench_obsidian_saved", "p1_research_saved", "p1_research_obsidian_saved", "p1_plan_saved", "p1_plan_obsidian_saved","""
    content = content.replace('        "p1_bench_raw", "p1_bench_tags", "p1_research_tags", "p1_plan_tags",', keys_changes)

    # Update render_part1() callbacks for persistent UI textareas
    print("Step 7: Define UI input callbacks inside render_part1 region...")
    callbacks_code = """
    # ── UI 입력값 세션 보존 콜백 ──
    def on_p1_bench_prompt_change():
        st.session_state.p1_bench_prompt = st.session_state.p1_bench_prompt_input

    def on_p1_bench_raw_change():
        st.session_state.p1_bench_raw = st.session_state.p1_bench_raw_ta
        # 수정 발생 시 자동 주제 재파싱 처리
        st.session_state.p1_topics = _parse_topics(st.session_state.p1_bench_raw)
        st.session_state.pipeline_state["topic_candidates"] = st.session_state.p1_topics
        save_workspace_state()

    def on_p1_bench_tags_change():
        st.session_state.p1_bench_tags = st.session_state.p1_bench_tags_input

    def on_p1_research_prompt_change():
        st.session_state.p1_research_prompt = st.session_state.p1_research_prompt_input

    def on_p1_research_result_change():
        st.session_state.p1_research_result = st.session_state.p1_research_result_ta
        st.session_state.pipeline_state["research_result"] = st.session_state.p1_research_result
        save_workspace_state()

    def on_p1_research_tags_change():
        st.session_state.p1_research_tags = st.session_state.p1_research_tags_input

    def on_p1_plan_prompt_change():
        st.session_state.p1_plan_prompt = st.session_state.p1_plan_prompt_input

    def on_p1_planning_result_change():
        st.session_state.p1_planning_result = st.session_state.p1_planning_result_ta
        st.session_state.pipeline_state["planning_result"] = st.session_state.p1_planning_result
        save_workspace_state()

    def on_p1_plan_tags_change():
        st.session_state.p1_plan_tags = st.session_state.p1_plan_tags_input
"""
    # Let's find where render_part1 starts and insert callbacks_code right after 'is_locked = ...'
    # "is_locked = not st.session_state.get("unlock_part1", False)" is typically near the beginning of render_part1()
    content = content.replace("is_locked = not st.session_state.get(\"unlock_part1\", False)", 
                              "is_locked = not st.session_state.get(\"unlock_part1\", False)\n" + callbacks_code)

    # Now replace the Tab 1 (tab_bench) content in render_part1()
    print("Step 8: Rewrite tab_bench UI and pipeline...")
    tab_bench_old = """    with tab_bench:
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
            
            if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked, key="p1_bench_start_btn"):
                if not st.session_state.p1_channel_url: 
                    st.error("[WARN] 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")
                else:
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
                          save_workspace_state()
            
            if st.session_state.p1_bench_raw:
                st.markdown("##### 📝 벤치마킹 분석 결과 원본 (수정 가능)")
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
                st.markdown("##### 💾 벤치마킹 결과 저장 및 옵시디언 백업")
                st.session_state.p1_bench_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_bench_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_bench_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 벤치마킹 결과 옵시디언 자동 백업", use_container_width=True, type="primary", key="p1_bench_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_bench_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    folder_name = "TopicMemory"
                    title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"
                    
                    val = f"## 📌 핵심 요약\\n- 채널: {st.session_state.p1_channel_url}\\n- 타겟 지역: {st.session_state.p1_region}\\n\\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\\n\\n"
                    val += f"## 📖 벤치마킹 상세 추천 리스트\\n"
                    for t in st.session_state.p1_topics:
                        val += f"### [[{t['title']}]]\\n- **추천 사유(체험담 기반):** {t['reason']}\\n- **예상 효과:** {t['effect']}\\n- **예상 반응:** {t['audience_reaction']}\\n\\n"
                    val += f"\\n## 🔗 원본 날것의 텍스트\\n```text\\n{st.session_state.p1_bench_raw}\\n```\\n"
                    
                    obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 벤치마킹 옵시디언 백업 완료!", icon="💾")
                        save_workspace_state()
                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                            st.success(f"✅ 옵시디언 및 GitHub 자동 저장 완료! (경로: {obs_path})")
                        else:
                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")"""

    tab_bench_new = """    with tab_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 벤치마킹 분석")
            st.caption("주제 20개 추천 (추천사유, 효과, 반응)")
            
            st.text_area(
                "🤖 젬마 작업지시 프롬프트 (벤치마킹)", 
                value=st.session_state.p1_bench_prompt, 
                height=100, 
                key="p1_bench_prompt_input",
                on_change=on_p1_bench_prompt_change,
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
                            
                            val = f"## 📌 핵심 요약\\n- 채널: {st.session_state.p1_channel_url}\\n- 타겟 지역: {st.session_state.p1_region}\\n\\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\\n\\n"
                            val += f"## 📖 벤치마킹 상세 추천 리스트\\n"
                            for t in parsed_topics:
                                val += f"### [[{t['title']}]]\\n- **추천 사유(체험담 기반):** {t['reason']}\\n- **예상 효과:** {t['effect']}\\n- **예상 반응:** {t['audience_reaction']}\\n\\n"
                            val += f"\\n## 🔗 원본 날것의 텍스트\\n```text\\n{raw_res}\\n```\\n"
                            
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
                st.text_area(
                    "벤치마킹 원본 텍스트", 
                    value=st.session_state.p1_bench_raw, 
                    height=300, 
                    key="p1_bench_raw_ta", 
                    on_change=on_p1_bench_raw_change,
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
                st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_bench_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_bench_tags_input",
                    on_change=on_p1_bench_tags_change,
                    disabled=is_locked
                )
                
                # 수동 예비 백업 버튼도 제공하되 세련되게 연출
                if st.button("💾 (예비용) 벤치마킹 수동 옵시디언 백업 실행", use_container_width=True, key="p1_bench_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_bench_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    folder_name = "TopicMemory"
                    title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"
                    
                    val = f"## 📌 핵심 요약\\n- 채널: {st.session_state.p1_channel_url}\\n- 타겟 지역: {st.session_state.p1_region}\\n\\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\\n\\n"
                    val += f"## 📖 벤치마킹 상세 추천 리스트\\n"
                    for t in st.session_state.p1_topics:
                        val += f"### [[{t['title']}]]\\n- **추천 사유(체험담 기반):** {t['reason']}\\n- **예상 효과:** {t['effect']}\\n- **예상 반응:** {t['audience_reaction']}\\n\\n"
                    val += f"\\n## 🔗 원본 날것의 텍스트\\n```text\\n{st.session_state.p1_bench_raw}\\n```\\n"
                    
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
                        st.rerun()"""

    content = content.replace(tab_bench_old, tab_bench_new)

    # Now replace the Tab 2 (tab_research) content in render_part1()
    print("Step 9: Rewrite tab_research UI and pipeline...")
    tab_research_old = """    with tab_research:
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
            
            if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p1_research_start_btn"):
                if not st.session_state.p1_topic_selection:
                    st.error("[WARN] 먼저 좌측의 '벤치마킹 시작' 버튼을 눌러 분석을 완료하고 주제를 선택해 주세요.")
                else:
                    with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):
                        topic_str = st.session_state.p1_topic_selection
                        st.session_state.p1_research_result = generate_research_draft_p1(
                             st.session_state.p1_channel_url, 
                             topic_str,
                             st.session_state.p1_gemma_protocol, 
                             st.session_state.base_prompt_rules,
                             st.session_state.p1_research_prompt
                         )
                    st.session_state.pipeline_state["research_result"] = st.session_state.p1_research_result
                    save_workspace_state()
            
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
                st.markdown("##### 💾 자료조사 결과 저장 및 옵시디언 백업")
                st.session_state.p1_research_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_research_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_research_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 자료조사 결과 옵시디언 자동 백업", use_container_width=True, type="primary", key="p1_research_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_research_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    folder_name = "ResearchMemory"
                    
                    topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                    title = f"자료조사 초안 - {topic_title}"
                    
                    val = f"## 📌 핵심 요약\\n- 선택 주제: {st.session_state.p1_topic_selection}\\n\\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\\n\\n"
                    val += f"## 📖 자료조사 및 초안 본문\\n{st.session_state.p1_research_result}\\n\\n"
                    
                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 자료조사 옵시디언 백업 완료!", icon="💾")
                        save_workspace_state()
                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                            st.success(f"✅ 옵시디언 및 GitHub 자동 저장 완료! (경로: {obs_path})")
                        else:
                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")"""

    tab_research_new = """    with tab_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 자료 조사 결과")
            st.caption("옵시디언/리서치 융합 기초 초안 작성 (출처 명기)")
            
            st.text_area(
                "🤖 젬마 작업지시 프롬프트 (자료 조사)", 
                value=st.session_state.p1_research_prompt, 
                height=100, 
                key="p1_research_prompt_input",
                on_change=on_p1_research_prompt_change,
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
                            
                            val = f"## 📌 핵심 요약\\n- 선택 주제: {st.session_state.p1_topic_selection}\\n\\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\\n\\n"
                            val += f"## 📖 자료조사 및 초안 본문\\n{res}\\n\\n"
                            
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
                st.text_area(
                    "자료 조사 결과 (수정 가능)", 
                    value=st.session_state.p1_research_result, 
                    height=350, 
                    key="p1_research_result_ta",
                    on_change=on_p1_research_result_change,
                    disabled=is_locked
                )
                
                if st.button("[SEARCH] 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_res_p1"):
                    popup_edit_research()
 
                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_research_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_research_tags_input",
                    on_change=on_p1_research_tags_change,
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
                    
                    val = f"## 📌 핵심 요약\\n- 선택 주제: {st.session_state.p1_topic_selection}\\n\\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\\n\\n"
                    val += f"## 📖 자료조사 및 초안 본문\\n{st.session_state.p1_research_result}\\n\\n"
                    
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
                        st.rerun()"""

    content = content.replace(tab_research_old, tab_research_new)

    # Now replace the Tab 3 (tab_plan) content in render_part1()
    print("Step 10: Rewrite tab_plan UI and pipeline...")
    tab_plan_old = """    with tab_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안")
            st.caption("15분 영상 뼈대 총괄 시나리오 기획 (마스터 플랜)")
            
            st.session_state.p1_plan_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (총괄 기획)", 
                value=st.session_state.p1_plan_prompt, 
                height=100, 
                key="p1_plan_prompt_input",
                disabled=is_locked
            )
        
            if st.button("[ALCHEMY] 철학·감정 융합 설계", use_container_width=True, disabled=is_locked, key="p1_plan_start_btn"):
                if not st.session_state.p1_research_result:
                    st.error("[WARN] 먼저 중앙의 '자료조사 및 초안 작성'을 완료해 주세요.")
                else:
                    with st.spinner("철학·성경·감정 융합 구조 설계 중..."):
                        st.session_state.p1_planning_result = generate_final_planning_p1(
                             st.session_state.p1_research_result,
                             st.session_state.p1_gemma_protocol, 
                             st.session_state.base_prompt_rules,
                             st.session_state.p1_plan_prompt
                        )
                    st.session_state.pipeline_state["planning_result"] = st.session_state.p1_planning_result
                    save_workspace_state()

            if st.session_state.p1_planning_result:
               st.markdown("<br>", unsafe_allow_html=True)
               st.session_state.p1_planning_result = st.text_area(
                   "최종 기획안 (수정 가능)", 
                   value=st.session_state.p1_planning_result, 
                   height=350, 
                   key="p1_planning_result_ta",
                   disabled=is_locked
               )
               
               c_view, c_copy = st.columns(2)
               with c_view:
                   if st.button("👁 팝업에서 크게 보기", use_container_width=True, key="p1_plan_view_btn"):
                       popup_edit_planning()
               with c_copy:
                   if st.button("📋 클립보드 복사", use_container_width=True, key="p1_plan_copy_btn"):
                       pyperclip.copy(st.session_state.p1_planning_result)
                       st.success("총괄 기획안 복사 완료")

               st.divider()
               st.markdown("##### 💾 기획안 결과 저장 및 옵시디언 백업")
               st.session_state.p1_plan_tags = st.text_input(
                   "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                   value=st.session_state.p1_plan_tags, 
                   placeholder="예: 외로움, 존재의미, 고통, 용서", 
                   key="p1_plan_tags_input",
                   disabled=is_locked
               )
               
               if st.button("💾 최종 기획안 옵시디언 자동 백업", use_container_width=True, type="primary", key="p1_plan_save_backup_btn", disabled=is_locked):
                   tag_list = [t.strip() for t in st.session_state.p1_plan_tags.split(",") if t.strip()]
                   tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                   tag_hashes = " ".join([f"#{t}" for t in tag_list])
                   
                   ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                   today_str = datetime.now().strftime("%Y-%m-%d")
                   folder_name = "PlanningMemory"
                   
                   topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"
                   title = f"최종 기획안 - {topic_title}"
                   
                   val = f"## 📌 핵심 요약\\n- 선택 주제: {st.session_state.p1_topic_selection}\\n\\n"
                   val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\\n\\n"
                   val += f"## 📖 최종 시나리오 기획안 본문\\n{st.session_state.p1_planning_result}\\n\\n"
                   
                   obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")
                   if obs_path:
                       lock_file_readonly(obs_path)
                       st.toast("✅ 기획안 옵시디언 백업 완료!", icon="💾")
                       save_workspace_state()
                       success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                       if success:
                           st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                           st.success(f"✅ 옵시디언 및 GitHub 자동 저장 완료! (경로: {obs_path})")
                       else:
                           st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")"""

    tab_plan_new = """    with tab_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안")
            st.caption("15분 영상 뼈대 총괄 시나리오 기획 (마스터 플랜)")
            
            st.text_area(
                "🤖 젬마 작업지시 프롬프트 (총괄 기획)", 
                value=st.session_state.p1_plan_prompt, 
                height=100, 
                key="p1_plan_prompt_input",
                on_change=on_p1_plan_prompt_change,
                disabled=is_locked
            )
        
            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---
            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])
            with c_btn1:
                if st.button("[ALCHEMY] 철학·감정 융합 설계", use_container_width=True, disabled=is_locked, key="p1_plan_start_btn"):
                    if not st.session_state.p1_research_result:
                        st.error("[WARN] 먼저 중앙의 '자료조사 및 초안 작성'을 완료해 주세요.")
                    else:
                        # 시작 즉시 리셋
                        st.session_state.p1_planning_result = ""
                        st.session_state.p1_plan_tags = ""
                        st.session_state.p1_plan_saved = False
                        st.session_state.p1_plan_obsidian_saved = False
                        save_workspace_state()
                        
                        with st.spinner("철학·성경·감정 융합 구조 설계 중..."):
                            res = generate_final_planning_p1(
                                 st.session_state.p1_research_result,
                                 st.session_state.p1_gemma_protocol, 
                                 st.session_state.base_prompt_rules,
                                 st.session_state.p1_plan_prompt
                            )
                            st.session_state.p1_planning_result = res
                            st.session_state.pipeline_state["planning_result"] = res
                            st.session_state.p1_plan_saved = True
                            save_workspace_state()
                            
                            # 젬마 키워드 자동 세분화
                            keywords = extract_keywords_via_gemma(res, st.session_state.base_prompt_rules)
                            st.session_state.p1_plan_tags = keywords
                            
                            # 자동 옵시디언 RAG 저장 진행
                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                            
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            folder_name = "PlanningMemory"
                            topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"
                            title = f"최종 기획안 - {topic_title}"
                            
                            val = f"## 📌 핵심 요약\\n- 선택 주제: {st.session_state.p1_topic_selection}\\n\\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\\n\\n"
                            val += f"## 📖 최종 시나리오 기획안 본문\\n{res}\\n\\n"
                            
                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")
                            if obs_path:
                                lock_file_readonly(obs_path)
                                st.toast("💾 기획안 결과 로컬 자동 저장 완료!", icon="💾")
                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                if success:
                                    st.session_state.p1_plan_obsidian_saved = True
                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                else:
                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                save_workspace_state()
                                st.rerun()
            
            with c_btn2:
                if st.session_state.get("p1_plan_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_plan_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_plan_local_waiting")
            
            with c_btn3:
                if st.session_state.get("p1_plan_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_plan_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_plan_obs_waiting")

            if st.session_state.p1_planning_result:
               st.markdown("<br>", unsafe_allow_html=True)
               st.text_area(
                   "최종 기획안 (수정 가능)", 
                   value=st.session_state.p1_planning_result, 
                   height=350, 
                   key="p1_planning_result_ta",
                   on_change=on_p1_planning_result_change,
                   disabled=is_locked
               )
               
               c_view, c_copy = st.columns(2)
               with c_view:
                   if st.button("👁 팝업에서 크게 보기", use_container_width=True, key="p1_plan_view_btn"):
                       popup_edit_planning()
               with c_copy:
                   if st.button("📋 클립보드 복사", use_container_width=True, key="p1_plan_copy_btn"):
                       pyperclip.copy(st.session_state.p1_planning_result)
                       st.success("총괄 기획안 복사 완료")

               st.divider()
               st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
               st.text_input(
                   "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                   value=st.session_state.p1_plan_tags, 
                   placeholder="예: 외로움, 존재의미, 고통, 용서", 
                   key="p1_plan_tags_input",
                   on_change=on_p1_plan_tags_change,
                   disabled=is_locked
               )
               
               if st.button("💾 (예비용) 최종 기획안 수동 옵시디언 백업 실행", use_container_width=True, key="p1_plan_save_backup_btn", disabled=is_locked):
                   tag_list = [t.strip() for t in st.session_state.p1_plan_tags.split(",") if t.strip()]
                   tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                   tag_hashes = " ".join([f"#{t}" for t in tag_list])
                   
                   ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                   folder_name = "PlanningMemory"
                   
                   topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"
                   title = f"최종 기획안 - {topic_title}"
                   
                   val = f"## 📌 핵심 요약\\n- 선택 주제: {st.session_state.p1_topic_selection}\\n\\n"
                   val += f"## 🎯 핵심 감정 / RAG 태그\\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\\n\\n"
                   val += f"## 📖 최종 시나리오 기획안 본문\\n{st.session_state.p1_planning_result}\\n\\n"
                   
                   obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")
                   if obs_path:
                       lock_file_readonly(obs_path)
                       st.toast("✅ 수동 기획안 옵시디언 백업 완료!", icon="💾")
                       st.session_state.p1_plan_obsidian_saved = True
                       save_workspace_state()
                       success, msg = auto_git_push(f"Manual Save (Locked): {title}")
                       if success:
                           st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                       else:
                           st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                       st.rerun()"""

    content = content.replace(tab_plan_old, tab_plan_new)

    # Let's adjust routing logic and other version references to app_v13_26.py
    # Especially st.info("👉 render_part8_dashboard() 함수가 이곳에 연결됩니다...")
    # There might be references to app_v13_25.py inside RUN_APP.bat as well, which we will update later.
    
    print("Step 11: Write final code to app_v13_26.py...")
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("app_v13_26.py successfully written!")

if __name__ == "__main__":
    main()
