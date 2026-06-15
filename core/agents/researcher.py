# -*- coding: utf-8 -*-
"""
core/agents/researcher.py — Researcher 에이전트 (Task M)

역할: 옵시디언 두뇌 활용 — 심층 검색, 연결, 주제 추천
"""

from .base import BaseAgent


class ResearcherAgent(BaseAgent):
    name = "Researcher"
    role = "옵시디언 심층 검색 + 자료 연결 + 주제 추천"

    def specific_instructions(self) -> str:
        return (
            "당신은 옵시디언 두뇌의 사서입니다.\n"
            "채널에 축적된 모든 지식을 검색하고 연결합니다.\n"
            "외부 자료와 내부 지식을 교차 분석하여 최상위 자료를 반환합니다."
        )

    def execute(self, context: dict) -> dict:
        """기본 실행 — deep_search 래퍼"""
        query = context.get("query", "")
        channel = context.get("channel") or self.profile.get("channel_name", "")
        ctx = context.get("context")
        results = self.deep_search(query, channel, ctx)
        return {"results": results, "agent": self.name}

    # ── 핵심 검색 ──────────────────────────────────────────────────────

    def deep_search(self, query: str, channel: str, context: dict = None) -> list:
        """
        4-레이어 심층 검색:
        1) 키워드 검색
        2) 카테고리 기반 확장
        3) 그래프 탐색 (옵시디언 링크)
        4) 컨텍스트 필터 + 우선순위
        """
        if not query:
            return []

        keyword_results   = self._keyword_search(query, channel)
        category_results  = self._category_search(query)
        graph_results     = self._graph_traversal(query, depth=2)

        all_results = self._merge_and_rank(
            keyword_results,
            category_results,
            graph_results,
        )

        if context:
            all_results = self._filter_by_context(all_results, context)

        return all_results[:10]

    def _keyword_search(self, query: str, channel: str) -> list:
        try:
            from core.obsidian import search_rag
            return search_rag(query, top_k=15) or []
        except Exception as e:
            self.log(f"키워드 검색 오류: {e}")
            return []

    def _category_search(self, query: str) -> list:
        try:
            from core.obsidian import search_by_category
            from core.config import UNIVERSAL_CATEGORIES
            related = [c for c in UNIVERSAL_CATEGORIES if any(w in c for w in query.split())]
            results = []
            for cat in related[:3]:
                results.extend(search_by_category(cat, top_k=5) or [])
            return results
        except Exception as e:
            self.log(f"카테고리 검색 오류: {e}")
            return []

    def _graph_traversal(self, query: str, depth: int = 2) -> list:
        try:
            from core.obsidian import traverse_links
            return traverse_links(query, depth=depth) or []
        except Exception as e:
            self.log(f"그래프 탐색 오류: {e}")
            return []

    def _merge_and_rank(self, *result_lists) -> list:
        seen = set()
        merged = []
        for lst in result_lists:
            for item in lst:
                key = str(item)[:100]
                if key not in seen:
                    seen.add(key)
                    merged.append(item)
        return merged

    def _filter_by_context(self, results: list, context: dict) -> list:
        part_num = context.get("part_num", 0)
        if not part_num:
            return results
        relevant_keywords = {
            1: ["주제", "트렌드", "댓글", "벤치마킹"],
            2: ["감정", "기획", "구조", "훅"],
            3: ["대본", "씬", "나레이션", "장면"],
        }
        keys = relevant_keywords.get(part_num, [])
        if not keys:
            return results
        scored = [
            (sum(1 for k in keys if k in str(r)), r)
            for r in results
        ]
        return [r for _, r in sorted(scored, key=lambda x: -x[0])]

    # ── 주제 추천 ──────────────────────────────────────────────────────

    def suggest_next_topics(self, channel: str) -> list:
        """누적 댓글 분석 기반 다음 영상 주제 5개 추천"""
        try:
            from core.obsidian import load_all_comments, load_previous_topics
            all_comments = load_all_comments(channel)
            previous    = load_previous_topics(channel)

            emerging = self._detect_emerging_patterns(all_comments)
            new_topics = [t for t in emerging if t not in previous]

            prompt = self.build_base_prompt(
                f"다음 시청자 감정 패턴에서 채널 주제 5개를 추천하세요.\n"
                f"이미 제작한 주제: {', '.join(str(p) for p in previous[:10])}\n"
                f"새로운 패턴: {', '.join(str(e) for e in new_topics[:20])}\n"
                "떡상 가능성 순으로 정렬. JSON 배열로 반환."
            )
            raw = self.call_ai(prompt)
            import json, re
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                return json.loads(m.group())[:5]
        except Exception as e:
            self.log(f"주제 추천 오류: {e}")
        return []

    def _detect_emerging_patterns(self, comments: list) -> list:
        """댓글에서 부상 중인 감정/주제 패턴 감지"""
        from collections import Counter
        emotion_keywords = [
            "고독", "외로움", "후회", "상실", "배신", "공허",
            "자식", "부모", "친구", "은퇴", "죽음", "이별",
        ]
        counts = Counter()
        for c in comments:
            text = str(c)
            for kw in emotion_keywords:
                if kw in text:
                    counts[kw] += 1
        return [kw for kw, _ in counts.most_common(10)]

    # ── 연결 발견 ──────────────────────────────────────────────────────

    def find_connections(self, content: str) -> dict:
        """주어진 자료와 연결되는 노트 3종 발굴"""
        try:
            from core.obsidian import search_rag
            similar       = search_rag(content[:200], top_k=5) or []
            complementary = search_rag(f"{content[:100]} 반론", top_k=3) or []
            opposing      = search_rag(f"{content[:100]} 반대 관점", top_k=3) or []
        except Exception:
            similar = complementary = opposing = []
        return {"similar": similar, "complementary": complementary, "opposing": opposing}

    def create_connections(self, wiki_path: str):
        """위키 저장 후 옵시디언 링크 자동 생성"""
        try:
            from core.obsidian import create_obsidian_links
            create_obsidian_links(wiki_path)
        except Exception as e:
            self.log(f"링크 생성 오류: {e}")

    # ── 지식 지도 ──────────────────────────────────────────────────────

    def generate_knowledge_map(self, channel: str) -> dict:
        """채널 지식 지도 (노드 + 엣지) 생성"""
        nodes, edges = [], []
        try:
            from core.obsidian import list_all_obsidian_files, load_schema_meta
            for f in list_all_obsidian_files(channel):
                meta = load_schema_meta(f) or {}
                nodes.append({
                    "id": meta.get("source_id", str(f)),
                    "title": meta.get("title", ""),
                    "categories": meta.get("categories", []),
                    "size": meta.get("reference_count", 1),
                })
                for link in meta.get("links", []):
                    edges.append({"from": meta.get("source_id", ""), "to": link})
        except Exception as e:
            self.log(f"지식 지도 생성 오류: {e}")
        return {"nodes": nodes, "edges": edges}
