# -*- coding: utf-8 -*-
"""
test_claude_bridge.py — 앱과 클로드 코드를 잇는 다리 검증
════════════════════════════════════════════════════════════════════════
실행: python3 test_claude_bridge.py

실제 클로드 코드 CLI 를 부르지 않는다. 가짜 CLI 를 만들어서
"20곡 중간에 죽어도 이어지는가" 를 진짜로 확인한다.
"""

import json
import os
import shutil
import stat
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_bridge import (  # noqa: E402
    BridgeError, ClaudeBridge, SongSpec, build_prompt, _extract_json, _safe_id,
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


def make_spec(song_id="song_001", **kw):
    base = dict(
        song_id=song_id,
        topic="이사 가던 날 두고 온 화분",
        genre="슬로우 락",
        channel_name="한밤의 가사",
        identity_line="잠들기 전 혼자인 사람 곁에 앉아 있어 주는",
        audience="40-50대, 새벽에 잠 안 올 때 보는 사람",
        voice_rules=["존댓말로 말한다"],
        forbidden=["설교하지 않는다", "희망회로를 돌리지 않는다"],
        singer="낮고 건조한 남성 보컬",
        source_excerpts=[
            {"source": "수필집 A", "text": "베란다에 남은 화분 자국이 동그랗다"},
            {"source": "시집 B", "text": "이삿짐 트럭이 골목을 빠져나갔다"},
        ],
    )
    base.update(kw)
    return SongSpec(**base)


# ── 가짜 클로드 CLI ────────────────────────────────────────────
# 프롬프트에서 출력 경로를 읽어 JSON 을 써주는 스크립트.
# 진짜 CLI 와 같은 방식으로 동작하므로 배치 재개를 실제로 검증할 수 있다.

_FAKE_CLI = '''#!/usr/bin/env python3
import json, re, sys, os
prompt = sys.argv[2] if len(sys.argv) > 2 else ""

if os.environ.get("FAKE_FAIL") == "1":
    sys.stderr.write("rate limit exceeded\\n")
    sys.exit(1)
if os.environ.get("FAKE_SILENT") == "1":
    sys.exit(0)                      # 성공했다면서 파일을 안 만든다

m = re.search(r"아래 JSON 을 이 파일에 써라: (.+)", prompt)
out = m.group(1).strip()
sid = re.search(r'"song_id": "([^"]+)"', prompt).group(1)
inst = '"instrumental": true' in prompt

if os.environ.get("FAKE_STDOUT_ONLY") == "1":
    print("```json")
    print(json.dumps({"song_id": sid, "title": "화면으로 나온 곡",
                      "lyrics": "[Verse 1]\\n줄\\n[Outro]\\n[End]",
                      "style": "ballad", "instrumental": False}, ensure_ascii=False))
    print("```")
    sys.exit(0)

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump({
        "song_id": sid,
        "title": f"{sid} 제목",
        "lyrics": "" if inst else "[Verse 1]\\n베란다에 남은 동그란 자국\\n\\n[Outro]\\n[End]",
        "style": "instrumental lofi, soft swell" if inst else "korean slow rock, restrained verse, full chorus",
        "instrumental": inst,
    }, f, ensure_ascii=False, indent=2)
'''


def install_fake_cli(tmp_dir):
    """가짜 claude 명령을 만들고 경로를 돌려준다."""
    path = os.path.join(tmp_dir, "fake_claude.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(_FAKE_CLI)
    os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
    return path


class FakeBridge(ClaudeBridge):
    """가짜 CLI 를 쓰는 다리. 파이썬으로 스크립트를 실행한다."""

    def __init__(self, work_dir, script, **kw):
        super().__init__(work_dir, claude_cmd=sys.executable, **kw)
        self._script = script

    def _run_args(self, prompt):
        return [sys.executable, self._script, "-p", prompt]


# ClaudeBridge.generate 가 [cmd, "-p", prompt] 를 쓰므로,
# cmd 자리에 python 을 넣고 스크립트를 앞에 끼우도록 감싼다.
def patched_bridge(work_dir, script, **kw):
    bridge = ClaudeBridge(work_dir, claude_cmd=sys.executable, **kw)
    original = subprocess_run_holder["run"]

    def run(args, **rkw):
        if args and args[0] == sys.executable and args[1] == "-p":
            args = [sys.executable, script, "-p", args[2]]
        return original(args, **rkw)

    subprocess_run_holder["run"] = run
    return bridge


import subprocess  # noqa: E402

subprocess_run_holder = {"run": subprocess.run}


def _dispatch(args, **kw):
    return subprocess_run_holder["run"](args, **kw)


subprocess.run = _dispatch


# ══════════════════════════════════════════════════════════════

def test_prompt():
    print("\n[1] 프롬프트 — 가사 품질이 여기서 갈린다")
    spec = make_spec()
    prompt = build_prompt(spec, "/tmp/out.json")

    check("주제가 들어간다", spec.topic in prompt)
    check("채널 정체성이 들어간다", spec.identity_line in prompt)
    check("시청자가 들어간다", spec.audience in prompt)
    check("대표 가수가 들어간다", spec.singer in prompt)
    check("옵시디언 발췌가 들어간다", "베란다에 남은 화분 자국" in prompt)
    check("출처가 들어간다", "수필집 A" in prompt)
    check("인용 금지를 명시한다", "그대로 가져오지 마라" in prompt)
    check("장면만 뽑으라고 한다", "구체적인 장면" in prompt)
    check("개념어 금지를 명시한다", "개념어를 가사에 넣지 마라" in prompt)
    check("AI 상투구를 나열한다", "밤하늘의 별" in prompt and "흘러가는 시간" in prompt)
    check("금지 규칙이 들어간다", "설교하지 않는다" in prompt)
    check("화법이 들어간다", "존댓말로 말한다" in prompt)
    check("출력 경로를 지정한다", "/tmp/out.json" in prompt)

    check("떼창 금지를 명시한다", "live, crowd, audience" in prompt)
    check("종료 태그를 요구한다", "[Outro] 와 [End]" in prompt)
    check("음절 규격을 준다", "6~12" in prompt)
    check("빈 줄 금지를 명시한다", "빈 줄을 겹쳐 쓰지 마라" in prompt)
    check("강약 지시를 요구한다", "crescendo" in prompt)

    inst = build_prompt(make_spec(instrumental=True), "/tmp/o.json")
    check("연주곡은 가사칸을 비우라고 한다", "빈 문자열로 둬라" in inst)
    check("연주곡은 보컬 단어를 막는다", "vocal, singer" in inst)
    check("연주곡엔 음절 규격이 없다", "6~12" not in inst)


def test_availability():
    print("\n[2] CLI 확인")
    with tempfile.TemporaryDirectory() as tmp:
        no_cli = ClaudeBridge(tmp, claude_cmd=os.path.join(tmp, "없는_claude"))
        check("없는 경로면 False", not no_cli.available())
        hint = no_cli.install_hint()
        check("설치 방법을 알려준다", "npm install" in hint)
        check("대안을 알려준다", "work/pending" in hint)

        check("PATH 에 없는 이름도 False",
              not ClaudeBridge(tmp, claude_cmd="claude_없는이름_9z").available())

        check("실행 가능한 파일이면 True",
              ClaudeBridge(tmp, claude_cmd=sys.executable).available())
        check("PATH 에 있는 이름이면 True",
              ClaudeBridge(tmp, claude_cmd=os.path.basename(sys.executable)).available())

        not_exec = os.path.join(tmp, "그냥파일.txt")
        open(not_exec, "w").close()
        check("실행 권한이 없으면 False",
              not ClaudeBridge(tmp, claude_cmd=not_exec).available())


def test_no_cli_leaves_request():
    print("\n[3] CLI 가 없어도 요청서는 남는다")
    with tempfile.TemporaryDirectory() as tmp:
        bridge = ClaudeBridge(tmp, claude_cmd=os.path.join(tmp, "없는_claude"))
        spec = make_spec("song_x")
        try:
            bridge.generate(spec)
            check("BridgeError 를 던진다", False, "(안 던짐)")
        except BridgeError as exc:
            check("BridgeError 를 던진다", True)
            check("설치 방법을 담는다", "npm install" in str(exc))

        pending = os.path.join(tmp, "pending", "song_x.json")
        check("요청서가 남는다", os.path.isfile(pending))
        data = json.load(open(pending, encoding="utf-8"))
        check("요청서에 프롬프트가 있다", "prompt" in data and len(data["prompt"]) > 100)
        check("요청서에 출력 경로가 있다", "out_path" in data)
        check("요청서에 원본 spec 이 있다", data["spec"]["topic"] == spec.topic)


def test_single_generate():
    print("\n[4] 곡 하나 만들기")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        bridge = patched_bridge(os.path.join(tmp, "work"), script, pause_between=0)

        data = bridge.generate(make_spec("song_001"))
        check("결과를 돌려준다", data["song_id"] == "song_001")
        check("제목이 있다", "title" in data)
        check("가사가 있다", "lyrics" in data)
        check("스타일이 있다", "style" in data)
        check("파일로 남는다", bridge.result_path("song_001").is_file())

        again = bridge.generate(make_spec("song_001"))
        check("두 번째는 캐시를 쓴다", again == data)

        inst = bridge.generate(make_spec("inst_001", instrumental=True))
        check("연주곡은 가사가 빈다", inst["lyrics"] == "")


def test_batch_resume():
    print("\n[5] 20곡 배치 — 중간에 죽어도 이어진다 (핵심)")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        work = os.path.join(tmp, "work")
        bridge = patched_bridge(work, script, pause_between=0)

        specs = [make_spec(f"song_{i:03d}") for i in range(1, 21)]

        # 5곡을 만든 뒤 한도에 걸린 상황
        first = bridge.generate_batch(specs[:5])
        check("첫 5곡 성공", len(first.done) == 5, f"(실제 {len(first.done)})")

        os.environ["FAKE_FAIL"] = "1"
        blocked = bridge.generate_batch(specs)
        os.environ.pop("FAKE_FAIL")

        check("이미 만든 5곡은 건너뛴다", len(blocked.skipped) == 5,
              f"(실제 {len(blocked.skipped)})")
        check("나머지는 실패로 기록", len(blocked.failed) == 15,
              f"(실제 {len(blocked.failed)})")
        check("한도 걸림을 알아본다",
              "한도" in blocked.failed[0]["error"])
        check("실패해도 멈추지 않는다", len(blocked.failed) == 15)

        # 한도가 풀린 뒤 다시 누른다
        resumed = bridge.generate_batch(specs)
        check("건너뛴 곡 5개 그대로", len(resumed.skipped) == 5)
        check("남은 15곡을 이어서 만든다", len(resumed.done) == 15,
              f"(실제 {len(resumed.done)})")
        check("실패 없음", resumed.ok)

        done_files = list((bridge.done_dir).glob("*.json"))
        check("파일이 20개", len(done_files) == 20, f"(실제 {len(done_files)})")

        # 세 번째는 전부 건너뛴다
        third = bridge.generate_batch(specs)
        check("다 있으면 전부 건너뛴다", len(third.skipped) == 20 and not third.done)


def test_batch_progress():
    print("\n[6] 진행 상황 표시")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        bridge = patched_bridge(os.path.join(tmp, "work"), script, pause_between=0)

        lines = []
        bridge.generate_batch([make_spec(f"s{i}") for i in range(3)],
                              on_progress=lines.append)
        check("곡마다 알린다", len(lines) >= 3, f"(실제 {len(lines)}줄)")
        check("몇 곡 중 몇 곡인지 보인다", any("[1/3]" in ln for ln in lines))
        check("끝났음을 알린다", any("끝." in ln for ln in lines))


def test_stop_on_error():
    print("\n[7] stop_on_error")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        bridge = patched_bridge(os.path.join(tmp, "work"), script, pause_between=0)

        os.environ["FAKE_FAIL"] = "1"
        r = bridge.generate_batch([make_spec(f"s{i}") for i in range(5)],
                                  stop_on_error=True)
        os.environ.pop("FAKE_FAIL")
        check("첫 실패에서 멈춘다", len(r.failed) == 1, f"(실제 {len(r.failed)})")


def test_failure_modes():
    print("\n[8] 실패 처리")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        bridge = patched_bridge(os.path.join(tmp, "work"), script, pause_between=0)

        os.environ["FAKE_SILENT"] = "1"
        try:
            bridge.generate(make_spec("silent"))
            check("파일을 안 만들면 실패로 본다", False, "(성공했다고 함)")
        except BridgeError as exc:
            check("파일을 안 만들면 실패로 본다", "생기지 않았습니다" in str(exc))
        os.environ.pop("FAKE_SILENT")

        os.environ["FAKE_STDOUT_ONLY"] = "1"
        data = bridge.generate(make_spec("stdout_only"))
        check("화면에만 뱉어도 건져낸다", data["title"] == "화면으로 나온 곡")
        os.environ.pop("FAKE_STDOUT_ONLY")

        os.environ["FAKE_FAIL"] = "1"
        try:
            bridge.generate(make_spec("rate_limited"))
            check("한도 걸림을 알아본다", False, "(성공했다고 함)")
        except BridgeError as exc:
            check("한도 걸림을 알아본다", "한도" in str(exc))
            check("이어서 하면 된다고 안내한다", "이어갑니다" in str(exc))
        os.environ.pop("FAKE_FAIL")


def test_failed_log():
    print("\n[9] 실패 기록")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        bridge = patched_bridge(os.path.join(tmp, "work"), script, pause_between=0)

        os.environ["FAKE_FAIL"] = "1"
        bridge.generate_batch([make_spec("bad_song")])
        os.environ.pop("FAKE_FAIL")

        log = bridge.failed_dir / "bad_song.txt"
        check("실패를 파일로 남긴다", log.is_file())
        check("내용이 있다", len(log.read_text(encoding="utf-8")) > 10)


def test_helpers():
    print("\n[10] 도우미")
    check("한글 ID 를 살린다", _safe_id("한밤의_가사_001") == "한밤의_가사_001")
    check("경로 문자를 없앤다", "/" not in _safe_id("a/b\\c"))
    check("빈 ID 는 기본값", _safe_id("") == "untitled")
    check("점 두 개를 없앤다", ".." not in _safe_id("../etc/passwd"))

    fenced = '설명\n```json\n{"a": 1}\n```\n끝'
    check("코드펜스에서 JSON 을 건진다", _extract_json(fenced) == {"a": 1})
    check("맨 JSON 도 건진다", _extract_json('앞 {"b": 2} 뒤') == {"b": 2})
    check("JSON 이 없으면 None", _extract_json("그냥 글") is None)


def test_pending_count():
    print("\n[11] 남은 요청 세기")
    with tempfile.TemporaryDirectory() as tmp:
        script = install_fake_cli(tmp)
        bridge = patched_bridge(os.path.join(tmp, "work"), script, pause_between=0)

        for i in range(3):
            bridge.write_request(make_spec(f"p{i}"))
        check("요청 3개", bridge.pending_count() == 3, f"(실제 {bridge.pending_count()})")

        bridge.generate(make_spec("p0"))
        check("하나 처리되면 2개", bridge.pending_count() == 2,
              f"(실제 {bridge.pending_count()})")


def test_no_paid_dependency():
    print("\n[12] 비용 0원 — 유료 SDK 없음")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "claude_bridge.py"), encoding="utf-8") as f:
        src = f.read().lower()
    for token in ("import anthropic", "openai", "api.anthropic.com",
                  "anthropic_api_key", "import requests", "httpx"):
        check(f"'{token}' 미사용", token not in src)


if __name__ == "__main__":
    print("=" * 60)
    print("클로드 코드 다리 — 검증")
    print("=" * 60)

    test_prompt()
    test_availability()
    test_no_cli_leaves_request()
    test_single_generate()
    test_batch_resume()
    test_batch_progress()
    test_stop_on_error()
    test_failure_modes()
    test_failed_log()
    test_helpers()
    test_pending_count()
    test_no_paid_dependency()

    print("\n" + "=" * 60)
    if _failed:
        print(f"실패 {len(_failed)}건 / 통과 {_passed}건")
        for f_ in _failed:
            print(f"  X {f_}")
        sys.exit(1)
    print(f"전부 통과 — {_passed}건")
    print("=" * 60)
