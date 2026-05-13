# -*- coding: utf-8 -*-
"""
🪞 현자의 거울 스튜디오 (Sage's 거울 스튜디오) — Master App v8.0
================================================================
[v8.0 업데이트 사항: 2026-05-11 19:10]
- 물리적 상태 저장 (Workspace Persistence) 도입
- 앱 개발 도중 데이터가 날아가지 않도록 현재 입력된 내용(UI/UX 상태)을 JSON 파일로 로컬 저장 및 불러오기
- 사이드바에 '현재 상태 저장 / 불러오기' 물리적 버튼 추가
- 원본 파일 훼손 없이 독립 복사본으로 안전망 유지
"""

import streamlit as st
import os
import re
import stat
import json
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
    page_title="Sage's Mirror Studio v8.0",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# =====================================================================
# 상태 저장 유틸리티 (v8.0 신규)
# =====================================================================
WORKSPACE_STATE_FILE = r"C:\SageMirror_Production\workspace_state.json"

def save_workspace_state():
    keys_to_save = [
        "path_obsidian", "github_repo_url", "tavily_api_key",
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        "p1_channel_url", "p1_region", "p1_topics", "p1_topic_selection",
        "p1_research_result", "p1_planning_result", "unlock_part1"
    ]
    data = {}
    for k in keys_to_save:
        if k in st.session_state:
            data[k] = st.session_state[k]
    try:
        with open(WORKSPACE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def load_workspace_state():
    if os.path.exists(WORKSPACE_STATE_FILE):
        try:
            with open(WORKSPACE_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception:
            pass
    return {}

# =====================================================================
# 2. 세션 상태 초기화
# =====================================================================
DEFAULT_OBSIDIAN_RULES_V80 = """[옵시디언 지식 구조화 규칙서]
모든 지식은 반드시 아래의 마크다운 양식을 엄격하게 준수하여 출력해야 합니다.

# [[Title of Concept/Entity]]

## 📌 Brief Summary
(A concise 1-2 sentence definition of this topic.)

## 📖 Core Content
(Detailed explanation synthesized from raw sources.)

## 🔗 Knowledge Connections
- **Related Topics:** [[Related-Concept-A]], [[Related-Concept-B]]
- **Projects/Contexts:** [[Project-Name]]
- **Contradictions/Notes:** (e.g., "Source X claims this, but Source Y disagrees.")

---
*Last updated: {오늘 날짜}*
"""

MASTER_RESEARCH_PROMPT_V80 = """[자료 조사 파트 전용 마스터 규칙서: 절대 가이드]

1. 타겟 시청자 (Target Audience)
   - 주요 타겟은 40대~70대(4070) 중장년층입니다.
   - 이들은 인생의 절벽, 은퇴, 인간관계의 단절, 외로움, 고독 등의 아픔을 겪고 있습니다.
   - 단순한 위로가 아닌, 성경적 지혜와 철학적 통찰이 결합된 '무거운 공감'을 원합니다.

2. 화자 설정 (Persona)
   - 화자는 산전수전을 다 겪고 깨달음을 얻은 '60대 현자(Sage)'입니다.
   - 시청자를 지칭할 때는 반드시 '@Protagonist' 라는 명칭을 사용하여 존중과 애정을 담습니다.

3. 지식의 추출 및 구조화 원칙 (마스터 키워드 전략)
   - 모든 자료를 분석할 때, 문맥에서 가장 중요한 5개의 핵심 단어를 추출하십시오.
   - 추출된 단어는 반드시 옵시디언 위키 링크 형식인 `[[키워드]]` 로 표기해야 합니다.
   - 각 키워드는 [철학], [심리], [성경] 3가지 카테고리 중 어디에 속하는지 명확히 분류하십시오.

[대본 핵심 가이드 및 영감 도출 지시서]
1. 🎯 베스트 키워드: 유튜브 알고리즘 & 감성 타격 키워드 3개 도출 (형태: `[[핵심키워드1]]`)
2. 📖 오늘의 명언: 대본의 주제를 꿰뚫는 철학자, 사상가, 혹은 성경의 명언 1개를 제시하십시오.
3. 🔥 핵심 전달 메시지: 이 영상이 끝났을 때 가슴에 남아야 할 단 하나의 위로/교훈 (2문장 이내)

[통합 기획 지시서 작성 원칙]
위에서 도출된 자료들을 종합하여 15분 분량의 유튜브 다큐멘터리 기획안을 작성하십시오.
1. 영상의 뼈대 (구조): 도입(공감) - 전개(해석) - 절정(명언/해답) - 결말(격려)
2. 시각적 스타일: 렘브란트풍의 묵직한 명암(Chiaroscuro), 어둠 속 한 줄기 빛
"""

GEMMA_PROTOCOL_V80 = """[Gemma4 행동 및 작업 지침서 (Gemma Protocol)]

당신은 이제 현자의 거울 스튜디오의 '수석 기획자'입니다. 아직 학습 중인 AI가 아니라, 다음의 엄격한 규칙을 따르는 전문가로 행동해야 합니다.

1. 출처 명기 의무화 (Absolute Citation)
   - 당신이 제공하는 모든 정보, 명언, 주장에는 반드시 출처(책 제목, 저자명, 성경 장절 등)를 명확히 기재해야 합니다.

2. 마크다운 및 태그 강제성
   - 중요한 개념어는 반드시 `[[단어]]` 형태로 출력하여 지식 연결이 가능하게 하십시오.
   - 답변은 장황한 서술형을 피하고, 글머리 기호(-, *, 1. 2.)를 사용하여 가독성 높게 구조화하십시오.

3. 페르소나 몰입 및 톤앤매너
   - 당신은 4070 세대의 아픔을 이해하는 60대 현자입니다. 가벼운 이모티콘이나 경박한 어투를 절대 사용하지 마십시오.
   - 모든 분석과 기획은 깊이 있는 심리학(융의 그림자 등), 철학(쇼펜하우어, 니체 등), 성경적 세계관에 기반해야 합니다.
"""

def init_session_state():
    loaded_data = load_workspace_state()
    defaults = {
        "logged_in": False,
        "path_obsidian": r"C:\SageMirror_Production\00_Obsidian_Archive", 
        "path_assets": r"C:\SageMirror_Production\00_Assets",
        "path_memo": r"C:\SageMirror_Production\00_Memo",
        "github_token": "",
        "github_repo_url": "https://github.com/rokmc9457303l-hue/SageMirror_Studio.git",
        "github_local_path": r"C:\SageMirror_Production",
        "tavily_api_key": "",
        "obsidian_rules": DEFAULT_OBSIDIAN_RULES_V80,
        "base_prompt_rules": MASTER_RESEARCH_PROMPT_V80,
        "obsidian_history": [],
        "prompt_history": [],
        "popup_history": [],
        "popup_search_history": [],
        "unlock_part1": False,
        "unlock_part2": False,
        
        "p1_gemma_protocol": GEMMA_PROTOCOL_V80,
        "p1_channel_search_results": [],
        "p1_channel_url": "",
        "p1_region": "국내+국외 모두",
        "p1_topics": [],
        "p1_topic_selection": None,
        "p1_research_result": "",
        "p1_planning_result": "",
        "p1_saved_paths": [],
    }
    
    # 이전에 저장된 물리적 상태가 있다면 오버라이드
    for k, v in loaded_data.items():
        if v: defaults[k] = v

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# =====================================================================
# [보안 로직 & 자동화 로직]
# =====================================================================
def lock_file_readonly(filepath):
    try:
        if os.path.exists(filepath):
            os.chmod(filepath, stat.S_IREAD)
            return True
    except Exception as e:
        st.warning(f"파일 락(Lock) 실패: {e}")
    return False

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
# 로그인 & 사이드바
# =====================================================================
def render_login():
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE} <span style='color:#10B981;font-size:0.5em;'>v8.0 Save State Edition</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888'>성경 · 철학 · 에세이가 융합된 다큐멘터리 자동화 스튜디오</p>", unsafe_allow_html=True)
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pw = st.text_input("마스터 비밀번호", type="password")
        if st.button("로그인", type="primary", use_container_width=True):
            if pw == MASTER_PW_DEFAULT:
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("비밀번호 불일치.")

if not st.session_state.logged_in:
    render_login()
    st.stop()

with st.sidebar:
    st.markdown(f"### {APP_TITLE} **v8.0**")
    status = check_ollama_status()
    if status["server"] and status["model"]: st.success(f"✅ Ollama | {OLLAMA_MODEL}")
    else: st.error(f"❌ Ollama 에러")

    st.divider()
    st.info(f"📂 **옵시디언 아카이브**\n{st.session_state.path_obsidian}")
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
            
    # V8.0 신규 추가: 물리적 상태 저장 버튼
    st.divider()
    st.markdown("💾 **작업 상태 관리 (물리적 백업)**")
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        if st.button("상태 저장", use_container_width=True):
            if save_workspace_state(): 
                st.success("데이터 보존!")
            else: 
                st.error("저장 실패")
    with c_s2:
        if st.button("불러오기", use_container_width=True):
            loaded = load_workspace_state()
            if loaded:
                for k, v in loaded.items():
                    st.session_state[k] = v
                st.success("복구 완료!")
                st.rerun()
            else:
                st.warning("저장된 데이터 없음")

    st.divider()
    part = st.radio("이동할 파트", ["Part 1: Librarian", "Part 2: Alchemist", "Part 3-4: Architect+Writer", "Part 5: Image Consistency", "Part 6: Opal Dispatcher", "Part 7: CapCut Bridge", "Part 8: Final Assembly"], index=0)
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# =====================================================================
# 팝업 로직 (Gemma Protocol 및 결과창들)
# =====================================================================
@st.dialog("📝 젬마 프로토콜 (Gemma Protocol) 편집", width="large")
def popup_edit_gemma_protocol():
    st.markdown("여기서 행동 지침과 작업 지침서를 상세하게 수정할 수 있습니다. 텍스트를 드래그하고 복사/붙여넣기 하세요.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p1_gemma_protocol, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p1_gemma_protocol = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()

@st.dialog("📚 자료 조사 결과 (팝업)", width="large")
def popup_edit_research():
    st.markdown("결과를 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")
    new_val = st.text_area("자료 조사 결과", value=st.session_state.p1_research_result, height=500, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p1_research_result = new_val
            st.rerun()
    with c2:
        if st.button("닫기", use_container_width=True):
            st.rerun()

@st.dialog("🎬 총괄 시나리오 기획 (팝업)", width="large")
def popup_edit_planning():
    st.markdown("기획안을 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")
    new_val = st.text_area("최종 기획안", value=st.session_state.p1_planning_result, height=500, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p1_planning_result = new_val
            st.rerun()
    with c2:
        if st.button("닫기", use_container_width=True):
            st.rerun()

# =====================================================================
# 공통 UI 레이아웃 (마스터 템플릿: 상단 2개)
# =====================================================================
def render_top_panel():
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 마스터 프롬프트", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=300, key="top_ob_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="ob_btn"): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🎯 마스터 프롬프트 (전역 가이드)</div>', unsafe_allow_html=True)
            st.text_area("기본 프롬프트", value=st.session_state.base_prompt_rules, height=300, key="top_pr_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="pr_btn"): popup_edit_prompt()
            st.markdown('</div>', unsafe_allow_html=True)

def render_common_top():
    _l, _r = st.columns([7, 2])
    with _r:
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True): popup_assistant()
    render_top_panel()
    st.divider()

# =====================================================================
# Part 1 엔진 API 로직
# =====================================================================
TOPIC_PATTERN = re.compile(r"^\s*(\d{1,2})[.)\]]\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$", re.MULTILINE)

def _parse_topics(raw: str):
    parsed = []
    for m in TOPIC_PATTERN.findall(raw or ""):
        _, title, reason, effect, reaction = m
        parsed.append({"title": title.strip().lstrip("*").strip(), "reason": reason.strip(), "effect": effect.strip(), "audience_reaction": reaction.strip()})
    return parsed

@st.cache_data(ttl=900, show_spinner=False)
def analyze_channel_to_topics(channel, region, obsidian_rules, base_prompt, gemma_protocol) -> list:
    base = f"""[젬마 프로토콜]\n{gemma_protocol}\n\n[옵시디언 규칙서]\n{obsidian_rules}\n\n[기본 프롬프트]\n{base_prompt}

[과제]
다음 타겟 채널을 분석하여 핵심 주제 20개를 추출하십시오.
(요구사항: 사람이 직접 운영하는 채널이라 가정하고, 해당 채널의 영상에 달린 시청자 댓글 200개 이상을 분석했다고 가상으로 설정하십시오. 시청자들의 실제 체험담, "나도 그런 일 있었는데 이렇게 해결했다"는 식의 공감/경험 포인트가 반영된 생생한 주제를 뽑아내야 합니다.)

채널: {channel}
지역: {region}

[출력양식]
NN. 주제 | 추천사유(체험담 기반) | 예상효과 | 예상반응"""

    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules
    raw = call_gemma(base, system=sys_ctx)
    if isinstance(raw, str) and raw.startswith("[ERROR]"): st.error(raw); return []
    parsed = _parse_topics(raw)
    if len(parsed) < 20: parsed = _parse_topics(call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)) or parsed
    return parsed[:20]

def generate_research_draft(channel_url, topic, gemma_protocol, master_prompt):
    base = f"""[젬마 프로토콜]\n{gemma_protocol}\n\n[마스터 규칙서]\n{master_prompt}

[작업 지시]
다음 선택된 주제에 대하여, 200여 개의 시청자 공감 댓글(체험담)을 참조하였다고 가정하고, 철학/심리학/성경 기반 지식을 융합하여 '자료 조사 및 기초 초안'을 작성하시오.
* 주제: {topic}
* 타겟 채널: {channel_url}

[필수 포함 항목]
1. 세부 주제 및 매력적인 제목 (Title)
2. 핵심 키워드 (`[[키워드]]` 형식, 반드시 포함)
3. 시청자 후킹 기법 (실제 체험담을 활용한 공감 형성)
4. 타겟 채널 구조 분석 기반 차별화 전략
5. **모든 대본/자료의 출처 명기 필수** (책 이름, 저자명, 성경 구절 등 명확히 표기)
"""
    return call_gemma(base, system=SAGE_PERSONA)

def generate_final_planning(research_result, gemma_protocol, master_prompt):
    base = f"""[젬마 프로토콜]\n{gemma_protocol}\n\n[마스터 규칙서]\n{master_prompt}

[자료 조사 결과]
{research_result}

[작업 지시]
위 자료 조사 결과를 바탕으로 '15분 분량의 유튜브 다큐멘터리 총괄 시나리오 기획안(뼈대)'을 작성하시오.

[필수 포함 항목]
1. 영상의 구조 (도입부: 시청자 체험담 공감 - 전개부: 철학/심리 해석 - 절정부: 성경적/현자의 해답 - 결말부: 격려)
2. 4070 시청자 감성 타격 전략 및 시각적 연출 가이드 (렘브란트풍 등)
3. 클라이맥스에 들어갈 '오늘의 명언' 및 교훈
"""
    return call_gemma(base, system=SAGE_PERSONA)

# =====================================================================
# Part 1 렌더링
# =====================================================================
def render_part1():
    render_common_top()
    st.markdown('<div class="sage-header"><h2 style="margin:0">📚 Part 1 — Librarian (실전 벤치마킹 & 타겟 심층 분석)</h2></div>', unsafe_allow_html=True)
    
    with st.expander("🔒 시스템 설정 잠금 해제 (마스터 PIN: 7777)", expanded=False):
        pin = st.text_input("Part 1 PIN", type="password", key="p1_pin_input")
        if pin == PART_PINS["part1"]: st.session_state.unlock_part1 = True
        elif pin: st.session_state.unlock_part1 = False

    is_locked = not st.session_state.unlock_part1
    if is_locked:
        st.warning("🔒 분석 실행 및 편집을 위해 위 설정 창에서 마스터 PIN(7777)을 입력해 주세요.")

    # ---------------------------------------------------------
    # 중간 2개 (AI 프로토콜 / 타겟 설정)
    # ---------------------------------------------------------
    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")
    c_left, c_right = st.columns(2, gap="large")
    
    with c_left:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)
        st.text_area("젬마 프로토콜 (수정은 편집 버튼 클릭)", value=st.session_state.p1_gemma_protocol, height=270, label_visibility="collapsed")
        if st.button("🔍 프로토콜 팝업 편집 (복사/붙여넣기)"):
            popup_edit_gemma_protocol()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_right:
        st.markdown("##### 🔍 떡상 채널 발굴용 탐색기")
        st.caption("AI 카피를 배제한 순수 인간 운영의 최고 조회수 채널 여러 개를 검색하여 검토합니다.")
        search_kw = st.text_input("검색 키워드 (가이드라인 기반 자동 세팅)", value="50대 심리 철학 위로 채널", disabled=is_locked)
        
        if st.button("🌐 전 세계 채널 5개 탐색 및 리스트업 (Tavily)", disabled=is_locked, use_container_width=True):
            if not st.session_state.tavily_api_key:
                st.error("좌측 사이드바 '⚙️ 설정 변경'에서 Tavily API Key를 먼저 입력하세요.")
            else:
                with st.spinner("최고 떡상 원본 채널 5개를 심층 탐색 중..."):
                    from sage_engine import tavily_search
                    q = search_kw + " highest views human operated psychology philosophy -AI -auto youtube channel"
                    res = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                    
                    if "error" in res: st.error(res["error"])
                    else:
                        st.session_state.p1_channel_search_results = res.get("results", [])
                        st.success("🎯 채널 검색 완료! 아래 목록에서 가장 적합한 채널을 선택하세요.")
        
        if st.session_state.p1_channel_search_results:
            with st.container(border=True):
                st.markdown("**🎯 분석할 채널을 선택하세요 (선택 시 아래 URL에 자동 입력됨):**")
                options = []
                for i, r in enumerate(st.session_state.p1_channel_search_results):
                    options.append(f"[{i+1}] {r.get('title', '제목없음')} - {r.get('url', '#')}")
                
                selected_channel = st.radio("검색된 채널 리스트", options, label_visibility="collapsed", disabled=is_locked)
                
                if selected_channel:
                    selected_url = selected_channel.split(" - ")[-1]
                    st.session_state.p1_channel_url = selected_url
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 🎯 분석 대상 확정")
        st.session_state.p1_channel_url = st.text_input("타겟 유튜브 URL (위에서 선택 시 자동 입력됨)", value=st.session_state.p1_channel_url, disabled=is_locked)
        st.session_state.p1_region = st.selectbox("타겟 지역", ["국내+국외 모두", "국내 우선", "국외 우선"], disabled=is_locked)

    st.divider()

    # ---------------------------------------------------------
    # 하단 3분할 (칸별로 테두리 박스로 세로 구분)
    # ---------------------------------------------------------
    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진 (하단 3분할)")
    c_bench, c_research, c_plan = st.columns(3, gap="large")
    
    # [1. 벤치마킹 분석]
    with c_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 벤치마킹 분석")
            st.caption("주제 20개 추천 (추천사유, 효과, 반응)")
            
            if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked):
                if not st.session_state.p1_channel_url: 
                    st.error("⚠️ 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")
                else:
                    with st.spinner("채널 분석 중... (200개 댓글 공감 포인트 참조)"):
                        st.session_state.p1_topics = analyze_channel_to_topics(
                            st.session_state.p1_channel_url, st.session_state.p1_region, 
                            st.session_state.obsidian_rules, st.session_state.base_prompt_rules, st.session_state.p1_gemma_protocol
                        )
            
            if st.session_state.p1_topics:
                st.markdown("<br>", unsafe_allow_html=True)
                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p1_topics)]
                st.session_state.p1_topic_selection = st.selectbox("📌 기획할 주제 1개 선정", topics_display, disabled=is_locked)
                with st.expander("추출된 20개 상세 결과 보기"):
                    for t in st.session_state.p1_topics:
                        st.markdown(f"**{t['title']}**\n- 사유: {t['reason']}\n- 효과: {t['effect']}")

    # [2. 자료 조사 결과]
    with c_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 자료 조사 결과")
            st.caption("옵시디언/리서치 융합 기초 초안 작성 (출처 명기)")
            
            if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked):
                if not st.session_state.p1_topic_selection:
                    st.error("⚠️ 먼저 좌측의 '벤치마킹 시작' 버튼을 눌러 분석을 완료하고 주제를 선택해 주세요.")
                else:
                    with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):
                        topic_str = st.session_state.p1_topic_selection
                        st.session_state.p1_research_result = generate_research_draft(
                            st.session_state.p1_channel_url, topic_str,
                            st.session_state.p1_gemma_protocol, st.session_state.base_prompt_rules
                        )
            
            if st.session_state.p1_research_result:
                st.markdown("<br>", unsafe_allow_html=True)
                st.text_area("자료 조사 결과 (복사 가능)", value=st.session_state.p1_research_result, height=350, label_visibility="collapsed")
                if st.button("🔍 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_res"):
                    popup_edit_research()

    # [3. 총괄 기획안]
    with c_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안")
            st.caption("15분 영상 뼈대 총괄 시나리오 기획 (마스터 플랜)")
            
            if st.button("🎬 총괄 시나리오 기획", use_container_width=True, disabled=is_locked):
                if not st.session_state.p1_research_result:
                    st.error("⚠️ 먼저 중앙의 '자료조사 및 초안 작성'을 완료해 주세요.")
                else:
                    with st.spinner("시나리오 뼈대 설계 중..."):
                        st.session_state.p1_planning_result = generate_final_planning(
                            st.session_state.p1_research_result,
                            st.session_state.p1_gemma_protocol, st.session_state.base_prompt_rules
                        )
            
            if st.session_state.p1_planning_result:
                st.markdown("<br>", unsafe_allow_html=True)
                st.text_area("최종 기획안 (복사 가능)", value=st.session_state.p1_planning_result, height=270, label_visibility="collapsed")
                if st.button("🔍 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_plan"):
                    popup_edit_planning()
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔒 최종안 옵시디언 자동 백업", type="primary", use_container_width=True):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    base_name = f"part1_final_plan_{ts}"
                    if st.session_state.path_obsidian:
                        safe_makedirs(st.session_state.path_obsidian)
                        md_path = os.path.join(st.session_state.path_obsidian, f"{base_name}.md")
                        
                        topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection else "기획안"
                        
                        md = f"""# [[{topic_title}]]
## 📌 Brief Summary
Sage Mirror Studio v8.0 총괄 시나리오 기획안

## 📖 Core Content (Research)
{st.session_state.p1_research_result}

## 🎬 Final Scenario Plan
{st.session_state.p1_planning_result}

## 🔗 Knowledge Connections
- **Related Topics:** [[심리치유]], [[현자의거울]]
- **Projects/Contexts:** [[SageMirror_Production_v8.0]]

---
*Last updated: {today_str} {ts}*
"""
                        if save_markdown(md_path, md):
                            lock_file_readonly(md_path)
                            st.toast(f"✅ 기획안 저장 및 락(Lock) 완료", icon="🔒")
                            success, msg = auto_git_push(f"Auto Save (Locked): '{topic_title}'")

if part.startswith("Part 1"): render_part1()
else:
    render_common_top()
    st.markdown(f'<div class="sage-header"><h2 style="margin:0">{part}</h2></div>', unsafe_allow_html=True)
    st.info("👉 다음 지시서에서 구현됩니다.")
