import re

with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Instead of parsing lines, let's use regex to find and replace the exact blocks.
# The block starts with `c_title, c_control = st.columns([4.2, 5.8])`
# Then we have `with c_title:` and `with c_control:`
# We want to remove `c_title, c_control...` and `with c_control: ...` 
# But keep `with c_title:`

# We can replace `c_title, c_control = st.columns([4.2, 5.8])` -> `c_title = st.container()`
content = content.replace('c_title, c_control = st.columns([4.2, 5.8])', 'c_title = st.container()')

# Now we need to remove `with c_control:` block. 
# We'll split the file by lines and use a state machine that properly ignores blank lines.

lines = content.split('\n')
new_lines = []
skip = False
target_indent = -1

for line in lines:
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    if skip:
        if stripped == '':
            continue  # ignore blank lines
        if indent <= target_indent:
            skip = False  # End of block reached
        else:
            continue
            
    if 'with c_control:' in line:
        skip = True
        target_indent = len(line) - len(line.lstrip())
        continue
        
    if 'if not st.session_state.get("unlock_part' in line:
        line = line.replace('if not st.session_state', 'if False and not st.session_state')
        
    new_lines.append(line)

content = '\n'.join(new_lines)

# Now fix Right Gemma UI
gemma_panel_start = content.find('def render_right_gemma_panel():')
gemma_panel_end = content.find('# 파트 라우팅 블록')

new_gemma_panel = """def render_right_gemma_panel():
    st.markdown("<h4>🔍 리서치</h4>", unsafe_allow_html=True)
    
    st.markdown(\"\"\"
    <div id="right-gemma-sticky-marker"></div>
    <style>
    /* 우측 패널 고정을 위한 부모 컨테이너 설정 */
    div[data-testid="stHorizontalBlock"]:has(#right-gemma-sticky-marker) {
        align-items: flex-start !important;
    }
    div[data-testid="column"]:has(#right-gemma-sticky-marker) {
        position: sticky !important;
        top: 2rem !important;
        align-self: flex-start !important;
        height: calc(100vh - 4rem) !important;
        overflow-y: auto !important;
        padding-right: 5px;
        z-index: 999;
    }
    
    /* 둥근 통합 박스 스타일 */
    div[data-testid="stVerticalBlock"]:has(> div > div > div > #chatbar-marker) {
        background-color: #252525 !important;
        border: 1px solid #333 !important;
        border-radius: 22px !important;
        padding: 5px 15px !important;
        margin-top: 10px !important;
        gap: 0 !important;
    }
    
    /* 입력창 내부 투명화 */
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) div[data-testid="stTextInput"] input {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        padding: 10px 5px !important;
        font-size: 1rem !important;
        color: #fff !important;
    }
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) div[data-testid="stTextInput"] > div > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 모델 선택기 투명화 */
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) div[data-baseweb="select"] > div {
        border: none !important;
        background-color: transparent !important;
        color: #aaa !important;
        box-shadow: none !important;
        cursor: pointer;
    }
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) div[data-baseweb="select"] {
        margin-top: 5px;
    }
    
    /* ＋ 버튼 투명화 */
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) button[data-testid="baseButton-secondary"]:has(div:contains("＋")) {
        border: none !important;
        background-color: transparent !important;
        color: #aaa !important;
        font-size: 1.2rem !important;
        padding: 0 !important;
        box-shadow: none !important;
        margin-top: 5px;
    }
    
    /* ↑ 버튼 스타일 */
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) button[kind="primary"] {
        border-radius: 50% !important;
        background-color: #444 !important;
        color: white !important;
        border: none !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        margin-top: 2px;
        transition: 0.2s;
    }
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) button[kind="primary"]:hover {
        background-color: #e50914 !important;
    }
    
    /* gap 줄이기 */
    div[data-testid="stVerticalBlock"]:has(#chatbar-marker) > div {
        gap: 0 !important;
    }
    </style>
    \"\"\", unsafe_allow_html=True)

    if "right_popup_history" not in st.session_state:
        st.session_state.right_popup_history = _load_chat_history()

    # 1. 채팅 히스토리 컨테이너
    chat_container = st.container(height=480, border=True)
    with chat_container:
        if not st.session_state.right_popup_history:
            st.markdown("<div style='color:#888;padding:10px;text-align:center;'>💭 대화 내역이 없습니다.</div>", unsafe_allow_html=True)
        else:
            for msg in st.session_state.right_popup_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # 2. 하단 통합 박스
    chatbar_container = st.container(border=False)
    with chatbar_container:
        st.markdown('<div id="chatbar-marker"></div>', unsafe_allow_html=True)
        
        # 첫 줄: 입력창
        user_input = st.text_input("메시지 입력", placeholder="메시지를 입력하세요...", key="right_gemma_input_widget", label_visibility="collapsed")
        
        # 둘째 줄: ＋, 빈공간, 모델, ↑
        c_plus, c_space, c_model, c_send = st.columns([1, 4.5, 3.5, 1], gap="small")
        
        send_clicked = False
        
        with c_plus:
            with st.popover("＋", use_container_width=True):
                st.markdown("**기능 메뉴**")
                if st.button("📁 파일 탐색기", use_container_width=True):
                    st.info("다음 단계에서 연동 예정입니다.")
                if st.button("☁️ Google Drive / Docs", use_container_width=True):
                    st.info("다음 단계에서 연동 예정입니다.")
                st.markdown("---")
                st.markdown("🔎 **외부 리서치**")
                if st.button("📺 유튜브 채널 찾기", use_container_width=True):
                    st.info("다음 단계 연동 예정.")
                if st.button("🎬 성공 영상 찾기", use_container_width=True):
                    st.info("다음 단계 연동 예정.")
                st.markdown("---")
                if st.button("🧩 현재 Part로 Push", use_container_width=True):
                    last_assistant_msg = None
                    for msg in reversed(st.session_state.right_popup_history):
                        if msg.get("role") == "assistant" and msg.get("source") != "사용자 입력":
                            last_assistant_msg = msg
                            break
                    if last_assistant_msg:
                        st.session_state["right_gemma_push_packet"] = {
                            "source": "right_gemma",
                            "target_part": st.session_state.get("sidebar_part", "파트 1").split(":")[0].strip(),
                            "type": "external_research",
                            "engine": st.session_state.get("right_gemma_model_select", ""),
                            "query": "마지막 응답 Push",
                            "result": last_assistant_msg.get("content", ""),
                            "status": "waiting_user_review"
                        }
                        st.success("자료 전달 대기 완료.")
                    else:
                        st.warning("Push할 응답이 없습니다.")
                if st.button("📋 응답 복사", use_container_width=True):
                    last_assistant_msg = None
                    for msg in reversed(st.session_state.right_popup_history):
                        if msg.get("role") == "assistant" and msg.get("source") != "사용자 입력":
                            last_assistant_msg = msg
                            break
                    if last_assistant_msg:
                        st.code(last_assistant_msg.get("content", ""))
                st.markdown("---")
                if st.button("🧹 대화 초기화", use_container_width=True):
                    st.session_state.right_popup_history = []
                    _save_chat_history([])
                    st.rerun()
                    
        with c_space:
            st.write("") # 빈 공간
            
        with c_model:
            models_display = ["G2", "G4", "GM", "G3", "TV"]
            models_internal = ["gemma4:e2b", "gemma4:e4b", "gemini-2.5-flash", "gemini-3-flash", "Tavily 웹 검색"]
            selected_mode_display = st.selectbox("엔진", models_display, key="right_gemma_model_select", label_visibility="collapsed")
            selected_mode = models_internal[models_display.index(selected_mode_display)]
            
        with c_send:
            send_clicked = st.button("↑", key="right_gemma_send_button", use_container_width=True, type="primary")

    # 3. 전송 로직 (RAG/Obsidian 없음)
    if send_clicked and user_input.strip():
        new_model_id = selected_mode
        if selected_mode == "Tavily 웹 검색":
            new_model_id = "tavily"
            
        st.session_state.right_popup_history.append({
            "role": "user",
            "content": user_input,
            "model": new_model_id,
            "part": "Right Gemma",
            "source": "사용자 입력"
        })
        
        with chat_container.chat_message("user"):
            st.markdown(user_input)

        with chat_container.chat_message("assistant"):
            sys_prompt = "너는 현자의 거울 스튜디오의 수석 어시스턴트다. 묻는 말에 사실에 기초하여 신중히 답하라. 등장인물은 오직 @Protagonist 로 지칭하라."
            
            if new_model_id == "tavily":
                st.error("Tavily 웹 검색은 다음 단계에서 연동됩니다.")
                response = "연동 대기 중"
                source_label = "Tavily 대기"
            elif "gemini" in new_model_id:
                with st.spinner("Gemini 리서치 중..."):
                    stream_gen = stream_gemini(user_input, system_prompt=sys_prompt, model_name=new_model_id)
                    response = st.write_stream(stream_gen)
                    source_label = "Gemini API"
            else:
                with st.spinner("Gemma 분석 중..."):
                    stream_gen = _stream_gemma_a_mode_p0(user_input, system=sys_prompt, model=new_model_id)
                    response = st.write_stream(stream_gen)
                    source_label = f"로컬 {new_model_id.upper()} 스트리밍"
            
        st.session_state.right_popup_history.append({
            "role": "assistant",
            "content": response,
            "model": new_model_id,
            "part": "Right Gemma",
            "source": source_label
        })
        _save_chat_history(st.session_state.right_popup_history)
        st.rerun()

"""

content = content[:gemma_panel_start] + new_gemma_panel + '\n' + content[gemma_panel_end:]

with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("UI updated successfully.")
