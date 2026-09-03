# -*- coding: utf-8 -*-
"""
claude_bridge.py — 앱과 클로드 코드를 잇는 다리 v1.0
════════════════════════════════════════════════════════════════════════

이 파일이 하는 일 하나: **앱에서 클로드 API 호출을 없앤다.**

    [지금]   앱 ──HTTP──▶ Claude API ──▶ 응답        곡당 100원
    [바꾼 뒤] 앱 ──subprocess──▶ claude -p ──▶ 파일   0원

같은 클로드인데 API 로 부르면 토큰 과금이 나가고,
클로드 코드 CLI 로 부르면 구독 안이라 돈이 안 나간다.

같이 해결되는 것 — 20곡 배치가 통째로 날아가는 문제
------------------------------------------------------
곡 하나가 끝날 때마다 즉시 파일로 떨어뜨린다.
7번째에서 죽어도 1~6번은 남아 있고, 다시 누르면 8번부터 이어간다.

의존성: 표준 라이브러리만.

사용법
------
    from claude_bridge import ClaudeBridge

    bridge = ClaudeBridge(work_dir="work")

    if not bridge.available():
        print(bridge.install_hint())      # CLI 가 없으면 파일 방식으로 안내

    result = bridge.generate_batch(specs, on_progress=print)
    print(f"성공 {len(result.done)} / 실패 {len(result.failed)}")
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

__all__ = ["ClaudeBridge", "SongSpec", "BatchResult", "BridgeError"]


class BridgeError(RuntimeError):
    """클로드 코드 호출이 실패했다."""


# ══════════════════════════════════════════════════════════════
# SECTION 1 — 곡 하나의 요청서
# ══════════════════════════════════════════════════════════════

@dataclass
class SongSpec:
    """
    곡 하나를 만들기 위해 필요한 전부.
    앱의 앞 파트들이 이걸 채워서 넘긴다.
    """
    song_id: str
    topic: str                                  # 이번 곡의 주제
    genre: str = ""                             # 장르
    instrumental: bool = False                  # 연주곡인가

    # 채널 정체성 — 안 바뀌는 것
    channel_name: str = ""
    identity_line: str = ""                     # 이 채널은 ___ 채널이다
    audience: str = ""
    voice_rules: List[str] = field(default_factory=list)
    forbidden: List[str] = field(default_factory=list)
    singer: str = ""                            # 대표 가수 설명

    # 옵시디언 발췌 — 3~4개만. 많으면 가사가 산문이 된다
    source_excerpts: List[Dict[str, str]] = field(default_factory=list)

    # 곡 규격
    language: str = "한국어"
    max_seconds: int = 240
    syllables_per_line: str = "6~12"

    def to_dict(self) -> Dict:
        return {
            "song_id": self.song_id, "topic": self.topic, "genre": self.genre,
            "instrumental": self.instrumental, "channel_name": self.channel_name,
            "identity_line": self.identity_line, "audience": self.audience,
            "voice_rules": self.voice_rules, "forbidden": self.forbidden,
            "singer": self.singer, "source_excerpts": self.source_excerpts,
            "language": self.language, "max_seconds": self.max_seconds,
            "syllables_per_line": self.syllables_per_line,
        }


@dataclass
class BatchResult:
    done: List[str] = field(default_factory=list)      # 성공한 song_id
    failed: List[Dict[str, str]] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)   # 이미 있어서 건너뜀

    @property
    def ok(self) -> bool:
        return not self.failed


# ══════════════════════════════════════════════════════════════
# SECTION 2 — 프롬프트
# ══════════════════════════════════════════════════════════════
# 가사 품질이 여기서 갈린다. 두 가지가 핵심이다.
#   1. 옵시디언 자료를 인용하지 말고 장면만 뽑게 한다
#   2. 수노 사고 6종을 애초에 안 만들게 규칙을 준다

_AI_CLICHES = [
    "밤하늘의 별", "흘러가는 시간", "마음 속 깊은 곳", "눈물이 흘러",
    "바람에 실려", "영원히 함께", "빛나는 순간", "끝없는 여정",
    "가슴 깊이", "별처럼 빛나", "운명처럼", "세상 끝에서",
]


def build_prompt(spec: SongSpec, out_path: Path) -> str:
    """클로드 코드에 던질 프롬프트를 만든다."""
    p: List[str] = []

    p.append("너는 유튜브 음악 채널의 작사가다. 곡 하나의 가사와 수노 지시서를 쓴다.\n")

    # ── 채널 정체성 ──
    p.append("## 채널")
    if spec.channel_name:
        p.append(f"- 이름: {spec.channel_name}")
    if spec.identity_line:
        p.append(f"- 정체성: 이 채널은 {spec.identity_line} 채널이다.")
    if spec.audience:
        p.append(f"- 시청자: {spec.audience}")
    if spec.genre:
        p.append(f"- 장르: {spec.genre}")
    if spec.singer and not spec.instrumental:
        p.append(f"- 대표 가수: {spec.singer}")
    p.append("")

    p.append("## 이번 곡")
    p.append(f"- 주제: {spec.topic}")
    p.append(f"- 언어: {spec.language}")
    p.append(f"- 형태: {'연주곡 (가사 없음)' if spec.instrumental else '가사 있는 곡'}")
    p.append("")

    # ── 옵시디언 발췌 ──
    if spec.source_excerpts:
        p.append("## 참고 자료")
        p.append("아래는 작가의 자료에서 뽑은 대목이다.\n")
        for i, ex in enumerate(spec.source_excerpts[:4], 1):
            src = ex.get("source", "출처 미상")
            text = (ex.get("text", "") or "").strip()
            p.append(f"[{i}] {src}")
            p.append(f"    {text}")
        p.append("")
        p.append("**이 자료를 쓰는 방법 — 이걸 어기면 가사가 망가진다:**")
        p.append("- 문장을 그대로 가져오지 마라. 시의 리듬과 노래의 리듬은 다르다.")
        p.append("- 자료에서 **구체적인 장면과 사물만** 뽑아 써라.")
        p.append("- 개념어를 가사에 넣지 마라. '고독'이 아니라 '식은 밥 두 공기'다.")
        p.append("- 자료 4개 중 2~3개만 써도 된다. 억지로 다 넣지 마라.")
        p.append("")

    # ── 금지 ──
    p.append("## 절대 금지")
    p.append("- 아래 상투구는 하나도 쓰지 마라. AI 가사의 표시다:")
    p.append(f"  {', '.join(_AI_CLICHES)}")
    p.append("- 추상 명사로 감정을 말하지 마라. 장면으로 보여줘라.")
    p.append("- 교훈으로 끝맺지 마라.")
    for rule in spec.forbidden:
        p.append(f"- {rule}")
    p.append("")

    if spec.voice_rules:
        p.append("## 화법")
        for rule in spec.voice_rules:
            p.append(f"- {rule}")
        p.append("")

    # ── 수노 규칙 ── 사고 6종을 애초에 안 만들게 한다
    p.append("## 수노 지시서 규칙 — 반드시 지켜라")
    if spec.instrumental:
        p.append("- **연주곡이다. lyrics 는 반드시 빈 문자열로 둬라.** 한 글자도 넣지 마라.")
        p.append("- style 에 vocal, singer, singing, lyrics, voice, choir 를 쓰지 마라.")
        p.append("- style 에 instrumental 을 반드시 넣어라.")
    else:
        p.append(f"- 한 행은 {spec.syllables_per_line} 음절. 한국어는 음절 수가 곧 멜로디 길이다.")
        p.append("- 구조 태그를 써라: [Verse 1] [Pre-Chorus] [Chorus] [Verse 2] [Bridge] [Outro] [End]")
        p.append("- **마지막에 [Outro] 와 [End] 를 반드시 넣어라.** 없으면 곡이 끝났다 다시 시작한다.")
        p.append("- 빈 줄을 겹쳐 쓰지 마라. 구간 사이에 한 줄만. 겹치면 무음 구간이 생긴다.")
        p.append(f"- 가사가 너무 길면 마지막이 잘린다. 전체 {spec.max_seconds}초 안에 들어가게.")
    p.append("- **style 에 live, crowd, audience, arena, stadium, concert 를 절대 쓰지 마라.**")
    p.append("  이 단어들이 갑작스러운 떼창의 원인이다.")
    p.append("- style 에 강약 지시를 넣어라. 예: soft restrained verse, full crescendo chorus")
    p.append("")

    # ── 출력 ──
    p.append("## 출력")
    p.append(f"아래 JSON 을 이 파일에 써라: {out_path}")
    p.append("설명이나 인사말은 쓰지 말고 파일만 만들어라.\n")
    p.append("```json")
    p.append(json.dumps({
        "song_id": spec.song_id,
        "title": "노래 제목",
        "lyrics": "" if spec.instrumental else "[Verse 1]\n...\n\n[Outro]\n[End]",
        "style": "수노 스타일 프롬프트 (영어)",
        "instrumental": spec.instrumental,
        "notes": "이 가사가 어느 자료의 어떤 장면에서 왔는지 한 줄",
    }, ensure_ascii=False, indent=2))
    p.append("```")

    return "\n".join(p)


# ══════════════════════════════════════════════════════════════
# SECTION 3 — 다리
# ══════════════════════════════════════════════════════════════

class ClaudeBridge:
    """
    앱과 클로드 코드 CLI 사이의 다리.

    work_dir 아래에 이렇게 쌓인다.
        work/done/<song_id>.json      완성된 곡
        work/pending/<song_id>.json   요청서 (CLI 가 없을 때 사람이 처리)
        work/failed/<song_id>.txt     실패 기록
    """

    def __init__(
        self,
        work_dir: str = "work",
        *,
        timeout: int = 300,
        pause_between: float = 2.0,
        claude_cmd: Optional[str] = None,
    ):
        self.work_dir = Path(work_dir)
        self.done_dir = self.work_dir / "done"
        self.pending_dir = self.work_dir / "pending"
        self.failed_dir = self.work_dir / "failed"
        for d in (self.done_dir, self.pending_dir, self.failed_dir):
            d.mkdir(parents=True, exist_ok=True)

        self.timeout = timeout
        self.pause_between = pause_between   # 곡 사이 간격. 사용량 한도를 피한다
        self._cmd = claude_cmd or shutil.which("claude")

    # ── CLI 확인 ──────────────────────────────────────────────

    def available(self) -> bool:
        """
        클로드 코드 CLI 를 쓸 수 있는가.

        이름이 잡혀 있는 것만으로는 부족하다. 실제로 실행 가능한 파일인지
        확인한다. 잘못된 경로가 설정에 남아 있으면 곡을 만들기 직전에
        터지는 대신 여기서 미리 걸러진다.
        """
        if not self._cmd:
            return False
        if os.path.sep in self._cmd or (os.path.altsep and os.path.altsep in self._cmd):
            return os.path.isfile(self._cmd) and os.access(self._cmd, os.X_OK)
        return shutil.which(self._cmd) is not None

    @staticmethod
    def install_hint() -> str:
        return (
            "클로드 코드 CLI 를 찾지 못했습니다.\n"
            "  설치: npm install -g @anthropic-ai/claude-code\n"
            "  확인: claude --version\n"
            "\n"
            "설치 전까지는 파일 방식으로 돌아갑니다.\n"
            "  1) 앱이 work/pending/ 에 요청서를 만듭니다\n"
            "  2) 클로드 코드에 'work/pending 폴더를 처리해줘' 라고 하십시오\n"
            "  3) work/done/ 에 결과가 쌓이면 앱이 읽습니다"
        )

    # ── 곡 하나 ───────────────────────────────────────────────

    def result_path(self, song_id: str) -> Path:
        return self.done_dir / f"{_safe_id(song_id)}.json"

    def load_done(self, song_id: str) -> Optional[Dict]:
        """이미 만들어진 곡을 읽는다. 없으면 None."""
        path = self.result_path(song_id)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def write_request(self, spec: SongSpec) -> Path:
        """요청서를 pending 에 남긴다. CLI 가 없을 때 사람이 처리하는 통로."""
        path = self.pending_dir / f"{_safe_id(spec.song_id)}.json"
        _atomic_write(path, json.dumps({
            "spec": spec.to_dict(),
            "prompt": build_prompt(spec, self.result_path(spec.song_id)),
            "out_path": str(self.result_path(spec.song_id)),
        }, ensure_ascii=False, indent=2))
        return path

    def generate(self, spec: SongSpec, *, force: bool = False) -> Dict:
        """
        곡 하나를 만든다.

        force=False 이면 이미 있는 곡은 그대로 돌려준다 (재개용).
        CLI 가 없으면 요청서만 남기고 BridgeError 를 던진다.
        """
        if not force:
            existing = self.load_done(spec.song_id)
            if existing is not None:
                return existing

        out_path = self.result_path(spec.song_id)
        self.write_request(spec)                 # CLI 가 죽어도 요청서는 남는다

        if not self.available():
            raise BridgeError(
                f"클로드 코드 CLI 가 없어 '{spec.song_id}' 를 만들지 못했습니다.\n"
                + self.install_hint()
            )

        prompt = build_prompt(spec, out_path)
        try:
            proc = subprocess.run(
                [self._cmd, "-p", prompt],
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            raise BridgeError(f"'{spec.song_id}' 생성이 {self.timeout}초를 넘겨 중단했습니다.")
        except OSError as exc:
            raise BridgeError(f"클로드 코드 실행 실패: {exc}")

        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "")[-500:]
            if _looks_like_rate_limit(tail):
                raise BridgeError(
                    f"사용량 한도에 걸렸습니다. 잠시 뒤에 다시 누르면 "
                    f"'{spec.song_id}' 부터 이어갑니다.\n{tail}"
                )
            raise BridgeError(f"클로드 코드가 실패했습니다 (코드 {proc.returncode}):\n{tail}")

        # 클로드가 파일을 안 썼으면 stdout 에서 JSON 을 건져본다
        if not out_path.is_file():
            salvaged = _extract_json(proc.stdout or "")
            if salvaged is None:
                raise BridgeError(
                    f"'{spec.song_id}' 결과 파일이 생기지 않았습니다.\n"
                    f"stdout 끝부분: {(proc.stdout or '')[-300:]}"
                )
            _atomic_write(out_path, json.dumps(salvaged, ensure_ascii=False, indent=2))

        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise BridgeError(f"'{spec.song_id}' 결과 파일이 깨졌습니다: {exc}")

        missing = [k for k in ("title", "lyrics", "style") if k not in data]
        if missing:
            raise BridgeError(f"'{spec.song_id}' 결과에 빠진 항목: {', '.join(missing)}")

        return data

    # ── 여러 곡 ───────────────────────────────────────────────

    def generate_batch(
        self,
        specs: List[SongSpec],
        *,
        on_progress: Optional[Callable[[str], None]] = None,
        stop_on_error: bool = False,
    ) -> BatchResult:
        """
        여러 곡을 만든다. 20곡을 걸어도 끝까지 간다.

        이미 done 에 있는 곡은 건너뛴다. 그래서 중간에 죽어도
        다시 부르면 남은 곳부터 이어간다.

        stop_on_error=False (기본) 이면 한 곡이 실패해도 나머지를 계속 만든다.
        """
        result = BatchResult()
        say = on_progress or (lambda _msg: None)
        total = len(specs)

        for i, spec in enumerate(specs, 1):
            if self.load_done(spec.song_id) is not None:
                result.skipped.append(spec.song_id)
                say(f"[{i}/{total}] {spec.song_id} — 이미 있음, 건너뜀")
                continue

            say(f"[{i}/{total}] {spec.song_id} — 생성 중...")
            try:
                self.generate(spec)
                result.done.append(spec.song_id)
                say(f"[{i}/{total}] {spec.song_id} — 완료")
            except BridgeError as exc:
                message = str(exc)
                result.failed.append({"song_id": spec.song_id, "error": message})
                _atomic_write(self.failed_dir / f"{_safe_id(spec.song_id)}.txt", message)
                say(f"[{i}/{total}] {spec.song_id} — 실패: {message.splitlines()[0]}")
                if stop_on_error:
                    say("중단합니다. 고친 뒤 다시 누르면 여기서부터 이어갑니다.")
                    break

            if i < total and self.pause_between > 0:
                time.sleep(self.pause_between)

        say(
            f"끝. 새로 만든 곡 {len(result.done)}개, "
            f"건너뛴 곡 {len(result.skipped)}개, 실패 {len(result.failed)}개"
        )
        return result

    def pending_count(self) -> int:
        """아직 처리되지 않은 요청서 수."""
        return sum(
            1 for p in self.pending_dir.glob("*.json")
            if not (self.done_dir / p.name).is_file()
        )


# ══════════════════════════════════════════════════════════════
# SECTION 4 — 도우미
# ══════════════════════════════════════════════════════════════

_UNSAFE = re.compile(r"[^\w가-힣\-.]+")


def _safe_id(song_id: str) -> str:
    """파일명으로 쓸 수 있게 다듬는다. 한글은 살린다."""
    cleaned = _UNSAFE.sub("_", (song_id or "").strip()).strip("._")
    return cleaned or "untitled"


def _atomic_write(path: Path, text: str) -> None:
    """
    임시 파일에 쓴 뒤 제자리로 옮긴다.
    반쯤 쓰인 파일이 남으면 다음 실행에서 그걸 '완성된 곡'으로 오해한다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


_RATE_LIMIT_HINTS = ("rate limit", "usage limit", "429", "quota", "too many requests")


def _looks_like_rate_limit(text: str) -> bool:
    low = (text or "").lower()
    return any(hint in low for hint in _RATE_LIMIT_HINTS)


def _extract_json(text: str) -> Optional[Dict]:
    """
    클로드가 파일 대신 화면에 JSON 을 뱉었을 때 건져낸다.
    코드펜스 안을 먼저 보고, 없으면 마지막 중괄호 덩어리를 본다.
    """
    fence = re.search(r"```(?:json)?\s*\n(.+?)\n```", text or "", re.S)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass

    start = (text or "").find("{")
    end = (text or "").rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None
