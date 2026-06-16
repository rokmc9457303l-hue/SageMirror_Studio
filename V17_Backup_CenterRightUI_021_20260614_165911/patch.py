import sys
import os

target = r'C:\SageMirror_Production\V17_Working_RightChat_004\app_v17_2_3.py'
with open(target, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix payload and timeout
old_payload = """            payload = {
                "model": engine_id,
                "prompt": f"{context}\\n\\n{query}" if context else query,
                "stream": False,
                "options": {
                    "num_predict": 2000,
                    "temperature": 0.2
                }
            }
            resp = requests.post(url, json=payload, timeout=30)"""

new_payload = """            payload = {
                "model": engine_id,
                "prompt": f"{context}\\n\\n{query}" if context else query,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "num_predict": 2000,
                    "temperature": 0.2
                }
            }
            resp = requests.post(url, json=payload, timeout=(10, 180))"""

if old_payload in text:
    text = text.replace(old_payload, new_payload)
    print("Payload and timeout patched.")
else:
    print("Failed to patch payload. Maybe already patched or format differs?")

# 2. Fix UI spinner
old_spinner = """        with chat_container.chat_message("assistant"):
            with st.spinner("검색 및 답변 생성 중..."):"""

new_spinner = """        with chat_container.chat_message("assistant"):
            spinner_msg = "로컬 모델을 준비하고 있습니다. 최초 실행은 최대 2분 정도 걸릴 수 있습니다." if selected_mode in ["gemma4:e2b", "gemma4:e4b"] else "검색 및 답변 생성 중..."
            with st.spinner(spinner_msg):"""

if old_spinner in text:
    text = text.replace(old_spinner, new_spinner)
    print("UI Spinner patched.")
else:
    print("Failed to patch UI spinner. Trying an alternative search.")
    # fallback
    import re
    m = re.search(r'with st\.spinner\("([^"]+)"\):', text[text.find('with chat_container.chat_message("assistant"):') : text.find('res = run_right_research_engine')])
    if m:
        old_sp = m.group(0)
        new_sp = f'''spinner_msg = "로컬 모델을 준비하고 있습니다. 최초 실행은 최대 2분 정도 걸릴 수 있습니다." if selected_mode in ["gemma4:e2b", "gemma4:e4b"] else "{m.group(1)}"
            with st.spinner(spinner_msg):'''
        text = text.replace(old_sp, new_sp)
        print("Fallback UI Spinner patched.")

with open(target, 'w', encoding='utf-8') as f:
    f.write(text)
