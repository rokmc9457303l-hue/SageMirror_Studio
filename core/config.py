# -*- coding: utf-8 -*-
"""
core/config.py — 경로·설정 중앙 관리
"""

from pathlib import Path

# ── 기본 경로 ─────────────────────────────────────
BASE_PATH         = Path(r"C:\SageMirror_Studio_v18")
DATA_PATH         = BASE_PATH / "data"
PROMPTS_PATH      = BASE_PATH / "prompts"

# ── 옵시디언 ─────────────────────────────────────
OBSIDIAN_PATH     = Path(r"C:\SageMirror_Production\00_Obsidian")
OBSIDIAN_RAW      = OBSIDIAN_PATH / "01_Raw_Data"
OBSIDIAN_WIKI     = OBSIDIAN_PATH / "01_Wiki"
OBSIDIAN_SCHEMA   = OBSIDIAN_PATH / "02_Schema"
OBSIDIAN_ARCHIVE  = OBSIDIAN_RAW  / "99_과거_아카이브_통합"
OBSIDIAN_CHANNEL  = OBSIDIAN_RAW               # 채널별 경로는 get_channel_path() 사용
OBSIDIAN_UNIVERSAL = OBSIDIAN_PATH / "범용카테고리"
OBSIDIAN_SYSTEM    = OBSIDIAN_PATH / "시스템"
OBSIDIAN_LOGS      = OBSIDIAN_PATH / "03_Logs"
OBSIDIAN_RAW_NEW   = OBSIDIAN_PATH / "00_Raw_Data"

# ── 채널 기본값 (사이드바에서 변경 가능) ──────────
CHANNEL_NAME = ""          # 채널명은 Profile에서 동적 로드 (하드코딩 금지)

# ── 앱 정보 ───────────────────────────────────────
APP_NAME    = "SAGE Studio"
APP_VERSION = "v100.0.0"
APP_PORT    = 8506

# ── 8파트 한글 이름 ───────────────────────────────
PART_NAMES = {
    1: "자료수집",
    2: "주제변환",
    3: "대본설계",
    4: "이미지생성",
    5: "영상제작",
    6: "나레이션",
    7: "편집연결",
    8: "최종완성",
}

# ── 모델 설정 ─────────────────────────────────────
MODELS = {
    "gemma4:e2b":       {"label": "Gemma 4 e2b",   "type": "local",  "desc": "로컬 기본"},
    "gemma4:e4b":       {"label": "Gemma 4 e4b",   "type": "local",  "desc": "로컬 강화"},
    "gemini-2.5-flash": {"label": "Gemini Flash",  "type": "remote", "desc": "자료조사 보조"},
    "gemini-2.5-pro":   {"label": "App Research",  "type": "remote", "desc": "심층 연구용"},
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
