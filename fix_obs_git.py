import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import subprocess

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[로드] 줄 수: {len(content.splitlines())}")

# =============================================================================
# OBS_RAG_CLICK 버튼 교체 — 빈 줄 포함 실제 패턴으로
# 연동 OK: 버튼 숨기고 카드에 🔍 아이콘 버튼만 우측에 붙임
# 연동 X: 빨간 🔴 표시
# =============================================================================

# 현재 코드에서 실제 패턴 찾기 (빈 줄 포함)
obs_start = content.find('"OBS_RAG_CLICK"')
if obs_start < 0:
    print("OBS_RAG_CLICK 못찾음")
else:
    # 버튼 블록 전체 범위: if st.button( 부터 popup_obsidian_history() 까지
    btn_start = content.rfind('if st.button(', 0, obs_start)
    popup_end_marker = 'popup_obsidian_history()'
    popup_end = content.find(popup_end_marker, obs_start) + len(popup_end_marker)
    
    old_obs_btn_block = content[btn_start:popup_end]
    print(f"[OBS] 교체 대상 ({len(old_obs_btn_block)}자):\n{repr(old_obs_btn_block[:100])}")
    
    new_obs_btn_block = '''if st.button(
                "🔍",
                key="top_obs_history_btn",
                use_container_width=True,
                help="클릭: 옵시디언 RAG 백업 파일 목록 보기"
            ):
                popup_obsidian_history()'''
    
    content = content[:btn_start] + new_obs_btn_block + content[popup_end:]
    print("[OBS] 교체 완료!")

# =============================================================================
# GIT_CLICK 버튼 교체
# =============================================================================
git_start = content.find('"GIT_CLICK"')
if git_start < 0:
    print("GIT_CLICK 못찾음")
else:
    btn_start = content.rfind('if st.button(', 0, git_start)
    popup_end_marker = 'popup_git_history()'
    popup_end = content.find(popup_end_marker, git_start) + len(popup_end_marker)
    
    old_git_btn_block = content[btn_start:popup_end]
    print(f"[GIT] 교체 대상 ({len(old_git_btn_block)}자):\n{repr(old_git_btn_block[:100])}")
    
    new_git_btn_block = '''if st.button(
                "🔍",
                key="top_git_history_btn",
                use_container_width=True,
                help="클릭: GitHub 커밋 히스토리 보기"
            ):
                popup_git_history()'''
    
    content = content[:btn_start] + new_git_btn_block + content[popup_end:]
    print("[GIT] 교체 완료!")

# =============================================================================
# 연동 미설정 시 빨간 동그라미 추가 — obs_ok=False 카드에 🔴 추가
# =============================================================================
old_obs_warn = '\'<span class="stat-label"><span style="color:#fbbf24;">⬤</span>  옵시디언 확인필요</span>\''
new_obs_warn = '\'<span class="stat-label"><span style="color:#fbbf24;">⬤</span>  옵시디언 확인필요 <span style="color:#ef4444;font-size:0.8em;">🔴 미연결</span></span>\''

obs_warn_count = content.count(old_obs_warn)
content = content.replace(old_obs_warn, new_obs_warn)
print(f"[OBS미연결] 빨간 표시 추가: {obs_warn_count}개")

old_git_err = '\'<span class="stat-label"><span style="color:#f87171;">⬤</span>  Git 미연동</span>\''
new_git_err = '\'<span class="stat-label"><span style="color:#f87171;">⬤</span>  Git 미연동 <span style="color:#ef4444;font-size:0.8em;">🔴 미연결</span></span>\''

git_err_count = content.count(old_git_err)
content = content.replace(old_git_err, new_git_err)
print(f"[GIT미연결] 빨간 표시 추가: {git_err_count}개")

# =============================================================================
# SYNC_CLICK 버튼: 텍스트만 더 명확하게 변경 (기능 로직 유지)
# =============================================================================
old_sync = '"SYNC_CLICK"'
new_sync = '"⚡ 전체 즉시 동기화"'
sync_count = content.count(old_sync)
content = content.replace(old_sync, new_sync)
print(f"[SYNC] 버튼 텍스트 변경: {sync_count}개")

# =============================================================================
# 저장 및 컴파일
# =============================================================================
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n[저장] 줄 수: {len(content.splitlines())}")

result = subprocess.run(
    ['C:\\Python314\\python.exe', '-m', 'py_compile', target_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0:
    print("COMPILE: ✅ OK!")
else:
    print(f"COMPILE ERROR:\n{result.stderr}")

print("\n=== 최종 확인 ===")
with open(target_file, 'r', encoding='utf-8') as f:
    c2 = f.read()
print(f"OBS_RAG_CLICK 잔존: {c2.count('OBS_RAG_CLICK')}개 (목표: 0)")
print(f"GIT_CLICK 잔존: {c2.count('GIT_CLICK')}개 (목표: 0)")
print(f"SYNC_CLICK 잔존: {c2.count('SYNC_CLICK')}개 (목표: 0)")
print(f"🔴 미연결 표시: {c2.count('🔴 미연결')}개")
print(f"glass-control-box HTML: {c2.count('class=\"glass-control-box\"')}개")
