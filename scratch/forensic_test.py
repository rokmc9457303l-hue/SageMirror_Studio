import time
import os
import sys

# Streamlit session state mock
class SessionStateMock(dict):
    def __getattr__(self, item):
        return self.get(item)
    def __setattr__(self, key, value):
        self[key] = value

import streamlit as st
if not hasattr(st, 'session_state') or not st.session_state:
    st.session_state = SessionStateMock()

st.session_state["popup_gemma_mode"] = "A"
st.session_state["selected_model"] = "gemma4:e2b"

# Import app modules
sys.path.append(os.getcwd())
from app_v17_1_4A import call_gemma, _orig_call_gemma

sys_ctx = """너는 현자의 거울 스튜디오의 60대 현자 멘토다.
[빠른 대화 지침]
1. 아주 짧고 간결하게 1~3문장 이내로 답하라.
2. 사용자의 작업을 도울 준비가 되어 있음을 실용적으로 말하라.
3. 철학적 과장이나 감성적 서술은 절대 하지 마라.
예: '안녕하세요. 어떤 작업을 이어가면 될까요?'"""

print("[ forensic_test ] call_gemma('안녕') 호출 시작...")
t0 = time.perf_counter()
try:
    res = call_gemma("안녕", system=sys_ctx, model="gemma4:e2b")
    t1 = time.perf_counter()
    print(f"[STATUS] 성공")
    print(f"[ELAPSED] {t1 - t0:.2f}초")
    print(f"[RESPONSE] {res}")
except Exception as e:
    print(f"[STATUS] 에러 발생: {e}")
