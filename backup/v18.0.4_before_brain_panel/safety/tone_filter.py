# -*- coding: utf-8 -*-
"""
safety/tone_filter.py — AI 냄새 표현 자동 필터
"""

# ── 금지 표현 (1020 자기계발 톤) ──
BANNED_PHRASES = [
    "함께 나아가요", "함께 해요", "여러분 모두",
    "이겨낼 수 있어요", "행복하세요", "긍정적으로",
    "에너지를 받아요", "힘내세요", "응원합니다",
    "파이팅", "화이팅", "최고예요",
    "정말 멋져요", "대박", "굿잡",
    "할 수 있어요!", "포기하지 마세요",
]

# ── AI 특유 표현 ──
AI_SMELL_PHRASES = [
    "도움이 되었기를 바랍니다", "궁금한 점이 있으시면",
    "더 알고 싶으시다면", "추가 질문이 있으시면",
    "결론적으로 말씀드리면", "요약하자면",
    "정리하자면", "마지막으로",
]


def detect_ai_smell(text: str) -> list:
    """AI 냄새 / 금지 표현 검출"""
    detected = []
    for phrase in BANNED_PHRASES + AI_SMELL_PHRASES:
        if phrase in text:
            detected.append(phrase)
    return detected


def filter_ai_smell(text: str) -> dict:
    """검출 결과 + 권장 조치"""
    detected = detect_ai_smell(text)
    return {
        "clean": len(detected) == 0,
        "detected": detected,
        "count": len(detected),
        "action": "재생성 권장" if detected else "통과",
    }


def auto_clean(text: str) -> str:
    """간단한 자동 제거"""
    for phrase in BANNED_PHRASES + AI_SMELL_PHRASES:
        text = text.replace(phrase, "")
    return text.strip()
