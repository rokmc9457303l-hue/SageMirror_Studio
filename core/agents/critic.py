# -*- coding: utf-8 -*-
"""
core/agents/critic.py — Critic (4층 검증 에이전트)

Layer 1: 사실검증 (할루시네이션 탐지)
Layer 2: 출처검증 (성경/철학 인용 원전 확인)
Layer 3: 완성도검증 (필수 필드 + 분량 기준)
Layer 4: 일관성검증 (채널 톤/금지표현/프로필 일치)
"""

from .base import BaseAgent
from core.critic.data_request import DataIssue, DataRequest
from core.critic.patterns import (
    scan_hallucination,
    check_forbidden,
    BIBLE_VERSE_PATTERN,
    PHILOSOPHER_PATTERN,
    COMPLETENESS_RULES,
)


class CriticAgent(BaseAgent):
    name = "Critic"
    role = "4층 품질 검증관"

    # ── 최소 통과 점수 기준 ──────────────────────────────────────────
    MIN_PASS_SCORE = 70.0  # 100점 만점

    def specific_instructions(self) -> str:
        return (
            "당신은 콘텐츠 품질 검증 전문가입니다.\n"
            "4개 레이어에서 순차적으로 검증합니다:\n"
            "Layer1: 할루시네이션/근거 없는 주장 탐지\n"
            "Layer2: 성경/철학 인용 원전 확인\n"
            "Layer3: 필수 필드 완성도 점검\n"
            "Layer4: 채널 톤/금지 표현/일관성 점검\n"
            "각 문제를 구체적으로 기록하고 자동 수정 가능 여부를 표시합니다."
        )

    def execute(self, context: dict) -> dict:
        """4층 검증 실행. 결과: DataRequest 포함 dict 반환"""
        part = context.get("part", 0)
        topic = context.get("topic", "")

        dr = DataRequest(part=part, topic=topic)

        # Layer 1: 사실검증
        self._layer1_fact_check(context, dr)

        # Layer 2: 출처검증
        self._layer2_source_check(context, dr)

        # Layer 3: 완성도검증
        self._layer3_completeness(context, dr)

        # Layer 4: 일관성검증
        self._layer4_consistency(context, dr)

        # 총점 계산 (100점 만점)
        dr.total_score = self._calc_score(dr)
        dr.passed = dr.total_score >= self.MIN_PASS_SCORE and not dr.has_blockers

        status = "APPROVED" if dr.passed else "NEEDS_DATA"
        self.log(
            f"Part{part} 검증 완료. 점수={dr.total_score:.1f} "
            f"{'통과' if dr.passed else '실패'} "
            f"이슈={len(dr.issues)}개"
        )

        return {
            "passed": dr.passed,
            "score": dr.total_score,
            "status": status,
            "data_request": dr.to_dict(),
            "summary": dr.summary_text(),
            "agent": self.name,
        }

    # ── Layer 1: 사실검증 ────────────────────────────────────────────

    def _layer1_fact_check(self, context: dict, dr: DataRequest):
        """할루시네이션 패턴 스캔"""
        full_text = self._extract_all_text(context)
        findings = scan_hallucination(full_text)

        for desc, severity, matched, auto_fix, hint in findings:
            dr.add_issue(DataIssue(
                layer=1,
                layer_name="사실검증",
                issue_type="HALLUCINATION",
                field_name="본문",
                detail=f"{desc}: '{matched[:60]}'",
                original_text=matched,
                suggestion=f"출처를 명시하거나 표현을 완화하세요",
                severity=severity,
                auto_fixable=auto_fix,
                search_query=hint,
            ))

    # ── Layer 2: 출처검증 ────────────────────────────────────────────

    def _layer2_source_check(self, context: dict, dr: DataRequest):
        """성경 구절 + 철학 인용 원전 확인"""
        full_text = self._extract_all_text(context)

        # 성경 구절 감지
        bible_matches = BIBLE_VERSE_PATTERN.findall(full_text)
        if bible_matches:
            sources = context.get("research_sources", [])
            has_bible_source = any("bible" in str(s).lower() or "성경" in str(s) for s in sources)
            if not has_bible_source:
                dr.add_issue(DataIssue(
                    layer=2,
                    layer_name="출처검증",
                    issue_type="NO_SOURCE",
                    field_name="성경 인용",
                    detail=f"성경 구절 감지됨({', '.join(bible_matches[:3])})이나 출처 자료 없음",
                    suggestion="출처 자료에 성경 구절 원문 포함 필요",
                    severity="ERROR",
                    auto_fixable=True,
                    search_query=f"성경 {bible_matches[0]} 원문 해석",
                ))

        # 철학자 인용 감지
        phil_matches = PHILOSOPHER_PATTERN.findall(full_text)
        if phil_matches:
            sources = context.get("research_sources", [])
            has_phil_source = any(
                any(ph in str(s) for ph in phil_matches)
                for s in sources
            )
            if not has_phil_source and len(phil_matches) > 0:
                dr.add_issue(DataIssue(
                    layer=2,
                    layer_name="출처검증",
                    issue_type="NO_SOURCE",
                    field_name="철학 인용",
                    detail=f"철학자 언급({', '.join(set(phil_matches[:3]))})이나 원전 자료 없음",
                    suggestion="해당 철학자의 원전 인용 또는 참조 자료 추가 필요",
                    severity="WARN",
                    auto_fixable=True,
                    search_query=f"{phil_matches[0]} 명언 원전 출처",
                ))

        # 자료 소스 수 검사
        sources = context.get("research_sources", [])
        if len(sources) < 1:
            dr.add_issue(DataIssue(
                layer=2,
                layer_name="출처검증",
                issue_type="NO_SOURCE",
                field_name="research_sources",
                detail="출처 자료가 전혀 없습니다",
                suggestion="최소 1개 이상의 출처 자료 필요",
                severity="ERROR",
                auto_fixable=True,
                search_query=context.get("topic", "") + " 관련 자료",
            ))

    # ── Layer 3: 완성도검증 ──────────────────────────────────────────

    def _layer3_completeness(self, context: dict, dr: DataRequest):
        """필수 필드 존재 + 최소 길이 검사"""
        for field_name, rules in COMPLETENESS_RULES.items():
            value = context.get(field_name)

            if rules.get("required") and (value is None or value == "" or value == []):
                dr.add_issue(DataIssue(
                    layer=3,
                    layer_name="완성도검증",
                    issue_type="INCOMPLETE",
                    field_name=field_name,
                    detail=f"필수 필드 '{field_name}' 누락",
                    severity="ERROR",
                    auto_fixable=False,
                ))
                continue

            if value is None:
                continue

            # 문자열 최소 길이
            min_len = rules.get("min_len", 0)
            if isinstance(value, str) and len(value) < min_len:
                dr.add_issue(DataIssue(
                    layer=3,
                    layer_name="완성도검증",
                    issue_type="INCOMPLETE",
                    field_name=field_name,
                    detail=f"'{field_name}' 내용 너무 짧음 ({len(value)}/{min_len}자)",
                    severity="WARN",
                    auto_fixable=False,
                ))

            # 리스트 최소 개수
            min_items = rules.get("min_items", 0)
            if isinstance(value, list) and len(value) < min_items:
                dr.add_issue(DataIssue(
                    layer=3,
                    layer_name="완성도검증",
                    issue_type="INCOMPLETE",
                    field_name=field_name,
                    detail=f"'{field_name}' 항목 부족 ({len(value)}/{min_items}개)",
                    severity="WARN",
                    auto_fixable=False,
                ))

    # ── Layer 4: 일관성검증 ──────────────────────────────────────────

    def _layer4_consistency(self, context: dict, dr: DataRequest):
        """금지 표현 + 채널 프로필 일관성"""
        full_text = self._extract_all_text(context)
        profile = self.profile

        # 금지 표현 검사
        extra_forbidden = profile.get("forbidden_expressions", [])
        found_forbidden = check_forbidden(full_text, extra_forbidden)

        for expr in found_forbidden:
            dr.add_issue(DataIssue(
                layer=4,
                layer_name="일관성검증",
                issue_type="FORBIDDEN",
                field_name="본문",
                detail=f"금지 표현 발견: '{expr}'",
                original_text=expr,
                suggestion=f"'{expr}'을 제거하고 채널 톤에 맞는 표현으로 교체",
                severity="ERROR",
                auto_fixable=False,
            ))

        # 타겟 연령층 부적합 표현 (Profile의 forbidden_youth_terms 또는 기본값 사용)
        target = profile.get("target_audience", "")
        youth_terms = profile.get("forbidden_youth_terms", ["MZ", "레전드", "ㄹㅇ", "킹갓", "밈", "짤", "갓생"])
        if target and youth_terms:
            for term in youth_terms:
                if term in full_text:
                    dr.add_issue(DataIssue(
                        layer=4,
                        layer_name="일관성검증",
                        issue_type="INCONSISTENT",
                        field_name="본문",
                        detail=f"타겟({target}) 부적합 표현: '{term}'",
                        suggestion=f"'{term}' 제거 또는 타겟 친화적 표현으로 교체",
                        severity="ERROR",
                        auto_fixable=False,
                    ))

    # ── 공통 유틸 ────────────────────────────────────────────────────

    def _extract_all_text(self, context: dict) -> str:
        """context 내 모든 문자열 값을 합쳐 반환"""
        parts = []
        for v in context.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                parts.extend(str(item) for item in v)
            elif isinstance(v, dict):
                parts.extend(str(vv) for vv in v.values())
        return " ".join(parts)

    def _calc_score(self, dr: DataRequest) -> float:
        """이슈 수 기반 100점 감점식 점수 계산"""
        score = 100.0
        deductions = {
            "CRITICAL": 30.0,
            "ERROR": 15.0,
            "WARN": 5.0,
        }
        for issue in dr.issues:
            score -= deductions.get(issue.severity, 0)
        return max(0.0, score)
