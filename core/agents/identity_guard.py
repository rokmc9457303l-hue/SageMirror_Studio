# -*- coding: utf-8 -*-
"""
core/agents/identity_guard.py — IdentityGuardAgent (Task 26)

매 Part마다 채널 정체성 일관성 검사.
IDENTITY.md 기준으로 금지 표현·톤·타겟 일치 여부 자동 판정.
"""

import re
from .base import BaseAgent


class IdentityGuardAgent(BaseAgent):
    name = "IdentityGuard"
    role = "채널 정체성 일관성 검사관"

    def specific_instructions(self) -> str:
        return (
            "당신은 채널 정체성 일관성 검사관입니다.\n"
            "IDENTITY.md의 기준을 엄격하게 적용하여\n"
            "금지 표현, 톤 불일치, 타겟 불일치를 찾아냅니다.\n"
            "통과 기준: 위반 없음 + 톤 일치 + 타겟 부합."
        )

    def execute(self, context: dict) -> dict:
        content     = context.get("content", "")
        channel_key = context.get("channel_key", "")
        return self.check(content, channel_key)

    def check(self, content: str, channel_key: str = None) -> dict:
        """채널 정체성 검사 실행"""
        if channel_key is None:
            try:
                import streamlit as st
                channel_key = st.session_state.get("current_channel_profile", "")
            except Exception:
                channel_key = ""

        self.log(f"정체성 검사 시작: {channel_key}")

        # IDENTITY.md 로드
        identity = self._load_identity(channel_key)
        profile  = self.profile

        violations = []

        # ── 1. 금지 표현 검사 ────────────────────────────
        forbidden = profile.get("forbidden_expressions", [])
        if identity:
            # IDENTITY.md에서 금지 표현 추출 (보강)
            id_forbidden = self._extract_forbidden_from_identity(identity)
            forbidden = list(set(forbidden + id_forbidden))

        for word in forbidden:
            if word and word in content:
                violations.append({
                    "type":     "금지_표현",
                    "detail":   f"'{word}' 사용됨",
                    "severity": "ERROR",
                    "fixable":  True,
                })

        # ── 2. 톤 불일치 검사 ───────────────────────────
        tone_ok, tone_detail = self._check_tone(content, profile)
        if not tone_ok:
            violations.append({
                "type":     "톤_불일치",
                "detail":   tone_detail,
                "severity": "WARN",
                "fixable":  False,
            })

        # ── 3. 타겟 시청자 불일치 검사 ──────────────────
        target_ok, target_detail = self._check_target(content, profile)
        if not target_ok:
            violations.append({
                "type":     "타겟_불일치",
                "detail":   target_detail,
                "severity": "WARN",
                "fixable":  False,
            })

        # ── 4. AI 냄새 패턴 검사 ────────────────────────
        ai_violations = self._check_ai_smell(content)
        violations.extend(ai_violations)

        passed = all(v["severity"] != "ERROR" for v in violations)
        self.log(f"검사 완료: {'통과' if passed else '실패'} 위반 {len(violations)}건")

        return {
            "passed":     passed,
            "violations": violations,
            "channel":    channel_key,
            "agent":      self.name,
        }

    def _load_identity(self, channel_key: str) -> str:
        if not channel_key:
            return ""
        try:
            from core.md_loader import load_channel_md
            return load_channel_md(channel_key, "IDENTITY.md")
        except Exception:
            return ""

    def _extract_forbidden_from_identity(self, identity_text: str) -> list:
        """IDENTITY.md에서 금지 표현 섹션 파싱"""
        forbidden = []
        in_section = False
        for line in identity_text.splitlines():
            if "금지 표현" in line:
                in_section = True
                continue
            if in_section:
                if line.startswith("#"):
                    break
                stripped = line.strip().lstrip("-").strip()
                if stripped and not stripped.startswith("선호"):
                    forbidden.append(stripped)
        return [f for f in forbidden if f and len(f) > 1]

    def _check_tone(self, content: str, profile: dict) -> tuple:
        """채널 톤 일치 여부 (AI 강의 말투 감지)"""
        tone = profile.get("tone", "")
        if not tone:
            return True, ""

        # "차분함" / "진지함" 채널에서 강의 말투 감지
        if any(t in tone for t in ("차분", "진지", "철학", "절제")):
            lecture_patterns = [
                r"오늘은\s+.*?(알아보겠습니다|배워보겠습니다)",
                r"(먼저|우선).{0,10}(설명|소개)드리겠습니다",
                r"정리하자면",
                r"요약하면",
                r"결론적으로",
            ]
            for pat in lecture_patterns:
                if re.search(pat, content):
                    return False, f"강의 말투 감지 (톤: {tone})"

        # "활기참" 채널에서 지나치게 느린 표현 감지
        if "활기" in tone:
            slow_patterns = [r"조용히\s+바라", r"말없이\s+앉"]
            for pat in slow_patterns:
                if re.search(pat, content):
                    return False, f"채널 톤과 상반된 표현 (톤: {tone})"

        return True, ""

    def _check_target(self, content: str, profile: dict) -> tuple:
        """타겟 시청자 불일치 감지"""
        target = profile.get("target_audience", "")
        if not target:
            return True, ""

        # 시니어 타겟 채널에서 1020 밈/표현 감지
        if any(t in target for t in ("시니어", "50~70", "40~70", "4070", "중장년")):
            youth_patterns = [r"ㅋㅋ", r"ㅠㅠ", r"레전드", r"갓벽", r"소름돋", r"미쳤다"]
            for pat in youth_patterns:
                if re.search(pat, content):
                    return False, f"타겟({target}) 부적합 표현 감지"

        return True, ""

    def _check_ai_smell(self, content: str) -> list:
        """AI 냄새 패턴 감지"""
        issues = []
        patterns = [
            (r"(물론|당연히|분명히)\s*,?\s*(이런|그런|저런)", "AI 상투어: 물론/당연히"),
            (r"그렇기\s*때문에\s*우리는", "AI 상투어: 그렇기 때문에 우리는"),
            (r"중요한\s*점은", "AI 상투어: 중요한 점은"),
            (r"이\s*글에서는", "AI 자기참조"),
            (r"도움이\s*되었으면", "AI 마무리 상투어"),
        ]
        for pat, desc in patterns:
            if re.search(pat, content):
                issues.append({
                    "type":     "AI_냄새",
                    "detail":   desc,
                    "severity": "WARN",
                    "fixable":  True,
                })
        return issues

    def format_report(self, result: dict) -> str:
        """UI 표시용 리포트"""
        passed     = result.get("passed", False)
        violations = result.get("violations", [])
        channel    = result.get("channel", "")

        lines = [
            f"## {'✅' if passed else '❌'} 정체성 검사 — {channel}",
            f"위반: {len(violations)}건",
            "",
        ]
        for v in violations:
            icon = "❌" if v["severity"] == "ERROR" else "⚠️"
            lines.append(f"{icon} [{v['type']}] {v['detail']}"
                         + (" (자동수정 가능)" if v.get("fixable") else ""))
        if not violations:
            lines.append("✅ 정체성 일관성 유지")
        return "\n".join(lines)
