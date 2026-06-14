# -*- coding: utf-8 -*-
"""
core/agents/loop.py — Critic-Scout 자동 재검증 루프

흐름:
  Part 실행 → Critic 검증 → PASS: 완료
                           → FAIL: Scout 보강 → Part 재실행 → 재검증
  최대 3회 반복 후 포기 (MANUAL_NEEDED)
"""

from .critic import CriticAgent
from .scout import ScoutAgent


MAX_ITERATIONS = 3


def critic_scout_loop(
    context: dict,
    part_runner,   # callable: context → dict (Part 에이전트 실행 함수)
    part_num: int,
) -> dict:
    """
    Critic-Scout 자동 루프.

    Args:
        context: 현재 Part 실행 컨텍스트
        part_runner: callable(context) → dict (Part 재실행)
        part_num: Part 번호 (1~8)

    Returns:
        {
            "passed": bool,
            "iterations": int,
            "final_context": dict,
            "data_request": dict | None,
            "summary": str,
        }
    """
    critic = CriticAgent()
    scout = ScoutAgent()

    current_context = dict(context)
    last_data_request = None
    summary_lines = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        summary_lines.append(f"\n### 검증 Round {iteration}")

        # Critic 검증
        critic_result = critic.execute(current_context)
        last_data_request = critic_result.get("data_request")

        summary_lines.append(
            f"점수: {critic_result['score']:.1f} | "
            f"{'✅ 통과' if critic_result['passed'] else '❌ 실패'}"
        )
        summary_lines.append(critic_result.get("summary", ""))

        if critic_result["passed"]:
            return {
                "passed": True,
                "iterations": iteration,
                "final_context": current_context,
                "data_request": last_data_request,
                "summary": "\n".join(summary_lines),
            }

        # 자동 수정 가능 이슈만 Scout로 보강
        if iteration < MAX_ITERATIONS:
            auto_fixable_issues = [
                i for i in (last_data_request.get("issues", []) if last_data_request else [])
                if i.get("auto_fixable")
            ]

            if auto_fixable_issues:
                summary_lines.append(f"Scout 보강 시작: {len(auto_fixable_issues)}개 쿼리")
                dr_for_scout = {
                    "topic": current_context.get("topic", ""),
                    "issues": auto_fixable_issues,
                }
                current_context = scout.reinforce(dr_for_scout, current_context)

                # Part 재실행
                try:
                    new_result = part_runner(current_context)
                    current_context.update(new_result)
                    summary_lines.append("Part 재실행 완료")
                except Exception as e:
                    summary_lines.append(f"Part 재실행 오류: {e}")
            else:
                summary_lines.append("자동 수정 가능 이슈 없음 — 수동 보완 필요")
                break

    return {
        "passed": False,
        "iterations": MAX_ITERATIONS,
        "final_context": current_context,
        "data_request": last_data_request,
        "summary": "\n".join(summary_lines) + "\n\n⚠️ 수동 보완 필요",
        "status": "MANUAL_NEEDED",
    }
