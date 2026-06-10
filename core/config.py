# -*- coding: utf-8 -*-
"""
core/config.py — 경로·설정 중앙 관리
"""

from pathlib import Path

# ── 기본 경로 ─────────────────────────────────────
BASE_PATH         = Path(r"C:\SageMirror_Studio_v18")
DATA_PATH         = BASE_PATH / "data"
PROMPTS_PATH      = BASE_PATH / "prompts"

# ── 옵시디언 (기존 데이터 재사용) ────────────────
OBSIDIAN_PATH     = Path(r"C:\SageMirror_Production\00_Obsidian_Archive")
OBSIDIAN_CHANNEL  = OBSIDIAN_PATH / "채널_현자의거울"
OBSIDIAN_UNIVERSAL = OBSIDIAN_PATH / "범용카테고리"
OBSIDIAN_SYSTEM   = OBSIDIAN_PATH / "시스템"

# ── 앱 정보 ───────────────────────────────────────
APP_NAME    = "현자의 거울 스튜디오"
APP_VERSION       = "v18.0.37"
APP_PORT    = 8506

# ── 8파트 한글 이름 ───────────────────────────────
PART_NAMES = {
    1: "자료수집",
    2: "총괄기획",
    3: "대본작성",
    4: "이미지생성",
    5: "영상생성",
    6: "나레이션·배경음악",
    7: "숏폼생성",
    8: "최종조립",
}

# ── 모델 설정 ─────────────────────────────────────
MODELS = {
    "gemma4:e2b":       {"label": "Gemma 4 e2b", "type": "local",  "desc": "로컬 기본"},
    "gemma4:e4b":       {"label": "Gemma 4 e4b", "type": "local",  "desc": "로컬 강화"},
    "gemini-2.5-flash": {"label": "Gemini Flash", "type": "remote", "desc": "자료조사 보조"},
}
DEFAULT_MODEL = "gemma4:e2b"

# ── 16개 범용 카테고리 ────────────────────────────
UNIVERSAL_CATEGORIES = [
    "감정", "철학", "다크심리학", "성경·신앙",
    "심리학", "문학·에세이", "고전소설", "한국문학",
    "인생단계", "역사·인물", "경제·비즈니스", "건강·생활",
    "유튜브전략", "채널운영", "제작자료", "출처자료",
]

# ── API 키 (초기값, 사이드바에서 입력) ────────────
API_KEYS = {
    "tavily":   "",
    "youtube":  "",
    "gemini":   "",
    "github":   "",
}
