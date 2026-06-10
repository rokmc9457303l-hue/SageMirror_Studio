# -*- coding: utf-8 -*-
"""
ui/right_assistant.py
V17 Reborn - 우측 고정 젬마 보조 참모 대화창

역할:
- 전체 Part 1~8 공통 우측 대화창
- 중앙 작업창을 직접 덮어쓰지 않음
- 검수 / 보강 / 옵시디언 저장 / 젬마 재참조 / 최종 재검수 흐름의 UI 뼈대
"""

import streamlit as st


ASSISTANT_MODELS = [
    "gemma4:e2b",
    "gemma4:e4b",
    "Gemini",
    "앱 리서치",
]


def inject_right_assistant_css() -> None:
    """우측 고정 대화창 CSS."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-right: 390px !important;
        }

        .sage-right-assistant {
            position: fixed;
            top: 0;
            right: 0;
            width: 360px;
            height: 100vh;
            background: #061f26;
            border-left: 1px solid rgba(212, 175, 106, 0.35);
            z-index: 999999;
            display: flex;
            flex-direction: column;
            box-shadow: -8px 0 24px rgba(0,0,0,0.35);
            font-family: "Pretendard", "Noto Sans KR", sans-serif;
        }

        .sage-right-header {
            padding: 14px 16px 10px 16px;
            border-bottom: 1px solid rgba(212, 175, 106, 0.25);
            background: #062832;
        }

        .sage-right-title {
            color: #f5e9d3;
            font-size: 18px;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .sage-right-meta {
            color: #b9a98c;
            font-size: 12px;
            line-height: 1.5;
        }

        .sage-right-body {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            padding-bottom: 150px;
        }

        .sage-chat-card {
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(212,175,106,0.15);
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
            color: #f5e9d3;
            font-size: 13px;
            line-height: 1.55;
            white-space: pre-wrap;
        }

        .sage-chat-role {
            color: #d4af6a;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .sage-quick-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-top: 10px;
        }

        .sage-quick-item {
            background: rgba(212,175,106,0.1);
            border: 1px solid rgba(212,175,106,0.18);
            border-radius: 8px;
            padding: 7px;
            color: #f5e9d3;
            font-size: 11px;
            text-align: center;
        }

        .sage-right-input {
            position: fixed;
            right: 0;
            bottom: 0;
            width: 360px;
            background: #062832;
            border-top: 1px solid rgba(212, 175, 106, 0.25);
            padding: 10px 12px 12px 12px;
            z-index: 1000000;
        }

        .sage-input-mock {
            background: #102f38;
            border: 1px solid rgba(212,175,106,0.25);
            border-radius: 18px;
            color: #f5e9d3;
            padding: 10px 12px;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .sage-plus {
            font-size: 20px;
            color: #f5e9d3;
        }

        .sage-send {
            background: #f5e9d3;
            color: #062832;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_right_assistant_state() -> None:
    """우측 대화창 세션 기본값."""
    if "right_assistant_messages" not in st.session_state:
        st.session_state["right_assistant_messages"] = [
            {
                "role": "system",
                "content": (
                    "젬마 보조 참모 대기 중입니다.\\n"
                    "중앙 결과물을 직접 덮어쓰지 않고, 검수·보강·저장·재참조·최종 보고를 담당합니다."
                ),
            }
        ]

    if "right_assistant_model" not in st.session_state:
        st.session_state["right_assistant_model"] = "gemma4:e2b"


def add_right_assistant_message(role: str, content: str) -> None:
    """대화창 메시지 추가."""
    ensure_right_assistant_state()
    st.session_state["right_assistant_messages"].append(
        {
            "role": role,
            "content": content,
        }
    )


def render_right_assistant(current_part: str = "Part 1", episode_id: str = "EP001") -> None:
    """우측 고정 젬마 보조 참모 대화창 렌더링."""
    ensure_right_assistant_state()
    inject_right_assistant_css()

    selected_model = st.session_state.get("right_assistant_model", "gemma4:e2b")
    global_model = st.session_state.get("global_model", "gemma4:e2b")

    messages_html = ""
    for msg in st.session_state.get("right_assistant_messages", [])[-12:]:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        role_label = {
            "system": "시스템",
            "user": "사용자",
            "assistant": "젬마 참모",
            "critic": "검수",
            "research": "리서치",
        }.get(role, role)

        safe_content = (
            str(content)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        messages_html += f"""
        <div class="sage-chat-card">
            <div class="sage-chat-role">{role_label}</div>
            {safe_content}
        </div>
        """

    html = f"""
    <div class="sage-right-assistant">
        <div class="sage-right-header">
            <div class="sage-right-title">🤖 젬마 보조 참모</div>
            <div class="sage-right-meta">
                현재 파트: {current_part}<br>
                현재 에피소드: {episode_id}<br>
                중앙 모델: {global_model}<br>
                우측 모델: {selected_model}
            </div>
            <div class="sage-quick-grid">
                <div class="sage-quick-item">🔍 자동 검수</div>
                <div class="sage-quick-item">🌐 보강 리서치</div>
                <div class="sage-quick-item">🧠 옵시디언 저장</div>
                <div class="sage-quick-item">🔁 젬마 재참조</div>
                <div class="sage-quick-item">✅ 최종 재검수</div>
                <div class="sage-quick-item">📋 사용자 보고</div>
            </div>
        </div>
        <div class="sage-right-body">
            {messages_html}
        </div>
        <div class="sage-right-input">
            <div class="sage-input-mock">
                <span class="sage-plus">+</span>
                <span style="flex:1;color:#9fb0b6;">Ask anything / 명령 입력</span>
                <span>{selected_model}</span>
                <span class="sage-send">↑</span>
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)