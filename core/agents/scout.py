# -*- coding: utf-8 -*-
"""
core/agents/scout.py — Scout (자료 보강 에이전트)

역할:
- Critic이 요청한 DataRequest 자동 처리
- Tavily 웹 검색 + Gemini Deep Research
- 보강된 자료를 옵시디언에 저장
- 보강 결과 요약 반환
"""

from .base import BaseAgent


class ScoutAgent(BaseAgent):
    name = "Scout"
    role = "자료 보강 정찰대"

    def specific_instructions(self) -> str:
        return (
            "당신은 자료 부족 문제를 자동으로 해결하는 정찰대입니다.\n"
            "DataRequest의 검색 쿼리를 실행하고 신뢰할 수 있는 출처에서 자료를 수집합니다.\n"
            "성경 인용구는 원전을 확인하고, 통계는 출처 URL을 포함합니다.\n"
            "수집한 자료를 옵시디언 Raw_Data에 저장합니다."
        )

    def execute(self, context: dict) -> dict:
        """DataRequest 또는 직접 query/missing_data를 받아 자동 자료 보강 실행"""
        from core.critic.data_request import DataRequest

        # 직접 query 인터페이스 (hub_menu 자동 보강에서 호출)
        if "query" in context and "data_request" not in context:
            topic = context.get("query", "")
            missing = context.get("missing_data", [])
            queries = [topic] if topic else []
            queries += [f"{topic} {cat}" for cat in missing[:3] if cat]
            if not queries:
                return {"error": "검색 쿼리 없음", "results": [], "saved_count": 0}
            results = []
            for q in queries[:5]:
                result = self._search_and_save(q, topic)
                if result:
                    results.append(result)
            self.log(f"직접 보강 완료: {len(results)}건 수집")
            return {
                "success": len(results) > 0,
                "topic": topic,
                "saved_count": len(results),
                "results": results,
                "agent": self.name,
                "message": f"{len(results)}건 수집·저장 완료" if results else "수집 결과 없음",
            }

        data_request = context.get("data_request")
        if not data_request:
            return {"error": "DataRequest 없음", "results": [], "saved_count": 0}

        queries = []
        if isinstance(data_request, dict):
            issues = data_request.get("issues", [])
            queries = [i.get("search_query") for i in issues if i.get("search_query")]
            topic = data_request.get("topic", "")
        elif isinstance(data_request, DataRequest):
            queries = data_request.get_scout_queries()
            topic = data_request.topic
        else:
            return {"error": "DataRequest 형식 오류", "results": [], "saved_count": 0}

        if not queries:
            self.log("보강 쿼리 없음")
            return {"results": [], "count": 0}

        results = []
        for q in queries[:5]:
            result = self._search_and_save(q, topic)
            if result:
                results.append(result)

        self.log(f"보강 완료: {len(results)}/{len(queries)} 쿼리 성공")
        return {
            "success": len(results) > 0,
            "topic": topic,
            "queries_attempted": len(queries[:5]),
            "success_count": len(results),
            "saved_count": len(results),
            "results": results,
            "agent": self.name,
            "message": f"{len(results)}건 수집·저장 완료" if results else "수집 결과 없음",
        }

    def _search_and_save(self, query: str, topic: str) -> dict:
        """Tavily 검색 → 결과 저장"""
        try:
            from core.web_search import tavily_search
            search_result = tavily_search(query)
        except Exception:
            search_result = self._fallback_gemini_search(query)

        if not search_result:
            return None

        title = f"scout_{topic[:20]}_{query[:30]}"
        try:
            from core.obsidian import save_dual
            path = save_dual(title, str(search_result), "조사자료", source_type="scout_search")
        except Exception as e:
            self.log(f"저장 오류: {e}")
            path = None

        return {
            "query": query,
            "content": str(search_result)[:500],
            "saved_to": str(path) if path else "",
        }

    def _fallback_gemini_search(self, query: str) -> str:
        """Tavily 실패 시 Gemini로 대체 검색"""
        prompt = (
            f"다음 질문에 대해 신뢰할 수 있는 출처를 찾아 답변하세요:\n{query}\n\n"
            "출처(URL 또는 저자/책명)를 반드시 포함하세요."
        )
        return self.call_ai(prompt, force_gemini=True)

    def reinforce(self, data_request, part_context: dict) -> dict:
        """Critic-Scout 루프에서 호출: 보강 후 갱신된 context 반환"""
        scout_result = self.execute({"data_request": data_request, **part_context})

        if scout_result.get("success_count", 0) > 0:
            # 보강된 자료를 context에 추가
            new_sources = part_context.get("research_sources", []) + scout_result.get("results", [])
            part_context["research_sources"] = new_sources
            part_context["scout_reinforced"] = True

        return part_context
