import sys
import re

sys.stdout.reconfigure(encoding="utf-8")

with open("sage_popups_v17_1_21.py", "r", encoding="utf-8") as f:
    code = f.read()

fixes = 0

# === 수정 1: input_key를 popup_history 길이와 연동 ===
old1 = "_inp_key = f\"popup_input_{st.session_state.get('input_key', 0)}\""
new1 = "_inp_key = f\"popup_input_{len(st.session_state.popup_history)}\""
if old1 in code:
    code = code.replace(old1, new1, 1)
    fixes += 1
    print("수정1 완료: input_key = popup_history 길이 연동")
else:
    print("수정1 패턴 못찾음")

# === 수정 2: 응답 처리 블록 단순화 ===
old_resp = '''            # 사용자 + 로딩 표시 (_chat_box 안)
            with _chat_box:
                with st.chat_message("user"):
                    st.markdown(_prompt)
                _loading_ph = st.empty()
                with _loading_ph.container():
                    with st.chat_message("assistant"):
                        st.markdown("● ● ●")'''

new_resp = ""
if old_resp in code:
    code = code.replace(old_resp, new_resp, 1)
    fixes += 1
    print("수정2-1 완료: _chat_box 안 로딩 표시 제거")
else:
    print("수정2-1 패턴 못찾음")

if "if True:" in code:
    code = code.replace("if True:", "with st.spinner(\"● ● ● 응답 생성 중...\"):", 1)
    fixes += 1
    print("수정2-2 완료: st.spinner 교체")
else:
    print("수정2-2 패턴 못찾음")

# === 수정 3: 응답 저장 후 _loading_ph 교체 코드 제거 ===
old_save_pattern = '''            # 로딩 → 실제 응답으로 교체
            try:
                _loading_ph.empty()
                with _loading_ph.container():
                    with st.chat_message("assistant"):
                        st.markdown(_resp)
            except Exception:
                pass'''
if old_save_pattern in code:
    code = code.replace(old_save_pattern, "", 1)
    fixes += 1
    print("수정3-1 완료: _loading_ph 교체 제거")
else:
    print("수정3-1 패턴 못찾음")

old_input_key = '''            st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1'''
if old_input_key in code:
    code = code.replace(old_input_key, "            # input_key는 popup_history 길이로 자동 연동됨", 1)
    fixes += 1
    print("수정3-2 완료: input_key 수동 증가 제거")
else:
    print("수정3-2 패턴 못찾음")

# === 수정 4: 복사 버튼을 st.toast로 변경 ===
pattern = r'if st\.button\("□ 복사".*?st\.code\(_msg\["content"\], language="markdown"\)'
match = re.search(pattern, code, re.DOTALL)
if match:
    old_match = match.group(0)
    new_code = '''if st.button("□ 복사", key=_copy_id, help="클립보드 복사"):
                            st.toast("📋 응답이 클립보드에 복사되었습니다!")
                            try:
                                _esc = _msg["content"].replace("`", "\\\\`").replace("$", "\\\\$")
                                st.html(f"<script>navigator.clipboard.writeText(`{_esc}`);</script>")
                            except Exception:
                                pass'''
    code = code.replace(old_match, new_code, 1)
    fixes += 1
    print("수정4 완료: 복사 버튼 → toast + JS clipboard")
else:
    print("수정4 패턴 못찾음")

# === 수정 5: 입력 영역 columns gap 제거 + 통합 스타일 ===
old_cols = '_ic, _bc, _mc = st.columns([4, 0.7, 1.5])'
new_cols = '_ic, _bc, _mc = st.columns([5, 1, 1.5], gap="small")'
if old_cols in code:
    code = code.replace(old_cols, new_cols, 1)
    fixes += 1
    print("수정5 완료: 입력 영역 비율 조정")
else:
    print("수정5 패턴 못찾음")

with open("sage_popups_v17_1_21.py", "w", encoding="utf-8") as f:
    f.write(code)

print(f"\\n총 {fixes}개 수정 완료")
