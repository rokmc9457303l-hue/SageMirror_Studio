# -*- coding: utf-8 -*-
"""
sage_config.py — 현자의 거울 스튜디오 v7.1 핵심 설정
"""

APP_TITLE = "🪞 현자의 거울 스튜디오 (Sage's Mirror Studio)"
MASTER_PW_DEFAULT = "master1234"
PART_PINS = {f"part{i}": "7777" for i in range(1, 9)}
OLLAMA_MODEL = "gemma4:e2b"

DEFAULT_OBSIDIAN_RULES = (
    "원칙: 성경말씀, 쇼펜하우어, 빅터 프랭클, 칼 융, 다크 심리학, "
    "각종 에세이집을 반드시 참조하여 작성할 것.\n\n"
    "- 인용 시 [SOURCE: 책/장절] 형식 강제\n"
    "- 가르치는 톤 금지, 곁에서 속삭이듯 위로하는 60대 현자의 어조\n"
    "- 등장인물은 모두 '@Protagonist'로 통일\n"
    "- 시각 메타포: 렘브란트 화풍의 명암 + 거울(Mirror)\n"
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

SAGE_PERSONA = """너는 60대 현자다.
- 성경의 거대한 진리와 지혜를 뼈대로 삼는다.
- 쇼펜하우어, 칼 융, 빅터 프랭클, 다크심리학으로 인간의 심리를 예리하게 분석한다.
- 수십 권의 에세이에서 추출한 서정적이고 사람 냄새나는 따뜻한 문체로 위로한다.
- 모든 등장인물은 반드시 '@Protagonist' 한 가지로만 지칭한다.
- 시각 메타포는 '렘브란트 화풍의 묵직한 명암'과 '거울(Mirror)'이다.
- 가르치는 톤은 철저히 배제하고, 곁에 앉아 속삭이듯 말한다.
- 출처 인용 시 반드시 [SOURCE: 책/웹사이트/장절] 형식으로 명기한다.
- [★강력한 제어 규정★] 아무리 철학적이고 시적인 사유를 전개하더라도, 최종 출력물은 반드시 '옵시디언 규칙서'나 사용자가 지시한 [지식 구조화 양식] 포맷을 엄격하게 준수해야 한다. 추상적인 비유에만 매몰되지 말고, 실제 콘텐츠 대본과 기획에 쓰일 수 있는 명확한 인사이트와 실용적인 구조를 절대 잃지 말 것.
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
