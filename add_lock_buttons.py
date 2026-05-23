# -*- coding: utf-8 -*-
"""현자의 거울 — Lock 버튼 위치 교정 패치 스크립트 v2"""
import os, re, shutil
from datetime import datetime

files = sorted([f for f in os.listdir('.') if re.match(r'app_v15_9_2\d\.py', f)
                and 'backup' not in f and 'stable' not in f], reverse=True)
if not files:
    files = sorted([f for f in os.listdir('.') if f.startswith('app_v15_9_') and f.endswith('.py')
                    and 'backup' not in f], reverse=True)
if not files:
    print("파일 없음"); input("Enter..."); exit()

TARGET = files[0]
num = int(re.search(r'app_v15_9_(\d+)', TARGET).group(1))
OUTPUT = f"app_v15_9_{num+1}.py"
print(f"대상: {TARGET} → 출력: {OUTPUT}")

os.makedirs("00_History", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M")
shutil.copy(TARGET, f"00_History/{TARGET.replace('.py','')}_backup_{ts}.py")
print("백업 완료")

with open(TARGET, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 기존 잘못된 Lock 버튼 제거
pattern = r'\n    # ── 🔒 Part 1 최종본 Lock[^\n]*(?:\n[^\n]*){11}\n'
removed = len(re.findall(pattern, content))
content = re.sub(pattern, '\n', content)
print(f"기존 버튼 {removed}개 제거")

# Lock 함수 추가
LOCK_FUNCS = """
# ════════════════════════════════════════════
# Lock & 수정본 생성 시스템
# ════════════════════════════════════════════
def lock_and_push_final_version(part_num, display_name, keys_to_backup):
    try:
        obs_path = st.session_state.get("path_obsidian", "")
        if not obs_path:
            st.error("옵시디언 경로 미설정"); return
        locks_dir = os.path.join(obs_path, "Studio", "Final_Locks")
        os.makedirs(locks_dir, exist_ok=True)
        fpath = os.path.join(locks_dir, f"Part{part_num}_Final_LOCK.md")
        from datetime import datetime as _dt
        lines = [f"# Part {part_num} - {display_name} LOCK", f"> {_dt.now().strftime('%Y-%m-%d %H:%M')}\\n"]
        for k in keys_to_backup:
            v = st.session_state.get(k, "")
            if v: lines.append(f"## {k}\\n{v}")
        with open(fpath, "w", encoding="utf-8") as f: f.write("\\n\\n".join(lines))
        try:
            import stat as _s; os.chmod(fpath, _s.S_IRUSR | _s.S_IRGRP | _s.S_IROTH)
        except: pass
        st.success(f"Part {part_num} Lock 완료!")
        ok, msg = auto_git_push(f"LOCK: Part{part_num}")
        st.success("GitHub Push 완료!") if ok else st.warning(f"Push 실패: {msg}")
        save_workspace_state()
    except Exception as e:
        st.error(f"Lock 오류: {e}")

def create_revision_version(part_num, display_name, keys_to_backup):
    try:
        obs_path = st.session_state.get("path_obsidian", "")
        locks_dir = os.path.join(obs_path, "Studio", "Final_Locks")
        lock_file = os.path.join(locks_dir, f"Part{part_num}_Final_LOCK.md")
        if not os.path.exists(lock_file):
            st.error(f"먼저 Part {part_num} Lock을 완료하세요."); return
        rev = 1
        while os.path.exists(os.path.join(locks_dir, f"Part{part_num}_REV{rev}.md")):
            rev += 1
        rpath = os.path.join(locks_dir, f"Part{part_num}_REV{rev}.md")
        from datetime import datetime as _dt
        with open(lock_file, "r", encoding="utf-8") as f: orig = f.read()
        with open(rpath, "w", encoding="utf-8") as f:
            f.write(f"# REV{rev}\\n> {_dt.now().strftime('%Y-%m-%d %H:%M')}\\n\\n---\\n\\n" + orig)
        st.success(f"수정본 생성: Part{part_num}_REV{rev}.md")
    except Exception as e:
        st.error(f"수정본 오류: {e}")

"""

if 'def lock_and_push_final_version' not in content:
    content = content.replace('def render_part1():', LOCK_FUNCS + 'def render_part1():', 1)
    print("Lock 함수 추가")

# Step 2 앞에 버튼 삽입
BTN = """
    # 🔒 Part 1 Lock 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    _lc1, _rc1 = st.columns(2)
    with _lc1:
        if st.button("🔒 Part 1 최종본 Lock & GitHub Push", key="p1_lock_btn", use_container_width=True):
            lock_and_push_final_version(1, "벤치마킹 & 자료조사", ["p1_research_result","p1_planning_result"])
    with _rc1:
        if st.button("🔓 Part 1 수정본 생성", key="p1_rev_btn", use_container_width=True):
            create_revision_version(1, "벤치마킹 & 자료조사", ["p1_research_result","p1_planning_result"])

"""

MARKER = '    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진")'
if MARKER in content:
    content = content.replace(MARKER, BTN + MARKER, 1)
    print("Part 1 Lock 버튼 삽입 완료!")
else:
    print("삽입 위치 못찾음 - 파일 구조 다를 수 있음")

content = re.sub(r'Master App v15\.9\.\d+', f'Master App v15.9.{num+1}', content)
content = re.sub(r'\*\*v15\.9\.\d+\*\*', f'**v15.9.{num+1}**', content)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(content)

import py_compile
try:
    py_compile.compile(OUTPUT, doraise=True)
    print(f"\n✅ {OUTPUT} 완성! 문법 OK!")
    print("RUN_APP.bat 에서 파일명 바꾸고 실행하세요!")
except py_compile.PyCompileError as e:
    print(f"❌ 오류: {e}")

input("\nEnter 종료...")
