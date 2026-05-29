import sys
sys.stdout.reconfigure(encoding="utf-8")
fp = r"C:\SageMirror_Production\sage_popups_v17_1_18.py"
with open(fp, "r", encoding="utf-8") as f:
    code = f.read()

old = '''            # 모델별 분기 처리
            with st.spinner("● ● ●"):
                import time as _time
                _t0 = _time.perf_counter()'''

new = '''            # 모델별 분기 처리 — _chat_box 안에서 로딩 표시
            import time as _time
            _t0 = _time.perf_counter()
            with _chat_box:
                with st.chat_message("assistant"):
                    _resp_ph = st.empty()
                    _resp_ph.markdown("● ● ●")
            with st.spinner(""):'''

if old in code:
    code = code.replace(old, new, 1)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS")
else:
    print("ERROR: 못찾음")
