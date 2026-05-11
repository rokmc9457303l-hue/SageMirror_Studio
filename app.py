# -*- coding: utf-8 -*-
"""
🪞 현자의 거울 스튜디오 (Sage's Mirror Studio) — Master App v7.1
================================================================
[v7.1] gemma4:e4b 모델 연동 | 11대 코어 규칙 완전 준수
[필수] pip install -r requirements.txt
[Ollama] ollama pull gemma4:e4b  /  ollama serve
[실행] streamlit run app.py
"""

import streamlit as st
import os
import re
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
    DEFAULT_OBSIDIAN_RULES, DEFAULT_BASE_PROMPT,
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
    page_title="Sage's Mirror Studio v7.1",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# =====================================================================
# 2. 세션 상태 초기화
# =====================================================================
def init_session_state():
    defaults = {
        "logged_in": False,
        "path_obsidian": "",
        "path_assets": "",
        "path_memo": "",
        "github_token": "",
        "github_repo_url": "",
        "github_local_path": str(Path.cwd()),
        "tavily_api_key": "",
        # 상단 공용 패널
        "obsidian_rules": DEFAULT_OBSIDIAN_RULES,
        "base_prompt_rules": DEFAULT_BASE_PROMPT,
        "obsidian_history": [],
        "prompt_history": [],
        # Sage Pop-up
        "popup_history": [],
        "popup_search_history": [],
        # Part 잠금
        "unlock_part1": False,
        "unlock_part2": False,
        # Part 1
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

init_session_state()


# =====================================================================
# 3. 로그인
# =====================================================================
def render_login():
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#888'>성경 · 철학 · 에세이가 융합된 다큐멘터리 자동화 스튜디오</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center'><span class='model-badge'>🧠 Active Model: {OLLAMA_MODEL}</span></p>",
        unsafe_allow_html=True,
    )
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("### 🔐 접근 제어 (Master Lock)")
        pw = st.text_input("마스터 비밀번호", type="password", key="master_pw_input")
        if st.button("로그인", type="primary", use_container_width=True):
            if pw == MASTER_PW_DEFAULT:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("비밀번호가 일치하지 않습니다.")
        st.caption(f"기본 비밀번호: `{MASTER_PW_DEFAULT}` (운영 시 변경)")

if not st.session_state.logged_in:
    render_login()
    st.stop()


# =====================================================================
# 4. 사이드바
# =====================================================================
with st.sidebar:
    st.markdown(f"### {APP_TITLE}")

    # Ollama 상태 표시
    status = check_ollama_status()
    if status["server"] and status["model"]:
        st.success(f"✅ Ollama 연결 | 모델: {OLLAMA_MODEL}")
    elif status["server"]:
        st.warning(f"⚠️ 서버 ON / 모델 미확인\n사용 가능: {', '.join(status['models'][:5])}")
    else:
        st.error(f"❌ Ollama 미연결 → `ollama serve` 실행 필요")

    st.divider()

    with st.expander("📁 다중 저장 경로", expanded=False):
        st.session_state.path_obsidian = st.text_input(
            "옵시디언 볼트 (.md)", value=st.session_state.path_obsidian,
            placeholder="C:/Obsidian/Vault/SageMirror",
        )
        st.session_state.path_assets = st.text_input(
            "에셋 (CSV/JSON)", value=st.session_state.path_assets,
            placeholder="C:/SageMirror/assets",
        )
        st.session_state.path_memo = st.text_input(
            "메모 (.txt)", value=st.session_state.path_memo,
            placeholder="C:/SageMirror/memo",
        )
        if st.button("📂 경로 일괄 생성", use_container_width=True):
            ok = True
            for p in [st.session_state.path_obsidian, st.session_state.path_assets, st.session_state.path_memo]:
                if p:
                    ok = safe_makedirs(p) and ok
            if ok:
                st.success("✅ 경로 생성 완료")

    with st.expander("🚀 GitHub 자동 백업", expanded=False):
        st.session_state.github_token = st.text_input(
            "GitHub PAT", value=st.session_state.github_token, type="password",
        )
        st.session_state.github_repo_url = st.text_input(
            "Repo URL", value=st.session_state.github_repo_url,
            placeholder="https://github.com/USER/sage-mirror.git",
        )
        st.session_state.github_local_path = st.text_input(
            "로컬 Repo 경로", value=st.session_state.github_local_path,
        )
        if st.button("🚀 GitHub Push", use_container_width=True):
            if not GIT_AVAILABLE:
                st.error("GitPython 미설치")
            elif not (st.session_state.github_token and st.session_state.github_repo_url):
                st.error("Token/URL 입력 필요")
            else:
                try:
                    rp = Path(st.session_state.github_local_path)
                    rp.mkdir(parents=True, exist_ok=True)
                    if not (rp / ".git").exists():
                        Repo.init(rp)
                    repo = Repo(rp)
                    repo.git.add(A=True)
                    if repo.is_dirty(untracked_files=True):
                        repo.index.commit(f"auto-backup {datetime.now().isoformat(timespec='seconds')}")
                    auth = st.session_state.github_repo_url.replace(
                        "https://", f"https://{st.session_state.github_token}@"
                    )
                    if "origin" in [r.name for r in repo.remotes]:
                        repo.remotes.origin.set_url(auth)
                    else:
                        repo.create_remote("origin", auth)
                    repo.remotes.origin.push(refspec="HEAD:refs/heads/main", force=True)
                    st.success("✅ Push 완료")
                except Exception as e:
                    st.error(f"Push 실패: {e}")

    with st.expander("🔑 외부 API", expanded=False):
        st.session_state.tavily_api_key = st.text_input(
            "Tavily API Key", value=st.session_state.tavily_api_key, type="password",
        )

    st.divider()
    st.markdown("### 📚 파트 메뉴")
    part = st.radio(
        "이동할 파트",
        [
            "Part 1: Librarian",
            "Part 2: Alchemist",
            "Part 3-4: Architect+Writer",
            "Part 5: Image Consistency",
            "Part 6: Opal Dispatcher",
            "Part 7: CapCut Bridge",
            "Part 8: Final Assembly",
        ],
        index=0, key="part_menu",
    )

    st.divider()
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()


# =====================================================================
# 5. 상단 공용 패널
# =====================================================================
def render_top_panel():
    with st.expander("📋 상단: 옵시디언 규칙서 및 타겟 선정 프롬프트", expanded=False):
        L, R = st.columns(2, gap="medium")

        with L:
            st.markdown(
                '<div class="top-panel-card">'
                '<div class="top-panel-title">📚 옵시디언 규칙서 (참조할 뼈대)</div>',
                unsafe_allow_html=True,
            )
            st.text_area(
                "옵시디언 규칙서",
                value=st.session_state.obsidian_rules, height=180,
                key="top_obsidian_view", label_visibility="collapsed",
            )
            st.session_state.obsidian_rules = st.session_state.top_obsidian_view
            bL1, bL2 = st.columns(2)
            with bL1:
                if st.button("🔍 팝업 편집", use_container_width=True, key="open_ob_popup"):
                    popup_edit_obsidian()
            with bL2:
                st.download_button(
                    "📥 .md", data=st.session_state.obsidian_rules,
                    file_name="obsidian_rules.md",
                    use_container_width=True, key="dl_ob_inline",
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with R:
            st.markdown(
                '<div class="top-panel-card">'
                '<div class="top-panel-title">🎯 기본 프롬프트 (타겟 선정 원칙)</div>',
                unsafe_allow_html=True,
            )
            st.text_area(
                "기본 프롬프트",
                value=st.session_state.base_prompt_rules, height=180,
                key="top_prompt_view", label_visibility="collapsed",
            )
            st.session_state.base_prompt_rules = st.session_state.top_prompt_view
            bR1, bR2 = st.columns(2)
            with bR1:
                if st.button("🔍 팝업 편집", use_container_width=True, key="open_pr_popup"):
                    popup_edit_prompt()
            with bR2:
                st.download_button(
                    "📥 .txt", data=st.session_state.base_prompt_rules,
                    file_name="base_prompt.txt",
                    use_container_width=True, key="dl_pr_inline",
                )
            st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# 6. 공용 헤더 (Sage 팝업 + 상단 패널)
# =====================================================================
def render_common_top():
    _l, _r = st.columns([7, 2])
    with _r:
        if st.button("🤖 Sage Pop-up", type="secondary",
                     use_container_width=True,
                     key=f"open_popup_{st.session_state.part_menu}"):
            popup_assistant()
    render_top_panel()
    st.divider()


# =====================================================================
# 7. Part 1 — Librarian (20개 주제 추출)
# =====================================================================
TOPIC_PATTERN = re.compile(
    r"^\s*(\d{1,2})[.)\]]\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$",
    re.MULTILINE,
)


def _parse_topics(raw: str):
    parsed = []
    for m in TOPIC_PATTERN.findall(raw or ""):
        _, title, reason, effect, reaction = m
        parsed.append({
            "title": title.strip().lstrip("*").strip(),
            "reason": reason.strip(),
            "effect": effect.strip(),
            "audience_reaction": reaction.strip(),
        })
    return parsed


@st.cache_data(ttl=900, show_spinner=False)
def analyze_channel_to_topics(channel, extra, region, obsidian_rules, base_prompt) -> list:
    base = f"""
[옵시디언 규칙서 — 반드시 준수]
{obsidian_rules}

[기본 프롬프트 — 채널 선정 원칙]
{base_prompt}

[과제]
아래 타겟 유튜브 채널의 시청자 결핍/고통/호응 포인트를 분석하여,
'60대 현자 다큐멘터리 채널'의 핵심 주제 20개를 추출하라.

[타겟 채널] {channel}
[지역 우선순위] {region}
[추가 컨텍스트]
{extra or "(없음)"}

[필수 출력 양식 — 정확히 20줄, 다른 텍스트 절대 금지]
NN. 주제명 | 추천 사유 | 예상 효과 | 예상 시청자 반응

[예시]
01. 인생의 절벽 앞에서 멈춰 선 @Protagonist에게 | 댓글 38% '의미 상실' | 빅터 프랭클 의미치료 공감 | "눈물이 멈추지 않습니다"

[제약]
- 정확히 20줄(01~20). 파이프(|)로만 구분.
- [성경 + 심리학 + 에세이적 위로] 융합 주제만.
- 등장인물은 '@Protagonist'. 
"""
    sys_ctx = SAGE_PERSONA + "\n\n[옵시디언 규칙서]\n" + obsidian_rules
    raw = call_gemma(base, system=sys_ctx)
    if isinstance(raw, str) and raw.startswith("[ERROR]"):
        st.error(raw)
        return []
    parsed = _parse_topics(raw)
    if len(parsed) < 20:
        retry = base + "\n\n[자가 교정] 양식 위반. 파이프(|) 양식으로 정확히 20줄만 다시 출력."
        raw2 = call_gemma(retry, system=sys_ctx)
        parsed = _parse_topics(raw2) or parsed
    return parsed[:20]


def save_part1_topic(chosen: dict) -> list:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"part1_selected_topic_{ts}"
    saved = []

    if st.session_state.path_obsidian:
        md_path = os.path.join(st.session_state.path_obsidian, f"{base}.md")
        md = (
            f"# Part 1 — 선택된 주제\n\n"
            f"- **저장 시각:** {ts}\n"
            f"- **타겟 채널:** {st.session_state.p1_channel_url}\n"
            f"- **지역:** {st.session_state.p1_region}\n"
            f"- **AI 모델:** {OLLAMA_MODEL}\n\n"
            f"## 🎯 주제\n**{chosen['title']}**\n\n"
            f"## 📊 추천 사유\n{chosen['reason']}\n\n"
            f"## 🎬 예상 효과\n{chosen['effect']}\n\n"
            f"## 💬 예상 반응\n{chosen['audience_reaction']}\n\n---\n\n"
            f"## 추가 컨텍스트\n{st.session_state.p1_extra_notes or '(없음)'}\n\n"
            f"[SOURCE: Sage Mirror Studio v7.1 / {OLLAMA_MODEL}]\n"
        )
        if save_markdown(md_path, md):
            saved.append(md_path)

    if st.session_state.path_assets:
        json_path = os.path.join(st.session_state.path_assets, f"{base}.json")
        payload = {
            "ts": ts, "model": OLLAMA_MODEL,
            "channel": st.session_state.p1_channel_url,
            "region": st.session_state.p1_region,
            "extra_notes": st.session_state.p1_extra_notes,
            "selected_topic": chosen,
            "all_20_candidates": st.session_state.p1_topics,
        }
        if save_json(json_path, payload):
            saved.append(json_path)

        csv_path = os.path.join(st.session_state.path_assets, f"{base}_all20.csv")
        rows = [[i+1, t["title"], t["reason"], t["effect"], t["audience_reaction"]]
                for i, t in enumerate(st.session_state.p1_topics)]
        if save_csv(csv_path, rows, ["#","주제명","추천사유","예상효과","예상반응"]):
            saved.append(csv_path)

    if st.session_state.path_memo:
        txt_path = os.path.join(st.session_state.path_memo, f"{base}.txt")
        content = (
            f"[선택 주제] {chosen['title']}\n"
            f"[추천 사유] {chosen['reason']}\n"
            f"[예상 효과] {chosen['effect']}\n"
            f"[예상 반응] {chosen['audience_reaction']}\n"
            f"[타겟 채널] {st.session_state.p1_channel_url}\n"
            f"[AI 모델] {OLLAMA_MODEL}\n"
            f"[저장 시각] {ts}\n"
        )
        if save_txt(txt_path, content):
            saved.append(txt_path)

    if saved:
        st.toast(f"✅ {len(saved)}개 파일 저장 완료", icon="✅")
    else:
        st.warning("⚠️ 사이드바에서 저장 경로를 먼저 설정하세요.")
    return saved


def render_part1():
    render_common_top()
    st.markdown(
        '<div class="sage-header"><h2 style="margin:0">📚 Part 1 — Librarian '
        '(실전 벤치마킹 & 타겟 심층 분석)</h2></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<span class='model-badge'>🧠 {OLLAMA_MODEL}</span>",
        unsafe_allow_html=True,
    )
    st.caption(
        "타겟: **구독자 적지만 조회수 폭발 심리/철학 채널** — "
        "댓글 빈출 키워드를 흡수하여 **20개 주제** 추출"
    )

    # PIN 잠금
    with st.expander("🔒 시스템 설정 잠금 해제 (PIN)", expanded=False):
        pin = st.text_input("Part 1 PIN", type="password", key="p1_pin_input")
        if pin:
            if pin == PART_PINS["part1"]:
                st.session_state.unlock_part1 = True
                st.success("🔓 잠금 해제됨")
            else:
                st.session_state.unlock_part1 = False
                st.warning("PIN 불일치")
        if not st.session_state.unlock_part1:
            st.info("🔒 잠금 상태 (PIN 입력 필요)")
    is_locked = not st.session_state.unlock_part1

    # Step 1
    st.subheader("🎯 Step 1. 벤치마킹 타겟 채널")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.session_state.p1_channel_url = st.text_input(
            "타겟 YouTube 채널 URL / 채널명",
            value=st.session_state.p1_channel_url,
            placeholder="https://www.youtube.com/@channel",
            disabled=is_locked,
        )
    with c2:
        st.session_state.p1_region = st.selectbox(
            "지역",
            ["국내+국외 모두", "국내 우선", "국외 우선"],
            index=["국내+국외 모두", "국내 우선", "국외 우선"].index(st.session_state.p1_region),
            disabled=is_locked,
        )
    st.session_state.p1_extra_notes = st.text_area(
        "추가 컨텍스트(선택)",
        value=st.session_state.p1_extra_notes, height=130, disabled=is_locked,
        placeholder="예) 댓글에 '결혼 후 외로움', '부모와의 단절' 반복...",
    )

    # Step 2
    st.divider()
    st.subheader("🧪 Step 2. Gemma4 분석 → 20개 핵심 주제")
    if st.button("🚀 분석 시작", type="primary", disabled=is_locked):
        if not st.session_state.p1_channel_url.strip():
            st.error("타겟 채널을 먼저 입력하세요.")
        else:
            with st.spinner(f"Sage가 타겟 채널을 해부 중... ({OLLAMA_MODEL})"):
                topics = analyze_channel_to_topics(
                    channel=st.session_state.p1_channel_url,
                    extra=st.session_state.p1_extra_notes,
                    region=st.session_state.p1_region,
                    obsidian_rules=st.session_state.obsidian_rules,
                    base_prompt=st.session_state.base_prompt_rules,
                )
            if topics:
                st.session_state.p1_topics = topics
                st.session_state.p1_saved = False
                st.session_state.p1_save_ts = None
                st.session_state.p1_saved_paths = []
                if len(topics) < 20:
                    st.warning(f"⚠️ {len(topics)}개만 추출됨. 재실행 권장.")
                else:
                    st.success("✅ 20개 주제 추출 완료")
            else:
                st.error("주제 추출 실패. Ollama 상태를 확인하세요.")

    # 결과 표시
    if st.session_state.p1_topics:
        st.divider()
        st.subheader("📊 추출된 핵심 주제 (드래그·복사 가능)")
        df = pd.DataFrame(st.session_state.p1_topics).rename(columns={
            "title": "주제명", "reason": "추천 사유",
            "effect": "예상 효과", "audience_reaction": "예상 반응",
        })
        df.index = range(1, len(df) + 1)
        st.dataframe(df, use_container_width=True, height=520)

        with st.expander("📋 복사용 통합 텍스트", expanded=False):
            joined = "\n".join(
                f"{i+1:02d}. {t['title']} | {t['reason']} | {t['effect']} | {t['audience_reaction']}"
                for i, t in enumerate(st.session_state.p1_topics)
            )
            st.code(joined, language="markdown")

        # Step 3
        st.divider()
        st.subheader("🎯 Step 3. 최종 주제 1개 선택 → Part 2")
        options = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p1_topics)]
        sel = st.selectbox("Part 2로 넘길 주제", options, key="p1_select")
        idx = int(sel.split(".")[0]) - 1
        chosen = st.session_state.p1_topics[idx]
        st.info(f"**선택 주제:** {chosen['title']}")

        sc1, sc2 = st.columns([1, 3])
        with sc1:
            if st.session_state.p1_saved:
                st.markdown(
                    f"<div class='saved-banner'>✅ 저장 완료<br>"
                    f"<small>{st.session_state.p1_save_ts}</small></div>",
                    unsafe_allow_html=True,
                )
            else:
                if st.button("💾 저장 → Part 2 전송",
                             type="primary", use_container_width=True, key="p1_save_btn"):
                    paths = save_part1_topic(chosen)
                    st.session_state.p1_selected_topic = chosen
                    st.session_state.p1_saved = True
                    st.session_state.p1_save_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.p1_saved_paths = paths
                    st.rerun()
        with sc2:
            if st.session_state.p1_saved:
                st.success(f"✅ Part 2 전송 완료 ({st.session_state.p1_save_ts})")
                if st.session_state.p1_saved_paths:
                    with st.expander("저장 파일 목록"):
                        for p in st.session_state.p1_saved_paths:
                            st.code(p)


# =====================================================================
# 8. 라우팅
# =====================================================================
if part.startswith("Part 1"):
    render_part1()
elif part.startswith("Part 2"):
    render_common_top()
    st.markdown(
        '<div class="sage-header"><h2 style="margin:0">⚗️ Part 2 — Alchemist (지식 융합 / RAG)</h2></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"<span class='model-badge'>🧠 {OLLAMA_MODEL}</span>", unsafe_allow_html=True)
    if st.session_state.p1_selected_topic:
        st.info(f"🔗 Part 1 전송 주제: **{st.session_state.p1_selected_topic['title']}**")
        with st.expander("Part 1 선택 주제 상세"):
            st.json(st.session_state.p1_selected_topic)
    else:
        st.warning("Part 1에서 주제를 선택·저장하지 않았습니다.")
    st.caption("👉 다음 지시서에서 본격 구현됩니다.")
else:
    render_common_top()
    st.markdown(
        f'<div class="sage-header"><h2 style="margin:0">{part}</h2></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"<span class='model-badge'>🧠 {OLLAMA_MODEL}</span>", unsafe_allow_html=True)
    st.info("👉 다음 지시서에서 본격 구현됩니다.")
