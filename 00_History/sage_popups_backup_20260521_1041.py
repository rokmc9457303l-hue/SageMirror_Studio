# -*- coding: utf-8 -*-
"""
sage_popups.py — 팝업 다이얼로그 (옵시디언/프롬프트 편집 + Sage 대화)
"""

import streamlit as st
from datetime import datetime
from sage_config import (
    DEFAULT_OBSIDIAN_RULES, DEFAULT_BASE_PROMPT,
    SAGE_PERSONA, OLLAMA_MODEL,
)
from sage_engine import call_gemma, call_gemma_stream, tavily_search, check_ollama_status


# =====================================================================
# 옵시디언 규칙서 편집 팝업
# =====================================================================
@st.dialog("📚 옵시디언 규칙서 — 상세 편집", width="large")
def popup_edit_obsidian():
    st.caption("성경·철학·에세이 참조 원칙 (모든 파트의 Gemma 호출 시스템 컨텍스트로 주입)")
    st.markdown("##### 📖 현재 내용 (스크롤 + 드래그 복사)")
    with st.container(height=350, border=True):
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;"
            f"padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>"
            f"{st.session_state.obsidian_rules}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("##### ✏️ 편집 (마우스로 세로 크기 자유 조절)")
    new_val = st.text_area(
        "옵시디언 규칙서 본문",
        value=st.session_state.obsidian_rules,
        height=280,
        key="popup_obsidian_edit_ta",
        label_visibility="collapsed",
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💾 저장", use_container_width=True, type="primary", key="ob_save"):
            st.session_state.obsidian_history.append(st.session_state.obsidian_rules)
            st.session_state.obsidian_rules = new_val
            st.toast("✅ 옵시디언 규칙서 저장", icon="✅")
            st.rerun()
    with c2:
        if st.button(
            f"⬅️ 뒤로 ({len(st.session_state.obsidian_history)})",
            use_container_width=True, key="ob_back",
            disabled=len(st.session_state.obsidian_history) == 0,
        ):
            st.session_state.obsidian_rules = st.session_state.obsidian_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 기본값", use_container_width=True, key="ob_reset"):
            st.session_state.obsidian_history.append(st.session_state.obsidian_rules)
            st.session_state.obsidian_rules = DEFAULT_OBSIDIAN_RULES
            st.rerun()
    with c4:
        st.download_button(
            "📥 .md",
            data=st.session_state.obsidian_rules,
            file_name=f"obsidian_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            use_container_width=True, key="ob_dl",
        )


# =====================================================================
# 기본 프롬프트 편집 팝업
# =====================================================================
@st.dialog("🎯 기본 프롬프트 (타겟 선정 원칙) — 상세 편집", width="large")
def popup_edit_prompt():
    st.caption("Part 1 Librarian의 채널 선정 1·2순위 규칙.")
    st.markdown("##### 📖 현재 내용 (스크롤 + 드래그 복사)")
    with st.container(height=350, border=True):
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;"
            f"padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>"
            f"{st.session_state.base_prompt_rules}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("##### ✏️ 편집")
    new_val = st.text_area(
        "기본 프롬프트 본문",
        value=st.session_state.base_prompt_rules,
        height=280,
        key="popup_prompt_edit_ta",
        label_visibility="collapsed",
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💾 저장", use_container_width=True, type="primary", key="pr_save"):
            st.session_state.prompt_history.append(st.session_state.base_prompt_rules)
            st.session_state.base_prompt_rules = new_val
            st.toast("✅ 기본 프롬프트 저장", icon="✅")
            st.rerun()
    with c2:
        if st.button(
            f"⬅️ 뒤로 ({len(st.session_state.prompt_history)})",
            use_container_width=True, key="pr_back",
            disabled=len(st.session_state.prompt_history) == 0,
        ):
            st.session_state.base_prompt_rules = st.session_state.prompt_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 기본값", use_container_width=True, key="pr_reset"):
            st.session_state.prompt_history.append(st.session_state.base_prompt_rules)
            st.session_state.base_prompt_rules = DEFAULT_BASE_PROMPT
            st.rerun()
    with c4:
        st.download_button(
            "📥 .txt",
            data=st.session_state.base_prompt_rules,
            file_name=f"base_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            use_container_width=True, key="pr_dl",
        )


# =====================================================================
# Sage Pop-up (Gemma + Tavily) 대화 팝업
# =====================================================================

def _on_popup_send():
    q = st.session_state.get("popup_chat_input_ta", "")
    if q.strip():
        st.session_state.popup_history.append({"role": "user", "content": q})
        st.session_state.pending_stream = q
        st.session_state.popup_chat_input_ta = ""

@st.dialog(f"🤖 세이지 팝업 — {OLLAMA_MODEL} + Tavily", width="large")
def popup_assistant():
    status = check_ollama_status()
    c_stat1, c_stat2 = st.columns(2)
    with c_stat1:
        if status["server"] and status["model"]:
            st.success(f"🟢 연결 정상: {OLLAMA_MODEL}")
        else:
            st.error(f"🔴 연결 에러: {OLLAMA_MODEL} 미확인")
    with c_stat2:
        if st.session_state.tavily_api_key:
            st.success("🟢 Tavily API (인터넷) 연결 정상")
        else:
            st.warning("🔴 Tavily API Key 미입력")
            
    st.markdown(f"<span class='model-badge'>🧠 {OLLAMA_MODEL}</span>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["💬 로컬 Gemma 대화", "🌐 Tavily 웹 리서치"])

    # ─── Gemma 대화 ───
    with tab1:
        st.markdown("##### 💬 대화 기록 (스크롤 / 드래그 복사)")
        chat_container = st.container(height=380, border=True)

        st.markdown("##### ✏️ 질문 입력")
        st.text_area(
            "질문 입력", key="popup_chat_input_ta",
            placeholder="현자에게 물어보세요... (전송 버튼 클릭)",
            height=140, label_visibility="collapsed",
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.button("📤 전송", use_container_width=True, key="popup_send", type="primary", on_click=_on_popup_send)
        with c2:
            back = st.button(
                f"⬅️ 뒤로 ({len(st.session_state.popup_history)//2})",
                use_container_width=True, key="popup_back",
                disabled=len(st.session_state.popup_history) < 2,
            )
        with c3:
            clear = st.button("🗑️ 초기화", use_container_width=True, key="popup_clear")
        with c4:
            if st.session_state.popup_history:
                all_chat = "\n\n".join(
                    f"[{m['role'].upper()}]\n{m['content']}"
                    for m in st.session_state.popup_history
                )
                st.download_button(
                    "📥 .md", data=all_chat,
                    file_name=f"sage_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    use_container_width=True, key="popup_dl",
                )

        if back and len(st.session_state.popup_history) >= 2:
            st.session_state.popup_history = st.session_state.popup_history[:-2]
            st.rerun()
        if clear:
            st.session_state.popup_history = []
            st.rerun()

        # 대화 내용 렌더링 및 스트리밍 처리 (가장 마지막에 실행되어야 정상 위치에 출력됨)
        with chat_container:
            if not st.session_state.popup_history and not st.session_state.get("pending_stream"):
                st.caption("아직 대화가 없습니다. 아래에 질문을 입력하세요.")
                
            for msg in st.session_state.popup_history:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div class='chat-bubble-user'><b>🧑 You</b><br>{msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div class='chat-bubble-sage'><b>🤖 Sage ({OLLAMA_MODEL})</b><br>{msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                    with st.expander("📋 복사용 텍스트", expanded=False):
                        st.code(msg["content"], language="markdown")

            # 대기 중인 스트리밍이 있다면 실행
            if st.session_state.get("pending_stream"):
                q_stream = st.session_state.pending_stream
                sys_ctx = SAGE_PERSONA + "\n\n[옵시디언 규칙서]\n" + st.session_state.obsidian_rules
                
                with st.status("🔮 젬마가 깊은 사유에 빠졌습니다...", expanded=True) as status:
                    st.write("지식의 심연을 들여다보고 있습니다...")
                    
                    st.markdown(f"<div class='chat-bubble-sage'><b>🤖 Sage ({OLLAMA_MODEL})</b><br>", unsafe_allow_html=True)
                    ans_placeholder = st.empty()
                    full_response = ""
                    
                    for token in call_gemma_stream(q_stream, system=sys_ctx):
                        full_response += token
                        ans_placeholder.markdown(full_response + "▌")
                    ans_placeholder.markdown(full_response)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    status.update(label="✅ 사유 완료", state="complete", expanded=False)
                
                with st.expander("📋 복사용 텍스트", expanded=False):
                    st.code(full_response, language="markdown")
                
                st.session_state.popup_history.append({"role": "assistant", "content": full_response})
                st.session_state.pending_stream = None

    # ─── Tavily ───
    with tab2:
        st.markdown("##### 🌐 웹 검색")
        sq = st.text_area(
            "검색어", key="tavily_q_ta",
            placeholder="예: 빅터 프랭클 의미치료 사례",
            height=80, label_visibility="collapsed",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            do_search = st.button("🔍 검색", key="tavily_search_btn",
                                  use_container_width=True, type="primary")
        with c2:
            sback = st.button(
                f"⬅️ 이전 ({len(st.session_state.popup_search_history)})",
                key="tavily_back", use_container_width=True,
                disabled=len(st.session_state.popup_search_history) == 0,
            )
        with c3:
            sclear = st.button("🗑️ 초기화", key="tavily_clear", use_container_width=True)

        if sback and st.session_state.popup_search_history:
            st.session_state.popup_search_history.pop()
            st.rerun()
        if sclear:
            st.session_state.popup_search_history = []
            st.rerun()
        if do_search and sq.strip():
            with st.spinner("Tavily 검색 중..."):
                res = tavily_search(sq, st.session_state.tavily_api_key)
            st.session_state.popup_search_history.append({"q": sq, "res": res})
            st.rerun()

        st.markdown("##### 📊 검색 결과")
        with st.container(height=380, border=True):
            if not st.session_state.popup_search_history:
                st.caption("아직 검색 기록이 없습니다.")
            else:
                latest = st.session_state.popup_search_history[-1]
                st.markdown(f"**🔎 검색어:** `{latest['q']}`")
                res = latest["res"]
                if "error" in res:
                    st.error(res["error"])
                else:
                    if res.get("answer"):
                        st.info(res["answer"])
                        with st.expander("📋 복사용", expanded=False):
                            st.code(res["answer"], language="markdown")
                        st.divider()
                    for idx, r in enumerate(res.get("results", []), 1):
                        st.markdown(f"**{idx}. [{r.get('title','')}]({r.get('url','')})**")
                        st.write(r.get("content", ""))
                        st.caption(f"[SOURCE: {r.get('url','')}]")
                        st.divider()
