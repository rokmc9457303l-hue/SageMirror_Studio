# -*- coding: utf-8 -*-
"""
core/agents/trend_analyzer.py — TrendAnalyzer (트렌드·알고리즘 분석기)

Part 1 Librarian에서 호출. 유튜브 알고리즘·키워드·트렌드를 분석하여
최적 제목 패턴·태그·업로드 전략을 제안한다.
"""

from .base import BaseAgent


class TrendAnalyzer(BaseAgent):
    name = "TrendAnalyzer"
    role = "트렌드·알고리즘·키워드 분석기"

    def specific_instructions(self) -> str:
        p = self.profile
        target = p.get("target_audience", "시청자")
        topics = ", ".join(p.get("typical_topics", []))
        return (
            f"당신은 유튜브 알고리즘·트렌드 전문 분석가입니다.\n"
            f"타겟: {target}\n"
            f"주요 주제: {topics}\n"
            "채널에 최적화된 키워드·제목 패턴·알고리즘 신호를 분석합니다.\n"
            "데이터 기반 추천만 합니다. 근거 없는 예측은 [ESTIMATE] 태그를 붙입니다."
        )

    def execute(self, context: dict) -> dict:
        niche = context.get("niche", context.get("topic", ""))
        return self.analyze(niche)

    def analyze(self, niche: str) -> dict:
        """전체 트렌드 분석 실행"""
        if not niche:
            return {"error": "주제(niche) 없음"}

        self.log(f"트렌드 분석 시작: '{niche}'")

        trending_keywords = self.extract_trending(niche)
        rising_topics     = self.find_rising_topics(niche)
        algorithm_hints   = self.analyze_algorithm_signals()
        title_patterns    = self.extract_winning_patterns(niche)
        thumbnail_patterns = self.extract_thumbnail_patterns()
        tag_recommendations = self.suggest_tags(niche, trending_keywords)
        best_upload_time  = self.suggest_upload_time(niche)

        self.log(f"트렌드 분석 완료: 키워드 {len(trending_keywords)}개")

        return {
            "niche": niche,
            "trending_keywords":    trending_keywords,
            "rising_topics":        rising_topics,
            "algorithm_hints":      algorithm_hints,
            "tag_recommendations":  tag_recommendations,
            "title_patterns":       title_patterns,
            "thumbnail_patterns":   thumbnail_patterns,
            "best_upload_time":     best_upload_time,
            "agent": self.name,
        }

    # ── 트렌드 키워드 추출 ──────────────────────────────────────

    def extract_trending(self, niche: str) -> list:
        """Tavily + Gemma로 현재 트렌딩 키워드 추출"""
        # Tavily 검색 시도
        tavily_data = self._tavily_search(f"{niche} 유튜브 트렌드 2025")
        if not tavily_data:
            tavily_data = ""

        prompt = self.build_base_prompt(
            f"주제: {niche}\n"
            f"검색 자료:\n{tavily_data[:1000]}\n\n"
            "현재 유튜브에서 이 주제와 관련하여 떠오르는 키워드 10개를 추출하라.\n"
            "각 키워드에 [인기도: 상/중/하] [검색량 추정] 붙여서 출력.\n"
            "근거 없는 예측은 [ESTIMATE] 표시."
        )
        result = self.call_ai(prompt)
        return self._parse_list(result)[:10]

    def find_rising_topics(self, niche: str) -> list:
        """상승 중인 세부 주제 발굴"""
        tavily_data = self._tavily_search(f"{niche} 급상승 유튜브 주제")
        prompt = self.build_base_prompt(
            f"주제: {niche}\n검색:\n{tavily_data[:800]}\n\n"
            "이 분야에서 최근 급상승 중인 세부 주제 5개를 추출하라.\n"
            "형식: 주제 | 상승 이유 | 예상 지속 기간"
        )
        result = self.call_ai(prompt)
        return self._parse_list(result)[:5]

    def analyze_algorithm_signals(self) -> dict:
        """유튜브 알고리즘 최적화 신호 분석"""
        p = self.profile
        target = p.get("target_audience", "")
        tone   = p.get("tone", "")

        prompt = self.build_base_prompt(
            f"타겟: {target}, 톤: {tone}\n\n"
            "현재 유튜브 알고리즘에서 중요한 신호를 분석하라:\n"
            "1. 시청 지속률 높이는 요소\n"
            "2. 클릭률(CTR) 높이는 요소\n"
            "3. 댓글/공유를 유발하는 요소\n"
            "4. 알고리즘 추천 확률 높이는 구조\n"
            "각 항목 3개씩 구체적으로."
        )
        result = self.call_ai(prompt)
        return {
            "raw_analysis": result,
            "key_signals": ["시청 지속률 > 40%", "처음 30초 훅", "댓글 유발 질문"],
        }

    def extract_winning_patterns(self, niche: str) -> list:
        """떡상 영상 제목 공통 패턴 추출"""
        tavily_data = self._tavily_search(f"{niche} 유튜브 조회수 높은 영상 제목")
        prompt = self.build_base_prompt(
            f"주제: {niche}\n검색:\n{tavily_data[:800]}\n\n"
            "조회수 높은 영상들의 제목 패턴을 분석하라:\n"
            "- 수사 의문문 패턴\n"
            "- 숫자 활용 패턴\n"
            "- 감정 단어 패턴\n"
            "- 반전/충격 키워드 패턴\n"
            "각 패턴별 예시 2개 포함."
        )
        result = self.call_ai(prompt)
        return self._parse_list(result)[:8]

    def extract_thumbnail_patterns(self) -> list:
        """떡상 영상 썸네일 패턴 추출"""
        p = self.profile
        style  = p.get("visual_style", "")
        symbols = p.get("core_symbols", [])

        prompt = self.build_base_prompt(
            f"채널 시각 스타일: {style}\n핵심 상징: {', '.join(symbols)}\n\n"
            "클릭률 높은 썸네일의 공통 패턴을 분석하라:\n"
            "1. 색상 구성 (3가지 이내)\n"
            "2. 텍스트 배치\n"
            "3. 인물/오브젝트 구성\n"
            "4. 감정 표현 방식\n"
            "이 채널 스타일에 맞는 썸네일 가이드 3개."
        )
        result = self.call_ai(prompt)
        return self._parse_list(result)[:5]

    def suggest_tags(self, niche: str, trending_keywords: list = None) -> list:
        """채널 최적 태그 추천"""
        kw_text = ", ".join((trending_keywords or [])[:5])
        prompt = self.build_base_prompt(
            f"주제: {niche}\n트렌딩 키워드: {kw_text}\n\n"
            "유튜브 알고리즘 최적화 태그 20개를 추천하라.\n"
            "형식: #태그 (용도: 주요/보조/롱테일)\n"
            "주요 태그 5개, 보조 태그 10개, 롱테일 5개."
        )
        result = self.call_ai(prompt)
        return self._parse_list(result)[:20]

    def suggest_upload_time(self, niche: str) -> dict:
        """최적 업로드 시간 추천"""
        p = self.profile
        target = p.get("target_audience", "")
        return {
            "recommended": "목/금 오후 6~8시 [ESTIMATE]",
            "target_based": f"{target} 기준 추천" if target else "일반 추천",
            "rationale": "타겟 시청자 활동 피크 시간대 기반",
        }

    # ── 내부 유틸 ────────────────────────────────────────────

    def _tavily_search(self, query: str) -> str:
        try:
            from core.web_search import tavily_search
            result = tavily_search(query)
            return str(result)[:1500] if result else ""
        except Exception:
            return ""

    def _parse_list(self, text: str) -> list:
        lines = [l.strip().lstrip("0123456789.-) ").strip()
                 for l in text.splitlines() if l.strip() and len(l.strip()) > 3]
        return [l for l in lines if l]
