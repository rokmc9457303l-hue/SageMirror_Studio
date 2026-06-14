# -*- coding: utf-8 -*-
"""
core/agents/quality_assurance.py — QualityAssuranceAgent (최종 품질 검사)

역할:
- Part 1~7 전체 Packet을 받아 영상 출시 전 종합 점검
- 13개 체크리스트 자동 검사
- 떡상 확률 계산
- 개선 제안 생성
"""

from .base import BaseAgent


class QualityAssuranceAgent(BaseAgent):
    name = "QA Master"
    role = "영상 출시 전 종합 품질 검사"

    # 13개 체크리스트
    CHECKLIST_KEYS = [
        "주제_명확성",
        "제목_클릭유도",
        "썸네일_시선유도",
        "도입_5초_훅",
        "감정_곡선",
        "대본_일관성",
        "이미지_캐릭터_일관성",
        "나레이션_휴먼터치",
        "BGM_감정매칭",
        "숏폼_파생점",
        "출처_표기_완전성",
        "Profile_부합도",
        "트렌드_부합도",
    ]

    # 각 항목 배점
    WEIGHTS = {
        "주제_명확성":        10,
        "제목_클릭유도":      10,
        "썸네일_시선유도":     8,
        "도입_5초_훅":       10,
        "감정_곡선":          8,
        "대본_일관성":        10,
        "이미지_캐릭터_일관성": 7,
        "나레이션_휴먼터치":   8,
        "BGM_감정매칭":       5,
        "숏폼_파생점":        5,
        "출처_표기_완전성":   10,
        "Profile_부합도":     5,
        "트렌드_부합도":       4,
    }

    def specific_instructions(self) -> str:
        p = self.profile
        ch_name = p.get("channel_name", "이 채널")
        return (
            f"당신은 {ch_name} 채널의 영상 출시 전 최종 품질 검사관입니다.\n"
            "13개 체크리스트를 엄격하게 검사하고 떡상 확률을 계산합니다.\n"
            "통과 기준: 총점 75점 이상, 필수 항목(주제/제목/훅/출처) 모두 통과.\n"
            "개선 제안은 구체적이고 실행 가능하게 작성합니다."
        )

    def execute(self, context: dict) -> dict:
        all_packets = context.get("all_packets", context)
        return self.final_check(all_packets)

    def final_check(self, all_packets: dict) -> dict:
        """전체 Packet 종합 품질 검사"""
        self.log("최종 QA 검사 시작")

        checklist = {k: False for k in self.CHECKLIST_KEYS}
        improvements = []
        details = {}

        # ── 개별 항목 검사 ──────────────────────────────────
        checklist["주제_명확성"], d = self._check_topic_clarity(all_packets)
        details["주제_명확성"] = d
        if not checklist["주제_명확성"]:
            improvements.append("주제를 한 문장으로 명확히 정의하세요")

        checklist["제목_클릭유도"], d = self._check_title(all_packets)
        details["제목_클릭유도"] = d
        if not checklist["제목_클릭유도"]:
            improvements.append("제목에 감정 자극 단어 또는 수사 의문문을 추가하세요")

        checklist["썸네일_시선유도"], d = self._check_thumbnail(all_packets)
        details["썸네일_시선유도"] = d

        checklist["도입_5초_훅"], d = self._check_hook(all_packets)
        details["도입_5초_훅"] = d
        if not checklist["도입_5초_훅"]:
            improvements.append("대본 첫 5초(씬 001~002)에 강력한 훅을 삽입하세요")

        checklist["감정_곡선"], d = self._check_emotion_curve(all_packets)
        details["감정_곡선"] = d

        checklist["대본_일관성"], d = self._check_script_consistency(all_packets)
        details["대본_일관성"] = d

        checklist["이미지_캐릭터_일관성"], d = self._check_visual_consistency(all_packets)
        details["이미지_캐릭터_일관성"] = d

        checklist["나레이션_휴먼터치"], d = self._check_narration(all_packets)
        details["나레이션_휴먼터치"] = d

        checklist["BGM_감정매칭"], d = self._check_bgm(all_packets)
        details["BGM_감정매칭"] = d

        checklist["숏폼_파생점"], d = self._check_shorts(all_packets)
        details["숏폼_파생점"] = d

        checklist["출처_표기_완전성"], d = self._check_citations(all_packets)
        details["출처_표기_완전성"] = d
        if not checklist["출처_표기_완전성"]:
            improvements.append("모든 인용구에 [SOURCE: ...] 표기를 추가하세요")

        checklist["Profile_부합도"], d = self._check_profile_match(all_packets)
        details["Profile_부합도"] = d
        if not checklist["Profile_부합도"]:
            improvements.append("금지 표현을 제거하고 채널 톤을 재검토하세요")

        checklist["트렌드_부합도"], d = self._check_trend(all_packets)
        details["트렌드_부합도"] = d

        # ── 총점 계산 ────────────────────────────────────────
        total_score = sum(
            self.WEIGHTS.get(k, 5) for k, v in checklist.items() if v
        )

        # ── 떡상 확률 계산 ───────────────────────────────────
        viral_probability = self._calc_viral_probability(checklist, total_score, all_packets)

        # ── 필수 항목 통과 여부 ──────────────────────────────
        mandatory = ["주제_명확성", "제목_클릭유도", "도입_5초_훅", "출처_표기_완전성"]
        all_mandatory_pass = all(checklist[k] for k in mandatory)
        passed = total_score >= 75 and all_mandatory_pass

        self.log(f"QA 완료: 총점={total_score} 떡상확률={viral_probability:.1%} {'통과' if passed else '실패'}")

        return {
            "총점": total_score,
            "passed": passed,
            "all_mandatory_pass": all_mandatory_pass,
            "체크리스트": checklist,
            "세부사항": details,
            "떡상_확률": viral_probability,
            "개선_제안": improvements,
            "agent": self.name,
        }

    # ── 개별 항목 검사 메서드 ────────────────────────────────

    def _check_topic_clarity(self, pkts: dict) -> tuple:
        p1 = pkts.get("p1_packet") or pkts.get(1, {})
        topic = str(p1.get("topic", "") if isinstance(p1, dict) else "")
        ok = bool(topic) and len(topic) > 5
        return ok, f"주제: {topic[:50] if topic else '없음'}"

    def _check_title(self, pkts: dict) -> tuple:
        p2 = pkts.get("p2_packet") or pkts.get(2, {})
        candidates = []
        if isinstance(p2, dict):
            candidates = p2.get("title_candidates", [])
        ok = bool(candidates) and len(candidates) >= 3
        return ok, f"제목 후보 {len(candidates)}개"

    def _check_thumbnail(self, pkts: dict) -> tuple:
        p4 = pkts.get("p4_packet") or pkts.get(4, {})
        has = bool(p4) and isinstance(p4, dict) and len(p4) > 2
        return has, "이미지 패킷 존재" if has else "p4_packet 없음"

    def _check_hook(self, pkts: dict) -> tuple:
        p3 = pkts.get("p3_packet") or pkts.get(3, {})
        script = ""
        if isinstance(p3, dict):
            script = str(p3.get("script", "") or p3.get("scenes", ""))
        hook_keywords = ["바로", "지금", "당신", "혹시", "들어보셨나요", "아십니까", "왜"]
        has_hook = any(kw in script[:300] for kw in hook_keywords) if script else False
        return has_hook, "훅 키워드 감지됨" if has_hook else "첫 씬에 훅 없음"

    def _check_emotion_curve(self, pkts: dict) -> tuple:
        p3 = pkts.get("p3_packet") or pkts.get(3, {})
        has = bool(p3) and isinstance(p3, dict)
        return has, "대본 패킷 존재" if has else "p3_packet 없음"

    def _check_script_consistency(self, pkts: dict) -> tuple:
        p3 = pkts.get("p3_packet") or pkts.get(3, {})
        p = self.profile
        forbidden = p.get("forbidden_expressions", [])
        script = ""
        if isinstance(p3, dict):
            script = str(p3.get("script", ""))
        violations = [f for f in forbidden if f in script]
        ok = len(violations) == 0
        return ok, f"금지 표현 {len(violations)}개 감지" if violations else "일관성 OK"

    def _check_visual_consistency(self, pkts: dict) -> tuple:
        p4 = pkts.get("p4_packet") or pkts.get(4, {})
        has = bool(p4)
        return has, "이미지 패킷 확인 필요" if not has else "이미지 패킷 존재"

    def _check_narration(self, pkts: dict) -> tuple:
        p6 = pkts.get("p6_packet") or pkts.get(6, {})
        has = bool(p6)
        return has, "나레이션 패킷 존재" if has else "p6_packet 없음"

    def _check_bgm(self, pkts: dict) -> tuple:
        p6 = pkts.get("p6_packet") or pkts.get(6, {})
        bgm = ""
        if isinstance(p6, dict):
            bgm = str(p6.get("bgm_cuesheet", "") or p6.get("bgm", ""))
        has = bool(bgm)
        return has, "BGM 큐시트 존재" if has else "BGM 큐시트 없음"

    def _check_shorts(self, pkts: dict) -> tuple:
        p7 = pkts.get("p7_packet") or pkts.get(7, {})
        has = bool(p7)
        return has, "숏폼 패킷 존재" if has else "p7_packet 없음"

    def _check_citations(self, pkts: dict) -> tuple:
        import re
        all_text = " ".join(
            str(v) for pkt in pkts.values() if isinstance(pkt, dict)
            for v in pkt.values() if isinstance(v, str)
        )
        sources = re.findall(r"\[SOURCE:", all_text)
        need_verify = re.findall(r"\[NEED_VERIFY\]", all_text)
        ok = len(sources) >= 3 and len(need_verify) == 0
        return ok, f"출처 {len(sources)}개, NEED_VERIFY {len(need_verify)}개"

    def _check_profile_match(self, pkts: dict) -> tuple:
        from core.critic.patterns import check_forbidden
        p = self.profile
        forbidden = p.get("forbidden_expressions", [])
        all_text = " ".join(
            str(v) for pkt in pkts.values() if isinstance(pkt, dict)
            for v in pkt.values() if isinstance(v, str)
        )
        found = check_forbidden(all_text, forbidden)
        return len(found) == 0, f"금지 표현 {len(found)}개: {', '.join(found[:3])}" if found else "Profile 부합 OK"

    def _check_trend(self, pkts: dict) -> tuple:
        p1 = pkts.get("p1_packet") or pkts.get(1, {})
        has_trend = isinstance(p1, dict) and bool(p1.get("trend_analysis"))
        return has_trend, "트렌드 분석 포함" if has_trend else "트렌드 분석 없음 (선택)"

    # ── 떡상 확률 계산 ────────────────────────────────────────

    def _calc_viral_probability(self, checklist: dict, score: int, pkts: dict) -> float:
        """
        떡상 확률 = 기본 점수 기반 + 핵심 요소 가중치
        핵심 요소: 훅 + 감정곡선 + 제목 + Profile 부합
        """
        base = score / 100.0

        # 핵심 4개 모두 통과 시 보너스
        core_keys = ["도입_5초_훅", "감정_곡선", "제목_클릭유도", "Profile_부합도"]
        core_pass = sum(1 for k in core_keys if checklist.get(k, False))
        bonus = core_pass * 0.05

        probability = min(0.95, base * 0.7 + bonus)
        return round(probability, 3)

    def format_report(self, result: dict) -> str:
        """UI 표시용 QA 리포트 문자열"""
        score = result.get("총점", 0)
        passed = result.get("passed", False)
        viral = result.get("떡상_확률", 0)
        checklist = result.get("체크리스트", {})
        improvements = result.get("개선_제안", [])

        lines = [
            f"## 🏆 QA 최종 점검 결과",
            f"총점: **{score}/100** | {'✅ 출시 가능' if passed else '❌ 보완 필요'}",
            f"떡상 확률: **{viral:.1%}**",
            "",
            "### 체크리스트",
        ]
        weights = self.WEIGHTS
        for k, v in checklist.items():
            icon = "✅" if v else "❌"
            lines.append(f"{icon} {k.replace('_', ' ')} ({weights.get(k, 5)}점)")

        if improvements:
            lines += ["", "### 개선 제안"]
            for i, imp in enumerate(improvements, 1):
                lines.append(f"{i}. {imp}")

        return "\n".join(lines)
