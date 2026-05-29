# -*- coding: utf-8 -*-
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open("sage_popups_v17_1_16.py", "r", encoding="utf-8") as f:
    code = f.read()

changes = []

# 수정 1: 대화 기록 height=400 제거
target1 = "        _chat_box = st.container(height=400)"
repl1 = "        _chat_box = st.container()"
if target1 in code:
    code = code.replace(target1, repl1)
    changes.append("수정 1 성공")
else:
    changes.append("수정 1 실패 (대상 없음)")

# 수정 2+3: 모델선택/입력창/전송 한 행으로 통합
old_input = """        # ── 입력 영역 (Claude 스타일) ──────────────────────────
        # 모델 선택 (입력창 위 우측 정렬)
        _, _mc = st.columns([3, 1])
        with _mc:
            _sel = st.selectbox(
                "모델",
                _MODELS,
                index=_MODELS.index(st.session_state.popup_selected_model)
                if st.session_state.popup_selected_model in _MODELS else 0,
                key="popup_model_sel_14",
                label_visibility="collapsed",
            )
            st.session_state.popup_selected_model = _sel

        # 입력창 + 전송 버튼
        _ic, _bc = st.columns([5, 1])
        with _ic:
            _prompt = st.text_input(
                "입력",
                key="popup_input_14",
                placeholder="현자에게 물어보세요...",
                label_visibility="collapsed",
            )
        with _bc:
            _send = st.button("↑", key="popup_send_14", type="primary",
                              use_container_width=True)"""

new_input = """        # ── 입력 영역 (Claude 스타일) ──────────────────────────
        _ic, _bc, _mc = st.columns([4, 0.8, 1.5])
        with _ic:
            _inp_key = f"popup_input_{st.session_state.get('input_key', 0)}"
            _prompt = st.text_area(
                "입력",
                key=_inp_key,
                placeholder="현자에게 물어보세요...",
                label_visibility="collapsed",
                height=None,
                max_chars=2000,
            )
        with _bc:
            _send = st.button("↑", key="popup_send_14", type="primary",
                              use_container_width=True)
        with _mc:
            _sel = st.selectbox(
                "모델",
                _MODELS,
                index=_MODELS.index(st.session_state.popup_selected_model)
                if st.session_state.popup_selected_model in _MODELS else 0,
                key="popup_model_sel_14",
                label_visibility="collapsed",
            )
            st.session_state.popup_selected_model = _sel"""

if old_input in code:
    code = code.replace(old_input, new_input, 1)
    changes.append("수정 2+3 성공")
else:
    changes.append("수정 2+3 실패 (대상 없음)")

# 수정 4: 전송 후 input_key 증가
old_save = "            _save_chat_history(st.session_state.popup_history)"
new_save = """            _save_chat_history(st.session_state.popup_history)
            st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1"""

if old_save in code:
    code = code.replace(old_save, new_save, 1)
    changes.append("수정 4 성공")
else:
    changes.append("수정 4 실패 (대상 없음)")

with open("sage_popups_v17_1_16.py", "w", encoding="utf-8") as f:
    f.write(code)

for c in changes:
    print(c)

print("패치 프로세스 완료")
