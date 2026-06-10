# -*- coding: utf-8 -*-
"""
ui/right_assistant.py
V17 Reborn - 우측 젬마 보조 참모 대화창 (Streamlit Native Widget 버전)
"""

import streamlit as st

ASSISTANT_MODELS = [
    "gemma4:e2b",
    "gemma4:e4b",
    "Gemini",
    "앱 리서치",
]

def ensure_right_assistant_state_v3() -> None:
    """우측 대화창 세션 기본값 (v3)."""
    if "right_assistant_messages_v3" not in st.session_state:
        st.session_state["right_assistant_messages_v3"] = [
            {
                "role": "system",
                "content": (
                    "🤖 젬마 보조 참모 대기 중입니다.\n"
                    "중앙 결과물을 직접 덮어쓰지 않고, 검수·보강·저장·재참조·최종 보고를 담당합니다."
                ),
            }
        ]

    if "right_assistant_model_v3" not in st.session_state:
        st.session_state["right_assistant_model_v3"] = "gemma4:e2b"

    if "right_assistant_input_v3" not in st.session_state:
        st.session_state["right_assistant_input_v3"] = ""

def add_message_v3(role: str, content: str) -> None:
    ensure_right_assistant_state_v3()
    st.session_state["right_assistant_messages_v3"].append({"role": role, "content": content})

def handle_quick_action(action_name: str) -> None:
    add_message_v3("user", f"[{action_name}] 실행 요청")
    add_message_v3("assistant", f"'{action_name}' 명령을 접수했습니다. (기능 연결 대기중)")

def render_right_assistant(current_part: str = "Part 1", episode_id: str = "EP001") -> None:
    """우측 젬마 보조 참모 대화창 렌더링 (Native Widgets)."""
    ensure_right_assistant_state_v3()
    
    st.markdown(
        """
        <style>
        .assistant-sticky-panel {
            position: sticky;
            top: 2rem;
            z-index: 1000;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="assistant-sticky-panel">', unsafe_allow_html=True)
    
    st.markdown("### 🤖 젬마 보조 참모")
    
    global_model = st.session_state.get("global_model", "gemma4:e2b")
    selected_model = st.session_state["right_assistant_model_v3"]
    
    st.caption(f"파트: **{current_part}** | 에피소드: **{episode_id}**")
    st.caption(f"중앙 모델: `{global_model}` | 우측 모델: `{selected_model}`")
    
    st.markdown("---")
    
    # 빠른 기능 버튼 (그리드 배치)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 자동 검수", use_container_width=True, key="btn_check"):
            handle_quick_action("자동 검수")
        if st.button("🧠 옵시디언 저장", use_container_width=True, key="btn_obsidian"):
            handle_quick_action("옵시디언 저장")
        if st.button("✅ 최종 재검수", use_container_width=True, key="btn_final"):
            handle_quick_action("최종 재검수")
    with col2:
        if st.button("🌐 보강 리서치", use_container_width=True, key="btn_research"):
            handle_quick_action("보강 리서치")
        if st.button("🔁 젬마 재참조", use_container_width=True, key="btn_retry"):
            handle_quick_action("젬마 재참조")
        if st.button("📋 사용자 보고", use_container_width=True, key="btn_report"):
            handle_quick_action("사용자 보고")
            
    # * 기능 메뉴
    if hasattr(st, 'popover'):
        with st.popover("⚙️ 부가 기능 메뉴", use_container_width=True):
            st.button("📁 파일 가져오기", key="pop_file", on_click=lambda: handle_quick_action("파일 가져오기"))
            st.button("📂 폴더 가져오기", key="pop_folder", on_click=lambda: handle_quick_action("폴더 가져오기"))
            st.button("🔍 현재 결과 검수", key="pop_curr_chk", on_click=lambda: handle_quick_action("현재 결과 검수"))
            st.button("🌐 앱 리서치 실행", key="pop_app_res", on_click=lambda: handle_quick_action("앱 리서치 실행"))
    else:
        with st.expander("⚙️ 부가 기능 메뉴"):
            st.button("📁 파일 가져오기", key="exp_file", on_click=lambda: handle_quick_action("파일 가져오기"), use_container_width=True)
            st.button("📂 폴더 가져오기", key="exp_folder", on_click=lambda: handle_quick_action("폴더 가져오기"), use_container_width=True)
            st.button("🔍 현재 결과 검수", key="exp_curr_chk", on_click=lambda: handle_quick_action("현재 결과 검수"), use_container_width=True)
            st.button("🌐 앱 리서치 실행", key="exp_app_res", on_click=lambda: handle_quick_action("앱 리서치 실행"), use_container_width=True)

    st.markdown("---")
    
    # 메시지 영역 (스크롤 컨테이너)
    msg_container = st.container(height=400)
    with msg_container:
        for msg in st.session_state["right_assistant_messages_v3"]:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            if role == "system":
                st.info(content)
            elif role == "user":
                with st.chat_message("user"):
                    st.write(content)
            else:
                with st.chat_message("assistant"):
                    st.write(content)
                    
    st.markdown("---")
    
    # 모델 선택 및 입력창
    st.session_state["right_assistant_model_v3"] = st.selectbox(
        "참모 모델 선택", 
        options=ASSISTANT_MODELS, 
        index=ASSISTANT_MODELS.index(selected_model) if selected_model in ASSISTANT_MODELS else 0,
        label_visibility="collapsed"
    )
    
    def on_chat_submit():
        user_input = st.session_state.get("chat_input_v3", "").strip()
        if user_input:
            add_message_v3("user", user_input)
            add_message_v3("assistant", f"입력하신 '{user_input[:10]}...' 접수 완료.")
            st.session_state["chat_input_v3"] = ""
            
    st.text_input(
        "Ask anything / 명령 입력",
        key="chat_input_v3",
        on_change=on_chat_submit,
        placeholder="명령을 입력하고 Enter를 누르세요..."
    )
    
    st.markdown('</div>', unsafe_allow_html=True)