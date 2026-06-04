# -*- coding: utf-8 -*-
"""
panel/right_panel.py — v4 표준 채팅 패턴

해결:
- st.chat_input 으로 입력 자동 클리어
- 응답을 대화 컨테이너 안에서 생성
- 스트리밍 응답 유지
"""

import streamlit as st
import requests
import json
from datetime import datetime

from core.config import MODELS, DEFAULT_MODEL, PART_NAMES
from core.state import get_state, set_state
from core.auto_save import schedule_chat_save


BRAIN_SYSTEM_PROMPT = """너는 현자의 거울 스튜디오의 공장장 젬마다.

[CRITICAL — 생각 과정 표시 금지]
- "Thinking", "Thinking Process", "Let me think" 같은 단어 절대 금지
- 분석 과정 단계 절대 표시 금지
- 즉시 최종 답변만 출력
- 답변은 1~3 문장 이내

[역할] 현자(60대 한국인 콘텐츠 크리에이터)의 비서
[원칙] 빠르고 간결한 한국어 응답, 4070 어조
[금지] AI 냄새 표현, 추측 인용, 장황한 설명, 영어 답변
[형식] 바로 본론, 부연 설명 없음
"""


def quick_stream(prompt: str, system: str = "", model: str = None, timeout: int = 180):
    """Ollama 스트리밍"""
    model = model or DEFAULT_MODEL
    full = (system.strip() + "\n\n" + prompt) if system.strip() else prompt
    
    payload = {
        "model": model,
        "prompt": full,
        "stream": True,
        "keep_alive": "30m",
        "options": {
            "num_predict": 200,
            "temperature": 0.2,
            "top_p": 0.85,
            "top_k": 20,
            "repeat_penalty": 1.1,
            "stop": ["Thinking", "thinking", "Process:", "Step 1"],
        },
    }
    
    try:
        with requests.post(
            "http://localhost:11434/api/generate",
            json=payload, stream=True, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                except Exception:
                    continue
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done", False):
                    break
    except requests.Timeout:
        yield "\n\n(응답 시간 초과 — Ollama 모델이 워밍업 안 됐을 수 있습니다)"
    except Exception as e:
        yield f"\n\n(오류: {e})"


def render_right_panel():
    """우측 브레인 패널 메인"""
    
    current_part = get_state("current_part", 1)
    part_name = PART_NAMES.get(current_part, "?")
    
    # 헤더
    st.markdown("### 🧙 SAGE 브레인")
    st.caption(f"📍 Part {current_part} - {part_name}")
    
    # 상태 표시줄
    c1, c2, c3 = st.columns(3)
    c1.caption("🟢 RAG")
    c2.caption("🟢 인용")
    c3.caption("🟢 AI냄새")
    
    # 모델 선택 (별도 줄)
    models = list(MODELS.keys())
    cur_model = get_state("rp_model", DEFAULT_MODEL)
    sel = st.selectbox(
        "모델",
        models,
        index=models.index(cur_model) if cur_model in models else 0,
        format_func=lambda x: MODELS[x]["label"],
        key="rp_model_sel",
    )
    if sel != cur_model:
        set_state("rp_model", sel)
    
    st.markdown("---")
    
    # 대화 + 응답 생성 (모두 컨테이너 안)
    render_chat_with_response()
    
    # 입력 (chat_input 사용 → 자동 클리어)
    user_input = st.chat_input("메시지를 입력하세요...")
    
    if user_input:
        # 사용자 메시지만 추가하고 rerun
        history = get_state("rp_history", [])
        history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat(),
        })
        set_state("rp_history", history)
        st.rerun()


def render_chat_with_response():
    """대화 표시 + 응답 생성 (모두 컨테이너 안)"""
    history = get_state("rp_history", [])
    
    box = st.container(height=400, border=True)
    
    with box:
        if not history:
            st.markdown(
                "<div style='color:#888; text-align:center; padding:50px 20px;'>"
                "💬 SAGE 브레인과 대화를 시작하세요"
                "</div>",
                unsafe_allow_html=True
            )
            return
        
        # 기존 대화 표시
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # 마지막 메시지가 user면 → 응답 생성 (컨테이너 안)
        if history[-1]["role"] == "user":
            generate_response_in_container(history)


def generate_response_in_container(history):
    """응답 생성 (컨테이너 안에서)"""
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        # 컨텍스트 준비
        recent = history[-7:-1] if len(history) > 1 else []
        recent_ctx = "\n".join([
            f"{m['role']}: {m['content'][:200]}"
            for m in recent
        ])
        
        current_part = get_state("current_part", 1)
        model = get_state("rp_model", DEFAULT_MODEL)
        
        full_prompt = f"""[Part {current_part} - {PART_NAMES.get(current_part)}]

[최근 대화]
{recent_ctx if recent_ctx else '(첫 대화)'}

[메시지]
{history[-1]["content"]}

간결하게 답변하라."""
        
        # 스트리밍 응답
        full_response = ""
        for token in quick_stream(
            prompt=full_prompt,
            system=BRAIN_SYSTEM_PROMPT,
            model=model,
            timeout=180,
        ):
            full_response += token
            placeholder.markdown(full_response + "▌")
        
        placeholder.markdown(full_response)
        
        # 응답을 history에 추가
        history.append({
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now().isoformat(),
            "model": model,
        })
        set_state("rp_history", history)
        
        # 백그라운드 자동 저장
        try:
            schedule_chat_save(
                user_input=history[-2]["content"],
                ai_response=full_response,
                part_context=current_part,
            )
        except Exception:
            pass
