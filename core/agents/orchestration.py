# -*- coding: utf-8 -*-
"""
core/agents/orchestration.py — Part 실행 오케스트레이션 (Task N)

실행 흐름:
  1. Researcher 자동 호출 (RAG 컨텍스트 수집)
  2. 메인 에이전트 실행
  3. Critic 검수
  4. Curator 자동 저장
  5. Researcher 연결 생성
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def get_agent_for_part(part_num: int):
    """Part 번호 → 해당 에이전트 인스턴스 반환"""
    from core.agents.librarian import LibrarianAgent
    from core.agents.conductor import ConductorAgent

    mapping = {
        1: LibrarianAgent,
    }
    cls = mapping.get(part_num, ConductorAgent)
    return cls()


def execute_part(part_num: int, user_input: str, channel: str) -> dict:
    """
    Part 실행 with Researcher → Agent → Critic → Curator 자동 연결.

    Args:
        part_num:   실행할 Part 번호 (1~8)
        user_input: 사용자 입력 텍스트 또는 이전 packet
        channel:    채널 키 (profile channel_name)

    Returns:
        에이전트 결과 dict
    """
    from core.agents.researcher import ResearcherAgent
    from core.agents.critic import CriticAgent
    from core.agents.curator import CuratorAgent
    from core.profile_loader import load_current_profile

    researcher = ResearcherAgent()
    critic     = CriticAgent()
    curator    = CuratorAgent()

    # 1. Researcher — RAG 컨텍스트 자동 수집
    rag_context = researcher.deep_search(
        query=user_input,
        channel=channel,
        context={"part_num": part_num},
    )

    # 2. 메인 에이전트 실행
    agent = get_agent_for_part(part_num)
    profile = load_current_profile()
    result = agent.execute({
        "input": user_input,
        "topic": user_input,
        "rag": rag_context,
        "profile": profile,
        "channel": channel,
    })

    # 3. Critic 검수
    critic_result = critic.execute({
        "part": part_num,
        "topic": user_input,
        "research_sources": rag_context,
        **result,
    })

    if not critic_result.get("passed", True):
        # Critic 실패 시 Scout 보완 + 재시도 (최대 1회)
        result = _handle_critic_failure(
            part_num, user_input, channel,
            critic_result, researcher, curator
        )

    # 4. Curator 자동 저장
    content_str = str(result)
    paths = curator.auto_save(
        content=content_str,
        source_type=f"part{part_num}_result",
        channel=channel,
    )

    # 5. Researcher 연결 생성
    if paths.get("wiki"):
        researcher.create_connections(paths["wiki"])

    result["_obsidian_paths"] = paths
    result["_critic_score"]   = critic_result.get("score", 0)
    return result


def _handle_critic_failure(
    part_num, user_input, channel,
    critic_result, researcher, curator
) -> dict:
    """Critic 실패 시 Scout 보강 + 재실행"""
    from core.agents.scout import ScoutAgent

    scout = ScoutAgent()
    missing = [
        issue.get("category", "")
        for issue in critic_result.get("issues", [])
        if issue.get("severity") in ("CRITICAL", "ERROR")
    ]

    scout_result = scout.execute({
        "query": user_input,
        "missing_data": missing,
    })

    agent = get_agent_for_part(part_num)
    from core.profile_loader import load_current_profile
    profile = load_current_profile()

    return agent.execute({
        "input": user_input,
        "topic": user_input,
        "rag": scout_result.get("results", []),
        "profile": profile,
        "channel": channel,
        "_retry": True,
    })
