import sys
sys.stdout.reconfigure(encoding="utf-8")
filepath = r"C:\SageMirror_Production\sage_popups.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old = '''                # \uc2dc\uc2a4\ud15c \ucee8\ud14d\uc2a4\ud2b8 \uad6c\uc131
                _current_mode = st.session_state.get("popup_gemma_mode", "A")'''

if old in content:
    print("이미 수정됨")
else:
    target = '                # \u2500\u2500 \ud1b5\ud569 \uc2dc\uc2a4\ud15c \ucee8\ud14d\uc2a4\ud2b8 \uad6c\uc131 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500'
    idx = content.find(target)
    if idx == -1:
        print("ERROR: 찾지 못함")
    else:
        line_num = content[:idx].count('\n') + 1
        print(f"찾음: {line_num}라인")
        print(repr(content[idx:idx+200]))
