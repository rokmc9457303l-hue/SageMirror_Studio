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
from sage_engine import call_gemma, tavily_search


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
@st.dialog("🤖 Sage Pop-up — Gemma4:e4b + Tavily", width="large")
def popup_assistant():
    st.markdown(f"<span class='model-badge'>🧠 {OLLAMA_MODEL}</span>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["💬 로컬 Gemma 대화", "🌐 Tavily 웹 리서치"])

    # ─── Gemma 대화 ───
    with tab1:
        st.markdown("##### 💬 대화 기록 (스크롤 / 드래그 복사)")
        with st.container(height=380, border=True):
            if not st.session_state.popup_history:
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

        st.markdown("##### ✏️ 질문 입력")
        q = st.text_area(
            "질문 입력", key="popup_chat_input_ta",
            placeholder="현자에게 물어보세요... (전송 버튼 클릭)",
            height=140, label_visibility="collapsed",
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            send = st.button("📤 전송", use_container_width=True, key="popup_send", type="primary")
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
        if send and q.strip():
            st.session_state.popup_history.append({"role": "user", "content": q})
            sys_ctx = SAGE_PERSONA + "\n\n[옵시디언 규칙서]\n" + st.session_state.obsidian_rules
            with st.spinner(f"Sage가 사색 중... ({OLLAMA_MODEL})"):
                ans = call_gemma(q, system=sys_ctx)
            st.session_state.popup_history.append({"role": "assistant", "content": ans})
            st.rerun()

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
