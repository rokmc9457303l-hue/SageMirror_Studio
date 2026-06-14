# -*- coding: utf-8 -*-
"""
core/agents/curator.py — Curator (지식 큐레이터 에이전트)

역할:
- 옵시디언 RAG에서 관련 자료 검색
- Raw → Wiki 정제 저장
- 지식 충분도 점수 계산
- 자료 부족 시 DataRequest 생성
"""

from .base import BaseAgent


class CuratorAgent(BaseAgent):
    name = "Curator"
    role = "지식 큐레이터"

    def specific_instructions(self) -> str:
        p = self.profile
        philosophy = ", ".join(p.get("philosophy_anchor", []))
        return (
            f"당신은 옵시디언 RAG 지식 큐레이터입니다.\n"
            f"철학 기반: {philosophy}\n"
            "주어진 주제에 관련된 자료를 검색하고 품질을 평가합니다.\n"
            "성경/철학/심리/역사 카테고리별로 균형 있는 자료를 확보합니다.\n"
            "18점 만점으로 자료 충분도를 점수화합니다."
        )

    def execute(self, context: dict) -> dict:
        """주제에 대한 RAG 검색 + 충분도 점수 계산"""
        topic = context.get("topic", "")
        if not topic:
            return {"error": "주제 없음", "score": 0, "sources": []}

        # RAG 검색
        sources = self._search_rag(topic)

        # 충분도 점수 계산
        score_result = self._calculate_sufficiency(sources, topic)

        self.log(f"주제 '{topic}' RAG 검색 완료. 점수: {score_result['total']}/18")

        return {
            "topic": topic,
            "sources": sources,
            "sufficiency_score": score_result,
            "agent": self.name,
        }

    def _search_rag(self, topic: str) -> list:
        """옵시디언 RAG에서 관련 문서 검색"""
        try:
            from core.obsidian import search_rag
            results = search_rag(topic, top_k=10)
            return results if isinstance(results, list) else []
        except Exception as e:
            self.log(f"RAG 검색 오류: {e}")
            return []

    def _calculate_sufficiency(self, sources: list, topic: str) -> dict:
        """18점 만점 자료 충분도 점수화"""
        score = {
            "relevance": 0,      # 관련성 0~3
            "source_quality": 0, # 출처성 0~3
            "depth": 0,          # 깊이 0~3
            "balance": 0,        # 균형 0~3
            "usability": 0,      # 제작 활용성 0~3
            "recency": 0,        # 최신성 0~3
            "total": 0,
            "verdict": "부족",
        }

        if not sources:
            return score

        count = len(sources)

        # 관련성: 키워드 매칭 기준 0~3
        topic_words = set(topic.split())
        relevant = sum(
            1 for s in sources
            if any(w in str(s) for w in topic_words)
        )
        score["relevance"] = min(3, int(relevant / max(count, 1) * 3 + 0.5))

        # 출처성: 출처 URL/저자 포함 여부
        has_source = sum(1 for s in sources if "url" in str(s) or "source" in str(s).lower())
        score["source_quality"] = min(3, int(has_source / max(count, 1) * 3 + 0.5))

        # 깊이: 문서 길이 기준
        avg_len = sum(len(str(s)) for s in sources) / max(count, 1)
        score["depth"] = 3 if avg_len > 500 else (2 if avg_len > 200 else 1 if avg_len > 50 else 0)

        # 균형: 성경/철학/심리/감정 카테고리 존재 여부
        categories = {"성경", "철학", "심리", "감정"}
        found_cats = sum(
            1 for cat in categories
            if any(cat in str(s) for s in sources)
        )
        score["balance"] = min(3, found_cats)

        # 제작 활용성: 유튜브 제작 관련 키워드 존재
        prod_keywords = ["나레이션", "장면", "씬", "감정", "후킹", "대본"]
        usable = sum(1 for s in sources if any(k in str(s) for k in prod_keywords))
        score["usability"] = min(3, int(usable / max(count, 1) * 3 + 0.5))

        # 최신성: 날짜 필드 존재 여부
        has_date = sum(1 for s in sources if "date" in str(s).lower() or "2024" in str(s) or "2025" in str(s))
        score["recency"] = min(3, int(has_date / max(count, 1) * 3 + 0.5))

        total = sum(v for k, v in score.items() if k not in ("total", "verdict"))
        score["total"] = total
        score["verdict"] = (
            "충분" if total >= 15
            else "보완 필요" if total >= 10
            else "부족"
        )

        return score

    def curate_to_wiki(self, raw_text: str, title: str, category: str) -> str:
        """원본 텍스트를 Wiki로 정제 후 저장"""
        prompt = self.build_base_prompt(
            f"다음 자료를 옵시디언 위키 형식으로 정제하세요.\n"
            f"제목: {title}\n카테고리: {category}\n\n"
            f"자료:\n{raw_text[:3000]}\n\n"
            "출력: 핵심 요약(3줄) + 주요 인용구 + 감정 키워드 + 활용 포인트"
        )
        refined = self.call_ai(prompt)
        if not refined:
            return raw_text

        try:
            from core.obsidian import save_dual
            save_dual(title, refined, category, source_type="curated")
        except Exception as e:
            self.log(f"Wiki 저장 오류: {e}")

        return refined
