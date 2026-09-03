# -*- coding: utf-8 -*-
"""
suno_lint.py — 수노 지시서 사고 검사기 v1.0
════════════════════════════════════════════════════════════════════════

수노에 던지기 전에 지시서를 검사한다. 실제로 겪은 사고 6종을 막는다.

  1. 연주곡을 뽑았는데 가사가 나온다
  2. 가사곡인데 갑자기 떼창·라이브가 된다
  3. 곡 중간에 무음 구간이 생긴다
  4. 곡이 끝났다가 10초쯤 뒤에 다시 시작하다 뚝 멈춘다
  5. 마지막 부분에서 갑자기 잘려서 멈춘다
  6. 곡이 밋밋하다

왜 AI 를 쓰지 않는가
--------------------
이 여섯 가지는 전부 규칙으로 잡힌다. 규칙은 100% 재현되고 비용이 0이다.
AI 로 검사하면 어떤 날은 잡고 어떤 날은 놓친다. 그리고 돈이 나간다.

의존성: 표준 라이브러리만. 어떤 앱에든 그대로 넣어 쓸 수 있다.

사용법
------
    from suno_lint import lint

    result = lint(lyrics, style, instrumental=False)
    if not result.ok:
        for issue in result.blocking:
            print(issue.message)
        return                      # 내보내지 않는다

    send_to_suno(result.lyrics, result.style)   # 자동 수정이 적용된 것
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

__all__ = [
    "lint", "Issue", "LintResult",
    "count_syllables", "estimate_seconds",
    "BLOCK", "WARN", "FIXED",
]

BLOCK = "block"   # 이게 하나라도 있으면 내보내면 안 된다
WARN = "warn"     # 사람이 보고 판단한다
FIXED = "fixed"   # 자동으로 고쳤다


# ══════════════════════════════════════════════════════════════
# SECTION 1 — 한글 음절 세기
# ══════════════════════════════════════════════════════════════
# 한국어 가사는 음절 수가 곧 노래 길이다. 이걸로 곡이 잘릴지 미리 안다.

_HANGUL_FIRST = 0xAC00
_HANGUL_LAST = 0xD7A3
_EN_VOWEL_GROUP = re.compile(r"[aeiouy]+", re.I)


def count_syllables(text: str) -> int:
    """
    가창 음절 수를 센다.
      한글 완성형 1자 = 1음절
      숫자 1자 = 1음절
      영단어 = 모음군 수 (최소 1)
    공백과 문장부호는 세지 않는다.
    """
    if not text:
        return 0

    count = 0
    for ch in text:
        code = ord(ch)
        if _HANGUL_FIRST <= code <= _HANGUL_LAST:
            count += 1
        elif ch.isdigit():
            count += 1

    for word in re.findall(r"[A-Za-z]+", text):
        count += max(1, len(_EN_VOWEL_GROUP.findall(word)))

    return count


# 중간 템포 한국어 가창의 대략적인 속도.
# 정확한 값이 아니라 "확실히 넘칠 때"를 잡기 위한 눈금이다.
SYLLABLES_PER_SECOND = 2.5


def estimate_seconds(lyrics: str, rate: float = SYLLABLES_PER_SECOND) -> float:
    """
    가사만으로 노래의 최소 길이를 어림한다.
    간주와 반복은 빠져 있으므로 이 값은 항상 실제보다 짧다.
    즉 이 값이 이미 한도를 넘으면 곡은 반드시 잘린다.
    """
    return count_syllables(strip_tags(lyrics)) / max(rate, 0.1)


# ══════════════════════════════════════════════════════════════
# SECTION 2 — 구조 태그
# ══════════════════════════════════════════════════════════════

# [Verse 1], (Chorus), [후렴] 같은 구조 표기
_TAG_LINE = re.compile(
    r"^\s*[\[\(]\s*"
    r"(verse|pre[\s\-]?chorus|chorus|hook|bridge|intro|outro|refrain|interlude|"
    r"instrumental|inst|solo|break|drop|end|fade\s*out|ad[\s\-]?lib|"
    r"후렴|벌스|브릿지|간주|도입|전주|아웃트로|끝)"
    r"[^\]\)]*[\]\)]\s*[:：]?\s*$",
    re.I,
)

# 곡이 끝났음을 수노에게 알리는 태그. 이게 없으면 모델이 곡을 다시 시작한다.
_END_TAG = re.compile(r"[\[\(]\s*(outro|end|fade\s*out|ending|아웃트로|끝)\b", re.I)


def is_tag_line(line: str) -> bool:
    """구조 표기 행인가."""
    return bool(_TAG_LINE.match(line or ""))


def strip_tags(lyrics: str) -> str:
    """구조 표기를 뺀 실제 가창 부분만 남긴다."""
    return "\n".join(
        line for line in (lyrics or "").splitlines()
        if line.strip() and not is_tag_line(line)
    )


# ══════════════════════════════════════════════════════════════
# SECTION 3 — 금지어
# ══════════════════════════════════════════════════════════════

# 이 단어들이 스타일 문구에 있으면 수노가 관객 소리와 떼창을 넣는다.
LIVE_WORDS = [
    "live", "crowd", "audience", "arena", "stadium", "concert",
    "cheering", "applause", "clapping", "sing along", "singalong",
    "festival", "encore", "라이브", "떼창", "관객", "함성",
]

# 연주곡인데 이 단어들이 있으면 수노가 보컬을 넣는다.
VOCAL_WORDS = [
    "vocal", "singer", "sung", "singing", "lyrics", "voice",
    "choir", "harmony", "rap", "verse", "chorus",
    "보컬", "가수", "노래", "가사",
]

# 곡의 강약을 지시하는 말. 하나도 없으면 밋밋해진다.
DYNAMICS_WORDS = [
    "build", "swell", "crescendo", "drop", "quiet", "soft", "loud",
    "intense", "gentle", "sparse", "full", "climax", "restrained",
    "dynamic", "layered", "stripped", "powerful", "whisper",
    "고조", "잔잔", "폭발", "절정", "속삭", "웅장",
]


def _find_words(text: str, words: List[str]) -> List[str]:
    """본문에 실제로 등장한 단어를 찾는다. 영단어는 단어 경계를 지킨다."""
    low = (text or "").lower()
    hits = []
    for word in words:
        w = word.lower()
        if re.search(r"[a-z]", w):
            if re.search(rf"\b{re.escape(w)}\b", low):
                hits.append(word)
        elif w in low:
            hits.append(word)
    return hits


def _remove_words(text: str, words: List[str]) -> str:
    """스타일 문구에서 금지어를 걷어내고 남은 구두점을 정리한다."""
    out = text or ""
    for word in words:
        if re.search(r"[a-zA-Z]", word):
            out = re.sub(rf"\b{re.escape(word)}\b", "", out, flags=re.I)
        else:
            out = out.replace(word, "")
    out = re.sub(r"\s*,\s*,+", ", ", out)      # 빈 항목이 남긴 쉼표
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip(" ,\t\n")


# ══════════════════════════════════════════════════════════════
# SECTION 4 — 결과 자료형
# ══════════════════════════════════════════════════════════════

@dataclass
class Issue:
    code: str
    severity: str
    message: str
    hint: str = ""

    def __str__(self) -> str:
        mark = {BLOCK: "[막음]", WARN: "[주의]", FIXED: "[고침]"}.get(self.severity, "")
        return f"{mark} {self.message}" + (f"\n      → {self.hint}" if self.hint else "")


@dataclass
class LintResult:
    ok: bool
    lyrics: str
    style: str
    issues: List[Issue] = field(default_factory=list)
    est_seconds: float = 0.0
    syllables: int = 0

    @property
    def blocking(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == BLOCK]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == WARN]

    @property
    def fixes(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == FIXED]

    def report(self) -> str:
        """사람이 읽는 검사 보고서."""
        head = "통과" if self.ok else f"내보낼 수 없음 — 막힌 항목 {len(self.blocking)}건"
        lines = [
            f"수노 지시서 검사: {head}",
            f"  음절 {self.syllables}개 · 최소 길이 약 {self.est_seconds:.0f}초",
        ]
        if self.issues:
            lines.append("")
            lines.extend(f"  {issue}" for issue in self.issues)
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# SECTION 5 — 검사
# ══════════════════════════════════════════════════════════════

def lint(
    lyrics: str,
    style: str,
    *,
    instrumental: bool = False,
    max_seconds: float = 240.0,
    autofix: bool = True,
) -> LintResult:
    """
    수노 지시서를 검사하고, 고칠 수 있는 것은 고쳐서 돌려준다.

    lyrics       : 가사 (연주곡이면 비어 있어야 한다)
    style        : 스타일 프롬프트
    instrumental : 연주곡이면 True
    max_seconds  : 곡 길이 한도. 넘으면 경고
    autofix      : 빈 줄 정리와 종료 태그 삽입을 자동으로 할지

    반환한 LintResult 의 .ok 가 False 면 내보내지 말 것.
    """
    issues: List[Issue] = []
    out_lyrics = lyrics or ""
    out_style = style or ""

    # ── 1. 연주곡인데 가사가 있다 ─────────────────────────────
    if instrumental:
        sung = strip_tags(out_lyrics)
        if re.search(r"[가-힣A-Za-z]", sung):
            preview = sung.strip().splitlines()[0][:40]
            issues.append(Issue(
                "INSTRUMENTAL_HAS_LYRICS", BLOCK,
                "연주곡인데 가사칸에 글자가 남아 있습니다.",
                f"이대로 보내면 노래가 나옵니다. 가사칸을 비우십시오. (남은 글: {preview}...)",
            ))

        vocal_hits = _find_words(out_style, VOCAL_WORDS)
        if vocal_hits:
            issues.append(Issue(
                "INSTRUMENTAL_VOCAL_STYLE", BLOCK,
                f"연주곡인데 스타일에 보컬을 부르는 말이 있습니다: {', '.join(vocal_hits)}",
                "이 단어들을 빼고 instrumental 을 넣으십시오.",
            ))

    # ── 2. 떼창·라이브 ────────────────────────────────────────
    live_hits = _find_words(out_style, LIVE_WORDS)
    if live_hits:
        cleaned = _remove_words(out_style, live_hits)
        issues.append(Issue(
            "LIVE_KEYWORD", BLOCK,
            f"스타일에 라이브·관객을 부르는 말이 있습니다: {', '.join(live_hits)}",
            f"이게 떼창의 원인입니다. 빼면 이렇게 됩니다 → {cleaned or '(비어 있음)'}",
        ))

    # ── 3. 중간 무음 ──────────────────────────────────────────
    if _has_gap(out_lyrics):
        if autofix:
            out_lyrics = _fix_gaps(out_lyrics)
            issues.append(Issue(
                "BLANK_LINES", FIXED,
                "구조 태그 사이의 빈 줄을 정리했습니다.",
                "빈 줄이 많으면 곡 중간에 무음 구간이 생깁니다.",
            ))
        else:
            issues.append(Issue(
                "BLANK_LINES", WARN,
                "빈 줄이 겹쳐 있어 무음 구간이 생길 수 있습니다.",
            ))

    # ── 4. 종료 태그 없음 ─────────────────────────────────────
    if not instrumental or strip_tags(out_lyrics).strip():
        if not _END_TAG.search(out_lyrics):
            if autofix:
                out_lyrics = out_lyrics.rstrip() + "\n\n[Outro]\n[End]"
                issues.append(Issue(
                    "NO_END_TAG", FIXED,
                    "종료 태그가 없어 [Outro] 와 [End] 를 넣었습니다.",
                    "이게 없으면 곡이 끝났다가 다시 시작합니다.",
                ))
            else:
                issues.append(Issue(
                    "NO_END_TAG", WARN,
                    "종료 태그가 없습니다. 곡이 끝났다 다시 시작할 수 있습니다.",
                ))

    # ── 5. 길이 초과 ──────────────────────────────────────────
    syllables = count_syllables(strip_tags(out_lyrics))
    est = estimate_seconds(out_lyrics)
    if est > max_seconds:
        over = int(est - max_seconds)
        cut = int(over * SYLLABLES_PER_SECOND)
        issues.append(Issue(
            "TOO_LONG", WARN,
            f"가사가 깁니다. 최소 {est:.0f}초인데 한도는 {max_seconds:.0f}초입니다.",
            f"약 {over}초 초과. 음절 {cut}개쯤 줄이거나 extend 를 쓰십시오. "
            f"이대로면 마지막이 잘립니다.",
        ))

    # ── 6. 밋밋함 ─────────────────────────────────────────────
    if not _find_words(out_style, DYNAMICS_WORDS):
        issues.append(Issue(
            "NO_DYNAMICS", WARN,
            "스타일에 강약 지시가 없습니다.",
            "벌스는 잔잔하게, 후렴은 고조되게 같은 말을 넣으면 밋밋함이 줄어듭니다. "
            "예: soft restrained verse, full crescendo chorus",
        ))

    blocking = [i for i in issues if i.severity == BLOCK]
    return LintResult(
        ok=not blocking,
        lyrics=out_lyrics,
        style=out_style,
        issues=issues,
        est_seconds=est,
        syllables=syllables,
    )


# ══════════════════════════════════════════════════════════════
# SECTION 6 — 빈 줄 처리
# ══════════════════════════════════════════════════════════════

def _has_gap(lyrics: str) -> bool:
    """무음을 만들 만한 빈 줄이 있는가."""
    lines = (lyrics or "").splitlines()

    blank_run = 0
    for i, line in enumerate(lines):
        if line.strip():
            blank_run = 0
            continue
        blank_run += 1
        if blank_run >= 2:
            return True
        # 태그 바로 다음의 빈 줄도 무음을 만든다
        if i > 0 and is_tag_line(lines[i - 1]):
            return True
    return False


def _fix_gaps(lyrics: str) -> str:
    """
    빈 줄을 정리한다.
      - 태그 바로 다음의 빈 줄은 없앤다
      - 연속된 빈 줄은 하나로 줄인다
      - 앞뒤 공백을 없앤다
    구간 사이의 빈 줄 하나는 남긴다. 그건 무음이 아니라 구분이다.
    """
    lines = (lyrics or "").splitlines()
    out: List[str] = []

    for line in lines:
        if line.strip():
            out.append(line.rstrip())
            continue
        if not out:                          # 맨 앞 빈 줄
            continue
        if is_tag_line(out[-1]):             # 태그 바로 다음
            continue
        if not out[-1].strip():              # 이미 빈 줄
            continue
        out.append("")

    while out and not out[-1].strip():
        out.pop()

    return "\n".join(out)


# ══════════════════════════════════════════════════════════════
# SECTION 7 — 명령줄에서 바로 쓰기
# ══════════════════════════════════════════════════════════════

def main(argv: Optional[List[str]] = None) -> int:
    """
    사용법:
        python suno_lint.py 가사파일.txt "스타일 문구"
        python suno_lint.py --instrumental 가사파일.txt "lofi piano"
    """
    import sys
    args = list(argv if argv is not None else sys.argv[1:])

    instrumental = False
    if "--instrumental" in args:
        instrumental = True
        args.remove("--instrumental")

    if not args:
        print(main.__doc__)
        return 2

    lyrics_path = args[0]
    style = args[1] if len(args) > 1 else ""

    try:
        with open(lyrics_path, "r", encoding="utf-8") as f:
            lyrics = f.read()
    except OSError as exc:
        print(f"가사 파일을 읽지 못했습니다: {exc}")
        return 2

    result = lint(lyrics, style, instrumental=instrumental)
    print(result.report())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
