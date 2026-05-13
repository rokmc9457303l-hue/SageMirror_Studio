# -*- coding: utf-8 -*-
"""
🪞 현자의 거울 스튜디오 (Sage's Mirror Studio) — Master App v7.4
================================================================
[v7.4 업데이트 사항: 2026-05-11 17:10]
- UI 구조 개편: 중간 좌측(젬마 프로토콜), 우측(Tavily 채널 탐색) 분리
- 최상단 우측 프롬프트를 '마스터 규칙서(Master Research Prompt)'로 기본 탑재
- 원본 파일(app_v7.3) 훼손 없이 독립 복사본으로 안전망 유지
"""

import streamlit as st
import os
import re
import stat
from pathlib import Path
from datetime import datetime
import pandas as pd

try:
    from git import Repo
    GIT_AVAILABLE = True
except Exception:
    GIT_AVAILABLE = False

# ── 내부 모듈 ──
from sage_config import (
    APP_TITLE, MASTER_PW_DEFAULT, PART_PINS, OLLAMA_MODEL,
    DEFAULT_OBSIDIAN_RULES,
    SAGE_PERSONA, GLOBAL_CSS,
)
from sage_engine import (
    safe_makedirs, save_markdown, save_json, save_csv, save_txt,
    call_gemma, check_ollama_status,
)
from sage_popups import (
    popup_edit_obsidian, popup_edit_prompt, popup_assistant,
)

# =====================================================================
# 1. 페이지 설정
# =====================================================================
st.set_page_config(
    page_title="Sage's Mirror Studio v7.4",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# =====================================================================
# 2. 세션 상태 초기화 (v7.4 하드코딩 적용)
# =====================================================================
MASTER_RESEARCH_PROMPT = """[자료 조사 파트 전용 마스터 규칙서: 절대 가이드]
1. 타겟 시청자 (Target Audience)
   - 주요 타겟은 40대~70대(4070) 중장년층입니다.
   - 단순한 위로가 아닌, 성경적 지혜와 철학적 통찰이 결합된 '무거운 공감'을 원합니다.

2. 화자 설정 (Persona)
   - 화자는 산전수전을 다 겪고 깨달음을 얻은 '60대 현자(Sage)'입니다.
   - 시청자를 지칭할 때는 반드시 '@Protagonist' 라는 명칭을 사용하여 존중과 애정을 담습니다.

[대본 핵심 가이드 및 영감 도출 지시서]
1. 🎯 베스트 키워드: 유튜브 알고리즘 & 감성 타격 키워드 3개 도출 (형태: `[[핵심키워드1]]`)
2. 📖 오늘의 명언: 주제를 관통하는 철학자/성경 명언 1개 제시
3. 🔥 핵심 전달 메시지: 이 영상이 끝났을 때 가슴에 남아야 할 단 하나의 위로/교훈 (2문장 이내)

[통합 기획 지시서 작성 원칙]
1. 영상의 뼈대 (구조): 도입(공감) - 전개(해석) - 절정(명언/해답) - 결말(격려)
2. 시각적 스타일: 렘브란트풍의 묵직한 명암(Chiaroscuro), 어둠 속 한 줄기 빛
"""

def init_session_state():
    defaults = {
        "logged_in": False,
        "path_obsidian": r"C:\SageMirror_Production\00_Obsidian_Archive", 
        "path_assets": r"C:\SageMirror_Production\00_Assets",
        "path_memo": r"C:\SageMirror_Production\00_Memo",
        "github_token": "",
        "github_repo_url": "https://github.com/rokmc9457303l-hue/SageMirror_Studio.git",
        "github_local_path": r"C:\SageMirror_Production",
        "tavily_api_key": "",
        "obsidian_rules": DEFAULT_OBSIDIAN_RULES,
        "base_prompt_rules": MASTER_RESEARCH_PROMPT,
        "obsidian_history": [],
        "prompt_history": [],
        "popup_history": [],
        "popup_search_history": [],
        "unlock_part1": False,
        "unlock_part2": False,
        "p1_gemma_protocol": "",
        "p1_channel_search_results": [],
        "p1_channel_url": "",
        "p1_extra_notes": "",
        "p1_region": "국내+국외 모두",
        "p1_topics": [],
        "p1_selected_topic": None,
        "p1_saved": False,
        "p1_save_ts": None,
        "p1_saved_paths": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
            
    # v7.4 강제 업데이트
    if st.session_state.base_prompt_rules != MASTER_RESEARCH_PROMPT and not st.session_state.get("p1_saved"):
        st.session_state.base_prompt_rules = MASTER_RESEARCH_PROMPT

init_session_state()

# =====================================================================
# [보안 로직] 파일 읽기 전용 잠금 (덮어쓰기 방지)
# =====================================================================
def lock_file_readonly(filepath):
    try:
        if os.path.exists(filepath):
            os.chmod(filepath, stat.S_IREAD)
            return True
    except Exception as e:
        st.warning(f"파일 락(Lock) 실패: {e}")
    return False

# =====================================================================
# [자동화 로직] GitHub 자동 푸시
# =====================================================================
def auto_git_push(commit_message: str):
    if not GIT_AVAILABLE: return False, "GitPython 미설치"
    try:
        rp = Path(st.session_state.github_local_path)
        rp.mkdir(parents=True, exist_ok=True)
        if not (rp / ".git").exists(): Repo.init(rp)
        repo = Repo(rp)
        repo.git.add(A=True)
        
        if repo.is_dirty(untracked_files=True):
            repo.index.commit(f"{commit_message} (Auto Backup: {datetime.now().strftime('%Y%m%d_%H%M%S')})")
        
        auth = st.session_state.github_repo_url.replace("https://", f"https://{st.session_state.github_token}@") if st.session_state.github_token else st.session_state.github_repo_url
        if "origin" in [r.name for r in repo.remotes]: repo.remotes.origin.set_url(auth)
        else: repo.create_remote("origin", auth)
            
        repo.remotes.origin.push(refspec="HEAD:refs/heads/main", force=True)
        return True, "자동 백업 푸시 성공"
    except Exception as e:
        return False, f"푸시 실패: {e}"

# =====================================================================
# 3. 로그인
# =====================================================================
def render_login():
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE} <span style='color:#10B981;font-size:0.5em;'>v7.4 Research UI Edition</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888'>성경 · 철학 · 에세이가 융합된 다큐멘터리 자동화 스튜디오 (System Locked & GitHub Sync)</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'><span class='model-badge'>🧠 Active Model: {OLLAMA_MODEL}</span></p>", unsafe_allow_html=True)
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### 🔐 접근 제어 (Master Lock)")
        pw = st.text_input("마스터 비밀번호", type="password", key="master_pw_input")
        if st.button("로그인", type="primary", use_container_width=True):
            if pw == MASTER_PW_DEFAULT:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("비밀번호 불일치.")
        st.caption(f"기본: `{MASTER_PW_DEFAULT}`")

if not st.session_state.logged_in:
    render_login()
    st.stop()

# =====================================================================
# 4. 사이드바
# =====================================================================
with st.sidebar:
    st.markdown(f"### {APP_TITLE} **v7.4**")
    status = check_ollama_status()
    if status["server"] and status["model"]: st.success(f"✅ Ollama | {OLLAMA_MODEL}")
    elif status["server"]: st.warning(f"⚠️ 서버 ON / 모델 미확인")
    else: st.error(f"❌ Ollama 미연결")

    st.divider()
    st.info(f"📂 **옵시디언 아카이브 (읽기전용 보호 중)**\n{st.session_state.path_obsidian}")
    st.info(f"🚀 **GitHub 연동 중**\n{st.session_state.github_repo_url.split('/')[-1]}")

    with st.expander("⚙️ 설정 변경", expanded=False):
        st.session_state.path_obsidian = st.text_input("옵시디언 볼트", value=st.session_state.path_obsidian)
        st.session_state.github_repo_url = st.text_input("Repo URL", value=st.session_state.github_repo_url)
        st.session_state.github_token = st.text_input("GitHub PAT (공란 권장)", value=st.session_state.github_token, type="password")
        st.session_state.tavily_api_key = st.text_input("Tavily API Key", value=st.session_state.tavily_api_key, type="password")
        if st.button("수동 동기화"):
            success, msg = auto_git_push("Manual Sync")
            if success: st.success(msg)
            else: st.error(msg)

    st.divider()
    st.markdown("### 📚 파트 메뉴")
    part = st.radio("이동할 파트", ["Part 1: Librarian", "Part 2: Alchemist", "Part 3-4: Architect+Writer", "Part 5: Image Consistency", "Part 6: Opal Dispatcher", "Part 7: CapCut Bridge", "Part 8: Final Assembly"], index=0, key="part_menu")
    st.divider()
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# =====================================================================
# 5. 상단 패널
# =====================================================================
def render_top_panel():
    with st.expander("📋 상단: 옵시디언 규칙서 및 마스터 프롬프트", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=220, key="top_ob_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="ob_btn"): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🎯 자료 조사 전용 마스터 프롬프트</div>', unsafe_allow_html=True)
            st.text_area("기본 프롬프트", value=st.session_state.base_prompt_rules, height=220, key="top_pr_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="pr_btn"): popup_edit_prompt()
            st.markdown('</div>', unsafe_allow_html=True)

def render_common_top():
    _l, _r = st.columns([7, 2])
    with _r:
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True): popup_assistant()
    render_top_panel()
    st.divider()

# =====================================================================
# 7. Part 1 — Librarian
# =====================================================================
TOPIC_PATTERN = re.compile(r"^\s*(\d{1,2})[.)\]]\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$", re.MULTILINE)

def _parse_topics(raw: str):
    parsed = []
    for m in TOPIC_PATTERN.findall(raw or ""):
        _, title, reason, effect, reaction = m
        parsed.append({"title": title.strip().lstrip("*").strip(), "reason": reason.strip(), "effect": effect.strip(), "audience_reaction": reaction.strip()})
    return parsed

@st.cache_data(ttl=900, show_spinner=False)
def analyze_channel_to_topics(channel, extra, region, obsidian_rules, base_prompt) -> list:
    base = f"[옵시디언 규칙서]\n{obsidian_rules}\n\n[기본 프롬프트]\n{base_prompt}\n\n[과제]\n타겟 채널 분석 -> 핵심 20개 추출.\n채널: {channel}\n지역: {region}\n[출력양식]\nNN. 주제 | 추천사유 | 예상효과 | 예상반응"
    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules
    raw = call_gemma(base, system=sys_ctx)
    if isinstance(raw, str) and raw.startswith("[ERROR]"): st.error(raw); return []
    parsed = _parse_topics(raw)
    if len(parsed) < 20: parsed = _parse_topics(call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)) or parsed
    return parsed[:20]

def save_part1_topic(chosen: dict) -> list:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_name = f"part1_selected_topic_{ts}"
    saved = []

    if st.session_state.path_obsidian:
        safe_makedirs(st.session_state.path_obsidian)
        md_path = os.path.join(st.session_state.path_obsidian, f"{base_name}.md")
        md = f"# [[{chosen['title']}]]\n\n## 📌 Brief Summary\n(Sage Mirror Studio Part 1)\n\n## 📖 Core Content\n- **추천 사유:** {chosen['reason']}\n- **예상 효과:** {chosen['effect']}\n\n## 🔗 Knowledge Connections\n- **Related Topics:** [[심리치유]], [[현자의거울]]\n\n---\n*Last updated: {today_str} {ts}*"
        if save_markdown(md_path, md): 
            lock_file_readonly(md_path)
            saved.append(md_path)

    if saved:
        st.toast(f"✅ 파일 저장 및 읽기전용 락(Lock) 완료", icon="🔒")
        success, msg = auto_git_push(f"Auto Save (Locked): '{chosen['title']}'")
    return saved

def render_part1():
    render_common_top()
    st.markdown('<div class="sage-header"><h2 style="margin:0">📚 Part 1 — Librarian (실전 벤치마킹 & 타겟 심층 분석)</h2></div>', unsafe_allow_html=True)
    
    with st.expander("🔒 시스템 설정 잠금 해제 (PIN)", expanded=False):
        pin = st.text_input("Part 1 PIN", type="password", key="p1_pin_input")
        if pin == PART_PINS["part1"]: st.session_state.unlock_part1 = True
        elif pin: st.session_state.unlock_part1 = False

    is_locked = not st.session_state.unlock_part1

    # ---------------------------------------------------------
    # NEW UI SECTION: Step 1 (Gemma Protocol & Channel Search)
    # ---------------------------------------------------------
    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 채널 탐색")
    c_left, c_right = st.columns(2, gap="large")
    
    with c_left:
        st.session_state.p1_gemma_protocol = st.text_area(
            "📝 젬마 프로토콜 (Gemma Protocol)",
            value=st.session_state.p1_gemma_protocol,
            placeholder="어린아이 같은 젬마에게 부여할 엄격한 규칙을 작성하세요...\n(예: 답변 시 반드시 [[키워드]] 형태를 사용하고, 심리/철학에 기반할 것)",
            height=200,
            disabled=is_locked
        )
        
    with c_right:
        st.markdown("##### 🔍 인간 운영 '철학/심리' 떡상 채널 탐색기")
        st.caption("AI 카피/재사용 채널을 거르고 진짜 원본 채널을 찾습니다.")
        search_kw = st.text_input("검색 키워드", value="50대 심리 철학 위로 채널", disabled=is_locked)
        
        if st.button("🌐 전 세계 채널 검색 (Tavily)", disabled=is_locked, use_container_width=True):
            if not st.session_state.tavily_api_key:
                st.error("좌측 사이드바 '⚙️ 설정 변경'에서 Tavily API Key를 먼저 입력하세요.")
            else:
                with st.spinner("Tavily 엔진을 통해 원본 채널 탐색 중..."):
                    from sage_engine import tavily_search
                    q = search_kw + " youtube channel psychology philosophy -AI -auto"
                    res = tavily_search(q, st.session_state.tavily_api_key, max_results=3)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.session_state.p1_channel_search_results = res.get("results", [])
        
        if st.session_state.p1_channel_search_results:
            with st.container(border=True):
                st.markdown("**검색된 원본 채널 목록**")
                for r in st.session_state.p1_channel_search_results:
                    st.markdown(f"- **[{r.get('title', '제목없음')}]({r.get('url', '#')})**")
                    st.caption(r.get('content', '')[:80] + "...")

    st.divider()

    # ---------------------------------------------------------
    # OLD Step 1 -> Step 2
    # ---------------------------------------------------------
    st.subheader("🎯 Step 2. 벤치마킹 타겟 채널 설정")
    c1, c2 = st.columns([3, 1])
    with c1: st.session_state.p1_channel_url = st.text_input("타겟 유튜브 URL 입력", value=st.session_state.p1_channel_url, disabled=is_locked)
    with c2: st.session_state.p1_region = st.selectbox("지역", ["국내+국외 모두", "국내 우선", "국외 우선"], disabled=is_locked)
    
    st.divider()

    # ---------------------------------------------------------
    # OLD Step 2 -> Step 3
    # ---------------------------------------------------------
    st.subheader("🧪 Step 3. Gemma4 분석 → 20개 핵심 주제 (현재 로직 유지)")
    if st.button("🚀 분석 시작", type="primary", disabled=is_locked):
        if not st.session_state.p1_channel_url: st.error("채널 입력 필요")
        else:
            with st.spinner("분석 중..."):
                st.session_state.p1_topics = analyze_channel_to_topics(st.session_state.p1_channel_url, "", st.session_state.p1_region, st.session_state.obsidian_rules, st.session_state.base_prompt_rules)
            st.rerun()

    if st.session_state.p1_topics:
        df = pd.DataFrame(st.session_state.p1_topics)
        st.dataframe(df, use_container_width=True)

        st.subheader("🎯 Step 4. 최종 주제 선택 및 지식 구조화 백업")
        st.caption("저장된 파일은 OS 수준에서 **읽기 전용**으로 보호되어 절대 덮어쓸 수 없습니다.")
        options = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p1_topics)]
        sel = st.selectbox("주제", options, key="p1_select")
        chosen = st.session_state.p1_topics[int(sel.split(".")[0]) - 1]
        
        if st.button("🔒 지식 구조화 포맷으로 저장 및 백업(Git+Obsidian)", type="primary"):
            st.session_state.p1_saved_paths = save_part1_topic(chosen)
            st.session_state.p1_save_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"✅ 안전하게 백업 및 잠금 완료 ({st.session_state.p1_save_ts})")
            for p in st.session_state.p1_saved_paths: st.code(p)

if part.startswith("Part 1"): render_part1()
else:
    render_common_top()
    st.markdown(f'<div class="sage-header"><h2 style="margin:0">{part}</h2></div>', unsafe_allow_html=True)
    st.info("👉 다음 지시서에서 구현됩니다.")
