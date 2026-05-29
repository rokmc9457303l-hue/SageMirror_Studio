# -*- coding: utf-8 -*-
import sys
import re

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open("sage_popups_v17_1_17.py", "r", encoding="utf-8") as f:
    code = f.read()

fixes = 0

# ─── 수정 1: input_key 세션 초기화 ───────────────
old1 = "    _defs = {"
new1 = """    if "input_key" not in st.session_state:
        st.session_state["input_key"] = 0
    _defs = {"""
if old1 in code and '"input_key" not in st.session_state' not in code:
    code = code.replace(old1, new1, 1)
    fixes += 1
    print("수정1 완료: input_key 초기화")
else:
    print("수정1 스킵 (이미 적용됨)")

# ─── 수정 2: 대화 기록 height 복원 ──────────────
if "        _chat_box = st.container()" in code:
    code = code.replace(
        "        _chat_box = st.container()",
        "        _chat_box = st.container(height=350)"
    )
    fixes += 1
    print("수정2 완료: height=350 복원")
elif "height=350" in code:
    print("수정2 스킵 (height=350 이미 있음)")
else:
    print("수정2 실패: _chat_box 못찾음")

# ─── 수정 3: 입력 영역 Claude 스타일로 교체 ─────
pattern = r'        # ── 입력 영역.*?use_container_width=True\)'
match = re.search(pattern, code, re.DOTALL)
if match:
    old_input = match.group(0)
    new_input = '''        # ── 입력 영역 (Claude 스타일) ──────────────────────────
        # CSS: textarea 얇게
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
</style>""", unsafe_allow_html=True)

        _inp_key = f"popup_input_{st.session_state.get('input_key', 0)}"
        _ic, _bc, _mc = st.columns([4, 0.7, 1.5])
        with _ic:
            _prompt = st.text_area(
                "입력",
                key=_inp_key,
                placeholder="현자에게 물어보세요...",
                label_visibility="collapsed",
                height=68,
                max_chars=3000,
            )
        with _bc:
            st.markdown("<div style='margin-top:20px'></div>",
                        unsafe_allow_html=True)
            _send = st.button("↑", key="popup_send_17", type="primary",
                              use_container_width=True)
        with _mc:
            st.markdown("<div style='margin-top:4px'></div>",
                        unsafe_allow_html=True)
            _sel = st.selectbox(
                "모델",
                _MODELS,
                index=_MODELS.index(st.session_state.popup_selected_model)
                if st.session_state.popup_selected_model in _MODELS else 0,
                key="popup_model_sel_17",
                label_visibility="collapsed",
            )
            st.session_state.popup_selected_model = _sel'''
    code = code.replace(old_input, new_input, 1)
    fixes += 1
    print("수정3 완료: 입력 영역 Claude 스타일")
else:
    print("수정3 실패: 입력 영역 패턴 못찾음 — 수동 확인 필요")

# ─── 수정 4: 전송 후 input_key 증가 ─────────────
old4 = "            _save_chat_history(st.session_state.popup_history)"
new4 = """            _save_chat_history(st.session_state.popup_history)
            st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1"""

# 이전 버전에서 수정4가 적용되었는지 확인 (sage_popups_v17_1_16.py 에 st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1 가 이미 들어있는 경우)
already_has_key_increment = 'st.session_state["input_key"] = st.session_state.get("input_key"' in code or 'st.session_state[\'input_key\'] = st.session_state.get(\'input_key\'' in code

if already_has_key_increment:
    print("수정4 스킵 (이미 적용됨)")
elif old4 in code:
    code = code.replace(old4, new4, 1)
    fixes += 1
    print("수정4 완료: 전송 후 input_key 증가")
else:
    print("수정4 실패: _save_chat_history 대상 못찾음")

with open("sage_popups_v17_1_17.py", "w", encoding="utf-8") as f:
    f.write(code)

print(f"\n총 {fixes}개 수정 완료")
