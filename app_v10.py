# -*- coding: utf-8 -*-
"""
🪞 현자의 거울 스튜디오 (Sage's 거울 스튜디오) — Master App v10.0
================================================================
[v10.0 업데이트 사항: 2026-05-13]
- Part 3-4 (Architect+Writer) 모듈 및 UI 추가
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
    page_title="Sage's Mirror Studio v10.0",
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
        "p5_image_master_prompt", "unlock_part5"
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

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🏛️ SECTION 1 — 옵시디언 볼트 지식 계층 구조
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🔍 SECTION 3 — 지식 스캔 우선순위 규칙
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【젬마의 옵시디언 스캔 순서 — 반드시 이 순서를 지킨다】

STEP 1: 주제 키워드 추출
  입력: 자료조사 파트에서 넘겨받은 선택된 주제 1개
  처리: 주제를 3~7개의 핵심 키워드로 분해
  예시: "번아웃" → ["소진", "고갈", "무기력", "burnout", "회복", "쉼", "의미"]

STEP 2: Bible/ 폴더 우선 스캔
  이유: 성경 말씀이 대본의 영적 뼈대가 됨
  스캔 대상:
    ① BibleIndex.md 키워드 매핑 확인
    ② 시편(Psalms) — 감정 치유 관련 우선 탐색
    ③ 잠언(Proverbs) — 지혜 격언 우선 탐색
    ④ 신약 서신서 — 위로와 회복 관련
  출력: 관련 구절 3~7개 (장절 + 원문 + 한국어 번역)

STEP 3: Philosophy/ 폴더 스캔
  스캔 순서 (주제 감정에 따라 조정 가능):
    ① 칼 융 (CarlJung/) — 그림자·내면 갈등 주제 시 우선
    ② 빅터 프랭클 (ViktorFrankl/) — 고통·의미 주제 시 우선
    ③ 쇼펜하우어 (Schopenhauer/) — 욕망·고독·체념 주제 시 우선
    ④ 몽테뉴 (Montaigne/) — 자기 관조·인간 본성 주제 시 우선
    ⑤ 다크 심리학 (DarkPsychology/) — 인간관계·방어기제 주제 시
  출력: 철학 인용 3~5개 (원문 + 출처 + 대본 활용 포인트)

STEP 4: Essays/ 폴더 스캔
  목적: 딱딱한 성경·철학 언어를 따뜻한 에세이 문체로 감싸는 연결고리 확보
  스캔 기준: 주제 감정과 가장 가까운 에세이적 표현 3~5개 추출
  출력: 에세이 문장 or 단락 + 저자명 + 출처

STEP 5: 통합 지식 풀(Pool) 생성
  형식:
  {
    "topic": "선택된 주제",
    "bible_refs": [
      {"verse": "시편 23:4", "text": "내가 사망의 음침한 골짜기를...", "source": "성경 시편 23장 4절"}
    ],
    "philosophy_refs": [
      {"philosopher": "칼 융", "quote": "...", "concept": "그림자", "source": "분석심리학 — 칼 융, 1935"}
    ],
    "essay_refs": [
      {"author": "저자명", "text": "...", "source": "책명 — 저자명"}
    ],
    "fusion_concept": "세 지식군의 교차점 핵심 문장 (젬마가 분석·생성)"
  }

STEP 6: 부족한 자료 → 인터넷 리서치 보완
  조건: 옵시디언 스캔 결과가 3개 미만인 카테고리
  도구: Tavily API 검색
  검색 쿼리 형식: "[주제] [철학자명] 명언 인용" / "[주제] 심리학 연구 출처"
  출력: 검색 결과 상위 3개 요약 + URL 출처 명기
  규칙: 인터넷 자료는 반드시 [SOURCE: URL — 검색일] 형식으로 출처 표기

STEP 7: 최종 지식 초안 완성
  출력 파일명: knowledge_draft_[주제명]_[YYYYMMDD].md
  저장 경로: /Studio/ScriptDrafts/knowledge_draft_[주제명].md
  옵시디언 링크: [[ScriptDrafts/knowledge_draft_주제명]]
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🔗 SECTION 4 — 출처 표기 절대 규칙 (Source Citation Rules)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【출처 표기는 영상 파트와 이미지 파트에서 거울 텍스트로 사용됨 — 절대 생략 불가】

성경 출처 형식:
  [SOURCE: 성경 — 구약/신약 [책명] [장]:[절]]
  예시: [SOURCE: 성경 — 구약 시편 23:4]
  예시: [SOURCE: 성경 — 신약 로마서 8:28]

철학 출처 형식:
  [SOURCE: [책명] — [저자명], [출판년도], [장/페이지(있을 경우)]]
  예시: [SOURCE: 의지와 표상으로서의 세계 — 쇼펜하우어, 1818, 1권 4장]
  예시: [SOURCE: 분석심리학 — 칼 융, 1935]
  예시: [SOURCE: 빅터 프랭클의 죽음의 수용소에서 — 빅터 프랭클, 1946]
  예시: [SOURCE: 수상록 — 몽테뉴, 1580, 2권 6장]

에세이 출처 형식:
  [SOURCE: [에세이 제목] — [저자명], [출판년도]]

인터넷 출처 형식:
  [SOURCE: [출처명] — [URL], 검색일: [YYYY-MM-DD]]

출처 없는 자료 처리 규칙:
  → 반드시 [SOURCE: 출처 미확인 — 젬마 생성 내용] 표기
  → 이 표기가 있는 내용은 사용자가 직접 검증 후 사용
  → 출처 불명 내용을 출처 있는 것처럼 표기하는 것은 절대 금지
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📊 SECTION 5 — 지식 융합 원칙 (Knowledge Fusion Principles)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【3원 지식 융합 공식 — 현자의 거울 채널 정체성】

기둥 1: 성경 (Bible) — 영적 거대 진리의 뼈대
  역할: 시청자에게 자신보다 큰 존재와의 연결감을 줌
  적용: 인용 구절은 직접 나열 금지. 반드시 현재의 상처와 연결하여 풀어야 함
  금지: "성경에 이런 말이 있습니다" 같은 강의식 도입

기둥 2: 철학 (Philosophy) — 심리학적 원인 분석의 두뇌
  역할: 시청자가 자신의 고통이 '왜' 일어나는지 이해하게 함
  적용: 철학 개념을 일상 언어로 완전히 재번역해야 함
  금지: 학술 용어 나열 / 설교식 설명

기둥 3: 에세이 (Essay) — 따뜻한 인간 문체의 살결
  역할: 차가운 진리를 따뜻하게 감싸 시청자가 거부감 없이 흡수하게 함
  적용: 에세이 특유의 독백 톤 ("나는..." / "당신도..." / "우리는...")
  금지: 정보 나열 / "결론적으로" 등의 AI 클리셰

【융합 출력 형식】
성경: [구절] → 진리 제시
    ↓ 에세이 다리 문장 (감정 연결)
철학: [개념/인용] → 심리적 원인 분석
    ↓ 에세이 다리 문장 (공감 표현)
위로 결론: 성경 + 철학의 교차점에서 나온 오직 하나의 위로 문장

【성경 진리가 뼈대인 이유 — 젬마가 반드시 인식할 원칙】
모든 철학과 에세이는 성경의 진리를 보완하는 도구다.
성경과 충돌하는 철학 주장이 나올 경우:
  → 해당 철학의 인간적 통찰은 살리되
  → 성경의 영적 해답으로 귀결시킨다
  → 절대로 철학을 성경보다 우위에 두지 않는다
```

---

*이 문서 전문을 대본 파트 좌측 상단 `st.text_area`에 붙여넣으세요.*  
*버전: v2.0 | 현자의 거울 스튜디오 | Obsidian RAG Edition*
"""

MASTER_RESEARCH_PROMPT_V81 = """[자료 조사 파트 전용 마스터 규칙서: 절대 가이드]

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

IMAGE_PART_MASTER_PROMPT_V3 = r"""# 🖼️ 현자의 거울 — 이미지 파트 마스터 규정서 v3.0
## 최상단 우측칸 입력용 | Google Flow (나노바나나) × 크롬 자동화 전용

---

> **이 문서의 위치:** 이미지 파트 (Part 5) 최상단 우측 입력란  
> **적용 도구:** 구글 플로우(나노바나나) + 크롬 자동화 확장 프로그램  
> **이 문서를 읽는 사람:** 젬마 AI + 사용자(총감독)  
> **절대 원칙:** 씬 번호 누락·변경 금지 / 캐릭터 외형 변경 절대 금지 / 기존 내용 요약·삭제 금지

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🏛️ 섹션 0 — 이미지 파트 핵심 원칙 (Core Principles)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【핵심 원칙 — 작업 전 반드시 숙지】

본 파트는 확정된 대본(Part 3·4)의 씬 번호 001~112를
구글 플로우(나노바나나)를 통해 렘브란트 유화풍 이미지로
변환하는 자동화 공정이다.

원칙 1: 씬 번호 누락·변경 절대 금지
원칙 2: @Protagonist 캐릭터 외형 변경 절대 금지
원칙 3: A/B 참조 이미지는 크롬 확장 슬롯에 항상 고정(Pin) 상태 유지
원칙 4: C파트 프롬프트는 반드시 A·B 고정값과 결합하여 출력
원칙 5: 출력 형식은 아래 C-1 규격 한 줄 파이프(|) 형식을 절대 준수
원칙 6: 모든 씬에 MASTER STYLE TAG + NEGATIVE PROMPT 반드시 결합
원칙 7: 캐릭터 일관성이 깨지면 A-MASTER 재결합 후 즉시 재생성
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🧍 섹션 A — 주인공 고정 프롬프트 (A-FIXED CHARACTER ASSET)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【A-MASTER — 구글 플로우 참조 이미지 A 생성 시 사용하는 절대 고정값】
모든 C파트 프롬프트에 자동 결합된다. 이 값은 절대 수정하지 않는다.

영문 고정값:
"@Protagonist: A 60-year-old male philosopher and sage,
deeply lined face carved by decades of sorrow and wisdom,
thick silver-grey beard with subtle natural texture,
sorrowful yet luminous eyes that carry ancient knowing,
wearing a dark burgundy-black heavy linen robe with worn leather belt,
gold thread embroidery at cuffs, slightly hunched posture of quiet dignity,
large weathered hands showing the veins of age.
Rembrandt single warm key light from upper-left at 45 degrees,
catching the right cheekbone and brow, leaving left side in deep umber shadow,
warm amber candlelight color temperature 2600K."

---
【A-REFERENCE SHEET 생성 양식 — 플로우에 최초 1회 생성 후 고정(Pin)】

Character reference sheet, single composite image:
- Top row: 4-angle full body (front / left-side / right-side / back)
- Bottom row: 4-angle half body bust (front / left-side / right-side / back)
Additional: full body from upper waist, half body from lower waist
Style tags: Cinematic oil painting, Rembrandt chiaroscuro,
single candle key light upper-left, umber ochre palette,
masterpiece quality, 16:9,
--no cartoon anime 3D CGI digital art modern clothing
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🌄 섹션 B — 배경·소품 고정 프롬프트 (B-FIXED ENVIRONMENT ASSET)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
【B-MASTER — 구글 플로우 참조 이미지 B 생성 시 사용하는 절대 고정값】

@배경(Master Background):
"17th-century European philosopher's study,
floor-to-ceiling dark oak bookshelves heavy with ancient leather-bound tomes,
rough-hewn stone walls with cracks and age stains,
flagstone floor with worn rugs, dusty amber atmosphere,
dramatic single-source candlelight casting long deep shadows,
deep impasto texture, umber and ochre palette,
dust motes visible in light shafts,
antique wooden writing desk with scattered manuscripts"

---

@거울(Mirror — 핵심 오브제):
"Ornate antique bronze baroque standing mirror, 180cm tall,
heavy tarnished gold frame with acanthus leaf carvings and cherub details,
slightly foggy and imperfect aged glass surface with minor dark spots,
the mirror leans against the stone wall at a slight angle,
candlelight reflects off the bronze frame in warm amber streaks,
the glass has a subtle greenish-grey tint from centuries of oxidation"

---

@거울속아바타 — 기본값 (Mirror Avatar — Default):
"Inside the mirror: a younger version of @Protagonist,
age approximately 30, same bone structure and facial features as @Protagonist
but skin without deep wrinkles, original dark hair not yet grey,
expression slightly different from the outside — knowing, haunting,
figure is slightly ethereal and translucent,
soft internal glow as if memory has taken form,
edges slightly blurred as befits a reflection in aged glass"

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
  → PIN 상태 확인: 슬롯에 🔒 표시 확인
  ⚠️ 이 PIN이 해제되면 모든 캐릭터 일관성이 깨진다

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

배치 실행 중 주의사항:
  ⚠️ 배치 중간에 슬롯 PIN이 자동 해제될 수 있음 → 5씬마다 확인
  ⚠️ 네트워크 끊김 시 마지막 성공한 씬 번호 기록 후 이어서 실행
  ⚠️ 생성 속도: 씬당 최소 30초 대기 (서버 과부하 방지)
  ⚠️ 10씬마다 생성 결과물 일괄 검수 실시 (일관성 누적 오류 방지)
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ✅ 섹션 G — 씬 생성 전 체크리스트 (검수 기준)
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
*버전: v3.0 | 현자의 거울 스튜디오 | Google Flow × Chrome Extension Edition*
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
        "p34_gemma_protocol": GEMMA_PROTOCOL_V81,
        "p34_master_prompt": "",
        "unlock_part34": False,
        "p34_scene_structure": "",
        "p34_narration_script": "",
        "p34_image_script": "",
        "p34_capcut_data": "",
        "p5_image_master_prompt": IMAGE_PART_MASTER_PROMPT_V3,
        "unlock_part5": False,
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
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE} <span style='color:#10B981;font-size:0.5em;'>v8.2 Design Edition</span></h1>", unsafe_allow_html=True)
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
    st.markdown(f"### {APP_TITLE} **v8.2**")
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
    # V8.1: 상단 빈 공간을 활용하여 타이틀과 로그인(PIN) 창을 일렬로 배치
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    
    with c_title:
        st.markdown('<div class="sage-header-compact"><h3 style="margin:0;">📚 Part 1 — Librarian (실전 벤치마킹 & 타겟 심층 분석)</h3></div>', unsafe_allow_html=True)
        
    with c_pin:
        # 이쁘게 디자인된 로그인(로그) 창
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        pin = st.text_input("🔒 마스터 PIN", type="password", key="p1_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN 입력 (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pin == PART_PINS["part1"]: st.session_state.unlock_part1 = True
        elif pin: st.session_state.unlock_part1 = False

    with c_popup:
        st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True): popup_assistant()

    is_locked = not st.session_state.unlock_part1
    if is_locked:
        st.warning("⚠️ 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.divider()
    render_top_panel()
    st.divider()

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
Sage Mirror Studio v8.1 총괄 시나리오 기획안

## 📖 Core Content (Research)
{st.session_state.p1_research_result}

## 🎬 Final Scenario Plan
{st.session_state.p1_planning_result}

## 🔗 Knowledge Connections
- **Related Topics:** [[심리치유]], [[현자의거울]]
- **Projects/Contexts:** [[SageMirror_Production_v8.1]]

---
*Last updated: {today_str} {ts}*
"""
                        if save_markdown(md_path, md):
                            lock_file_readonly(md_path)
                            st.toast(f"✅ 기획안 저장 및 락(Lock) 완료", icon="🔒")
                            success, msg = auto_git_push(f"Auto Save (Locked): '{topic_title}'")

@st.dialog("📝 젬마 프로토콜 (Gemma Protocol) 편집", width="large")
def popup_edit_gemma_protocol_p2():
    st.markdown("여기서 행동 지침과 작업 지침서를 상세하게 수정할 수 있습니다. 텍스트를 드래그하고 복사/붙여넣기 하세요.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p2_gemma_protocol, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p2_gemma_protocol = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()

@st.dialog("📚 자료 조사 결과 (팝업)", width="large")
def popup_edit_research_p2():
    st.markdown("결과를 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")
    new_val = st.text_area("자료 조사 결과", value=st.session_state.p2_research_result, height=500, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p2_research_result = new_val
            st.rerun()
    with c2:
        if st.button("닫기", use_container_width=True):
            st.rerun()

@st.dialog("🎬 총괄 시나리오 기획 (팝업)", width="large")
def popup_edit_planning_p2():
    st.markdown("기획안을 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")
    new_val = st.text_area("최종 기획안", value=st.session_state.p2_planning_result, height=500, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p2_planning_result = new_val
            st.rerun()
    with c2:
        if st.button("닫기", use_container_width=True):
            st.rerun()

def render_part2():
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    
    with c_title:
        st.markdown('<div class="sage-header-compact"><h3 style="margin:0;">📚 Part 2 — Alchemist (대본 파트)</h3></div>', unsafe_allow_html=True)
        
    with c_pin:
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        pin = st.text_input("🔒 마스터 PIN", type="password", key="p2_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN 입력 (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pin == PART_PINS["part2"]: st.session_state.unlock_part2 = True
        elif pin: st.session_state.unlock_part2 = False

    with c_popup:
        st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p2_popup_btn"): popup_assistant()

    if "unlock_part2" not in st.session_state:
        st.session_state.unlock_part2 = False
    is_locked = not st.session_state.unlock_part2
    if is_locked:
        st.warning("⚠️ 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.divider()
    render_top_panel()
    st.divider()

    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")
    c_left, c_right = st.columns(2, gap="large")
    
    with c_left:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)
        if "p2_gemma_protocol" not in st.session_state: st.session_state.p2_gemma_protocol = st.session_state.get("p1_gemma_protocol", "")
        st.text_area("젬마 프로토콜 (수정은 편집 버튼 클릭)", value=st.session_state.p2_gemma_protocol, height=270, label_visibility="collapsed", key="p2_protocol_area")
        if st.button("🔍 프로토콜 팝업 편집 (복사/붙여넣기)", key="p2_edit_proto"):
            popup_edit_gemma_protocol_p2()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_right:
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">🖼️ 썸네일 카드 (Thumbnail Card)</div>', unsafe_allow_html=True)
        st.caption("자료조사 결과를 참조하여 썸네일(이미지), 주제, 제목을 3가지 버전으로 생성합니다.")
        
        if st.button("🚀 썸네일/주제/제목 3세트 생성 (AI)", use_container_width=True, disabled=is_locked, key="p2_thumb_btn"):
            if "p2_research_result" not in st.session_state or not st.session_state.p2_research_result:
                st.error("⚠️ 먼저 하단의 '자료조사 및 초안 작성'을 완료해 주세요.")
            else:
                with st.spinner("자료조사 기반 썸네일 3세트 기획 중..."):
                    # 향후 Gemma API 호출 로직이 들어갈 곳
                    st.info("썸네일 생성 AI 로직 연동 대기 중...")
                    st.session_state.p2_thumbnail_plan = "임시 썸네일 기획안 3세트 (추후 연동)"
        
        if "p2_thumbnail_plan" not in st.session_state:
            st.session_state.p2_thumbnail_plan = ""
            
        st.text_area("썸네일 기획 결과 (수정 가능)", value=st.session_state.p2_thumbnail_plan, height=195, label_visibility="collapsed", key="p2_thumb_area")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진 (하단 3분할)")
    c_bench, c_research, c_plan = st.columns(3, gap="large")
    
    with c_bench:
        with st.container(border=True):
            st.markdown("### 1️⃣ 채널 벤치마킹 및 주제 도출")
            st.caption("200개 댓글 분석 기반 타겟 시청자 공감 포인트 추출")
            
            if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked, key="p2_bench_btn"):
                if not st.session_state.p2_channel_url: 
                    st.error("⚠️ 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")
                else:
                    with st.spinner("채널 분석 중... (200개 댓글 공감 포인트 참조)"):
                        st.session_state.p2_topics = analyze_channel_to_topics(
                            st.session_state.p2_channel_url, st.session_state.p2_region, 
                            st.session_state.obsidian_rules, st.session_state.base_prompt_rules, st.session_state.p2_gemma_protocol
                        )
            
            if "p2_topics" in st.session_state and st.session_state.p2_topics:
                st.markdown("<br>", unsafe_allow_html=True)
                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p2_topics)]
                st.session_state.p2_topic_selection = st.selectbox("📌 기획할 주제 1개 선정", topics_display, disabled=is_locked, key="p2_topic_sel")
                with st.expander("추출된 20개 상세 결과 보기"):
                    for t in st.session_state.p2_topics:
                        st.markdown(f"**{t['title']}**\n- 사유: {t['reason']}\n- 효과: {t['effect']}")

    with c_research:
        with st.container(border=True):
            st.markdown("### 2️⃣ 옵시디언 융합 리서치")
            st.caption("성경/철학/에세이 3원 지식 융합 초안 작성")
            
            if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p2_res_btn"):
                if "p2_topic_selection" not in st.session_state or not st.session_state.p2_topic_selection:
                    st.error("⚠️ 먼저 좌측의 '벤치마킹 시작' 버튼을 눌러 분석을 완료하고 주제를 선택해 주세요.")
                else:
                    with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):
                        topic_str = st.session_state.p2_topic_selection
                        st.session_state.p2_research_result = generate_research_draft(
                            st.session_state.p2_channel_url, topic_str,
                            st.session_state.p2_gemma_protocol, st.session_state.base_prompt_rules
                        )
            
            if "p2_research_result" in st.session_state and st.session_state.p2_research_result:
                st.markdown("<br>", unsafe_allow_html=True)
                st.text_area("자료 조사 결과 (복사 가능)", value=st.session_state.p2_research_result, height=350, label_visibility="collapsed", key="p2_res_area")
                if st.button("🔍 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_res2_btn"):
                    popup_edit_research_p2()

    with c_plan:
        with st.container(border=True):
            st.markdown("### 3️⃣ 총괄 기획안 (시나리오 뼈대)")
            st.caption("최종 영상 기획 및 112씬 대본 설계를 위한 뼈대 완성")
            
            if st.button("🎬 총괄 시나리오 기획", use_container_width=True, disabled=is_locked, key="p2_plan_btn"):
                if "p2_research_result" not in st.session_state or not st.session_state.p2_research_result:
                    st.error("⚠️ 먼저 중앙의 '자료조사 및 초안 작성'을 완료해 주세요.")
                else:
                    with st.spinner("시나리오 뼈대 설계 중..."):
                        st.session_state.p2_planning_result = generate_final_planning(
                            st.session_state.p2_research_result,
                            st.session_state.p2_gemma_protocol, st.session_state.base_prompt_rules
                        )
            
            if "p2_planning_result" in st.session_state and st.session_state.p2_planning_result:
                st.markdown("<br>", unsafe_allow_html=True)
                st.text_area("최종 기획안 (복사 가능)", value=st.session_state.p2_planning_result, height=270, label_visibility="collapsed", key="p2_plan_area")
                if st.button("🔍 팝업에서 크게 보기 / 복붙", use_container_width=True, key="pop_plan2_btn"):
                    popup_edit_planning_p2()
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔒 최종안 옵시디언 자동 백업", type="primary", use_container_width=True, key="p2_backup_btn"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    base_name = f"part2_final_plan_{ts}"
                    if st.session_state.path_obsidian:
                        safe_makedirs(st.session_state.path_obsidian)
                        md_path = os.path.join(st.session_state.path_obsidian, f"{base_name}.md")
                        topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection else "기획안"
                        md = f"# [[{topic_title}]]\n## 📌 Brief Summary\nSage Mirror Studio v8.1 대본\n\n## 📖 Core Content\n{st.session_state.p2_research_result}\n\n## 🎬 Final Scenario\n{st.session_state.p2_planning_result}\n\n---\n*Last updated: {today_str} {ts}*\n"
                        if save_markdown(md_path, md):
                            lock_file_readonly(md_path)
                            st.toast(f"✅ 대본 백업 및 락(Lock) 완료", icon="🔒")
                            auto_git_push(f"Auto Save (Locked): '{topic_title}'")

@st.dialog("🎯 이미지 파트 마스터 프롬프트 편집", width="large")
def popup_edit_image_prompt():
    st.markdown("이미지 생성 규칙서를 상세하게 수정할 수 있습니다.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p5_image_master_prompt, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary", key="p5_save_prompt"):
            st.session_state.p5_image_master_prompt = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True, key="p5_cancel_prompt"):
            st.rerun()

def render_part5():
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    
    with c_title:
        st.markdown('<div class="sage-header-compact"><h3 style="margin:0;">🖼️ Part 5 — Image Consistency (구글 플로우 연동)</h3></div>', unsafe_allow_html=True)
        
    with c_pin:
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        pin = st.text_input("🔒 마스터 PIN", type="password", key="p5_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN 입력 (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # PART_PINS에 part5가 없을 수도 있으므로 기본값 7777 사용
        if pin == PART_PINS.get("part5", "7777"): st.session_state.unlock_part5 = True
        elif pin: st.session_state.unlock_part5 = False

    with c_popup:
        st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p5_popup_btn"): popup_assistant()

    if "unlock_part5" not in st.session_state:
        st.session_state.unlock_part5 = False
    is_locked = not st.session_state.unlock_part5
    if is_locked:
        st.warning("⚠️ 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.divider()
    
    # Custom Top Panel for Part 5
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 이미지 마스터 규정서", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=300, key="p5_top_ob_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="p5_ob_btn"): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🖼️ 이미지 파트 마스터 규정서 v3.0</div>', unsafe_allow_html=True)
            st.text_area("이미지 마스터 프롬프트", value=st.session_state.p5_image_master_prompt, height=300, key="p5_top_pr_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="p5_pr_btn"): popup_edit_image_prompt()
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.divider()
    st.info("👉 이미지 생성 자동화 UI 및 씬(Scene) 관리 인터페이스가 곧 이곳에 구현될 예정입니다.")

@st.dialog("🎯 마스터 프롬프트 편집 (Part 3-4)", width="large")
def popup_edit_prompt_p34():
    st.markdown("대본 작성 규정서를 수정합니다.")
    new_val = st.text_area("규칙서 내용", value=st.session_state.p34_master_prompt, height=400, label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 저장 및 닫기", use_container_width=True, type="primary"):
            st.session_state.p34_master_prompt = new_val
            st.rerun()
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()

def render_part34():
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    
    with c_title:
        st.markdown('<div class="sage-header-compact"><h3 style="margin:0;">✍️ Part 3-4 — Architect & Writer (대본 설계 및 작성)</h3></div>', unsafe_allow_html=True)
        
    with c_pin:
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        pin = st.text_input("🔒 마스터 PIN", type="password", key="p34_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN 입력 (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pin == PART_PINS.get("part34", "7777"): st.session_state.unlock_part34 = True
        elif pin: st.session_state.unlock_part34 = False

    with c_popup:
        st.markdown('<div style="margin-top: 5px;"></div>', unsafe_allow_html=True)
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="p34_popup_btn"): popup_assistant()

    if "unlock_part34" not in st.session_state:
        st.session_state.unlock_part34 = False
    is_locked = not st.session_state.unlock_part34
    if is_locked:
        st.warning("⚠️ 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.")
    
    st.divider()
    
    # Custom Top Panel for Part 3-4
    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 대본 마스터 프롬프트", expanded=True):
        L, R = st.columns(2, gap="medium")
        with L:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)
            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=300, key="p34_top_ob_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="p34_ob_btn"): popup_edit_obsidian()
            st.markdown('</div>', unsafe_allow_html=True)
        with R:
            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🎯 대본 마스터 프롬프트 (가이드)</div>', unsafe_allow_html=True)
            st.text_area("대본 마스터 프롬프트", value=st.session_state.p34_master_prompt, height=300, key="p34_top_pr_view", label_visibility="collapsed")
            if st.button("🔍 편집", key="p34_pr_btn"): popup_edit_prompt_p34()
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.divider()

    # ── Step 1: 젬마 프로토콜 (중간 영역) ──
    st.subheader("🧩 Step 1. 젬마 프로토콜 로딩")
    with st.container(border=True):
        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Part 3-4 전용)</div>', unsafe_allow_html=True)
        st.text_area("젬마 프로토콜", value=st.session_state.p34_gemma_protocol, height=200, label_visibility="collapsed", key="p34_proto_area")
        if st.button("🔍 프로토콜 팝업 편집", key="p34_edit_proto"):
            popup_edit_prompt_p34()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ── Step 2: Architect — 기-승-전-결 112씬 뼈대 설계 ──
    st.subheader("🏗️ Step 2. Architect — 112씬 구조 설계 (기-승-전-결)")
    with st.container(border=True):
        st.caption("Part 2에서 완성된 기획안을 기반으로, 112씬의 기-승-전-결 서사 뼈대를 설계합니다.")
        
        c_arch_btn, c_arch_info = st.columns([3, 7])
        with c_arch_btn:
            if st.button("🚀 112씬 구조 자동 설계 (AI)", use_container_width=True, disabled=is_locked, type="primary", key="p34_arch_btn"):
                p2_plan = st.session_state.get("p2_planning_result", "")
                if not p2_plan:
                    st.error("⚠️ Part 2의 '총괄 기획안'이 비어 있습니다. Part 2를 먼저 완료해 주세요.")
                else:
                    with st.spinner("기-승-전-결 112씬 뼈대 설계 중..."):
                        prompt = f"""[지시] 아래 기획안을 바탕으로 112씬 분량의 대본 구조(뼈대)를 설계해 주세요.

[기획안]
{p2_plan}

[출력 형식]
기(001-028): 각 씬의 한 줄 요약 (감정: EXPR코드)
승(029-056): 각 씬의 한 줄 요약 (감정: EXPR코드)
전(057-084): 각 씬의 한 줄 요약 (감정: EXPR코드)
결(085-112): 각 씬의 한 줄 요약 (감정: EXPR코드)

{st.session_state.p34_gemma_protocol}"""
                        result = call_gemma(prompt)
                        st.session_state.p34_scene_structure = result
        with c_arch_info:
            st.info("Part 2 기획안 → 기(001~028) / 승(029~056) / 전(057~084) / 결(085~112) 자동 분배")

        st.text_area("📐 112씬 구조 설계 결과 (수정 가능)", value=st.session_state.p34_scene_structure, height=400, key="p34_struct_area")
        
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            if st.button("💾 구조 설계 저장", use_container_width=True, key="p34_save_struct"):
                st.session_state.p34_scene_structure = st.session_state.p34_struct_area
                save_workspace_state()
                st.toast("✅ 112씬 구조 설계 저장 완료!", icon="💾")
        with c_s2:
            if st.button("🔒 옵시디언 백업", use_container_width=True, disabled=is_locked, key="p34_backup_struct"):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                if st.session_state.path_obsidian:
                    safe_makedirs(st.session_state.path_obsidian)
                    md_path = os.path.join(st.session_state.path_obsidian, f"part34_structure_{ts}.md")
                    md = f"# [[112씬 구조 설계]]\n## 📌 Brief Summary\n112씬 기-승-전-결 뼈대\n\n## 📖 Core Content\n{st.session_state.p34_scene_structure}\n\n---\n*Last updated: {ts}*\n"
                    if save_markdown(md_path, md):
                        lock_file_readonly(md_path)
                        st.toast("✅ 구조 설계 백업 및 락(Lock) 완료", icon="🔒")

    st.divider()

    # ── Step 3: Writer — 3단 대본 집필 (나레이션 / 이미지 / 캡컷) ──
    st.subheader("✍️ Step 3. Writer — 대본 집필 (3단 분리)")
    st.caption("확정된 112씬 구조 위에 살을 붙여, 나레이션·이미지·캡컷 3종 대본을 각각 집필합니다.")
    
    c_narr, c_img, c_cap = st.columns(3, gap="large")
    
    with c_narr:
        with st.container(border=True):
            st.markdown("### 1️⃣ 나레이션 대본")
            st.caption("시청자가 듣게 될 순수 나레이션 텍스트 (CosyVoice 연동)")
            
            if st.button("🎙️ 나레이션 대본 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_narr_btn"):
                if not st.session_state.p34_scene_structure:
                    st.error("⚠️ Step 2의 '112씬 구조 설계'를 먼저 완료해 주세요.")
                else:
                    with st.spinner("나레이션 대본 집필 중..."):
                        prompt = f"""[지시] 아래 112씬 구조를 바탕으로 각 씬의 나레이션 대본을 작성하세요.
화자는 60대 현자(Sage)이며, 4070 시청자에게 말하듯 따뜻하고 묵직한 톤으로 작성합니다.

[112씬 구조]
{st.session_state.p34_scene_structure}

[출력 형식] 
씬번호(3자리) | 나레이션 대본 텍스트

{st.session_state.p34_gemma_protocol}"""
                        st.session_state.p34_narration_script = call_gemma(prompt)
            
            st.text_area("나레이션 대본", value=st.session_state.p34_narration_script, height=350, label_visibility="collapsed", key="p34_narr_area")
            if st.button("💾 나레이션 저장", use_container_width=True, key="p34_save_narr"):
                st.session_state.p34_narration_script = st.session_state.p34_narr_area
                save_workspace_state()
                st.toast("✅ 나레이션 대본 저장!", icon="💾")

    with c_img:
        with st.container(border=True):
            st.markdown("### 2️⃣ 이미지 생성용 대본")
            st.caption("씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ (Part 5 연동)")
            
            if st.button("🖼️ 이미지 프롬프트 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_img_btn"):
                if not st.session_state.p34_narration_script:
                    st.error("⚠️ 좌측의 '나레이션 대본'을 먼저 완료해 주세요.")
                else:
                    with st.spinner("이미지 프롬프트 변환 중..."):
                        prompt = f"""[지시] 아래 나레이션 대본을 이미지 파트 규격(C-1)에 맞춰 변환하세요.

[나레이션 대본]
{st.session_state.p34_narration_script}

[출력 형식 — 반드시 준수]
씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@

한글묘사에는: 인물동작, 시선, 빛, 소품태그, 표정코드[EXPR-0X] 필수
영어프롬프트에는: [A-MASTER], 소품태그, 표정값, [@배경], [MASTER STYLE TAG], [NEGATIVE PROMPT] 필수

{st.session_state.p34_gemma_protocol}"""
                        st.session_state.p34_image_script = call_gemma(prompt)
            
            st.text_area("이미지 프롬프트", value=st.session_state.p34_image_script, height=350, label_visibility="collapsed", key="p34_img_area")
            if st.button("💾 이미지 대본 저장", use_container_width=True, key="p34_save_img"):
                st.session_state.p34_image_script = st.session_state.p34_img_area
                save_workspace_state()
                st.toast("✅ 이미지 대본 저장!", icon="💾")

    with c_cap:
        with st.container(border=True):
            st.markdown("### 3️⃣ 캡컷 에셋 데이터")
            st.caption("CapCut 자동 조립용 JSON (타임라인·BGM·이미지 매핑)")
            
            if st.button("🎬 캡컷 JSON 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_cap_btn"):
                if not st.session_state.p34_image_script:
                    st.error("⚠️ 중앙의 '이미지 대본'을 먼저 완료해 주세요.")
                else:
                    with st.spinner("캡컷 JSON 조립 중..."):
                        prompt = f"""[지시] 아래 이미지 대본을 CapCut 자동화 JSON으로 변환하세요.

[이미지 대본]
{st.session_state.p34_image_script}

[출력 형식 — JSON]
각 씬: scene_id, script, action_kr, expression, props_used, image_file, audio_file, timeline_order, duration_sec

{st.session_state.p34_gemma_protocol}"""
                        st.session_state.p34_capcut_data = call_gemma(prompt)
            
            st.text_area("캡컷 JSON", value=st.session_state.p34_capcut_data, height=350, label_visibility="collapsed", key="p34_cap_area")
            if st.button("💾 캡컷 데이터 저장", use_container_width=True, key="p34_save_cap"):
                st.session_state.p34_capcut_data = st.session_state.p34_cap_area
                save_workspace_state()
                st.toast("✅ 캡컷 에셋 저장!", icon="💾")

    st.divider()

    # ── 최종 백업 ──
    if st.button("🔒 Part 3-4 전체 대본 옵시디언 자동 백업", type="primary", use_container_width=True, disabled=is_locked, key="p34_final_backup"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        today_str = datetime.now().strftime("%Y-%m-%d")
        if st.session_state.path_obsidian:
            safe_makedirs(st.session_state.path_obsidian)
            md_path = os.path.join(st.session_state.path_obsidian, f"part34_full_script_{ts}.md")
            md = f"# [[대본 최종본 v{ts}]]\n## 📌 Brief Summary\nSage Mirror Studio v10.0 — Part 3-4 완성 대본\n\n"
            md += f"## 📐 112씬 구조 설계\n{st.session_state.p34_scene_structure}\n\n"
            md += f"## 🎙️ 나레이션 대본\n{st.session_state.p34_narration_script}\n\n"
            md += f"## 🖼️ 이미지 프롬프트 대본\n{st.session_state.p34_image_script}\n\n"
            md += f"## 🎬 캡컷 에셋 JSON\n```json\n{st.session_state.p34_capcut_data}\n```\n\n"
            md += f"---\n*Last updated: {today_str} {ts}*\n"
            if save_markdown(md_path, md):
                lock_file_readonly(md_path)
                st.toast("✅ Part 3-4 전체 대본 백업 및 락(Lock) 완료!", icon="🔒")
                auto_git_push(f"Auto Save (Part 3-4 Full Script): {ts}")

if part.startswith("Part 1"): render_part1()
elif part.startswith("Part 2"): render_part2()
elif part.startswith("Part 3-4"): render_part34()
elif part.startswith("Part 5"): render_part5()
else:
    # 빈 공간 채우기를 위해 다른 파트들도 구조 변경 가능
    _l, _r = st.columns([7, 2])
    with _r:
        if st.button("🤖 Sage Pop-up", type="secondary", use_container_width=True, key="other_popup_btn"): popup_assistant()
    render_top_panel()
    st.divider()
    
    st.markdown(f'<div class="sage-header-compact"><h3 style="margin:0;">{part}</h3></div>', unsafe_allow_html=True)
    st.info("👉 다음 지시서에서 구현됩니다.")

