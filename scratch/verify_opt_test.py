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
st.session_state["popup_keep_alive"] = "10m"
st.session_state["popup_num_predict"] = 40
st.session_state["popup_temperature"] = 0.2
st.session_state["popup_top_p"] = 0.8

# Import app modules
sys.path.append(os.getcwd())
from app_v17_1_4B import call_gemma

sys_ctx = """너는 현자의 거울 스튜디오의 60대 현자 멘토다.
[빠른 대화 지침]
1. 아주 짧고 간결하게 1~3문장 이내로 답하라.
2. 사용자의 작업을 도울 준비가 되어 있음을 실용적으로 말하라.
3. 철학적 과장이나 감성적 서술은 절대 하지 마라.
예: '안녕하세요. 어떤 작업을 이어가면 될까요?'"""

# 1차 테스트: 안녕
print("[ verify_opt_test ] call_gemma('안녕') 호출 시작...")
t0 = time.perf_counter()
try:
    res = call_gemma("안녕", system=sys_ctx, model="gemma4:e2b")
    t1 = time.perf_counter()
    print(f"[TEST 1 - STATUS] 성공")
    print(f"[TEST 1 - ELAPSED] {t1 - t0:.2f}초")
    print(f"[TEST 1 - RESPONSE] {res}")
except Exception as e:
    print(f"[TEST 1 - STATUS] 에러 발생: {e}")

# 2차 테스트: 짧게 인사해줘
print("\n[ verify_opt_test ] call_gemma('짧게 인사해줘') 호출 시작...")
t2 = time.perf_counter()
try:
    res = call_gemma("짧게 인사해줘", system=sys_ctx, model="gemma4:e2b")
    t3 = time.perf_counter()
    print(f"[TEST 2 - STATUS] 성공")
    print(f"[TEST 2 - ELAPSED] {t3 - t2:.2f}초")
    print(f"[TEST 2 - RESPONSE] {res}")
except Exception as e:
    print(f"[TEST 2 - STATUS] 에러 발생: {e}")
