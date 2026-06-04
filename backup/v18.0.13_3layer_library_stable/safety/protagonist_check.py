# -*- coding: utf-8 -*-
"""
safety/protagonist_check.py — @Protagonist 화자 일관성 검증
"""

# ── @Protagonist 정체성 ──
PROTAGONIST_IDENTITY = {
    "age":      "60대 중후반",
    "wisdom":   "서양 철학을 체화한 현자",
    "tone":     "조용하고 깊은 통찰, 가르치지 않음",
    "audience": "4070 세대",
}

# ── 금지 화자 톤 ──
FORBIDDEN_TONES = [
    "친구처럼", "동생처럼",  # 너무 가벼움
    "자기야", "여러분~",      # 너무 친근
    "고객님", "회원님",      # 영업 톤
    "강사", "코치",          # 자기계발 톤
]


def check_protagonist_voice(text: str) -> dict:
    """@Protagonist 톤 일관성 점검"""
    issues = []
    
    for forbidden in FORBIDDEN_TONES:
        if forbidden in text:
            issues.append(f"부적절 톤: '{forbidden}'")
    
    if "ㅋㅋ" in text or "ㅎㅎ" in text or "ㅠㅠ" in text:
        issues.append("4070 세대 부적합 표현 (자음 반복)")
    
    if "!" * 3 in text or "??" * 2 in text:
        issues.append("과도한 감정 표현")
    
    return {
        "consistent": len(issues) == 0,
        "issues": issues,
        "identity": PROTAGONIST_IDENTITY,
        "action": "재작성 권장" if issues else "통과",
    }
