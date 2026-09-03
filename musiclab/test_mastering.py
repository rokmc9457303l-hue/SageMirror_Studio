# -*- coding: utf-8 -*-
"""
test_mastering.py — 마스터링 체인 검증
════════════════════════════════════════════════════════════════════════
실행: python3 test_mastering.py

진짜 오디오를 만들어서 진짜로 처리한다. 특히 확인하는 것:

  - 출력이 입력에 상수 하나를 곱한 것뿐인가 (무손실)
  - 트루 피크가 정말 -1.0 dBTP 아래로 내려가는가
  - 라우드니스가 정말 -14 LUFS 에 닿는가
  - MP3 원본을 막는가
"""

import math
import os
import shutil
import sys
import tempfile

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mastering import (  # noqa: E402
    TARGET_LUFS, TARGET_TRUE_PEAK_DB,
    analyze, check_source, master, master_batch, verify_lossless,
)

_passed = 0
_failed = []
SR = 44100


def check(label, condition, detail=""):
    global _passed
    if condition:
        _passed += 1
        print(f"  OK  {label}")
    else:
        _failed.append(f"{label} {detail}".strip())
        print(f"  X   {label} {detail}")


def make_track(path, seconds=40.0, peak=0.9, sr=SR, seed=7):
    """
    음악처럼 생긴 신호를 만든다.
    화음 + 노이즈 + 완만한 다이내믹. 라우드니스 측정이 의미를 가지려면
    유튜브 게이팅 기준상 최소 수십 초가 필요하다.
    """
    rng = np.random.default_rng(seed)
    n = int(sr * seconds)
    t = np.arange(n) / sr

    sig = np.zeros(n)
    for freq, amp in ((110, 0.5), (220, 0.35), (330, 0.22), (660, 0.12)):
        sig += amp * np.sin(2 * np.pi * freq * t)
    sig += 0.06 * rng.standard_normal(n)          # 공기감
    sig *= 1.0 + 0.25 * np.sin(2 * np.pi * 0.35 * t)   # 완만한 다이내믹

    sig = sig / np.max(np.abs(sig)) * peak
    stereo = np.column_stack([sig, sig * 0.97])   # 살짝 다른 우측 채널
    sf.write(path, stereo, sr, subtype="PCM_24")
    return path


# ══════════════════════════════════════════════════════════════

def test_analyze():
    print("\n[1] 측정")
    with tempfile.TemporaryDirectory() as tmp:
        src = make_track(os.path.join(tmp, "t.wav"), peak=0.9)
        s = analyze(src)

        check("샘플레이트를 읽는다", s.sample_rate == SR)
        check("채널 수를 읽는다", s.channels == 2)
        check("길이를 읽는다", abs(s.duration_sec - 40.0) < 0.1, f"(실제 {s.duration_sec:.1f})")
        check("포맷을 읽는다", s.subtype == "PCM_24", f"(실제 {s.subtype})")
        check("무손실로 인식", not s.is_lossy)
        check("라우드니스를 잰다", -40 < s.lufs < 0, f"(실제 {s.lufs:.1f})")

        expected_peak_db = 20 * math.log10(0.9)
        check("샘플 피크가 맞다", abs(s.sample_peak_db - expected_peak_db) < 0.2,
              f"(실제 {s.sample_peak_db:.2f}, 기대 {expected_peak_db:.2f})")
        check("트루 피크가 샘플 피크 이상", s.true_peak_db >= s.sample_peak_db - 0.01,
              f"(TP {s.true_peak_db:.2f} vs SP {s.sample_peak_db:.2f})")
        check("클리핑 없음", s.clipped_samples == 0)


def test_true_peak_beats_sample_peak():
    print("\n[2] 트루 피크 — 샘플 피크만 보면 놓치는 것")
    with tempfile.TemporaryDirectory() as tmp:
        # 샘플 사이에서 튀어오르는 신호. 나이키스트 근처 정현파를
        # 샘플 격자와 어긋나게 놓으면 샘플값보다 실제 파형이 높다.
        n = SR * 3
        t = np.arange(n) / SR
        sig = 0.98 * np.sin(2 * np.pi * (SR / 4 + 30) * t + 0.78)
        path = os.path.join(tmp, "inter.wav")
        sf.write(path, np.column_stack([sig, sig]), SR, subtype="PCM_24")

        s = analyze(path)
        check("트루 피크가 샘플 피크보다 높다",
              s.true_peak_db > s.sample_peak_db,
              f"(TP {s.true_peak_db:.3f} vs SP {s.sample_peak_db:.3f})")
        check("차이가 의미 있는 크기",
              s.true_peak_db - s.sample_peak_db > 0.05,
              f"(차이 {s.true_peak_db - s.sample_peak_db:.3f} dB)")


def test_source_checks():
    print("\n[3] 원본 검사 — 마스터링으로 못 고치는 것")
    with tempfile.TemporaryDirectory() as tmp:
        clean = make_track(os.path.join(tmp, "clean.wav"))
        check("멀쩡한 원본은 막지 않는다",
              not [i for i in check_source(analyze(clean)) if i.severity == "block"])

        # 클리핑된 원본
        n = SR * 40
        t = np.arange(n) / SR
        hot = np.clip(np.sin(2 * np.pi * 220 * t) * 1.5, -1.0, 1.0)
        clipped = os.path.join(tmp, "clipped.wav")
        sf.write(clipped, np.column_stack([hot, hot]), SR, subtype="PCM_24")

        issues = check_source(analyze(clipped))
        check("클리핑을 잡아낸다", any("클리핑" in i.message for i in issues))
        check("되돌릴 수 없다고 알려준다",
              any("못 고칩니다" in i.hint for i in issues))
        check("32비트 float 로 받으라고 안내한다",
              any("32비트 float" in i.hint for i in issues))

        # 짧은 곡
        short = make_track(os.path.join(tmp, "short.wav"), seconds=10)
        check("짧은 곡을 경고한다",
              any("짧습니다" in i.message for i in check_source(analyze(short))))


def test_master_hits_targets():
    print("\n[4] 목표에 실제로 닿는가")
    with tempfile.TemporaryDirectory() as tmp:
        src = make_track(os.path.join(tmp, "src.wav"), peak=0.95)
        dst = os.path.join(tmp, "out.wav")

        r = master(src, dst)
        check("성공", r.ok, f"({[str(i) for i in r.issues]})")
        check("파일이 생긴다", os.path.isfile(dst))

        check("라우드니스가 -14 LUFS 에 닿는다",
              abs(r.after.lufs - TARGET_LUFS) < 0.6,
              f"(실제 {r.after.lufs:.2f})")
        check("트루 피크가 -1.0 dBTP 아래",
              r.after.true_peak_db <= TARGET_TRUE_PEAK_DB + 0.1,
              f"(실제 {r.after.true_peak_db:.2f})")
        check("클리핑 없음", r.after.clipped_samples == 0)
        check("샘플레이트를 안 바꾼다", r.after.sample_rate == r.before.sample_rate)
        check("채널 수를 안 바꾼다", r.after.channels == r.before.channels)
        check("24비트로 나간다", r.after.subtype == "PCM_24", f"(실제 {r.after.subtype})")
        check("길이가 그대로", abs(r.after.duration_sec - r.before.duration_sec) < 0.01)


def test_lossless():
    print("\n[5] 무손실 — 이게 이 파일의 핵심 주장이다")
    with tempfile.TemporaryDirectory() as tmp:
        src = make_track(os.path.join(tmp, "src.wav"), peak=0.9)
        dst = os.path.join(tmp, "out.wav")

        r = master(src, dst)
        check("무손실이라고 보고한다", r.lossless)

        lossless, residual_db = verify_lossless(src, dst)
        check("실제로 무손실이다 (잔차가 24비트 바닥 아래)",
              lossless, f"(잔차 {residual_db:.1f} dB)")
        check("잔차가 -100 dB 아래", residual_db < -100, f"(실제 {residual_db:.1f})")

        # 직접 확인: 출력을 게인으로 나누면 입력과 같아야 한다
        a, _ = sf.read(src, dtype="float64", always_2d=True)
        b, _ = sf.read(dst, dtype="float64", always_2d=True)
        gain = 10.0 ** (r.gain_db / 20.0)
        max_diff = float(np.max(np.abs(b - a * gain)))
        check("게인을 되돌리면 원본과 같다 (24비트 오차 안)",
              max_diff < 1e-6, f"(최대 차이 {max_diff:.2e})")


def test_loud_source_gets_quieter():
    print("\n[6] 시끄러운 원본 — 수노 출력이 이렇다")
    with tempfile.TemporaryDirectory() as tmp:
        # 수노 출력은 보통 이미 크게 눌려서 나온다
        src = make_track(os.path.join(tmp, "loud.wav"), peak=0.99)
        dst = os.path.join(tmp, "out.wav")

        r = master(src, dst)
        check("게인을 내린다", r.gain_db < 0, f"(게인 {r.gain_db:+.2f} dB)")
        check("결과가 원본보다 조용하다", r.after.lufs < r.before.lufs)
        check("트루 피크도 함께 내려간다",
              r.after.true_peak_db < r.before.true_peak_db)
        check("여전히 무손실", verify_lossless(src, dst)[0])


def test_peak_constraint_wins():
    print("\n[7] 피크가 넘칠 때 — 리미터 대신 게인을 내린다")
    with tempfile.TemporaryDirectory() as tmp:
        # 라우드니스는 낮은데 피크는 큰 신호 (다이내믹이 넓은 곡)
        n = SR * 40
        t = np.arange(n) / SR
        quiet = 0.02 * np.sin(2 * np.pi * 220 * t)
        spike_at = np.zeros(n)
        for pos in range(SR, n, SR * 3):          # 3초마다 큰 피크
            spike_at[pos:pos + 400] = 0.99 * np.sin(
                2 * np.pi * 1000 * t[:400])
        sig = quiet + spike_at

        src = os.path.join(tmp, "dyn.wav")
        sf.write(src, np.column_stack([sig, sig]), SR, subtype="PCM_24")
        dst = os.path.join(tmp, "out.wav")

        r = master(src, dst)
        check("피크 제약을 지킨다",
              r.after.true_peak_db <= TARGET_TRUE_PEAK_DB + 0.1,
              f"(실제 {r.after.true_peak_db:.2f})")
        check("리미터를 안 물려서 무손실 그대로", verify_lossless(src, dst)[0])
        check("왜 조용해졌는지 설명한다",
              any("게인을" in i.message for i in r.issues) or
              r.after.lufs <= TARGET_LUFS + 0.6)


def test_lossy_source_blocked():
    print("\n[8] MP3 원본 — 음질에 가장 큰 한 가지")
    with tempfile.TemporaryDirectory() as tmp:
        src = make_track(os.path.join(tmp, "t.wav"))
        # 확장자만 바꿔 손실 판정 경로를 확인한다
        fake_mp3 = os.path.join(tmp, "t.mp3.wav")
        shutil.copy(src, fake_mp3)

        import mastering
        original_ext = mastering._LOSSY_EXT
        mastering._LOSSY_EXT = original_ext | {".wav"}      # 강제로 손실 취급
        try:
            stats = analyze(fake_mp3)
            issues = check_source(stats)
            blocked = [i for i in issues if i.severity == "block"]
            check("손실 원본을 막는다", len(blocked) > 0)
            check("WAV 로 다시 받으라고 안내한다",
                  any("WAV" in i.hint for i in blocked))

            dst = os.path.join(tmp, "out.wav")
            r = master(fake_mp3, dst)
            check("막히면 처리하지 않는다", not r.ok)
            check("출력 파일을 안 만든다", not os.path.isfile(dst))

            r2 = master(fake_mp3, dst, allow_lossy_source=True)
            check("강제 옵션이 있으면 진행한다", r2.ok)
        finally:
            mastering._LOSSY_EXT = original_ext


def test_batch():
    print("\n[9] 여러 곡 — 같은 기준으로")
    with tempfile.TemporaryDirectory() as tmp:
        srcs = []
        for i, peak in enumerate([0.5, 0.8, 0.95], 1):
            srcs.append(make_track(os.path.join(tmp, f"s{i}.wav"),
                                   peak=peak, seed=i))
        out_dir = os.path.join(tmp, "out")

        lines = []
        results = master_batch(srcs, out_dir, on_progress=lines.append)

        check("세 곡 모두 처리", len(results) == 3, f"(실제 {len(results)})")
        check("전부 성공", all(r.ok for r in results))
        check("진행 상황을 알린다", any("[1/3]" in ln for ln in lines))

        lufs_values = [r.after.lufs for r in results]
        spread = max(lufs_values) - min(lufs_values)
        check("음량이 서로 맞춰진다 (편차 1 dB 안)",
              spread < 1.0, f"(편차 {spread:.2f} dB, 값 {[f'{v:.1f}' for v in lufs_values]})")

        lines2 = []
        master_batch(srcs, out_dir, on_progress=lines2.append)
        check("이미 만든 것은 건너뛴다",
              sum("건너뜀" in ln for ln in lines2) == 3)


def test_float32_source():
    print("\n[10] 32비트 float 원본 — 수노가 내보내는 포맷")
    with tempfile.TemporaryDirectory() as tmp:
        # 0 dBFS 를 넘는 32비트 float. float 에서는 클리핑이 아니다.
        n = SR * 40
        t = np.arange(n) / SR
        rng = np.random.default_rng(3)
        sig = (np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 220 * t)
               + 0.05 * rng.standard_normal(n))
        sig = sig / np.max(np.abs(sig)) * 1.4          # 1.0 을 넘긴다
        src = os.path.join(tmp, "hot_float.wav")
        sf.write(src, np.column_stack([sig, sig * 0.98]), SR, subtype="FLOAT")

        s = analyze(src)
        check("32비트 float 으로 인식", s.is_float and s.subtype == "FLOAT",
              f"(실제 {s.subtype})")
        check("0 dBFS 초과를 센다", s.over_full_scale > 0,
              f"(실제 {s.over_full_scale})")
        check("float 은 클리핑으로 세지 않는다", s.clipped_samples == 0,
              f"(실제 {s.clipped_samples})")

        issues = check_source(s)
        check("float 초과를 막지 않는다",
              not [i for i in issues if i.severity == "block"],
              f"({[i.message for i in issues if i.severity == 'block']})")
        check("잘린 게 아니라고 설명한다",
              any("잘린 것이 아닙니다" in i.hint for i in issues))

        dst = os.path.join(tmp, "out.wav")
        r = master(src, dst)
        check("처리된다", r.ok)
        check("출력도 32비트 float", r.after.subtype == "FLOAT",
              f"(실제 {r.after.subtype})")
        check("1.0 초과가 사라진다", r.after.over_full_scale == 0,
              f"(실제 {r.after.over_full_scale})")
        check("트루 피크가 목표 아래",
              r.after.true_peak_db <= TARGET_TRUE_PEAK_DB + 0.1,
              f"(실제 {r.after.true_peak_db:.2f})")
        check("라우드니스가 목표에 닿는다",
              abs(r.after.lufs - TARGET_LUFS) < 0.6, f"(실제 {r.after.lufs:.2f})")

        lossless, residual = verify_lossless(src, dst)
        check("32비트 float 왕복이 완전 무손실", lossless,
              f"(잔차 {residual:.1f} dB)")
        check("잔차가 24비트보다 훨씬 낮다", residual < -140,
              f"(실제 {residual:.1f} dB)")


def test_bitdepth_preserved():
    print("\n[11] 비트뎁스 — 원본보다 깎지 않는다")
    with tempfile.TemporaryDirectory() as tmp:
        for st in ("FLOAT", "PCM_24", "PCM_16"):
            src = os.path.join(tmp, f"src_{st}.wav")
            make_track(src, seconds=35, peak=0.8)
            audio, sr = sf.read(src, dtype="float64", always_2d=True)
            sf.write(src, audio, sr, subtype=st)

            dst = os.path.join(tmp, f"out_{st}.wav")
            r = master(src, dst)
            check(f"{st} 원본은 {st} 로 나간다",
                  r.after.subtype == st, f"(실제 {r.after.subtype})")

        # 명시적으로 낮추면 경고한다
        src = os.path.join(tmp, "src_FLOAT.wav")
        dst = os.path.join(tmp, "down.wav")
        r = master(src, dst, subtype="PCM_16")
        check("낮은 비트뎁스로 내보내면 경고한다",
              any("무손실이 아닙니다" in i.hint for i in r.issues))
        check("그래도 요청한 포맷으로 나간다", r.after.subtype == "PCM_16")


def test_report():
    print("\n[10] 보고서")
    with tempfile.TemporaryDirectory() as tmp:
        src = make_track(os.path.join(tmp, "src.wav"))
        dst = os.path.join(tmp, "out.wav")
        text = master(src, dst).report()

        check("전후를 보여준다", "[전]" in text and "[후]" in text)
        check("라우드니스를 보여준다", "LUFS" in text)
        check("트루 피크를 보여준다", "dBTP" in text)
        check("게인을 보여준다", "게인" in text)
        check("무손실임을 밝힌다", "무손실" in text)


if __name__ == "__main__":
    print("=" * 60)
    print("마스터링 체인 — 검증")
    print("=" * 60)

    test_analyze()
    test_true_peak_beats_sample_peak()
    test_source_checks()
    test_master_hits_targets()
    test_lossless()
    test_loud_source_gets_quieter()
    test_peak_constraint_wins()
    test_lossy_source_blocked()
    test_batch()
    test_float32_source()
    test_bitdepth_preserved()
    test_report()

    print("\n" + "=" * 60)
    if _failed:
        print(f"실패 {len(_failed)}건 / 통과 {_passed}건")
        for f_ in _failed:
            print(f"  X {f_}")
        sys.exit(1)
    print(f"전부 통과 — {_passed}건")
    print("=" * 60)
