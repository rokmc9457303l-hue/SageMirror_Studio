import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("sage_popups_v17_1_20.py", "r", encoding="utf-8") as f:
    code = f.read()

fixes = 0

# === 수정 1: 대화창 height 350 → 500 ===
if "_chat_box = st.container(height=350)" in code:
    code = code.replace(
        "_chat_box = st.container(height=350)",
        "_chat_box = st.container(height=500)",
        1
    )
    fixes += 1
    print("수정1: 대화창 height 500 적용")

# === 수정 2: 입력 영역 CSS Claude 스타일 ===
old_css = '''        # CSS: textarea 얇게
        st.markdown("""
<style>
div[data-testid="stTextArea"] textarea {
    min-height: 52px !important;
    max-height: 160px !important;
    overflow-y: auto !important;
    resize: none !important;
    padding: 14px 16px !important;
    font-size: 0.95rem !important;
}
div[data-testid="stTextArea"] {
    border-radius: 12px !important;
}
</style>""", unsafe_allow_html=True)'''

new_css = '''        # CSS: Claude 스타일 입력창
        st.markdown("""
<style>
div[data-testid="stTextArea"] textarea {
    min-height: 60px !important;
    max-height: 200px !important;
    overflow-y: auto !important;
    resize: none !important;
    padding: 18px 22px !important;
    font-size: 1rem !important;
    border-radius: 24px !important;
    background-color: #1a1a21 !important;
    border: 1px solid #333344 !important;
    color: #EAEAEA !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: #9B59B6 !important;
    box-shadow: 0 0 0 2px rgba(155, 89, 182, 0.2) !important;
}
div[data-testid="stTextArea"] {
    border-radius: 24px !important;
}
button[data-testid="baseButton-primary"] {
    border-radius: 50% !important;
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    padding: 0 !important;
    font-size: 1.2rem !important;
}
div[data-testid="stSelectbox"] > div {
    border-radius: 20px !important;
    background-color: #1a1a21 !important;
}
</style>""", unsafe_allow_html=True)'''

if old_css in code:
    code = code.replace(old_css, new_css, 1)
    fixes += 1
    print("수정2: Claude 스타일 CSS 적용")
else:
    print("수정2: CSS 패턴 못찾음")

# === 수정 3: 응답 처리 — _chat_box 안 표시 + JS 초기화 ===
old_resp = '''        # ── 젬마 응답 처리 ─────────────────────────────────────
        if _send and _prompt and _prompt.strip():
            _cur_model = st.session_state.popup_selected_model

            st.session_state.popup_history.append({
                "role": "user",
                "content": _prompt,
                "model": _cur_model,
                "part": current_part_name,
            })

            _sys = "너는 현자의 거울 스튜디오의 어시스턴트다. 묻는 말에 정확하고 짧게 답하라."
            if st.session_state.get("tavily_rag_context"):
                _sys += f"\\n\\n[참조 자료]\\n{st.session_state.tavily_rag_context[:800]}"

            with st.spinner("● ● ●"):'''

new_resp = '''        # ── 젬마 응답 처리 ─────────────────────────────────────
        if _send and _prompt and _prompt.strip():
            _cur_model = st.session_state.popup_selected_model

            st.session_state.popup_history.append({
                "role": "user",
                "content": _prompt,
                "model": _cur_model,
                "part": current_part_name,
            })

            # 사용자 + 로딩 표시 (_chat_box 안)
            with _chat_box:
                with st.chat_message("user"):
                    st.markdown(_prompt)
                _loading_ph = st.empty()
                with _loading_ph.container():
                    with st.chat_message("assistant"):
                        st.markdown("● ● ●")

            _sys = "너는 현자의 거울 스튜디오의 어시스턴트다. 묻는 말에 정확하고 짧게 답하라."
            if st.session_state.get("tavily_rag_context"):
                _sys += f"\\n\\n[참조 자료]\\n{st.session_state.tavily_rag_context[:800]}"

            if True:'''

if old_resp in code:
    code = code.replace(old_resp, new_resp, 1)
    fixes += 1
    print("수정3: 사용자/로딩 표시 _chat_box 안 처리")

# === 수정 4: 응답 후 _loading_ph 교체 + JS 초기화 ===
old_save = '''            _save_chat_history(st.session_state.popup_history)
            st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1'''

new_save = '''            _save_chat_history(st.session_state.popup_history)
            st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1
            # 로딩 → 실제 응답으로 교체
            try:
                _loading_ph.empty()
                with _loading_ph.container():
                    with st.chat_message("assistant"):
                        st.markdown(_resp)
            except Exception:
                pass
            # JS 입력창 초기화 (st.html 권장 방식 사용)
            try:
                st.html(
                    "<script>setTimeout(()=>{var t=parent.document.querySelectorAll('textarea');t.forEach(x=>{if(x.placeholder&&x.placeholder.includes('현자')){x.value='';x.dispatchEvent(new Event('input',{bubbles:true}));}});},200);</script>"
                )
            except Exception:
                pass'''

if old_save in code:
    code = code.replace(old_save, new_save, 1)
    fixes += 1
    print("수정4: 응답 교체 + JS 초기화")

with open("sage_popups_v17_1_20.py", "w", encoding="utf-8") as f:
    f.write(code)

print(f"\\n총 {fixes}개 수정 완료")
