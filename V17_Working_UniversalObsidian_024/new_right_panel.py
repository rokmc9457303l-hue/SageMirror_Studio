def render_right_gemma_panel():
    # [DOM 진단 확인] CSS 셀렉터: data-testid="stColumn" (≠ "column")
    # stMain(overflow:auto)이 스크롤 컨테이너 → stColumn에 sticky 적용
    st.html('''
    <div id="right-research-marker"></div>
    <style>
    div[data-testid="stColumn"]:has(#right-research-marker) {
        position: sticky !important;
        top: 8px !important;
        align-self: flex-start !important;
        max-height: calc(100vh - 16px) !important;
        overflow: hidden !important;
        z-index: 10;
    }
    </style>
    ''')

    if "right_research_history" not in st.session_state:
        st.session_state.right_research_history = []

    chat_container = st.container(height=520, border=True)
    with chat_container:
        if not st.session_state.right_research_history:
            pass
        else:
            for msg in st.session_state.right_research_history:
                with st.chat_message(msg["role"]):
                    if msg.get("status") == "error":
                        st.error(msg["content"])
                    else:
                        st.markdown(msg["content"])
                    if msg.get("sources"):
                        with st.expander("출처 확인"):
                            for s in msg["sources"]:
                                st.write(f"- [{s.get('title')}]({s.get('url')})")


    # === 입력창 초기화 로직 ===
    if "right_gemma_clear_flag" in st.session_state and st.session_state.right_gemma_clear_flag:
        st.session_state.right_gemma_input_widget = ""
        st.session_state.right_gemma_clear_flag = False

    user_input = st.text_area(
        "메시지",
        placeholder="메시지 입력하세요...",
        height=125,
        key="right_gemma_input_widget",
        label_visibility="collapsed"
    )

    ctrl_plus, ctrl_model, ctrl_send = st.columns([1.2, 2.4, 0.9])
    send_clicked = False

    with ctrl_plus:
        with st.popover("＋ 기능", use_container_width=True):
            if st.button("📁 로컬 자료 가져오기", use_container_width=True):
                st.info("로컬 자료 가져오기는 다음 단계에서 파일 탐색기와 연결합니다.")
            if st.button("☁️ Google Drive · Docs 연결", use_container_width=True):
                st.info("Google Drive · Docs 연결은 다음 단계에서 설정창 Provider와 연결합니다.")
            if st.button("📓 NotebookLM 자료 폴더 연결", use_container_width=True):
                st.info("NotebookLM 자료 폴더 연결은 다음 단계에서 Drive 폴더 경로와 연결합니다.")
            if st.button("🧹 우측 대화 초기화", use_container_width=True):
                st.session_state.right_research_history = []
                st.rerun()

    with ctrl_model:
        # [v17_007] 우측 전용 키 — global_model 간섭 차단
        ENGINE_IDS = ["gemma4:e2b", "gemma4:e4b", "gemini-2.5-flash", "gemini-3-flash", "Tavily 웹 검색"]
        ENGINE_LABELS = {
            "gemma4:e2b":       "Gemma E2B · 로컬",
            "gemma4:e4b":       "Gemma E4B · 로컬",
            "gemini-2.5-flash": "Gemini Flash · 리서치",
            "gemini-3-flash":   "Gemini Pro · 리서치",
            "Tavily 웹 검색":   "Tavily · 웹 검색",
        }
        
        selected_model_label = st.selectbox(
            "엔진 선택",
            options=[ENGINE_LABELS[k] for k in ENGINE_IDS],
            index=0,
            key="right_gemma_engine_selectbox",
            label_visibility="collapsed"
        )
        
        selected_engine = ENGINE_IDS[0]
        for k, v in ENGINE_LABELS.items():
            if v == selected_model_label:
                selected_engine = k
                break

    with ctrl_send:
        if st.button("🚀 전송", type="primary", use_container_width=True):
            if not user_input.strip():
                st.warning("메시지를 입력하세요.")
            else:
                send_clicked = True
                
    if send_clicked:
        st.session_state.right_research_history.append({"role": "user", "content": user_input})
        st.session_state.right_gemma_clear_flag = True
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
                
            with st.chat_message("assistant"):
                with st.spinner(f"({selected_model_label}) 처리 중..."):
                    import datetime
                    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    req_packet = {
                        "request_id": f"REQ-{now_str}",
                        "source_part": "RIGHT_ASSISTANT",
                        "target_panel": "RIGHT_ASSISTANT",
                        "query": user_input,
                        "required_outputs": ["summary", "source_notes", "keywords", "obsidian_save"],
                        "status": "QUEUED",
                        "retry_count": 0,
                        "created_at": now_str,
                        "last_error": "",
                        "obsidian_paths": {"raw": "", "wiki": "", "schema": ""}
                    }
                    st.session_state.right_research_inbox = st.session_state.get("right_research_inbox", [])
                    st.session_state.right_research_inbox.append(req_packet)
                    st.session_state.right_research_last_request_id = req_packet["request_id"]
                    
                    st.session_state.right_gemma_input_widget = ""
                    st.rerun()
