# -*- coding: utf-8 -*-
"""
V17 Reborn 공통 설정 파일
- Part 이름
- 기본 로컬 모델
- API 키 로딩
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_env_value(key_name: str, default: str = "") -> str:
    """
    .env 파일에서 KEY=VALUE 형식의 값을 읽는다.
    python-dotenv 없이도 동작하게 만든 기본 함수.
    """
    if not ENV_PATH.exists():
        return default

    try:
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = ENV_PATH.read_text(encoding="cp949").splitlines()

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith(f"{key_name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")

    return default


PART_NAMES = {
    1: "Part 1 - 자료수집 / 벤치마킹",
    2: "Part 2 - 총괄기획",
    3: "Part 3 - 본작업 / 대본",
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


YOUTUBE_API_KEY = load_env_value("YOUTUBE_API_KEY")