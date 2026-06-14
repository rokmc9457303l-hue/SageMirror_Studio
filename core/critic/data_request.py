# -*- coding: utf-8 -*-
"""
core/critic/data_request.py — 검수 실패 시 자료 요청 데이터 클래스

Critic이 검증 실패 항목을 DataIssue로 기록하고
DataRequest로 묶어 Scout/UI에 전달.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class DataIssue:
    """단일 검수 실패 항목"""

    layer: int                          # 1~4 (층)
    layer_name: str                     # 사실검증 / 출처검증 / 완성도검증 / 일관성검증
    issue_type: str                     # HALLUCINATION / NO_SOURCE / INCOMPLETE / INCONSISTENT / FORBIDDEN
    field_name: str                     # 문제 발생 필드
    detail: str                         # 구체적 문제 설명
    original_text: str = ""             # 문제가 된 원문
    suggestion: str = ""                # 권고 수정 방향
    severity: str = "WARN"             # WARN / ERROR / CRITICAL
    auto_fixable: bool = False          # Scout 자동 보강 가능 여부
    search_query: Optional[str] = None  # Scout가 사용할 검색 쿼리

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "layer_name": self.layer_name,
            "issue_type": self.issue_type,
            "field_name": self.field_name,
            "detail": self.detail,
            "original_text": self.original_text,
            "suggestion": self.suggestion,
            "severity": self.severity,
            "auto_fixable": self.auto_fixable,
            "search_query": self.search_query,
        }


@dataclass
class DataRequest:
    """Critic이 생성하는 자료 요청서"""

    part: int
    topic: str
    issues: list = field(default_factory=list)        # List[DataIssue]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_score: float = 0.0
    passed: bool = False
    auto_fixable_count: int = 0
    manual_needed_count: int = 0

    def add_issue(self, issue: DataIssue):
        self.issues.append(issue)
        if issue.auto_fixable:
            self.auto_fixable_count += 1
        else:
            self.manual_needed_count += 1

    @property
    def critical_issues(self) -> list:
        return [i for i in self.issues if i.severity == "CRITICAL"]

    @property
    def error_issues(self) -> list:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warning_issues(self) -> list:
        return [i for i in self.issues if i.severity == "WARN"]

    @property
    def has_blockers(self) -> bool:
        return len(self.critical_issues) > 0 or len(self.error_issues) > 0

    def get_scout_queries(self) -> list:
        """Scout 자동 검색에 사용할 쿼리 목록"""
        return [
            i.search_query
            for i in self.issues
            if i.auto_fixable and i.search_query
        ]

    def to_dict(self) -> dict:
        return {
            "part": self.part,
            "topic": self.topic,
            "created_at": self.created_at,
            "total_score": self.total_score,
            "passed": self.passed,
            "auto_fixable_count": self.auto_fixable_count,
            "manual_needed_count": self.manual_needed_count,
            "issues": [i.to_dict() for i in self.issues],
        }

    def summary_text(self) -> str:
        """우측 패널 표시용 요약 텍스트"""
        lines = [
            f"## 검수 결과 — Part {self.part}",
            f"주제: {self.topic}",
            f"점수: {self.total_score:.1f} | {'✅ 통과' if self.passed else '❌ 실패'}",
            f"이슈: 치명({len(self.critical_issues)}) 오류({len(self.error_issues)}) 경고({len(self.warning_issues)})",
            "",
        ]
        for i in self.issues:
            icon = {"CRITICAL": "🔴", "ERROR": "🟠", "WARN": "🟡"}.get(i.severity, "⚪")
            lines.append(f"{icon} [Layer{i.layer}:{i.layer_name}] {i.field_name}")
            lines.append(f"   → {i.detail}")
            if i.suggestion:
                lines.append(f"   💡 {i.suggestion}")
        return "\n".join(lines)
