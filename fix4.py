import sys
sys.stdout.reconfigure(encoding="utf-8")
fp = r"C:\SageMirror_Production\sage_popups.py"
with open(fp, "r", encoding="utf-8") as f:
    lines = f.readlines()
s = 1350
e = 1375
ra_s = 1377
ra_e = None
for i in range(ra_s, min(ra_s+15, len(lines))):
    if lines[i].strip() == "" and ra_e is None and i > ra_s+3:
        ra_e = i
        break
if ra_e is None:
    ra_e = ra_s + 10
nb = []
nb.append('                # A/B 모드 시스템 컨텍스트 분기\n')
nb.append('                _current_mode = st.session_state.get("popup_gemma_mode","A")\n')
nb.append('                if _current_mode == "A":\n')
nb.append('                    sys_ctx = SAGE_PERSONA\n')
nb.append('                else:\n')
for line in lines[s+1:e+1]:
    nb.append("    " + line)
nb.append("\n")
nb.append('                    # Recent Activity (B모드만)\n')
for line in lines[ra_s+1:ra_e]:
    nb.append("    " + line)
result = lines[:s] + nb + lines[ra_e:]
with open(fp, "w", encoding="utf-8") as f:
    f.writelines(result)
print(f"SUCCESS: {s+1}~{ra_e}라인 수정완료")
