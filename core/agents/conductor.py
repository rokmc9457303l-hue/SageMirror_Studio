# -*- coding: utf-8 -*-
"""
core/agents/conductor.py — Conductor (지휘자 에이전트)

역할:
- 전체 8파트 파이프라인 상태 관리
- Part 간 packet 전달 조율
- 검증 실패 시 재시도 지시
- 진행 상황 요약 보고
"""

from .base import BaseAgent


class ConductorAgent(BaseAgent):
    name = "Conductor"
    role = "파이프라인 지휘자"

    def specific_instructions(self) -> str:
        return (
            "당신은 8파트 콘텐츠 제작 파이프라인의 지휘자입니다.\n"
            "각 Part 에이전트의 실행 순서를 조율하고 packet 상태를 관리합니다.\n"
            "검증 실패 시 해당 Part를 재실행 지시하고 최대 3회까지 재시도합니다.\n"
            "진행 상황을 간결하게 보고합니다."
        )

    def execute(self, context: dict) -> dict:
        """파이프라인 전체 상태 점검 후 다음 실행 지시 반환"""
        from core.state import get_state

        packets = get_state("packets", {})
        status_report = []
        next_action = None

        for part_num in range(1, 9):
            key = f"p{part_num}_packet"
            pkt = packets.get(key, {})
            status = pkt.get("status", "PENDING")
            topic = pkt.get("topic", "")
            status_report.append({
                "part": part_num,
                "status": status,
                "topic": topic,
                "version": pkt.get("version", ""),
            })

            if status in ("PENDING", "FAILED") and next_action is None:
                next_action = {"run_part": part_num, "reason": f"Part {part_num} 상태: {status}"}

        self.log(f"파이프라인 점검 완료. 다음 실행: {next_action}")

        return {
            "pipeline_status": status_report,
            "next_action": next_action,
            "agent": self.name,
        }

    def get_pipeline_summary(self) -> str:
        """UI 표시용 파이프라인 요약 텍스트"""
        result = self.execute({})
        lines = ["## 파이프라인 현황"]
        icons = {
            "PENDING": "⬜",
            "DRAFT": "🔵",
            "REVIEW": "🟡",
            "APPROVED": "✅",
            "LOCKED": "🔒",
            "PUSHED": "🚀",
            "FAILED": "❌",
        }
        for s in result["pipeline_status"]:
            icon = icons.get(s["status"], "⬜")
            topic_txt = f" — {s['topic'][:20]}" if s["topic"] else ""
            lines.append(f"{icon} Part {s['part']}{topic_txt} [{s['status']}]")
        if result["next_action"]:
            na = result["next_action"]
            lines.append(f"\n→ 다음: Part {na['run_part']} ({na['reason']})")
        return "\n".join(lines)
