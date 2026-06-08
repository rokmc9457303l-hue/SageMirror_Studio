# -*- coding: utf-8 -*-
"""
sage_right_panel.py — 우측 고정 브레인 패널 v2.0
[2026-05-31 전면 재설계]

변경 내역:
- 기본 모델: gemini-2.5-flash (3~8초, 노트북 부하 없음)
- 입력창: Gemini 스타일 1줄 [+][입력][모델▾][↑]
- 브레인 시스템 프롬프트: 8파트 파이프라인 전체 탑재
- 옵시디언: 저장만 (RAG 조회 제거)
- 우측 패널 sticky (스크롤 따라 움직이지 않음)
- 로딩 스피너: 생성 중 회전 아이콘
- 자동저장: raw 방식만 (gemma 추가 호출 없음)
"""

import streamlit as st
import requests
import json
from datetime import datetime
from pathlib import Path

# ── 외부 모듈 안전 임포트 ─────────────────────────────────────────────
try:
    from sage_config import OLLAMA_MODEL
except Exception:
    OLLAMA_MODEL = "gemma4:e2b"

try:
    from sage_engine import call_gemma, tavily_search
except Exception:
    def call_gemma(p, system="", model="gemma4:e2b"): return "[sage_engine 오류]"
    def tavily_search(q, k): return {}

try:
    from sage_popups import _save_to_obsidian_with_tags, PART_CONTEXT_MAP
except Exception:
    _save_to_obsidian_with_tags = None
    PART_CONTEXT_MAP = {}

try:
    from research_router import run_tavily_research, format_search_results_markdown
    _ROUTER_OK = True
except Exception:
    _ROUTER_OK = False

# ── 경로 상수 ─────────────────────────────────────────────────────────
BASE_PATH     = Path(r"C:\SageMirror_Production")
OBSIDIAN_PATH = BASE_PATH / "00_Obsidian"
SESSION_PATH  = BASE_PATH / "00_Session_States"
CHAT_JSON     = SESSION_PATH / "right_panel_chat.json"
YT_JSON       = SESSION_PATH / "yt_monitor_channels.json"

# ── 모델 목록 ─────────────────────────────────────────────────────────
# Gemma = 로컬 기본 브레인 (오프라인 작동)
# Gemini = 자료조사·출처 검색 보조 (인터넷 필요)
RP_MODELS = ["gemma4:e2b", "gemma4:e4b", "gemini-2.5-flash"]
RP_DEFAULT = "gemma4:e2b"

# ── 8파트 브레인 시스템 프롬프트 ────────────────────────────────────
# Gemma = 로컬 총괄 브레인 / Gemini·Tavily = 자료조사 보조
BRAIN_PROMPT = """[현자의 거울 스튜디오 — 총괄 브레인]

너는 현자의 거울 유튜브 제작 시스템의 총괄 AI다.
로컬에서 실행되며 8파트 전체 작업을 지휘·실행한다.
대상: 40~70대 한국인 / 철학·심리·성경 롱폼 콘텐츠

[8파트 파이프라인]
P1 Librarian  → 벤치마킹·주제발굴·자료조사 → P2 전달 패킷
P2 Alchemist  → 철학·성경·심리 3원 융합 → 기획안
P3 Writer     → 나레이션 대본·이미지 대본·CapCut 에셋
P4 Image      → @Protagonist·@거울속아바타 렘브란트 명암 프롬프트
P5 Video      → Google Opal 영상 생성 프롬프트
P6 Narration  → TTS 감정지시(EXPR-01~06) + BGM 무드
P7 Shorts     → 숏폼 추출 + CapCut 타임코드
P8 Final      → 제목·설명·태그 + 업로드 패키지

[철학 기승전결 프레임]
기: 쇼펜하우어(고통·의지·권태) + 다크심리학(나르시시즘·가스라이팅·조종·그림자자아) — 문제 제기
승: 융(그림자·페르소나·무의식) + 프랭클(로고테라피·실존적 공허) — 심층 분석
전: 몽테뉴(자기 관찰·에세이) + 심리학(회복탄력성·자존감) — 전환점
결: 성경(시편·잠언·전도서) — 회복·희망·은혜

[현재 파트 & 데이터]
{part_info}

[응답 원칙]
· 인사 → 간결히 인사
· 작업 지시 → 즉시 실행, 결과 제시
· 검토 요청 → 기승전결·감정흐름·철학 프레임 점검
· 수정 → 원본 유지하며 개선안 제시
· 불확실 → 솔직히 확인 필요 답변
· 항상 한국어로 답하라
"""

# ── 파트별 편집 가능 키 ───────────────────────────────────────────────
# ── 범용 카테고리 태그 (다채널 운영 대응) ────────────────────────────
# 특정 채널·심리학에 종속되지 않는 보편 분류 체계
UNIVERSAL_CATEGORY_TAGS = {
    "감정":       ["고독","외로움","후회","불안","상실","슬픔","공허","두려움","희망","용기","분노","수치","감사","기쁨"],
    "철학":       ["쇼펜하우어","니체","스토아","칸트","소크라테스","하이데거","실존주의","몽테뉴","파스칼","노자","장자","불교"],
    "다크심리학": ["나르시시즘","가스라이팅","조종","트라우마","학습된 무기력","정서학대","그림자자아","착취","방치"],
    "성경·신앙":  ["시편","잠언","전도서","욥기","이사야","로마서","기도","회복","은혜","성경","신앙","영성"],
    "심리학":     ["자존감","애착","번아웃","회복탄력성","인지행동","로고테라피","실존적공허","프랭클","융","개성화"],
    "문학·에세이":["몽테뉴","수상록","에세이","팡세","명상록","세네카","에픽테토스","스토아","파스칼"],
    "고전소설":   ["도스토옙스키","톨스토이","헤세","카뮈","카프카","죄와벌","카라마조프","데미안","이방인","변신","어린왕자"],
    "한국문학":   ["황석영","이청준","박경리","토지","윤동주","이상","한국소설","한국시"],
    "인생단계":   ["은퇴","노년","중년","빈둥지","자녀독립","죽음준비","노후","4050","6070","인생2막"],
    "역사·인물":  ["역사","인물","위인","문명","사건","시대","전쟁","문화","리더십"],
    "경제·비즈니스":["경제","투자","은퇴","부업","재테크","창업","직업","시장"],
    "건강·생활":  ["수면","운동","건강","노년","라이프","식습관","마음챙김","웰니스"],
    "유튜브전략": ["제목","썸네일","후킹","알고리즘","시청지속","조회수","구독","shorts"],
    "채널운영":   ["채널","타겟","콘텐츠","포맷","페르소나","기획","벤치마킹"],
    "제작자료":   ["이미지","영상","나레이션","BGM","대본","프롬프트","CapCut","씬"],
    "출처자료":   ["논문","책","기사","PDF","연구","출처","웹","인용"],
}

def _classify_content_tags(content: str, title: str = "") -> dict:
    """
    콘텐츠에서 범용 카테고리·키워드 자동 분류.
    특정 채널에 종속되지 않는 보편 태그 생성.
    """
    text = (content + " " + title).lower()
    detected = {}
    for category, keywords in UNIVERSAL_CATEGORY_TAGS.items():
        hits = [kw for kw in keywords if kw.lower() in text]
        if hits:
            detected[category] = hits[:6]
    return detected


def _build_obs_tags(content: str, title: str = "") -> tuple:
    """
    Raw/Wiki 저장 시 공통 태그 블록 생성.
    Returns: (wiki_links_str, hash_tags_str, category_section_str)
    """
    detected = _classify_content_tags(content, title)
    all_kws = []
    category_lines = []
    for cat, kws in detected.items():
        all_kws.extend(kws)
        cat_tag = cat.replace("·","_").replace(" ","_")
        category_lines.append(f"- **{cat}**: {', '.join(kws)} → #{cat_tag}")
    all_kws = list(dict.fromkeys(all_kws))[:12]
    wiki_links = " ".join([f"[[{kw}]]" for kw in all_kws])
    hash_tags  = " ".join([f"#{kw.replace(' ','_')}" for kw in all_kws])
    cat_section = "\n".join(category_lines) if category_lines else "(태그 없음)"
    return wiki_links, hash_tags, cat_section


APP_EDIT_KEYS = {
    "파트 1": {"p1_bench_result":"📊 벤치마킹","p1_research_result":"🔬 자료조사","p1_planning_result":"📋 기획안"},
    "파트 2": {"p2_research_result":"🔬 연구 결과","p2_planning_result":"📋 기획안"},
    "파트 3": {"p34_narration_script":"🎙️ 나레이션","p34_image_script":"🖼️ 이미지 대본"},
    "파트 4": {"p5img_result":"🖼️ 이미지 프롬프트"},
    "파트 6": {"p6_narration_result":"🎙️ 나레이션","p6_bgm_result":"🎵 BGM"},
    "파트 8": {"p8_production_guide":"📦 최종 가이드"},
}

# ─────────────────────────────────────────────────────────────────────
# CSS — Gemini 스타일 + Sticky 패널
# ─────────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ── 우측 컬럼 Sticky 고정 ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child {
    position: sticky !important;
    top: 0px !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow-y: auto !important;
    align-self: flex-start !important;
    z-index: 100 !important;
    border-left: 1px solid rgba(155,89,182,0.18);
    background: #0b0b10;
}

/* ── 메시지 스타일 ── */
.rp-msg-user {
    background: rgba(155,89,182,0.1);
    border-left: 2px solid #9b59b6;
    border-radius: 0 8px 8px 8px;
    padding: 8px 12px;
    margin: 4px 0;
    color: #e0d4f5;
    font-size: 0.85rem;
    line-height: 1.6;
}
.rp-msg-asst {
    padding: 6px 12px;
    margin: 4px 0;
    color: #cdc0e0;
    font-size: 0.85rem;
    line-height: 1.7;
}

/* ── 헤더 ── */
.rp-hdr {
    color: #b894e0;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 6px 0 4px;
}
.rp-part-badge {
    background: rgba(155,89,182,0.15);
    color: #b894e0;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.68rem;
    font-weight: 600;
}

/* ── Gemini 스타일 입력창 ── */
.rp-input-wrap {
    background: #14101e;
    border: 1px solid rgba(155,89,182,0.28);
    border-radius: 26px;
    padding: 2px 8px;
    margin-top: 4px;
}
.rp-input-wrap div[data-testid="stHorizontalBlock"] {
    align-items: center !important;
    gap: 2px !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    border-radius: 0 !important;
}
div[data-testid="stTextArea"] textarea {
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: #e8e0f0 !important;
    font-size: 0.88rem !important;
    resize: none !important;
    padding: 10px 4px !important;
    min-height: 44px !important;
    max-height: 120px !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border: none !important;
    box-shadow: none !important;
}
div[data-testid="stTextArea"] > label { display: none !important; }
div[data-testid="stTextArea"] > div > div { border: none !important; }

/* ── 입력창 내 버튼 정렬 ── */
.rp-input-wrap button {
    background: transparent !important;
    border: none !important;
    color: #9b59b6 !important;
    font-size: 1.1rem !important;
    min-width: 34px !important;
    height: 34px !important;
    padding: 0 !important;
    border-radius: 50% !important;
}
.rp-input-wrap button:hover {
    background: rgba(155,89,182,0.15) !important;
}
.rp-input-wrap button[kind="primary"] {
    background: #7d3dab !important;
    color: white !important;
}
.rp-input-wrap button[kind="primary"]:hover {
    background: #9b59b6 !important;
}

/* ── selectbox 컴팩트 ── */
.rp-input-wrap div[data-testid="stSelectbox"] > div {
    background: transparent !important;
    border: none !important;
    color: #8870a8 !important;
    font-size: 0.75rem !important;
    min-height: 32px !important;
}
.rp-input-wrap div[data-testid="stSelectbox"] > div:hover {
    background: rgba(155,89,182,0.08) !important;
}

/* ── 로딩 스피너 ── */
@keyframes rp-spin {
    0%   { transform: rotate(0deg);   }
    100% { transform: rotate(360deg); }
}
.rp-loading {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    color: #9b59b6;
    font-size: 0.78rem;
}
.rp-loading-icon {
    display: inline-block;
    animation: rp-spin 1s linear infinite;
}

/* ── 허브 탭 ── */
.rp-hub { border-bottom: 1px solid rgba(155,89,182,0.15); padding-bottom: 8px; }

/* ── 복사 버튼 ── */
button[kind="secondary"].rp-copy {
    font-size: 0.7rem !important;
    padding: 2px 8px !important;
    height: 24px !important;
    color: #6a5a7a !important;
}
</style>
"""

# ─────────────────────────────────────────────────────────────────────
# 세션 초기화
# ─────────────────────────────────────────────────────────────────────
def _rp_init():
    defs = {
        "rp_history":        [],
        "rp_model":          RP_DEFAULT,
        "rp_hub_open":       False,
        "rp_hub_tab":        "",
        "rp_tavily_ctx":     "",
        "rp_pending_prompt": None,
        "rp_yt_channels":    _load_yt_channels(),
        "rp_local_path":     str(BASE_PATH),
        "rp_send_key":       0,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.rp_history:
        st.session_state.rp_history = _load_chat_json()

# ─────────────────────────────────────────────────────────────────────
# 저장 / 로드
# ─────────────────────────────────────────────────────────────────────
def _save_chat_json():
    try:
        SESSION_PATH.mkdir(parents=True, exist_ok=True)
        CHAT_JSON.write_text(
            json.dumps(st.session_state.rp_history, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass

def _load_chat_json() -> list:
    try:
        if CHAT_JSON.exists():
            d = json.loads(CHAT_JSON.read_text(encoding="utf-8", errors="ignore"))
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []

def _save_yt_channels(chs):
    try:
        SESSION_PATH.mkdir(parents=True, exist_ok=True)
        YT_JSON.write_text(json.dumps(chs, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _load_yt_channels() -> list:
    try:
        if YT_JSON.exists():
            d = json.loads(YT_JSON.read_text(encoding="utf-8", errors="ignore"))
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []

# ─────────────────────────────────────────────────────────────────────
# 브레인 시스템 프롬프트 빌더 (8파트 컨텍스트, Obsidian 조회 없음)
# ─────────────────────────────────────────────────────────────────────
def _build_brain_prompt() -> str:
    part_val = st.session_state.get("sidebar_part", "파트 1")
    # 파트 키 추출
    part_key = "part1"
    for k in ["part1","part2","part3","part34","part4","part5","part6","part7","part8"]:
        num = k.replace("part","").replace("34","3")
        if f"파트 {num}" in part_val or f"파트{num}" in part_val:
            part_key = k
            break

    # 현재 파트 데이터 (session_state에서 직접 읽기)
    part_data_lines = []
    if PART_CONTEXT_MAP:
        info = PART_CONTEXT_MAP.get(part_key, {})
        for sk in info.get("keys", [])[:4]:
            val = str(st.session_state.get(sk, ""))[:400]
            if val.strip():
                part_data_lines.append(f"  [{sk}]: {val}")
    
    part_info = f"파트: {part_val}\n"
    if part_data_lines:
        part_info += "현재 데이터:\n" + "\n".join(part_data_lines)
    else:
        part_info += "현재 데이터: (없음 — 작업 시작 전)"

    # Tavily 컨텍스트 (있을 때만)
    tav = st.session_state.get("rp_tavily_ctx", "")
    tav_section = f"\n[참조 자료 — 웹검색]\n{tav[:400]}" if tav else ""

    # 옵시디언 RAG (활성화 시 — 현재 파트 키워드로 검색)
    obs_section = ""
    if st.session_state.get("rp_obs_rag_on", True):
        obs_query = part_val + " " + " ".join(part_data_lines)[:100]
        obs_result = _obs_search_rag(obs_query, max_files=3, max_chars=400)
        if obs_result:
            obs_section = f"\n[옵시디언 관련 자료 — RAG]\n{obs_result}"

    return BRAIN_PROMPT.format(part_info=part_info) + tav_section + obs_section

# ─────────────────────────────────────────────────────────────────────
# 스트리밍 제너레이터
# ─────────────────────────────────────────────────────────────────────
def _stream_gemma(prompt: str, system: str = "", model: str = "gemma4:e2b"):
    """Ollama 로컬 스트리밍"""
    full = (system.strip() + "\n\n" + prompt) if system.strip() else prompt
    payload = {
        "model": model, "prompt": full, "stream": True,
        "keep_alive": st.session_state.get("popup_keep_alive", "10m"),
        "options": {
            "num_predict": st.session_state.get("popup_num_predict", 400),
            "temperature": st.session_state.get("popup_temperature", 0.3),
            "top_p":       st.session_state.get("popup_top_p", 0.9),
        }
    }
    try:
        in_think = False
        with requests.post("http://localhost:11434/api/generate",
                           json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line: continue
                try: chunk = json.loads(line.decode("utf-8"))
                except Exception: continue
                tok = chunk.get("response", "")
                if tok:
                    if "<think>" in tok: in_think = True
                    if in_think:
                        if "</think>" in tok: in_think = False
                        continue
                    yield tok
                if chunk.get("done", False): break
    except Exception as e:
        yield f"\n[Gemma 오류] {e}\n→ Ollama 실행 확인: http://localhost:11434"


def _stream_gemini(prompt: str, system: str = "", model: str = "gemini-2.5-flash"):
    """Gemini API 스트리밍"""
    try:
        import google.generativeai as genai
        api_key = st.session_state.get("gemini_api_key", "")
        if not api_key:
            yield "[Gemini API 키 없음 — [+] ⚙️ 설정에서 입력하세요]"
            return
        genai.configure(api_key=api_key)
        gm = genai.GenerativeModel(model)
        full = (system + "\n\n" + prompt) if system else prompt
        for chunk in gm.generate_content(full, stream=True):
            try: yield chunk.text
            except Exception: continue
    except Exception as e:
        yield f"\n[Gemini 오류] {e}"

# ─────────────────────────────────────────────────────────────────────
# 옵시디언 저장 (raw 방식만 — 추가 gemma 호출 없음)
# ─────────────────────────────────────────────────────────────────────
def _obs_save_raw(content: str, title: str, folder: str = "Chat") -> str:
    """Raw 모드 저장 — 범용 카테고리·키워드 태그 자동 생성"""
    try:
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_dir = OBSIDIAN_PATH / folder
        save_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c for c in title[:40] if c.isalnum() or c in " -_[]").strip()
        path = save_dir / f"{safe}_{ts}.md"

        wiki_links, hash_tags, cat_section = _build_obs_tags(content, title)

        md = f"""# {title}

## 메타데이터
- **저장 시각**: {today}
- **저장 폴더**: {folder}
- **저장 모드**: Raw

## 범용 카테고리 태그 (자동 분류)
{cat_section}

## 키워드 링크
{wiki_links}

## 해시 태그
{hash_tags}

---

## 📖 내용

{content}
"""
        path.write_text(md, encoding="utf-8")
        return str(path)
    except Exception as e:
        return f"[저장 실패] {e}"


def _obs_save_wiki(content: str, title: str, model: str, folder: str = "WikiNotes") -> str:
    """Wiki 모드 — Gemma가 구조화 후 범용 태그 포함 저장 (수동 전용)"""
    try:
        wiki_prompt = f"""아래 내용을 옵시디언 Wiki 노트 형식으로 구조화하라.
반드시 아래 섹션을 포함하라:
# [[{title}]]
## 📌 핵심 요약
## 🎯 핵심 개념
## 📖 주요 내용
## 💡 제작 활용 포인트 (유튜브 콘텐츠 관점)
## 🔗 연결 개념 ([[위키링크]] 형식)
## 📚 출처 및 참고

[원문]
{content[:1500]}"""
        wiki_md = call_gemma(wiki_prompt, model=model)
        if not wiki_md or len(wiki_md) < 30:
            wiki_md = content

        wiki_links, hash_tags, cat_section = _build_obs_tags(content, title)
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_dir = OBSIDIAN_PATH / folder
        save_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c for c in f"[WIKI] {title}"[:45] if c.isalnum() or c in " -_[]").strip()
        path = save_dir / f"{safe}_{ts}.md"
        full_md = f"""{wiki_md}

---

## 🏷️ 범용 카테고리 태그 (자동 분류)
{cat_section}

## 🔑 키워드 링크
{wiki_links}

## # 해시 태그
{hash_tags}

---
*[Wiki 변환: {today} / 모델: {model}]*
"""
        path.write_text(full_md, encoding="utf-8")
        return str(path)
    except Exception as e:
        return f"[Wiki 저장 실패] {e}"


def _obs_search_rag(query: str, max_files: int = 4, max_chars: int = 500) -> str:
    """옵시디언 볼트 키워드 검색 → RAG 컨텍스트 반환 (Gemma 시스템 프롬프트 주입용)"""
    if not OBSIDIAN_PATH.exists():
        return ""
    try:
        keywords = [w for w in query.lower().split() if len(w) > 1][:8]
        if not keywords:
            return ""
        scored = []
        for md_file in OBSIDIAN_PATH.rglob("*.md"):
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
                score = sum(text.lower().count(kw) for kw in keywords)
                if score > 0:
                    scored.append((score, md_file, text))
            except Exception:
                continue
        scored.sort(key=lambda x: x[0], reverse=True)
        parts = []
        for _, path, text in scored[:max_files]:
            parts.append(f"[{path.parent.name}/{path.stem}]\n{text[:max_chars]}")
        return "\n\n".join(parts)
    except Exception:
        return ""


def _auto_obs_save(response: str, prompt: str, model: str):
    """자동 저장 — raw 방식, gemma 추가 호출 없음 (속도 최적화)"""
    if not response or len(response) < 20: return
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        _obs_save_raw(
            f"## 질문\n{prompt}\n\n## 응답 ({model})\n{response}",
            f"[Chat] {prompt[:30].strip()}_{ts}",
            "Chat"
        )
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────────
# 허브 탭 함수들
# ─────────────────────────────────────────────────────────────────────
def _hub_research():
    st.caption("🔎 Tavily 웹 자료조사")
    tkey = st.session_state.get("tavily_api_key", "")
    if not tkey:
        st.warning("⚙️ 설정에서 Tavily API 키 입력 필요")
        return
    q = st.text_input("검색어", key="rp_tq", placeholder="예: 쇼펜하우어 의지론")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔎 검색", key="rp_tgo", use_container_width=True):
            if q.strip():
                with st.spinner("검색 중..."):
                    res = tavily_search(q.strip(), tkey)
                    if "results" in res:
                        ctx = "\n".join([f"- **{r.get('title','')}**: {r.get('content','')[:200]}" for r in res["results"][:4]])
                        st.session_state.rp_tavily_ctx = ctx
                        st.success(f"✅ {len(res['results'])}건")
                        with st.expander("결과"):
                            st.markdown(ctx)
    with c2:
        if st.button("🧠 옵시디언 저장", key="rp_tobs", use_container_width=True):
            ctx = st.session_state.get("rp_tavily_ctx","")
            if ctx:
                p = _obs_save_raw(ctx, f"[Tavily] {q}", "ResearchMemory")
                st.toast(f"저장: {Path(p).name if not p.startswith('[') else p}")


def _hub_app_research():
    st.caption("🔬 앱 리서치")
    if not _ROUTER_OK:
        st.warning("research_router 모듈 없음")
        return
    tkey = st.session_state.get("tavily_api_key","")
    kw = st.text_input("키워드", key="rp_rkw", placeholder="예: 빅터 프랭클 로고테라피")
    if st.button("🔬 실행", key="rp_rgo", use_container_width=True):
        if kw.strip() and tkey:
            with st.spinner("리서치 중..."):
                try:
                    results = run_tavily_research(kw.strip(), tkey)
                    md = format_search_results_markdown(results)
                    st.session_state.rp_tavily_ctx = md[:800]
                    st.markdown(md[:1200])
                    _obs_save_raw(md, f"[Research] {kw}", "ResearchMemory")
                    st.toast("💾 저장 완료!")
                except Exception as e:
                    st.error(f"오류: {e}")


def _hub_file_explorer():
    st.caption("📂 로컬 파일 탐색기")
    path_in = st.text_input("폴더 경로", value=st.session_state.rp_local_path, key="rp_lpin")
    if st.button("열기", key="rp_lopen"):
        st.session_state.rp_local_path = path_in
    p = Path(st.session_state.rp_local_path)
    if p.exists() and p.is_dir():
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        sel = st.selectbox("파일 선택", ["(선택)"] + [i.name for i in items], key="rp_fsel")
        if sel != "(선택)":
            sp = p / sel
            if sp.is_file() and sp.suffix.lower() in [".txt",".md",".py",".json",".csv"]:
                text = sp.read_text(encoding="utf-8", errors="ignore")
                st.text_area("미리보기", text[:800], height=100, key="rp_fprev")
                model = st.session_state.get("rp_model", RP_DEFAULT)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📝 Raw", key="rp_fraw"):
                        r = _obs_save_raw(text[:5000], f"[File] {sp.name}", "References")
                        st.toast(f"저장: {Path(r).name}")
                with c2:
                    if st.button("📖 Wiki", key="rp_fwiki"):
                        r = _obs_save_wiki(text[:3000], sp.stem, model, "WikiNotes")
                        st.toast(f"Wiki: {Path(r).name}")


def _hub_youtube():
    st.caption("📺 유튜브 채널 모니터")
    yt_key = st.session_state.get("youtube_api_key","")
    if not yt_key:
        st.warning("⚙️ 설정에서 YouTube API 키 입력 필요")
        return
    new_ch = st.text_input("채널 ID 추가", key="rp_ynew", placeholder="UCxxxxxx")
    if st.button("➕ 추가", key="rp_yadd"):
        ch = new_ch.strip()
        if ch and ch not in st.session_state.rp_yt_channels:
            st.session_state.rp_yt_channels.append(ch)
            _save_yt_channels(st.session_state.rp_yt_channels)
            st.rerun()
    for i, ch in enumerate(st.session_state.rp_yt_channels):
        c1, c2 = st.columns([4,1])
        with c1: st.code(ch, language=None)
        with c2:
            if st.button("🗑️", key=f"rp_ydel_{i}"):
                st.session_state.rp_yt_channels.pop(i)
                _save_yt_channels(st.session_state.rp_yt_channels)
                st.rerun()
    if st.session_state.rp_yt_channels:
        if st.button("🔄 체크 & 벤치마킹", key="rp_ycheck", use_container_width=True, type="primary"):
            _yt_check(yt_key)


def _yt_check(api_key: str):
    model = st.session_state.get("rp_model", RP_DEFAULT)
    items_all = []
    for ch_id in st.session_state.rp_yt_channels:
        try:
            r = requests.get(
                f"https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet&channelId={ch_id}&order=date&maxResults=3&key={api_key}&type=video",
                timeout=15
            ).json()
            for item in r.get("items", []):
                s = item.get("snippet",{})
                items_all.append(f"채널: {s.get('channelTitle',ch_id)}\n제목: {s.get('title','')}\n설명: {s.get('description','')[:200]}")
        except Exception as e:
            st.warning(f"[{ch_id}] 오류: {e}")
    if not items_all: st.warning("결과 없음"); return
    summary = "\n\n".join(items_all)
    with st.spinner("벤치마킹 분석 중..."):
        result = call_gemma(
            f"아래 최신 영상들을 분석하라:\n1. 공통 주제 패턴\n2. 후킹 제목 전략\n3. 우리 채널 적용 아이디어 3가지\n\n{summary[:2000]}",
            model=model
        )
    st.markdown(result)
    _obs_save_raw(f"## 영상 목록\n{summary}\n\n## 분석\n{result}", f"[YT벤치마킹] {datetime.now().strftime('%Y%m%d')}", "TopicMemory")
    st.toast("💾 옵시디언 저장 완료")


def _hub_obsidian():
    st.caption("🧠 옵시디언 듀얼 엔진")
    model = st.session_state.get("rp_model", RP_DEFAULT)

    # ── RAG 검색 ──────────────────────────────────────────────────
    st.markdown("**🔍 RAG 검색 (옵시디언 → 컨텍스트 주입)**")
    search_q = st.text_input("검색어", key="rp_osq", placeholder="예: 쇼펜하우어 고독")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 검색", key="rp_osgo", use_container_width=True):
            if search_q.strip():
                result = _obs_search_rag(search_q.strip(), max_files=5, max_chars=600)
                if result:
                    st.session_state.rp_tavily_ctx = result
                    st.success(f"✅ 관련 자료 발견 — 컨텍스트 주입됨")
                    with st.expander("검색 결과"):
                        st.markdown(result[:1000])
                else:
                    st.warning("관련 자료 없음")
    with c2:
        rag_on = st.toggle(
            "자동 RAG",
            value=st.session_state.get("rp_obs_rag_on", True),
            key="rp_orag_toggle",
            help="파트 전환 시 자동으로 옵시디언 검색 후 컨텍스트 주입"
        )
        st.session_state.rp_obs_rag_on = rag_on

    st.divider()

    # ── 저장 ──────────────────────────────────────────────────────
    st.markdown("**💾 저장 (Raw / Wiki)**")
    title = st.text_input("제목", key="rp_otitle", placeholder="예: 쇼펜하우어 정리")
    folder = st.selectbox("폴더", [
        "TopicMemory","ResearchMemory","ScriptDrafts",
        "WikiNotes","References","Chat","Part1_Librarian","Part2_Alchemist",
        "Logs","DarkPsychology"
    ], key="rp_ofolder")
    obs_content = st.text_area("내용", height=80, key="rp_ocontent")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Raw 저장", key="rp_oraw", use_container_width=True):
            if title and obs_content:
                p = _obs_save_raw(obs_content, title, folder)
                st.toast(f"📝 {Path(p).name}")
    with c2:
        if st.button("📖 Wiki 변환", key="rp_owiki", use_container_width=True):
            if title and obs_content:
                with st.spinner("Wiki 변환 중..."):
                    p = _obs_save_wiki(obs_content, title, model, folder)
                st.toast(f"📖 {Path(p).name}")


def _hub_obs_recent():
    st.caption("📖 최근 저장 노트")
    if not OBSIDIAN_PATH.exists():
        st.warning("옵시디언 경로 없음"); return
    try:
        files = sorted(OBSIDIAN_PATH.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:6]
        for f in files:
            ts = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d %H:%M")
            with st.expander(f"📄 {f.stem[:22]} ({ts})"):
                st.markdown(f.read_text(encoding="utf-8", errors="ignore")[:500])
                if st.button("📎 컨텍스트 추가", key=f"rp_oatt_{f.stem[:8]}"):
                    st.session_state.rp_tavily_ctx = f.read_text(encoding="utf-8", errors="ignore")[:600]
                    st.toast("✅ 컨텍스트 주입됨")
    except Exception as e:
        st.error(f"오류: {e}")


def _hub_app_editor():
    st.caption("✏️ 파트 결과물 수정")
    part_val = st.session_state.get("sidebar_part","파트 1")
    matched = None
    for label in APP_EDIT_KEYS:
        if label in part_val: matched = label; break
    if not matched: matched = "파트 1"
    keys_map = APP_EDIT_KEYS.get(matched, {})
    if not keys_map: st.caption("수정 가능 항목 없음"); return
    sel_label = st.selectbox("항목", list(keys_map.values()), key="rp_esel")
    sel_key = {v:k for k,v in keys_map.items()}.get(sel_label,"")
    current = str(st.session_state.get(sel_key,""))
    if current:
        st.text_area("현재 내용", current[:400], height=70, key="rp_ecur", disabled=True)
    inst = st.text_area("수정 지시", height=55, key="rp_einst", placeholder='예: "3번 주제 더 감성적으로"')
    model = st.session_state.get("rp_model", RP_DEFAULT)
    if st.button("✏️ 수정 생성", key="rp_ego", use_container_width=True, type="primary"):
        if inst.strip() and sel_key:
            with st.spinner("수정 중..."):
                new_val = call_gemma(f"지시: {inst}\n\n[원본]\n{current[:1500]}\n\n수정 내용만 출력:", model=model)
            if new_val and len(new_val) > 10:
                st.text_area("수정 결과", new_val[:600], height=100, key="rp_eprev")
                if st.button("✅ 적용", key="rp_eapply"):
                    st.session_state[sel_key] = new_val
                    st.toast(f"✅ {sel_label} 수정 완료")
                    st.rerun()


def _hub_settings():
    st.caption("⚙️ 설정")
    for label, key in [("Gemini API 키","gemini_api_key"),("Tavily API 키","tavily_api_key"),("YouTube API 키","youtube_api_key")]:
        val = st.text_input(label, type="password", value=st.session_state.get(key,""), key=f"rp_s_{key}")
        if val != st.session_state.get(key,""):
            st.session_state[key] = val
    st.divider()
    st.caption("브레인 모델 선택")
    st.markdown(
        "<small>"
        "<b>gemma4:e2b</b> — 로컬 기본 브레인 (오프라인 작동)<br>"
        "<b>gemma4:e4b</b> — 로컬 강화 브레인 (오프라인, 더 강력)<br>"
        "<b>gemini-2.5-flash</b> — 자료조사 보조 (인터넷 필요)"
        "</small>",
        unsafe_allow_html=True
    )
    sel = st.selectbox("모델 선택", RP_MODELS, index=RP_MODELS.index(st.session_state.rp_model) if st.session_state.rp_model in RP_MODELS else 0, key="rp_smsel")
    st.session_state.rp_model = sel
    st.divider()
    st.caption("Gemma 파라미터")
    st.session_state["popup_num_predict"] = st.slider("max tokens", 128, 1024, st.session_state.get("popup_num_predict",400), 64, key="rp_snp")
    st.session_state["popup_temperature"] = st.slider("temperature", 0.0, 1.0, st.session_state.get("popup_temperature",0.3), 0.05, key="rp_stmp")
    st.divider()
    if st.button("🗑️ 대화 기록 초기화", key="rp_sclear", use_container_width=True):
        st.session_state.rp_history = []
        try: CHAT_JSON.unlink() if CHAT_JSON.exists() else None
        except Exception: pass
        st.toast("🗑️ 초기화 완료")
        st.rerun()

# ── 허브 탭 맵 ──────────────────────────────────────────────────────
_HUB_TABS = {
    "🔎 자료조사": _hub_research,
    "🔬 앱리서치": _hub_app_research,
    "📂 파일":     _hub_file_explorer,
    "📺 유튜브":   _hub_youtube,
    "🧠 옵시디언": _hub_obsidian,
    "📖 최근저장": _hub_obs_recent,
    "✏️ 앱수정":   _hub_app_editor,
    "⚙️ 설정":     _hub_settings,
}

def _render_hub():
    with st.container(border=True):
        cols = st.columns(len(_HUB_TABS))
        for i, (label, _) in enumerate(_HUB_TABS.items()):
            with cols[i]:
                is_active = st.session_state.rp_hub_tab == label
                if st.button(label, key=f"rp_hb_{i}", use_container_width=True,
                              type="primary" if is_active else "secondary"):
                    st.session_state.rp_hub_tab = "" if is_active else label
                    st.rerun()
        active = st.session_state.rp_hub_tab
        if active and active in _HUB_TABS:
            st.divider()
            _HUB_TABS[active]()

# ─────────────────────────────────────────────────────────────────────
# 메인 렌더링
# ─────────────────────────────────────────────────────────────────────
def render_right_panel():
    _rp_init()
    st.markdown(_CSS, unsafe_allow_html=True)

    # 파트 이름 (짧게)
    part_val = st.session_state.get("sidebar_part","파트 1")
    part_short = part_val.split(":")[0].strip() if ":" in part_val else part_val[:6]

    # ── 헤더 ──────────────────────────────────────────────────────
    hc1, hc2 = st.columns([3, 2])
    with hc1:
        st.markdown('<div class="rp-hdr">⬡ SAGE 브레인</div>', unsafe_allow_html=True)
    with hc2:
        st.markdown(f'<div class="rp-part-badge" style="text-align:center">📍 {part_short}</div>', unsafe_allow_html=True)

    # ── 허브 패널 ─────────────────────────────────────────────────
    if st.session_state.rp_hub_open:
        _render_hub()

    # ── 채팅 영역 ─────────────────────────────────────────────────
    chat_h = 360 if st.session_state.rp_hub_open else 520
    chat_box = st.container(height=chat_h)

    with chat_box:
        if not st.session_state.rp_history:
            st.markdown(
                "<div style='color:#3a2a4a;text-align:center;margin-top:100px;font-size:0.85rem;'>"
                "현자에게 무엇이든 물어보세요 🤖</div>",
                unsafe_allow_html=True,
            )

        # 기존 이력 표시
        for i, msg in enumerate(st.session_state.rp_history):
            with st.chat_message(msg["role"], avatar="🧑" if msg["role"]=="user" else "🤖"):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    st.caption(f"_{msg.get('ts','')[:16]}_")
                    if st.button("□ 복사", key=f"rp_cp_{i}"):
                        try:
                            esc = msg["content"].replace("`","\\`").replace("$","\\$")
                            st.html(f"<script>navigator.clipboard.writeText(`{esc}`);</script>")
                            st.toast("📋 복사됨")
                        except Exception: pass

        # ── 스트리밍 처리 ──────────────────────────────────────────
        if st.session_state.rp_pending_prompt:
            _prompt = st.session_state.rp_pending_prompt
            _model  = st.session_state.rp_model
            _sys    = _build_brain_prompt()

            with st.chat_message("assistant", avatar="⚙️"):
                st.markdown(
                    '<div class="rp-loading">'
                    '<span class="rp-loading-icon">⚙️</span> 생성 중...</div>',
                    unsafe_allow_html=True,
                )
                try:
                    if _model.startswith("gemma"):
                        _gen = _stream_gemma(_prompt, _sys, _model)
                    else:
                        _gen = _stream_gemini(_prompt, _sys, _model)
                    _resp = st.write_stream(_gen)
                except Exception as e:
                    _resp = f"[오류] {e}"
                    st.error(_resp)

            st.session_state.rp_history.append({
                "role": "assistant", "content": _resp,
                "model": _model, "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            st.session_state.rp_pending_prompt = None
            _save_chat_json()
            _auto_obs_save(_resp, _prompt, _model)
            st.rerun()

    # ── Gemini 스타일 1줄 입력창 ─────────────────────────────────
    inp_key = f"rp_input_{st.session_state.rp_send_key}"
    st.markdown('<div class="rp-input-wrap">', unsafe_allow_html=True)
    col_plus, col_input, col_model, col_send = st.columns([0.5, 5, 2, 0.6], gap="small")

    with col_plus:
        if st.button("＋", key="rp_hub_toggle", help="기능 허브"):
            st.session_state.rp_hub_open = not st.session_state.rp_hub_open
            if not st.session_state.rp_hub_open:
                st.session_state.rp_hub_tab = ""
            st.rerun()

    with col_input:
        _prompt_val = st.text_area(
            "입력", key=inp_key,
            placeholder="현자에게 물어보세요...",
            label_visibility="collapsed",
            height=44, max_chars=4000,
        )

    with col_model:
        _sel = st.selectbox(
            "모델", RP_MODELS,
            index=RP_MODELS.index(st.session_state.rp_model) if st.session_state.rp_model in RP_MODELS else 0,
            key="rp_msel", label_visibility="collapsed",
        )
        st.session_state.rp_model = _sel

    with col_send:
        _send = st.button("↑", key="rp_send_btn", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 전송 처리 ────────────────────────────────────────────────
    if _send and _prompt_val and _prompt_val.strip():
        st.session_state.rp_history.append({
            "role": "user", "content": _prompt_val.strip(),
            "model": st.session_state.rp_model,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        st.session_state.rp_pending_prompt = _prompt_val.strip()
        st.session_state.rp_send_key += 1
        st.rerun()

    # ── 상태 표시 ────────────────────────────────────────────────
    if st.session_state.get("rp_tavily_ctx"):
        st.caption("🔗 웹 자료 컨텍스트 주입 중")
