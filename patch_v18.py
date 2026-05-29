import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("sage_popups_v17_1_18.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

fixes = 0

# 수정1: popup_model_sel_14 블록 제거 (1608라인 근처)
start_del = None
end_del = None
for i, line in enumerate(lines):
    if 'key="popup_model_sel_14"' in line:
        for j in range(i, max(i-20, 0), -1):
            if lines[j].strip().startswith("with _mc:") or "with _mc" in lines[j]:
                start_del = j
                break
        indent = len(lines[i]) - len(lines[i].lstrip())
        for k in range(i+3, min(i+15, len(lines))):
            if lines[k].strip() and (len(lines[k]) - len(lines[k].lstrip())) <= indent - 4:
                end_del = k
                break
        break

if start_del and end_del:
    del lines[start_del:end_del]
    fixes += 1
    print(f"수정1 완료: {start_del+1}~{end_del}라인 제거")
else:
    new_lines = []
    skip = False
    for i, line in enumerate(lines):
        if 'popup_model_sel_14' in line:
            skip = True
            while new_lines and ('with _mc:' in new_lines[-1] or 'margin-top:4px' in new_lines[-1] or (new_lines[-1].strip().startswith('with _mc') )):
                new_lines.pop()
        elif skip:
            if line.strip() and not line.strip().startswith('_sel =') and not line.strip().startswith('index=') and not line.strip().startswith('if st.session') and not line.strip().startswith(')') and not line.strip().startswith('key=') and not line.strip().startswith('"모델"') and not 'label_visibility' in line and not 'popup_model_sel_14' in line:
                skip = False
                new_lines.append(line)
        else:
            new_lines.append(line)
    lines = new_lines
    fixes += 1
    print("수정1 완료: popup_model_sel_14 블록 제거")

with open("sage_popups_v17_1_18.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

with open("sage_popups_v17_1_18.py", "r", encoding="utf-8") as f:
    code = f.read()

# 수정2: st.spinner("● ● ●") 위에 사용자 메시지 즉시 표시 추가
old2 = '''            # 시스템 프롬프트 (초경량)
            _sys = "너는 현자의 거울 스튜디오의 어시스턴트다. 묻는 말에 정확하고 짧게 답하라."'''

new2 = '''            # 사용자 메시지 즉시 표시
            with _chat_box:
                with st.chat_message("user"):
                    st.markdown(_prompt)

            # 시스템 프롬프트 (초경량)
            _sys = "너는 현자의 거울 스튜디오의 어시스턴트다. 묻는 말에 정확하고 짧게 답하라."'''

if old2 in code:
    code = code.replace(old2, new2, 1)
    fixes += 1
    print("수정2 완료: 사용자 메시지 즉시 표시")
else:
    print("수정2 실패")

# 수정3: 응답 저장 후 응답 즉시 표시
old3 = "            _save_chat_history(st.session_state.popup_history)\n            st.session_state[\"input_key\"] = st.session_state.get(\"input_key\", 0) + 1"
new3 = '''            _save_chat_history(st.session_state.popup_history)
            st.session_state["input_key"] = st.session_state.get("input_key", 0) + 1
            # 응답 즉시 표시
            with _chat_box:
                with st.chat_message("assistant"):
                    st.markdown(_resp)
                    if st.button("□ 복사", key=f"copy_new_{len(st.session_state.popup_history)}", help="복사"):
                        st.code(_resp, language="markdown")
            # JS로 입력창 초기화
            st.components.v1.html("<script>setTimeout(()=>{var ta=parent.document.querySelectorAll('textarea');ta.forEach(t=>{if(t.placeholder&&t.placeholder.includes('현자')){t.value='';t.dispatchEvent(new Event('input',{bubbles:true}));}});},200);</script>", height=0)'''

if old3 in code:
    code = code.replace(old3, new3, 1)
    fixes += 1
    print("수정3 완료: 응답 즉시 표시 + 입력창 초기화")
else:
    print("수정3 실패")

with open("sage_popups_v17_1_18.py", "w", encoding="utf-8") as f:
    f.write(code)

print(f"\\n총 {fixes}개 수정 완료")
