# -*- coding: utf-8 -*-
"""
mastering.py — 음질 우선 마스터링 체인 v1.0
════════════════════════════════════════════════════════════════════════

목표: **음질을 한 조각도 잃지 않으면서** 20곡이 한 앨범처럼 들리게 한다.

설계 원칙 — 왜 이렇게 만들었는가
────────────────────────────────
1. **기본 경로는 순수 게인이다.**
   라우드니스를 맞추는 데 필요한 건 곱셈 하나뿐이다. 압축도 리미팅도
   하지 않는다. 곱셈은 파형을 바꾸지 않으므로 왜곡이 수학적으로 0이다.
   `verify_lossless()` 로 실제로 0인지 확인할 수 있다.

2. **32비트 float 로 처리한다.**
   중간 단계 양자화 손실이 없다. 마지막에만 24비트로 내보낸다.

3. **트루 피크를 -1.0 dBTP 이하로 잡는다.**
   유튜브는 오디오를 다시 인코딩한다. 그때 샘플 사이에서 파형이
   0 dBFS 를 넘으면 찌그러진다. 헤드룸을 미리 확보해야 그게 안 생긴다.
   4배 오버샘플링으로 실제 피크를 잰다. 샘플 피크만 보면 놓친다.

4. **리샘플링하지 않는다.** 44.1kHz 소스는 44.1kHz 그대로 나간다.

5. **스템 분리를 하지 않는다.**
   분리기는 위상 뭉개짐과 번짐을 남기고, 다시 합치면 그 손상이
   최종물에 들어간다. 음질이 목적이라면 원본을 안 건드리는 게 맞다.

가장 큰 레버는 이 파일 밖에 있다
────────────────────────────────
**수노에서 WAV 로 받는 것.** MP3 는 이미 손실 압축이라 거기에 무엇을
걸어도 잃은 것은 돌아오지 않는다. `check_source()` 가 이걸 검사한다.

필요한 것: numpy, soundfile, pyloudnorm (matchering 은 있으면 쓴다)
    pip install numpy soundfile pyloudnorm matchering
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

try:
    from scipy.signal import resample_poly
    _HAS_SCIPY = True
except Exception:  # pragma: no cover
    _HAS_SCIPY = False

try:
    import matchering as mg
    _HAS_MATCHERING = True
except Exception:
    _HAS_MATCHERING = False

__all__ = [
    "analyze", "check_source", "master", "verify_lossless",
    "AudioStats", "MasterResult", "Issue",
    "TARGET_LUFS", "TARGET_TRUE_PEAK_DB",
]

# 유튜브 기준. 이보다 크게 만들면 유튜브가 눌러서 다이내믹만 손해다.
TARGET_LUFS = -14.0
# 유튜브가 AAC 로 다시 인코딩할 때 클리핑이 안 생기는 헤드룸.
TARGET_TRUE_PEAK_DB = -1.0

_LOSSY_EXT = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wma"}
_EPS = 1e-12


# ══════════════════════════════════════════════════════════════
# SECTION 1 — 측정
# ══════════════════════════════════════════════════════════════

@dataclass
class Issue:
    severity: str          # "block" | "warn" | "info"
    message: str
    hint: str = ""

    def __str__(self) -> str:
        mark = {"block": "[막음]", "warn": "[주의]", "info": "[안내]"}.get(self.severity, "")
        return f"{mark} {self.message}" + (f"\n      → {self.hint}" if self.hint else "")


@dataclass
class AudioStats:
    path: str
    sample_rate: int
    channels: int
    frames: int
    duration_sec: float
    subtype: str                 # PCM_16, PCM_24, FLOAT, MPEG_LAYER_III ...
    is_lossy: bool
    lufs: float                  # 통합 라우드니스
    true_peak_db: float          # dBTP — 4배 오버샘플링으로 잰 진짜 피크
    sample_peak_db: float        # dBFS — 샘플만 본 피크
    clipped_samples: int         # 0 dBFS 에 닿은 샘플 수

    def summary(self) -> str:
        return (
            f"{os.path.basename(self.path)}\n"
            f"  {self.sample_rate} Hz · {self.channels}ch · {self.subtype} · "
            f"{self.duration_sec:.1f}초\n"
            f"  라우드니스 {self.lufs:.2f} LUFS\n"
            f"  트루 피크 {self.true_peak_db:.2f} dBTP "
            f"(샘플 피크 {self.sample_peak_db:.2f} dBFS)\n"
            f"  클리핑 샘플 {self.clipped_samples}개"
        )


def _to_db(amplitude: float) -> float:
    return 20.0 * math.log10(max(abs(amplitude), _EPS))


def _true_peak_db(audio: np.ndarray, oversample: int = 4) -> float:
    """
    트루 피크를 잰다 (dBTP).

    샘플 피크만 보면 안 되는 이유: 디지털 샘플 사이에서 실제 파형은
    샘플값보다 높이 올라갈 수 있다. 유튜브가 재인코딩할 때 그 지점이
    찌그러진다. 4배 오버샘플링해서 그 사이를 본다.
    """
    if audio.size == 0:
        return -math.inf

    if not _HAS_SCIPY:
        # scipy 가 없으면 샘플 피크에 관례적 여유를 얹는다.
        # 정확하지 않으므로 scipy 설치를 권한다.
        return _to_db(float(np.max(np.abs(audio)))) + 0.5

    data = audio if audio.ndim == 2 else audio[:, None]
    peak = 0.0
    for ch in range(data.shape[1]):
        up = resample_poly(data[:, ch], oversample, 1)
        peak = max(peak, float(np.max(np.abs(up))))
    return _to_db(peak)


def _read_float(path: str) -> Tuple[np.ndarray, int, str]:
    """
    오디오를 float64 로 읽는다.
    always_2d 로 모노도 (n, 1) 모양으로 통일한다.
    """
    info = sf.info(path)
    audio, sr = sf.read(path, dtype="float64", always_2d=True)
    return audio, sr, info.subtype


def analyze(path: str) -> AudioStats:
    """파일 하나를 측정한다. 아무것도 바꾸지 않는다."""
    audio, sr, subtype = _read_float(path)
    frames, channels = audio.shape

    meter = pyln.Meter(sr)
    # pyloudnorm 은 모노를 1차원으로도 받지만 2차원을 그대로 준다
    loudness = meter.integrated_loudness(audio if channels > 1 else audio[:, 0])

    sample_peak = float(np.max(np.abs(audio))) if frames else 0.0
    ext = os.path.splitext(path)[1].lower()

    return AudioStats(
        path=path,
        sample_rate=sr,
        channels=channels,
        frames=frames,
        duration_sec=frames / sr if sr else 0.0,
        subtype=subtype,
        is_lossy=ext in _LOSSY_EXT,
        lufs=float(loudness),
        true_peak_db=_true_peak_db(audio),
        sample_peak_db=_to_db(sample_peak),
        clipped_samples=int(np.sum(np.abs(audio) >= 0.999999)),
    )


def check_source(stats: AudioStats) -> List[Issue]:
    """
    원본이 마스터링할 만한 물건인지 본다.
    여기서 걸리는 것은 마스터링으로 되돌릴 수 없는 손상이다.
    """
    issues: List[Issue] = []

    if stats.is_lossy:
        issues.append(Issue(
            "block",
            f"손실 압축 파일입니다 ({stats.subtype}).",
            "MP3 는 이미 버려진 정보가 있어 마스터링으로 되돌릴 수 없습니다. "
            "수노에서 WAV 로 다시 받으십시오. 음질에 가장 큰 차이를 만드는 한 가지입니다.",
        ))

    if stats.clipped_samples > 0:
        pct = 100.0 * stats.clipped_samples / max(stats.frames * stats.channels, 1)
        issues.append(Issue(
            "warn" if pct < 0.01 else "block",
            f"이미 클리핑된 샘플이 {stats.clipped_samples}개 있습니다 ({pct:.4f}%).",
            "원본에서 이미 찌그러진 것이라 마스터링으로 못 고칩니다. "
            "수노에서 다시 뽑는 편이 낫습니다.",
        ))

    if stats.true_peak_db > 0.0:
        issues.append(Issue(
            "warn",
            f"트루 피크가 이미 0 dBFS 를 넘습니다 ({stats.true_peak_db:.2f} dBTP).",
            "게인을 내리면 해결되지만, 원본에서 이미 리미터가 물렸을 수 있습니다.",
        ))

    if stats.duration_sec < 30:
        issues.append(Issue(
            "warn",
            f"길이가 {stats.duration_sec:.0f}초로 짧습니다.",
            "라우드니스 측정이 부정확할 수 있습니다.",
        ))

    if stats.sample_rate < 44100:
        issues.append(Issue(
            "warn",
            f"샘플레이트가 낮습니다 ({stats.sample_rate} Hz).",
            "44100 Hz 이상을 권합니다.",
        ))

    return issues


# ══════════════════════════════════════════════════════════════
# SECTION 2 — 마스터링
# ══════════════════════════════════════════════════════════════

@dataclass
class MasterResult:
    ok: bool
    src_path: str
    dst_path: str
    before: Optional[AudioStats] = None
    after: Optional[AudioStats] = None
    gain_db: float = 0.0
    used_matchering: bool = False
    lossless: bool = True            # 순수 게인만 걸었는가
    issues: List[Issue] = field(default_factory=list)

    def report(self) -> str:
        lines = [f"마스터링: {'완료' if self.ok else '중단'}"]
        if self.before:
            lines.append(f"\n[전]\n{_indent(self.before.summary())}")
        if self.after:
            lines.append(f"\n[후]\n{_indent(self.after.summary())}")
        if self.before and self.after:
            lines.append(
                f"\n  게인 {self.gain_db:+.2f} dB · "
                f"{'레퍼런스 매칭 적용' if self.used_matchering else '순수 게인'} · "
                f"{'무손실' if self.lossless else '처리 있음'}"
            )
        if self.issues:
            lines.append("")
            lines.extend(f"  {i}" for i in self.issues)
        return "\n".join(lines)


def _indent(text: str, pad: str = "  ") -> str:
    return "\n".join(pad + line for line in text.splitlines())


def master(
    src_path: str,
    dst_path: str,
    *,
    reference: Optional[str] = None,
    target_lufs: float = TARGET_LUFS,
    target_true_peak_db: float = TARGET_TRUE_PEAK_DB,
    subtype: str = "PCM_24",
    allow_lossy_source: bool = False,
) -> MasterResult:
    """
    곡 하나를 마스터링한다.

    reference           : 레퍼런스 음원 경로. 주면 matchering 으로 음색을 맞춘다
    target_lufs         : 목표 라우드니스. 유튜브 기준 -14
    target_true_peak_db : 트루 피크 상한. 유튜브 재인코딩 대비 -1.0
    subtype             : 출력 포맷. PCM_24 권장 (PCM_16 은 dither 없이 쓰지 말 것)
    allow_lossy_source  : MP3 원본을 허용할지. 기본은 막는다

    무손실 보장:
      reference 없이 돌리면 출력은 입력에 상수 하나를 곱한 것이다.
      압축도 리미팅도 EQ 도 걸지 않는다. verify_lossless() 로 확인 가능.
    """
    before = analyze(src_path)
    issues = check_source(before)

    blocking = [i for i in issues if i.severity == "block"]
    if blocking and not allow_lossy_source:
        return MasterResult(
            ok=False, src_path=src_path, dst_path=dst_path,
            before=before, issues=issues,
        )

    audio, sr, _ = _read_float(src_path)
    used_matchering = False

    # ── 1. 레퍼런스 매칭 (선택) ────────────────────────────────
    # matchering 이 주파수 밸런스를 맞춘다. 이 단계만 파형을 바꾼다.
    if reference:
        if not _HAS_MATCHERING:
            issues.append(Issue(
                "warn",
                "matchering 이 설치되지 않아 레퍼런스 매칭을 건너뜁니다.",
                "pip install matchering",
            ))
        elif not os.path.isfile(reference):
            issues.append(Issue("warn", f"레퍼런스 파일이 없습니다: {reference}"))
        else:
            audio, sr = _run_matchering(src_path, reference, sr, issues)
            used_matchering = audio is not None
            if audio is None:
                audio, sr, _ = _read_float(src_path)

    # ── 2. 라우드니스를 목표에 맞춘다 — 순수 게인 ──────────────
    meter = pyln.Meter(sr)
    measured = meter.integrated_loudness(audio if audio.shape[1] > 1 else audio[:, 0])
    gain_db = target_lufs - float(measured)

    # ── 3. 트루 피크가 넘치면 게인을 더 내린다 ────────────────
    # 리미터를 물리지 않는다. 게인 감소는 왜곡이 0 이고, 리미팅은 아니다.
    # 유튜브는 어차피 큰 소리를 눌러서 재생하므로 조금 조용한 편이 안전하다.
    peak_after_gain = _true_peak_db(audio) + gain_db
    if peak_after_gain > target_true_peak_db:
        reduction = peak_after_gain - target_true_peak_db
        gain_db -= reduction
        issues.append(Issue(
            "info",
            f"트루 피크를 지키려고 게인을 {reduction:.2f} dB 더 내렸습니다.",
            f"라우드니스는 {target_lufs + (-reduction):.2f} LUFS 가 됩니다. "
            f"리미터를 물리지 않았으므로 왜곡은 없습니다.",
        ))

    audio = audio * (10.0 ** (gain_db / 20.0))

    # ── 4. 내보내기 ───────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(dst_path)) or ".", exist_ok=True)
    sf.write(dst_path, audio, sr, subtype=subtype)

    after = analyze(dst_path)

    # 목표에 실제로 닿았는지 확인한다
    if after.true_peak_db > target_true_peak_db + 0.1:
        issues.append(Issue(
            "warn",
            f"트루 피크가 목표를 넘었습니다: {after.true_peak_db:.2f} dBTP",
            f"목표는 {target_true_peak_db:.1f} dBTP 입니다.",
        ))
    if after.clipped_samples > 0:
        issues.append(Issue(
            "warn", f"출력에 클리핑 샘플이 {after.clipped_samples}개 있습니다."))

    return MasterResult(
        ok=True, src_path=src_path, dst_path=dst_path,
        before=before, after=after,
        gain_db=gain_db,
        used_matchering=used_matchering,
        lossless=not used_matchering,
        issues=issues,
    )


def _run_matchering(src, reference, sr, issues) -> Tuple[Optional[np.ndarray], int]:
    """matchering 을 돌리고 결과를 읽어온다. 실패하면 (None, sr)."""
    import tempfile
    try:
        mg.log(warning_handler=lambda m: issues.append(Issue("info", f"matchering: {m}")))
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "matched.wav")
            mg.process(
                target=src, reference=reference,
                results=[mg.pcm24(out)],
            )
            audio, new_sr, _ = _read_float(out)
            return audio, new_sr
    except Exception as exc:
        issues.append(Issue("warn", f"레퍼런스 매칭에 실패해 건너뜁니다: {exc}"))
        return None, sr


# ══════════════════════════════════════════════════════════════
# SECTION 3 — 무손실 검증
# ══════════════════════════════════════════════════════════════

def verify_lossless(src_path: str, dst_path: str, tolerance_db: float = -100.0) -> Tuple[bool, float]:
    """
    출력이 입력에 상수를 곱한 것뿐인지 확인한다.

    최적 게인으로 정렬한 뒤 남는 차이(잔차)를 잰다. 순수 게인이었다면
    잔차는 24비트 양자화 바닥 수준이어야 한다.

    반환: (무손실인가, 잔차 dB)
    """
    a, sr_a, _ = _read_float(src_path)
    b, sr_b, _ = _read_float(dst_path)

    if sr_a != sr_b:
        return False, 0.0
    n = min(len(a), len(b))
    if n == 0 or a.shape[1] != b.shape[1]:
        return False, 0.0
    a, b = a[:n], b[:n]

    # 최소제곱으로 최적 게인을 구한다
    denom = float(np.sum(a * a))
    if denom < _EPS:
        return False, 0.0
    gain = float(np.sum(a * b)) / denom

    residual = b - a * gain
    rms = float(np.sqrt(np.mean(residual ** 2)))
    residual_db = _to_db(rms)

    return residual_db <= tolerance_db, residual_db


# ══════════════════════════════════════════════════════════════
# SECTION 4 — 여러 곡
# ══════════════════════════════════════════════════════════════

def master_batch(
    src_paths: List[str],
    out_dir: str,
    *,
    reference: Optional[str] = None,
    on_progress=None,
    **kwargs,
) -> List[MasterResult]:
    """
    여러 곡을 같은 기준으로 마스터링한다.
    같은 reference 를 쓰면 20곡이 한 앨범처럼 들린다.

    한 곡이 실패해도 나머지를 계속한다. 이미 만들어진 것은 건너뛴다.
    """
    say = on_progress or (lambda _m: None)
    results: List[MasterResult] = []
    total = len(src_paths)

    for i, src in enumerate(src_paths, 1):
        name = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(out_dir, f"{name}_mastered.wav")

        if os.path.isfile(dst):
            say(f"[{i}/{total}] {name} — 이미 있음, 건너뜀")
            continue

        say(f"[{i}/{total}] {name} — 처리 중...")
        try:
            r = master(src, dst, reference=reference, **kwargs)
            results.append(r)
            if r.ok and r.after:
                say(f"[{i}/{total}] {name} — {r.after.lufs:.1f} LUFS · "
                    f"{r.after.true_peak_db:.1f} dBTP")
            else:
                say(f"[{i}/{total}] {name} — 중단: "
                    f"{r.issues[0].message if r.issues else '알 수 없음'}")
        except Exception as exc:
            say(f"[{i}/{total}] {name} — 실패: {exc}")
            results.append(MasterResult(
                ok=False, src_path=src, dst_path=dst,
                issues=[Issue("block", str(exc))],
            ))

    return results


# ══════════════════════════════════════════════════════════════
# SECTION 5 — 명령줄
# ══════════════════════════════════════════════════════════════

def main(argv: Optional[List[str]] = None) -> int:
    """
    사용법:
        python mastering.py analyze 곡.wav
        python mastering.py master 곡.wav 결과.wav [레퍼런스.wav]
    """
    import sys
    args = list(argv if argv is not None else sys.argv[1:])
    if not args:
        print(main.__doc__)
        return 2

    cmd = args[0]
    if cmd == "analyze" and len(args) >= 2:
        stats = analyze(args[1])
        print(stats.summary())
        for issue in check_source(stats):
            print(f"\n{issue}")
        return 0

    if cmd == "master" and len(args) >= 3:
        result = master(args[1], args[2], reference=args[3] if len(args) > 3 else None)
        print(result.report())
        if result.ok and not result.used_matchering:
            lossless, residual = verify_lossless(args[1], args[2])
            print(f"\n  무손실 검증: {'통과' if lossless else '실패'} "
                  f"(잔차 {residual:.1f} dB)")
        return 0 if result.ok else 1

    print(main.__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
