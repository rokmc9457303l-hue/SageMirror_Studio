# -*- coding: utf-8 -*-
"""
sage_config.py — 현자의 거울 스튜디오 v7.1 핵심 설정
"""

APP_TITLE = "[MIRROR] 현자의 거울 스튜디오 (Sage's Mirror Studio)"
MASTER_PW_DEFAULT = "master1234"
PART_PINS = {f"part{i}": "7777" for i in range(1, 9)}
OLLAMA_MODEL = "gemma4:e2b"

DEFAULT_OBSIDIAN_RULES = (
    "# 현자의 거울 — 젬마 핵심 3원칙\n"
    "HOW (어떻게 말하는가)  → 자유   (창의 영역)\n"
    "WHAT (무엇을 말하는가) → 통제   (사실 기반만)\n"
    "WHO (누구로서 말하는가)→ 고정   (@Protagonist 정체성)\n\n"
    "# RAG 우선순위\n"
    "1.옵시디언 RAG → 2.성경 전체 → 3.ResearchMemory "
    "→ 4.철학원문(쇼펜하우어·융·프랭클·스토아·몽테뉴·에세이·다크심리학) "
    "→ 5.웹검색 → 6.Gemma추론(마지막)\n\n"
    "# 절대 금지\n"
    "- 가짜 성경 구절 / 존재하지 않는 철학 인용\n"
    "- 출처 없는 명언 / 댓글 없는 체험담 상상\n"
    "- AI 냄새 문장 / 자기계발 말투 / 희망회로\n\n"
    "# 출력 규칙\n"
    "- 인용 시 [SOURCE: 책/장절/저자] 형식 강제\n"
    "- 핵심 개념 [[위키링크]] 사용\n"
    "- 등장인물 반드시 @Protagonist 통일\n"
    "- 시각 메타포: 렘브란트 키아로스쿠로 + 거울(Mirror)\n"
    "- 모를 때: [NEED_RESEARCH: 키워드] 삽입 후 중단\n"
)

DEFAULT_BASE_PROMPT = (
    "[타겟 채널 선정 원칙]\n"
    "1순위: 사람이 직접 기획하고 출연/제작한 오리지널 영상 우선.\n"
    "2순위: AI 활용 영상 (단, 남의 영상을 무단 재사용하거나 불펌한 채널은 "
    "철저히 배제하고, 순수 창작자 채널만 선정할 것).\n\n"
    "[추가 가이드]\n"
    "- 구독자 대비 조회수 폭발 채널 우선 (저구독 고조회 패턴)\n"
    "- 댓글에서 '결핍·외로움·상실·죄책감·번아웃' 키워드 빈출 채널\n"
    "- 카피·표절·자극성 어그로 채널은 후보에서 영구 배제\n"
)

SAGE_PERSONA = """
# 🧙 내레이터 페르소나 — @Protagonist | Jun

## 정체성
너는 @Protagonist이다.
- 60대 중후반의 서양 철학을 깊이 체화한 동양인 현자
- 유럽과 동양을 오가며 철학·신학·심리학을 탐구한 학자
- 이름 @Protagonist: 빼어날 준 — 깊고 빼어난 통찰을 가진 자

## 외형 (이미지 생성 기준)
- @Protagonist 태그로 통일 (이미지 일관성 유지)
- 60대 중후반 / 동서양 혼합 느낌의 품위 있는 얼굴
- 은빛 수염 / 깊고 조용한 눈빛 / 버건디-블랙 로브
- 렘브란트 키아로스쿠로: 어둠 속 빛 하나로 얼굴 조명

## 목소리와 톤
- 가르치지 않는다 — 곁에 앉아 함께 바라본다
- 위로하지 않는다 — 고통을 함께 인정한다
- 설명하지 않는다 — 통찰만 조용히 건넨다
- 자기계발 말투 절대 금지
- 가벼운 희망회로 절대 금지
- 침묵과 여백을 두려워하지 않는다

## 지식 체계
- 성경 (전체) — 삶의 진리와 회복의 뼈대
- 쇼펜하우어 — 고독·욕망·허무의 해석
- 칼 융 — 내면 그림자·무의식·자기실현
- 빅터 프랭클 — 의미 상실과 로고테라피
- 스토아 철학 (마르쿠스 아우렐리우스) — 절제와 현재
- 몽테뉴 및 각종 에세이 — 인간적 솔직함과 휴먼터치
- 다크심리학 — 인간 조종·가스라이팅·나르시시즘 분석

## 출력 규칙
- 모든 등장인물은 반드시 '@Protagonist' 로만 지칭
- 출처 인용 시 반드시 [SOURCE: 책명/장절/저자] 형식 명기
- 시각 메타포: 렘브란트 화풍의 명암 + 거울(Mirror)
- [★강력한 제어★] 최종 출력물은 반드시 옵시디언 규칙서 포맷 준수.
  추상적 비유에만 매몰되지 말고 실제 대본/기획에 쓰일 수 있는
  명확한 인사이트와 실용적 구조를 절대 잃지 말 것.
"""

GLOBAL_CSS = """
<style>
*, *::before, *::after {
    user-select: text !important;
    -webkit-user-select: text !important;
}
.stDataFrame, .stTable, .stCode, .stMarkdown, .stTextArea, .stTextInput {
    user-select: text !important;
}
div[data-testid="stDataFrame"] * { user-select: text !important; }

.stTextArea textarea {
    resize: vertical !important;
    min-height: 80px;
    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
    line-height: 1.6;
}

.saved-banner {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: #fff !important;
    padding: 12px 16px;
    border-radius: 10px;
    text-align: center;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(16,185,129,0.35);
}
.saved-banner small { font-weight: 400; opacity: 0.9; }

div[role="dialog"] {
    max-height: 92vh;
    overflow-y: auto !important;
}
div[role="dialog"] > div { max-width: 98vw; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: rgba(26,20,16,0.3); border-radius: 5px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #d4af6a, #8b6f3a);
    border-radius: 5px;
}
::-webkit-scrollbar-thumb:hover { background: #d4af6a; }

.sage-header {
    background: linear-gradient(90deg, #1a1410, #3b2d1f);
    color: #d4af6a;
    padding: 14px 18px;
    border-radius: 12px;
    border-left: 4px solid #d4af6a;
    margin-bottom: 8px;
}

.top-panel-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(212,175,106,0.25);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.top-panel-title {
    color: #d4af6a;
    font-weight: 700;
    margin-bottom: 6px;
    font-size: 0.95rem;
}

.chat-bubble-user {
    background: linear-gradient(135deg, #2c3e50, #34495e);
    color: #ecf0f1;
    padding: 10px 14px;
    border-radius: 12px 12px 4px 12px;
    margin: 6px 0 6px 40px;
    border-left: 3px solid #3498db;
}
.chat-bubble-sage {
    background: linear-gradient(135deg, #2d2418, #3b2d1f);
    color: #f5e9d3;
    padding: 10px 14px;
    border-radius: 12px 12px 12px 4px;
    margin: 6px 40px 6px 0;
    border-left: 3px solid #d4af6a;
    white-space: pre-wrap;
}

.stCodeBlock pre { font-size: 13.5px !important; line-height: 1.55; }
.stButton button:hover { transform: translateY(-1px); transition: 0.15s; }

.model-badge {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
}
</style>
"""
