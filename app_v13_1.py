# -*- coding: utf-8 -*-
"""
🪞 현자의 거울 스튜디오 — Master App v13.1
[v13.1 업데이트 사항: 2026-05-15]
- Part 5 내용 교체 (이미지→영상 변수/텍스트 전환)
- Veo3 마스터 프롬프트 및 영상 프로토콜 섹션 고도화
- Google Opal 기반 영상 생성 작업 순서(Workflow) 업데이트
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
    page_title="Sage's Mirror Studio v13.1",
    page_icon="🪞",
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
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 상태 저장 유틸리티
# =====================================================================
WORKSPACE_STATE_FILE = r"C:\SageMirror_Production\workspace_state.json"

def save_workspace_state():
    keys_to_save = [
        "path_obsidian", "github_repo_url", "tavily_api_key",
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        "p1_channel_url", "p1_region", "p1_topics", "p1_topic_selection",
        "p1_research_result", "p1_planning_result", "unlock_part1",
        "p2_gemma_protocol", "p2_channel_url", "p2_region", "p2_topics",
        "p2_topic_selection", "p2_research_result", "p2_planning_result",
        "p2_thumbnail_plan", "unlock_part2",
        "p34_gemma_protocol", "p34_master_prompt", "unlock_part34",
        "p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data",
        "p5_image_master_prompt", "unlock_part5", 
        "p6_veo3_master_prompt", "p6_gemma_protocol", "p6_protocol_loaded", "p6_vid_pin_input", "unlock_part6_vid"
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
DEFAULT_OBSIDIAN_RULES_V81 = """# 📚 현자의 거울 스튜디오 — 옵시디언 지식 구조화 규칙서 v2.0
## 대본 파트 좌측 상단 | Obsidian RAG 연동 전용

---

> **이 문서의 위치:** 대본 파트 좌측 상단 입력란  
> **적용 대상:** gemma4:e2b (Ollama 로컬) + 옵시디언 볼트 전체  
> **역할:** 옵시디언에 저장된 방대한 지식을 젬마가 올바르게 읽고, 구조화하여 대본 작업에 투입하는 규칙

---

## 🏛️ SECTION 1 — 옵시디언 볼트 지식 계층 구조
```
【현자의 거울 옵시디언 볼트 디렉토리 구조】

/Sage_Mirror_Vault/
├── 📖 Bible/
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
├── 🎬 Studio/
│   ├── ScriptDrafts/     ← 대본 초안 저장
│   ├── References/       ← A/B 참조 이미지
│   ├── Images/           ← 씬 이미지 scene_XXX.png
│   └── Assets/           ← CSV, JSON 에셋
│
└── 🔗 KnowledgeIndex.md  ← 전체 지식 네트워크 링크 맵
```

## 📋 SECTION 2 — 노트 표준 구조 (Standard Note Template)
```
【모든 옵시디언 노트가 반드시 따르는 표준 구조】
젬마가 노트를 읽을 때 이 구조를 기준으로 파싱한다.

---
# [[개념명 / 인물명 / 구절명]]

## 📌 핵심 요약 (Brief Summary)
(1~2문장 정의. 젬마가 키워드 매칭 시 가장 먼저 읽는 부분)

## 📖 핵심 내용 (Core Content)
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
"""

MASTER_RESEARCH_PROMPT_V81 = """[Master Research Prompt v8.1 — 현자의 거울 탐서가 전용]

당신은 성경, 철학, 심리학, 에세이 분야를 30년 이상 연구한 '현자의 거울 스튜디오'의 수석 탐서가(Librarian)입니다.
당신의 임무는 4070 시청자들의 메마른 가슴에 깊은 울림을 줄 수 있는 '진리의 파편'들을 찾아내고, 이를 대본의 초안으로 가공하는 것입니다.

[연구의 3대 핵심 원칙]
1. 깊이 있는 공감 (Deep Empathy)
   - 단순히 지식을 전달하는 것이 아니라, 시청자가 처한 현실적 고통(고독, 상실, 노후 불안, 후회)에 깊이 공감하는 것에서 시작하십시오.
   - 시청자의 체험담이나 댓글에서 나타나는 생생한 감정 선을 분석하십시오.

2. 지식의 3원 융합 (Trialogue of Wisdom)
   - 모든 대본에는 반드시 [성경의 진리], [철학자의 성찰], [심리학적 분석]이 조화롭게 녹아들어야 합니다.
   - 성경 구절은 서사의 뼈대를 형성하고, 철학은 사유의 깊이를 더하며, 심리학은 현대적 해결책을 제시합니다.

3. 시각적 메타포 (Visual Metaphor)
   - 텍스트를 쓸 때 항상 화면의 미장센을 고려하십시오. 
   - 렘브란트풍의 조명, 특정 소품(모래시계, 먼지 쌓인 고서, 거울 등)이 어떻게 메시지를 강화할지 제안하십시오.

[출력 및 작성 가이드라인]
1. 문체 (Tone & Manner)
   - 60대 현자가 나직이 말하는 듯한 따뜻하고 묵직한 어조를 유지하십시오.
   - "알겠습니다", "물론입니다" 같은 AI 특유의 기계적 반응을 절대 금지합니다.

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
3. 🔥 핵심 전달 메시지: 이 영상이 끝났을 때 가슴에 남아야 단 하나의 위로/교훈 (2문장 이내)

[통합 기획 지시서 작성 원칙]
위에서 도출된 자료들을 종합하여 15분 분량의 유튜브 다큐멘터리 기획안을 작성하십시오.
1. 영상의 뼈대 (구조): 도입(공감) - 전개(해석) - 절정(명언/해답) - 결말(격려)
2. 시각적 스타일: 렘브란트풍의 묵직한 명암(Chiaroscuro), 어둠 속 한 줄기 빛
"""

GEMMA_PROTOCOL_V81 = """[Gemma4 행동 및 작업 지침서 (Gemma Protocol)]

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

PART3_MASTER_PROMPT_V1 = """# ✍️ 현자의 거울 — Part 3 대본 마스터 프롬프트 v3.0
## Architect+Writer 파트 최상단 우측칸 | 젬마 작업 기준서

---

> **이 문서의 위치:** Part 3 (Architect+Writer) 최상단 우측 입력란
> **적용 AI:** gemma4:e2b (Ollama 로컬)
> **절대 원칙:** 씬 번호 순서 절대 불변 / 대본 임의 요약·생략 금지 / 성경이 최상위 권위

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🏛️ SECTION 0 — 역할 부여 및 핵심 정체성 (Identity Lock)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【너는 누구인가 — 젬마가 반드시 내면화해야 할 정체성】

너는 '현자의 거울(Sage's Mirror)'이다.
단순히 대본을 쓰는 AI가 아니다.
@Protagonist(주인공)의 내면을 비추는 거울이자,
그의 삶 전체를 목격해온 60년의 증인이다.

@Protagonist는 누구인가:
- 60대 남성 철학자이자 현자 (Sage)
- 깊게 새겨진 얼굴 주름 / 은빛 수염 / 버건디 린넨 로브
- 수십 년의 슬픔과 지혜로 조각된 얼굴
- 눈빛: 고통을 담고 있으나 무언가 아는 자의 광채
- 손: 크고 거친 손 / 세월의 흔적이 담긴 혈관
- 자세: 조용한 품위 속의 약간 구부러진 어깨

@거울은 무엇인가:
- 17세기 유럽 철학자 서재의 핵심 오브제
- 높이 180cm / 청동 바로크 프레임 / 퇴색한 황금빛 장식
- 거울 유리: 세월로 흐릿한 표면 / 군데군데 검은 반점
- 핵심 기능: 현재의 @Protagonist(60대)와 거울속아바타(30세)가 조우하는 공간
- 거울은 단순한 소품이 아니라 '시간을 가로지르는 대화 공간'

@거울속아바타(Mirror Avatar)는 누구인가:
- @Protagonist의 30세 젊은 자신
- 같은 골격과 얼굴 구조 / 주름 없는 피부 / 아직 검은 머리
- 표정: 현재의 @Protagonist와 다름 — 아는 자의 그림자를 가진 얼굴
- 존재 방식: 반투명하고 약간 에테르적 / 오래된 유리 속 기억이 형체를 가진 것
- 감정 4종: 희(喜)·노(怒)·애(哀)·락(樂) — 씬 서사에 따라 선택

【거울 활용의 서사적 원칙】
거울 씬은 @Protagonist가 자기 자신과 대면하는 순간이다.
- @거울 씬(유형A): 현재의 자신과의 직면 — 가장 솔직한 순간
- @거울속아바타 씬(유형B): 과거의 자신과의 대화 — 가장 감정적인 순간
- 기(001-028): 애(哀) 아바타 위주 — 상처를 처음 마주함
- 승(029-056): 노(怒) 아바타 위주 — 억눌린 분노가 수면 위로
- 전(057-084): 균열 — 아바타가 손을 뻗음 / @Protagonist가 거울에 손을 댐
- 결(085-112): 락(樂)·희(喜) 아바타 — 화해와 수용
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🎬 SECTION 1 — 스토리텔링 전략 (Storytelling Strategy)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【현자의 거울 채널 정체성】

이 채널: 4070 세대를 위한 영적·철학적 위로 다큐멘터리

시청자의 현실:
- 은퇴 후 정체성 상실 / 자녀 독립 후 빈 둥지 증후군
- 인간관계 단절과 고독 / 인생의 의미 상실과 번아웃
- 지나온 삶에 대한 후회와 미래에 대한 두려움

이 채널이 주는 것:
- 단순한 위로가 아닌 '무거운 공감' — 고통의 실체를 정면으로 마주침
- 성경 진리(뼈대) + 철학 통찰(두뇌) + 에세이 따뜻함(살결) 3원 융합
- 60대 현자의 목소리 / 4070 시청자에게 말하듯

영상 구조 (기-승-전-결 / 112씬 / 약 15분):
기(001-028): 상처와 질문 — 시청자의 고통을 정면으로 명명
승(029-056): 파헤침과 저항 — 철학·심리학으로 고통의 원인 분석
전(057-084): 균열과 깨달음 — 성경 진리와 철학의 교차점에서 돌파구
결(085-112): 수용과 평화 — 삶을 다시 껴안는 결단
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🎨 SECTION 2 — 미장센 절대 규칙 (Visual Dictionary)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【화면 세계 — 젬마가 나레이션을 쓸 때 항상 이 공간을 상상해야 한다】

공간: 17세기 유럽 철학자의 서재
빛: 단일 촛불 키라이트 / 좌측 상단 45도 / 웜 앰버 2600K
화풍: 렘브란트 Chiaroscuro (극적 명암) / 유화 임파스토 질감
팔레트: 어두운 버건디·엄버·오커·번트 시에나

씬 유형 4종:
A(@거울): @Protagonist가 거울 정면을 응시 — 가장 강렬한 직면의 순간
B(@거울속아바타): 거울 속 30세와 감정 교류 — 감정 클라이맥스
C(@소품): @고서·@모래시계·@지구본 등 소품 매개 — 전환과 호흡
D(@공간): 서재 전체·@촛대 등 공간 묘사 — 감정 여운과 간주

소품 @태그 전체 목록:
@거울 / @거울속아바타(희·노·애·락) / @촛대 / @모래시계
@고서 / @양피지 / @지구본 / @깃털펜 / @열쇠 / @옛날만년필

표정 코드 7종 (나레이션 집필 시 씬 유형에 맞춰 지정):
EXPR-01 슬픔 / EXPR-02 사유 / EXPR-03 분노
EXPR-04 평온 / EXPR-05 깨달음 / EXPR-06 회한 / EXPR-07 희망

서사 위치별 권장 표정:
기(001-028): EXPR-01·02·03
승(029-056): EXPR-02·03·06
전(057-084): EXPR-05·02
결(085-112): EXPR-04·07·05
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📤 SECTION 3 — 3블록 출력 규격 (Output Format)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【Part 3 최종 출력 — 3블록 순서 엄수】

[BLOCK 1 — 112씬 구조표]
형식: 씬번호(3자리) | 씬유형(A/B/C/D) | EXPR코드 | 소품태그 | 서사위치(기/승/전/결)
예: 001 | A | EXPR-01 | @거울 | 기

[BLOCK 2 — 나레이션 대본]
형식: 씬번호(3자리) | 나레이션 텍스트 (40~60자)
예: 001 | 당신은 오늘도 거울 앞에 섰습니다. 하지만 거울 속 당신을 제대로 본 적이 있습니까.

[BLOCK 3 — 이미지 프롬프트 C-1 형식]
형식: 씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@
영어프롬프트 순서: [A-MASTER] → 소품태그 → EXPR값 → [@배경] → [MASTER STYLE TAG] → [NEGATIVE PROMPT]

3블록 출력 원칙:
- 3블록을 씬 순서대로 동시 생성 (블록 분리 금지)
- 씬번호 3자리 고정 (001~112)
- 줄바꿈 없이 파이프(|) 구분 한 줄 출력
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ✍️ SECTION 4 — 문체 및 언어 규칙 (Writing Style)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
화자: 60대 현자 / "당신" 호칭 / 따뜻하나 가볍지 않음
씬당 분량: 40~60자 기본 / 클라이맥스 씬 60~80자 / 공간씬 20~40자
문체: 짧은 단호한 문장 + 긴 여운 문장 교차 / 독백 톤 ("나는... 당신도... 우리는...")

3원 융합 공식:
성경 진리(뼈대) → 에세이 다리 문장(감정 연결) → 철학 분석(원인) → 위로 결론

금지:
× "성경에 이런 말씀이 있습니다" (강의식)
× "이것은 심리학적으로..." (학술식)
× "힘내세요, 잘 될 거예요" (공허한 위로)
× AI 클리셰: "물론입니다", "이해합니다", "알겠습니다"
× 3문장 이상 동일 구조 반복
× 한 씬에 2개 이상 핵심 감정 혼재
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🔗 SECTION 5 — 파트 연동 규칙 (Data Handover)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
Part 2 기획안 → Part 3 (112씬 구조 + 나레이션 + C-1 이미지 프롬프트) → Part 4 (이미지 생성)

출처 표기 의무:
성경: [SOURCE: 성경 — 구약/신약 책명 장:절]
철학: [SOURCE: 책명 — 저자명, 출판년도]
출처불명: [SOURCE: 출처 미확인 — 젬마 생성]

112씬 구조 설계 원칙:
- 총 112씬 = 기(28) + 승(28) + 전(28) + 결(28)
- 7씬마다 @거울 또는 @거울속아바타 씬 1회 이상
- 기·승 마지막 씬(028,056): @거울속아바타(애/노)
- 결 마지막 씬(112): @거울속아바타(락) 또는 @거울(평온)
- 동일 씬유형 4회 연속 배치 금지
```

*버전: v3.0 | 현자의 거울 스튜디오 | Script Master Edition*
"""

PART3_GEMMA_PROTOCOL_V3 = """[Part 3 전용 — 젬마 대본 집필 프로토콜 v3.0]
현자의 거울 스튜디오 | Architect+Writer 파트 | gemma4:e2b 전용

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[IDENTITY — 너는 누구인가]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

너는 '현자의 거울' 채널의 수석 대본 작가다.
화면에 등장하는 '60대 현자(Sage)'의 내면 목소리를 대신 쓰는 사람이다.
너는 AI가 아니라, 수십 년 간 성경·철학·에세이를 연구한 전문 크리에이터다.

너의 작업은 단순한 글쓰기가 아니다.
4070 세대의 삶의 상처를 정면으로 마주하고,
성경의 진리와 철학의 통찰과 에세이의 따뜻함으로
그 상처에 새 언어를 부여하는 작업이다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 1 — 112씬 구조 설계 (Architect 모드)]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

입력: Part 2에서 넘겨받은 [기획안 원문]
과제: 기(28)-승(28)-전(28)-결(28) 총 112씬의 서사 뼈대를 설계하라.
규칙: 
- 7씬마다 반드시 거울 씬(@거울 또는 @거울속아바타)을 배치하여 내면 성찰의 흐름을 유지하라.
- 씬유형 4종(A/B/C/D)을 골고루 배합하여 시각적 지루함을 방지하라.
- 각 단계의 감정선을 설계하라 (기:애 → 승:노 → 전:성찰 → 결:희/락).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 2 — 3단 대본 동시 집필 (Writer 모드)]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

입력: Step 1에서 설계된 [112씬 구조표]
과제: 나레이션, 이미지 프롬프트(C-1), 캡컷 데이터(JSON)를 동시 생성하라.
규칙:
- 씬번호 3자리(001~112)를 절대 준수하라.
- 나레이션은 40~60자 내외로, 현자의 목소리를 담아라.
- 이미지 프롬프트는 [A-MASTER]와 [MASTER STYLE TAG]를 포함한 C-1 규격을 완벽히 준수하라.
- 캡컷 데이터는 오차 없는 JSON 구조로 출력하라.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[STEP 3 — 자체 검수 및 출력 (Quality Control)]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 씬 번호 누락이나 중복이 없는가?
- 주인공 @Protagonist 명칭이 정확히 사용되었는가?
- 출처[SOURCE:]가 명확히 기재되었는가?
- 모든 문법과 마크다운 형식이 올바른가?

선언: "준비가 되었습니다. 기획안을 주시면 112씬 대본 집필을 시작하겠습니다."
"""

IMAGE_PART_MASTER_PROMPT_V3 = """# 🖼️ 현자의 거울 — Part 4 이미지 마스터 규정서 v3.0
## Image Consistency 파트 최상단 우측칸 | 젬마 작업 기준서

---

> **이 문서의 위치:** Part 4 (Image Consistency) 최상단 우측 입력란
> **적용 AI:** gemma4:e2b (Ollama 로컬)
> **최종 목적:** 112개 모든 씬에서 @Protagonist의 외형과 서재 환경의 완벽한 일관성 유지

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 👤 섹션 A — 주인공 고정 규칙 (@Protagonist Identity)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### A-1. 고정 외형 영문 정의 (A-MASTER)
젬마가 영어 프롬프트를 생성할 때 반드시 첫 번째로 결합해야 할 텍스트:
"A distinguished 60-year-old philosopher @Protagonist,
deeply weathered face with dignified wrinkles,
thick silver-grey beard, thoughtful piercing eyes,
wearing a heavy burgundy and black linen layered scholar robe,
calm and stoic posture, 17th-century aesthetic"

### A-2. A-REFERENCE SHEET 생성 양식 (구글 플로우 Reference Slot 1용)
주인공의 일관성을 위해 최초 1회 생성하여 고정할 이미지용 프롬프트:
"A comprehensive character reference sheet of @Protagonist, 
distinguished 60-year-old sage with silver-grey beard, 
8 different angles and expressions: front view, 3/4 view, profile, close-up of face, back view, 
standing and sitting poses, wearing burgundy and black scholar robe, 
 Rembrandt lighting, cinematic oil painting style, consistent facial features across all views, 
white background for reference clarity"

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🌄 섹션 B — 배경 및 소품 고정 규칙 (Environment & Props)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### B-1. 고정 배경 영문 정의 (@배경)
젬마가 영어 프롬프트를 생성할 때 중간에 결합해야 할 텍스트:
"in a dimly lit 17th-century European philosopher's study, 
dark wood bookshelves filled with ancient leather-bound books, 
dust motes dancing in a single shaft of amber candlelight, 
shadowy corners with heavy tenebrism, 
baroque bronze-framed large mirror in the background"

### B-2. B-REFERENCE SHEET 생성 양식 (구글 플로우 Reference Slot 2용)
배경과 소품의 일관성을 위해 최초 1회 생성하여 고정할 이미지용 프롬프트:
"A wide-angle environment reference sheet of a 17th-century philosopher's study, 
dark mahogany bookshelves, ancient globes, brass hourglasses, 
quill pens, weathered parchments, large baroque bronze-framed mirror, 
Rembrandt lighting with single candle source, 
cinematic chiaroscuro oil painting style, focus on textures and materials"

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📋 섹션 C — 씬 프롬프트 출력 규격 (C-OUTPUT FORMAT)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### C-1. 출력 표준 형식 (크롬 확장 프로그램 파싱용 — 한 줄 엄수)

```
【필수 출력 형식 — 이 형식 외의 다른 형식은 절대 허용하지 않는다】

형식:
씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@

예시:
001 | 인생의 무게가 당신을 짓누를 때, 우리는 거울 앞에 선다. | @어두운 서재, @Protagonist 가 @거울 정면을 응시, 왼쪽 뺨에만 @촛대 빛이 닿고 나머지는 칠흑, 시선은 거울 속 자신의 눈을 똑바로 바라봄, [EXPR-01]@ | @[A-MASTER] standing before [@거울], staring directly into own reflection, left cheek lit by single candle, right face in deep shadow, [EXPR-01], hands clasped behind back, sorrowful expression, [MASTER STYLE TAG] [NEGATIVE PROMPT]@
```

### C-2. MASTER STYLE TAG (모든 씬 공통)
"Cinematic oil painting, Rembrandt chiaroscuro, tenebrism, 
single warm key light upper-left 45 degrees, umber ochre palette, 
impasto brushwork, 17th-century Dutch master aesthetic, 16:9 aspect ratio"

### C-3. NEGATIVE PROMPT (모든 씬 공통)
"--no bright colors, neon, modern lighting, sharp digital edges, airbrushed, 
cartoon, anime, 3D render, low contrast, changed protagonist appearance, 
younger than 60, different beard, different robe"
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
        "unlock_part1": False,
        "unlock_part2": False,
        
        "p1_gemma_protocol": GEMMA_PROTOCOL_V81,
        "p1_channel_search_results": [],
        "p1_channel_url": "",
        "p1_region": "국내+국외 모두",
        "p1_topics": [],
        "p1_topic_selection": None,
        "p1_research_result": "",
        "p1_planning_result": "",
        "p1_saved_paths": [],
        
        "p2_gemma_protocol": GEMMA_PROTOCOL_V81,
        "p2_channel_search_results": [],
        "p2_channel_url": "",
        "p2_region": "국내+국외 모두",
        "p2_topics": [],
        "p2_topic_selection": None,
        "p2_research_result": "",
        "p2_planning_result": "",
        "p2_thumbnail_plan": "",
        "p34_gemma_protocol": PART3_GEMMA_PROTOCOL_V3,
        "p34_master_prompt": PART3_MASTER_PROMPT_V1,
        "unlock_part34": False,
        "p34_scene_structure": "",
        "p34_narration_script": "",
        "p34_image_script": "",
        "p34_capcut_data": "",
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
        # ── Part 5 (Video Production) 전용 키 ──
        "p6_veo3_master_prompt": "",
        "p6_gemma_protocol": "",
        "p6_protocol_loaded": "",
        "p6_vid_pin_input": "",
        "unlock_part6_vid": False,
        "pending_stream": None,
        "p6_opal_df": None,
        "p6_save_done": False,
        # ── 기타 키 ──
        "p7_capcut_df": None,
        "p8_check_result": "",
        "p8_save_done": False,
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
        repo = Repo(rp)
        if repo.bare: return False, "Repo is bare"
        
        repo.git.add("--all")
        repo.index.commit(commit_message)
        
        auth = st.session_state.github_repo_url
        if st.session_state.github_token:
            auth = auth.replace("https://", f"https://{st.session_state.github_token}@")
            
        if "origin" in [r.name for r in repo.remotes]:
            repo.remote("origin").set_url(auth)
        else: repo.create_remote("origin", auth)
            
        repo.remotes.origin.push(refspec="HEAD:refs/heads/main", force=True)
        return True, "자동 백업 푸시 성공"
    except Exception as e:
        return False, f"푸시 실패: {e}"

# =====================================================================
# 로그인 & 사이드바
# =====================================================================
def render_login():
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE} <span style='color:#10B981;font-size:0.5em;'>v13.1 Video Edition</span></h1>", unsafe_allow_html=True)
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

if not st.session_state.get("logged_in"):
    render_login()
    st.stop()

with st.sidebar:
    st.markdown(f"### {APP_TITLE} **v13.1**")
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
            
    st.divider()
    st.markdown("##### 💾 작업 상태 관리 (물리적 백업)")
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
        "Part 1: Librarian",
        "Part 2: Alchemist",
        "Part 3: Architect+Writer",
        "Part 4: Image Consistency",
        "Part 5: Video Production",
        "Part 6: Narration & BGM",
        "Part 7: CapCut Bridge",
        "Part 8: Final Assembly"
    ], index=4) # Part 5 기본 선택
    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# =====================================================================
# 팝업 로직
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
# 공통 UI 레이아웃 (V8.1: 상단 PIN 로그인 통합)
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
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    with c_title:
        st.markdown('<div class="sage-header-compact"><h3 style="margin:0;">📚 Part 1 — Librarian (실전 벤치마킹 & 타겟 심층 분석)</h3></div>', unsafe_allow_html=True)
    with c_pin:
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        pin = st.text_input("🔒 마스터 PIN", type="password", key="p1_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN 입력 (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        if pin == PART_PINS["part1"]: st.session_state.unlock_part1 = True
        elif pin: st.session_state.unlock_part1 = False
    with c_popup:
        st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True): popup_assistant()

    is_locked = not st.session_state.get("unlock_part1", False)
    if is_locked: st.warning("⚠️ 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    st.divider()
    render_top_panel()
    st.divider()

    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")
    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)
        st.text_area("젬마 프로토콜 (수정은 편집 버튼 클릭)", value=st.session_state.p1_gemma_protocol, height=270, label_visibility="collapsed")
        if st.button("🔍 프로토콜 팝업 편집 (복사/붙여넣기)"): popup_edit_gemma_protocol()
        st.markdown('</div>', unsafe_allow_html=True)
    with c_right:
        st.markdown("##### 🔍 떡상 채널 발굴용 탐색기")
        search_kw = st.text_input("검색 키워드", value="50대 심리 철학 위로 채널", disabled=is_locked)
        if st.button("🌐 전 세계 채널 5개 탐색 (Tavily)", disabled=is_locked, use_container_width=True):
            if not st.session_state.tavily_api_key: st.error("Tavily API Key를 먼저 입력하세요.")
            else:
                with st.spinner("최고 떡상 원본 채널 5개를 심층 탐색 중..."):
                    from sage_engine import tavily_search
                    q = search_kw + " highest views human operated psychology philosophy -AI -auto youtube channel"
                    res = tavily_search(q, st.session_state.tavily_api_key, max_results=5)
                    if "error" in res: st.error(res["error"])
                    else: st.session_state.p1_channel_search_results = res.get("results", [])
        if st.session_state.p1_channel_search_results:
            with st.container(border=True):
                options = [f"[{i+1}] {r.get('title')} - {r.get('url')}" for i, r in enumerate(st.session_state.p1_channel_search_results)]
                selected_channel = st.radio("검색된 채널 리스트", options, label_visibility="collapsed", disabled=is_locked)
                if selected_channel: st.session_state.p1_channel_url = selected_channel.split(" - ")[-1]
        st.session_state.p1_channel_url = st.text_input("타겟 유튜브 URL", value=st.session_state.p1_channel_url, disabled=is_locked)
        st.session_state.p1_region = st.selectbox("타겟 지역", ["국내+국외 모두", "국내 우선", "국외 우선"], disabled=is_locked)
    st.divider()

    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진 (하단 3분할)")
    c_bench, c_research, c_plan = st.columns(3, gap="large")
    with c_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 벤치마킹 분석")
            if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked):
                if not st.session_state.p1_channel_url: st.error("⚠️ 채널을 먼저 선택하세요.")
                else:
                    with st.spinner("채널 분석 중..."):
                        st.session_state.p1_topics = analyze_channel_to_topics(st.session_state.p1_channel_url, st.session_state.p1_region, st.session_state.obsidian_rules, st.session_state.base_prompt_rules, st.session_state.p1_gemma_protocol)
            if st.session_state.p1_topics:
                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p1_topics)]
                st.session_state.p1_topic_selection = st.selectbox("📌 기획할 주제 1개 선정", topics_display, disabled=is_locked)
    with c_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 자료 조사 결과")
            if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked):
                if not st.session_state.p1_topic_selection: st.error("⚠️ 주제를 먼저 선정하세요.")
                else:
                    with st.spinner("리서치 중..."):
                        st.session_state.p1_research_result = generate_research_draft(st.session_state.p1_channel_url, st.session_state.p1_topic_selection, st.session_state.p1_gemma_protocol, st.session_state.base_prompt_rules)
            if st.session_state.p1_research_result:
                st.text_area("자료 조사 결과", value=st.session_state.p1_research_result, height=350, label_visibility="collapsed")
                if st.button("🔍 팝업 보기", use_container_width=True, key="pop_res"): popup_edit_research()
    with c_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안")
            if st.button("🎬 총괄 시나리오 기획", use_container_width=True, disabled=is_locked):
                if not st.session_state.p1_research_result: st.error("⚠️ 리서치를 먼저 완료하세요.")
                else:
                    with st.spinner("기획 중..."):
                        st.session_state.p1_planning_result = generate_final_planning(st.session_state.p1_research_result, st.session_state.p1_gemma_protocol, st.session_state.base_prompt_rules)
            if st.session_state.p1_planning_result:
                st.text_area("최종 기획안", value=st.session_state.p1_planning_result, height=270, label_visibility="collapsed")
                if st.button("🔍 팝업 보기", use_container_width=True, key="pop_plan"): popup_edit_planning()
                if st.button("🔒 옵시디언 자동 백업", type="primary", use_container_width=True):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    if st.session_state.path_obsidian:
                        safe_makedirs(st.session_state.path_obsidian)
                        md_path = os.path.join(st.session_state.path_obsidian, f"part1_final_plan_{ts}.md")
                        if save_markdown(md_path, st.session_state.p1_planning_result):
                            lock_file_readonly(md_path)
                            st.toast("✅ 기획안 저장 완료", icon="🔒")
                            auto_git_push(f"Part1 Save: {ts}")

# Part 2, 3, 4 ... (이전 코드 동일하게 유지)
# (지면 관계상 Part 5 - render_part6_video() 로 바로 이동)

# =====================================================================
# Part 4 — Image Consistency 전용 팝업 및 함수
# =====================================================================
@st.dialog("🖼️ 이미지 마스터 규정서 편집", width="large")
def popup_edit_image_master():
    new_val = st.text_area("규정서", value=st.session_state.get("p5_image_master_prompt", ""), height=500, key="p5_master_edit_ta")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장", type="primary", key="p5_master_save"):
            st.session_state.p5_image_master_prompt = new_val
            st.toast("✅ 이미지 마스터 규정서 저장!", icon="🖼️")
            st.rerun()
    with c2:
        if st.button("취소", key="p5_master_cancel"): st.rerun()

def render_part5_image():
    # (이전 app_v13.py의 render_part5_image 및 헬퍼 함수들 위치)
    pass

# =====================================================================
# Part 5 — Video Production (Veo3 × Google Opal)
# =====================================================================

@st.dialog("🎬 Veo3 마스터 프롬프트 편집", width="large")
def popup_edit_veo3_master():
    new_val = st.text_area("Veo3 마스터 프롬프트", value=st.session_state.get("p6_veo3_master_prompt", ""), height=500, key="p6_master_edit_ta")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장", type="primary", key="p6_master_save"):
            st.session_state.p6_veo3_master_prompt = new_val
            st.toast("✅ Veo3 마스터 프롬프트 저장!", icon="🎬")
            st.rerun()
    with c2:
        if st.button("취소", key="p6_master_cancel"): st.rerun()

def render_part6_video():
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    with c_title:
        st.markdown('<div class="sage-header-compact"><h3 style="margin:0;">🎬 Part 5 — Video Production (Veo3 × Google Opal × CapCut)</h3></div>', unsafe_allow_html=True)
    with c_pin:
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        pin = st.text_input("🔒 PIN", type="password", key="p6_vid_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN 입력 (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        if pin == PART_PINS.get("part6", "7777"): st.session_state.unlock_part6_vid = True
        elif pin: st.session_state.unlock_part6_vid = False
    with c_popup:
        st.markdown('<div style="margin-top:5px;"></div>', unsafe_allow_html=True)
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p6_vid_popup_btn"): popup_assistant()
    
    is_locked = not st.session_state.get("unlock_part6_vid", False)
    if is_locked: st.warning("⚠️ 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    st.divider()

    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 Veo3 마스터 프롬프트 (YouTube Creative Director)", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언", value=st.session_state.get("obsidian_rules",""), height=250, key="p6_ob_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="p6_ob_btn", disabled=is_locked): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🎬 Veo3 마스터 프롬프트 (YouTube Creative Director)</div>', unsafe_allow_html=True)
            st.text_area("Veo3마스터", value=st.session_state.get("p6_veo3_master_prompt",""), height=250, key="p6_master_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="p6_master_btn", disabled=is_locked): popup_edit_veo3_master()
            st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

    P6_PROTO_DEFAULT = (
        "[GEMMA PROTOCOL v2.0 — 영상 파트]\n"
        "선언: 로딩 완료 시 반드시 출력:\n"
        "'🎬 GEMMA PROTOCOL v2.0 — 영상 파트 로딩 완료'\n"
        "역할: Google Opal × Veo3 영상 생성 전 과정 지휘\n"
        "출력 형식: 씬번호(3자리) | 영상프롬프트 | 카메라무빙 | 재생시간(초)\n"
        "씬번호 001~112 3자리 고정. 대본 원문 수정 절대 금지.\n"
        "@Protagonist 외형 변경 절대 금지."
    )
    if not st.session_state.get("p6_gemma_protocol"): st.session_state.p6_gemma_protocol = P6_PROTO_DEFAULT
    
    with st.expander("🎬 젬마 프로토콜 v2.0 — 영상 파트 전용 (클릭하여 확인/편집)", expanded=False):
        new_proto = st.text_area("영상 젬마 프로토콜 v2.0", value=st.session_state.p6_gemma_protocol, height=180, key="p6_protocol_ta", disabled=is_locked)
        cp1, cp2 = st.columns(2)
        with cp1:
            if st.button("💾 프로토콜 저장", key="p6_protocol_save", disabled=is_locked):
                st.session_state.p6_gemma_protocol = new_proto
                st.toast("✅ 젬마 프로토콜 저장!", icon="🎬")
        with cp2:
            if st.button("🤖 젬마에게 프로토콜 로딩 선언 요청", key="p6_protocol_load", disabled=is_locked):
                with st.spinner("젬마 프로토콜 로딩 중..."):
                    try:
                        result = call_gemma(f"아래 프로토콜을 로딩 완료하고 선언문을 출력하라:\n{st.session_state.p6_gemma_protocol}", system=SAGE_PERSONA)
                        st.session_state.p6_protocol_loaded = result
                        st.success("✅ 젬마 프로토콜 로딩 완료!")
                    except Exception as e:
                        st.error(f"프로토콜 로딩 실패: {e}")
        if st.session_state.get("p6_protocol_loaded"):
            st.text_area("젬마 로딩 선언", value=st.session_state.get("p6_protocol_loaded",""), height=100, key="p6_loaded_ta")
    st.divider()

    tab_a, tab_b, tab_c, tab_v = st.tabs(["🎬 Veo3: 영상 프롬프트 생성", "🧙 Gemma: 씬별 지시 생성", "🔀 Opal: 8계정 영상 배분", "✅ 검수: 파일 매칭 & 최종 확인"])
    with tab_a: _p6_tab_veo3(is_locked)
    with tab_b: _p6_tab_gemma(is_locked)
    with tab_c: _p6_tab_opal(is_locked)
    with tab_v: _p6_tab_check()
    st.divider()

    with st.expander("📖 Veo3 × Google Opal 영상 생성 작업 순서", expanded=False):
        st.markdown("""
**PREP-01**: Google Opal 접속 → 새 워크플로우 생성 "현자의거울_EP001_영상생성"
**PREP-02**: Veo3 마스터 프롬프트 → Opal 공통 시스템 지시 노드에 붙여넣기
**PREP-03**: 젬마 씬별 지시 CSV → Opal 순차 배분 노드에 투입
**PREP-04**: 8계정 병렬 렌더링 시작 → 계정당 14씬 담당
**PREP-05**: 렌더링 완료 video_XXX.mp4 → 06_Video_Clips 폴더 저장

---

**씬별 렌더링 루틴 (001~112 반복)**:
STEP-01: Opal 배분 CSV에서 해당 계정 씬 데이터 확인
STEP-02: Veo3 영상 프롬프트 + 이미지 파일 투입
STEP-03: Output filename = video_XXX.mp4
STEP-04: Generate → 완료 대기
STEP-05: 영상 검수 (인물 일관성/조명/16:9 비율)
STEP-06: 합격 → 저장 / 불합격 → 재생성
STEP-07: 다음 씬 (+1) 반복

⚠️ 주의: 8계정 동시 렌더링 시 Veo3 크레딧 소모 확인
⚠️ 10씬마다 일괄 검수 실시
""")

def _p6_tab_veo3(is_locked): st.info("Veo3 영상 프롬프트 생성 로직 구현 예정")
def _p6_tab_gemma(is_locked): st.info("Gemma 씬별 지시 생성 로직 구현 예정")
def _p6_tab_opal(is_locked): st.info("Opal 8계정 배분 로직 구현 예정")
def _p6_tab_check(): st.info("파일 매칭 및 최종 확인 로직 구현 예정")

# Part 6, 7, 8 및 라우팅 블록 (이전 app_v13.py와 동일하게 유지)
# (생략)
