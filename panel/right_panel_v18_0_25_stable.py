# -*- coding: utf-8 -*-
"""
panel/right_panel.py — v5 비스트리밍 안정 버전

핵심 변경:
- stream=True → stream=False (Thinking 모드 무한 대기 방지)
- 명시적 진행 표시 (사용자가 응답 진행 상황 인지)
- timeout 명확히 작동
"""

import streamlit as st
import requests
from datetime import datetime

from core.config import MODELS, DEFAULT_MODEL, PART_NAMES
from core.state import get_state, set_state
from core.auto_save import schedule_chat_save


BRAIN_SYSTEM_PROMPT = """너는 현자의 거울 스튜디오의 공장장 젬마다.

[CRITICAL]
- 한국어로만 답변
- 1~3문장 이내
- 즉시 본론, 부연 설명 없음
- "Thinking", "Process" 단어 사용 금지

[역할] 현자(60대 콘텐츠 크리에이터)의 비서
[금지] AI 냄새 표현, 추측 인용, 영어 답변
"""


def call_gemini_with_messages(messages: list, model_key: str) -> str:
    """Gemini API 멀티턴 호출"""
    try:
        from google import genai as _genai
        api_key = st.session_state.get("api_gemini", "")
        if not api_key:
            return "Gemini API 키가 없습니다."
        client = _genai.Client(api_key=api_key)
        system_txt = ""
        gemini_contents = []
        for m in messages:
            if m["role"] == "system":
                system_txt = m["content"]
            elif m["role"] == "user":
                gemini_contents.append(
                    _genai.types.Content(
                        role="user",
                        parts=[_genai.types.Part(text=m["content"])]
                    )
                )
            elif m["role"] == "assistant":
                gemini_contents.append(
                    _genai.types.Content(
                        role="model",
                        parts=[_genai.types.Part(text=m["content"])]
                    )
                )
        cfg_obj = _genai.types.GenerateContentConfig(
            system_instruction=system_txt,
            max_output_tokens=4096,
            temperature=0.7,
        )
        resp = client.models.generate_content(
            model=model_key,
            contents=gemini_contents,
            config=cfg_obj,
        )
        return resp.text or "응답 없음"
    except Exception as e:
        return f"[Gemini 오류] {e}"


def call_ollama_sync(prompt: str, system: str = "", model: str = None,
                     timeout: int = 120) -> tuple:
    """Ollama 동기 호출 (비스트리밍) — Thinking 후처리 / Gemini 자동 라우팅"""
    import time
    import re

    current_model = get_state("current_model", DEFAULT_MODEL)
    model = model or current_model

    # ── Gemini 라우팅 ────────────────────────────────
    if "gemini" in model.lower():
        start = time.time()
        try:
            from core.brain import call_gemini
            response = call_gemini(prompt=prompt, system=system, model=model)
            elapsed = time.time() - start
            if not response or response.startswith("[Gemini"):
                return False, response or "(빈 응답)", elapsed
            return True, response, elapsed
        except Exception as e:
            return False, f"(Gemini 오류: {e})", time.time() - start

    # ── Ollama 호출 ──────────────────────────────────
    full = (system.strip() + "\n\n" + prompt) if system.strip() else prompt

    payload = {
        "model": model,
        "prompt": full,
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "num_predict": 400,
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
        },
    }

    start = time.time()

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=timeout,
        )
        elapsed = time.time() - start

        if resp.status_code != 200:
            return False, f"오류: HTTP {resp.status_code}", elapsed

        data = resp.json()
        response_text = data.get("response", "")

        if not response_text:
            return False, "(빈 응답 — 모델 재시도 권장)", elapsed

        # ── Thinking 부분 후처리 ────────────────────
        cleaned = clean_thinking_response(response_text)

        if not cleaned.strip():
            return False, "(Thinking 후 빈 응답 — 다시 시도해주세요)", elapsed

        return True, cleaned, elapsed

    except requests.Timeout:
        elapsed = time.time() - start
        return False, f"({timeout}초 시간 초과)", elapsed
    except requests.ConnectionError:
        return False, "(Ollama 서버 연결 실패)", 0
    except Exception as e:
        return False, f"(오류: {e})", 0


def clean_thinking_response(text: str) -> str:
    """Thinking 부분 제거 후 실제 답변만 추출"""
    import re
    
    # 패턴 1: "...done thinking." 이후만 추출
    if "...done thinking." in text:
        parts = text.split("...done thinking.")
        if len(parts) > 1:
            return parts[-1].strip()
    
    # 패턴 2: "</think>" 태그 이후
    if "</think>" in text:
        parts = text.split("</think>")
        if len(parts) > 1:
            return parts[-1].strip()
    
    # 패턴 3: "Thinking Process:" 블록 제거
    text = re.sub(
        r'Thinking(?:\s*Process)?:.*?(?=\n\n)',
        '',
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    
    # 패턴 4: 줄 단위로 "1.", "2." 형식의 thinking 단계 제거
    lines = text.split('\n')
    filtered = []
    in_thinking = False
    
    for line in lines:
        stripped = line.strip()
        if re.match(r'^Thinking', stripped, re.IGNORECASE):
            in_thinking = True
            continue
        if in_thinking and re.match(r'^\d+\.\s+\*\*', stripped):
            continue
        if in_thinking and stripped.startswith('*'):
            continue
        if in_thinking and stripped == '':
            in_thinking = False
            continue
        if not in_thinking:
            filtered.append(line)
    
    result = '\n'.join(filtered).strip()
    return result if result else text.strip()


def render_right_panel():
    """우측 브레인 패널"""
    
    current_part = get_state("current_part", 1)
    part_name = PART_NAMES.get(current_part, "?")
    
    st.markdown("### 🧙 SAGE 브레인")
    st.caption(f"📍 Part {current_part} - {part_name}")
    
    # 자동 모니터링 상태
    from core.auto_monitor import get_all_status, has_alerts, get_alert_summary
    status = get_all_status()
    
    c1, c2, c3 = st.columns(3)
    c1.caption(f"{status['rag']['color']} RAG ({status['rag']['files']})")
    c2.caption(f"{status['cite']['color']} 인용")
    c3.caption(f"{status['smell']['color']} AI냄새")
    
    if has_alerts():
        alerts = get_alert_summary()
        with st.expander(f"⚠️ 알림 {len(alerts)}건", expanded=False):
            for alert in alerts:
                st.warning(f"**{alert['type']}**: {alert['message']}")
    
    # [+] 허브 메뉴 (새로 추가)
    from panel.hub_menu import render_hub_menu, render_text_input_panel
    render_hub_menu()
    render_text_input_panel()
    
    # 모델 선택
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
    
    render_chat_with_response()
    
    user_input = st.chat_input("메시지를 입력하세요...")
    
    if user_input:
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
        
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if history[-1]["role"] == "user":
            user_msg = history[-1]["content"]
            model_key = get_state("rp_model", DEFAULT_MODEL)
            with st.chat_message("assistant"):
                with st.status("⬡ 생각 중...", expanded=True) as status_box:
                    st.write("📡 모델 호출 중...")
                    response = generate_response_sync(user_msg, history[:-1], model_key)
                    status_box.update(label="✅ 완료", state="complete")
                st.markdown(response)
            history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "model": model_key,
            })
            set_state("rp_history", history)


def generate_response_sync(user_msg: str, history: list, model_key: str) -> str:
    """Tavily 검색 우선 → Gemini/Ollama 분석 응답 생성"""
    import requests as _req

    # 1. Tavily 실시간 검색 시도
    tavily_context = ""
    tavily_key = st.session_state.get("api_tavily", "")
    if tavily_key:
        try:
            tv_res = _req.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": user_msg,
                    "search_depth": "advanced",
                    "max_results": 5,
                    "include_answer": True
                },
                timeout=15
            )
            if tv_res.status_code == 200:
                tv_data = tv_res.json()
                lines = []
                if tv_data.get("answer"):
                    lines.append(f"[검색 요약] {tv_data['answer']}")
                for r in tv_data.get("results", [])[:5]:
                    lines.append(
                        f"- {r.get('title','')}: {r.get('content','')[:200]} "
                        f"(출처: {r.get('url','')})"
                    )
                tavily_context = "\n".join(lines)
        except Exception:
            tavily_context = ""

    # 2. 시스템 프롬프트 구성
    system_prompt = (
        "당신은 현자의 거울 스튜디오 공장장 젬마입니다.\n"
        "현자님(60대 유튜브 크리에이터)을 보좌합니다.\n"
        "채널: 현자의 거울 (@Ethan Cinematic Video)\n"
        "타겟: 4070세대 / 철학·심리·성경 다큐 스타일\n"
        "답변은 반드시 한국어로, 존댓말로 작성하세요.\n"
    )
    if tavily_context:
        system_prompt += (
            "\n[실시간 검색 결과 - 반드시 아래 정보를 바탕으로 답변하세요]\n"
            + tavily_context + "\n"
        )

    # 3. 대화 히스토리 구성
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    # 4. 모델 라우팅
    cur_model = st.session_state.get("current_model", DEFAULT_MODEL)
    model_info = MODELS.get(cur_model, {})
    model_type = model_info.get("type", "local")

    if model_type == "remote":
        result = call_gemini_with_messages(messages, cur_model)
    else:
        success, result, _ = call_ollama_sync(user_msg, BRAIN_SYSTEM_PROMPT, cur_model)
        if not success:
            result = result or "응답을 생성하지 못했습니다."

    return result if result else "응답을 생성하지 못했습니다."
