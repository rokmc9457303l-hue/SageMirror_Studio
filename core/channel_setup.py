# -*- coding: utf-8 -*-
"""
core/channel_setup.py — 채널 생성 시 5개 MD 파일 자동 생성 (Tasks 22, 33)

새 채널 생성 시:
1. profiles/{key}.yaml 저장 (profile_loader 경유)
2. prompts/channels/{key}/ 폴더 + 5개 MD 생성
3. prompts/channels/_template/ 변수 치환
4. 옵시디언 Raw 채널 폴더 자동 생성
"""

from pathlib import Path
from core.config import PROMPTS_PATH


# 5개 MD 파일 이름
CHANNEL_MD_FILES = [
    "IDENTITY.md",
    "START_COMMAND.md",
    "TOPIC_RULES.md",
    "STYLE_GUIDE.md",
    "BENCHMARK_RULES.md",
]

TEMPLATE_DIR = PROMPTS_PATH / "channels" / "_template"


def _fmt_list(items) -> str:
    if isinstance(items, list):
        return "\n".join(f"- {i}" for i in items if i)
    return str(items) if items else ""


def create_channel_with_md(channel_key: str, config: dict) -> dict:
    """
    새 채널 생성:
    1. prompts/channels/{channel_key}/ 폴더 생성
    2. _template/ MD 파일 복사 + 변수 치환
    3. 옵시디언 Raw 채널 폴더 생성
    반환: {success, channel_folder, md_files, obsidian_folder}
    """
    channel_folder = PROMPTS_PATH / "channels" / channel_key
    channel_folder.mkdir(parents=True, exist_ok=True)

    created_files = []

    if TEMPLATE_DIR.exists():
        # 템플릿 복사 + 변수 치환
        variables = _build_variables(config)
        for tmpl_file in TEMPLATE_DIR.glob("*.md"):
            content = tmpl_file.read_text(encoding="utf-8")
            rendered = _substitute(content, variables)
            out_path = channel_folder / tmpl_file.name
            out_path.write_text(rendered, encoding="utf-8")
            created_files.append(tmpl_file.name)
    else:
        # 템플릿 없으면 직접 생성
        created_files = _write_md_files(channel_key, config, channel_folder)

    # 옵시디언 Raw 채널 폴더 생성
    obsidian_folder = _create_obsidian_folder(channel_key, config)

    # 캐시 무효화
    try:
        from core.md_loader import load_md
        load_md.clear()
    except Exception:
        pass

    return {
        "success":        True,
        "channel_folder": str(channel_folder),
        "md_files":       created_files,
        "obsidian_folder": obsidian_folder,
    }


def _build_variables(config: dict) -> dict:
    """config → {{변수}} 치환 딕셔너리"""
    def fmt(val):
        if isinstance(val, list):
            return ", ".join(str(v) for v in val if v)
        return str(val) if val else ""

    return {
        "CHANNEL_NAME":          fmt(config.get("channel_name", "")),
        "TARGET_AUDIENCE":       fmt(config.get("target_audience", "")),
        "TONE":                  fmt(config.get("tone", "")),
        "VISUAL_STYLE":          fmt(config.get("visual_style", "")),
        "TYPICAL_CATEGORIES":    fmt(config.get("typical_categories", [])),
        "TYPICAL_TOPICS":        fmt(config.get("typical_topics", [])),
        "FORBIDDEN_EXPRESSIONS": fmt(config.get("forbidden_expressions", [])),
        "PREFERRED_EXPRESSIONS": fmt(config.get("preferred_expressions", [])),
        "PHILOSOPHY_ANCHOR":     fmt(config.get("philosophy_anchor", [])),
        "NARRATOR_STYLE":        fmt(config.get("narrator_style", "")),
        "FORBIDDEN_TOPICS":      fmt(config.get("forbidden_topics", [])),
        "COLOR_PALETTE":         fmt(config.get("color_palette", "자동")),
        "CORE_SYMBOLS":          fmt(config.get("core_symbols", [])),
    }


def _substitute(text: str, variables: dict) -> str:
    for key, val in variables.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def _write_md_files(channel_key: str, config: dict, folder: Path) -> list:
    """템플릿 없을 때 직접 5개 MD 파일 생성"""
    ch  = config.get("channel_name", channel_key)
    tgt = config.get("target_audience", "")
    tone= config.get("tone", "")
    vis = config.get("visual_style", "")
    sym = _fmt_list(config.get("core_symbols", []))
    pal = config.get("color_palette", "자동")
    cats= _fmt_list(config.get("typical_categories", []))
    tops= _fmt_list(config.get("typical_topics", []))
    phil= _fmt_list(config.get("philosophy_anchor", []))
    forb= _fmt_list(config.get("forbidden_expressions", []))
    pref= _fmt_list(config.get("preferred_expressions", []))
    forb_topics = _fmt_list(config.get("forbidden_topics", []))

    files = {
        "IDENTITY.md": f"""# {ch} — 채널 정체성

## 채널 기본
- 채널명: {ch}
- 타깃 시청자: {tgt}
- 톤: {tone}
- 나레이션 스타일: {config.get('narrator_style', '')}

## 시각 정체성
- 시각 스타일: {vis}
- 핵심 상징: {sym}
- 색채 방향: {pal}

## 콘텐츠 정체성
- 주요 카테고리: {cats}
- 자주 다루는 주제:
{tops}
- 철학적 앵커: {phil}

## 표현 규칙
- 금지 표현:
{forb}
- 선호 표현:
{pref}

## 시청자 약속
- 채널 어조: {tone}
- 타깃 시청자: {tgt}
""",
        "START_COMMAND.md": f"""# "{ch}" 채널 — "시작" 명령 실행 프롬프트

사용자가 "시작" 입력 시 다음을 자동 실행:

## 1단계: 정체성 로드
- IDENTITY.md 전체 로드
- 이전 영상 최근 5편 자동 RAG

## 2단계: 떡상 채널 검색 (Librarian)
검색 기준:
- 카테고리: {cats}
- 구독자: 1만 이하
- 떡상 지수: 조회수/구독자 ≥ 5
- 댓글 밀도: 0.5% 이상
- 시청 유발 키워드 댓글 존재

## 3단계: 주제 발굴
- 댓글 200개 자동 수집
- {tgt}의 감정 고통 추출
- 채널 정체성 부합 주제만 필터링
- 최소 10개 주제 후보 + 댓글 근거

## 4단계: 사용자 선택 대기
- 주제 후보 표시
- 사용자: 1개 선택
- 선택 후 자동으로 Part 2 진입
""",
        "TOPIC_RULES.md": f"""# {ch} — 주제 선정 규칙

## 적합한 주제
{tops}

## 금지 주제
- 정치적 갈등
- 종교 분쟁
- 개인 비방
{forb_topics}

## 주제 필터
- {tgt}이 공감할 수 있는가
- 댓글 근거가 있는가
- 채널 정체성과 맞는가
- 이전 영상과 중복되지 않는가
""",
        "STYLE_GUIDE.md": f"""# {ch} — 스타일 가이드

## 어조
{tone}

## 어휘
- 선호:
{pref}
- 금지:
{forb}

## 문장 구조
- 짧고 호흡감 있게
- 감정 절정 직전 침묵(...)
- 클리셰 금지

## 시각 일관성
- 시각 스타일: {vis}
- 핵심 상징 반복:
{sym}
""",
        "BENCHMARK_RULES.md": f"""# {ch} — 벤치마킹 채널 선정 기준

## 발굴 조건
- 카테고리: {cats}
- 구독자 ≤ 10,000
- 떡상 지수 ≥ 5
- 댓글 밀도 ≥ 0.5%
- 업로드 6개월 이내 활동

## 추출 요소
- 시청 유지 장치
- 도입 5초 훅
- 감정 곡선
- 썸네일 기법
- 제목 패턴

## 금지
- 직접 복제
- 사례 그대로 인용
- 영상 구조 모방
""",
    }

    created = []
    for filename, content in files.items():
        (folder / filename).write_text(content, encoding="utf-8")
        created.append(filename)
    return created


def _create_obsidian_folder(channel_key: str, config: dict) -> str:
    """옵시디언 Raw 채널 폴더 생성"""
    try:
        from core.config import OBSIDIAN_RAW_NEW
        ch_name = config.get("channel_name", channel_key)
        folder  = OBSIDIAN_RAW_NEW / f"채널_{ch_name}"
        for sub in ("Part1_자료수집", "Part2_주제변환", "Part3_대본설계",
                    "Part4_이미지생성", "Part5_영상제작", "Part6_나레이션",
                    "Part7_편집연결", "Part8_최종완성"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        return str(folder)
    except Exception:
        return ""


def get_channel_md_status(channel_key: str) -> dict:
    """채널의 MD 파일 존재 여부 확인"""
    folder = PROMPTS_PATH / "channels" / channel_key
    status = {}
    for fname in CHANNEL_MD_FILES:
        status[fname] = (folder / fname).exists()
    return {"folder": str(folder), "files": status, "all_exist": all(status.values())}
