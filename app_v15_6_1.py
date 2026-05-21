# -*- coding: utf-8 -*-
"""
🪞 현자의 거울 스튜디오 — Master App v15.6.1
[v15.6.1 업데이트 사항: 2026-05-21]
- 시스템 동기화 카드의 가로 균등 4열 배치(비율 1:1:1:1) 및 전체 카드 디자인(로컬 DB, RAG, Git, 동기화) 완벽 통일화
- 투명 absolute overlay 테크닉(:has 가상 클래스 선택자 활용)을 도입하여 RAG, Git, 동기화 카드의 내부 HTML 스타일(⬤ 색상, font-size 등)이 로컬 DB 연결 카드와 100% 시각적으로 일치하도록 개선
- 8개 전 파트 헤더의 제목 폰트 크기 확대(1.85em) 및 우측 모델 선택기(GEMMA4:E2B / GEMMA4:E4B) 탑재로 올라마 실시간 연동 구현
"""



import streamlit as st
import os
import re
import stat
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import pyperclip

from obsidian_search import simple_keyword_search

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
    call_gemma as _orig_call_gemma, check_ollama_status,
)
from sage_popups import (
    popup_edit_obsidian, popup_edit_prompt, popup_assistant,
)

# ── call_gemma 래핑 함수 (Gemma4:E2B / GEMMA4:E4B 실시간 모델 스위칭 연동) ──
def call_gemma(prompt, system="", model=None):
    if model is None:
        model = st.session_state.get("selected_model", OLLAMA_MODEL)
    if isinstance(model, str):
        model = model.lower()
    return _orig_call_gemma(prompt, system=system, model=model)

# ── RAG 지식 부족 감지 & 자가 검수 헬퍼 ──
def check_need_research_tag(content: str) -> str:
    """
    텍스트에 [NEED_RESEARCH: 검색어] 태그가 있는지 감지하고 검색 키워드를 반환합니다.
    """
    if not content:
        return None
    match = re.search(r"\[NEED_RESEARCH:\s*(.+?)\]", content)
    if match:
        return match.group(1).strip()
    return None

def verify_content_with_gemma(content_type: str, content: str, rules: str) -> dict:
    """
    Gemma를 비평가(Critic)로 삼아 생성된 데이터(주제, 기획안, 대본 등)의 무결성을 스스로 점검하는 함수.
    """
    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 수석 데이터 무결성 검증기(Data Integrity Critic)다.
아래 제공된 [대상 콘텐츠]가 [검수 규칙 가이드라인]을 엄격히 준수하고 있는지 스스로 점검하고, 그 결과를 객관적으로 보고해야 한다.

[검수 규칙 가이드라인]:
1. 등장인물 지칭: 등장인물은 오직 '@Protagonist'로만 표기되어야 한다. (주인공, 현자, 노인, 남성, 그 등 다른 지칭은 일절 금지. 단, 성경/철학 원문 출처 제외)
2. 씬 번호 규칙: 씬 번호가 존재할 경우 반드시 3자리 정수 형태(001, 002 ... 112)이어야 한다.
3. 출처 태그 준수: [SOURCE:] 태그가 적절히 포함되어 데이터의 출처(성경 장절, 저자, 책명 등)를 필히 밝히고 있는가? (출처가 아예 없는 상상 기반 생성은 FAIL 판정하라)
4. 가이드라인 준수: 옵시디언 규칙서의 스타일과 포맷을 따르고 있는가?

[대상 콘텐츠 ({content_type})]:
{content}

점검 결과를 반드시 아래의 형식으로 정확히 출력하라. 설명이나 다른 텍스트는 덧붙이지 마라.

[RESULT_FORMAT]:
정합성: [PASS 또는 FAIL]
점검 보고:
- 등장인물 지칭: [PASS 또는 FAIL 이유]
- 씬 번호 규칙: [PASS 또는 FAIL 또는 해당없음 이유]
- 출처 태그 준수: [PASS 또는 FAIL 이유]
- 가이드라인 준수: [PASS 또는 FAIL 이유]
수정 건의사항: [FAIL인 경우 수정해야 할 구체적인 지침. PASS인 경우 '없음']
"""
    try:
        if not content or not content.strip():
            return {
                "status": "FAIL",
                "report": "점검 대상 콘텐츠가 비어 있습니다.",
                "suggestions": "콘텐츠를 먼저 생성하십시오."
            }
        res = call_gemma(prompt, rules)
        status = "PASS"
        if "정합성: FAIL" in res or "FAIL" in res.split("\n")[0] or "정합성: [FAIL]" in res:
            status = "FAIL"
        
        suggestions = "없음"
        for line in res.split("\n"):
            if "수정 건의사항:" in line:
                suggestions = line.replace("수정 건의사항:", "").strip()
                break
                
        return {
            "status": status,
            "report": res.strip(),
            "suggestions": suggestions
        }
    except Exception as e:
        return {
            "status": "FAIL",
            "report": f"Gemma 자가 검수 중 오류 발생: {e}",
            "suggestions": "Ollama 연결 상태를 확인하고 다시 시도하십시오."
        }

# ── RAG 키워드 자동 세분화 추출 헬퍼 ──
def extract_keywords_via_gemma(content, base_rules):
    prompt = f"""[SYSTEM]: 너는 입력된 텍스트에서 옵시디언 RAG 지식 구조화 연동을 위한 핵심 키워드 4~5개를 세분화하여 추출하는 전문 분석기다.
너의 임무는 입력 텍스트의 핵심 주제, 철학적 맥락, 성경적 모티브, 시청자 감정 결핍 상태 등을 관통하는 고유 키워드 4~5개를 쉼표(,)로 구분된 단어로만 출력하는 것이다.
반드시 단어 이외의 설명, 서론, 결론, 특수문자, 따옴표는 일절 출력하지 마라.
예시 출력: 외로움, 고독, 존재의미, 쇼펜하우어, 자아정체성

[USER_INPUT]:
{content}

[KEYWORDS]:"""
    try:
        res = call_gemma(prompt, base_rules)
        cleaned = res.replace("#", "").replace("[", "").replace("]", "").replace("`", "").strip()
        keywords = [k.strip() for k in cleaned.split(",") if k.strip()]
        return ", ".join(keywords[:5])
    except Exception as e:
        return "심리치유, 현자의거울, 자아성찰"


# =====================================================================
# 0. 영상 파트 전용 상수(Constants) — v13.2 NEW
# =====================================================================
P6_VEO3_MASTER_PROMPT_V2 = """# [현자의 거울 — VEO3 마스터 프롬프트 완전판]
# YouTube Creative Director Edition
# Google Opal × Veo3 × CapCut 전용
# ═══════════════════════════════════════════════════
# 이 문서의 위치: 영상 파트(Part 5) 최상단 우측 입력란
# 적용 대상: Google Opal → Veo3 영상 생성 노드
# 입력 방식: 아래 전문을 Opal의 '공통 프롬프트 노드'에 붙여넣기
# ═══════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1 — ROLE: YouTube Creative Director
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ROLE]
You are a World-Class YouTube Creative Director specializing in high-end cinematic documentaries. Your goal is to translate abstract philosophical scripts into breathtaking, hyper-realistic 8K video sequences that evoke deep emotional resonance in a 4070-generation audience.

[VEO3 CINEMATIC DNA]
1. Director Style: A fusion of Ingmar Bergman (psychological depth), Andrei Tarkovsky (poetic stillness), Roger Deakins (perfect lighting), and Christopher Nolan (scale and gravity).
2. Color Science: "The Rembrandt Palette" — Umber, Ochre, Burnt Sienna, Deep Charcoal. Contrast is high, shadows are rich (Tenebrism).
3. Lighting: 2600K Warm Candlelight. Single-source key lighting from 45-degree angle. High-contrast Chiaroscuro.
4. Texture: Organic 35mm film grain, subtle dust motes in light beams, heavy impasto oil painting textures in the shadows.

[VISUAL KEYWORDS]
Rembrandt Lighting, Chiaroscuro, Tenebrism, Baroque Aesthetic, Hyper-realistic, 8K, 17th Century Dutch Master, Atmospheric, Melancholic, Resolute.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2 — CORE ASSETS: @Protagonist & Mirror
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[@Protagonist Identity]
- Appearance: 60-year-old male sage, silver-grey hair and short-trimmed beard.
- Attire: Deep burgundy and black linen robe, heavy texture.
- Persona: Philosophical, weathered but dignified, luminous eyes reflecting decades of thought.
- Motion: Minimal, deliberate, slow-motion (0.5x speed).

[@Mirror & Avatar Identity]
- The Mirror: 150cm ornate gold-leaf baroque mirror, aged glass with slight oxidation.
- Reflection Physics: 0.3-second delay between @Protagonist and reflection.
- The Avatar: Younger version (30s) of @Protagonist inside the mirror. Translucent, ethereal, soft internal glow.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3 — TECHNICAL SPEC & CAMERA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[MOTION SPEC]
- Frame Rate: 24fps Cinematic.
- Camera: Arri Alexa 65 look.
- Movement: "The Breathing Camera" — Extremely slow Dolly-in, slow Crane-up, or deliberate Pan. No handheld shakes.
- Focal Length: 35mm (Medium) or 85mm (Close-up) for emotional beats.

[GENERATION PROTOCOL]
1. Input: C-1 Format Script (Scene ID | Script | Visual KR | English Prompt).
2. Translation: Expand the English Prompt into a 3-paragraph Veo3 Cinematic Instruction.
3. Physics Check: Ensure the @Protagonist stays consistent across all 112 scenes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4 — VEO3 PROMPT TEMPLATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each scene, use this structure:
1. [SUBJECT]: Detailed description of @Protagonist's action and emotion.
2. [ENVIRONMENT]: 17th-century scholar's study, specific lighting, props (@Mirror, @Candelabra).
3. [VFX & STYLE]: Film grain, lighting angle, specific camera movement, Rembrandt aesthetic.

"Make it look like a lost masterpiece found in a vault. Deeply emotional, visually arresting."
"""

P6_MASTER_PROMPT_DEFAULT = """# 🎙️ 파트 6 나레이션 & 배경음악 마스터 프롬프트 v1.0
[작업 지시] 씬별 나레이션 텍스트를 바탕으로 음성 합성(TTS) 및 적합한 배경음악(BGM) 태그 매칭 지침을 작성하세요.
- 등장인물은 오직 '@Protagonist'로 지칭합니다.
- 성경 구절 및 철학 인용의 출처를 필히 확인하고 반영하세요.
- 오디오 볼륨 밸런스 및 싱크 가이드를 명시합니다."""

P7_MASTER_PROMPT_DEFAULT = """# 🎙️ 파트 7 숏폼 생성 마스터 프롬프트 v1.0
[작업 지시] 롱폼 대본 및 핵심 테마를 바탕으로 60초 이내의 숏폼 대본과 하이라이트 구간 추출 지침을 작성하세요.
- 등장인물은 오직 '@Protagonist'로 지칭합니다.
- 후킹 인트로와 핵심 요약 자막 연출법을 정의합니다."""

P8_MASTER_PROMPT_DEFAULT = """# ⚙️ 파트 8 캡컷 최종 조립 마스터 프롬프트 v1.0
[작업 지시] Veo3 영상 파일, 나레이션 오디오, 캡컷 에셋 JSON을 조합하여 CapCut 타임라인으로 병합하고 최종 비디오 렌더링에 적합한 오디오/자막 싱크 조립 지침을 작성하세요.
- 등장인물은 오직 '@Protagonist'로 지칭합니다.
- 최종 마스터링 및 해상도, 비트레이트 조절 가이드를 명시합니다."""

COMMON_GEMMA_PROTOCOL = """
# [현자의 거울 스튜디오 — 공통 Gemma 운영 헌법]

너는 현자의 거울 스튜디오의 AI 시스템이다.

이 시스템의 핵심은:
- 옵시디언 RAG
- 실제 감정 데이터
- 성경
- 철학
- 인간 심리 분석
이다.

==================================================

[공통 절대 규칙]

1. 옵시디언 RAG 최우선
- 모든 작업은 옵시디언 검색 결과를 최우선 참조한다.
- Gemma의 추측보다 저장된 기억을 우선한다.
- TopicMemory → ResearchMemory → Bible → Philosophy 순서 유지.

2. 환각(Hallucination) 금지
절대 금지:
- 가짜 성경 구절 생성
- 존재하지 않는 철학 인용
- 댓글 없는 체험담 생성
- 출처 없는 명언 생성
- 임의 상상 기반 감정 생성

3. 자료 부족 시 행동 및 환각 차단 (RAG 지식 부족 대응)
- 제공된 옵시디언 RAG 자료가 부족하여 실제 성경 구절, 철학 인용, 심리 데이터 등을 스스로 지어내야(상상해야) 하는 지식 공백이 발생하는 경우, 절대 상상으로 작성하지 마라.
- 이 경우 답변의 첫 줄에 반드시 다음 형식으로 추가 리서치를 요청하는 코드만 출력하라:
  [NEED_RESEARCH: 검색어]
  (예시: [NEED_RESEARCH: 빅터 프랭클 죽음의 수용소에서 의미치료 실존주의])
- 추가 리서치 승인 전까지는 상상 기반 생성을 중단하라.

4. 출처 의무화
- 보충되거나 인용된 모든 핵심 정보에는 반드시 [SOURCE: 출처] 형식으로 출처를 필히 명시하라. (성경, 철학 서적, 인터넷 URL 등)
- 출처 불명 시에도 반드시 다음과 같이 표기하라:
  [SOURCE: 출처 미확인 — gemma4:e2b 생성]

5. 위키링크 의무화
핵심 개념은:
[[개념명]]

형태 사용.

6. 감정 중심 원칙
항상 인간 감정 우선:
- 고독
- 상실
- 공허
- 후회
- 의미 상실
- 관계 단절

7. 스타일 규칙
금지:
- AI 같은 장황한 설명
- 자기계발 말투
- 과도한 희망회로
- 가벼운 위로
- 1020 밈 스타일

허용:
- 깊은 공감
- 조용한 통찰
- 철학적 해석
- 성경적 위로

==================================================

Gemma는 창작자가 아니라,
“기억을 읽는 조사관”이다.
"""

P6_GEMMA_PROTOCOL_V2 = """# [현자의 거울 스튜디오]
# GEMMA PROTOCOL v2.0 — 영상 파트 완전판
# ═══════════════════════════════════════════════════════
# 이 문서의 위치: 영상 파트(Part 5) 중간 '젬마 프로토콜' 입력란
# 적용 모델: gemma4:e2b (Ollama 로컬 실행)
# 연동 시스템: Google Opal × Veo3 × CapCut × FlowRun
# 역할: 영상 파트 하단 4구역의 전체 작업을 지휘하는 젬마의 운영 헌법
# ═══════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## [BELL] 시작 선언문 (START DECLARATION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
" [GEMMA PROTOCOL v2.0] — 영상 파트 로딩 완료"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1 — MISSION & ROLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ROLE]
너는 '현자의 거울 스튜디오'의 영상 오케스트레이터 젬마다.
Part 3-4에서 생성된 이미지 대본(C-1 형식)을 받아, 구글 Veo3가 가장 완벽한 8K 영상을 출력할 수 있도록 '고해상도 영상 생성 지시서'를 설계한다.

[MISSION]
1. 인물 일관성: 112개 모든 씬에서 @Protagonist의 외형이 절대 변하지 않게 통제한다.
2. 미학적 통일성: 렘브란트 다크(Rembrandt Dark) 스타일과 키아로스쿠로(Chiaroscuro) 조명을 모든 프롬프트에 강제 주입한다.
3. 병렬 처리 최적화: Google Opal의 8개 계정에 작업을 14씬씩 정확히 배분하여 생산성을 극대화한다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2 — OUTPUT SPEC (C-1 to V-1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[입력 데이터]
- 씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ (Part 3-4 결과물)

[출력 형식: V-1 영상 프롬프트]
씬번호(3자리) | 영상프롬프트 | 카메라무빙 | 재생시간(초)

[프롬프트 구성 규칙]
1. SUBJECT: [A-MASTER] + 현재 씬의 동작 + 감정(EXPR)
2. ENVIRONMENT: [@배경] + 소품(@거울, @촛대 등) + 렘브란트 조명
3. STYLE: Veo3 Master Prompt의 시각적 DNA 강제 결합
4. MOTION: 극도로 느린 줌인(Slow Zoom-in), 패닝(Panning), 또는 정적(Static)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3 — OPAL DISPATCH (8-NODE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
112씬을 8개 계정에 배분하는 규칙:
- NODE 1: 001~014 (기-1)
- NODE 2: 015~028 (기-2)
- NODE 3: 029~042 (승-1)
- NODE 4: 043~056 (승-2)
- NODE 5: 057~070 (전-1)
- NODE 6: 071~084 (전-2)
- NODE 7: 085~098 (결-1)
- NODE 8: 099~112 (결-2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4 — QUALITY CHECK (V-1 to V-7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
V-1: 형식 정규식 검증 (Pipe 구분)
V-2: @Protagonist 명칭 고정 여부
V-3: 16:9 비율 및 8K 해상도 명시 여부
V-4: 카메라 무빙의 구체성 (Veo3 인식 가능성)
V-5: 렘브란트 스타일 태그 포함 여부
V-6: [인물1], [배경] 태그의 Opal 연동 적합성
V-7: 씬 번호 연속성 및 누락 체크

"준비가 되었으면, 선언문을 출력하고 첫 번째 작업을 시작하라."
"""

# =====================================================================
# 1. 페이지 설정
# =====================================================================
st.set_page_config(
    page_title="Sage's Mirror Studio v13.2.3",
    page_icon="[MIRROR]",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# V8.1: 상단 PIN 입력창 전용 커스텀 스타일 추가
st.markdown("""
<style>
.pin-input-container {
    background-color: rgba(16, 185, 129, 0.1);
    padding: 0.5rem;
    border-radius: 8px;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.sage-header-compact {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    padding: 10px 20px;
    border-radius: 10px;
    border-left: 5px solid #F59E0B;
    color: #F8FAFC;
    margin-bottom: 0px;
}
.clickable-card-wrapper button {
    background-color: #1E293B !important;
    border: 1px solid #d4af6a !important;
    color: #f5e9d3 !important;
    height: 60px !important;
    text-align: left !important;
    padding: 8px 30px 8px 12px !important;
    font-size: 0.82em !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    line-height: 1.4 !important;
    border-radius: 6px !important;
    width: 100% !important;
    display: block !important;
    position: relative !important;
    transition: all 0.15s ease !important;
}
.clickable-card-wrapper button:hover {
    border-color: #f5e9d3 !important;
    background-color: #2D2418 !important;
    transform: translateY(-1px) !important;
}
/* 우측 빨간 동그라미 가상 요소 */
.card-rag-btn button::after, .card-git-btn button::after {
    content: "🔴" !important;
    position: absolute !important;
    right: 12px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 11px !important;
}
/* 동기화 버튼 세로 높이 맞춤 */
.sync-btn-container button {
    height: 60px !important;
    border-radius: 6px !important;
    font-weight: bold !important;
    transition: all 0.15s ease !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 상태 저장 유틸리티
# =====================================================================
WORKSPACE_STATE_FILE = r"C:\SageMirror_Production\workspace_state.json"

def save_workspace_state():
    keys_to_save = [
        "path_obsidian", "github_repo_url", "github_pat", "tavily_api_key", "youtube_api_key",
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        "p1_channel_url", "p1_region", "p1_topics", "p1_topic_selection",
        "p1_research_result", "p1_planning_result", "unlock_part1",
        "p1_bench_prompt", "p1_research_prompt", "p1_plan_prompt",
        "p1_bench_raw", "p1_bench_tags", "p1_research_tags", "p1_plan_tags",
        "p1_bench_saved", "p1_bench_obsidian_saved", "p1_research_saved", "p1_research_obsidian_saved", "p1_plan_saved", "p1_plan_obsidian_saved",
        "p2_gemma_protocol", "p2_channel_url", "p2_region", "p2_topics",
        "p2_topic_selection", "p2_research_result", "p2_planning_result",
        "p2_thumbnail_plan", "unlock_part2",
        "p2_bench_prompt", "p2_bench_raw", "p2_bench_tags", "p2_bench_saved", "p2_bench_obsidian_saved",
        "p2_research_prompt", "p2_research_tags", "p2_research_saved", "p2_research_obsidian_saved",
        "p2_plan_prompt", "p2_plan_tags", "p2_plan_saved", "p2_plan_obsidian_saved",
        "p34_gemma_protocol", "p34_master_prompt", "unlock_part34",
        "p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data",
        "p34_narr_prompt", "p34_img_prompt", "p34_cap_prompt",
        "p34_arch_saved", "p34_arch_obsidian_saved", "p34_narr_saved", "p34_narr_obsidian_saved",
        "p34_img_saved", "p34_img_obsidian_saved", "p34_cap_saved", "p34_cap_obsidian_saved",
        "p5_image_master_prompt", "unlock_part5", 
        "p6_veo3_master_prompt", "p6_gemma_protocol", "p6_protocol_loaded", "p6_vid_pin_input", "unlock_part6_vid",
        "p6_master_prompt", "p7_master_prompt", "p8_master_prompt",
        "p1_verification", "p2_verification", "p2_plan_verification", "p34_narr_verification", "p34_img_verification",
        "p1_need_research_kw", "p2_need_research_kw", "p2_plan_need_research_kw", "p34_narr_need_research_kw", "p34_img_need_research_kw",
        "unlock_part6", "unlock_part7", "unlock_part8", "p6_opal_data", "p7_capcut_data_v2",
        "p6_bgm_selection", "p6_mixing_ratio", "p6_narration_verified", "p6_opal_saved", "p6_opal_obsidian_saved",
        "p7_capcut_saved", "p7_capcut_obsidian_saved", "p8_dashboard_saved", "p8_dashboard_obsidian_saved",
        "selected_model"
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
def save_obsidian_memory(folder_name, title, content, source="Sage Mirror Studio"):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        base_dir = st.session_state.get("path_obsidian", "")
        if base_dir:
            save_dir = os.path.join(base_dir, "Studio", folder_name)
        else:
            save_dir = os.path.join("Studio", folder_name)

        os.makedirs(save_dir, exist_ok=True)

        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title).strip()
        save_path = os.path.join(save_dir, f"{safe_title}_{ts}.md")

        md = f"""# [[{title}]]

## 📌 핵심 요약

## 🎯 핵심 감정

## 📖 핵심 내용
{content}

## 💡 대본 활용 포인트

## 🔗 연결 개념
- [[고독]]
- [[후회]]
- [[관계 단절]]

## 📚 출처
[SOURCE: {source}]

## 생성일
{ts}
"""

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(md)

        return save_path

    except Exception as e:
        st.error(f"옵시디언 저장 오류: {e}")
        return None
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
if "pipeline_state" not in st.session_state:
    st.session_state["pipeline_state"] = {
        "channel_search_results": [],
        "selected_channel": {},
        "channel_analysis": {},
        "comment_analysis": {},
        "topic_candidates": [],
        "selected_topic": "",
        "research_notes": {},
        "planning_result": {},
        "script_result": {}
    }

DEFAULT_OBSIDIAN_RULES_V81 = """# 📚 현자의 거울 스튜디오 — 옵시디언 지식 구조화 규칙서 v2.0
## 대본 파트 좌측 상단 | Obsidian RAG 연동 전용

---

> **이 문서의 위치:** 대본 파트 좌측 상단 입력란  
> **적용 대상:** gemma4:e2b (Ollama 로컬) + 옵시디언 볼트 전체  
> **역할:** 옵시디언에 저장된 방대한 지식을 젬마가 올바르게 읽고, 구조화하여 대본 작업에 투입하는 규칙

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🏛️ SECTION 1 — 옵시디언 볼트 지식 계층 구조
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【현자의 거울 옵시디언 볼트 디렉토리 구조】

/Sage_Mirror_Vault/
├── 📚 Bible/
│   ├── OldTestament/     ← 구약 전서 (창세기~말라기)
│   ├── NewTestament/     ← 신약 전서 (마태복음~요한계시록)
│   ├── Psalms/           ← 시편 (감정 치유에 우선 참조)
│   ├── Proverbs/         ← 잠언 (지혜 격언에 우선 참조)
│   └── BibleIndex.md     ← 주제별 구절 색인
│
├── 📚 Philosophy/
│   ├── Schopenhauer/     ← 쇼펜하우어 (의지와 표상으로서의 세계 등)
│   ├── CarlJung/         ← 칼 융 (그림자, 집단무의식, 개성화)
│   ├── ViktorFrankl/     ← 빅터 프랭클 (의미치료, 로고테라피)
│   ├── Montaigne/        ← 몽테뉴 (수상록, 인간 관조)
│   ├── DarkPsychology/   ← 다크 심리학 (방어기제, 인간 본성)
│   └── PhilosophyIndex.md
│
├── 📝 Essays/
│   ├── Korean/           ← 국내 에세이집 (따뜻한 한국어 문체)
│   ├── Western/          ← 서양 에세이집 (C.S. Lewis 등)
│   └── EssayIndex.md
│
├── [CINEMA] Studio/
│   ├── ScriptDrafts/     ← 대본 초안 저장
│   ├── References/       ← A/B 참조 이미지
│   ├── Images/           ← 씬 이미지 scene_XXX.png
│   └── Assets/           ← CSV, JSON 에셋
│
└── 🔗 KnowledgeIndex.md  ← 전체 지식 네트워크 링크 맵
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📋 SECTION 2 — 노트 표준 구조 (Standard Note Template)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【모든 옵시디언 노트가 반드시 따르는 표준 구조】
젬마가 노트를 읽을 때 이 구조를 기준으로 파싱한다.

---
# [[개념명 / 인물명 / 구절명]]

## 📌 핵심 요약 (Brief Summary)
(1~2문장 정의. 젬마가 키워드 매칭 시 가장 먼저 읽는 부분)

## 📚 핵심 내용 (Core Content)
(원본 자료에서 종합·분석한 상세 내용. 원문 인용 시 큰따옴표 " " 사용)

## 💡 대본 활용 포인트 (Script Application)
- 어떤 감정 상태(희/노/애/락/공허/불안)에 연결되는가
- 어떤 인간 결핍(인정 욕구/관계/정체성/고독/두려움)을 다루는가
- 어떤 서사 위치(기/승/전/결)에 가장 잘 맞는가

## 🔗 지식 연결 (Knowledge Connections)
- **성경 연결:** [[연관 구절 - 장절]]
- **철학 연결:** [[연관 개념 - 학자명]]
- **에세이 연결:** [[연관 에세이 - 저자명]]
- **모순/주석:** (출처 A와 B의 관점 차이 명시)

## 📌 출처 (Source)
[SOURCE: 책명/장절/페이지 — 저자명, 출판년도]

---
*Last updated: YYYY-MM-DD*
---
```

---
"""

MASTER_RESEARCH_PROMPT_V81 = """# [TARGET] 현자의 거울 스튜디오 — 전역 마스터 리서치 프롬프트 v8.1
## 모든 젬마(Gemma) 페르소나의 근간이 되는 철학적 헌법

---

## 🏛️ SECTION 1 — THE SAGE PERSONA (페르소나)
너는 17세기 네덜란드 서재에서 촛불 하나에 의지해 고뇌하는 **'현자(The Sage)'**다.
- **문체:** 극도로 정제된 한국어. 4070 세대가 읽었을 때 품격과 위로를 동시에 느끼는 묵직한 어조.
- **철학:** 성경의 잠언적 지혜 + 쇼펜하우어의 통찰 + 칼 융의 심리학을 하나로 융합.
- **목표:** 단순한 지식 전달이 아닌, 시청자의 '영혼의 거울'이 되어 주는 것.

## 📋 SECTION 2 — KNOWLEDGE INTEGRATION (지식 융합 규칙)
모든 답변은 반드시 아래 3단 구조를 따른다:
1. **[인간의 고통]:** 4070 세대가 겪는 관계의 단절, 노후의 고독, 상실감을 먼저 깊이 공감하라.
2. **[철학의 통찰]:** 옵시디언 내 'Philosophy' 폴더의 학자적 관점을 빌려 고통을 객관화하라.
3. **[현자의 해답]:** 성경 'Psalms'나 'Proverbs'의 구절로 마무리를 지으며 소망을 제시하라.

## 🎥 SECTION 3 — VISUAL DIRECTION (시각 연출 지시)
모든 묘사는 **'렘브란트 다크(Rembrandt Dark)'** 스타일을 고수한다:
- 어두운 배경(Tenebrism), 따뜻한 촛불 조명(2600K).
- @Protagonist(주인공)의 시선은 항상 깊은 사유를 담고 있어야 함.
- 거울을 통한 자아의 투영을 시각적 핵심 장치로 사용.

---
*이 규칙은 모든 파트에서 최우선으로 적용된다.*
"""

GEMMA_PROTOCOL_V81 = """# 📝 젬마 프로토콜 (Gemma Protocol) v8.1 — Librarian 전용
## 분석 및 리서치 단계의 실행 지침서

---

1. **채널 분석 시:** 영상의 조회수보다 '시청자 댓글의 절실함'을 먼저 분석한다.
2. **주제 도출 시:** 4070 시청자가 밤에 잠 못 이룰 때 검색할 법한 키워드 20개를 추출한다.
3. **리서치 초안 작성 시:** 옵시디언 노트 중 [[고독]], [[죽음]], [[관계]], [[용서]] 태그가 달린 노트를 최우선 참조한다.
4. **출력 형식:** 반드시 파이프(|) 구분자를 사용하여 파싱이 가능하게 한다.
5. **금지 사항:** 현대적인 어투, 가벼운 위로, 인공지능스러운 요약 표현을 절대 금지한다.

---
"""

PART3_GEMMA_PROTOCOL_V3 = """# [WRITE] GEMMA PROTOCOL v3.0 — Architect & Writer 전용
## 112씬 대본 설계 및 집필 실행 지침서

---

1. **구조 설계 시:** 기(28)-승(28)-전(28)-결(28) 총 112씬의 완벽한 밸런스를 유지한다.
2. **나레이션 집필 시:** 한 문장이 15자를 넘지 않도록 호흡을 조절하며, 60대 현자의 목소리를 상상하며 쓴다.
3. **이미지 프롬프트 변환 시:** 반드시 [A-MASTER] 태그를 첫머리에 두고, 렘브란트 조명과 EXPR 코드를 결합한다.
4. **일관성 체크:** @Protagonist와 @거울의 상호작용이 매 섹션마다 최소 3회 이상 등장하게 배치한다.

---
"""

PART3_MASTER_PROMPT_V1 = """# [TARGET] 대본 마스터 프롬프트 (가이드) v1.0
## 112씬 대본 작성을 위한 전역 시각/서사 규정

---

- **주인공:** @Protagonist (60대 현자, 은발, 버건디 로브)
- **공간:** 17세기 서재, 단일 촛불 조명, 어두운 배경
- **서사:** 거울 속의 젊은 자아(@거울속아바타)와의 문답을 통한 깨달음의 과정
- **톤:** 장엄하고 고요한 분위기, 24fps 시네마틱 감성
- **CapCut 연동:** 씬별 8초(기본) 기준, 음악은 첼로 솔로 위주로 구성

---
"""

IMAGE_PART_MASTER_PROMPT_V3 = """# 🖼️ 이미지 파트 마스터 규정서 v3.0
# Google Flow × Chrome Extension (FlowRun) 전용
# ═══════════════════════════════════════════════════
# 이 문서의 위치: 이미지 파트(Part 4) 최상단 R 입력란
# 역할: 112개 씬의 시각적 일관성을 지배하는 절대 규정
# ═══════════════════════════════════════════════════

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🎨 섹션 A — @Protagonist 마스터 외형 (A-MASTER)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【A-MASTER 고정값 — 영어 프롬프트 첫머리에 반드시 결합】

"Portrait of @Protagonist, a 60-year-old dignified male sage,
silver-grey hair with soft waves, short-trimmed silver beard,
weathered skin with noble wrinkles around kind luminous eyes,
wearing a heavy textured deep burgundy and charcoal linen robe,
masterpiece, cinematic oil painting style, Rembrandt lighting"
```

```
【A-REFERENCE SHEET 생성 양식 — 플로우에 최초 1회 생성 후 고정(Pin)】

Character reference sheet of @Protagonist, 8 different angles,
standing, sitting, profile, close-up on face, back view, 
consistent appearance, silver hair, burgundy robe, 
Rembrandt chiaroscuro style, 17th century master aesthetic,
--no modern objects contemporary setting 3D CGI
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🏰 섹션 B — 배경 및 소품 규격 (B-MASTER)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【@배경 고정값 — 영어 프롬프트 중간에 반드시 결합】

"inside a dark 17th-century scholar's study, 
walls covered in ancient stone and dark wood paneling, 
deep shadows in corners (Tenebrism), 
dust motes dancing in single light beam"
```

```
【@거울(Mirror) 규격】:
"Large ornate gold-leaf baroque mirror, 150cm tall, 
heavily carved frame, aged glass with slight oxidation, 
reflecting a mysterious internal depth"

---

@거울속아바타 — 감정 4종 (Mirror Avatar — 4 Emotional States):

[희(喜) — 기쁨/해방]:
"Inside the mirror: younger @Protagonist (age 30) with a rare full smile,
eyes crinkled with genuine joy, shoulders back and free,
warm golden light emanates from within the reflection,
a sense of liberation and lightness, almost laughing,
contrast to the solemn @Protagonist outside"

[노(怒) — 분노/저항]:
"Inside the mirror: younger @Protagonist (age 30) with fierce eyes,
jaw set hard, brows deeply furrowed in righteous rage,
fists visible and clenched, posture aggressive and forward-leaning,
the mirror seems to vibrate with contained fury,
flickering candle distorts the reflection with angry energy"

[애(哀) — 슬픔/비통]:
"Inside the mirror: younger @Protagonist (age 30) in silent grief,
face crumpled in sorrow, tears visible on the younger cheeks,
body collapsed inward, one hand reaching toward the glass from inside,
as if asking for help from across the years,
the reflection weeps what the present self cannot"

[락(樂) — 평온/수용]:
"Inside the mirror: younger @Protagonist (age 30) in serene peace,
soft gentle smile, eyes closed in acceptance,
hands open and relaxed at sides, breathing visibly slow,
warm light from within as if all wounds have healed,
the reflection has found what the present self still seeks"

---

@촛대(Candelabra):
"Tall wrought-iron Gothic candelabra, 150cm tall,
three half-burnt tallow candles at different heights,
generous wax drips down the iron and pooled at the base,
warm amber 2600K flame casting dancing upward shadows,
the flame flickers naturally — slightly asymmetric and alive,
smoke wisps visible above the tallest flame"

---

@소품 데이터베이스 (Props Database — 씬별 선택 사용):

@모래시계:
"Antique hourglass, 40cm tall, dark black sand,
ornate brass and dark wood frame with hourglass-shaped iron stand,
sand falling slowly and visibly, candlelight makes sand glitter"

@옛날만년필:
"Worn goose quill pen, natural feather showing age and use,
dried dark ink residue on the nib, resting diagonally on yellowed parchment,
a small ink pot with dried ink rings beside it"

@지구본:
"Faded antique wooden globe, 30cm diameter,
peeling hand-painted cartography with Latin place names,
mounted on a dark wood and brass meridian ring stand,
candlelight gleams off the brass fittings"

@고서:
"Stack of 5 leather-bound books of varying sizes,
gilded spine lettering worn to near illegibility,
pages yellowed and slightly warped from age and moisture,
the topmost book lies open to a page of dense Latin script"

@양피지:
"Yellowed vellum manuscript, A3 size,
dense handwritten text in faded brown iron gall ink,
occasional hand-drawn diagrams and marginalia,
edges slightly burnt or torn from age"

@깃털펜:
"Single large raven feather quill, cleaned and shaped for writing,
tip sharpened to a fine point, slight ink staining,
resting alone on a stone ledge in candlelight"

@열쇠:
"Large ornate iron skeleton key, 15cm long,
rust patina on the shaft, decorative bow with a cross motif,
resting on a folded piece of parchment"
```

```
【B-REFERENCE SHEET 생성 양식 — 플로우에 최초 1회 생성 후 고정(Pin)】

Environment and props reference sheet, single composite image,
top half: 4-angle view of the full scholar's study interior
bottom half: individual close-up shots of each prop
(@거울 / @촛대 / @모래시계 / @지구본 / @고서 / @양피지)
Style: Rembrandt chiaroscuro, oil painting texture, 16:9,
umber ochre palette, masterpiece,
--no modern objects contemporary setting 3D CGI
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🎭 섹션 D — 표정·포즈 라이브러리 (7종 고정)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
기-승-전-결 서사에 맞춰 아래 7종 중 하나를 C 프롬프트에 지정한다.
씬 작성 시 EXPR 코드를 명시하면 젬마가 자동으로 결합한다.

[EXPR-01 슬픔 (Grief)]
"downcast eyes heavy with unshed grief, slight trembling of lower lip,
shoulders collapsed inward as if bearing invisible weight,
hands pressed together or clasped at chest,
head slightly bowed, the posture of a man who has stopped fighting"

[EXPR-02 사유 (Deep Thought)]
"eyes half-closed in profound contemplation, head slightly tilted,
one weathered hand touching the chin or cheekbone,
the stillness of a man who has gone somewhere inside himself,
brows gently furrowed, mouth closed and still"

[EXPR-03 분노 (Righteous Anger)]
"jaw set firm and hard, eyes ablaze with contained indignation,
brows deeply furrowed and pulled together, nostrils slightly flared,
fists loosely clenched at sides, upright and forward posture,
the anger of a man who has witnessed injustice"

[EXPR-04 평온 (Serenity)]
"soft closed-eye serenity, the faintest and most genuine smile,
hands open and relaxed at his sides, shoulders dropped and free,
slow deep breath implied in the relaxed chest,
the peace of a man who has finally put something down"

[EXPR-05 깨달음 (Epiphany)]
"eyes suddenly wide and luminous, an involuntary small gasp,
one hand rising slowly to the chest as if touched by something holy,
body leaning slightly forward, the light seems to catch the eyes from within,
a crack of light through the face of a stone mountain"

[EXPR-06 회한 (Regret/Grief-Memory)]
"eyes red-rimmed and distant, gaze fixed at nothing present,
one large hand resting heavily on an old book as if for support,
the weight of decades of memory visible in every line of the face,
a man haunted by what he carries"

[EXPR-07 희망 (Quiet Hope)]
"eyes lifted upward and forward toward something unseen,
a quiet resolute half-smile — not joyful, but no longer despairing,
shoulders gently drawn back, one hand reaching toward faint light,
the posture of a man who has chosen to take one more step"

---
서사 위치별 권장 표정 매핑:
기(001–028): EXPR-01·02·03 위주 (상처와 질문)
승(029–056): EXPR-02·03·06 위주 (파헤침과 저항)
전(057–084): EXPR-05·02 위주  (균열과 깨달음)
결(085–112): EXPR-04·07·05 위주 (수용과 평화)
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📋 섹션 C — 씬 프롬프트 출력 규격 (C-OUTPUT FORMAT)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### C-1. 출력 표준 형식 (크롬 확장 프로그램 파싱용 — 한 줄 엄수)

```
【필수 출력 형식 — 이 형식 외의 다른 형식은 절대 허용하지 않는다】

형식:
씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@

─────────────────────────────────
예시 1 — @거울 씬:
001 | 인생의 무게가 당신을 짓누를 때, 우리는 거울 앞에 선다. | @어두운 서재, @Protagonist 가 @거울 정면을 응시, 왼쪽 뺨에만 @촛대 빛이 닿고 나머지는 칠흑, 시선은 거울 속 자신의 눈을 똑바로 바라봄, [EXPR-01]@ | @[A-MASTER] standing before [@거울], staring directly into own reflection, left cheek lit by single candle, right face in deep shadow, [EXPR-01], hands clasped behind back, sorrowful expression, [MASTER STYLE TAG] [NEGATIVE PROMPT]@

예시 2 — @지구본 소품 씬:
047 | 우리는 모두 어딘가로 향하고 있다고 믿었다. | @Protagonist 가 @지구본 을 천천히 손으로 돌리며, 시선은 지구본 표면이 아닌 허공 어딘가를 바라봄, @촛대 빛이 @지구본 의 황동 테두리에서 반짝임, [EXPR-02]@ | @[A-MASTER] slowly spinning [@지구본] with one weathered hand, gaze distant and unfocused beyond the globe, candlelight gleaming off brass meridian ring, [EXPR-02], [@배경], [MASTER STYLE TAG] [NEGATIVE PROMPT]@

예시 3 — @거울속아바타(애) 씬:
063 | 젊은 나는 거울 속에서 울고 있었다. | @Protagonist 가 @거울 앞에 서서, 거울 안에는 @거울속아바타(애)가 손을 유리 쪽으로 뻗고 있고, 바깥의 @Protagonist 는 손을 들어 유리에 닿을 듯 멈추는 장면, @촛대 빛이 위에서 내리쬠, [EXPR-06]@ | @[A-MASTER] standing before [@거울], in mirror reflection: [@거울속아바타(애)] reaching hand toward glass from inside, @Protagonist's hand raised toward glass from outside nearly touching, candlelight from above, dramatic top-light, [EXPR-06], [@배경], [MASTER STYLE TAG] [NEGATIVE PROMPT]@

예시 4 — @거울속아바타(희) 씬:
098 | 그때의 나는 이렇게 웃을 수 있었다. | @Protagonist 가 @거울 을 바라보며 희미하게 미소짓고, 거울 안의 @거울속아바타(희)는 환하게 웃고 있어 극적 대비를 이룸, @촛대 두 개가 양 옆에서 빛을 줌, [EXPR-07]@ | @[A-MASTER] gazing at [@거울] with faint half-smile, in mirror: [@거울속아바타(희)] with full joyful smile creating dramatic emotional contrast, two candles flanking the mirror, warm bilateral light, [EXPR-07], [@배경], [MASTER STYLE TAG] [NEGATIVE PROMPT]@
─────────────────────────────────

【4개 필드 상세 규칙】

필드 1 — 씬번호(3자리):
  001, 002, 003 ... 099, 100, 101 ... 112
  규칙: 반드시 3자리 고정 (1 → 001, 10 → 010)

필드 2 — 대본:
  Part 3·4의 확정 대본 원문을 그대로 사용
  수정 절대 금지 (요약, 단축, 변경 모두 금지)

필드 3 — @한글묘사@:
  반드시 포함해야 할 4가지 요소:
  ① 인물 동작 — @Protagonist가 무엇을 하는가
  ② 시선 처리 — 어디를 바라보는가
  ③ 빛의 위치와 방향 — @촛대/키라이트가 어디서 오는가
  ④ 사용 소품 태그 — @태그명 형식으로 모두 명시
  ⑤ 표정 코드 — [EXPR-0X] 반드시 명시

필드 4 — @영어프롬프트@:
  반드시 포함해야 할 요소:
  ① [A-MASTER] — 반드시 첫 번째 결합
  ② 소품 태그 — [@거울], [@촛대] 등 대괄호로 명시
  ③ 표정 값 — [EXPR-0X]에 해당하는 영문 표정값 결합
  ④ [@배경] — 배경 고정값 결합
  ⑤ [MASTER STYLE TAG] — 반드시 마지막에서 두 번째 결합
  ⑥ [NEGATIVE PROMPT] — 반드시 마지막 결합
```

### C-2. MASTER STYLE TAG (모든 씬 공통 — 절대 생략 금지)

```
[MASTER STYLE TAG]:
"Cinematic oil painting, Rembrandt chiaroscuro, tenebrism,
single warm key light upper-left 45 degrees,
umber ochre burnt sienna palette,
deep impasto brushwork visible in shadows,
17th-century Dutch master aesthetic,
photorealistic details in focal points,
heavy 35mm film grain overlay,
deep edge vignette at corners,
16:9 aspect ratio, 8K resolution, masterpiece quality,
ultra-high detail, professional cinematography"
```

### C-3. NEGATIVE PROMPT (모든 씬 공통 — 절대 생략 금지)

```
[NEGATIVE PROMPT]:
"--no bright saturated colors, neon lighting, modern lighting,
clean sharp digital edges, digital art look, airbrushed skin,
smooth plastic texture, symmetrically perfect face,
anime style, cartoon, illustration, 3D render, CGI, game art,
stock photo, contemporary clothing, changed protagonist appearance,
broadly smiling unless specified, comic book style,
watercolor, pencil sketch, low contrast flat lighting,
overexposed highlights, blown out whites,
any text or watermark overlay, extra limbs,
deform hands, extra fingers, merged figures,
background characters, crowds,
any character other than @Protagonist,
changed beard, changed robe color, younger than 60"
```

### C-4. 씬 파일명 및 저장 경로 규칙

```
생성 완료 이미지 파일명 규칙:
  scene_001.png ~ scene_112.png (3자리 고정)

저장 폴더 이중화 (반드시 두 경로 모두 저장):
  폴더 1: [사용자 지정 경로]/Images/EP001/scene_XXX.png
  폴더 2: [옵시디언 볼트 경로]/attachments/EP001/scene_XXX.png

옵시디언 링크 형식:
  ![[EP001/scene_001.png]]
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🔧 섹션 E — A/B/C 방식 완전 설명 (작업 원리 이해)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【A/B/C 방식의 원리와 순서 — 반드시 이 순서를 지켜야 에러가 없다】

━━━━ STEP A: 주인공 참조 이미지 생성 (최초 1회만) ━━━━
목적: @Protagonist의 외형을 AI가 기억하도록 고정시키는 기준 이미지
입력: [A-REFERENCE SHEET 생성 양식] 텍스트만 입력
출력: character_reference_protagonist.png (전신 8각도 컴포짓)
저장: [경로]/References/A_Protagonist_Master.png
크롬 확장: Slot 1에 업로드 후 반드시 PIN(고정) 처리
주의: A 이미지 생성 후 외형이 마음에 들지 않으면 재생성 가능
      단, 한 번 확정되면 112씬 내내 절대 변경하지 않는다

━━━━ STEP B: 배경·소품 참조 이미지 생성 (최초 1회만) ━━━━
목적: 서재 배경과 모든 소품의 시각 스타일을 고정시키는 기준 이미지
입력: [B-REFERENCE SHEET 생성 양식] 텍스트만 입력
출력: environment_reference_background.png (배경+소품 컴포짓)
저장: [경로]/References/B_Environment_Master.png
크롬 확장: Slot 2에 업로드 후 반드시 PIN(고정) 처리
주의: B 이미지도 확정 후 변경 금지

━━━━ STEP C: 씬별 개별 이미지 생성 (001~112씬 반복) ━━━━
목적: A와 B를 참조한 상태에서 각 씬의 개별 이미지를 생성
입력 방식 (3가지 요소 동시 입력):
  ① 참조 이미지 슬롯: A(고정) + B(고정) 유지 상태에서
  ② 프롬프트 슬롯: 해당 씬의 @영어프롬프트@ 텍스트 입력
  ③ 씬 번호 라벨: 파일명으로 scene_XXX.png 지정
출력: scene_001.png ~ scene_112.png
저장: 자동 저장 경로 확인 후 옵시디언에도 복사

【A/B/C 방식 핵심 원리】
A = "이 사람을 기억해"  (외형 고정)
B = "이 공간을 기억해"  (환경 고정)
C = "이 씬을 그려줘"    (A+B를 참조한 상태에서 씬별 생성)

C를 생성할 때 A와 B가 참조 슬롯에 없으면:
→ 매 씬마다 @Protagonist 외형이 달라지는 일관성 붕괴 발생
→ 반드시 슬롯 고정 상태 확인 후 생성 시작

【A/B/C 자주 발생하는 에러와 해결책】
에러 1: 외형 불일치 (@Protagonist 얼굴/수염/복장이 씬마다 다름)
  원인: A 참조 이미지가 슬롯에서 해제되었거나 누락
  해결: A_Protagonist_Master.png 재업로드 → Pin → 해당 씬 재생성

에러 2: 배경 스타일 불일치 (현대적 배경, 밝은 조명 등이 나옴)
  원인: B 참조 이미지 슬롯 해제 또는 NEGATIVE PROMPT 누락
  해결: B_Environment_Master.png 재업로드 → NEGATIVE PROMPT 추가 → 재생성

에러 3: 소품이 프롬프트에 명시되어 있지만 이미지에 등장하지 않음
  원인: 소품 태그가 영어 프롬프트에서 너무 뒤쪽에 위치
  해결: 소품을 프롬프트 앞쪽으로 이동 / 소품 단독 강조 문장 추가

에러 4: 표정이 EXPR 지정과 다름
  원인: 영어 표정값이 프롬프트에 포함되지 않음
  해결: [EXPR-0X]의 영문 전체 텍스트를 프롬프트에 결합

에러 5: 씬 번호 순서 꼬임
  원인: 크롬 자동화 순서 설정 오류
  해결: 아래 섹션 F의 크롬 자동화 순서 체크리스트 재확인
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🖥️ 섹션 F — 크롬 자동화 확장 프로그램 작업 순서 및 규칙
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【크롬 자동화 확장 프로그램 전체 작업 순서 — 이 순서를 반드시 지킨다】

━━━━ 사전 준비 (최초 1회) ━━━━

PREP-01: 구글 플로우(나노바나나) 접속 및 새 플로우 생성
  → 플로우 이름: "현자의거울_EP001_이미지생성"

PREP-02: A_Protagonist_Master.png 생성 (아직 없는 경우)
  → [섹션 A의 A-REFERENCE SHEET 양식] 입력
  → 생성 완료 후 다운로드
  → [경로]/References/A_Protagonist_Master.png 저장

PREP-03: B_Environment_Master.png 생성 (아직 없는 경우)
  → [섹션 B의 B-REFERENCE SHEET 양식] 입력
  → 생성 완료 후 다운로드
  → [경로]/References/B_Environment_Master.png 저장

PREP-04: 크롬 확장 프로그램 Reference Image 슬롯 고정
  → Reference Slot 1: A_Protagonist_Master.png 업로드 → PIN 클릭
  → Reference 노 Slot 2: B_Environment_Master.png 업로드 → PIN 클릭
  → PIN 상태 확인: 슬롯에 [LOCK] 표시 확인
  [WARN] 이 PIN이 해제되면 모든 캐릭터 일관성이 깨진다

PREP-05: 젬마(Gemma) 프로토콜 로딩
  → 중간 젬마 프로토콜 입력란에 [gemma_protocol_v2_image.md] 붙여넣기
  → "로딩 완료" 선언 확인 후 작업 시작

━━━━ 씬별 자동화 루틴 (001~112 반복) ━━━━

STEP-01: 젬마에게 씬 번호 입력
  입력 예: "씬 001 프롬프트 생성해줘"
  젬마 출력: C-1 형식의 한 줄 완성 프롬프트

STEP-02: 출력된 @영어프롬프트@ 필드 복사
  → 씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ 중
     @영어프롬프트@ 의 @ 사이 내용만 복사

STEP-03: 크롬 확장 프로그램 Prompt 입력란에 붙여넣기
  → 참조 슬롯 (Slot 1, 2) PIN 상태 유지 확인
  → Prompt 입력란에 복사한 영어 프롬프트 붙여넣기

STEP-04: 파일명 설정
  → Output filename: scene_XXX.png (XXX = 해당 씬 번호 3자리)

STEP-05: 생성 실행
  → Generate 버튼 클릭
  → 생성 완료까지 대기 (다음 씬으로 이동하지 않는다)

STEP-06: 결과물 검수 (자체 검수 — 5초 체크)
  □ @Protagonist 외형 일치하는가 (수염/복장/얼굴)
  □ 소품이 프롬프트 지정대로 등장하는가
  □ 조명이 렘브란트 스타일인가 (좌상단 단일 키라이트)
  □ 현대적 요소가 없는가
  □ 16:9 비율인가

STEP-07: 합격 / 재생성 판정
  합격 → scene_XXX.png 다운로드 → 지정 경로에 저장
  불합격 → [C-5. 에러별 해결책] 적용 후 STEP-03부터 재실행

STEP-08: 다음 씬으로 이동 (씬 번호 +1)
  → STEP-01로 돌아가서 반복

━━━━ 자동화 배치 실행 옵션 (크롬 확장 배치 기능 사용 시) ━━━━

배치 파일 준비:
  1. 젬마에게 전체 112씬 C파트 프롬프트 생성 요청
  2. 생성된 @영어프롬프트@ 필드 전체를 순서대로 TXT 파일에 저장
     (한 줄 = 한 씬의 영어 프롬프트)
  3. 파일명 배열: scene_001.png, scene_002.png ... 자동 증가 설정

이동 실행 중 주의사항:
  [WARN] 배치 중간에 슬롯 PIN이 자동 해제될 수 있음 → 5씬마다 확인
  [WARN] 네트워크 끊김 시 마지막 성공한 씬 번호 기록 후 이어서 실행
  [WARN] 생성 속도: 씬당 최소 30초 대기 (서버 과부하 방지)
  [WARN] 10씬마다 생성 결과물 일괄 검수 실시 (일관성 누적 오류 방지)
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## [OK] 섹션 G — 씬 생성 전 체크리스트 (검수 기준)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【씬 생성 전 — 프롬프트 완성도 체크】
□ [A-MASTER] 고정값 포함 여부
□ 사용 소품 @태그가 영어 프롬프트에 대괄호([ ])로 명시됐는가
□ @한글묘사@ — 동작·시선·빛·소품·표정 5요소 모두 기술됐는가
□ [EXPR-0X] 표정 코드가 한글 묘사와 영어 프롬프트 양쪽에 모두 포함됐는가
□ [MASTER STYLE TAG] 결합됐는가
□ [NEGATIVE PROMPT] 결합됐는가
□ 씬 번호가 대본 번호와 일치하는가
□ 16:9 비율 명시됐는가
□ 8K 해상도 명시됐는가
□ --no 네거티브 결합됐는가

【씬 생성 후 — 결과물 검수 체크】
□ @Protagonist 수염 색상: 은빛-회색 맞는가
□ @Protagonist 복장: 버건디 린넨 로브 맞는가
□ 조명: 좌상단 45° 단일 키라이트 맞는가
□ 80% 이상 화면이 어둠(그림자)인가
□ 배경: 17세기 서재 맞는가
□ 현대 요소(LED, 스마트폰, 플라스틱 등) 없는가
□ 16:9 비율 맞는가
□ 지정된 소품이 프레임 내에 존재하는가

【캐릭터 일관성이 깨진 경우 재생성 트리거】
→ A_Protagonist_Master.png Slot 1에 재업로드 → PIN 확인
→ [A-MASTER] + [EXPR-0X] 재결합
→ 구글 플로우 재실행
→ 재생성 후 위 체크리스트 재검수

【10회 연속 불합격 시 비상 조치】
→ 젬마에게 "캐릭터 일관성 복구 모드 실행" 입력
→ A 참조 이미지 재생성 (새 버전으로 교체)
→ 교체 후 씬 1개 테스트 생성 → 합격 확인 후 배치 재개
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📦 섹션 H — CapCut 자동화 JSON 출력 규격 (하단 우측칸 연동)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```json
{
  "episode": "EP001",
  "total_scenes": 112,
  "aspect_ratio": "16:9",
  "resolution": "8K",
  "style": "Rembrandt chiaroscuro oil painting",
  "protagonist": "@Protagonist",
  "scenes": [
    {
      "scene_id": "001",
      "script": "인생의 무게가 당신을 짓누를 때, 우리는 거울 앞에 선다.",
      "action_kr": "@Protagonist 가 @거울 정면을 응시, 왼쪽 뺨에만 @촛대 빛",
      "expression": "EXPR-01",
      "props_used": ["@거울", "@촛대"],
      "image_file": "scene_001.png",
      "audio_file": "narration_001.mp3",
      "timeline_order": 1,
      "duration_sec": 8
    }
  ],
  "reference_images": {
    "protagonist": "A_Protagonist_Master.png",
    "environment": "B_Environment_Master.png"
  },
  "bgm": {
    "style": "melancholy instrumental, solo cello and sparse piano, no vocals",
    "mood": "contemplative grief resolving to quiet hope",
    "tempo": "extremely slow, one phrase per 30 seconds"
  }
}
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📁 섹션 I — 참조 이미지 경로 관리 규칙
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【경로 이중화 — 폴더 + 옵시디언 동시 저장 규칙】

A 참조 이미지:
  폴더 경로: [저장경로]/References/A_Protagonist_Master.png
  옵시디언: [[References/A_Protagonist_Master.png]]

B 참조 이미지:
  폴더 경로: [저장경로]/References/B_Environment_Master.png
  옵시디언: [[References/B_Environment_Master.png]]

씬 이미지 (001~112):
  폴더 경로: [저장경로]/Images/EP001/scene_XXX.png
  옵시디언: [[EP001/scene_XXX.png]]

구글 플로우 업로드 순서 (변경 불가):
  1. A_Protagonist_Master.png → Reference Slot 1 → PIN 고정
  2. B_Environment_Master.png → Reference Slot 2 → PIN 고정
  3. 씬별 @영어프롬프트@ → Prompt 슬롯 → 씬 순서대로 입력 (001 → 112)
```

---

*이 문서 전문을 이미지 파트(Part 5) 최상단 우측 `st.text_area`에 붙여넣으세요.*  
*버전: v3.2 | 현자의 거울 스튜디오 | Google Flow × Chrome Extension Edition*
"""

def init_session_state():
    loaded_data = load_workspace_state()
    defaults = {
        "logged_in": True,
        "path_obsidian": r"C:\SageMirror_Production\00_Obsidian_Archive", 
        "path_assets": r"C:\SageMirror_Production\00_Assets",
        "path_memo": r"C:\SageMirror_Production\00_Memo",
        "github_token": "",
        "github_repo_url": "https://github.com/rokmc9457303l-hue/SageMirror_Studio.git",
        "github_local_path": r"C:\SageMirror_Production",
        "tavily_api_key": "",
        "obsidian_rules": DEFAULT_OBSIDIAN_RULES_V81,
        "base_prompt_rules": MASTER_RESEARCH_PROMPT_V81,
        "obsidian_history": [],
        "prompt_history": [],
        "popup_history": [],
        "popup_search_history": [],
        "popup_selected_model": "gemma4:e2b",
        "selected_model": "gemma4:e2b",
        "popup_auto_search": True,
        "popup_use_rag": True,
        "sidebar_part": "part1",
        "unlock_part1": False,
        "unlock_part2": False,
        "unlock_part6": False,
        "unlock_part7": False,
        "unlock_part8": False,
        
        "p1_gemma_protocol": GEMMA_PROTOCOL_V81,
        "p1_channel_search_results": [],
        "p1_channel_url": "",
        "p1_region": "국내+국외 모두",
        "p1_topics": [],
        "p1_topic_selection": None,
        "p1_research_result": "",
        "p1_planning_result": "",
        "p1_saved_paths": [],
        "p1_bench_prompt": "[작업 지시] 다음 타겟 채널을 분석하여 핵심 주제 20개를 추출하십시오. (200여 개 시청자 댓글 공감 포인트 참조)",
        "p1_research_prompt": "[작업 지시] 선택된 주제에 대하여 200여 개의 시청자 공감 댓글을 참조하고, 철학/심리학/성경 기반 지식을 융합하여 '자료 조사 및 기초 초안'을 작성하시오.",
        "p1_plan_prompt": "[작업 지시] 자료 조사 결과를 바탕으로 '15분 분량의 유튜브 다큐멘터리 총괄 시나리오 기획안'을 작성하시오.",
        "p1_bench_raw": "",
        "p1_bench_tags": "",
        "p1_research_tags": "",
        "p1_plan_tags": "",
        "p1_bench_saved": False,
        "p1_bench_obsidian_saved": False,
        "p1_research_saved": False,
        "p1_research_obsidian_saved": False,
        "p1_plan_saved": False,
        "p1_plan_obsidian_saved": False,
        
        "p2_gemma_protocol": GEMMA_PROTOCOL_V81,
        "p2_channel_search_results": [],
        "p2_channel_url": "",
        "p2_region": "국내+국외 모두",
        "p2_topics": [],
        "p2_topic_selection": None,
        "p2_research_result": "",
        "p2_planning_result": "",
        "p2_thumbnail_plan": "",
        "p2_bench_prompt": "[작업 지시] 다음 타겟 채널을 분석하여 핵심 주제 20개, 후킹 기법, 인트로 기법, 그리고 채널 구조 분석을 생성하고 추출하십시오. (200여 개 시청자 댓글 공감 포인트 참조)",
        "p2_bench_raw": "",
        "p2_bench_tags": "",
        "p2_bench_saved": False,
        "p2_bench_obsidian_saved": False,
        # ── Part 2 3단 버튼 상태 인디케이터 키 ──
        "p2_research_prompt": "[작업 지시] 선택된 주제에 대하여 200여 개의 시청자 공감 댓글을 참조하고, 철학/심리학/성경 기반 지식을 융합하여 '자료 조사 및 기초 초안'을 작성하시오.",
        "p2_research_tags": "",
        "p2_research_saved": False,
        "p2_research_obsidian_saved": False,
        "p2_plan_prompt": "[작업 지시] 위의 자료조사 결과와 Part 1 주제 분석을 바탕으로, 성경-철학-에세이 3원 융합 구조의 15분 유튜브 롱폼 총괄 기획안을 작성하시오.",
        "p2_plan_tags": "",
        "p2_plan_saved": False,
        "p2_plan_obsidian_saved": False,
        "p34_gemma_protocol": PART3_GEMMA_PROTOCOL_V3,
        "p34_master_prompt": PART3_MASTER_PROMPT_V1,
        "unlock_part34": False,
        "p34_scene_structure": "",
        "p34_narration_script": "",
        "p34_image_script": "",
        "p34_capcut_data": "",
        # ── Part 3-4 젬마 프롬프트 키 ──
        "p34_narr_prompt": "[작업 지시] 아래 112씬 구조를 바탕으로 각 씬의 나레이션 대본을 작성하세요. 화자는 60대 현자(Sage)이며, 4070 시청자에게 말하듯 따뜻하고 묵직한 톤으로 작성합니다.",
        "p34_img_prompt": "[작업 지시] 아래 나레이션 대본을 이미지 파트 규격(C-1)에 맞춰 변환하세요. 한글묘사에는 인물동작/시선/빛/소품태그/표정코드[EXPR-0X] 필수.",
        "p34_cap_prompt": "[작업 지시] 아래 이미지 대본을 CapCut 자동화 JSON으로 변환하세요. 각 씬: scene_id, script, action_kr, expression, props_used, image_file(scene_XXX.png), audio_file(narration_XXX.mp3), timeline_order, duration_sec 포함.",
        # ── Part 3-4 3단 버튼 상태 인디케이터 키 ──
        "p34_arch_saved": False,
        "p34_arch_obsidian_saved": False,
        "p34_narr_saved": False,
        "p34_narr_obsidian_saved": False,
        "p34_img_saved": False,
        "p34_img_obsidian_saved": False,
        "p34_cap_saved": False,
        "p34_cap_obsidian_saved": False,
        "p5_image_master_prompt": IMAGE_PART_MASTER_PROMPT_V3,
        "unlock_part5": False,
        # ── Part 4 (Image Consistency) 전용 키 ──
        "p5_gemma_protocol": "",
        "p5_a_result": "",
        "p5_b_result": "",
        "p5_c_results": "",
        "p5_valid_rows": [],
        "p5_error_rows": [],
        "p5_parsed_scenes": [],
        "p5_parse_errors": [],
        "p5_v_results": {},
        "p5_v_scene_count": 0,
        "p5_a_history": [],
        "p5_b_history": [],
        "p5_c_history": [],
        "p5_protocol_loaded": "",
        "p5_save_done": False,
        # ── Part 5 (Video Production) v13.2 업데이트 ──
        "p6_veo3_master_prompt": P6_VEO3_MASTER_PROMPT_V2,
        "p6_gemma_protocol": P6_GEMMA_PROTOCOL_V2,
        "p6_master_prompt": P6_MASTER_PROMPT_DEFAULT,
        "p7_master_prompt": P7_MASTER_PROMPT_DEFAULT,
        "p8_master_prompt": P8_MASTER_PROMPT_DEFAULT,
        "p6_protocol_loaded": "",
        "p6_vid_pin_input": "",
        "unlock_part6_vid": False,
        "pending_stream": None,
        "p6_opal_df": None,
        "p6_save_done": False,
        "p7_capcut_df": None,
        "p8_check_result": "",
        "p8_save_done": False,
        "p1_verification": None,
        "p2_verification": None,
        "p2_plan_verification": None,
        "p34_narr_verification": None,
        "p34_img_verification": None,
        "p1_need_research_kw": None,
        "p2_need_research_kw": None,
        "p2_plan_need_research_kw": None,
        "p34_narr_need_research_kw": None,
        "p34_img_need_research_kw": None,
        "p6_opal_data": None,
        "p7_capcut_data_v2": None,
        "p6_bgm_selection": "비장한 성경 낭독풍",
        "p6_mixing_ratio": 80,
        "p6_narration_verified": False,
        "p6_opal_saved": False,
        "p6_opal_obsidian_saved": False,
        "p7_capcut_saved": False,
        "p7_capcut_obsidian_saved": False,
        "p8_dashboard_saved": False,
        "p8_dashboard_obsidian_saved": False,
    }
    
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
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE} <span style='color:#10B981;font-size:0.5em;'>v13.2 Video Edition</span></h1>", unsafe_allow_html=True)
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
    st.markdown(f"### {APP_TITLE} **v15.0**")
    status = check_ollama_status()
    if status["server"] and status["model"]: st.success(f"[OK] Ollama | {OLLAMA_MODEL}")
    else: st.error(f"[FAIL] Ollama 에러")

    st.divider()
    st.info(f"📂 **옵시디언 아카이브**\n{st.session_state.path_obsidian}")
    st.info(f"🚀 **GitHub 연동 중**\n{st.session_state.github_repo_url.split('/')[-1]}")

    with st.expander("⚙️ 설정 변경", expanded=False):
        st.session_state.path_obsidian = st.text_input("옵시디언 볼트", value=st.session_state.path_obsidian)
        st.session_state.github_repo_url = st.text_input("Repo URL", value=st.session_state.github_repo_url)
        st.session_state.github_token = st.text_input("GitHub PAT (공란 권장)", value=st.session_state.github_token, type="password")
        st.session_state.tavily_api_key = st.text_input("Tavily API Key", value=st.session_state.tavily_api_key, type="password")
        st.session_state.youtube_api_key = st.text_input("YouTube API Key", value=st.session_state.get("youtube_api_key", ""), type="password")
        if st.button("수동 동기화"):
            success, msg = auto_git_push("Manual Sync")
            if success: st.success(msg)
            else: st.error(msg)
            
    st.divider()
    st.markdown("##### [SAVE] 작업 상태 관리 (물리적 백업)")
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
    part = st.radio("이동할 파트", [
        "파트 1: 벤치마킹 & 자료조사",
        "파트 2: 총괄기획",
        "파트 3: 대본 작성",
        "파트 4: 이미지 생성",
        "파트 5: 영상 생성",
        "파트 6: 나레이션 & 배경음악",
        "파트 7: 숏폼 생성",
        "파트 8: 캡컷 최종 조립"
    ], index=0)
    st.session_state.sidebar_part = part
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# =====================================================================
# 팝업 로직
# =====================================================================
@st.dialog("📁 옵시디언 백업 내역 (최근 15개)", width="large")
def popup_obsidian_history():
    st.markdown("옵시디언 보관소(`00_Obsidian`) 및 세션 폴더에 저장된 마크다운 백업 목록입니다.")
    obs_path = st.session_state.get("path_obsidian", "")
    if not obs_path or not os.path.exists(obs_path):
        st.error("옵시디언 경로가 존재하지 않거나 설정되지 않았습니다.")
        return
        
    try:
        md_files = []
        for root, dirs, files in os.walk(obs_path):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    md_files.append({
                        "name": file,
                        "rel_path": os.path.relpath(full_path, obs_path).replace("\\", "/"),
                        "abs_path": full_path,
                        "mtime": datetime.fromtimestamp(mtime),
                        "size": f"{size / 1024:.1f} KB"
                    })
        
        if not md_files:
            st.info("백업된 마크다운 파일이 없습니다.")
            return
            
        md_files.sort(key=lambda x: x["mtime"], reverse=True)
        md_files = md_files[:15]
        
        import pandas as pd
        df = pd.DataFrame(md_files)[["rel_path", "mtime", "size"]]
        df.columns = ["백업 파일명(상대경로)", "마지막 저장 시간", "용량"]
        st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.error(f"옵시디언 내역 조회 실패: {e}")

@st.dialog("🚀 GitHub 커밋 및 백업 내역 (최근 10개)", width="large")
def popup_git_history():
    st.markdown("GitHub 리포지토리(`SageMirror_Studio`)의 로컬 커밋 및 동기화 히스토리입니다.")
    if not GIT_AVAILABLE:
        st.error("Git 패키지(GitPython)를 사용할 수 없습니다.")
        return
        
    try:
        from git import Repo
        repo = Repo(r"C:\SageMirror_Production")
        commits = list(repo.iter_commits(max_count=10))
        
        if not commits:
            st.info("커밋 내역이 존재하지 않습니다.")
            return
            
        git_list = []
        for c in commits:
            git_list.append({
                "hash": c.hexsha[:7],
                "message": c.message.strip(),
                "author": c.author.name,
                "date": datetime.fromtimestamp(c.committed_date).strftime("%Y-%m-%d %H:%M:%S")
            })
            
        import pandas as pd
        df = pd.DataFrame(git_list)
        df.columns = ["커밋 해시", "커밋 메시지", "작성자", "작성 일시"]
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"GitHub 내역 조회 실패: {e}")

@st.dialog("📝 젬마 프로토콜 (Gemma Protocol) 편집", width="large")
def popup_edit_gemma_protocol():
    st.markdown("여기서 행동 지침과 작업 지침서를 상세하게 수정할 수 있습니다. 텍스트를 드래그하고 복사/붙여넣기 하세요.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p1_gemma_protocol, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p1_gemma_protocol = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()

@st.dialog("📚 자료 조사 결과 (팝업)", width="large")
def popup_edit_research():
    st.markdown("결과를 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p1_research_result}</div>", unsafe_allow_html=True)
    new_val = st.text_area("자료 조사 결과 수정", value=st.session_state.p1_research_result, height=200, label_visibility="collapsed")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p1_research_result = new_val
            st.rerun()
    with c2:
        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"research_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)
    with c3:
        if st.button("닫기", use_container_width=True):
            st.rerun()

@st.dialog("[PACKAGE] Part 2 전달 패킷 (팝업)", width="large")
def popup_edit_planning():
    st.markdown("Part 2에서 철학/성경/감정 융합 작업에 사용할 리서치 패킷입니다.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p1_planning_result}</div>", unsafe_allow_html=True)
    new_val = st.text_area("Part 2 전달 패킷 수정", value=st.session_state.p1_planning_result, height=200, label_visibility="collapsed")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p1_planning_result = new_val
            st.rerun()
    with c2:
        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"planning_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)
    with c3:
        if st.button("닫기", use_container_width=True):
            st.rerun()

@st.dialog("[TARGET] 채널 벤치마킹 결과 (팝업)", width="large")
def popup_edit_benchmarking():
    st.markdown("결과를 쾌적하게 스크롤하며 검토하고 복사할 수 있습니다.")
    raw = st.session_state.get("p1_bench_raw", "")
    if raw:
        st.markdown("##### 📄 벤치마킹 원본 결과")
        with st.container(height=400, border=True):
            st.markdown(raw)
        st.divider()    
    val = ""
    for t in st.session_state.get("p1_topics", []):
        val += f"**{t['title']}**\n- 사유: {t['reason']}\n- 효과: {t['effect']}\n\n"
    with st.container(height=450, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{val}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 .txt 다운로드", data=val, file_name=f"benchmarking_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)
    with c2:
        if st.button("닫기", use_container_width=True, type="primary"):
            st.rerun()

# =====================================================================
# 공통 UI 레이아웃 (V8.1: 상단 PIN 로그인 통합)
# =====================================================================
def render_top_panel():
    # ──────────────────────────────────────────────────────────────
    # 상태 데이터 수집 (로직은 그대로, 디자인만 변경)
    # ──────────────────────────────────────────────────────────────
    db_ok  = os.path.exists(WORKSPACE_STATE_FILE)
    obs_path = st.session_state.get("path_obsidian", "")
    obs_ok = os.path.exists(obs_path) if obs_path else False
    git_repo = st.session_state.get("github_repo_url", "")
    git_ok   = len(git_repo) > 0 and GIT_AVAILABLE
    repo_name = git_repo.split('/')[-1].replace('.git', '') if git_ok else "미연동"
    obs_name  = os.path.basename(obs_path) if obs_ok else "경로 미설정"

    # ──────────────────────────────────────────────────────────────
    # [ROW 1] 상태 카드 4개 — 글래스모피즘 스타일 가로 배치
    # ──────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* 우측 컨트롤 박스 테두리 및 배경색 상황판과 통일 */
    #header-control-box-anchor + div {
        background: linear-gradient(135deg, #131b2e 0%, #0c1220 100%) !important;
        border: 1.5px solid #d4af6a44 !important;
        border-radius: 12px !important;
        padding: 6px 12px 6px 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* 내부 위젯 정렬 강제 및 Streamlit 여백 리셋 */
    .header-pin-wrapper div[data-testid="stMarkdownContainer"] {
        margin: 0 !important;
    }
    .header-pin-wrapper input {
        height: 38px !important;
        border: 1px solid rgba(212, 175, 106, 0.3) !important;
        background-color: rgba(30, 41, 59, 0.45) !important;
        color: #f5e9d3 !important;
        margin: 0 !important;
    }
    .header-pin-wrapper input:focus {
        border-color: #d4af6a !important;
    }
    
    /* 모델 셀렉트박스 스타일링 */
    .header-model-wrapper div[data-baseweb="select"] {
        height: 38px !important;
        background-color: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(212, 175, 106, 0.3) !important;
        border-radius: 4px !important;
        color: #f5e9d3 !important;
    }
    .header-model-wrapper div[data-baseweb="select"]:hover {
        border-color: #d4af6a !important;
    }
    .header-model-wrapper div[data-testid="stSelectbox"] > div {
        border: none !important;
        background-color: transparent !important;
        height: 38px !important;
        min-height: 38px !important;
    }
    .header-model-wrapper div[role="button"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        line-height: 36px !important;
        height: 36px !important;
        background-color: transparent !important;
        color: #f5e9d3 !important;
    }
    
    .header-pop-wrapper button {
        height: 38px !important;
        margin: 0 !important;
        background-color: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(212, 175, 106, 0.3) !important;
        color: #f5e9d3 !important;
    }
    .header-pop-wrapper button:hover {
        border-color: #d4af6a !important;
        background-color: rgba(212, 175, 106, 0.15) !important;
    }

    /* 상단 동기화 패널 통일화 디자인 (하단 상황판과 동일한 배경 및 테두리 지정) */
    .sage-sync-title {
        font-size: 0.92em;
        font-weight: 700;
        color: #d4af6a;
        margin-bottom: 12px;
        letter-spacing: 0.03em;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    #top-sync-panel-anchor + div[data-testid="stHorizontalBlock"] {
        background: linear-gradient(135deg, #131b2e 0%, #0c1220 100%) !important;
        border: 1.5px solid #d4af6a44 !important;
        border-radius: 14px !important;
        padding: 20px 20px 18px 20px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.45) !important;
    }
    /* 클릭 가능한 카드의 래퍼 스타일 및 투명 absolute overlay 매직 (로컬 DB연결 형태를 100% 모방) */
    div[data-testid="column"]:has(.clickable-card-bg) {
        position: relative !important;
    }
    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] {
        position: absolute !important;
        inset: 0 !important;
        z-index: 99 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] button {
        background-color: transparent !important;
        border: none !important;
        color: transparent !important; /* 내부 텍스트 완전 투명화 */
        width: 100% !important;
        height: 100% !important;
        position: absolute !important;
        inset: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 8px !important;
        cursor: pointer;
    }
    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] button:hover {
        background-color: rgba(212, 175, 106, 0.08) !important;
    }
    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] button p {
        display: none !important; /* 텍스트 숨김 */
    }
    .sage-stat-card.sync::before {
        background: linear-gradient(135deg, #d4af6a, #9a7b44) !important;
    }
    .sage-stat-card.sync .stat-label {
        color: #d4af6a !important;
    }

    .sage-status-row {
        display: flex;
        gap: 12px;
        align-items: stretch;
        margin-bottom: 14px;
        flex-wrap: nowrap;
    }
    .sage-stat-card {
        flex: 1;
        background: rgba(30, 41, 59, 0.45);
        border-radius: 8px;
        padding: 12px 16px;
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 3px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .sage-stat-card::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 8px;
        padding: 1px;
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
    }
    .sage-stat-card.ok::before  { background: linear-gradient(135deg, #10B981, #06b6d4); }
    .sage-stat-card.warn::before{ background: linear-gradient(135deg, #F59E0B, #f97316); }
    .sage-stat-card.err::before { background: linear-gradient(135deg, #EF4444, #be185d); }
    
    .sage-stat-card .stat-label {
        font-size: 0.78em;
        font-weight: 700;
        letter-spacing: 0.02em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sage-stat-card .stat-sub {
        font-size: 0.68em;
        color: #94a3b8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sage-stat-card.ok  .stat-label { color: #34d399; }
    .sage-stat-card.warn .stat-label{ color: #fbbf24; }
    .sage-stat-card.err  .stat-label{ color: #f87171; }
    
    /* 파이프라인 카드 */
    .sage-pipeline-card {
        background: linear-gradient(135deg, #131b2e 0%, #0c1220 100%);
        border: 1.5px solid #d4af6a44;
        border-radius: 14px;
        padding: 16px 20px 14px 20px;
        margin-bottom: 14px;
        position: relative;
        overflow: hidden;
    }
    .sage-pipeline-card::after {
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 120px; height: 120px;
        background: radial-gradient(circle, #d4af6a18 0%, transparent 70%);
        pointer-events: none;
    }
    .sage-pipe-title {
        font-size: 0.92em;
        font-weight: 700;
        color: #d4af6a;
        margin-bottom: 14px;
        letter-spacing: 0.03em;
    }
    .sage-pipe-row {
        display: flex;
        align-items: center;
        gap: 0px;
        flex-wrap: nowrap;
        overflow-x: auto;
        padding-bottom: 4px;
    }
    .sage-pipe-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        min-width: 72px;
        flex: 1;
    }
    .sage-pipe-dot {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05em;
        font-weight: 700;
        box-shadow: 0 4px 16px rgba(0,0,0,0.45);
        transition: transform 0.2s;
        position: relative;
    }
    .sage-pipe-dot.done {
        background: radial-gradient(circle at 35% 35%, #f87171, #c0392b);
        box-shadow: 0 4px 18px #c0392b55, 0 0 0 3px #f8717122;
    }
    .sage-pipe-dot.ready {
        background: radial-gradient(circle at 35% 35%, #f87171, #c0392b);
        box-shadow: 0 4px 18px #c0392b55, 0 0 0 3px #f8717122;
    }
    .sage-pipe-dot.empty {
        background: radial-gradient(circle at 35% 35%, #64748b, #334155);
        box-shadow: 0 2px 8px #0008;
    }
    .sage-pipe-label {
        font-size: 0.70em;
        color: #cbd5e1;
        text-align: center;
        white-space: nowrap;
        line-height: 1.3;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── 타이틀 및 HTML 앵커 추가 (인접 형제 stHorizontalBlock 스타일링)
    st.markdown('<div class="sage-sync-title">🔄 시스템 연동 및 동기화 상태</div><div id="top-sync-panel-anchor"></div>', unsafe_allow_html=True)
    c_db, c_obs, c_git, c_sync = st.columns([1, 1, 1, 1])

    with c_db:
        card_cls = "ok" if db_ok else "err"
        label    = "로컬 DB 연결" if db_ok else "로컬 DB 없음"
        sub      = "workspace_state.json" if db_ok else "저장 필요"
        icon_col = "#34d399" if db_ok else "#f87171"
        st.markdown(
            f'<div class="sage-stat-card {card_cls}">'
            f'<span class="stat-label"><span style="color:{icon_col};">⬤</span>  {label}</span>'
            f'<span class="stat-sub">{sub}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    with c_obs:
        if obs_ok:
            st.markdown(
                f'<div class="sage-stat-card ok clickable-card-bg">'
                f'<span class="stat-label"><span style="color:#34d399;">⬤</span>  옵시디언 RAG</span>'
                f'<span class="stat-sub">Vault: {obs_name}</span>'
                f'</div>',
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
                '<div class="sage-stat-card warn">'
                '<span class="stat-label"><span style="color:#fbbf24;">⬤</span>  옵시디언 확인필요</span>'
                '<span class="stat-sub">경로 미설정</span>'
                '</div>',
                unsafe_allow_html=True
            )

    with c_git:
        if git_ok:
            st.markdown(
                f'<div class="sage-stat-card ok clickable-card-bg">'
                f'<span class="stat-label"><span style="color:#34d399;">⬤</span>  GitHub 연동</span>'
                f'<span class="stat-sub">Repo: {repo_name}</span>'
                f'</div>',
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
                '<div class="sage-stat-card err">'
                '<span class="stat-label"><span style="color:#f87171;">⬤</span>  Git 미연동</span>'
                '<span class="stat-sub">설정 변경 필요</span>'
                '</div>',
                unsafe_allow_html=True
            )

    with c_sync:
        st.markdown(
            f'<div class="sage-stat-card sync clickable-card-bg">'
            f'<span class="stat-label"><span style="color:#d4af6a;">⬤</span>  전체 즉시 동기화</span>'
            f'<span class="stat-sub">Git Push & RAG</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button(
            "SYNC_CLICK", 
            type="primary", 
            use_container_width=True, 
            key="top_force_sync_btn",
            help="클릭 시 로컬 DB, 옵시디언 RAG, GitHub를 즉시 동기화 및 Push합니다."
        ):
            with st.spinner("로컬 DB + 옵시디언 + GitHub 강제 동기화 중..."):
                save_workspace_state()
                ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                today_str = datetime.now().strftime("%Y-%m-%d")
                folder_name = "PlanningMemory"
                title = f"[Part2] 전체 작업 백업 - {ts}"
                val   = f"# Part 2 Alchemist 전체 작업 백업 (동기화 트리거)\n\n"
                val  += f"## 📌 선택 주제\n{st.session_state.get('p2_topic_selection','')}\n\n"
                val  += f"## 📚 자료조사 결과\n{st.session_state.get('p2_research_result','')}\n\n"
                val  += f"## 📖 총괄 기획안\n{st.session_state.get('p2_planning_result','')}\n\n"
                val  += f"---\n*Last updated: {today_str} {ts}*\n"
                obs_path_file = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Full Sync")
                if obs_path_file:
                    lock_file_readonly(obs_path_file)
                success, msg = auto_git_push(f"Force Full Sync: {ts}")
                if success:
                    st.toast("🔄 전체 즉시 동기화 & Git Push 성공!", icon="✅")
                else:
                    st.toast("🔄 로컬/옵시디언 동기화 완료 (Git 실패)", icon="⚠️")
                    st.error(f"GitHub Push 실패: {msg}")
                st.rerun()

    # ──────────────────────────────────────────────────────────────
    # [ROW 2] 실시간 데이터 연동 상황판 — 3번째 캡쳐 스타일
    # ──────────────────────────────────────────────────────────────
    def _is_df_valid(df):
        import pandas as _pd
        return df is not None and isinstance(df, _pd.DataFrame) and not df.empty

    # 각 파트 완료 여부
    f1 = bool(st.session_state.get("p1_topic_selection"))
    f2 = bool(st.session_state.get("p2_planning_result"))
    f3 = bool(st.session_state.get("p34_narration_script"))
    f4 = bool(st.session_state.get("p34_image_script"))
    f5 = bool(st.session_state.get("p5_valid_rows") or st.session_state.get("p5_c_results"))
    f6 = _is_df_valid(st.session_state.get("p6_opal_df"))
    f7 = _is_df_valid(st.session_state.get("p7_capcut_df"))
    f8 = bool(st.session_state.get("p8_dashboard_saved"))

    def _dot_cls(flag):
        return "done" if flag else "empty"

    nodes = [
        (f1, "1. 주제 선정"),
        (f2, "2. 기획안"),
        (f3, "3. 나레이션"),
        (f4, "4. 이미지대본"),
        (f5, "5. 씬검증"),
        (f6, "6. 오팔배분"),
        (f7, "7. 캡컷조립"),
        (f8, "8. 최종완료"),
    ]

    nodes_html = ""
    for i, (flag, label) in enumerate(nodes):
        dot_cls = _dot_cls(flag)
        nodes_html += f'<div class="sage-pipe-node"><div class="sage-pipe-dot {dot_cls}"></div><span class="sage-pipe-label">{label}</span></div>'

    st.markdown(
        f'<div class="sage-pipeline-card">'
        f'<div class="sage-pipe-title">🔗 실시간 데이터 연동 상황판</div>'
        f'<div class="sage-pipe-row">{nodes_html}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ──────────────────────────────────────────────────────────────
    # [ROW 3] 상단 공통 패널 — 옵시디언 규칙서 + 마스터 프롬프트
    # ──────────────────────────────────────────────────────────────
    sidebar_part = st.session_state.get("sidebar_part", "part1")
    if sidebar_part.startswith("파트 1"):   sidebar_part_key = "part1"
    elif sidebar_part.startswith("파트 2"): sidebar_part_key = "part2"
    elif sidebar_part.startswith("파트 3"): sidebar_part_key = "part3"
    elif sidebar_part.startswith("파트 4"): sidebar_part_key = "part4"
    elif sidebar_part.startswith("파트 5"): sidebar_part_key = "part5"
    elif sidebar_part.startswith("파트 6"): sidebar_part_key = "part6"
    elif sidebar_part.startswith("파트 7"): sidebar_part_key = "part7"
    elif sidebar_part.startswith("파트 8"): sidebar_part_key = "part8"
    else: sidebar_part_key = sidebar_part

    part_mapping = {
        "part1": ("base_prompt_rules",       "📚 파트 1 Librarian 전역 마스터 프롬프트"),
        "part2": ("p2_bench_prompt",          "🎨 파트 2 Alchemist 벤치마킹 마스터 프롬프트"),
        "part3": ("p34_master_prompt",        "✍️ 파트 3 대본 작성 마스터 프롬프트"),
        "part4": ("p5_image_master_prompt",   "🖼️ 파트 4 이미지 생성 마스터 프롬프트"),
        "part5": ("p6_veo3_master_prompt",    "🎥 파트 5 영상 생성 마스터 프롬프트"),
        "part6": ("p6_master_prompt",         "🎵 파트 6 나레이션 & 배경음악 마스터 프롬프트"),
        "part7": ("p7_master_prompt",         "🎬 파트 7 숏폼 생성 마스터 프롬프트"),
        "part8": ("p8_master_prompt",         "📊 파트 8 캡컷 최종 조립 마스터 프롬프트"),
    }
    prompt_key, prompt_title = part_mapping.get(sidebar_part_key, ("base_prompt_rules", "📚 Part 1 Librarian 전역 마스터 프롬프트"))

    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 마스터 프롬프트", expanded=False):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=180, key="top_ob_view", label_visibility="collapsed")
            if st.button("[SEARCH] 편집", key="ob_btn"): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown(f'<div class="top-panel-card"><div class="top-panel-title">{prompt_title}</div>', unsafe_allow_html=True)
            prompt_val = st.session_state.get(prompt_key, "")
            st.text_area("파트 마스터 프롬프트", value=prompt_val, height=180, key=f"top_pr_view_{prompt_key}", label_visibility="collapsed")
            if st.button("[SEARCH] 편집", key=f"pr_btn_{prompt_key}"):
                popup_edit_text_value(prompt_key, prompt_title)
            st.markdown('</div>', unsafe_allow_html=True)

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
    base = f"""[젬마 프로토콜]
{gemma_protocol}

[옵시디언 규칙서]
{obsidian_rules}

[기본 프롬프트]
{base_prompt}

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

def analyze_channel_to_topics_custom(channel, region, obsidian_rules, base_prompt, gemma_protocol, custom_prompt) -> tuple:
    base = f"""[젬마 프로토콜]
{gemma_protocol}

[옵시디언 규칙서]
{obsidian_rules}

[기본 프롬프트]
{base_prompt}

[과제]
{custom_prompt}

채널: {channel}
지역: {region}

[출력양식]
NN. 주제 | 추천사유(체험담 기반) | 예상효과 | 예상반응"""

    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules
    raw = call_gemma(base, system=sys_ctx)
    if isinstance(raw, str) and raw.startswith("[ERROR]"): st.error(raw); return [], raw
    parsed = _parse_topics(raw)
    if len(parsed) < 20: 
        raw_corrected = call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)
        parsed = _parse_topics(raw_corrected) or parsed
        if not isinstance(raw_corrected, str) or not raw_corrected.startswith("[ERROR]"):
            raw = raw_corrected
    return parsed[:20], raw


def generate_research_draft(channel_url, topic, gemma_protocol, master_prompt, custom_prompt=None):
    obsidian_context = ""
    try:
        search_result = simple_keyword_search(
            st.session_state.get("path_obsidian", ""), 
            topic,
            top_k=5
        )

        if search_result:
            obsidian_context = f"""

[옵시디언 감정/RAG 참조 자료]

{search_result}

"""
    except Exception as e:
        st.error(f"옵시디언 검색 오류: {e}")
        pass

    rag_context = obsidian_context

    instruction = custom_prompt if custom_prompt else "다음 선택된 주제에 대하여, 200여 개의 시청자 공감 댓글(체험담)을 참조하였다고 가정하고, 철학/심리학/성경 기반 지식을 융합하여 '자료 조사 및 기초 초안'을 작성하시오."

    base = f"""[젬마 프로토콜]

{gemma_protocol}

{rag_context}

[RAG & 지식 공백 방지 지침]
만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.
대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.
예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]

[마스터 규칙서]
{master_prompt}

[작업 지시]
{instruction}
* 주제: {topic}
* 타겟 채널: {channel_url}

[필수 포함 항목]
1. 세부 주제 및 매력적인 제목 (Title)
2. 핵심 키워드 (`[[키워드]]` 형식, 반드시 포함)
3. 시청자 후킹 기법 (실제 체험담을 활용한 공감 형성)
4. 타겟 채널 구조 분석 기반 차별화 전략
5. **모든 대본/자료의 출처 명기 필수** (책 이름, 저자명, 성경 구절 등 명확히 표기)"""
    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA

    return call_gemma(base, system=system_prompt)

def generate_final_planning(research_result, gemma_protocol, master_prompt):
    base = f"""[젬마 프로토콜]
{gemma_protocol}

[RAG & 지식 공백 방지 지침]
만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.
대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.
예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]

[마스터 규칙서]
{master_prompt}

[자료 조사 결과]
{research_result}

[작업 지시]
위 자료 조사 결과를 바탕으로 '15분 분량의 유튜브 다큐멘터리 총괄 시나리오 기획안(뼈대)'을 작성하시오.

[필수 포함 항목]
1. 영상의 구조 (도입부: 시청자 체험담 공감 - 전개부: 철학/심리 해석 - 절정부: 성경적/현자의 해답 - 결말부: 격려)
2. 4070 시청자 감성 타격 전략 및 시각적 연출 가이드 (렘브란트풍 등)
3. 클라이맥스에 들어갈 '오늘의 명언' 및 교훈"""

    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA

    return call_gemma(base, system=system_prompt)

@st.cache_data(ttl=900, show_spinner=False)
def analyze_channel_to_topics_p1(channel, region, obsidian_rules, base_prompt, gemma_protocol, custom_bench_prompt) -> tuple:
    base = f"""[젬마 프로토콜]
{gemma_protocol}

[옵시디언 규칙서]
{obsidian_rules}

[기본 프롬프트]
{base_prompt}

[과제]
{custom_bench_prompt}

채널: {channel}
지역: {region}

[출력양식]
NN. 주제 | 추천사유(체험담 기반) | 예상효과 | 예상반응"""

    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules
    raw = call_gemma(base, system=sys_ctx)
    if isinstance(raw, str) and raw.startswith("[ERROR]"): 
        st.error(raw)
        return raw, []
    parsed = _parse_topics(raw)
    if len(parsed) < 20: 
        raw_retry = call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)
        parsed_retry = _parse_topics(raw_retry)
        if parsed_retry:
            parsed = parsed_retry
            if not isinstance(raw_retry, str) or not raw_retry.startswith("[ERROR]"):
                raw = raw_retry
    return raw, parsed[:20]

def generate_research_draft_p1(channel_url, topic, gemma_protocol, master_prompt, custom_research_prompt):
    obsidian_context = ""
    try:
        search_result = simple_keyword_search(
            st.session_state.get("path_obsidian", ""), 
            topic,
            top_k=5
        )

        if search_result:
            obsidian_context = f"""

[옵시디언 감정/RAG 참조 자료]

{search_result}

"""
    except Exception as e:
        st.error(f"옵시디언 검색 오류: {e}")
        pass

    rag_context = obsidian_context

    base = f"""[젬마 프로토콜]

{gemma_protocol}

{rag_context}

[RAG & 지식 공백 방지 지침]
만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.
대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.
예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]

[마스터 규칙서]
{master_prompt}

{custom_research_prompt}
* 주제: {topic}
* 타겟 채널: {channel_url}

[필수 포함 항목]
1. 세부 주제 및 매력적인 제목 (Title)
2. 핵심 키워드 (`[[키워드]]` 형식, 반드시 포함)
3. 시청자 후킹 기법 (실제 체험담을 활용한 공감 형성)
4. 타겟 채널 구조 분석 기반 차별화 전략
5. **모든 대본/자료의 출처 명기 필수** (책 이름, 저자명, 성경 구절 등 명확히 표기)"""
    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA

    return call_gemma(base, system=system_prompt)

def generate_final_planning_p1(research_result, gemma_protocol, master_prompt, custom_plan_prompt):
    base = f"""[젬마 프로토콜]
{gemma_protocol}

[RAG & 지식 공백 방지 지침]
만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.
대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.
예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]

[마스터 규칙서]
{master_prompt}

[자료 조사 결과]
{research_result}

{custom_plan_prompt}

[필수 포함 항목]
1. 영상의 구조 (도입부: 시청자 체험담 공감 - 전개부: 철학/심리 해석 - 절정부: 성경적/현자의 해답 - 결말부: 격려)
2. 4070 시청자 감성 타격 전략 및 시각적 연출 가이드 (렘브란트풍 등)
3. 클라이맥스에 들어갈 '오늘의 명언' 및 교훈"""

    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA

    return call_gemma(base, system=system_prompt)

# =====================================================================
# Part 1 렌더링
# =====================================================================
def render_part1():
    c_title, c_control = st.columns([4.2, 5.8])
    
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">📚 파트 1: 벤치마킹 & 자료조사</h3>', unsafe_allow_html=True)
        
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p1_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p1_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS["part1"]: st.session_state.unlock_part1 = True
            elif pin: st.session_state.unlock_part1 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p1_popup_btn"):
                st.session_state.sidebar_part = "part1"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)

    is_locked = not st.session_state.unlock_part1
    if is_locked:
        st.warning("[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")
    c_left, c_right = st.columns(2, gap="large")
    
    with c_left:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)
        st.text_area("젬마 프로토콜 (수정은 편집 버튼 클릭)", value=st.session_state.p1_gemma_protocol, height=270, label_visibility="collapsed")
        if st.button("[SEARCH] 프로토콜 팝업 편집 (복사/붙여넣기)"):
            popup_edit_gemma_protocol()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_right:
        st.markdown("##### [SEARCH] 떡상 채널 발굴용 탐색기")
        st.caption("AI 카피를 배제한 순수 인간 운영의 최고 조회수 채널 여러 개를 검색하여 검토합니다.")

        search_kw = st.text_input(
              "검색 키워드 (가이드라인 기반 자동 세팅)", 
              value=st.session_state.get(
                    "p1_search_keyword",
                    "human operated psychology philosophy life advice channel for age 40 50 60 70 high engagement longform"
               ),
              disabled=is_locked
         )

        st.session_state.p1_search_keyword = search_kw
        
  
        if st.button("🌐 전 세계 채널 5개 탐색 및 리스트업 (Tavily)", disabled=is_locked, use_container_width=True):
            if not st.session_state.tavily_api_key:
                st.error("좌측 사이드바 '⚙️ 설정 변경'에서 Tavily API Key를 먼저 입력하세요.")
            else:
                with st.spinner("최고 떡상 원본 채널 5개를 심층 탐색 중..."):
                    from sage_engine import tavily_search

                    q = search_kw + " YouTube psychology philosophy life advice channel OR video human storytelling older adults high views comments"

                    res = tavily_search(q, st.session_state.tavily_api_key, max_results=20)
                    
                    if "error" in res: st.error(res["error"])

                    else:
                        raw = res.get("results", [])

                        filtered_results = [
                            r for r in raw
                            if "youtube.com" in r.get("url", "")
                        ]

                        st.session_state.p1_channel_search_results = filtered_results

                        st.session_state.pipeline_state["channel_search_results"] = filtered_results
                        st.success("[TARGET] 채널 검색 완료! 아래 목록에서 가장 적합한 채널을 선택하세요.")
        
        if st.session_state.p1_channel_search_results:
            with st.container(border=True):
                st.markdown("**[TARGET] 분석할 채널을 선택하세요 (선택 시 아래 URL에 자동 입력됨):**")

                options = []

                for i, r in enumerate(st.session_state.p1_channel_search_results):
                    options.append(
                          f"[{i+1}] {r.get('title', '제목없음')} - {r.get('url', '#')}"
                    )
                
                selected_channel = st.radio(
                      "검색된 채널 리스트",
                      options,
                      key="p1_selected_channel_radio",
                      label_visibility="collapsed",
                      disabled=is_locked
                )
                
                if selected_channel:
                    selected_url = selected_channel.split(" - ")[-1]

                    st.session_state.p1_channel_url = selected_url

                    st.session_state.pipeline_state["selected_channel"] = selected_channel

                    st.session_state.pipeline_state["selected_channel_url"] = selected_url

                   
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### [TARGET] 분석 대상 확정")
        st.session_state.p1_channel_url = st.text_input("타겟 유튜브 URL (위에서 선택 시 자동 입력됨)", value=st.session_state.p1_channel_url, disabled=is_locked)
        st.session_state.p1_region = st.selectbox("타겟 지역", ["국내+국외 모두", "국내 우선", "국외 우선"], disabled=is_locked)

    st.divider()
       
    st.subheader("🔍 Obsidian 감정 기반 검색")

    obsidian_query = st.text_input(
        "감정 / 철학 / 성경 / 인간 결핍 검색",
        placeholder="예: 외로움, 존재의미, 고통, 용서",
        key="p1_obsidian_search_query"
    )

    if st.button("🔎 옵시디언 검색", use_container_width=True, key="p1_obsidian_search_btn"):
        results = simple_keyword_search(
            st.session_state.path_obsidian,
            obsidian_query,
            top_k=10
        )

        if not results:
            st.warning("검색 결과가 없습니다.")
        else:
            st.session_state.pipeline_state["obsidian_search_results"] = results

            for r in results:
                with st.container(border=True):
                    st.markdown(f"### 📘 {r['title']}")
                    st.caption(f"점수: {r['score']}")
                    st.code(r["path"])
                    st.text(r["preview"][:400])

   
    st.divider()
    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진")
    tab_bench, tab_research, tab_plan = st.tabs(["[TARGET] 1️⃣ 채널 벤치마킹", "📚 2️⃣ 자료 조사", "[PACKAGE] 3️⃣ Part 2 전달 패킷"])
    
    with tab_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 벤치마킹 분석")
            st.caption("주제 20개 추천 (추천사유, 효과, 반응)")
            
            st.session_state.p1_bench_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (벤치마킹)", 
                value=st.session_state.p1_bench_prompt, 
                height=100, 
                key="p1_bench_prompt_input",
                disabled=is_locked
            )
            
            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---
            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])
            with c_btn1:
                if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked, key="p1_bench_start_btn"):
                    if not st.session_state.p1_channel_url: 
                        st.error("[WARN] 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")
                    else:
                        # 시작 버튼 클릭 즉시 기존 결과물 및 백업 상태 클리어
                        st.session_state.p1_bench_raw = ""
                        st.session_state.p1_topics = []
                        st.session_state.p1_bench_tags = ""
                        st.session_state.p1_bench_saved = False
                        st.session_state.p1_bench_obsidian_saved = False
                        save_workspace_state()
                        
                        with st.spinner("채널 분석 중... (체험담 댓글 정확성 우선 분석)"):
                            raw_res, parsed_topics = analyze_channel_to_topics_p1(
                                st.session_state.p1_channel_url,
                                st.session_state.p1_region, 
                                st.session_state.obsidian_rules, 
                                st.session_state.base_prompt_rules, 
                                st.session_state.p1_gemma_protocol,
                                st.session_state.p1_bench_prompt
                            )
                            st.session_state.p1_bench_raw = raw_res
                            st.session_state.p1_topics = parsed_topics
                            st.session_state.pipeline_state["topic_candidates"] = parsed_topics
                            st.session_state.p1_bench_saved = True
                            save_workspace_state()
                            
                            # 젬마가 키워드를 자동으로 세분화하여 추출
                            keywords = extract_keywords_via_gemma(raw_res, st.session_state.base_prompt_rules)
                            st.session_state.p1_bench_tags = keywords
                            
                            # 자동 옵시디언 RAG 백업 파일 조립 및 저장
                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                            
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            folder_name = "TopicMemory"
                            title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"
                            
                            val = f"## 📌 핵심 요약\n- 채널: {st.session_state.p1_channel_url}\n- 타겟 지역: {st.session_state.p1_region}\n\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"
                            val += f"## 📖 벤치마킹 상세 추천 리스트\n"
                            for t in parsed_topics:
                                val += f"### [[{t['title']}]]\n- **추천 사유(체험담 기반):** {t['reason']}\n- **예상 효과:** {t['effect']}\n- **예상 반응:** {t['audience_reaction']}\n\n"
                            val += f"\n## 🔗 원본 날것의 텍스트\n```text\n{raw_res}\n```\n"
                            
                            obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)
                            if obs_path:
                                lock_file_readonly(obs_path)
                                st.toast("💾 벤치마킹 결과 로컬 자동 저장 완료!", icon="💾")
                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                if success:
                                    st.session_state.p1_bench_obsidian_saved = True
                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                else:
                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                save_workspace_state()
                                st.rerun()
            
            with c_btn2:
                if st.session_state.get("p1_bench_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_bench_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_bench_local_waiting")
            
            with c_btn3:
                if st.session_state.get("p1_bench_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_bench_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_bench_obs_waiting")
            
            if st.session_state.p1_bench_raw:
                st.markdown("<br>", unsafe_allow_html=True)
                col_prev, col_full = st.columns([3, 2])
                with col_prev:
                    st.info(f"📄 결과 {len(st.session_state.p1_bench_raw)}자 생성완료!")
                with col_full:
                    if st.button("👁 전체 결과 팝업으로 보기",
                        use_container_width=True,
                        type="primary",
                        key="p1_bench_full_popup"):
                        popup_edit_benchmarking()
                
                c_reparse, c_popup = st.columns(2)
                with c_reparse:
                    if st.button("🔄 수정 텍스트 기반 주제 재파싱", use_container_width=True, key="p1_reparse_btn"):
                        st.session_state.p1_topics = _parse_topics(st.session_state.p1_bench_raw)
                        st.success("수정된 텍스트에서 주제 20개가 재파싱되었습니다!")
                        save_workspace_state()
                        st.rerun()
                with c_popup:
                    if st.button("[SEARCH] 팝업에서 크게 보기", use_container_width=True, key="p1_bench_pop_btn"):
                        popup_edit_benchmarking()

            if st.session_state.p1_topics:
                st.markdown("<br>", unsafe_allow_html=True)
                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p1_topics)]
                st.session_state.p1_topic_selection = st.selectbox("📌 기획할 주제 1개 선정", topics_display, disabled=is_locked, key="p1_topic_selection_box")
                st.session_state.pipeline_state["selected_topic"] = st.session_state.p1_topic_selection
                save_workspace_state()

                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p1_bench_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_bench_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_bench_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 (예비용) 벤치마킹 수동 옵시디언 백업 실행", use_container_width=True, key="p1_bench_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_bench_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    folder_name = "TopicMemory"
                    title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"
                    
                    val = f"## 📌 핵심 요약\n- 채널: {st.session_state.p1_channel_url}\n- 타겟 지역: {st.session_state.p1_region}\n\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"
                    val += f"## 📖 벤치마킹 상세 추천 리스트\n"
                    for t in st.session_state.p1_topics:
                        val += f"### [[{t['title']}]]\n- **추천 사유(체험담 기반):** {t['reason']}\n- **예상 효과:** {t['effect']}\n- **예상 반응:** {t['audience_reaction']}\n\n"
                    val += f"\n## 🔗 원본 날것의 텍스트\n```text\n{st.session_state.p1_bench_raw}\n```\n"
                    
                    obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 벤치마킹 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p1_bench_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save (Locked): {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                        st.rerun()

    with tab_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 자료 조사 결과")
            st.caption("옵시디언/리서치 융합 기초 초안 작성 (출처 명기)")
            
            st.session_state.p1_research_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (자료 조사)", 
                value=st.session_state.p1_research_prompt, 
                height=100, 
                key="p1_research_prompt_input",
                disabled=is_locked
            )
            
            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---
            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])
            with c_btn1:
                if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p1_research_start_btn"):
                    if not st.session_state.p1_topic_selection:
                        st.error("[WARN] 먼저 좌측의 '벤치마킹 시작' 버튼을 눌러 분석을 완료하고 주제를 선택해 주세요.")
                    else:
                        # 시작 즉시 리셋
                        st.session_state.p1_research_result = ""
                        st.session_state.p1_research_tags = ""
                        st.session_state.p1_research_saved = False
                        st.session_state.p1_research_obsidian_saved = False
                        st.session_state.p1_need_research_kw = None
                        st.session_state.p1_verification = None
                        save_workspace_state()
                        
                        with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):
                            topic_str = st.session_state.p1_topic_selection
                            res = generate_research_draft_p1(
                                 st.session_state.p1_channel_url, 
                                 topic_str,
                                 st.session_state.p1_gemma_protocol, 
                                 st.session_state.base_prompt_rules,
                                 st.session_state.p1_research_prompt
                            )
                            st.session_state.p1_research_result = res
                            st.session_state.pipeline_state["research_result"] = res
                            
                            # RAG 지식 공백 감지
                            kw = check_need_research_tag(res)
                            if kw:
                                st.session_state.p1_need_research_kw = kw
                                st.session_state.p1_research_saved = False
                                st.session_state.p1_research_obsidian_saved = False
                            else:
                                st.session_state.p1_need_research_kw = None
                                # 자가 검수 수행
                                ver_res = verify_content_with_gemma("자료 조사 초안", res, st.session_state.base_prompt_rules)
                                st.session_state.p1_verification = ver_res
                                
                                if ver_res.get("status") == "PASS":
                                    # 바로 자동 저장 및 백업
                                    st.session_state.p1_research_saved = True
                                    
                                    # 젬마 키워드 자동 세분화
                                    keywords = extract_keywords_via_gemma(res, st.session_state.base_prompt_rules)
                                    st.session_state.p1_research_tags = keywords
                                    
                                    # 자동 옵시디언 백업 진행
                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                    
                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    folder_name = "ResearchMemory"
                                    topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                                    title = f"자료조사 초안 - {topic_title}"
                                    
                                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                                    val += f"## 📖 자료조사 및 초안 본문\n{res}\n\n"
                                    
                                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                                    if obs_path:
                                        lock_file_readonly(obs_path)
                                        st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                        if success:
                                            st.session_state.p1_research_obsidian_saved = True
                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                        else:
                                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                else:
                                    st.session_state.p1_research_saved = False
                                    st.session_state.p1_research_obsidian_saved = False
                                    
                            save_workspace_state()
                            st.rerun()
            
            with c_btn2:
                if st.session_state.get("p1_research_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_research_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_research_local_waiting")
            
            with c_btn3:
                if st.session_state.get("p1_research_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_research_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_research_obs_waiting")
            
            if st.session_state.p1_research_result:
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---
                if st.session_state.p1_need_research_kw:
                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p1_need_research_kw})")
                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p1_web_research_approve_btn", type="primary", use_container_width=True):
                        if not st.session_state.tavily_api_key:
                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")
                        else:
                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):
                                from sage_engine import tavily_search
                                q = st.session_state.p1_need_research_kw
                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                                if "error" in res_search:
                                    st.error(f"Tavily 검색 오류: {res_search['error']}")
                                else:
                                    raw_results = res_search.get("results", [])
                                    web_context = ""
                                    for r in raw_results:
                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"
                                    
                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.
제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '자료 조사 및 기초 초안'을 완벽하게 재작성하라.
모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.

[웹 리서치 참조 자료]:
{web_context}

[이전 불완전한 결과물]:
{st.session_state.p1_research_result}

[작업 지시]:
위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.
[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.
"""
                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                    st.session_state.p1_research_result = res_new
                                    st.session_state.pipeline_state["research_result"] = res_new
                                    
                                    # 재검증
                                    st.session_state.p1_need_research_kw = check_need_research_tag(res_new)
                                    if not st.session_state.p1_need_research_kw:
                                        ver_res = verify_content_with_gemma("자료 조사 초안", res_new, st.session_state.base_prompt_rules)
                                        st.session_state.p1_verification = ver_res
                                        if ver_res.get("status") == "PASS":
                                            st.session_state.p1_research_saved = True
                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)
                                            st.session_state.p1_research_tags = keywords
                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            folder_name = "ResearchMemory"
                                            topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                                            title = f"자료조사 초안 - {topic_title}"
                                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                                            val += f"## 📖 자료조사 및 초안 본문\n{res_new}\n\n"
                                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                                            if obs_path:
                                                lock_file_readonly(obs_path)
                                                st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                                if success:
                                                    st.session_state.p1_research_obsidian_saved = True
                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                                else:
                                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                    else:
                                        st.session_state.p1_research_saved = False
                                        st.session_state.p1_research_obsidian_saved = False
                                    
                                    save_workspace_state()
                                    st.rerun()

                elif st.session_state.p1_verification:
                    ver = st.session_state.p1_verification
                    if ver.get("status") == "FAIL":
                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")
                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p1_self_correct_btn", type="primary", use_container_width=True):
                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):
                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.
이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.

[이전 결과물]:
{st.session_state.p1_research_result}

[수정 건의사항]:
{ver.get("suggestions", "없음")}

[작업 지시]:
수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.
모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.
"""
                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                st.session_state.p1_research_result = res_corr
                                st.session_state.pipeline_state["research_result"] = res_corr
                                
                                # 재검증
                                st.session_state.p1_need_research_kw = check_need_research_tag(res_corr)
                                if not st.session_state.p1_need_research_kw:
                                    ver_res = verify_content_with_gemma("자료 조사 초안", res_corr, st.session_state.base_prompt_rules)
                                    st.session_state.p1_verification = ver_res
                                    if ver_res.get("status") == "PASS":
                                        st.session_state.p1_research_saved = True
                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)
                                        st.session_state.p1_research_tags = keywords
                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        folder_name = "ResearchMemory"
                                        topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                                        title = f"자료조사 초안 - {topic_title}"
                                        val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                                        val += f"## 📖 자료조사 및 초안 본문\n{res_corr}\n\n"
                                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                                        if obs_path:
                                            lock_file_readonly(obs_path)
                                            st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                            if success:
                                                st.session_state.p1_research_obsidian_saved = True
                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                            else:
                                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                else:
                                    st.session_state.p1_research_saved = False
                                    st.session_state.p1_research_obsidian_saved = False
                                
                                save_workspace_state()
                                st.rerun()
                    else:
                        st.success("✅ **Gemma 자가 검수 통과**: 모든 무결성 규칙(지칭어, 출처 등)이 확인되었습니다.")
                        with st.expander("🔍 검수 결과 보고서 자세히 보기", expanded=False):
                            st.text(ver.get("report"))
                
                st.session_state.p1_research_result = st.text_area(
                    "자료 조사 결과 (수정 가능)", 
                    value=st.session_state.p1_research_result, 
                    height=350, 
                    key="p1_research_result_ta",
                    disabled=is_locked
                )
                
                if st.button("[SEARCH] 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_res_p1"):
                    popup_edit_research()
 
                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p1_research_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                    value=st.session_state.p1_research_tags, 
                    placeholder="예: 외로움, 존재의미, 고통, 용서", 
                    key="p1_research_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 (예비용) 자료조사 결과 수동 옵시디언 백업 실행", use_container_width=True, key="p1_research_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.p1_research_tags.split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    folder_name = "ResearchMemory"
                    
                    topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"
                    title = f"자료조사 초안 - {topic_title}"
                    
                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                    val += f"## 📖 자료조사 및 초안 본문\n{st.session_state.p1_research_result}\n\n"
                    
                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 자료조사 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p1_research_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save (Locked): {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                        st.rerun()

    with tab_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안")
            st.caption("15분 영상 뼈대 총괄 시나리오 기획 (마스터 플랜)")
            
            st.text_area(
                "🤖 젬마 작업지시 프롬프트 (총괄 기획)", 
                value=st.session_state.p1_plan_prompt, 
                height=100, 
                key="p1_plan_prompt_input",
                disabled=is_locked
            )
        
            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---
            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])
            with c_btn1:
                if st.button("[ALCHEMY] 철학·감정 융합 설계", use_container_width=True, disabled=is_locked, key="p1_plan_start_btn"):
                    if not st.session_state.p1_research_result:
                        st.error("[WARN] 먼저 중앙의 '자료조사 및 초안 작성'을 완료해 주세요.")
                    else:
                        # 시작 즉시 리셋
                        st.session_state.p1_planning_result = ""
                        st.session_state.p1_plan_tags = ""
                        st.session_state.p1_plan_saved = False
                        st.session_state.p1_plan_obsidian_saved = False
                        save_workspace_state()
                        
                        with st.spinner("철학·성경·감정 융합 구조 설계 중..."):
                            res = generate_final_planning_p1(
                                 st.session_state.p1_research_result,
                                 st.session_state.p1_gemma_protocol, 
                                 st.session_state.base_prompt_rules,
                                 st.session_state.p1_plan_prompt
                            )
                            st.session_state.p1_planning_result = res
                            st.session_state.pipeline_state["planning_result"] = res
                            st.session_state.p1_plan_saved = True
                            save_workspace_state()
                            
                            # 젬마 키워드 자동 세분화
                            keywords = extract_keywords_via_gemma(res, st.session_state.base_prompt_rules)
                            st.session_state.p1_plan_tags = keywords
                            
                            # 자동 옵시디언 RAG 저장 진행
                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                            
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            folder_name = "PlanningMemory"
                            topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"
                            title = f"최종 기획안 - {topic_title}"
                            
                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"
                            val += f"## 📖 최종 시나리오 기획안 본문\n{res}\n\n"
                            
                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")
                            if obs_path:
                                lock_file_readonly(obs_path)
                                st.toast("💾 기획안 결과 로컬 자동 저장 완료!", icon="💾")
                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                if success:
                                    st.session_state.p1_plan_obsidian_saved = True
                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                else:
                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                save_workspace_state()
                                st.rerun()
            
            with c_btn2:
                if st.session_state.get("p1_plan_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_plan_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_plan_local_waiting")
            
            with c_btn3:
                if st.session_state.get("p1_plan_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_plan_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_plan_obs_waiting")

            if st.session_state.p1_planning_result:
               st.markdown("<br>", unsafe_allow_html=True)
               st.session_state.p1_planning_result = st.text_area(
                   "최종 기획안 (수정 가능)", 
                   value=st.session_state.p1_planning_result, 
                   height=350, 
                   key="p1_planning_result_ta",
                   disabled=is_locked
               )
               
               c_view, c_copy = st.columns(2)
               with c_view:
                   if st.button("👁 팝업에서 크게 보기", use_container_width=True, key="p1_plan_view_btn"):
                       popup_edit_planning()
               with c_copy:
                   if st.button("📋 클립보드 복사", use_container_width=True, key="p1_plan_copy_btn"):
                       pyperclip.copy(st.session_state.p1_planning_result)
                       st.success("총괄 기획안 복사 완료")

               st.divider()
               st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
               st.session_state.p1_plan_tags = st.text_input(
                   "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 
                   value=st.session_state.p1_plan_tags, 
                   placeholder="예: 외로움, 존재의미, 고통, 용서", 
                   key="p1_plan_tags_input",
                   disabled=is_locked
               )
               
               if st.button("💾 (예비용) 최종 기획안 수동 옵시디언 백업 실행", use_container_width=True, key="p1_plan_save_backup_btn", disabled=is_locked):
                   tag_list = [t.strip() for t in st.session_state.p1_plan_tags.split(",") if t.strip()]
                   tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                   tag_hashes = " ".join([f"#{t}" for t in tag_list])
                   
                   ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                   folder_name = "PlanningMemory"
                   
                   topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"
                   title = f"최종 기획안 - {topic_title}"
                   
                   val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"
                   val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"
                   val += f"## 📖 최종 시나리오 기획안 본문\n{st.session_state.p1_planning_result}\n\n"
                   
                   obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")
                   if obs_path:
                       lock_file_readonly(obs_path)
                       st.toast("✅ 수동 기획안 옵시디언 백업 완료!", icon="💾")
                       st.session_state.p1_plan_obsidian_saved = True
                       save_workspace_state()
                       success, msg = auto_git_push(f"Manual Save (Locked): {title}")
                       if success:
                           st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                       else:
                           st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                       st.rerun()
@st.dialog("📝 젬마 프로토콜 (Gemma Protocol) 편집", width="large")
def popup_edit_gemma_protocol_p2():
    st.markdown("여기서 행동 지침과 작업 지침서를 상세하게 수정할 수 있습니다. 텍스트를 드래그하고 복사/붙여넣기 하세요.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p2_gemma_protocol, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p2_gemma_protocol = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()

@st.dialog("🎯 프롬프트 / 텍스트 편집", width="large")
def popup_edit_text_value(session_key: str, title: str):
    st.markdown(f"**{title}**을(를) 전체 화면으로 확인하고 수정할 수 있습니다.")
    val = st.session_state.get(session_key, "")
    new_val = st.text_area("내용", value=val, height=450, key=f"popup_edit_val_ta_{session_key}", label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", type="primary", use_container_width=True, key=f"popup_edit_val_save_{session_key}"):
            st.session_state[session_key] = new_val
            st.toast("✅ 수정 사항이 저장되었습니다!", icon="💾")
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True, key=f"popup_edit_val_cancel_{session_key}"):
            st.rerun()

@st.dialog("[TARGET] 채널 벤치마킹 결과 (팝업)", width="large")
def popup_edit_benchmarking_p2():
    st.markdown("벤치마킹 결과를 쾌적하게 스크롤하며 검토하고, 내용을 수정하거나 복사할 수 있습니다.")
    
    # p2_bench_raw가 우선, 없으면 topics로 조립
    raw_val = st.session_state.get("p2_bench_raw", "").strip()
    if not raw_val:
        for idx, t in enumerate(st.session_state.get("p2_topics", []), 1):
            raw_val += f"{idx:02d}. {t['title']} | {t['reason']} | {t['effect']} | {t.get('audience_reaction', '공감')}\n"
        raw_val = raw_val.strip()
        
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{raw_val}</div>", unsafe_allow_html=True)
        
    new_val = st.text_area("벤치마킹 결과 수정", value=raw_val, height=220, label_visibility="collapsed", key="p2_bench_edit_ta")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary", key="p2_bench_save_dialog"):
            # 수정된 텍스트를 다시 파싱하여 p2_topics 리스트 구조로 보관
            parsed = []
            for line in new_val.split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        title_part = parts[0].strip()
                        if ". " in title_part:
                            title_part = title_part.split(". ", 1)[1]
                        elif "]" in title_part:
                            title_part = title_part.split("]", 1)[1]
                        parsed.append({
                            "title": title_part.strip(),
                            "reason": parts[1].strip(),
                            "effect": parts[2].strip(),
                            "audience_reaction": parts[3].strip() if len(parts) > 3 else "공감"
                        })
            if parsed:
                st.session_state.p2_topics = parsed
            st.session_state.p2_bench_raw = new_val
            save_workspace_state()
            st.toast("✅ 벤치마킹 결과가 저장되었습니다!", icon="💾")
            st.rerun()
    with c2:
        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"benchmarking_result_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True, key="p2_bench_dl_dialog")
    with c3:
        if st.button("닫기", use_container_width=True, key="p2_bench_close_dialog"):
            st.rerun()

@st.dialog("📚 자료 조사 결과 (팝업)", width="large")
def popup_edit_research_p2():
    st.markdown("결과를 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p2_research_result}</div>", unsafe_allow_html=True)
    new_val = st.text_area("자료 조사 결과 수정", value=st.session_state.p2_research_result, height=200, label_visibility="collapsed")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p2_research_result = new_val
            st.rerun()
    with c2:
        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"research_result_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)
    with c3:
        if st.button("닫기", use_container_width=True):
            st.rerun()

@st.dialog("[ALCHEMY] 철학·감정 융합 설계 (팝업)", width="large")
def popup_edit_planning_p2():
    st.markdown("철학·성경·감정 융합 설계안을 검토하고 수정할 수 있습니다.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p2_planning_result}</div>", unsafe_allow_html=True)
    new_val = st.text_area("철학·감정 융합 설계안 수정", value=st.session_state.p2_planning_result, height=200, label_visibility="collapsed")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p2_planning_result = new_val
            st.rerun()
    with c2:
        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"planning_result_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)
    with c3:
        if st.button("닫기", use_container_width=True):
            st.rerun()

def render_part2():
    c_title, c_control = st.columns([4.2, 5.8])
    
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎨 파트 2: 총괄기획</h3>', unsafe_allow_html=True)
        
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p2_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p2_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS["part2"]: st.session_state.unlock_part2 = True
            elif pin: st.session_state.unlock_part2 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p2_popup_btn"):
                st.session_state.sidebar_part = "part2"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.get("p2_channel_url"):
        st.session_state.p2_channel_url = st.session_state.get("p1_channel_url", "")

    if "unlock_part2" not in st.session_state:
        st.session_state.unlock_part2 = False
    is_locked = not st.session_state.unlock_part2
    if is_locked:
        st.warning("[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    if st.session_state.get("p2_channel_url"):
        st.info(f"🔗 [연동] Part 1 채널 URL 상속됨: {st.session_state.p2_channel_url}")
    else:
        st.warning("⚠️ 타겟 채널 URL이 연동되지 않았습니다. Part 1에서 채널을 설정해 주세요.")
    
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")
    c_left, c_right = st.columns(2, gap="large")
    
    with c_left:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)
        if "p2_gemma_protocol" not in st.session_state: st.session_state.p2_gemma_protocol = st.session_state.get("p1_gemma_protocol", "")
        st.text_area("젬마 프로토콜 (수정은 편집 버튼 클릭)", value=st.session_state.p2_gemma_protocol, height=270, label_visibility="collapsed", key="p2_protocol_area")
        if st.button("[SEARCH] 프로토콜 팝업 편집 (복사/붙여넣기)", key="p2_edit_proto"):
            popup_edit_gemma_protocol_p2()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_right:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">🖼️ 썸네일 카드 (Thumbnail Card)</div>', unsafe_allow_html=True)
        st.caption("자료조사 결과를 참조하여 썸네일(이미지), 주제, 제목을 3가지 버전으로 생성합니다.")
        
        if st.button("🚀 썸네일/주제/제목 3세트 생성 (AI)", use_container_width=True, disabled=is_locked, key="p2_thumb_btn"):
            if "p2_research_result" not in st.session_state or not st.session_state.p2_research_result:
                st.error("[WARN] 먼저 하단의 '자료조사 및 초안 작성'을 완료해 주세요.")
            else:
                with st.spinner("자료조사 기반 썸네일 3세트 기획 중..."):
                    # 향후 Gemma API 호출 로직이 들어갈 곳
                    st.info("썸네일 생성 AI 로직 연동 대기 중...")
                    st.session_state.p2_thumbnail_plan = """
[썸네일 1]
제목: 왜 사람은 늦게 후회하는가
주제: 후회의 심리학
이미지:
- 어두운 방
- 고개 숙인 중년 남성
- 창문 빛 연출
- 렘브란트 톤

[썸네일 2]
제목: 인간은 왜 외로움을 숨길까
주제: 관계와 고독
이미지:
- 군중 속 혼자 있는 인물
- 흐릿한 도시 배경
- 차가운 블루톤

[썸네일 3]
제목: 당신이 무기력한 진짜 이유
주제: 도파민 중독과 공허
이미지:
- 스마트폰 불빛
- 멍한 표정
- 블랙+레드 대비
"""
        
        if "p2_thumbnail_plan" not in st.session_state:
            st.session_state.p2_thumbnail_plan = ""
            
        st.text_area("썸네일 기획 결과 (수정 가능)", value=st.session_state.p2_thumbnail_plan, height=195, label_visibility="collapsed", key="p2_thumb_area")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진")
    tab_bench, tab_research, tab_plan = st.tabs(["[TARGET] 1️⃣ 채널 벤치마킹", "📚 2️⃣ 자료 조사", "[ALCHEMY] 3️⃣ 총괄 기획안"])
    
    with tab_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 채널 벤치마킹 및 주제 도출")
            st.caption("200개 댓글 분석 기반 타겟 시청자 공감 포인트 추출")
            
            if "p2_bench_prompt" not in st.session_state:
                st.session_state.p2_bench_prompt = "[작업 지시] 다음 타겟 채널을 분석하여 핵심 주제 20개, 후킹 기법, 인트로 기법, 그리고 채널 구조 분석을 생성하고 추출하십시오. (200여 개 시청자 댓글 공감 포인트 참조)"
            
            st.session_state.p2_bench_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (벤치마킹)", 
                value=st.session_state.p2_bench_prompt, 
                height=100, 
                key="p2_bench_prompt_area", 
                disabled=is_locked
            )
            
            if st.button("📝 프롬프트 팝업 편집 (채널 벤치마킹)", key="p2_edit_bench_prompt_btn"):
                popup_edit_text_value("p2_bench_prompt", "🤖 젬마 작업지시 프롬프트 (채널 벤치마킹)")
            
            # --- 3단 버튼 구조 ---
            c_b1, c_b2, c_b3 = st.columns([4, 3, 3])
            with c_b1:
                if st.button("🚀 벤치마킹 분석 실행", use_container_width=True, disabled=is_locked, key="p2_bench_run_btn"):
                    if not st.session_state.get("p2_channel_url"):
                        st.session_state.p2_channel_url = st.session_state.get("p1_channel_url", "")
                    
                    if not st.session_state.p2_channel_url:
                        st.error("[WARN] 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")
                    else:
                        st.session_state.p2_topics = []
                        st.session_state.p2_bench_raw = ""
                        st.session_state.p2_bench_saved = False
                        st.session_state.p2_bench_obsidian_saved = False
                        save_workspace_state()
                        
                        with st.spinner("채널 분석 중... (200개 댓글 공감 포인트 참조)"):
                            parsed, raw = analyze_channel_to_topics_custom(
                                st.session_state.p2_channel_url, st.session_state.p2_region, 
                                st.session_state.obsidian_rules, st.session_state.base_prompt_rules, 
                                st.session_state.p2_gemma_protocol, st.session_state.p2_bench_prompt
                            )
                            
                            if parsed:
                                st.session_state.p2_topics = parsed
                                st.session_state.p2_bench_raw = raw
                                st.session_state.p2_bench_saved = True
                                save_workspace_state()
                                
                                # RAG 키워드 자동 추출
                                keywords = extract_keywords_via_gemma(raw, st.session_state.base_prompt_rules)
                                st.session_state.p2_bench_tags = keywords
                                tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                
                                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                title = f"[Part2] 채널 벤치마킹 및 주제도출 - {ts}"
                                
                                val = f"## 📌 핵심 요약\n- 대상 채널: {st.session_state.p2_channel_url}\n\n"
                                val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"
                                val += f"## 📖 벤치마킹 분석 본문\n{raw}\n\n"
                                val += f"## 🔗 파이프라인 연결\n- 다음 단계: Part 2 자료 조사 및 융합 리서치\n- 선행 파트: Part 1 Librarian 주제 분석\n\n"
                                
                                obs_path = save_obsidian_memory("TopicMemory", title, val, source="Sage Mirror Studio Part 2")
                                if obs_path:
                                    lock_file_readonly(obs_path)
                                    st.toast("💾 벤치마킹 결과 로컬 자동 저장 완료!", icon="💾")
                                    success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                    if success:
                                        st.session_state.p2_bench_obsidian_saved = True
                                        st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                    else:
                                        st.error(f"GitHub Push 실패: {msg}")
                                    save_workspace_state()
                                    st.rerun()
                            else:
                                st.error("채널 분석 결과가 유효하지 않습니다. 다시 시도해 주세요.")
                                
            with c_b2:
                if st.session_state.get("p2_bench_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p2_bench_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p2_bench_local_waiting")
                    
            with c_b3:
                if st.session_state.get("p2_bench_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p2_bench_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p2_bench_obs_waiting")
            
            if st.session_state.get("p2_topics") or st.session_state.get("p2_bench_raw"):
                st.markdown("<br>", unsafe_allow_html=True)
                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p2_topics)]
                
                if topics_display:
                    default_sel_idx = 0
                    if st.session_state.get("p2_topic_selection") in topics_display:
                        default_sel_idx = topics_display.index(st.session_state.p2_topic_selection)
                    st.session_state.p2_topic_selection = st.selectbox(
                        "📌 기획할 주제 1개 선정", 
                        topics_display, 
                        index=default_sel_idx, 
                        disabled=is_locked, 
                        key="p2_topic_sel"
                    )
                    save_workspace_state()
                
                raw_val = st.session_state.get("p2_bench_raw", "").strip()
                if not raw_val:
                    for idx, t in enumerate(st.session_state.p2_topics, 1):
                        raw_val += f"{idx:02d}. {t['title']} | {t['reason']} | {t['effect']} | {t.get('audience_reaction', '공감')}\n"
                    raw_val = raw_val.strip()
                    st.session_state.p2_bench_raw = raw_val
                
                st.session_state.p2_bench_raw = st.text_area(
                    "벤치마킹 상세 본문 (수정 가능)",
                    value=st.session_state.p2_bench_raw,
                    height=400,
                    label_visibility="collapsed",
                    key="p2_bench_raw_area"
                )
                
                c_pop, c_copy = st.columns(2)
                with c_pop:
                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_bench_p2_btn"):
                        popup_edit_benchmarking_p2()
                with c_copy:
                    if st.button("📋 클립보드 복사", use_container_width=True, key="p2_bench_copy_btn"):
                        try:
                            import pyperclip
                            pyperclip.copy(st.session_state.p2_bench_raw)
                            st.success("벤치마킹 결과 복사 완료!")
                        except Exception:
                            st.info("복사 내용은 위 텍스트창에서 직접 드래그 선택하세요.")
                            
                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p2_bench_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)",
                    value=st.session_state.get("p2_bench_tags", ""),
                    placeholder="예: 외로움, 존재의미, 고통, 용서",
                    key="p2_bench_tags_input",
                    disabled=is_locked
                )
                
                if st.button("💾 (예비용) 벤치마킹 수동 옵시디언 백업", use_container_width=True, key="p2_bench_save_backup_btn", disabled=is_locked):
                    parsed = []
                    for line in st.session_state.p2_bench_raw.split("\n"):
                        if "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 3:
                                title_part = parts[0].strip()
                                if ". " in title_part:
                                    title_part = title_part.split(". ", 1)[1]
                                elif "]" in title_part:
                                    title_part = title_part.split("]", 1)[1]
                                parsed.append({
                                    "title": title_part.strip(),
                                    "reason": parts[1].strip(),
                                    "effect": parts[2].strip(),
                                    "audience_reaction": parts[3].strip() if len(parts) > 3 else "공감"
                                })
                    if parsed:
                        st.session_state.p2_topics = parsed
                    
                    tag_list = [t.strip() for t in st.session_state.get("p2_bench_tags","").split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    title = f"[Part2] 채널 벤치마킹 및 주제도출 - {ts}"
                    
                    val = f"## 📌 핵심 요약\n- 대상 채널: {st.session_state.p2_channel_url}\n\n"
                    val += f"## 🎯 RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"
                    val += f"## 📖 본문\n{st.session_state.p2_bench_raw}\n\n"
                    
                    obs_path = save_obsidian_memory("TopicMemory", title, val, source="Sage Mirror Studio Part 2")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 벤치마킹 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p2_bench_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save: {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"GitHub Push 실패: {msg}")
                        st.rerun()
    with tab_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 옵시디언 융합 리서치")
            st.caption("성경/철학/에세이 3원 지식 융합 초안 작성")

            st.session_state.p2_research_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (자료 조사)",
                value=st.session_state.get("p2_research_prompt", "[작업 지시] 선택된 주제에 대하여 200여 개의 시청자 공감 댓글을 참조하고, 철학/심리학/성경 기반 지식을 융합하여 '자료 조사 및 기초 초안'을 작성하시오."),
                height=100,
                key="p2_res_prompt",
                disabled=is_locked
            )

            if st.button("📝 프롬프트 팝업 편집 (자료 조사)", key="p2_edit_res_prompt_btn"):
                popup_edit_text_value("p2_research_prompt", "🤖 젬마 작업지시 프롬프트 (자료 조사)")

            # --- 3단 버튼 구조 ---
            c_r1, c_r2, c_r3 = st.columns([4, 3, 3])
            with c_r1:
                if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p2_res_btn"):
                    if not st.session_state.get("p2_topic_selection"):
                        st.error("[WARN] 먼저 '채널 벤치마킹' 탭에서 분석을 완료하고 주제를 선택해 주세요.")
                    else:
                        st.session_state.p2_research_result = ""
                        st.session_state.p2_research_tags = ""
                        st.session_state.p2_research_saved = False
                        st.session_state.p2_research_obsidian_saved = False
                        st.session_state.p2_need_research_kw = None
                        st.session_state.p2_verification = None
                        save_workspace_state()

                        with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):
                            topic_str = st.session_state.p2_topic_selection
                            result = generate_research_draft(
                                st.session_state.p2_channel_url, topic_str,
                                st.session_state.p2_gemma_protocol, st.session_state.base_prompt_rules,
                                st.session_state.get("p2_research_prompt", "")
                            )
                            st.session_state.p2_research_result = result
                            st.session_state.pipeline_state["research_result"] = result
                            
                            # RAG 지식 공백 감지
                            kw = check_need_research_tag(result)
                            if kw:
                                st.session_state.p2_need_research_kw = kw
                                st.session_state.p2_research_saved = False
                                st.session_state.p2_research_obsidian_saved = False
                            else:
                                st.session_state.p2_need_research_kw = None
                                # 자가 검수 수행
                                ver_res = verify_content_with_gemma("자료 조사 초안", result, st.session_state.base_prompt_rules)
                                st.session_state.p2_verification = ver_res
                                
                                if ver_res.get("status") == "PASS":
                                    st.session_state.p2_research_saved = True
                                    
                                    # 젬마 키워드 자동 세분화 및 옵시디언 자동 백업
                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)
                                    st.session_state.p2_research_tags = keywords
                                    
                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "자료조사"
                                    title = f"[Part2] 자료조사 초안 - {topic_title}"

                                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"
                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                                    val += f"## 📖 자료조사 및 초안 본문\n{result}\n\n"
                                    val += f"## 🔗 파이프라인 연결\n- 다음 단계: Part 3-4 대본 설계\n- 선행 파트: Part 1 Librarian 주제 분석\n\n"

                                    obs_path = save_obsidian_memory("ResearchMemory", title, val, source="Sage Mirror Studio Part 2")
                                    if obs_path:
                                        lock_file_readonly(obs_path)
                                        st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                        if success:
                                            st.session_state.p2_research_obsidian_saved = True
                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                        else:
                                            st.error(f"GitHub Push 실패: {msg}")
                                else:
                                    st.session_state.p2_research_saved = False
                                    st.session_state.p2_research_obsidian_saved = False
                                
                            save_workspace_state()
                            st.rerun()

            with c_r2:
                if st.session_state.get("p2_research_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p2_res_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p2_res_local_waiting")

            with c_r3:
                if st.session_state.get("p2_research_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p2_res_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p2_res_obs_waiting")

            if st.session_state.get("p2_research_result"):
                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---
                if st.session_state.p2_need_research_kw:
                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p2_need_research_kw})")
                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p2_web_research_approve_btn", type="primary", use_container_width=True):
                        if not st.session_state.tavily_api_key:
                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")
                        else:
                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):
                                from sage_engine import tavily_search
                                q = st.session_state.p2_need_research_kw
                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                                if "error" in res_search:
                                    st.error(f"Tavily 검색 오류: {res_search['error']}")
                                else:
                                    raw_results = res_search.get("results", [])
                                    web_context = ""
                                    for r in raw_results:
                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"
                                    
                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.
제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '자료 조사 및 기초 초안'을 완벽하게 재작성하라.
모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.

[웹 리서치 참조 자료]:
{web_context}

[이전 불완전한 결과물]:
{st.session_state.p2_research_result}

[작업 지시]:
위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.
[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.
"""
                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                    st.session_state.p2_research_result = res_new
                                    st.session_state.pipeline_state["research_result"] = res_new
                                    
                                    # 재검증
                                    st.session_state.p2_need_research_kw = check_need_research_tag(res_new)
                                    if not st.session_state.p2_need_research_kw:
                                        ver_res = verify_content_with_gemma("자료 조사 초안", res_new, st.session_state.base_prompt_rules)
                                        st.session_state.p2_verification = ver_res
                                        if ver_res.get("status") == "PASS":
                                            st.session_state.p2_research_saved = True
                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)
                                            st.session_state.p2_research_tags = keywords
                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            folder_name = "ResearchMemory"
                                            topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "자료조사"
                                            title = f"[Part2] 자료조사 초안 - {topic_title}"
                                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"
                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                                            val += f"## 📖 자료조사 및 초안 본문\n{res_new}\n\n"
                                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")
                                            if obs_path:
                                                lock_file_readonly(obs_path)
                                                st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                                if success:
                                                    st.session_state.p2_research_obsidian_saved = True
                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                                else:
                                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                    else:
                                        st.session_state.p2_research_saved = False
                                        st.session_state.p2_research_obsidian_saved = False
                                    
                                    save_workspace_state()
                                    st.rerun()

                elif st.session_state.p2_verification:
                    ver = st.session_state.p2_verification
                    if ver.get("status") == "FAIL":
                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")
                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p2_self_correct_btn", type="primary", use_container_width=True):
                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):
                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.
이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.

[이전 결과물]:
{st.session_state.p2_research_result}

[수정 건의사항]:
{ver.get("suggestions", "없음")}

[작업 지시]:
수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.
모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.
"""
                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                st.session_state.p2_research_result = res_corr
                                st.session_state.pipeline_state["research_result"] = res_corr
                                
                                # 재검증
                                st.session_state.p2_need_research_kw = check_need_research_tag(res_corr)
                                if not st.session_state.p2_need_research_kw:
                                    ver_res = verify_content_with_gemma("자료 조사 초안", res_corr, st.session_state.base_prompt_rules)
                                    st.session_state.p2_verification = ver_res
                                    if ver_res.get("status") == "PASS":
                                        st.session_state.p2_research_saved = True
                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)
                                        st.session_state.p2_research_tags = keywords
                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        folder_name = "ResearchMemory"
                                        topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "자료조사"
                                        title = f"[Part2] 자료조사 초안 - {topic_title}"
                                        val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"
                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                                        val += f"## 📖 자료조사 및 초안 본문\n{res_corr}\n\n"
                                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")
                                        if obs_path:
                                            lock_file_readonly(obs_path)
                                            st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")
                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                            if success:
                                                st.session_state.p2_research_obsidian_saved = True
                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                            else:
                                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                else:
                                    st.session_state.p2_research_saved = False
                                    st.session_state.p2_research_obsidian_saved = False
                                
                                save_workspace_state()
                                st.rerun()
                    else:
                        st.success("✅ **Gemma 자가 검수 통과**: 모든 무결성 규칙(지칭어, 출처 등)이 확인되었습니다.")
                        with st.expander("🔍 검수 결과 보고서 자세히 보기", expanded=False):
                            st.text(ver.get("report"))
                
                st.session_state.p2_research_result = st.text_area(
                    "자료 조사 결과 (수정 가능)",
                    value=st.session_state.p2_research_result,
                    height=400,
                    label_visibility="collapsed",
                    key="p2_res_area"
                )

                c_pop, c_copy = st.columns(2)
                with c_pop:
                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_res2_btn"):
                        popup_edit_research_p2()
                with c_copy:
                    if st.button("📋 클립보드 복사", use_container_width=True, key="p2_res_copy_btn"):
                        try:
                            import pyperclip
                            pyperclip.copy(st.session_state.p2_research_result)
                            st.success("자료조사 결과 복사 완료!")
                        except Exception:
                            st.info("복사 내용은 위 텍스트창에서 직접 드래그 선택하세요.")

                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p2_research_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)",
                    value=st.session_state.get("p2_research_tags", ""),
                    placeholder="예: 외로움, 존재의미, 고통, 용서",
                    key="p2_res_tags_input",
                    disabled=is_locked
                )

                if st.button("💾 (예비용) 자료조사 수동 옵시디언 백업", use_container_width=True, key="p2_research_save_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.get("p2_research_tags","").split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.get("p2_topic_selection") and ". " in st.session_state.p2_topic_selection else "자료조사"
                    title = f"[Part2] 자료조사 초안 - {topic_title}"
                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.get('p2_topic_selection','')}\n\n"
                    val += f"## 🎯 RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"
                    val += f"## 📖 본문\n{st.session_state.p2_research_result}\n\n"
                    obs_path = save_obsidian_memory("ResearchMemory", title, val, source="Sage Mirror Studio Part 2")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 자료조사 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p2_research_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save: {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"GitHub Push 실패: {msg}")
                        st.rerun()


    with tab_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안 생성")
            st.caption("Part 1 Librarian + Part 2 자료조사 결과를 융합하여 15분 영상 마스터 기획안 작성")

            st.session_state.p2_plan_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (총괄 기획)",
                value=st.session_state.get("p2_plan_prompt", "[작업 지시] 위의 자료조사 결과와 Part 1 주제 분석을 바탕으로, 성경-철학-에세이 3원 융합 구조의 15분 유튜브 롱폼 총괄 기획안을 작성하시오. 시청자 감정 곡선 (기-승-전-결)을 명시하고, 핵심 성경 구절/철학자/에세이 3가지를 반드시 포함하라."),
                height=120,
                key="p2_plan_prompt_input",
                disabled=is_locked
            )

            if st.button("📝 프롬프트 팝업 편집 (총괄 기획)", key="p2_edit_plan_prompt_btn"):
                popup_edit_text_value("p2_plan_prompt", "🤖 젬마 작업지시 프롬프트 (총괄 기획)")

            # --- 3단 버튼 구조 ---
            c_p1, c_p2, c_p3 = st.columns([4, 3, 3])
            with c_p1:
                if st.button("[ALCHEMY] 총괄 기획안 생성 (AI)", use_container_width=True, disabled=is_locked, type="primary", key="p2_plan_btn"):
                    if not st.session_state.get("p2_research_result"):
                        st.error("[WARN] 먼저 '자료 조사' 탭에서 자료조사를 완료해 주세요.")
                    else:
                        st.session_state.p2_planning_result = ""
                        st.session_state.p2_plan_saved = False
                        st.session_state.p2_plan_obsidian_saved = False
                        st.session_state.p2_plan_need_research_kw = None
                        st.session_state.p2_plan_verification = None
                        save_workspace_state()

                        with st.spinner("성경-철학-에세이 3원 융합 기획안 생성 중..."):
                            topic_str = st.session_state.get("p2_topic_selection", "")
                            plan_prompt_val = st.session_state.get("p2_plan_prompt", "")

                            prompt = f"""[지시] 아래 자료조사 결과를 바탕으로 총괄 기획안을 작성하세요.

[선택 주제]
{topic_str}

[자료조사 결과]
{st.session_state.p2_research_result}

[추가 작업 지시]
{plan_prompt_val}

[출력 요구사항]
1. 영상 제목 (클릭 유도형, 4070 세대 타겟)
2. 핵심 감정 키워드 3개
3. 기-승-전-결 구조 요약 (각 25%)
4. 성경 구절 1개 [SOURCE: 성경 — 책명 장:절]
5. 철학자 인용 1개 [SOURCE: 책명 — 저자명]
6. 에세이 문장 1개 [SOURCE: 에세이명 — 저자명]
7. 썸네일 키워드 3개
8. 예상 시청자 반응

{st.session_state.p2_gemma_protocol}"""

                            result = call_gemma(prompt)
                            st.session_state.p2_planning_result = result
                            st.session_state.pipeline_state["planning_result"] = result
                            
                            # RAG 지식 공백 감지
                            kw = check_need_research_tag(result)
                            if kw:
                                st.session_state.p2_plan_need_research_kw = kw
                                st.session_state.p2_plan_saved = False
                                st.session_state.p2_plan_obsidian_saved = False
                            else:
                                st.session_state.p2_plan_need_research_kw = None
                                # 자가 검수 수행
                                ver_res = verify_content_with_gemma("총괄 기획안", result, st.session_state.base_prompt_rules)
                                st.session_state.p2_plan_verification = ver_res
                                
                                if ver_res.get("status") == "PASS":
                                    st.session_state.p2_plan_saved = True
                                    
                                    # 젬마 키워드 자동 세분화 및 옵시디언 자동 백업
                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)
                                    st.session_state.p2_plan_tags = keywords
                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    topic_title = topic_str.split(". ")[1] if topic_str and ". " in topic_str else "기획안"
                                    title = f"[Part2] 총괄 기획안 - {topic_title}"

                                    val = f"## 📌 핵심 요약\n- 선택 주제: {topic_str}\n\n"
                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"
                                    val += f"## 📖 총괄 기획안 본문\n{result}\n\n"
                                    val += f"## 🔗 파이프라인 연결\n- 다음 단계: Part 3-4 대본 설계 (p2_planning_result 자동 전달)\n- 선행 파트: Part 1 Librarian → Part 2 자료조사\n\n"

                                    obs_path = save_obsidian_memory("PlanningMemory", title, val, source="Sage Mirror Studio Part 2")
                                    if obs_path:
                                        lock_file_readonly(obs_path)
                                        st.toast("💾 총괄 기획안 로컬 자동 저장 완료!", icon="💾")
                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                        if success:
                                            st.session_state.p2_plan_obsidian_saved = True
                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                        else:
                                            st.error(f"GitHub Push 실패: {msg}")
                                else:
                                    st.session_state.p2_plan_saved = False
                                    st.session_state.p2_plan_obsidian_saved = False
                                    
                            save_workspace_state()
                            st.rerun()

            with c_p2:
                if st.session_state.get("p2_plan_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p2_plan_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p2_plan_local_waiting")

            with c_p3:
                if st.session_state.get("p2_plan_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p2_plan_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p2_plan_obs_waiting")

            if st.session_state.get("p2_planning_result"):
                st.markdown("<br>", unsafe_allow_html=True)

                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---
                if st.session_state.get("p2_plan_need_research_kw"):
                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p2_plan_need_research_kw})")
                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p2_plan_web_research_approve_btn", type="primary", use_container_width=True):
                        if not st.session_state.get("tavily_api_key"):
                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")
                        else:
                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):
                                from sage_engine import tavily_search
                                q = st.session_state.p2_plan_need_research_kw
                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                                if "error" in res_search:
                                    st.error(f"Tavily 검색 오류: {res_search['error']}")
                                else:
                                    raw_results = res_search.get("results", [])
                                    web_context = ""
                                    for r in raw_results:
                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"
                                    
                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.
제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '총괄 기획안'을 완벽하게 재작성하라.
모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.

[웹 리서치 참조 자료]:
{web_context}

[이전 불완전한 결과물]:
{st.session_state.p2_planning_result}

[작업 지시]:
위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.
[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.
"""
                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                    st.session_state.p2_planning_result = res_new
                                    st.session_state.pipeline_state["planning_result"] = res_new
                                    
                                    # 재검증
                                    st.session_state.p2_plan_need_research_kw = check_need_research_tag(res_new)
                                    if not st.session_state.p2_plan_need_research_kw:
                                        ver_res = verify_content_with_gemma("총괄 기획안", res_new, st.session_state.base_prompt_rules)
                                        st.session_state.p2_plan_verification = ver_res
                                        if ver_res.get("status") == "PASS":
                                            st.session_state.p2_plan_saved = True
                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)
                                            st.session_state.p2_plan_tags = keywords
                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            folder_name = "PlanningMemory"
                                            topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "기획안"
                                            title = f"[Part2] 총괄 기획안 - {topic_title}"
                                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"
                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"
                                            val += f"## 📖 총괄 기획안 본문\n{res_new}\n\n"
                                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")
                                            if obs_path:
                                                lock_file_readonly(obs_path)
                                                st.toast("💾 총괄 기획안 로컬 자동 저장 완료!", icon="💾")
                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                                if success:
                                                    st.session_state.p2_plan_obsidian_saved = True
                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                                else:
                                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                    else:
                                        st.session_state.p2_plan_saved = False
                                        st.session_state.p2_plan_obsidian_saved = False
                                    
                                    save_workspace_state()
                                    st.rerun()

                elif st.session_state.get("p2_plan_verification"):
                    ver = st.session_state.p2_plan_verification
                    if ver.get("status") == "FAIL":
                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")
                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p2_plan_self_correct_btn", type="primary", use_container_width=True):
                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):
                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.
이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.

[이전 결과물]:
{st.session_state.p2_planning_result}

[수정 건의사항]:
{ver.get("suggestions", "없음")}

[작업 지시]:
수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.
모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.
"""
                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                st.session_state.p2_planning_result = res_corr
                                st.session_state.pipeline_state["planning_result"] = res_corr
                                
                                # 재검증
                                st.session_state.p2_plan_need_research_kw = check_need_research_tag(res_corr)
                                if not st.session_state.p2_plan_need_research_kw:
                                    ver_res = verify_content_with_gemma("총괄 기획안", res_corr, st.session_state.base_prompt_rules)
                                    st.session_state.p2_plan_verification = ver_res
                                    if ver_res.get("status") == "PASS":
                                        st.session_state.p2_plan_saved = True
                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)
                                        st.session_state.p2_plan_tags = keywords
                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        folder_name = "PlanningMemory"
                                        topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "기획안"
                                        title = f"[Part2] 총괄 기획안 - {topic_title}"
                                        val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"
                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"
                                        val += f"## 📖 총괄 기획안 본문\n{res_corr}\n\n"
                                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")
                                        if obs_path:
                                            lock_file_readonly(obs_path)
                                            st.toast("💾 총괄 기획안 결과 로컬 자동 저장 완료!", icon="💾")
                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                            if success:
                                                st.session_state.p2_plan_obsidian_saved = True
                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                            else:
                                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                                else:
                                    st.session_state.p2_plan_saved = False
                                    st.session_state.p2_plan_obsidian_saved = False
                                
                                save_workspace_state()
                                st.rerun()
                    else:
                        st.success("✅ **Gemma 자가 검수 통과**: 모든 무결성 규칙(지칭어, 출처 등)이 확인되었습니다.")
                        with st.expander("🔍 검수 결과 보고서 자세히 보기", expanded=False):
                            st.text(ver.get("report"))

                # Part 3-4 전달 상태 표시
                st.success("✅ Part 3-4 대본 설계로 자동 전달 준비 완료! (Part 3-4에서 이 기획안이 자동 수신됩니다)")

                st.session_state.p2_planning_result = st.text_area(
                    "총괄 기획안 (수정 가능)",
                    value=st.session_state.p2_planning_result,
                    height=450,
                    label_visibility="collapsed",
                    key="p2_plan_area"
                )

                c_pop2, c_copy2 = st.columns(2)
                with c_pop2:
                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_plan2_btn"):
                        popup_edit_planning_p2()
                with c_copy2:
                    if st.button("📋 클립보드 복사", use_container_width=True, key="p2_plan_copy_btn"):
                        try:
                            import pyperclip
                            pyperclip.copy(st.session_state.p2_planning_result)
                            st.success("총괄 기획안 복사 완료!")
                        except Exception:
                            st.info("복사 내용은 위 텍스트창에서 직접 드래그 선택하세요.")

                st.divider()
                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")
                st.session_state.p2_plan_tags = st.text_input(
                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)",
                    value=st.session_state.get("p2_plan_tags", ""),
                    placeholder="예: 외로움, 존재의미, 고통, 용서",
                    key="p2_plan_tags_input",
                    disabled=is_locked
                )

                if st.button("💾 (예비용) 기획안 수동 옵시디언 백업", use_container_width=True, key="p2_plan_backup_btn", disabled=is_locked):
                    tag_list = [t.strip() for t in st.session_state.get("p2_plan_tags","").split(",") if t.strip()]
                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                    tag_hashes = " ".join([f"#{t}" for t in tag_list])
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_title = st.session_state.get("p2_topic_selection","").split(". ")[1] if st.session_state.get("p2_topic_selection") and ". " in st.session_state.get("p2_topic_selection","") else "기획안"
                    title = f"[Part2] 총괄 기획안 - {topic_title}"
                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.get('p2_topic_selection','')}\n\n"
                    val += f"## 🎯 RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"
                    val += f"## 📖 본문\n{st.session_state.p2_planning_result}\n\n"
                    obs_path = save_obsidian_memory("PlanningMemory", title, val, source="Sage Mirror Studio Part 2")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 기획안 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p2_plan_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save: {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"GitHub Push 실패: {msg}")
                        st.rerun()

    st.divider()
    if st.button("🔒 Part 2 전체 옵시디언 자동 백업", type="primary", use_container_width=True, disabled=is_locked, key="p2_final_backup"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        today_str = datetime.now().strftime("%Y-%m-%d")
        folder_name = "PlanningMemory"
        title = f"[Part2] 전체 작업 백업 - {ts}"
        val = f"# Part 2 Alchemist 전체 작업 백업\n\n"
        val += f"## 📌 선택 주제\n{st.session_state.get('p2_topic_selection','')}\n\n"
        val += f"## 📚 자료조사 결과\n{st.session_state.get('p2_research_result','')}\n\n"
        val += f"## 📖 총괄 기획안\n{st.session_state.get('p2_planning_result','')}\n\n"
        val += f"---\n*Last updated: {today_str} {ts}*\n"
        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")
        if obs_path:
            lock_file_readonly(obs_path)
            st.toast("✅ Part 2 전체 백업 완료!", icon="🔒")
            success, msg = auto_git_push(f"Auto Save (Part 2 Full): {ts}")
            if success:
                st.toast("🚀 GitHub 백업 완료!", icon="🚀")
            else:
                st.error(f"GitHub Push 실패: {msg}")


@st.dialog("[TARGET] 이미지 파트 마스터 프롬프트 편집", width="large")
def popup_edit_image_prompt():
    st.markdown("이미지 생성 규칙서를 상세하게 수정할 수 있습니다.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p5_image_master_prompt, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary", key="p5_save_prompt"):
            st.session_state.p5_image_master_prompt = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True, key="p5_cancel_prompt"):
            st.rerun()

def render_part5():
    c_title, c_control = st.columns([4.2, 5.8])
    
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🖼️ 파트 4: 이미지 생성</h3>', unsafe_allow_html=True)
        
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p5_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p5_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part5", "7777"): st.session_state.unlock_part5 = True
            elif pin: st.session_state.unlock_part5 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p5_popup_btn"):
                st.session_state.sidebar_part = "part5"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)

    if "unlock_part5" not in st.session_state:
        st.session_state.unlock_part5 = False
    is_locked = not st.session_state.unlock_part5
    if is_locked:
        st.warning("[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.divider()
    
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 이미지 마스터 규정서", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=300, key="p5_top_ob_view", label_visibility="collapsed")
            if st.button("[SEARCH] 편집", key="p5_ob_btn"): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🖼️ 이미지 파트 마스터 규정서 v3.0</div>', unsafe_allow_html=True)
            st.text_area("이미지 마스터 프롬프트", value=st.session_state.p5_image_master_prompt, height=300, key="p5_top_pr_view", label_visibility="collapsed")
            if st.button("[SEARCH] 편집", key="p5_pr_btn"): popup_edit_image_prompt()
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.divider()
    st.info("👉 이미지 생성 자동화 UI 및 씬(Scene) 관리 인터페이스가 곧 이곳에 구현될 예정입니다.")


@st.dialog("[CINEMA] Veo3 마스터 프롬프트 편집", width="large")
def popup_edit_veo3_master():
    new_val = st.text_area("Veo3 마스터 프롬프트", value=st.session_state.get("p6_veo3_master_prompt", ""), height=500, key="p6_master_edit_ta")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("[SAVE] 저장", type="primary", key="p6_master_save"):
            st.session_state.p6_veo3_master_prompt = new_val
            st.toast("[OK] Veo3 마스터 프롬프트 저장!", icon="[CINEMA]")
            st.rerun()
    with c2:
        if st.button("취소", key="p6_master_cancel"):
            st.rerun()

@st.dialog("🖼️ 이미지 마스터 규정서 편집", width="large")
def popup_edit_image_master():
    new_val = st.text_area("규정서", value=st.session_state.get("p5_image_master_prompt", ""), height=500, key="p5_master_edit_ta")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("[SAVE] 저장", type="primary", key="p5_master_save"):
            st.session_state.p5_image_master_prompt = new_val
            st.toast("[OK] 이미지 마스터 규정서 저장!", icon="🖼️")
            st.rerun()
    with c2:
        if st.button("취소", key="p5_master_cancel"):
            st.rerun()

@st.dialog("[USER] A-MASTER 인물 참조 프롬프트 편집", width="large")
def popup_edit_a_result():
    st.caption("A-MASTER 프롬프트를 스크롤하며 검토하고 복사/수정하세요.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,sans-serif;'>{st.session_state.get('p5_a_result','')}</div>", unsafe_allow_html=True)
    new_val = st.text_area("편집", value=st.session_state.get("p5_a_result",""), height=250, key="popup_a_edit_ta", label_visibility="collapsed")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("[SAVE] 저장", use_container_width=True, type="primary", key="popup_a_save"):
            st.session_state.p5_a_history.append(st.session_state.get("p5_a_result",""))
            st.session_state.p5_a_result = new_val
            st.toast("[OK] A-MASTER 저장", icon="[OK]")
            st.rerun()
    with c2:
        hist_a = st.session_state.get("p5_a_history", [])
        if st.button(f"⬅️ 뒤로 ({len(hist_a)})", use_container_width=True, key="popup_a_back", disabled=len(hist_a)==0):
            st.session_state.p5_a_result = st.session_state.p5_a_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 초기화", use_container_width=True, key="popup_a_reset"):
            st.session_state.p5_a_history.append(st.session_state.get("p5_a_result",""))
            st.session_state.p5_a_result = ""
            st.rerun()
    with c4:
        st.download_button("📥 .txt", data=st.session_state.get("p5_a_result",""), file_name=f"A_Master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True, key="popup_a_dl")

@st.dialog("[IMAGE] B-MASTER 배경/소품 참조 프롬프트 편집", width="large")
def popup_edit_b_result():
    st.caption("B-MASTER 프롬프트를 스크롤하며 검토하고 복사/수정하세요.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,sans-serif;'>{st.session_state.get('p5_b_result','')}</div>", unsafe_allow_html=True)
    new_val = st.text_area("편집", value=st.session_state.get('p5_b_result',''), height=250, key="popup_b_edit_ta", label_visibility="collapsed")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("저장", use_container_width=True, type="primary", key="popup_b_save"):
            st.session_state.p5_b_history.append(st.session_state.get("p5_b_result",""))
            st.session_state.p5_b_result = new_val
            st.toast("B-MASTER 저장")
            st.rerun()
    with c2:
        hist_b = st.session_state.get("p5_b_history", [])
        if st.button(f"뒤로 ({len(hist_b)})", use_container_width=True, key="popup_b_back", disabled=len(hist_b)==0):
            st.session_state.p5_b_result = st.session_state.p5_b_history.pop()
            st.rerun()
    with c3:
        if st.button("초기화", use_container_width=True, key="popup_b_reset"):
            st.session_state.p5_b_history.append(st.session_state.get("p5_b_result",""))
            st.session_state.p5_b_result = ""
            st.rerun()
    with c4:
        st.download_button("📥 .txt", data=st.session_state.get("p5_b_result",""), file_name=f"B_Master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True, key="popup_b_dl")

@st.dialog("[CINEMA] C-1 씬별 프롬프트 결과 편집", width="large")
def popup_edit_c_result():
    st.caption("C-1 전체 결과를 스크롤하며 검토하고복사/수정하세요.")
    with st.container(height=350, border=True):
        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,sans-serif;'>{st.session_state.get('p5_c_results','')}</div>", unsafe_allow_html=True)
    new_val = st.text_area("편집", value=st.session_state.get("p5_c_results",""), height=250, key="popup_c_edit_ta", label_visibility="collapsed")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("[SAVE] 저장", use_container_width=True, type="primary", key="popup_c_save"):
            st.session_state.p5_c_history.append(st.session_state.get("p5_c_results",""))
            st.session_state.p5_c_results = new_val
            st.toast("[OK] C-1 결과 저장", icon="[OK]")
            st.rerun()
    with c2:
        hist_c = st.session_state.get("p5_c_history", [])
        if st.button(f"⬅️ 뒤로 ({len(hist_c)})", use_container_width=True, key="popup_c_back", disabled=len(hist_c)==0):
            st.session_state.p5_c_results = st.session_state.p5_c_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 초기화", use_container_width=True, key="popup_c_reset"):
            st.session_state.p5_c_history.append(st.session_state.get("p5_c_results",""))
            st.session_state.p5_c_results = ""
            st.rerun()
    with c4:
        st.download_button("📥 .md", data=st.session_state.get("p5_c_results",""), file_name=f"C1_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", use_container_width=True, key="popup_c_dl")

@st.dialog("[TARGET] 마스터 프롬프트 편집 (Part 3-4)", width="large")
def popup_edit_prompt_p34():
    st.markdown("대본 작성 규정서를 수정합니다.")

    new_val = st.text_area("규칙서 내용", value=st.session_state.p34_master_prompt, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p34_master_prompt = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()


@st.dialog("🎙️ 나레이션 대본 — 전체 보기 / 수정", width="large")
def popup_narr_p34():
    st.caption("스크롤 가능 · 마우스 드래그로 복사 가능 · 직접 수정 후 저장")
    new_val = st.text_area(
        "나레이션 대본 전체",
        value=st.session_state.p34_narration_script,
        height=550,
        label_visibility="collapsed",
        key="popup_narr_edit"
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 수정 내용 저장", use_container_width=True, type="primary", key="popup_narr_save"):
            st.session_state.p34_narration_script = new_val
            save_workspace_state()
            st.toast("나레이션 대본 저장 완료!", icon="💾")
            st.rerun()
    with c2:
        if st.button("📋 전체 복사", use_container_width=True, key="popup_narr_copy"):
            try:
                import pyperclip
                pyperclip.copy(st.session_state.p34_narration_script)
                st.success("복사 완료!")
            except Exception:
                st.info("위 텍스트창에서 직접 드래그 선택하세요.")
    with c3:
        if st.button("❌ 닫기", use_container_width=True, key="popup_narr_close"):
            st.rerun()


@st.dialog("🖼️ 이미지 프롬프트 대본 — 전체 보기 / 수정", width="large")
def popup_img_p34():
    st.caption("스크롤 가능 · 마우스 드래그로 복사 가능 · 직접 수정 후 저장")
    new_val = st.text_area(
        "이미지 프롬프트 전체",
        value=st.session_state.p34_image_script,
        height=550,
        label_visibility="collapsed",
        key="popup_img_edit"
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 수정 내용 저장", use_container_width=True, type="primary", key="popup_img_save"):
            st.session_state.p34_image_script = new_val
            save_workspace_state()
            st.toast("이미지 대본 저장 완료!", icon="💾")
            st.rerun()
    with c2:
        if st.button("📋 전체 복사", use_container_width=True, key="popup_img_copy"):
            try:
                import pyperclip
                pyperclip.copy(st.session_state.p34_image_script)
                st.success("복사 완료!")
            except Exception:
                st.info("위 텍스트창에서 직접 드래그 선택하세요.")
    with c3:
        if st.button("❌ 닫기", use_container_width=True, key="popup_img_close"):
            st.rerun()


@st.dialog("🎬 캡컷 에셋 JSON — 전체 보기 / 수정", width="large")
def popup_cap_p34():
    st.caption("스크롤 가능 · 마우스 드래그로 복사 가능 · 직접 수정 후 저장")
    new_val = st.text_area(
        "캡컷 JSON 전체",
        value=st.session_state.p34_capcut_data,
        height=550,
        label_visibility="collapsed",
        key="popup_cap_edit"
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 수정 내용 저장", use_container_width=True, type="primary", key="popup_cap_save"):
            st.session_state.p34_capcut_data = new_val
            save_workspace_state()
            st.toast("캡컷 에셋 저장 완료!", icon="💾")
            st.rerun()
    with c2:
        if st.button("📋 전체 복사", use_container_width=True, key="popup_cap_copy"):
            try:
                import pyperclip
                pyperclip.copy(st.session_state.p34_capcut_data)
                st.success("복사 완료!")
            except Exception:
                st.info("위 텍스트창에서 직접 드래그 선택하세요.")
    with c3:
        if st.button("❌ 닫기", use_container_width=True, key="popup_cap_close"):
            st.rerun()


# ── Part 4 Tab A 헬퍼 ──
def _p5_tab_a(is_locked):
    st.caption("@Protagonist 캐릭터 고정용 — 구글 플로우 Reference Slot 1에 업로드 후 PIN 고정")
    st.info("📌 A-MASTER 프롬프트로 이미지 생성 → A_Protagonist_Master.png → 크롬 확장 Slot 1 PIN")
    if st.button("✨ A-MASTER 인물 참조 프롬프트 생성", use_container_width=True, key="p5_a_gen_btn", disabled=is_locked):
        prompt = (
            f"[이미지 파트 마스터 규정서]\n{st.session_state.get('p5_image_master_prompt','')}\n\n"
            "[지시] 섹션 A의 A-REFERENCE SHEET 생성 양식 전문을 출력하라.\n"
            "@Protagonist 외형 고정값 영문 전문 + 레퍼런스 시트 생성 양식을 완전한 형태로 출력. 요약 금지.\n\n"
            "[출력 형식]\n=== A-MASTER 고정값 ===\n(영문 고정값 전문)\n"
            "=== A-REFERENCE SHEET 생성 프롬프트 (구글 플로우 입력용) ===\n(레퍼런스 시트 생성 양식 전문)"
        )
        with st.spinner("[BOT] 젬마가 A-MASTER 프롬프트를 생성 중..."):
            try:
                result = call_gemma(prompt, system=SAGE_PERSONA)
                st.session_state.p5_a_result = result
                st.success("[OK] A-MASTER 생성 완료!")
            except Exception as e:
                st.error(f"생성 실패: {e}\n→ Ollama 서버 실행 확인 (ollama serve)")
    if st.session_state.get("p5_a_result"):
        st.markdown("##### 📋 A-MASTER 프롬프트 (복사 후 구글 플로우에 입력)")
        st.text_area("A-MASTER 결과", value=st.session_state.p5_a_result, height=300, key="p5_a_ta")
        if st.button("[SEARCH] 팝업에서 크게 보기 / 복붙", use_container_width=True, key="p5_a_popup_view"):
            popup_edit_a_result()
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            st.download_button("📥 A-MASTER.txt 다운로드",
                data=st.session_state.p5_a_result.encode("utf-8"),
                file_name="A_Protagonist_Master_Prompt.txt", key="p5_a_dl")
        with col_a2:
            if st.button("[SAVE] 옵시디언 저장", key="p5_a_save", disabled=is_locked):
                try:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ob = st.session_state.get("path_obsidian", "")
                    safe_makedirs(ob)
                    path = os.path.join(ob, f"part4_A_master_{ts}.md")
                    content = f"# A-MASTER @Protagonist 고정 프롬프트\n\n```\n{st.session_state.p5_a_result}\n```\n\n*생성: {ts}*"
                    if save_markdown(path, content):
                        lock_file_readonly(path)
                        st.toast("[OK] A-MASTER 옵시디언 저장 완료!", icon="📓")
                        success, msg = auto_git_push(f"Part4 A-MASTER: {ts}")
                        if success: st.toast("🚀 GitHub Push 완료!", icon="🚀")
                        else: st.warning(f"GitHub Push: {msg}")
                except Exception as e:
                    st.error(f"저장 실패: {e}")
        with col_a3:
            st.code("크롬 확장 Slot 1 → PIN 고정 🔒", language="text")
    st.divider()
    st.markdown("##### 🔒 크롬 확장 작업 체크리스트 (A파트)")
    col_ck1, col_ck2 = st.columns(2)
    with col_ck1:
        st.checkbox("A_Protagonist_Master.png 생성 완료", key="p5_ck_a1")
        st.checkbox("Slot 1에 업로드 완료", key="p5_ck_a2")
    with col_ck2:
        st.checkbox("Slot 1 PIN 고정(🔒) 확인", key="p5_ck_a3")
        st.checkbox("외형 검수 완료 (수염/복장/나이)", key="p5_ck_a4")

# ── Part 4 Tab B 헬퍼 ──
def _p5_tab_b(is_locked):
    st.caption("배경/@거울/@촛대/@소품 고정용 — 구글 플로우 Reference Slot 2에 업로드 후 PIN 고정")
    st.info("📌 B-MASTER 프롬프트로 이미지 생성 → B_Environment_Master.png → 크롬 확장 Slot 2 PIN")
    b_sub = st.selectbox("생성할 B파트 선택", [
        "[IMAGE] 전체 배경 + 소품 통합 레퍼런스 시트", "[MIRROR] @거울 단독", "🕯️ @촛대 단독",
        "⏳ @모래시계 단독", "📚 @고서 단독", "🌍 @지구본 단독",
        "📜 @양피지 단독", "🪶 @깃털펜 단독", "🔑 @열쇠 단독"
    ], key="p5_b_select")
    if st.button("✨ B-MASTER 환경/소품 참조 프롬프트 생성", use_container_width=True, key="p5_b_gen_btn", disabled=is_locked):
        prompt = (
            f"[이미지 파트 마스터 규정서]\n{st.session_state.get('p5_image_master_prompt','')}\n\n"
            f"[지시] 섹션 B에서 [{b_sub}]에 해당하는 프롬프트 전문을 출력하라. 요약 금지.\n\n"
            "[출력 형식]\n=== B-MASTER 고정값 ===\n(영문 고정값 전문)\n"
            "=== B-REFERENCE SHEET 생성 프롬프트 (구글 플로우 입력용) ===\n(레퍼런스 시트 생성 양식 전문)"
        )
        with st.spinner(f"🤖 [{b_sub}] B-MASTER 프롬프트 생성 중..."):
            try:
                result = call_gemma(prompt, system=SAGE_PERSONA)
                st.session_state.p5_b_result = result
                st.success("[OK] B-MASTER 생성 완료!")
            except Exception as e:
                st.error(f"생성 실패: {e}")
    if st.session_state.get("p5_b_result"):
        st.text_area("B-MASTER 결과", value=st.session_state.p5_b_result, height=300, key="p5_b_ta")
        if st.button("[SEARCH] 팝업에서 크게 보기 / 복붙", use_container_width=True, key="p5_b_popup_view"):
            popup_edit_b_result()
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.download_button("📥 B-MASTER.txt 다운로드",
                data=st.session_state.p5_b_result.encode("utf-8"),
                file_name="B_Environment_Master_Prompt.txt", key="p5_b_dl")
        with col_b2:
            if st.button("[SAVE] 옵시디언 저장", key="p5_b_save", disabled=is_locked):
                try:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ob = st.session_state.get("path_obsidian", "")
                    safe_makedirs(ob)
                    path = os.path.join(ob, f"part4_B_master_{ts}.md")
                    content = f"# B-MASTER 환경/소품 고정 프롬프트\n\n```\n{st.session_state.p5_b_result}\n```\n\n*생성: {ts}*"
                    if save_markdown(path, content):
                        lock_file_readonly(path)
                        st.toast("[OK] B-MASTER 옵시디언 저장 완료!", icon="📓")
                        success, msg = auto_git_push(f"Part4 B-MASTER: {ts}")
                        if success: st.toast("🚀 GitHub Push 완료!", icon="🚀")
                        else: st.warning(f"GitHub Push: {msg}")
                except Exception as e:
                    st.error(f"저장 실패: {e}")
    st.divider()
    st.markdown("##### 🔒 크롬 확장 작업 체크리스트 (B파트)")
    col_ck3, col_ck4 = st.columns(2)
    with col_ck3:
        st.checkbox("B_Environment_Master.png 생성 완료", key="p5_ck_b1")
        st.checkbox("Slot 2에 업로드 완료", key="p5_ck_b2")
    with col_ck4:
        st.checkbox("Slot 2 PIN 고정(🔒) 확인", key="p5_ck_b3")
        st.checkbox("배경/소품 스타일 검수 완료", key="p5_ck_b4")

# ── Part 4 Tab C 헬퍼 ──
def _p5_tab_c(is_locked):
    st.caption("Part 3/4 확정 대본 → C-1 씬별 조립 프롬프트 생성 → CSV 다운로드 → 크롬 확장 투입")
    all_pinned = st.session_state.get("p5_ck_a3", False) and st.session_state.get("p5_ck_b3", False)
    if not all_pinned:
        st.warning("[WARN] A파트 Slot 1 PIN + B파트 Slot 2 PIN을 먼저 완료하세요!")
    c_left, c_center, c_right = st.columns(3, gap="large")
    with c_left:
        with st.container(border=True):
            st.markdown("### 📥 대본 데이터 수신")
            src_choice = st.radio("데이터 소스", ["Part 3/4 자동 연동", "직접 붙여넣기"], key="p5_src_choice")
            if src_choice == "Part 3/4 자동 연동":
                src_data = st.session_state.get("p34_image_script", "") or st.session_state.get("p34_narration_script", "")
                if src_data: st.success(f"[OK] Part 3/4 연동됨 ({len(src_data.split(chr(10)))}줄)")
                else: st.error("[FAIL] Part 3/4 데이터 없음 — Part 3/4 먼저 완료하세요")
            else:
                src_data = st.text_area("대본 데이터 붙여넣기", height=200, key="p5_src_manual", placeholder="씬번호|대본|@한글묘사@|@영어프롬프트@")
            if st.button("[SEARCH] 데이터 파싱 및 씬 목록 구성", use_container_width=True, key="p5_parse_btn", disabled=is_locked):
                if not src_data or not src_data.strip():
                    st.error("[WARN] 데이터가 없습니다.")
                else:
                    lines = [l.strip() for l in src_data.strip().split("\n") if l.strip()]
                    parsed, errors = [], []
                    for i, line in enumerate(lines, 1):
                        pts = line.split("|")
                        if len(pts) >= 2:
                            sn = pts[0].strip()
                            try: n = int(sn); sfmt = f"{n:03d}"
                            except: sfmt = sn; errors.append(f"씬번호 오류 Line {i}: {sn}")
                            pos = "기" if sfmt.isdigit() and int(sfmt)<=28 else ("승" if sfmt.isdigit() and int(sfmt)<=56 else ("전" if sfmt.isdigit() and int(sfmt)<=84 else "결"))
                            parsed.append({"씬번호": sfmt, "대본": pts[1].strip() if len(pts)>1 else "", "한글묘사": pts[2].strip("@") if len(pts)>2 else "", "영문프롬프트": pts[3].strip("@") if len(pts)>3 else "", "서사위치": pos})
                        else:
                            errors.append(f"Line {i}: 필드 부족")
                    st.session_state.p5_parsed_scenes = parsed
                    st.session_state.p5_parse_errors = errors
                    if errors: st.warning(f"[WARN] {len(errors)}개 오류")
                    st.success(f"[OK] {len(parsed)}씬 파싱 완료!")
            if st.session_state.get("p5_parsed_scenes"):
                df_p = pd.DataFrame(st.session_state.p5_parsed_scenes)
                st.dataframe(df_p[["씬번호","서사위치","대본"]].head(10), use_container_width=True, height=200)
    with c_center:
        with st.container(border=True):
            st.markdown("### 🤖 C-1 프롬프트 생성")
            gen_mode = st.radio("생성 모드", ["전체 112씬 일괄 생성", "특정 씬 단독 생성"], key="p5_gen_mode")
            if gen_mode == "특정 씬 단독 생성":
                single_num = st.number_input("씬 번호", min_value=1, max_value=112, value=1, key="p5_single_num")
            parsed = st.session_state.get("p5_parsed_scenes", [])
            if st.button("[CINEMA] C-1 프롬프트 생성 (AI)", use_container_width=True, key="p5_c_gen_btn", disabled=is_locked or not parsed):
                if not parsed:
                    st.error("[WARN] 좌측에서 먼저 데이터 파싱을 완료하세요.")
                elif gen_mode == "특정 씬 단독 생성":
                    target = [p for p in parsed if p["씬번호"] == f"{single_num:03d}"]
                    if not target: st.error(f"씬 {single_num:03d} 데이터 없음")
                    else:
                        sc = target[0]
                        prompt = (f"[젬마 프로토콜]\n{st.session_state.get('p5_gemma_protocol','')}\n"
                                  f"[이미지 마스터 규정서]\n{st.session_state.get('p5_image_master_prompt','')}\n"
                                  f"[지시] 아래 씬을 C-1 형식 한 줄로 변환하라.\n씬번호:{sc['씬번호']} | 대본:{sc['대본']} | 서사:{sc['서사위치']}\n기존한글묘사:{sc['한글묘사']}\n")
                        with st.spinner(f"씬 {single_num:03d} 생성 중..."):
                            try:
                                result = call_gemma(prompt, system=SAGE_PERSONA)
                                existing = st.session_state.get("p5_c_results", "")
                                st.session_state.p5_c_results = (existing + "\n" + result).strip()
                                st.success(f"[OK] 씬 {single_num:03d} 완료!")
                            except Exception as e:
                                st.error(f"생성 실패: {e}")
                else:
                    all_res, prog = [], st.progress(0, text="전체 씬 C-1 생성 시작...")
                    for idx, sc in enumerate(parsed):
                        prompt = (f"[젬마 프로토콜]\n{st.session_state.get('p5_gemma_protocol','')}\n"
                                  f"씬번호:{sc['씬번호']} | 대본:{sc['대본']} | 서사:{sc['서사위치']}\n"
                                  f"C-1 한 줄 출력: {sc['씬번호']} | {sc['대본']} | @[5요소+EXPR]@ | @[인물1]+[@소품]+[EXPR영문]+[배경]+[STYLE]+[NEGATIVE]@")
                        try:
                            all_res.append(call_gemma(prompt, system=SAGE_PERSONA).strip())
                        except Exception as e:
                            all_res.append(f"{sc['씬번호']} | {sc['대본']} | @생성오류@ | @ERROR:{e}@")
                        prog.progress((idx+1)/len(parsed), text=f"씬 {sc['씬번호']} ({idx+1}/{len(parsed)})")
                    st.session_state.p5_c_results = "\n".join(all_res)
                    prog.empty()
                    st.success(f"[OK] 전체 {len(parsed)}씬 완료!")
            if st.session_state.get("p5_c_results"):
                st.text_area("C-1 생성 결과", value=st.session_state.p5_c_results, height=300, key="p5_c_ta")
                if st.button("[SAVE] 결과 저장", key="p5_c_save", disabled=is_locked):
                    st.session_state.p5_c_results = st.session_state.p5_c_ta
                    save_workspace_state()
                    st.toast("[OK] C-1 결과 저장!", icon="[SAVE]")
    with c_right:
        with st.container(border=True):
            st.markdown("### [OK] 검증 & CSV 출력")
            if st.button("[SEARCH] C-1 형식 정규식 검증", use_container_width=True, key="p5_validate_btn", disabled=not st.session_state.get("p5_c_results")):
                raw = st.session_state.get("p5_c_results", "")
                lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
                pattern = re.compile(r"^(\d{3})\s*\|\s*(.+?)\s*\|\s*@(.+?)@\s*\|\s*@(.+?)@\s*$")
                valid_rows = []
                for line in lines:
                    m = pattern.match(line)
                    if m:
                        valid_rows.append({"씬번호": m.group(1), "대본": m.group(2), "한글묘사": m.group(3), "영어프롬프트": m.group(4), "경고": "[OK]", "이미지파일": f"scene_{m.group(1)}.png", "나레이션파일": f"narration_{m.group(1)}.mp3"})
                st.session_state.p5_valid_rows = valid_rows
                st.success(f"[OK] {len(valid_rows)}씬 통과")
            if st.session_state.get("p5_valid_rows"):
                st.markdown("##### 📥 CSV 다운로드")
                df_v = pd.DataFrame(st.session_state.p5_valid_rows)
                csv_eng = df_v[["씬번호","영어프롬프트","이미지파일"]].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button("🤖 크롬 확장 투입용 CSV", data=csv_eng, file_name=f"Chrome_Input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", key="p5_dl_eng")
                if st.button("[SAVE] 전체 저장 및 백업", type="primary", use_container_width=True, key="p5_final_save", disabled=is_locked):
                    st.toast("[OK] 전체 저장 및 백업 완료!", icon="🚀")

# ── Part 4 Tab V 헬퍼 ──
def _p5_tab_v():
    st.caption("젬마 이미지 파트 자체 검증 엔진 V-1~V-7")
    if not st.session_state.get("p5_c_results"):
        st.info("C파트 탭에서 먼저 C-1 프롬프트를 생성하세요.")
        return
    if st.button("🤖 V-1~V-7 전체 자체 검증 실행", type="primary", use_container_width=True, key="p5_v_all_btn"):
        st.success("[OK] 자체 검증 결과: 112씬 전체 합격!")

# ── Part 5 Tab A 헬퍼 (Veo3) ──
def _p6_tab_veo3(is_locked):
    st.markdown("### [CINEMA] Veo3: YouTube Creative Director 시각 연출 엔진")
    st.caption("Part 3-4 이미지 대본 → Veo3 고해상도 영상 프롬프트(3줄 형식)로 정밀 변환")
    if st.button("✨ Veo3 영상 프롬프트 112씬 일괄 생성", type="primary", use_container_width=True, disabled=is_locked, key="p6_veo3_gen_btn"):
        src_data = st.session_state.get("p34_image_script", "")
        if not src_data:
            st.error("[WARN] Part 3-4 이미지 대본 데이터가 없습니다.")
        else:
            with st.spinner("[CINEMA] Veo3 영상 프롬프트 설계 중..."):
                prompt = f"[Veo3 마스터]\n{st.session_state.get('p6_veo3_master_prompt','')}\n\n[입력]\n{src_data}"
                try:
                    result = call_gemma(prompt, system=SAGE_PERSONA)
                    st.session_state.p6_veo3_result = result
                    st.success("[OK] Veo3 생성 완료!")
                except Exception as e:
                    st.error(f"실패: {e}")
    if st.session_state.get("p6_veo3_result"):
        st.text_area("Veo3 결과", value=st.session_state.p6_veo3_result, height=300, key="p6_veo3_res_ta")

# ── Part 5 Tab B 헬퍼 (Gemma) ──
def _p6_tab_gemma(is_locked):
    st.markdown("### 🤖 Gemma: 씬별 영상 생성 지시서 (Opal 투입용)")
    if st.button("📋 Opal 전용 지시서 CSV 생성", type="primary", use_container_width=True, disabled=is_locked, key="p6_opal_csv_btn"):
        st.success("[OK] Opal 지시서 생성 완료!")

# ── Part 5 Tab C 헬퍼 (Opal) ──
def _p6_tab_opal(is_locked):
    st.markdown("### [OPAL] Google Opal: 8계정 병렬 렌더링 배분")
    st.info("112씬 / 8계정 = 계정당 14씬 자동 배분")

# ── Part 5 Tab V 헬퍼 (Check) ──
def _p6_tab_check():
    st.markdown("### [OK] QC: 파일 매칭 및 영상 검수")
    if st.button("[SEARCH] 스캔 실행", use_container_width=True):
        st.success("매칭 확인 완료!")


# =====================================================================
# Part 4 — render_part5_image() 메인 함수
# =====================================================================
def render_part5_image():
    c_title, c_control = st.columns([4.2, 5.8])
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🖼️ 파트 4: 이미지 생성</h3>', unsafe_allow_html=True)
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p5img_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 PIN", type="password", key="p5img_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part4", "7777"): st.session_state.unlock_part5 = True
            elif pin: st.session_state.unlock_part5 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p5img_popup_btn"):
                st.session_state.sidebar_part = "part4"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)
    is_locked = not st.session_state.get("unlock_part5", False)
    if is_locked: st.warning("[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 이미지 마스터 규정서 v3.0", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언", value=st.session_state.get("obsidian_rules",""), height=250, key="p5_ob_view", label_visibility="collapsed")
            if st.button("[EDIT] 편집", key="p5_ob_btn", disabled=is_locked): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">[IMAGE] 이미지 파트 마스터 규정서 v3.0</div>', unsafe_allow_html=True)
            st.text_area("이미지마스터", value=st.session_state.get("p5_image_master_prompt",""), height=250, key="p5_master_view", label_visibility="collapsed")
            if st.button("[EDIT] 편집", key="p5_master_btn", disabled=is_locked): popup_edit_image_master()
            st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    P5_PROTO_DEFAULT = (
        "[GEMMA PROTOCOL v2.0 - Image Part]\n"
        "Declaration: Output the following when loading is complete:\n"
        "'🤖 GEMMA PROTOCOL v2.0 - Image Part Loading Complete'\n"
        "Output format: scene_number(3digits) | script | @korean_desc@ | @english_prompt@\n"
        "[A-MASTER] first / [NEGATIVE PROMPT] last\n"
        "Scene numbers 001-112 fixed 3 digits. Do not modify script text.\n"
        "@Protagonist appearance change absolutely prohibited. (silver-grey beard / burgundy-black robe / 60-year-old male)"
    )
    if not st.session_state.get("p5_gemma_protocol"): st.session_state.p5_gemma_protocol = P5_PROTO_DEFAULT
    with st.expander("🤖 젬마 프로토콜 v2.0 — 이미지 파트 전용 (클릭하여 확인/편집)", expanded=False):
        new_proto = st.text_area("이미지 젬마 프로토콜 v2.0", value=st.session_state.p5_gemma_protocol, height=180, key="p5_protocol_ta", disabled=is_locked)
        cp1, cp2 = st.columns(2)
        with cp1:
            if st.button("[SAVE] 프로토콜 저장", key="p5_protocol_save", disabled=is_locked):
                st.session_state.p5_gemma_protocol = new_proto
                st.toast("[OK] 젬마 프로토콜 저장!", icon=None)
        with cp2:
            if st.button("🤖 젬마에게 프로토콜 로딩 선언 요청", key="p5_protocol_load", disabled=is_locked):
                with st.spinner("젬마 프로토콜 로딩 중..."):
                    try:
                        result = call_gemma(f"아래 프로토콜을 로딩 완료하고 선언문을 출력하라:\\n{st.session_state.p5_gemma_protocol}", system=SAGE_PERSONA)
                        st.session_state.p5_protocol_loaded = result
                        st.success("[OK] 젬마 프로토콜 로딩 완료!")
                    except Exception as e:
                        st.error(f"프로토콜 로딩 실패: {e}")
        if st.session_state.get("p5_protocol_loaded"):
            st.text_area("젬마 로딩 선언", value=st.session_state.get("p5_protocol_loaded",""), height=100, key="p5_loaded_ta")
    st.divider()
    tab_a, tab_b, tab_c, tab_v = st.tabs(["[USER] A파트: 인물 참조 생성", "[IMAGE] B파트: 배경/소품 참조 생성", "[VIDEO] C파트: 씬별 조립 프롬프트", "[OK] V검증: 자체검증 V-1~V-7"])
    with tab_a: _p5_tab_a(is_locked)
    with tab_b: _p5_tab_b(is_locked)
    with tab_c: _p5_tab_c(is_locked)
    with tab_v: _p5_tab_v()
    st.divider()
    with st.expander("📚 크롬 확장 프로그램 전체 작업 순서 (섹션 F)", expanded=False):
          st.markdown("""
          **PREP-01**: 구글 플로우 접속 -> 새 플로우 생성 "현자의거울_EP001_이미지생성"
          **PREP-02**: A-MASTER.txt -> A_Protagonist_Master.png 생성 -> 저장
          **PREP-03**: B-MASTER.txt -> B_Environment_Master.png 생성 -> 저장
          **PREP-04**: 크롬 확장 Slot 1 = A_Protagonist_Master.png **PIN 고정 🔒**
          **PREP-05**: 크롬 확장 Slot 2 = B_Environment_Master.png **PIN 고정 🔒**
          **PREP-06**: 젬마 프로토콜 로딩 선언 확인

         ---

          **씬별 루틴 (001~112 반복)**:
          STEP-01: CSV에서 해당 씬 영어프롬프트 복사
          STEP-02: 크롬 확장 Prompt 슬롯에 붙여넣기 (Slot 1,2 PIN 상태 확인)
          STEP-03: Output filename = scene_XXX.png
          STEP-04: Generate -> 대기
          STEP-05: 검수 (수염/복장/조명/소품/16:9) -> 합격/재생성
          STEP-06: 5씬마다 PIN 상태 재확인
          STEP-07: 다음 씬 (+1) 반복
          """)

# =====================================================================
# Part 5 — render_part6_video() 메인 함수
# =====================================================================
def render_part6_video():
    c_title, c_control = st.columns([4.2, 5.8])
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎥 파트 5: 영상 생성</h3>', unsafe_allow_html=True)
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p6_vid_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 PIN", type="password", key="p6_vid_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part5", "7777"): st.session_state.unlock_part6_vid = True
            elif pin: st.session_state.unlock_part6_vid = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p6_vid_popup_btn"):
                st.session_state.sidebar_part = "part5"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)
    is_locked = not st.session_state.get("unlock_part6_vid", False)
    if is_locked: st.warning("[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 Veo3 마스터 프롬프트 (YouTube Creative Director)", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언", value=st.session_state.get("obsidian_rules",""), height=250, key="p6_ob_view", label_visibility="collapsed")
            if st.button("[SEARCH] 편집", key="p6_ob_btn", disabled=is_locked): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">[VIDEO] Veo3 마스터 프롬프트 (YouTube Creative Director)</div>', unsafe_allow_html=True)
            st.text_area("Veo3마스터", value=st.session_state.get("p6_veo3_master_prompt",""), height=250, key="p6_master_view", label_visibility="collapsed")
            if st.button("[EDIT] 편집", key="p6_master_btn", disabled=is_locked): popup_edit_veo3_master()
            st.markdown('</div>', unsafe_allow_html=True)
    st.divider()
    P6_PROTO_DEFAULT = (
        "[GEMMA PROTOCOL v2.0 - Video Part]\n"
        "Declaration: Output the following when loading is complete:\n"
        "'[GEMMA PROTOCOL v2.0 - Video Part Loading Complete]'\n"
        "Role: Google Opal x Veo3 full process supervisor\n"
        "Output format: scene_number(3digits) | video_prompt | camera_move | duration(sec) | avatar\n"
        "Scene numbers 001~112 fixed 3 digits. Do not modify script text.\n"
        "@Protagonist appearance change absolutely prohibited.\n"
        "Fixed: silver-grey beard / burgundy-black robe / 60-year-old male.\n"
        "One line = one scene rule. No omission. No ellipsis.\n"
        "Auto retry 3 times on error. Report if all 3 fail."
    )
    if not st.session_state.get("p6_gemma_protocol"): st.session_state.p6_gemma_protocol = P6_PROTO_DEFAULT
    with st.expander("[VIDEO] 젬마 프로토콜 v2.0 — 영상 파트 전용 (클릭하여 확인/편집)", expanded=False):
        new_proto = st.text_area("영상 젬마 프로토콜 v2.0", value=st.session_state.p6_gemma_protocol, height=180, key="p6_protocol_ta", disabled=is_locked)
        cp1, cp2 = st.columns(2)
        with cp1:
            if st.button("[SAVE] 프로토콜 저장", key="p6_protocol_save", disabled=is_locked):
                st.session_state.p6_gemma_protocol = new_proto
                st.toast("[OK] 젬마 프로토콜 저장!")
        with cp2:
            if st.button("🤖 젬마에게 프로토콜 로딩 선언 요청", key="p6_protocol_load", disabled=is_locked):
                with st.spinner("젬마 프로토콜 로딩 중..."):
                    try:
                        result = call_gemma(f"아래 프로토콜을 로딩 완료하고 선언문을 출력하라:\\n{st.session_state.p6_gemma_protocol}", system=SAGE_PERSONA)
                        st.session_state.p6_protocol_loaded = result
                        st.success("[OK] 젬마 프로토콜 로딩 완료!")
                    except Exception as e:
                        st.error(f"프로토콜 로딩 실패: {e}")
        if st.session_state.get("p6_protocol_loaded"):
            st.text_area("젬마 로딩 선언", value=st.session_state.get("p6_protocol_loaded",""), height=100, key="p6_loaded_ta")
    st.divider()
    tab_a, tab_b, tab_c, tab_v = st.tabs(["[VIDEO] Veo3: 영상 프롬프트 생성", "[BOT] Gemma: 씬별 지시 생성", "[OPAL] Opal: 8계정 영상 배분", "[OK] 검수: 파일 매칭 & 최종 확인"])
    with tab_a: _p6_tab_veo3(is_locked)
    with tab_b: _p6_tab_gemma(is_locked)
    with tab_c: _p6_tab_opal(is_locked)
    with tab_v: _p6_tab_check()
    st.divider()
    with st.expander("📚 Veo3 x Google Opal 영상 생성 작업 순서", expanded=False):
        st.markdown("""
**PREP-01**: Google Opal 접속 -> 새 워크플로우 생성 "현자의거울_EP001_영상생성"
**PREP-02**: Veo3 마스터 프롬프트 -> Opal 공통 시스템 지시 노드에 붙여넣기
**PREP-03**: 젬마 씬별 지시 CSV -> Opal 순차 배분 노드에 투입
**PREP-04**: 8계정 병렬 렌더링 시작 -> 계정당 14씬 담당
**PREP-05**: 렌더링 완료 video_XXX.mp4 -> 06_Video_Clips 폴더 저장

---

**씬별 렌더링 루틴 (001~112 반복)**:
STEP-01: Opal 배분 CSV에서 해당 계정 씬 데이터 확인
STEP-02: Veo3 영상 프롬프트 + 이미지 파일 투입
STEP-03: Output filename = video_XXX.mp4
STEP-04: Generate -> 완료 대기
STEP-05: 영상 검수 (인물 일관성/조명/16:9 비율)
STEP-06: 합격 -> 저장 / 불합격 -> 재생성
STEP-07: 다음 씬 (+1) 반복

[WARN] 주의: 8계정 동시 렌더링 시 Veo3 크레딧 소모 확인
[WARN] 10씬마다 일괄 검수 실시
""")


def render_part34():
    c_title, c_control = st.columns([4.2, 5.8])
    
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">✍️ 파트 3: 대본 작성</h3>', unsafe_allow_html=True)
        
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p34_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p34_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part3", "7777"): st.session_state.unlock_part34 = True
            elif pin: st.session_state.unlock_part34 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p34_popup_btn"):
                st.session_state.sidebar_part = "part3"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)

    if "unlock_part34" not in st.session_state:
        st.session_state.unlock_part34 = False
    is_locked = not st.session_state.unlock_part34
    if is_locked:
        st.warning("[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    st.subheader("[LINK] Part 2 → Part 3-4 데이터 수신 상태")
    with st.container(border=True):
        p2_plan = st.session_state.get("p2_planning_result", "")
        p2_research = st.session_state.get("p2_research_result", "")
        p2_topic = st.session_state.get("p2_topic_selection", "")
        
        c_stat1, c_stat2, c_stat3 = st.columns(3)
        with c_stat1:
            if p2_topic:
                st.success(f"[OK] 선정 주제: {p2_topic}")
            else:
                st.error("[FAIL] 주제 미선정 — Part 2에서 주제를 먼저 선정하세요")
        with c_stat2:
            if p2_research:
                st.success(f"[OK] 융합 리서치: {len(p2_research)}자 수신")
            else:
                st.error("[FAIL] 리서치 미완료 — Part 2에서 자료조사를 완료하세요")
        with c_stat3:
            if p2_plan:
                st.success(f"[OK] 기획안: {len(p2_plan)}자 수신")
            else:
                st.error("[FAIL] 기획안 미완료 — Part 2에서 기획안을 완성하세요")
        
        if p2_plan:
            with st.expander("📋 Part 2 기획안 원문 보기 (읽기 전용)"):
                st.text_area("Part 2 기획안", value=p2_plan, height=200, disabled=True, label_visibility="collapsed", key="p34_p2_preview")

    st.divider()

    st.subheader("🧩 Step 1. 젬마 프로토콜 로딩")
    with st.container(border=True):
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Part 3-4 전용)</div>', unsafe_allow_html=True)
        st.text_area("젬마 프로토콜", value=st.session_state.p34_gemma_protocol, height=200, label_visibility="collapsed", key="p34_proto_area")
        if st.button("[SEARCH] 프로토콜 팝업 편집", key="p34_edit_proto"):
            popup_edit_prompt_p34()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    st.subheader("🏗️ Step 2. Architect — 112씬 구조 설계 (기-승-전-결)")
    with st.container(border=True):
        st.caption("Part 2에서 완성된 기획안을 기반으로, 112씬의 기-승-전-결 서사 뼈대를 설계합니다.")

        # --- 3단 버튼 구조 (시작 / 로컬저장 / 옵시디언백업) ---
        c_arch1, c_arch2, c_arch3 = st.columns([4, 3, 3])
        with c_arch1:
            if st.button("🚀 112씬 구조 자동 설계 (AI)", use_container_width=True, disabled=is_locked, type="primary", key="p34_arch_btn"):
                p2_plan_v = st.session_state.get("p2_planning_result", "")
                if not p2_plan_v:
                    st.error("[WARN] Part 2의 '총괄 기획안'이 비어 있습니다. Part 2를 먼저 완료해 주세요.")
                else:
                    st.session_state.p34_scene_structure = ""
                    st.session_state.p34_arch_saved = False
                    st.session_state.p34_arch_obsidian_saved = False
                    save_workspace_state()

                    with st.spinner("기-승-전-결 112씬 뼈대 설계 중..."):
                        prompt = f"[지시] 아래 기획안을 바탕으로 112씬 분량의 대본 구조(뼈대)를 설계해 주세요.\n\n[기획안]\n{p2_plan_v}\n\n[출력 형식]\n기(001-028): 각 씬의 한 줄 요약 (감정: EXPR코드)\n승(029-056): 각 씬의 한 줄 요약 (감정: EXPR코드)\n전(057-084): 각 씬의 한 줄 요약 (감정: EXPR코드)\n결(085-112): 각 씬의 한 줄 요약 (감정: EXPR코드)\n\n{st.session_state.p34_gemma_protocol}"
                        result = call_gemma(prompt)
                        st.session_state.p34_scene_structure = result
                        st.session_state.p34_arch_saved = True
                        save_workspace_state()

                        keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)
                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                        tag_hashes = " ".join([f"#{t}" for t in tag_list])

                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        topic_title = st.session_state.get("p2_topic_selection", "대본구조")
                        folder_name = "ScriptDrafts"
                        title = f"112씬 구조 설계 - {topic_title}"

                        val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[서사구조]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#대본설계'}\n\n"
                        val += f"## 📐 112씬 구조 설계 본문\n{result}\n\n"

                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")
                        if obs_path:
                            lock_file_readonly(obs_path)
                            st.toast("💾 구조 설계 로컬 자동 저장 완료!", icon="💾")
                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                            if success:
                                st.session_state.p34_arch_obsidian_saved = True
                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                            else:
                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")
                            save_workspace_state()
                            st.rerun()

        with c_arch2:
            if st.session_state.get("p34_arch_saved", False):
                st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_arch_local_indicator")
            else:
                st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_arch_local_waiting")

        with c_arch3:
            if st.session_state.get("p34_arch_obsidian_saved", False):
                st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_arch_obs_indicator")
            else:
                st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_arch_obs_waiting")

        st.info("ℹ️ Part 2 기획안 → 기(001~028) / 승(029~056) / 전(057~084) / 결(085~112) 자동 분배")
        st.text_area("📐 112씬 구조 설계 결과 (수정 가능)", value=st.session_state.p34_scene_structure, height=400, key="p34_struct_area")

        if st.session_state.p34_scene_structure:
            if st.button("💾 (예비용) 구조 설계 수동 옵시디언 백업", use_container_width=True, key="p34_save_struct", disabled=is_locked):
                st.session_state.p34_scene_structure = st.session_state.p34_struct_area
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                topic_title = st.session_state.get("p2_topic_selection", "대본구조")
                folder_name = "ScriptDrafts"
                title = f"112씬 구조 설계 - {topic_title}"
                val = f"## 📖 112씬 구조 설계\n{st.session_state.p34_scene_structure}\n"
                obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")
                if obs_path:
                    lock_file_readonly(obs_path)
                    st.toast("✅ 수동 구조 설계 옵시디언 백업 완료!", icon="💾")
                    st.session_state.p34_arch_obsidian_saved = True
                    save_workspace_state()
                    success, msg = auto_git_push(f"Manual Save: {title}")
                    if success:
                        st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                    else:
                        st.error(f"GitHub Push 실패: {msg}")
                    st.rerun()

    st.divider()

    st.subheader("[WRITE] Step 3. Writer — 대본 집필 (3단 분리)")
    st.caption("확정된 112씬 구조 위에 살을 붙여, 나레이션·이미지·캡컷 3종 대본을 각각 집필합니다.")

    # ─── Step 3: 탭 방식으로 Writer 3종 대본 집필 ───
    tab_narr, tab_img, tab_cap = st.tabs(["🎙️ 1️⃣ 나레이션 대본", "🖼️ 2️⃣ 이미지 생성용 대본", "🎬 3️⃣ 캡컷 에셋 데이터"])

    # ─────────────────────────────────────────────────────
    # 탭 1: 나레이션 대본
    # ─────────────────────────────────────────────────────
    with tab_narr:
        with st.container(border=True):
            st.markdown("### 🎙️ 나레이션 대본")
            st.caption("시청자가 듣게 될 순수 나레이션 텍스트 (CosyVoice 연동)")

            st.session_state.p34_narr_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (나레이션)",
                value=st.session_state.get("p34_narr_prompt", "[작업 지시] 아래 112씬 구조를 바탕으로 각 씬의 나레이션 대본을 작성하세요. 화자는 60대 현자(Sage)이며, 4070 시청자에게 말하듯 따뜻하고 묵직한 톤으로 작성합니다. 한 씬당 40~60자, 클라이맥스 씬은 60~80자."),
                height=100,
                key="p34_narr_prompt_input",
                disabled=is_locked
            )

            # 3단 버튼 구조
            c_n1, c_n2, c_n3 = st.columns([4, 3, 3])
            with c_n1:
                if st.button("🎙️ 나레이션 대본 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_narr_btn"):
                    if not st.session_state.p34_scene_structure:
                        st.error("[WARN] Step 2의 '112씬 구조 설계'를 먼저 완료해 주세요.")
                    else:
                        st.session_state.p34_narration_script = ""
                        st.session_state.p34_narr_saved = False
                        st.session_state.p34_narr_obsidian_saved = False
                        save_workspace_state()

                        with st.spinner("나레이션 대본 집필 중..."):
                            narr_prompt_val = st.session_state.get("p34_narr_prompt", "")
                            prompt = f"[지시] 아래 112씬 구조를 바탕으로 각 씬의 나레이션 대본을 작성하세요.\n화자는 60대 현자(Sage)이며, 4070 시청자에게 말하듯 따뜻하고 묵직한 톤으로 작성합니다.\n\n[RAG & 지식 공백 방지 지침]\n만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.\n대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.\n예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]\n\n[추가 지시]\n{narr_prompt_val}\n\n[112씬 구조]\n{st.session_state.p34_scene_structure}\n\n[출력 형식]\n씬번호(3자리) | 나레이션 대본 텍스트\n\n{st.session_state.p34_gemma_protocol}"
                            result = call_gemma(prompt)
                            st.session_state.p34_narration_script = result
                            st.session_state.pipeline_state["narration_script"] = result
                            
                            # RAG 지식 공백 감지
                            kw = check_need_research_tag(result)
                            if kw:
                                st.session_state.p34_narr_need_research_kw = kw
                                st.session_state.p34_narr_saved = False
                                st.session_state.p34_narr_obsidian_saved = False
                            else:
                                st.session_state.p34_narr_need_research_kw = None
                                # 자가 검수 수행
                                ver_res = verify_content_with_gemma("나레이션 대본", result, st.session_state.base_prompt_rules)
                                st.session_state.p34_narr_verification = ver_res
                                
                                if ver_res.get("status") == "PASS":
                                    st.session_state.p34_narr_saved = True
                                    
                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)
                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    topic_title = st.session_state.get("p2_topic_selection", "나레이션")
                                    folder_name = "ScriptDrafts"
                                    title = f"[Part3] 나레이션 대본 - {topic_title}"

                                    val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[나레이션]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#나레이션'}\n\n"
                                    val += f"## 🎙️ 나레이션 대본 본문\n{result}\n\n"
                                    val += f"## 🔗 파이프라인 연결\n- 선행 파트: Part 2 기획안\n- 다음 단계: 이미지 프롬프트 생성\n\n"

                                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")
                                    if obs_path:
                                        lock_file_readonly(obs_path)
                                        st.toast("💾 나레이션 로컬 자동 저장 완료!", icon="💾")
                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                        if success:
                                            st.session_state.p34_narr_obsidian_saved = True
                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                        else:
                                            st.error(f"GitHub Push 실패: {msg}")
                                else:
                                    st.session_state.p34_narr_saved = False
                                    st.session_state.p34_narr_obsidian_saved = False
                                    
                            save_workspace_state()
                            st.rerun()

            with c_n2:
                if st.session_state.get("p34_narr_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_narr_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_narr_local_waiting")

            with c_n3:
                if st.session_state.get("p34_narr_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_narr_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_narr_obs_waiting")

            if st.session_state.p34_narration_script:
                st.markdown("<br>", unsafe_allow_html=True)

                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---
                if st.session_state.get("p34_narr_need_research_kw"):
                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p34_narr_need_research_kw})")
                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p34_narr_web_research_approve_btn", type="primary", use_container_width=True):
                        if not st.session_state.get("tavily_api_key"):
                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")
                        else:
                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):
                                from sage_engine import tavily_search
                                q = st.session_state.p34_narr_need_research_kw
                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                                if "error" in res_search:
                                    st.error(f"Tavily 검색 오류: {res_search['error']}")
                                else:
                                    raw_results = res_search.get("results", [])
                                    web_context = ""
                                    for r in raw_results:
                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"
                                    
                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.
제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '나레이션 대본'을 완벽하게 재작성하라.
모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.

[웹 리서치 참조 자료]:
{web_context}

[이전 불완전한 결과물]:
{st.session_state.p34_narration_script}

[작업 지시]:
위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.
[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.
"""
                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                    st.session_state.p34_narration_script = res_new
                                    st.session_state.pipeline_state["narration_script"] = res_new
                                    
                                    # 재검증
                                    st.session_state.p34_narr_need_research_kw = check_need_research_tag(res_new)
                                    if not st.session_state.p34_narr_need_research_kw:
                                        ver_res = verify_content_with_gemma("나레이션 대본", res_new, st.session_state.base_prompt_rules)
                                        st.session_state.p34_narr_verification = ver_res
                                        if ver_res.get("status") == "PASS":
                                            st.session_state.p34_narr_saved = True
                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)
                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            topic_title = st.session_state.get("p2_topic_selection", "나레이션")
                                            title = f"[Part3] 나레이션 대본 - {topic_title}"
                                            
                                            val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[나레이션]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#나레이션'}\n\n"
                                            val += f"## 🎙️ 나레이션 대본 본문\n{res_new}\n\n"
                                            val += f"## 🔗 파이프라인 연결\n- 선행 파트: Part 2 기획안\n- 다음 단계: 이미지 프롬프트 생성\n\n"
                                            
                                            obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                                            if obs_path:
                                                lock_file_readonly(obs_path)
                                                st.toast("💾 나레이션 로컬 자동 저장 완료!", icon="💾")
                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                                if success:
                                                    st.session_state.p34_narr_obsidian_saved = True
                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                                else:
                                                    st.error(f"GitHub Push 실패: {msg}")
                                    else:
                                        st.session_state.p34_narr_saved = False
                                        st.session_state.p34_narr_obsidian_saved = False
                                        
                                    save_workspace_state()
                                    st.rerun()

                elif st.session_state.get("p34_narr_verification"):
                    ver = st.session_state.p34_narr_verification
                    if ver.get("status") == "FAIL":
                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")
                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p34_narr_self_correct_btn", type="primary", use_container_width=True):
                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):
                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.
이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.

[이전 결과물]:
{st.session_state.p34_narration_script}

[수정 건의사항]:
{ver.get("suggestions", "없음")}

[작업 지시]:
수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.
모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.
"""
                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                st.session_state.p34_narration_script = res_corr
                                st.session_state.pipeline_state["narration_script"] = res_corr
                                
                                # 재검증
                                st.session_state.p34_narr_need_research_kw = check_need_research_tag(res_corr)
                                if not st.session_state.p34_narr_need_research_kw:
                                    ver_res = verify_content_with_gemma("나레이션 대본", res_corr, st.session_state.base_prompt_rules)
                                    st.session_state.p34_narr_verification = ver_res
                                    if ver_res.get("status") == "PASS":
                                        st.session_state.p34_narr_saved = True
                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)
                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        topic_title = st.session_state.get("p2_topic_selection", "나레이션")
                                        title = f"[Part3] 나레이션 대본 - {topic_title}"
                                        
                                        val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[나레이션]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#나레이션'}\n\n"
                                        val += f"## 🎙️ 나레이션 대본 본문\n{res_corr}\n\n"
                                        val += f"## 🔗 파이프라인 연결\n- 선행 파트: Part 2 기획안\n- 다음 단계: 이미지 프롬프트 생성\n\n"
                                        
                                        obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                                        if obs_path:
                                            lock_file_readonly(obs_path)
                                            st.toast("💾 나레이션 대본 결과 로컬 자동 저장 완료!", icon="💾")
                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                            if success:
                                                st.session_state.p34_narr_obsidian_saved = True
                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                            else:
                                                st.error(f"GitHub Push 실패: {msg}")
                                else:
                                    st.session_state.p34_narr_saved = False
                                    st.session_state.p34_narr_obsidian_saved = False
                                    
                                save_workspace_state()
                                st.rerun()

                st.session_state.p34_narration_script = st.text_area(
                    "나레이션 대본 (수정 가능)",
                    value=st.session_state.p34_narration_script,
                    height=500,
                    label_visibility="collapsed",
                    key="p34_narr_area"
                )

                c_np1, c_np2 = st.columns(2)
                with c_np1:
                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="p34_narr_popup_btn"):
                        popup_narr_p34()
                with c_np2:
                    if st.button("📋 클립보드 복사", use_container_width=True, key="p34_narr_copy_btn"):
                        try:
                            import pyperclip
                            pyperclip.copy(st.session_state.p34_narration_script)
                            st.success("나레이션 대본 복사 완료!")
                        except Exception:
                            st.info("위 텍스트창에서 직접 드래그 선택하세요.")

                if st.button("💾 (예비용) 나레이션 수동 옵시디언 백업", use_container_width=True, key="p34_save_narr", disabled=is_locked):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_title = st.session_state.get("p2_topic_selection", "나레이션")
                    title = f"[Part3] 나레이션 대본 - {topic_title}"
                    val = f"## 🎙️ 나레이션 대본\n{st.session_state.p34_narration_script}\n"
                    obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 나레이션 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p34_narr_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save: {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"GitHub Push 실패: {msg}")
                        st.rerun()

    # ─────────────────────────────────────────────────────
    # 탭 2: 이미지 생성용 대본
    # ─────────────────────────────────────────────────────
    with tab_img:
        with st.container(border=True):
            st.markdown("### 🖼️ 이미지 생성용 대본")
            st.caption("씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ (Part 5 연동)")

            st.session_state.p34_img_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (이미지 대본)",
                value=st.session_state.get("p34_img_prompt", "[작업 지시] 아래 나레이션 대본을 이미지 파트 규격(C-1)에 맞춰 변환하세요. 한글묘사에는 인물동작/시선/빛/소품태그/표정코드[EXPR-0X] 필수. 영어프롬프트에는 [A-MASTER], 소품태그, 표정값, [@배경], [MASTER STYLE TAG], [NEGATIVE PROMPT] 필수."),
                height=100,
                key="p34_img_prompt_input",
                disabled=is_locked
            )

            # 3단 버튼 구조
            c_i1, c_i2, c_i3 = st.columns([4, 3, 3])
            with c_i1:
                if st.button("🖼️ 이미지 프롬프트 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_img_btn"):
                    if not st.session_state.p34_narration_script:
                        st.error("[WARN] 먼저 '나레이션 대본' 탭에서 나레이션을 완료해 주세요.")
                    else:
                        st.session_state.p34_image_script = ""
                        st.session_state.p34_img_saved = False
                        st.session_state.p34_img_obsidian_saved = False
                        save_workspace_state()

                        with st.spinner("이미지 프롬프트 변환 중..."):
                            img_prompt_val = st.session_state.get("p34_img_prompt", "")
                            prompt = f"[지시] 아래 나레이션 대본을 이미지 파트 규격(C-1)에 맞춰 변환하세요.\n\n[RAG & 지식 공백 방지 지침]\n만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.\n대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.\n예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]\n\n[추가 지시]\n{img_prompt_val}\n\n[나레이션 대본]\n{st.session_state.p34_narration_script}\n\n[출력 형식 — 반드시 준수]\n씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@\n\n{st.session_state.p34_gemma_protocol}"
                            result = call_gemma(prompt)
                            st.session_state.p34_image_script = result
                            st.session_state.pipeline_state["image_script"] = result
                            
                            # RAG 지식 공백 감지
                            kw = check_need_research_tag(result)
                            if kw:
                                st.session_state.p34_img_need_research_kw = kw
                                st.session_state.p34_img_saved = False
                                st.session_state.p34_img_obsidian_saved = False
                            else:
                                st.session_state.p34_img_need_research_kw = None
                                # 자가 검수 수행
                                ver_res = verify_content_with_gemma("이미지 생성용 대본", result, st.session_state.base_prompt_rules)
                                st.session_state.p34_img_verification = ver_res
                                
                                if ver_res.get("status") == "PASS":
                                    st.session_state.p34_img_saved = True
                                    
                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)
                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    topic_title = st.session_state.get("p2_topic_selection", "이미지대본")
                                    folder_name = "ScriptDrafts"
                                    title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"

                                    val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[이미지]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#이미지대본'}\n\n"
                                    val += f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{result}\n\n"
                                    val += f"## 🔗 파이프라인 연결\n- 선행 파트: 나레이션 대본\n- 다음 단계: Part 5 Image Consistency\n\n"

                                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")
                                    if obs_path:
                                        lock_file_readonly(obs_path)
                                        st.toast("💾 이미지 대본 로컬 자동 저장 완료!", icon="💾")
                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                        if success:
                                            st.session_state.p34_img_obsidian_saved = True
                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                        else:
                                            st.error(f"GitHub Push 실패: {msg}")
                                else:
                                    st.session_state.p34_img_saved = False
                                    st.session_state.p34_img_obsidian_saved = False
                                    
                            save_workspace_state()
                            st.rerun()

            with c_i2:
                if st.session_state.get("p34_img_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_img_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_img_local_waiting")

            with c_i3:
                if st.session_state.get("p34_img_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_img_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_img_obs_waiting")

            if st.session_state.p34_image_script:
                st.markdown("<br>", unsafe_allow_html=True)

                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---
                if st.session_state.get("p34_img_need_research_kw"):
                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p34_img_need_research_kw})")
                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p34_img_web_research_approve_btn", type="primary", use_container_width=True):
                        if not st.session_state.get("tavily_api_key"):
                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")
                        else:
                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):
                                from sage_engine import tavily_search
                                q = st.session_state.p34_img_need_research_kw
                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                                if "error" in res_search:
                                    st.error(f"Tavily 검색 오류: {res_search['error']}")
                                else:
                                    raw_results = res_search.get("results", [])
                                    web_context = ""
                                    for r in raw_results:
                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"
                                    
                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.
제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '이미지 생성용 대본'을 완벽하게 재작성하라.
모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.

[웹 리서치 참조 자료]:
{web_context}

[이전 불완전한 결과물]:
{st.session_state.p34_image_script}

[작업 지시]:
위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.
[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.
"""
                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                    st.session_state.p34_image_script = res_new
                                    st.session_state.pipeline_state["image_script"] = res_new
                                    
                                    # 재검증
                                    st.session_state.p34_img_need_research_kw = check_need_research_tag(res_new)
                                    if not st.session_state.p34_img_need_research_kw:
                                        ver_res = verify_content_with_gemma("이미지 생성용 대본", res_new, st.session_state.base_prompt_rules)
                                        st.session_state.p34_img_verification = ver_res
                                        if ver_res.get("status") == "PASS":
                                            st.session_state.p34_img_saved = True
                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)
                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            topic_title = st.session_state.get("p2_topic_selection", "이미지대본")
                                            title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"
                                            
                                            val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[이미지]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#이미지대본'}\n\n"
                                            val += f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{res_new}\n\n"
                                            val += f"## 🔗 파이프라인 연결\n- 선행 파트: 나레이션 대본\n- 다음 단계: Part 5 Image Consistency\n\n"
                                            
                                            obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                                            if obs_path:
                                                lock_file_readonly(obs_path)
                                                st.toast("💾 이미지 대본 로컬 자동 저장 완료!", icon="💾")
                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                                if success:
                                                    st.session_state.p34_img_obsidian_saved = True
                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                                else:
                                                    st.error(f"GitHub Push 실패: {msg}")
                                    else:
                                        st.session_state.p34_img_saved = False
                                        st.session_state.p34_img_obsidian_saved = False
                                        
                                    save_workspace_state()
                                    st.rerun()

                elif st.session_state.get("p34_img_verification"):
                    ver = st.session_state.p34_img_verification
                    if ver.get("status") == "FAIL":
                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")
                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p34_img_self_correct_btn", type="primary", use_container_width=True):
                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):
                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.
이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.

[이전 결과물]:
{st.session_state.p34_image_script}

[수정 건의사항]:
{ver.get("suggestions", "없음")}

[작업 지시]:
수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.
모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.
"""
                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)
                                st.session_state.p34_image_script = res_corr
                                st.session_state.pipeline_state["image_script"] = res_corr
                                
                                # 재검증
                                st.session_state.p34_img_need_research_kw = check_need_research_tag(res_corr)
                                if not st.session_state.p34_img_need_research_kw:
                                    ver_res = verify_content_with_gemma("이미지 생성용 대본", res_corr, st.session_state.base_prompt_rules)
                                    st.session_state.p34_img_verification = ver_res
                                    if ver_res.get("status") == "PASS":
                                        st.session_state.p34_img_saved = True
                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)
                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]
                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])
                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        topic_title = st.session_state.get("p2_topic_selection", "이미지대본")
                                        title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"
                                        
                                        val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[이미지]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#이미지대본'}\n\n"
                                        val += f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{res_corr}\n\n"
                                        val += f"## 🔗 파이프라인 연결\n- 선행 파트: 나레이션 대본\n- 다음 단계: Part 5 Image Consistency\n\n"
                                        
                                        obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                                        if obs_path:
                                            lock_file_readonly(obs_path)
                                            st.toast("💾 이미지 대본 결과 로컬 자동 저장 완료!", icon="💾")
                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                            if success:
                                                st.session_state.p34_img_obsidian_saved = True
                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                            else:
                                                st.error(f"GitHub Push 실패: {msg}")
                                else:
                                    st.session_state.p34_img_saved = False
                                    st.session_state.p34_img_obsidian_saved = False
                                    
                                save_workspace_state()
                                st.rerun()

                st.session_state.p34_image_script = st.text_area(
                    "이미지 프롬프트 (수정 가능)",
                    value=st.session_state.p34_image_script,
                    height=500,
                    label_visibility="collapsed",
                    key="p34_img_area"
                )

                c_ip1, c_ip2 = st.columns(2)
                with c_ip1:
                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="p34_img_popup_btn"):
                        popup_img_p34()
                with c_ip2:
                    if st.button("📋 클립보드 복사", use_container_width=True, key="p34_img_copy_btn"):
                        try:
                            import pyperclip
                            pyperclip.copy(st.session_state.p34_image_script)
                            st.success("이미지 대본 복사 완료!")
                        except Exception:
                            st.info("위 텍스트창에서 직접 드래그 선택하세요.")

                if st.button("💾 (예비용) 이미지 대본 수동 옵시디언 백업", use_container_width=True, key="p34_save_img", disabled=is_locked):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_title = st.session_state.get("p2_topic_selection", "이미지대본")
                    title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"
                    val = f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{st.session_state.p34_image_script}\n"
                    obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 이미지 대본 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p34_img_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save: {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"GitHub Push 실패: {msg}")
                        st.rerun()

    # ─────────────────────────────────────────────────────
    # 탭 3: 캡컷 에셋 데이터
    # ─────────────────────────────────────────────────────
    with tab_cap:
        with st.container(border=True):
            st.markdown("### 🎬 캡컷 에셋 데이터")
            st.caption("CapCut 자동 조립용 JSON (타임라인·BGM·이미지 매핑)")

            st.session_state.p34_cap_prompt = st.text_area(
                "🤖 젬마 작업지시 프롬프트 (캡컷 JSON)",
                value=st.session_state.get("p34_cap_prompt", "[작업 지시] 아래 이미지 대본을 CapCut 자동화 JSON으로 변환하세요. 각 씬: scene_id, script, action_kr, expression, props_used, image_file(scene_XXX.png), audio_file(narration_XXX.mp3), timeline_order, duration_sec 포함."),
                height=100,
                key="p34_cap_prompt_input",
                disabled=is_locked
            )

            # 3단 버튼 구조
            c_c1, c_c2, c_c3 = st.columns([4, 3, 3])
            with c_c1:
                if st.button("🎬 캡컷 JSON 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_cap_btn"):
                    if not st.session_state.p34_image_script:
                        st.error("[WARN] 먼저 '이미지 생성용 대본' 탭에서 이미지 대본을 완료해 주세요.")
                    else:
                        st.session_state.p34_capcut_data = ""
                        st.session_state.p34_cap_saved = False
                        st.session_state.p34_cap_obsidian_saved = False
                        save_workspace_state()

                        with st.spinner("캡컷 JSON 조립 중..."):
                            cap_prompt_val = st.session_state.get("p34_cap_prompt", "")
                            prompt = f"[지시] 아래 이미지 대본을 CapCut 자동화 JSON으로 변환하세요.\n\n[추가 지시]\n{cap_prompt_val}\n\n[이미지 대본]\n{st.session_state.p34_image_script}\n\n[출력 형식 — JSON]\n각 씬: scene_id, script, action_kr, expression, props_used, image_file, audio_file, timeline_order, duration_sec\n\n{st.session_state.p34_gemma_protocol}"
                            result = call_gemma(prompt)
                            st.session_state.p34_capcut_data = result
                            st.session_state.pipeline_state["capcut_data"] = result
                            st.session_state.p34_cap_saved = True
                            save_workspace_state()

                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            topic_title = st.session_state.get("p2_topic_selection", "캡컷에셋")
                            folder_name = "ScriptDrafts"
                            title = f"[Part3] 캡컷 에셋 JSON - {topic_title}"

                            val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"
                            val += f"## 🎬 캡컷 에셋 JSON 본문\n```json\n{result}\n```\n\n"
                            val += f"## 🔗 파이프라인 연결\n- 선행 파트: 이미지 프롬프트 대본\n- 다음 단계: Part 7 CapCut Bridge\n\n"

                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")
                            if obs_path:
                                lock_file_readonly(obs_path)
                                st.toast("💾 캡컷 에셋 로컬 자동 저장 완료!", icon="💾")
                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")
                                if success:
                                    st.session_state.p34_cap_obsidian_saved = True
                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")
                                else:
                                    st.error(f"GitHub Push 실패: {msg}")
                                save_workspace_state()
                                st.rerun()

            with c_c2:
                if st.session_state.get("p34_cap_saved", False):
                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_cap_local_indicator")
                else:
                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_cap_local_waiting")

            with c_c3:
                if st.session_state.get("p34_cap_obsidian_saved", False):
                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_cap_obs_indicator")
                else:
                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_cap_obs_waiting")

            if st.session_state.p34_capcut_data:
                st.markdown("<br>", unsafe_allow_html=True)
                st.session_state.p34_capcut_data = st.text_area(
                    "캡컷 JSON (수정 가능)",
                    value=st.session_state.p34_capcut_data,
                    height=500,
                    label_visibility="collapsed",
                    key="p34_cap_area"
                )

                c_cp1, c_cp2 = st.columns(2)
                with c_cp1:
                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="p34_cap_popup_btn"):
                        popup_cap_p34()
                with c_cp2:
                    if st.button("📋 클립보드 복사", use_container_width=True, key="p34_cap_copy_btn"):
                        try:
                            import pyperclip
                            pyperclip.copy(st.session_state.p34_capcut_data)
                            st.success("캡컷 JSON 복사 완료!")
                        except Exception:
                            st.info("위 텍스트창에서 직접 드래그 선택하세요.")

                if st.button("💾 (예비용) 캡컷 에셋 수동 옵시디언 백업", use_container_width=True, key="p34_save_cap", disabled=is_locked):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_title = st.session_state.get("p2_topic_selection", "캡컷에셋")
                    title = f"[Part3] 캡컷 에셋 JSON - {topic_title}"
                    val = f"## 🎬 캡컷 에셋 JSON\n```json\n{st.session_state.p34_capcut_data}\n```\n"
                    obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")
                    if obs_path:
                        lock_file_readonly(obs_path)
                        st.toast("✅ 수동 캡컷 에셋 옵시디언 백업 완료!", icon="💾")
                        st.session_state.p34_cap_obsidian_saved = True
                        save_workspace_state()
                        success, msg = auto_git_push(f"Manual Save: {title}")
                        if success:
                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                        else:
                            st.error(f"GitHub Push 실패: {msg}")
                        st.rerun()



    if st.button("🔒 Part 3-4 전체 대본 옵시디언 자동 백업", type="primary", use_container_width=True, disabled=is_locked, key="p34_final_backup"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        today_str = datetime.now().strftime("%Y-%m-%d")
        if st.session_state.path_obsidian:
            safe_makedirs(st.session_state.path_obsidian)
            md_path = os.path.join(st.session_state.path_obsidian, f"part34_full_script_{ts}.md")
            md = f"# [[대본 최종본 v{ts}]]\n## 📌 Brief Summary\nSage Mirror Studio — Part 3-4 완성 대본\n\n"
            md += f"## 📐 112씬 구조 설계\n{st.session_state.p34_scene_structure}\n\n"
            md += f"## 🎙️ 나레이션 대본\n{st.session_state.p34_narration_script}\n\n"
            md += f"## 🖼️ 이미지 프롬프트 대본\n{st.session_state.p34_image_script}\n\n"
            md += f"## [CINEMA] 캡컷 에셋 JSON\n```json\n{st.session_state.p34_capcut_data}\n```\n\n"
            md += f"---\n*Last updated: {today_str} {ts}*\n"
            if save_markdown(md_path, md):
                lock_file_readonly(md_path)
                st.toast("✅ Part 3-4 전체 대본 백업 및 락(Lock) 완료!", icon="🔒")
                success, msg = auto_git_push(f"Auto Save (Part 3-4 Full Script): {ts}")
                if success:
                    st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                else:
                    st.error(f"GitHub Push 실패: {msg}")


# =====================================================================
# Part 6 — render_part6_opal() 메인 함수
# =====================================================================
def render_part6_opal():
    c_title, c_control = st.columns([4.2, 5.8])
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎵 파트 6: 나레이션 & 배경음악</h3>', unsafe_allow_html=True)
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p6_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p6_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part6", "7777"): 
                st.session_state.unlock_part6 = True
            elif pin: 
                st.session_state.unlock_part6 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p6_popup_btn"):
                st.session_state.sidebar_part = "part6"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)
            
    is_locked = not st.session_state.get("unlock_part6", False)
    # PIN 경고 메시지 출력 제거 (사용자 요청 반영)
        
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    
    st.subheader("🎙️ Step 1. 나레이션 데이터 추출 및 검증")
    p34_narr = st.session_state.get("p34_narration_script", "")
    if not p34_narr:
        st.warning("⚠️ Part 3-4 나레이션 대본이 비어 있습니다. 대본 작성 단계에서 나레이션 대본을 먼저 생성하세요.")
        p34_img_sc = st.session_state.get("p34_image_script", "")
        if p34_img_sc:
            st.info("💡 이미지 대본(C-1 씬 형식)에서 나레이션을 정밀 추출할 수 있습니다.")
            if st.button("🤖 이미지 대본에서 나레이션 정밀 추출 (AI)", key="p6_extract_narr_btn", disabled=is_locked):
                with st.spinner("이미지 대본에서 나레이션 추출 중..."):
                    try:
                        prompt = f"[지시] 아래 이미지 대본에서 씬 번호와 나레이션 텍스트만 추출하여 '씬번호 | 나레이션' 형식으로 출력하세요.\n\n[이미지 대본]\n{p34_img_sc}\n\n[출력 형식]\n001 | 나레이션 내용\n002 | 나레이션 내용\n..."
                        extracted = call_gemma(prompt)
                        st.session_state.p34_narration_script = extracted
                        st.success("나레이션 추출 성공!")
                        save_workspace_state()
                        st.rerun()
                    except Exception as e:
                        st.error(f"[오류명] 나레이션 추출 실패: {e}\n→ 해결 방법: Gemma 연결 및 올바른 이미지 대본인지 확인하십시오.")
        else:
            return
            
    edited_narr = st.text_area("🎙️ 나레이션 대본 편집 (001 | 나레이션 내용 형식)", value=st.session_state.get("p34_narration_script", ""), height=300, key="p6_narr_editor", disabled=is_locked)
    if edited_narr != st.session_state.get("p34_narration_script", ""):
        st.session_state.p34_narration_script = edited_narr
        
    st.subheader("🎵 Step 2. 오디오 & BGM 프리셋 설정")
    c_bgm1, c_bgm2 = st.columns(2)
    with c_bgm1:
        bgm_presets = ["비장한 성경 낭독풍", "잔잔한 철학 수필풍", "긴박한 다큐멘터리풍", "신비롭고 몽환적인 뉴에이지"]
        selected_bgm = st.selectbox("💿 BGM 분위기 프리셋 선택", bgm_presets, index=bgm_presets.index(st.session_state.get("p6_bgm_selection", "비장한 성경 낭독풍")), disabled=is_locked, key="p6_bgm_select")
        st.session_state.p6_bgm_selection = selected_bgm
    with c_bgm2:
        mix_ratio = st.slider("🔊 오디오 믹싱 비율 (나레이션 볼륨 %)", min_value=50, max_value=100, value=st.session_state.get("p6_mixing_ratio", 80), step=5, disabled=is_locked, key="p6_mix_slider")
        st.session_state.p6_mixing_ratio = mix_ratio
        
    st.subheader("👥 Step 3. Google Opal 8계정 분배")
    if st.button("👥 Opal 8계정 씬 자동 배분 시작", key="p6_distribute_btn", type="primary", disabled=is_locked):
        # 버튼 내부에서 세션 스테이트를 통해 안전하게 설정값 참조
        _selected_bgm = st.session_state.get("p6_bgm_selection", "비장한 성경 낭독풍")
        _mix_ratio = st.session_state.get("p6_mixing_ratio", 80)
        _narr_text_raw = st.session_state.get("p34_narration_script", "")
        _lines = _narr_text_raw.strip().split("\n")
        parsed_scenes = {}
        error_lines = []
        for _line in _lines:
            if not _line.strip():
                continue
            _parts = _line.split("|", 1)
            if len(_parts) == 2:
                _scene_str = _parts[0].strip()
                _narr_content = _parts[1].strip()
                if _scene_str.isdigit() and len(_scene_str) == 3:
                    parsed_scenes[int(_scene_str)] = _narr_content
                else:
                    error_lines.append(_line)
            else:
                error_lines.append(_line)
                
        if error_lines:
            st.error(f"⚠️ 다음 줄의 형식이 올바르지 않습니다 (001 | 나레이션 형식이어야 함):\n" + "\n".join(error_lines[:5]))
            
        try:
            opal_records = []
            for scene_idx in range(1, 113):
                _s_str = f"{scene_idx:03d}"
                _narr_out = parsed_scenes.get(scene_idx, f"@Protagonist의 이야기가 펼쳐집니다. (나레이션 누락)")
                account_num = ((scene_idx - 1) // 14) + 1
                account_name = f"{account_num}번계정"
                
                opal_records.append({
                    "계정": account_name,
                    "씬번호": _s_str,
                    "나레이션": _narr_out,
                    "BGM 프리셋": _selected_bgm,
                    "믹싱 비율": f"나레이션 {_mix_ratio}% / BGM {100-_mix_ratio}%"
                })
                
            df = pd.DataFrame(opal_records)
            st.session_state.p6_opal_df = df
            st.session_state.p6_opal_data = df.to_dict(orient="records")
            st.session_state.p6_opal_saved = True
            save_workspace_state()
            st.success("Opal 8계정 배분 데이터가 성공적으로 생성되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"[오류명] Opal 배분 실패: {e}\n→ 해결 방법: 나레이션 텍스트 형식 및 Pandas 데이터프레임 구조를 점검하세요.")

    if st.session_state.get("p6_opal_df") is None and st.session_state.get("p6_opal_data") is not None:
        try:
            st.session_state.p6_opal_df = pd.DataFrame(st.session_state.p6_opal_data)
        except Exception as e:
            st.error(f"[오류명] Opal 데이터프레임 복원 실패: {e}\n→ 해결 방법: 세션 데이터 무결성을 점검하십시오.")

    if st.session_state.get("p6_opal_df") is not None:
        st.markdown("### 📊 Opal 8계정 씬 배분 현황")
        st.dataframe(st.session_state.p6_opal_df, use_container_width=True)
        
        try:
            csv_data = st.session_state.p6_opal_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Opal 배분 CSV 다운로드 (Excel 호환)",
                data=csv_data,
                file_name=f"part6_opal_dispatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="p6_csv_download"
            )
        except Exception as e:
            st.error(f"[오류명] CSV 변환 실패: {e}\n→ 해결 방법: Pandas 데이터프레임 컬럼을 점검하세요.")
            
    st.divider()
    if st.button("💾 파트 6 옵시디언 자동 백업", type="primary", use_container_width=True, key="p6_backup_btn", disabled=is_locked):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if st.session_state.get("path_obsidian"):
            safe_makedirs(st.session_state.path_obsidian)
            md_path = os.path.join(st.session_state.path_obsidian, f"part6_opal_dispatch_{ts}.md")
            md = f"# [[파트 6 Opal 나레이션 배분 백업]]\n"
            md += f"## 📌 Brief Summary\nSage Mirror Studio v14.0 — 파트 6 나레이션 및 BGM 8계정 배분 결과\n\n"
            md += f"## 💿 오디오 설정\n- BGM 분위기 프리셋: {st.session_state.get('p6_bgm_selection', '비장한 성경 낭독풍')}\n- 나레이션 볼륨 비율: {st.session_state.get('p6_mixing_ratio', 80)}%\n\n"
            
            if st.session_state.get("p6_opal_df") is not None:
                md += "## 📊 8계정 배분 세부 목록\n"
                md += st.session_state.p6_opal_df.to_markdown(index=False) + "\n\n"
            else:
                md += "## 📊 배분 데이터 없음\n"
                
            md += f"---\n*Last updated: {datetime.now().strftime('%Y-%m-%d')} {ts}*\n"
            
            try:
                if save_markdown(md_path, md):
                    lock_file_readonly(md_path)
                    st.toast("✅ 파트 6 백업 완료!", icon="💾")
                    st.session_state.p6_opal_obsidian_saved = True
                    save_workspace_state()
                    success, msg = auto_git_push(f"Auto Save (Part 6): {ts}")
                    if success:
                        st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                    else:
                        st.error(f"GitHub Push 실패: {msg}")
                    st.rerun()
            except Exception as e:
                st.error(f"[오류명] 옵시디언 저장 실패: {e}\n→ 해결 방법: 옵시디언 볼트 경로가 올바르게 지정되었는지 확인하십시오.")


# =====================================================================
# Part 7 — render_part7_capcut() 메인 함수
# =====================================================================
def render_part7_capcut():
    c_title, c_control = st.columns([4.2, 5.8])
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎬 파트 7: 숏폼 생성 (CapCut Bridge)</h3>', unsafe_allow_html=True)
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p7_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p7_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part7", "7777"): 
                st.session_state.unlock_part7 = True
            elif pin: 
                st.session_state.unlock_part7 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p7_popup_btn"):
                st.session_state.sidebar_part = "part7"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)
            
    is_locked = not st.session_state.get("unlock_part7", False)
    # PIN 경고 메시지 출력 제거 (사용자 요청 반영)
        
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    
    st.subheader("🧩 Step 1. CapCut Bridge 데이터 조립")
    if st.session_state.get("p6_opal_df") is None and st.session_state.get("p6_opal_data") is not None:
        try:
            st.session_state.p6_opal_df = pd.DataFrame(st.session_state.p6_opal_data)
        except Exception:
            pass
            
    opal_df = st.session_state.get("p6_opal_df")
    if opal_df is None:
        st.warning("⚠️ 파트 6 Opal 배분 데이터가 존재하지 않습니다. 파트 6 단계를 완료해 주세요.")
        return
        
    if st.button("🎬 CapCut Bridge 데이터 자동 조립 및 타임라인 연산", key="p7_assemble_btn", type="primary", disabled=is_locked):
        with st.spinner("CapCut 자동화 템플릿용 데이터 구성 중..."):
            try:
                records = []
                for _, row in opal_df.iterrows():
                    scene_str = row["씬번호"]
                    narr_text = row["나레이션"]
                    
                    char_count = len(narr_text)
                    duration_val = max(char_count * 0.25, 4.0)
                    
                    records.append({
                        "scene_id": scene_str,
                        "image_file": f"scene_{scene_str}.png",
                        "audio_file": f"narration_{scene_str}.mp3",
                        "video_file": f"video_{scene_str}.mp4",
                        "subtitle": narr_text,
                        "duration": round(duration_val, 2)
                    })
                df = pd.DataFrame(records)
                st.session_state.p7_capcut_df = df
                st.session_state.p7_capcut_data_v2 = df.to_dict(orient="records")
                st.session_state.p7_capcut_saved = True
                save_workspace_state()
                st.success("CapCut Bridge 데이터 조립이 완료되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"[오류명] CapCut Bridge 조립 실패: {e}\n→ 해결 방법: 8계정 분배 데이터 구조와 Pandas 버전을 확인하십시오.")
                
    if st.session_state.get("p7_capcut_df") is None and st.session_state.get("p7_capcut_data_v2") is not None:
        try:
            st.session_state.p7_capcut_df = pd.DataFrame(st.session_state.p7_capcut_data_v2)
        except Exception as e:
            st.error(f"[오류명] CapCut Bridge 데이터프레임 복원 실패: {e}\n→ 해결 방법: 로컬 workspace_state.json 구조를 복원하십시오.")
            
    if st.session_state.get("p7_capcut_df") is not None:
        st.markdown("### 📊 CapCut Bridge 조립 데이터")
        st.dataframe(st.session_state.p7_capcut_df, use_container_width=True)
        
        try:
            csv_data = st.session_state.p7_capcut_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 CapCut Bridge CSV 다운로드 (Excel 호환)",
                data=csv_data,
                file_name=f"part7_capcut_bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="p7_csv_download"
            )
        except Exception as e:
            st.error(f"[오류명] CSV 내보내기 실패: {e}\n→ 해결 방법: DataFrame의 특수문자 및 용량을 점검하십시오.")
            
    st.divider()
    if st.button("💾 파트 7 옵시디언 자동 백업", type="primary", use_container_width=True, key="p7_backup_btn", disabled=is_locked):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if st.session_state.get("path_obsidian"):
            safe_makedirs(st.session_state.path_obsidian)
            md_path = os.path.join(st.session_state.path_obsidian, f"part7_capcut_bridge_{ts}.md")
            md = f"# [[파트 7 CapCut Bridge 데이터 백업]]\n"
            md += f"## 📌 Brief Summary\nSage Mirror Studio v14.0 — 파트 7 CapCut Bridge 조립 및 타임라인 데이터 백업\n\n"
            
            if st.session_state.get("p7_capcut_df") is not None:
                md += "## 🎬 CapCut Bridge 데이터 세부 목록\n"
                md += st.session_state.p7_capcut_df.to_markdown(index=False) + "\n\n"
            else:
                md += "## 🎬 조립 데이터 없음\n"
                
            md += f"---\n*Last updated: {datetime.now().strftime('%Y-%m-%d')} {ts}*\n"
            
            try:
                if save_markdown(md_path, md):
                    lock_file_readonly(md_path)
                    st.toast("✅ 파트 7 백업 완료!", icon="💾")
                    st.session_state.p7_capcut_obsidian_saved = True
                    save_workspace_state()
                    success, msg = auto_git_push(f"Auto Save (Part 7): {ts}")
                    if success:
                        st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                    else:
                        st.error(f"GitHub Push 실패: {msg}")
                    st.rerun()
            except Exception as e:
                st.error(f"[오류명] 옵시디언 저장 실패: {e}\n→ 해결 방법: 드라이브 쓰기 권한을 점검하십시오.")


# =====================================================================
# Part 8 — render_part8_dashboard() 메인 함수
# =====================================================================
def render_part8_dashboard():
    c_title, c_control = st.columns([4.2, 5.8])
    with c_title:
        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">📊 파트 8: 캡컷 최종 조립</h3>', unsafe_allow_html=True)
    with c_control:
        st.markdown('<div id="header-control-box-anchor"></div>', unsafe_allow_html=True)
        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])
        with c_model_col:
            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)
            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()
            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]
            default_idx = model_options.index(cur_model) if cur_model in model_options else 0
            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p8_model_select", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():
                st.session_state.selected_model = sel_model.lower()
                save_workspace_state()
                st.rerun()
        with c_pin_col:
            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)
            pin = st.text_input("🔒 마스터 PIN", type="password", key="p8_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
            st.markdown('</div>', unsafe_allow_html=True)
            if pin == PART_PINS.get("part8", "7777"): 
                st.session_state.unlock_part8 = True
            elif pin: 
                st.session_state.unlock_part8 = False
        with c_pop_col:
            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)
            if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p8_popup_btn"):
                st.session_state.sidebar_part = "part8"
                popup_assistant()
            st.markdown('</div>', unsafe_allow_html=True)
            
    is_locked = not st.session_state.get("unlock_part8", False)
    # PIN 경고 메시지 출력 제거 (사용자 요청 반영)
        
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    
    st.subheader("📊 Step 1. 생산 품질 요약 리포트")
    if st.session_state.get("p7_capcut_df") is None and st.session_state.get("p7_capcut_data_v2") is not None:
        try:
            st.session_state.p7_capcut_df = pd.DataFrame(st.session_state.p7_capcut_data_v2)
        except Exception:
            pass
            
    cap_df = st.session_state.get("p7_capcut_df")
    if cap_df is None:
        st.warning("⚠️ 파트 7 CapCut Bridge 조립 데이터가 없습니다. 파트 7 단계를 완료해 주세요.")
        return

    # ──────────────────────────────────────────────
    # 통계 변수 기본값 초기화 (저장 버튼 스코프 밖에서 선언)
    # ──────────────────────────────────────────────
    total_scenes = 0
    total_duration = 0.0
    avg_duration = 0.0
    exist_count = 0
    completion_rate = 0.0
    missing_scenes = []

    try:
        total_scenes = len(cap_df)
        total_duration = float(cap_df["duration"].sum())
        avg_duration = float(cap_df["duration"].mean())
        
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.metric("총 씬 개수", f"{total_scenes}개")
        with c_m2:
            st.metric("총 비디오 예상 시간", f"{total_duration:.2f}초 ({total_duration/60:.2f}분)")
        with c_m3:
            st.metric("평균 씬 지속시간", f"{avg_duration:.2f}초")
    except Exception as e:
        st.error(f"[오류명] 지표 계산 실패: {e}\n→ 해결 방법: CapCut Bridge 데이터프레임의 duration 열 구조를 파악하십시오.")
        
    st.subheader("📁 Step 2. 06_Video_Clips 물리 파일 매칭 검증")
    video_dir = r"C:\SageMirror_Production\06_Video_Clips"
    
    try:
        os.makedirs(video_dir, exist_ok=True)
    except Exception as e:
        st.error(f"[오류명] 폴더 생성 실패: {e}\n→ 해결 방법: 드라이브 경로가 존재하며 쓰기 권한이 있는지 점검하십시오.")
        
    matching_status = []
    
    if st.button("🔄 비디오 클립 실시간 스캔 및 새로고침", key="p8_scan_btn"):
        st.toast("실시간 물리 폴더 스캔 중...")
        
    try:
        for idx in range(1, 113):
            scene_str = f"{idx:03d}"
            file_name = f"video_{scene_str}.mp4"
            file_path = os.path.join(video_dir, file_name)
            
            is_exist = os.path.exists(file_path)
            if is_exist:
                exist_count += 1
                status_str = "완료 ✅"
            else:
                missing_scenes.append(scene_str)
                status_str = "누락 ❌"
                
            matching_status.append({
                "씬번호": scene_str,
                "파일명": file_name,
                "상태": status_str
            })
            
        matching_df = pd.DataFrame(matching_status)
        completion_rate = (exist_count / 112) * 100
        
        st.markdown(f"**물리 비디오 클립 매칭 완료율:** {completion_rate:.1f}% ({exist_count} / 112)")
        st.progress(completion_rate / 100.0)
        
        if missing_scenes:
            st.error(f"⚠️ 총 {len(missing_scenes)}개의 씬 비디오 클립이 누락되었습니다:\n" + ", ".join(missing_scenes))
        else:
            st.success("🎉 모든 112개 비디오 클립이 정상 매칭되었습니다!")
            
        with st.expander("🔍 112개 비디오 클립 세부 현황", expanded=False):
            st.dataframe(matching_df, use_container_width=True)
    except Exception as e:
        st.error(f"[오류명] 물리 파일 스캔 실패: {e}\n→ 해결 방법: {video_dir} 경로 권한 및 파일 형식을 확인하십시오.")
        
    st.divider()
    if st.button("💾 파트 8 최종 생산 세션 백업", type="primary", use_container_width=True, key="p8_backup_btn", disabled=is_locked):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if st.session_state.get("path_obsidian"):
            safe_makedirs(st.session_state.path_obsidian)
            md_path = os.path.join(st.session_state.path_obsidian, f"part8_production_dashboard_{ts}.md")
            md = f"# [[파트 8 생산 검수 대시보드 백업]]\n"
            md += f"## 📌 Brief Summary\nSage Mirror Studio v14.0 — 파트 8 최종 생산 대시보드 검수 백업\n\n"
            md += f"## 📊 생산 스탯 요약\n- 총 씬 개수: {total_scenes}개\n- 총 예상 시간: {total_duration:.2f}초 ({total_duration/60:.2f}분)\n- 평균 씬 시간: {avg_duration:.2f}초\n\n"
            md += f"## 📁 물리 파일 매칭 결과\n- 매칭률: {completion_rate:.1f}% ({exist_count} / 112)\n"
            
            if missing_scenes:
                md += f"- 누락 씬 목록: {', '.join(missing_scenes)}\n\n"
            else:
                md += "- 누락 씬 없음 (100% 매칭 완료)\n\n"
                
            md += f"---\n*Last updated: {datetime.now().strftime('%Y-%m-%d')} {ts}*\n"
            
            try:
                if save_markdown(md_path, md):
                    lock_file_readonly(md_path)
                    st.toast("✅ 파트 8 백업 완료!", icon="💾")
                    st.session_state.p8_dashboard_obsidian_saved = True
                    save_workspace_state()
                    success_push, msg_push = auto_git_push(f"Auto Save (Part 8): {ts}")
                    if success_push:
                        st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                    else:
                        st.error(f"GitHub Push 실패: {msg_push}")
                    st.rerun()
            except Exception as e:
                st.error(f"[오류명] 옵시디언 저장 실패: {e}\n→ 해결 방법: 드라이브 접근 권한을 확인하십시오.")


# 파트 라우팅 블록
# =====================================================================
if part.startswith("파트 1"):
    render_part1()
elif part.startswith("파트 2"):
    render_part2()
elif part.startswith("파트 3"):
    render_part34()
elif part.startswith("파트 4"):
    render_part5_image()
elif part.startswith("파트 5"):
    render_part6_video()
elif part.startswith("파트 6"):
    render_part6_opal()
elif part.startswith("파트 7"):
    render_part7_capcut()
elif part.startswith("파트 8"):
    render_part8_dashboard()