import sys
sys.stdout.reconfigure(encoding="utf-8")
fp = r"C:\SageMirror_Production\sage_popups.py"
with open(fp, "r", encoding="utf-8") as f:
    content = f.read()
old = 'if st.session_state.get("popup_use_rag", True):'
new = 'if st.session_state.get("popup_use_rag", True) and _current_mode == "B":'
if old in content:
    content = content.replace(old, new, 1)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS")
else:
    print("ERROR: 찾지 못함")
