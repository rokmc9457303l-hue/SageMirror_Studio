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
"\n# RAG 태그 사용 규칙\n"
"- [READ_OBSIDIAN:] 키워드는 RAG_TAG_SYSTEM 목록에서 선택\n"
"- 카테고리별 검색 가능: 고독/다크심리학/쇼펜하우어/성경 등\n"
"- 복수 키워드: [READ_OBSIDIAN: 고독, 쇼펜하우어, 시편]\n"
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


# ══════════════════════════════════════════════════════════════
# 🗂️ 현자의 거울 — RAG 검색 태그 시스템 v1.0
# 젬마가 [READ_OBSIDIAN:] 태그 사용 시 이 목록에서 키워드를 선택하라
# ══════════════════════════════════════════════════════════════

RAG_TAG_SYSTEM = """
[RAG 검색 가능 태그 전체 목록]
젬마가 [READ_OBSIDIAN: 키워드] 또는 [NEED_RESEARCH: 키워드] 사용 시
반드시 아래 태그 목록에서 가장 적합한 키워드를 선택하라.
목록에 없는 키워드는 가장 유사한 태그로 대체하라.

🔴 핵심 감정:
고독, 외로움, 고립, 소외, 단절, 혼자됨, 쓸쓸함,
후회, 회한, 자책, 죄책감, 미련, 아쉬움, 돌아봄,
상실, 죽음, 이별, 떠나보냄, 비어있음, 그리움,
공허, 허무, 무의미, 허탈, 무력감, 탈진,
슬픔, 우울, 절망, 무기력, 침묵, 체념,
분노, 억울함, 배신감, 상처, 원망, 서운함,
두려움, 불안, 걱정, 공포, 망설임, 회피,
수치심, 열등감, 자존감 붕괴, 부끄러움, 위축됨

🟡 관계 심리:
관계 단절, 가족 갈등, 부모 자식, 부부 갈등, 형제 단절,
친구 배신, 직장 인간관계, 오래된 관계, 관계 피로,
외면, 무시, 냉대, 거절, 버려짐, 선택받지 못함,
의존, 집착, 떠나지 못함, 관계 중독, 감정 소진,
혼자 남겨짐, 은퇴 후 고독, 빈둥지 증후군,
노년 고독, 황혼 이혼, 세대 갈등, 소통 단절

🌑 다크심리학:
가스라이팅, 현실 왜곡, 자존감 파괴, 심리 조종,
나르시시즘, 자기애적 학대, 지배 착취, 감정 착취,
정서적 방치, 냉담, 무관심 폭력, 감정 노예,
죄책감 유발, 수치심 주입, 조종자, 피해자화,
의존성 심화, 분리 불안, 심리적 학대,
공감 결여, 경계선 붕괴,
트라우마 결합, 복합 PTSD, 학습된 무기력,
독성 관계, 학대 사이클, 생존자 증후군

🟣 쇼펜하우어:
쇼펜하우어, 의지와 표상으로서의 세계, 맹목적 의지,
욕망의 허무, 고통의 근원, 의지 부정, 금욕주의,
권태와 고통, 염세주의, 비관주의, 고독의 철학,
천재와 고독, 동정심, 죽음과 의지,
미적 관조, 구원으로서의 예술, 쾌락의 환상,
마야의 베일, 세계 의지, 자아의 환상

🟠 칼 융:
칼 융, 분석심리학, 무의식, 집단 무의식,
그림자, 페르소나, 아니마, 아니무스,
자기실현, 개성화, 원형, 콤플렉스,
심리 유형, 내향, 외향, 공시성,
노년기 심리, 인생 후반, 중년 위기,
투사, 내면 아이, 억압된 감정,
상징과 꿈, 종교와 심리, 신화와 무의식

🟤 빅터 프랭클:
빅터 프랭클, 로고테라피, 의미치료, 죽음의 수용소에서,
삶의 의미, 의미 상실, 실존적 공허, 실존 분석,
비극적 낙관주의, 고통의 의미, 선택의 자유,
자기 초월, 자기 거리두기, 탈반성,
책임과 의미, 삶이 묻는 질문, 소명,
집단 신경증, 의미 없는 성공

🌿 스토아 철학:
스토아, 마르쿠스 아우렐리우스, 명상록, 에픽테토스,
세네카, 통제 이분법, 현재 집중,
감정 조절, 이성과 자연, 덕의 윤리,
죽음 명상, 메멘토 모리, 아모르 파티,
내면의 요새, 자연과의 조화, 판단 중지

🍃 몽테뉴·에세이:
몽테뉴, 수상록, 자기 탐구, 인간 본성,
불완전함의 수용, 자기 자신으로 살기,
경험의 철학, 회의주의, 관용, 자기 관찰,
일상의 철학, 죽음과 친해지기, 우정,
인간의 다양성, 솔직함, 자유로운 정신

📖 성경:
시편, 시편 23편, 시편 46편, 시편 91편, 시편 139편,
잠언, 잠언 3장, 잠언 31장,
전도서, 전도서 3장, 헛되고 헛되다, 때의 철학,
욥기, 고통과 신앙, 욥의 인내, 시련의 의미,
이사야, 이사야 40장, 위로의 신학, 새 힘,
로마서, 로마서 8장, 고통과 영광, 연단,
고린도전서, 사랑장, 고린도후서, 약함의 은혜,
마태복음, 산상수훈, 걱정 말라, 용서,
누가복음, 돌아온 탕자, 자비, 화해,
히브리서, 믿음의 정의,
야고보서, 시험과 인내, 지혜 구하기

🧠 심리학 일반:
자존감, 자아 정체성, 정체성 혼란,
트라우마, 애착, 불안 애착, 회피 애착, 안정 애착,
번아웃, 소진, 정서 조절, 감정 표현,
방어기제, 억압, 투사, 합리화, 부정,
인지왜곡, 흑백논리, 과잉일반화, 재앙화,
자기효능감, 레질리언스, 회복탄력성,
노화 심리, 죽음 불안, 생의 의미

🎭 인생 단계 (4070):
은퇴, 은퇴 후 정체성, 역할 상실, 직업 정체성,
노년기, 중년 위기, 인생 후반,
빈둥지, 자녀 독립, 부모 역할 종료,
건강 쇠퇴, 질병, 몸의 변화, 죽음 준비,
재정 불안, 노후 걱정, 경제적 불안,
인생 회고, 과거 정리, 남은 삶, 유산

🌍 영적·실존:
실존주의, 하이데거, 키르케고르,
죽음을 향한 존재, 본래성,
신앙, 영성, 기도, 묵상, 침묵,
용서와 화해, 회개, 은혜, 구원,
인생의 목적, 소명, 사명,
영원성, 내세, 부활, 희망

[READ_OBSIDIAN: 사용 규칙]
- 반드시 위 목록에서 가장 적합한 키워드 선택
- 복수 키워드 가능: [READ_OBSIDIAN: 고독, 쇼펜하우어]
- 카테고리명도 검색 가능: [READ_OBSIDIAN: 다크심리학]
- 목록에 없는 키워드는 가장 유사한 태그로 대체
"""

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

## RAG 태그 참조
- [READ_OBSIDIAN:] 사용 시 반드시 RAG_TAG_SYSTEM 목록에서 키워드 선택
- [NEED_RESEARCH:] 사용 시도 동일한 태그 체계 적용

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
