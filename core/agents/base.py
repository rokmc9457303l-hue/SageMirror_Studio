# -*- coding: utf-8 -*-
"""
core/agents/base.py — 모든 에이전트의 추상 기반

각 Part 에이전트 + 보조 에이전트(Conductor/Critic/Curator/Scout)가 상속.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path


class BaseAgent(ABC):
    """에이전트 공통 기반 클래스"""

    name: str = "BaseAgent"
    role: str = "기반 에이전트"

    def __init__(self):
        self._profile = None
        self._logs: list = []

    # ── 프로필 접근 ──────────────────────────────────────────────────

    @property
    def profile(self) -> dict:
        if self._profile is None:
            try:
                from core.profile_loader import load_current_profile
                self._profile = load_current_profile()
            except Exception:
                self._profile = {}
        return self._profile

    def reset_profile(self):
        """채널 전환 시 캐시 초기화"""
        self._profile = None

    # ── 하위 클래스 필수 구현 ────────────────────────────────────────

    @abstractmethod
    def specific_instructions(self) -> str:
        """에이전트별 특수 지시문 (AI 프롬프트에 삽입)"""

    @abstractmethod
    def execute(self, context: dict) -> dict:
        """
        핵심 실행. context: 이전 Part packet 또는 입력 데이터.
        반환: 결과 dict (packet 또는 분석 결과)
        """

    # ── AI 호출 공통 헬퍼 ────────────────────────────────────────────

    def call_ai(self, prompt: str, force_gemini: bool = False) -> str:
        """
        Gemma(로컬) 또는 Gemini(원격) 호출.
        force_gemini=True → 항상 Gemini 사용.
        """
        try:
            from core.llm import call_llm
            return call_llm(prompt, force_gemini=force_gemini)
        except Exception as e:
            self.log(f"[AI 호출 오류] {e}")
            return ""

    # ── 로깅 ─────────────────────────────────────────────────────────

    def log(self, message: str):
        """에이전트 내부 로그 (03_Logs에도 저장)"""
        entry = {
            "agent": self.name,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "msg": message,
        }
        self._logs.append(entry)
        try:
            from core.obsidian import log_agent_action
            log_agent_action(self.name, message)
        except Exception:
            pass

    def get_logs(self) -> list:
        return list(self._logs)

    # ── 프롬프트 빌더 ────────────────────────────────────────────────

    def build_base_prompt(self, task: str) -> str:
        """채널 프로필 + 특수 지시 + 작업 지시 조합"""
        p = self.profile
        forbidden = ", ".join(p.get("forbidden_expressions", []))
        philosophy = ", ".join(p.get("philosophy_anchor", []))
        return (
            f"[채널: {p.get('channel_name', '미지정')}]\n"
            f"[타겟: {p.get('target_audience', '')}]\n"
            f"[톤: {p.get('tone', '')}]\n"
            f"[금지 표현: {forbidden}]\n"
            f"[철학 기반: {philosophy}]\n\n"
            f"[{self.name} 지시]\n{self.specific_instructions()}\n\n"
            f"[작업]\n{task}"
        )

    # ── Packet 빌더 ──────────────────────────────────────────────────

    def make_packet(self, part: int, content: dict) -> dict:
        """표준 packet 래퍼 생성"""
        return {
            "part": part,
            "agent": self.name,
            "created_at": datetime.now().isoformat(),
            "status": "DRAFT",
            "version": "v001",
            **content,
        }
