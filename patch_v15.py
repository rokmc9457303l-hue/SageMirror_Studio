# -*- coding: utf-8 -*-
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open("sage_popups_v17_1_15.py", "r", encoding="utf-8") as f:
    code = f.read()

changes = []

# 수정 1: [0, 4] → [0.15, 3.85]
target1 = "_col_w = [1, 3] if _is_open else [0, 4]"
repl1 = "_col_w = [1, 3] if _is_open else [0.15, 3.85]"
if target1 in code:
    code = code.replace(target1, repl1)
    changes.append("수정 1 성공")
else:
    changes.append("수정 1 실패 (대상 없음)")

# 수정 2: 접기 버튼 rerun 제거 (들여쓰기 12칸으로 수정)
target2 = '''            if st.button("\u226a", key="sb_close", help="\uc88c\uce21 \ubc14 \uc811\uae30"):
                st.session_state.sidebar_open = False
                st.rerun()'''
repl2 = '''            if st.button("\u226a", key="sb_close", help="\uc88c\uce21 \ubc14 \uc811\uae30"):
                st.session_state.sidebar_open = False'''
if target2 in code:
    code = code.replace(target2, repl2)
    changes.append("수정 2 성공")
else:
    changes.append("수정 2 실패 (대상 없음)")

# 수정 3: 펼치기 버튼 rerun 제거
target3 = '''            if st.button("\u226b", key="sb_open", help="\uc88c\uce21 \ubc14 \uc5f4\uae30"):
                st.session_state.sidebar_open = True
                st.rerun()'''
repl3 = '''            if st.button("\u226b", key="sb_open", help="\uc88c\uce21 \ubc14 \uc5f4\uae30"):
                st.session_state.sidebar_open = True'''
if target3 in code:
    code = code.replace(target3, repl3)
    changes.append("수정 3 성공")
else:
    changes.append("수정 3 실패 (대상 없음)")

# 수정 4: 응답 후 st.rerun() 제거
target4 = "            _save_chat_history(st.session_state.popup_history)\n            st.rerun()"
repl4 = "            _save_chat_history(st.session_state.popup_history)"
if target4 in code:
    code = code.replace(target4, repl4)
    changes.append("수정 4 성공")
else:
    changes.append("수정 4 실패 (대상 없음)")

with open("sage_popups_v17_1_15.py", "w", encoding="utf-8") as f:
    f.write(code)

for c in changes:
    print(c)

print("패치 프로세스 완료")
