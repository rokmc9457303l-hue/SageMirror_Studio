# -*- coding: utf-8 -*-
"""
test_suno_lint.py — 수노 지시서 검사기 검증
════════════════════════════════════════════════════════════════════════
실행: python3 test_suno_lint.py

실제로 겪은 사고 6종이 정말로 잡히는지 확인한다.
표준 라이브러리만 쓴다. pytest 불필요.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from suno_lint import (  # noqa: E402
    BLOCK, FIXED, WARN,
    count_syllables, estimate_seconds, lint, strip_tags, is_tag_line,
)

_passed = 0
_failed = []


def check(label, condition, detail=""):
    global _passed
    if condition:
        _passed += 1
        print(f"  OK  {label}")
    else:
        _failed.append(f"{label} {detail}".strip())
        print(f"  X   {label} {detail}")


def codes(result):
    return {i.code for i in result.issues}


# ── 시료 ──────────────────────────────────────────────────────
GOOD_LYRICS = """[Verse 1]
현관 센서등이 나 대신 켜지고
식은 밥 두 공기가 그대로 있다

[Chorus]
잘 지내냐고 묻지를 못해서
문 앞에서 돌아섰다

[Outro]
[End]"""

GOOD_STYLE = "korean ballad, soft restrained verse, full crescendo chorus, piano and strings"


# ══════════════════════════════════════════════════════════════

def test_syllables():
    print("\n[1] 한글 음절 세기")
    check("한글 11음절", count_syllables("새벽 세시에 식은 밥 두 공기") == 11,
          f"(실제 {count_syllables('새벽 세시에 식은 밥 두 공기')})")
    check("공백과 부호는 안 셈", count_syllables("아, 그대여!") == count_syllables("아그대여"))
    check("영단어는 모음군", count_syllables("goodbye my love") == 5,
          f"(실제 {count_syllables('goodbye my love')})")
    check("숫자 1자 = 1음절", count_syllables("2026년") == 5, f"(실제 {count_syllables('2026년')})")
    check("빈 문자열은 0", count_syllables("") == 0)
    check("한영 혼합", count_syllables("사랑 forever") == 5, f"(실제 {count_syllables('사랑 forever')})")


def test_tags():
    print("\n[2] 구조 태그 인식")
    for tag in ["[Verse 1]", "(Chorus)", "[Pre-Chorus]", "[후렴]", "[Instrumental]",
                "[Bridge]", "[Outro]", "[Fade Out]", "[간주]"]:
        check(f"태그 인식: {tag}", is_tag_line(tag))
    check("가사 행은 태그 아님", not is_tag_line("현관 센서등이 나 대신 켜지고"))
    check("대괄호 문장은 태그 아님", not is_tag_line("[그대가 남긴 말이 아직도]"))
    check("strip_tags 가 태그를 뺌", "[Verse 1]" not in strip_tags(GOOD_LYRICS))
    check("strip_tags 가 가사는 남김", "현관 센서등이" in strip_tags(GOOD_LYRICS))


def test_clean_passes():
    print("\n[3] 멀쩡한 지시서는 통과해야 한다")
    r = lint(GOOD_LYRICS, GOOD_STYLE)
    check("통과", r.ok, f"(막힌 것: {[i.code for i in r.blocking]})")
    check("막힌 항목 없음", len(r.blocking) == 0)
    check("경고도 없음", len(r.warnings) == 0, f"(실제 {[i.code for i in r.warnings]})")


def test_instrumental_has_lyrics():
    print("\n[4] 사고 1 — 연주곡인데 가사가 나온다")
    r = lint(GOOD_LYRICS, "lofi piano, rain", instrumental=True)
    check("막힌다", not r.ok)
    check("원인을 짚는다", "INSTRUMENTAL_HAS_LYRICS" in codes(r))

    r2 = lint("", "lofi piano, gentle build, rain", instrumental=True)
    check("가사칸이 비면 통과", r2.ok, f"(막힌 것: {[i.code for i in r2.blocking]})")

    r3 = lint("[Instrumental]\n[Outro]", "lofi piano, soft swell", instrumental=True)
    check("태그만 있으면 통과", r3.ok, f"(막힌 것: {[i.code for i in r3.blocking]})")

    r4 = lint("", "lofi piano with female vocal", instrumental=True)
    check("연주곡 스타일에 보컬 단어가 있으면 막는다",
          "INSTRUMENTAL_VOCAL_STYLE" in codes(r4))


def test_live_keyword():
    print("\n[5] 사고 2 — 갑자기 떼창·라이브가 된다")
    for word in ["live recording", "crowd cheering", "arena rock", "stadium anthem",
                 "concert", "sing along", "떼창"]:
        r = lint(GOOD_LYRICS, f"korean ballad, {word}, soft build")
        check(f"막는다: {word}", not r.ok and "LIVE_KEYWORD" in codes(r))

    r = lint(GOOD_LYRICS, "korean ballad, live, gentle")
    hint = next(i.hint for i in r.issues if i.code == "LIVE_KEYWORD")
    check("고친 스타일을 제안한다", "live" not in hint.split("→")[-1].lower())

    # 단어 경계 — olive 의 live 를 잡으면 안 된다
    r2 = lint(GOOD_LYRICS, "olive grove ambience, soft swell")
    check("olive 를 live 로 오인하지 않는다", "LIVE_KEYWORD" not in codes(r2))

    r3 = lint(GOOD_LYRICS, "delivery truck sounds, quiet")
    check("delivery 를 live 로 오인하지 않는다", "LIVE_KEYWORD" not in codes(r3))


def test_blank_lines():
    print("\n[6] 사고 3 — 중간에 무음 구간이 생긴다")
    gappy = "[Verse 1]\n\n첫 줄\n\n\n\n둘째 줄\n\n[Outro]\n[End]"
    r = lint(gappy, GOOD_STYLE)
    check("빈 줄을 잡는다", "BLANK_LINES" in codes(r))
    check("자동으로 고친다", any(i.code == "BLANK_LINES" and i.severity == FIXED for i in r.issues))
    check("연속 빈 줄이 사라짐", "\n\n\n" not in r.lyrics)
    check("태그 다음 빈 줄이 사라짐", "[Verse 1]\n\n" not in r.lyrics)
    check("가사는 그대로 남음", "첫 줄" in r.lyrics and "둘째 줄" in r.lyrics)
    check("구간 사이 빈 줄 하나는 남김", "\n\n" in r.lyrics)

    r2 = lint(gappy, GOOD_STYLE, autofix=False)
    check("autofix 를 끄면 경고만", any(
        i.code == "BLANK_LINES" and i.severity == WARN for i in r2.issues))
    check("autofix 를 끄면 가사를 안 건드림", r2.lyrics == gappy)


def test_end_tag():
    print("\n[7] 사고 4 — 끝났다가 다시 시작한다")
    no_end = "[Verse 1]\n첫 줄\n\n[Chorus]\n후렴 줄"
    r = lint(no_end, GOOD_STYLE)
    check("종료 태그 없음을 잡는다", "NO_END_TAG" in codes(r))
    check("자동으로 넣는다", any(i.code == "NO_END_TAG" and i.severity == FIXED for i in r.issues))
    check("[Outro] 가 들어감", "[Outro]" in r.lyrics)
    check("[End] 가 들어감", "[End]" in r.lyrics)

    check("이미 있으면 안 건드림", "NO_END_TAG" not in codes(lint(GOOD_LYRICS, GOOD_STYLE)))
    check("Fade Out 도 종료로 인정",
          "NO_END_TAG" not in codes(lint("[Verse]\n줄\n[Fade Out]", GOOD_STYLE)))

    r2 = lint(no_end, GOOD_STYLE, autofix=False)
    check("autofix 를 끄면 경고만", any(
        i.code == "NO_END_TAG" and i.severity == WARN for i in r2.issues))


def test_too_long():
    print("\n[8] 사고 5 — 마지막이 잘린다")
    long_lyrics = "[Verse 1]\n" + "\n".join(["열두 음절짜리 가사가 여기에"] * 60) + "\n[Outro]\n[End]"
    r = lint(long_lyrics, GOOD_STYLE, max_seconds=240)
    check("길이 초과를 잡는다", "TOO_LONG" in codes(r))
    check("막지는 않고 경고", r.ok)

    issue = next(i for i in r.issues if i.code == "TOO_LONG")
    check("얼마나 줄일지 알려준다", "음절" in issue.hint)

    check("짧은 곡은 통과", "TOO_LONG" not in codes(lint(GOOD_LYRICS, GOOD_STYLE, max_seconds=240)))
    check("한도를 낮추면 잡힌다", "TOO_LONG" in codes(lint(GOOD_LYRICS, GOOD_STYLE, max_seconds=5)))
    check("길이 어림이 태그를 안 셈",
          estimate_seconds("[Verse 1]\n[Chorus]\n[Outro]") == 0)


def test_dynamics():
    print("\n[9] 사고 6 — 곡이 밋밋하다")
    r = lint(GOOD_LYRICS, "korean ballad, piano")
    check("강약 지시 없음을 잡는다", "NO_DYNAMICS" in codes(r))
    check("막지는 않고 경고", r.ok)
    check("예시를 준다", "예:" in next(i for i in r.issues if i.code == "NO_DYNAMICS").hint)

    check("영어 강약어를 인정", "NO_DYNAMICS" not in codes(lint(GOOD_LYRICS, GOOD_STYLE)))
    check("한국어 강약어를 인정",
          "NO_DYNAMICS" not in codes(lint(GOOD_LYRICS, "발라드, 잔잔하게 시작해 후렴에서 고조")))


def test_result_shape():
    print("\n[10] 결과 자료형")
    r = lint(GOOD_LYRICS, "korean ballad, live, piano", instrumental=True)
    check("막힌 것과 경고를 나눠서 준다", len(r.blocking) > 0)
    check("blocking 은 전부 block", all(i.severity == BLOCK for i in r.blocking))
    check("warnings 는 전부 warn", all(i.severity == WARN for i in r.warnings))
    check("fixes 는 전부 fixed", all(i.severity == FIXED for i in r.fixes))
    check("음절 수를 준다", r.syllables > 0)
    check("길이 어림을 준다", r.est_seconds > 0)

    text = r.report()
    check("보고서에 결론이 있다", "내보낼 수 없음" in text)
    check("보고서에 음절이 있다", "음절" in text)
    check("통과 보고서", "통과" in lint(GOOD_LYRICS, GOOD_STYLE).report())


def test_edge_cases():
    print("\n[11] 가장자리")
    r = lint("", "")
    check("전부 비어도 안 죽는다", isinstance(r.ok, bool))

    r2 = lint(None, None)
    check("None 이 와도 안 죽는다", isinstance(r2.ok, bool))

    r3 = lint("[Verse]\n줄", GOOD_STYLE)
    check("반환한 가사는 문자열", isinstance(r3.lyrics, str))
    check("반환한 스타일은 문자열", isinstance(r3.style, str))

    # 두 번 걸어도 결과가 같아야 한다
    once = lint(GOOD_LYRICS, GOOD_STYLE)
    twice = lint(once.lyrics, once.style)
    check("두 번 걸어도 같다", once.lyrics == twice.lyrics)

    # 여러 사고가 동시에
    bad = lint("가사가 남았다", "live crowd vocal", instrumental=True)
    check("여러 사고를 동시에 잡는다", len(bad.blocking) >= 2,
          f"(실제 {[i.code for i in bad.blocking]})")


def test_no_paid_dependency():
    print("\n[12] 비용 0원 — 외부 의존성 없음")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "suno_lint.py"), encoding="utf-8") as f:
        src = f.read().lower()
    for token in ("anthropic", "openai", "requests", "httpx", "urllib",
                  "gemini", "tavily", "socket", "ollama"):
        check(f"'{token}' 미사용", token not in src)


if __name__ == "__main__":
    print("=" * 60)
    print("수노 지시서 검사기 — 검증")
    print("=" * 60)

    test_syllables()
    test_tags()
    test_clean_passes()
    test_instrumental_has_lyrics()
    test_live_keyword()
    test_blank_lines()
    test_end_tag()
    test_too_long()
    test_dynamics()
    test_result_shape()
    test_edge_cases()
    test_no_paid_dependency()

    print("\n" + "=" * 60)
    if _failed:
        print(f"실패 {len(_failed)}건 / 통과 {_passed}건")
        for f_ in _failed:
            print(f"  X {f_}")
        sys.exit(1)
    print(f"전부 통과 — {_passed}건")
    print("=" * 60)
