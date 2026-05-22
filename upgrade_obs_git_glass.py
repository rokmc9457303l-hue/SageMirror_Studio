import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import subprocess

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[로드] 총 줄 수: {len(content.splitlines())}")

# =============================================================================
# 작업 A: OBS_RAG_CLICK / GIT_CLICK 버튼 제거 및 팝오버 스타일로 교체
# - 버튼 자체를 삭제하고, 카드를 클릭 시 바로 아래 팝업이 뜨는 구조 유지
# - 단, 버튼 라벨만 숨기고 팝업 기능은 유지 (로직 보존)
# - 카드를 클릭 가능한 미니 버튼으로 통합하여 버튼칸이 사라지게 함
# =============================================================================

# --- OBS 버튼: 기존 버튼 코드 → 카드에 팝업 연동된 작은 아이콘 버튼으로 교체
old_obs_block = '''    with c_obs:
        if obs_ok:
            st.markdown(
                f\'<div class="sage-stat-card ok clickable-card-bg">\\'
                f\'<span class="stat-label"><span style="color:#34d399;">⬤</span>  옵시디언 RAG</span>\\'
                f\'<span class="stat-sub">Vault: {obs_name}</span>\\'
                f\'</div>\',
                unsafe_allow_html=True
            )
            if st.button(
                "OBS_RAG_CLICK",
                key="top_obs_history_btn",
                use_container_width=True,
                help="클릭 시 옵시디언 RAG 백업 파일 목록을 팝업으로 조회합니다."
            ):
                popup_obsidian_history()
        else:
            st.markdown(
                \'<div class="sage-stat-card warn">\\'
                \'<span class="stat-label"><span style="color:#fbbf24;">⬤</span>  옵시디언 확인필요</span>\\'
                \'<span class="stat-sub">경로 미설정</span>\\'
                \'</div>\',
                unsafe_allow_html=True
            )'''

new_obs_block = '''    with c_obs:
        if obs_ok:
            with st.container():
                col_card, col_btn = st.columns([5, 1])
                with col_card:
                    st.markdown(
                        f\'<div class="sage-stat-card ok" style="border-radius:8px 0 0 8px;">\\'
                        f\'<span class="stat-label"><span style="color:#34d399;">⬤</span>  옵시디언 RAG</span>\\'
                        f\'<span class="stat-sub">Vault: {obs_name}</span>\\'
                        f\'</div>\',
                        unsafe_allow_html=True
                    )
                with col_btn:
                    st.markdown(\'<div style="height:60px;display:flex;align-items:center;justify-content:center;">\', unsafe_allow_html=True)
                    if st.button("🔍", key="top_obs_history_btn", help="옵시디언 RAG 백업 파일 목록 보기", use_container_width=True):
                        popup_obsidian_history()
                    st.markdown(\'</div>\', unsafe_allow_html=True)
        else:
            st.markdown(
                \'<div class="sage-stat-card warn">\\'
                \'<span class="stat-label"><span style="color:#fbbf24;">⬤</span>  옵시디언 미연결 🔴</span>\\'
                \'<span class="stat-sub">경로 미설정</span>\\'
                \'</div>\',
                unsafe_allow_html=True
            )'''

obs_count = content.count(old_obs_block)
print(f"[OBS] 구버전 블록 발견: {obs_count}개")
if obs_count > 0:
    content = content.replace(old_obs_block, new_obs_block)
    print("[OBS] 교체 완료!")

# --- GIT 버튼: 같은 방식으로 교체
old_git_block = '''    with c_git:
        if git_ok:
            st.markdown(
                f\'<div class="sage-stat-card ok clickable-card-bg">\\'
                f\'<span class="stat-label"><span style="color:#34d399;">⬤</span>  GitHub 연동</span>\\'
                f\'<span class="stat-sub">Repo: {repo_name}</span>\\'
                f\'</div>\',
                unsafe_allow_html=True
            )
            if st.button(
                "GIT_CLICK",
                key="top_git_history_btn",
                use_container_width=True,
                help="클릭 시 GitHub 로컬 커밋 및 동기화 히스토리를 팝업으로 조회합니다."
            ):
                popup_git_history()
        else:
            st.markdown(
                \'<div class="sage-stat-card err">\\'
                \'<span class="stat-label"><span style="color:#f87171;">⬤</span>  Git 미연동</span>\\'
                \'<span class="stat-sub">설정 변경 필요</span>\\'
                \'</div>\',
                unsafe_allow_html=True
            )'''

new_git_block = '''    with c_git:
        if git_ok:
            with st.container():
                col_card, col_btn = st.columns([5, 1])
                with col_card:
                    st.markdown(
                        f\'<div class="sage-stat-card ok" style="border-radius:8px 0 0 8px;">\\'
                        f\'<span class="stat-label"><span style="color:#34d399;">⬤</span>  GitHub 연동</span>\\'
                        f\'<span class="stat-sub">Repo: {repo_name}</span>\\'
                        f\'</div>\',
                        unsafe_allow_html=True
                    )
                with col_btn:
                    st.markdown(\'<div style="height:60px;display:flex;align-items:center;justify-content:center;">\', unsafe_allow_html=True)
                    if st.button("🔍", key="top_git_history_btn", help="GitHub 커밋 히스토리 보기", use_container_width=True):
                        popup_git_history()
                    st.markdown(\'</div>\', unsafe_allow_html=True)
        else:
            st.markdown(
                \'<div class="sage-stat-card err">\\'
                \'<span class="stat-label"><span style="color:#f87171;">⬤</span>  Git 미연동 🔴</span>\\'
                \'<span class="stat-sub">설정 변경 필요</span>\\'
                \'</div>\',
                unsafe_allow_html=True
            )'''

git_count = content.count(old_git_block)
print(f"[GIT] 구버전 블록 발견: {git_count}개")
if git_count > 0:
    content = content.replace(old_git_block, new_git_block)
    print("[GIT] 교체 완료!")

# =============================================================================
# 작업 B: 파트 헤더 우측 c_control 에 glass-control-box div 래핑 추가
# - 각 파트의 with c_control: 블록 내부에 div 감싸기
# 패턴: st.markdown('<div id="header-control-box-anchor"></div>'...)
# → 앞뒤에 glass-control-box div 추가
# =============================================================================
old_anchor = "st.markdown('<div id=\"header-control-box-anchor\"></div>', unsafe_allow_html=True)"
new_anchor = "st.markdown('<div class=\"glass-control-box\"><div id=\"header-control-box-anchor\"></div>', unsafe_allow_html=True)"

anchor_count = content.count(old_anchor)
print(f"\n[GLASS] anchor 패턴 발견: {anchor_count}개")
if anchor_count > 0:
    content = content.replace(old_anchor, new_anchor)
    print(f"[GLASS] {anchor_count}개 glass-control-box 시작 태그 추가!")

# glass-control-box 닫기: 각 파트의 with c_pop_col 블록 끝 </div> 다음에 추가
# 패턴: st.markdown('</div>', unsafe_allow_html=True) 다음에 is_locked 변수 정의
old_pop_end = "            st.markdown('</div>', unsafe_allow_html=True)\n\n    is_locked"
new_pop_end = "            st.markdown('</div>', unsafe_allow_html=True)\n        st.markdown('</div>', unsafe_allow_html=True)  # glass-control-box 닫기\n\n    is_locked"

pop_count = content.count(old_pop_end)
print(f"[GLASS] 닫기 패턴(is_locked) 발견: {pop_count}개")
if pop_count > 0:
    content = content.replace(old_pop_end, new_pop_end)
    print(f"[GLASS] {pop_count}개 glass-control-box 닫기 태그 추가!")
else:
    # 파트34/파트5_img 등 다른 패턴 시도
    alt_end = "            st.markdown('</div>', unsafe_allow_html=True)\r\n\r\n    is_locked"
    alt_count = content.count(alt_end)
    print(f"[GLASS] CRLF 패턴 발견: {alt_count}개")

# =============================================================================
# 저장 및 컴파일 검증
# =============================================================================
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n[저장] 완료! 줄 수: {len(content.splitlines())}")

# 컴파일
result = subprocess.run(
    ['C:\\Python314\\python.exe', '-m', 'py_compile', target_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0:
    print("COMPILE: ✅ OK!")
else:
    print(f"COMPILE ERROR:\n{result.stderr[:500]}")
