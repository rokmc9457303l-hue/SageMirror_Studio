# -*- coding: utf-8 -*-
"""
core/critic/patterns.py — 할루시네이션 탐지 패턴 + 금지 표현

Layer 1(사실검증)에서 사용하는 regex 패턴 사전.
"""

import re

# ── 할루시네이션 위험 패턴 ────────────────────────────────────────────
# (설명, 패턴, 심각도, 자동수정가능, 검색키워드힌트)
HALLUCINATION_PATTERNS = [
    (
        "근거 없는 통계",
        re.compile(r"\d{1,3}[%％](?:\s*의\s*|\s+)(?:사람|응답|조사|연구|전문가)", re.IGNORECASE),
        "ERROR",
        True,
        "출처 없는 통계 수치 검증",
    ),
    (
        "출처 없는 인용구",
        re.compile(r'[""]([^""]{20,})[""](?!\s*[-–—]\s*\w)', re.UNICODE),
        "ERROR",
        True,
        "인용구 원전 검색",
    ),
    (
        "과도한 일반화",
        re.compile(r"(모든|모두|항상|절대|반드시|누구나|어느 누구도)\s+\w+", re.UNICODE),
        "WARN",
        False,
        None,
    ),
    (
        "불확실한 수치",
        re.compile(r"약\s*\d+\s*(?:만|억|조|명|년|세기|배)", re.UNICODE),
        "WARN",
        True,
        "수치 검증",
    ),
    (
        "가상 사례 제시",
        re.compile(r"예를 들어.{0,30}(?:경우|상황|사람|시절)", re.UNICODE),
        "WARN",
        False,
        None,
    ),
    (
        "연구/실험 주장 (출처 없음)",
        re.compile(r"(?:연구|실험|논문|조사)\s*(?:에\s*따르면|결과|에서|에\s*의하면)", re.UNICODE),
        "ERROR",
        True,
        "연구 출처 검색",
    ),
    (
        "역사적 사실 단정",
        re.compile(r"\d{3,4}년\s*(?:에|에는|의)\s*\w+(?:이|가|은|는)\s*\w+(?:했다|이었다|이다)", re.UNICODE),
        "WARN",
        True,
        "역사 사실 검증",
    ),
]

# ── 성경 구절 패턴 (Layer 2 출처 검증용) ─────────────────────────────
BIBLE_VERSE_PATTERN = re.compile(
    r"(창세기|출애굽기|레위기|민수기|신명기|여호수아|사사기|룻기|사무엘|"
    r"열왕기|역대|에스라|느헤미야|에스더|욥기|시편|잠언|전도서|아가|"
    r"이사야|예레미야|예레미야애가|에스겔|다니엘|호세아|요엘|아모스|"
    r"오바댜|요나|미가|나훔|하박국|스바냐|학개|스가랴|말라기|"
    r"마태복음|마가복음|누가복음|요한복음|사도행전|로마서|고린도|"
    r"갈라디아|에베소|빌립보|골로새|데살로니가|디모데|디도|빌레몬|"
    r"히브리서|야고보서|베드로|요한서|유다서|요한계시록)"
    r"\s*\d+:\d+",
    re.UNICODE,
)

# ── 철학자 인용 패턴 ─────────────────────────────────────────────────
PHILOSOPHER_PATTERN = re.compile(
    r"(쇼펜하우어|프랭클|빅터\s*프랭클|칼\s*융|몽테뉴|스토아|"
    r"니체|키르케고르|하이데거|사르트르|카뮈|아리스토텔레스|"
    r"플라톤|소크라테스|마르쿠스\s*아우렐리우스|세네카|에픽테토스)"
    r"(?:의|은|는|이|가|에\s*따르면|에\s*의하면)?",
    re.UNICODE,
)

# ── 채널별 금지 표현 (기본값 — profile에서 오버라이드) ─────────────────
FORBIDDEN_EXPRESSIONS = [
    "힘내세요",
    "응원합니다",
    "함께 나아가요",
    "긍정적으로",
    "할 수 있어요",
    "포기하지 마세요",
    "요약하자면",
    "결론적으로",
    "도움이 되었기를",
    "자기계발",
    "꼰대",
    "1020",
    "MZ",
    "레전드",
    "ㄹㅇ",
    "킹갓",
]

# ── 필수 필드별 최소 품질 기준 ──────────────────────────────────────────
COMPLETENESS_RULES = {
    "topic": {"min_len": 5, "required": True},
    "core_emotion": {"min_len": 2, "required": True},
    "audience_pain": {"min_len": 10, "required": True},
    "research_sources": {"min_items": 1, "required": True},
    "title_candidates": {"min_items": 3, "required": True},
    "comment_insights": {"min_items": 0, "required": False},
    "benchmark_summary": {"min_len": 20, "required": False},
    "knowledge_score": {"required": False},
}


def check_forbidden(text: str, extra_forbidden: list = None) -> list:
    """텍스트에서 금지 표현 검출. 금지 표현 목록 반환."""
    found = []
    all_forbidden = FORBIDDEN_EXPRESSIONS + (extra_forbidden or [])
    for expr in all_forbidden:
        if expr in text:
            found.append(expr)
    return found


def scan_hallucination(text: str) -> list:
    """할루시네이션 패턴 스캔. [(설명, 심각도, 매치텍스트, 자동수정, 힌트), ...]"""
    results = []
    for desc, pattern, severity, auto_fix, hint in HALLUCINATION_PATTERNS:
        for match in pattern.finditer(text):
            results.append((desc, severity, match.group(), auto_fix, hint))
    return results
