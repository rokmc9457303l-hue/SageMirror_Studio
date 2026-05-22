import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import subprocess

target_file = r'C:\SageMirror_Production\app_v15_9_1.py'

with open(target_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"[로드] 총 줄 수: {len(lines)}")

# =============================================================================
# 핵심 전략: st.button("🔍") + 앞의 카드 HTML을 합쳐서
#            st.popover() 하나로 교체
#            → 카드처럼 보이는 팝오버 버튼 하나만 남김
# =============================================================================

content = ''.join(lines)

# ─── OBS 블록 교체 (4091~4097줄 범위)
# 현재: 카드 markdown + if st.button("🔍") + popup_obsidian_history()
# → 교체: 카드 markdown 유지 + st.popover로 🔍 아이콘 버튼 변환

old_obs_btn = (
    '            if st.button(\n'
    '                "🔍",\n'
    '                key="top_obs_history_btn",\n'
    '                use_container_width=True,\n'
    '                help="클릭: 옵시디언 RAG 백업 파일 목록 보기"\n'
    '            ):\n'
    '                popup_obsidian_history()'
)

new_obs_btn = (
    '            with st.popover("🔗 연동 내역", use_container_width=True):\n'
    '                st.caption("📂 옵시디언 RAG 최근 연동 파일")\n'
    '                try:\n'
    '                    import os as _os\n'
    '                    obs_path = st.session_state.get("obsidian_path", "")\n'
    '                    if obs_path and _os.path.exists(obs_path):\n'
    '                        _files = []\n'
    '                        for _root, _dirs, _fnames in _os.walk(obs_path):\n'
    '                            for _fn in _fnames:\n'
    '                                if _fn.endswith(".md"):\n'
    '                                    _fp = _os.path.join(_root, _fn)\n'
    '                                    _files.append((_os.path.getmtime(_fp), _fn, _fp))\n'
    '                        _files.sort(reverse=True)\n'
    '                        for _mtime, _fname, _fpath in _files[:10]:\n'
    '                            from datetime import datetime as _dt\n'
    '                            _ts = _dt.fromtimestamp(_mtime).strftime("%m/%d %H:%M")\n'
    '                            st.markdown(f"- `{_ts}` **{_fname}**")\n'
    '                    else:\n'
    '                        st.info("옵시디언 경로를 사이드바에서 설정해 주세요.")\n'
    '                except Exception as _e:\n'
    '                    st.error(f"목록 오류: {_e}")'
)

obs_count = content.count(old_obs_btn)
print(f"[OBS] 교체 대상 발견: {obs_count}개")
if obs_count > 0:
    content = content.replace(old_obs_btn, new_obs_btn)
    print("[OBS] popover 교체 완료!")
else:
    # 빈 줄 포함 버전 시도
    idx = content.find('"top_obs_history_btn"')
    if idx >= 0:
        btn_start = content.rfind('\n            if st.button(', 0, idx)
        btn_end = content.find('popup_obsidian_history()', idx) + len('popup_obsidian_history()')
        old_block = content[btn_start+1:btn_end]
        print(f"[OBS] 대안 발견 ({len(old_block)}자): {repr(old_block[:80])}")
        content = content[:btn_start+1] + new_obs_btn + content[btn_end:]
        print("[OBS] popover 교체 완료 (대안)!")

# ─── GIT 블록 교체
old_git_btn = (
    '            if st.button(\n'
    '                "🔍",\n'
    '                key="top_git_history_btn",\n'
    '                use_container_width=True,\n'
    '                help="클릭: GitHub 커밋 히스토리 보기"\n'
    '            ):\n'
    '                popup_git_history()'
)

new_git_btn = (
    '            with st.popover("🔗 연동 내역", use_container_width=True):\n'
    '                st.caption("🐙 GitHub 최근 커밋 내역")\n'
    '                try:\n'
    '                    from git import Repo as _Repo, InvalidGitRepositoryError\n'
    '                    import os as _os\n'
    '                    git_path = st.session_state.get("github_local_path", "")\n'
    '                    if git_path and _os.path.exists(git_path):\n'
    '                        _repo = _Repo(git_path)\n'
    '                        _commits = list(_repo.iter_commits(max_count=10))\n'
    '                        for _c in _commits:\n'
    '                            from datetime import datetime as _dt\n'
    '                            _ts = _dt.fromtimestamp(_c.committed_date).strftime("%m/%d %H:%M")\n'
    '                            _msg = _c.message.strip()[:40]\n'
    '                            st.markdown(f"- `{_ts}` {_msg}")\n'
    '                    else:\n'
    '                        st.info("GitHub 로컬 경로를 사이드바에서 설정해 주세요.")\n'
    '                except Exception as _e:\n'
    '                    st.error(f"히스토리 오류: {_e}")'
)

git_count = content.count(old_git_btn)
print(f"[GIT] 교체 대상 발견: {git_count}개")
if git_count > 0:
    content = content.replace(old_git_btn, new_git_btn)
    print("[GIT] popover 교체 완료!")
else:
    idx = content.find('"top_git_history_btn"')
    if idx >= 0:
        btn_start = content.rfind('\n            if st.button(', 0, idx)
        btn_end = content.find('popup_git_history()', idx) + len('popup_git_history()')
        old_block = content[btn_start+1:btn_end]
        print(f"[GIT] 대안 발견 ({len(old_block)}자): {repr(old_block[:80])}")
        content = content[:btn_start+1] + new_git_btn + content[btn_end:]
        print("[GIT] popover 교체 완료 (대안)!")

# =============================================================================
# popover 버튼 CSS 추가 — 기존 카드 스타일과 어울리는 미니 팝오버 버튼
# =============================================================================
popover_css = '''
    /* ═══ 시스템 연동 팝오버 버튼 스타일 ═══ */
    [data-testid="stPopover"] > div > button {
        background: rgba(212,175,106,0.12) !important;
        border: 1px solid rgba(212,175,106,0.35) !important;
        border-radius: 6px !important;
        color: #d4af6a !important;
        font-size: 0.75em !important;
        font-weight: 600 !important;
        padding: 3px 10px !important;
        margin-top: -2px !important;
        letter-spacing: 0.03em !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stPopover"] > div > button:hover {
        background: rgba(212,175,106,0.25) !important;
        border-color: rgba(212,175,106,0.7) !important;
        box-shadow: 0 2px 8px rgba(212,175,106,0.2) !important;
    }
'''

# 기존 sage-pipe-label CSS 블록 다음에 삽입
marker = '    /* ═══ 글래스모피즘 컨트롤 박스'
if marker in content:
    idx = content.index(marker)
    content = content[:idx] + popover_css + '\n' + content[idx:]
    print("[CSS] popover 버튼 스타일 추가 완료!")
else:
    print("[CSS] 삽입 위치 미발견 — 다른 위치 시도")
    marker2 = '    .glass-control-box {'
    if marker2 in content:
        idx = content.index(marker2)
        content = content[:idx] + popover_css + '\n' + content[idx:]
        print("[CSS] popover 버튼 스타일 추가 완료 (대안)!")

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
print(f"st.button 🔍 잔존: {c2.count('key=\"top_obs_history_btn\"') + c2.count('key=\"top_git_history_btn\"')}개 (목표: 0)")
print(f"st.popover 연동내역: {c2.count('연동 내역')}개 (목표: 2+)")
print(f"popover CSS: {c2.count('stPopover')}개")
