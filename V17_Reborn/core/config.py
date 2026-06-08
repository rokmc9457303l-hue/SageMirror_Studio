# -*- coding: utf-8 -*-
"""
core/config.py
V17 Reborn 기본 설정
"""

from pathlib import Path

APP_NAME = "현자의 거울 V17 Reborn"
APP_VERSION = "v17.reborn.0.1"

BASE_DIR = Path(r"C:\SageMirror_Production\V17_Reborn")

OBSIDIAN_BASE = Path(r"C:\SageMirror_Production\00_Obsidian\V17_Reborn")
OUTPUT_BASE = Path(r"C:\SageMirror_Outputs\V17_Reborn")

WORKSPACE_FILE = BASE_DIR / "data" / "workspace_state.json"

PART_NAMES = {
    1: "Part 1 - 자료수집 / 벤치마킹",
    2: "Part 2 - 총괄기획",
    3: "Part 3 - 대본작성",
    4: "Part 4 - 이미지 설계",
    5: "Part 5 - 영상 설계",
    6: "Part 6 - 나레이션 / BGM",
    7: "Part 7 - 숏폼",
    8: "Part 8 - 최종 조립",
}

DEFAULT_MODEL = "gemma4:e2b"

MODELS = {
    "gemma4:e2b": {
        "label": "Gemma4 E2B",
        "desc": "가벼운 기본 모델",
    },
    "gemma4:e4b": {
        "label": "Gemma4 E4B",
        "desc": "조금 더 깊은 분석용 모델",
    },
}