# -*- coding: utf-8 -*-
"""
core/agents/librarian.py — Librarian (자료수집 에이전트)

역할:
- Part 1 전체 자료수집 파이프라인 담당
- 댓글 200개 수집 + 감정 분류
- 주제 10개 이상 보장
- p1_packet 생성
"""

from datetime import datetime
from .base import BaseAgent


class LibrarianAgent(BaseAgent):
    name = "Librarian"
    role = "자료수집 사서"

    def specific_instructions(self) -> str:
        """AGENT_PROTOCOL.md 우선 로드, 없으면 기본값"""
        try:
            from core.md_loader import load_part_md
            md = load_part_md(1, "AGENT_PROTOCOL.md")
            if md:
                return md
        except Exception:
            pass
        p = self.profile
        topics = ", ".join(p.get("typical_topics", []))
        philosophy = ", ".join(p.get("philosophy_anchor", []))
        return (
            f"당신은 유튜브 채널 콘텐츠 제작을 위한 자료 수집 전문가입니다.\n"
            f"주요 주제: {topics}\n"
            f"철학 기반: {philosophy}\n"
            "댓글에서 시청자의 진짜 고통을 읽어내고,\n"
            "성경·철학·심리학 자료와 연결하여 깊이 있는 주제를 발굴합니다.\n"
            "출처 없는 주장, 할루시네이션, 일반화는 [NEED_VERIFY] 태그로 표기합니다.\n"
            "주제는 반드시 10개 이상 생성합니다."
        )

    def execute(self, context: dict) -> dict:
        """p1_packet 생성 (전체 파이프라인 실행)"""
        topic = context.get("topic", "")
        bench_raw = context.get("bench_raw", "")
        comments = context.get("comments", [])
        research_sources = context.get("research_sources", [])

        # 주제 생성 (10개 보장)
        topics = self.generate_topics(bench_raw, comments)

        # 자료조사
        if not research_sources:
            research_sources = self.search_sources(topic or topics[0] if topics else "")

        # 감정 키워드 추출
        core_emotion = self._extract_core_emotion(topic, research_sources)

        # p1_packet 구성
        packet = self.make_packet(1, {
            "topic": topic or (topics[0] if topics else ""),
            "core_emotion": core_emotion,
            "audience_pain": self._extract_audience_pain(comments),
            "benchmark_summary": bench_raw[:500] if bench_raw else "",
            "comment_insights": self._classify_comments(comments)[:20],
            "research_sources": research_sources[:10],
            "title_candidates": self._generate_titles(topic, core_emotion),
            "thumbnail_direction": self._generate_thumbnail(topic, core_emotion),
            "knowledge_score": self._calc_knowledge_score(research_sources),
            "topics_list": topics,
            "next_part": 2,
        })

        self.log(f"p1_packet 생성 완료: 주제='{packet['topic']}', 소스={len(research_sources)}개")
        return packet

    # ── 댓글 수집/분류 ──────────────────────────────────────────────

    def collect_comments(self, channel_id: str, api_key: str, max_count: int = 200) -> list:
        """YouTube API로 댓글 최대 200개 수집"""
        if not api_key or not channel_id:
            return []
        try:
            import requests
            comments = []
            video_ids = self._get_recent_video_ids(channel_id, api_key, max_videos=10)
            per_video = max(1, max_count // max(len(video_ids), 1))

            for vid in video_ids:
                if len(comments) >= max_count:
                    break
                url = (
                    "https://www.googleapis.com/youtube/v3/commentThreads"
                    f"?part=snippet&videoId={vid}&maxResults={per_video}"
                    f"&order=relevance&key={api_key}"
                )
                resp = requests.get(url, timeout=15).json()
                for item in resp.get("items", []):
                    top = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "text": top.get("textDisplay", ""),
                        "likes": top.get("likeCount", 0),
                        "video_id": vid,
                    })
            return comments[:max_count]
        except Exception as e:
            self.log(f"댓글 수집 오류: {e}")
            return []

    def _get_recent_video_ids(self, channel_id: str, api_key: str, max_videos: int = 10) -> list:
        try:
            import requests
            url = (
                "https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet&channelId={channel_id}&type=video"
                f"&order=date&maxResults={max_videos}&key={api_key}"
            )
            resp = requests.get(url, timeout=15).json()
            return [item["id"]["videoId"] for item in resp.get("items", [])]
        except Exception:
            return []

    def _classify_comments(self, comments: list) -> list:
        """댓글 감정 분류 (⭐ 등급 부여)"""
        classified = []
        priority_keywords = ["힘들었", "상처", "이혼", "혼자", "후회", "눈물", "공허", "떠났", "죽고"]
        emotion_keywords = ["외롭", "무서", "슬프", "두렵", "공감", "내 얘기", "울었"]

        for c in comments:
            text = c.get("text", "")
            likes = c.get("likes", 0)
            score = 0

            for kw in priority_keywords:
                if kw in text:
                    score += 3
            for kw in emotion_keywords:
                if kw in text:
                    score += 2
            if likes > 100:
                score += 2
            elif likes > 10:
                score += 1

            if len(text) < 10 or any(spam in text for spam in ["http", "구독", "홍보"]):
                continue

            star = "⭐⭐⭐" if score >= 5 else ("⭐⭐" if score >= 3 else "⭐")
            classified.append({
                "text": text[:200],
                "likes": likes,
                "star": star,
                "score": score,
            })

        classified.sort(key=lambda x: -x["score"])
        return classified

    # ── 주제 생성 (10개 보장) ────────────────────────────────────────

    def generate_topics(self, bench_raw: str = "", comments: list = None, extra: str = "") -> list:
        """주제 10개 이상 보장 (STEP_주제발굴.md 기반)"""
        comments = comments or []
        rag = self._load_rag()
        comment_insights = self._classify_comments(comments)[:10]
        comment_text = "\n".join(
            f"[{c['star']}] {c['text'][:100]}" for c in comment_insights
        )

        # STEP_주제발굴.md 로드 (없으면 기본 지시)
        step_guide = self._load_step_md("주제발굴")
        target = self.profile.get("target_audience", "타겟 시청자")

        task_text = (
            f"{step_guide}\n\n" if step_guide else ""
            f"[벤치마킹 자료]\n{bench_raw[:1500]}\n\n"
            f"[댓글 인사이트 상위 10개]\n{comment_text}\n\n"
            f"[옵시디언 RAG]\n{rag[:600]}\n\n"
            f"[추가 지시]\n{extra}\n\n"
            f"위 자료를 바탕으로 {target} 감정 고통 기반 주제를 최소 10개 이상 생성하라.\n"
            "형식: NN. [제목] | [핵심주제] | [추천사유] | [감정키워드] | [예상반응]\n"
            "반드시 10개 이상 출력할 것."
        )
        prompt = self.build_base_prompt(task_text)

        result = self.call_ai(prompt)
        topics = self._parse_topics(result)

        # 10개 미만이면 재시도
        if len(topics) < 10:
            self.log(f"주제 {len(topics)}개 → 재시도 (10개 보장)")
            result2 = self.call_ai(
                prompt + "\n\n앞서 생성한 주제에 추가로 더 생성하라. 총 10개 이상 되어야 한다."
            )
            topics += self._parse_topics(result2)

        return topics[:20]

    def _load_step_md(self, step_name: str) -> str:
        """STEP_{step_name}.md 로드 (없으면 빈 문자열)"""
        try:
            from core.md_loader import load_part_md
            return load_part_md(1, f"STEP_{step_name}.md")
        except Exception:
            return ""

    def _parse_topics(self, text: str) -> list:
        """텍스트에서 주제 목록 파싱"""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        topics = []
        for line in lines:
            # "1." 또는 "1)" 또는 "-" 로 시작하는 라인
            if line and (line[0].isdigit() or line.startswith("-")):
                clean = line.lstrip("0123456789.-) ").strip()
                if len(clean) > 5:
                    topics.append(clean)
        return topics

    # ── 자료조사 ─────────────────────────────────────────────────────

    def search_sources(self, topic: str, use_tavily: bool = True) -> list:
        """RAG 검색 + 필요 시 Tavily 보완"""
        sources = []

        # 옵시디언 RAG
        try:
            from core.obsidian import search_rag
            rag_text = search_rag(topic, max_files=8, max_chars=500)
            if rag_text:
                sources.append({"type": "rag", "content": rag_text, "query": topic})
        except Exception as e:
            self.log(f"RAG 검색 오류: {e}")

        # Tavily 보완 (RAG 부족 시)
        if use_tavily and len(sources) < 3:
            try:
                from core.web_search import tavily_search
                result = tavily_search(topic)
                if result:
                    sources.append({"type": "tavily", "content": str(result)[:1000], "query": topic})
            except Exception as e:
                self.log(f"Tavily 검색 오류: {e}")

        return sources

    # ── 내부 헬퍼 ────────────────────────────────────────────────────

    def _load_rag(self) -> str:
        try:
            from core.obsidian import search_rag
            return search_rag("감정 고독 후회 상실 철학 성경", max_files=3, max_chars=300)
        except Exception:
            return ""

    def _extract_core_emotion(self, topic: str, sources: list) -> str:
        text = topic + " ".join(str(s) for s in sources[:3])
        emotions = ["고독", "후회", "상실", "공허", "외로움", "두려움", "분노", "체념", "슬픔"]
        found = [e for e in emotions if e in text]
        return ", ".join(found[:3]) if found else "고독"

    def _extract_audience_pain(self, comments: list) -> str:
        if not comments:
            return "시청자 고통 데이터 없음"
        classified = self._classify_comments(comments)
        top = [c["text"][:100] for c in classified[:3] if c["star"] in ("⭐⭐⭐", "⭐⭐")]
        return "; ".join(top) if top else "댓글 분석 필요"

    def _generate_titles(self, topic: str, emotion: str) -> list:
        prompt = self.build_base_prompt(
            f"주제: {topic}\n핵심 감정: {emotion}\n\n"
            "타겟 시청자를 위한 유튜브 제목 후보 5개를 생성하라.\n"
            "각 제목은 클릭을 유도하되 금지 표현을 사용하지 않는다."
        )
        result = self.call_ai(prompt)
        lines = [l.strip().lstrip("0123456789.-) ").strip()
                 for l in result.splitlines() if l.strip() and len(l.strip()) > 5]
        return lines[:5] if lines else [f"{topic}에 대한 이야기"]

    def _generate_thumbnail(self, topic: str, emotion: str) -> str:
        p = self.profile
        symbols = " / ".join(p.get("core_symbols", []))
        style   = p.get("visual_style", "")
        hint = f"{style} | 상징: {symbols}" if (style or symbols) else ""
        return f"[{emotion}] {hint} | 메시지: {topic[:20]}"

    def _calc_knowledge_score(self, sources: list) -> dict:
        """Curator와 동일한 18점 점수화 (경량 버전)"""
        count = len(sources)
        if count == 0:
            return {"total": 0, "verdict": "부족"}
        base = min(3, count)
        return {
            "relevance": base,
            "source_quality": min(3, count),
            "depth": 2 if count >= 3 else 1,
            "balance": min(3, count),
            "usability": 2,
            "recency": 1,
            "total": min(18, base * 4 + 6),
            "verdict": "충분" if count >= 5 else ("보완 필요" if count >= 2 else "부족"),
        }


# ═══════════════════════════════════════════════════════════
# HitChannelFinder — 떡상 채널 발굴 알고리즘
# ═══════════════════════════════════════════════════════════

class HitChannelFinder(BaseAgent):
    """떡상 채널 자동 발굴 (저구독·고조회 필터링)"""

    name = "HitChannelFinder"
    role = "떡상 채널 발굴 알고리즘"

    # 떡상 기준
    VIRAL_RATIO_MIN   = 5.0    # 조회수 / 구독자 최소값
    COMMENT_DENSITY_MIN = 0.005  # 댓글 / 조회수 최소값
    RETENTION_KEYWORDS = ["끝까지", "여러 번", "또 봤", "정주행", "다시", "반복", "여러번"]

    def specific_instructions(self) -> str:
        return (
            "당신은 유튜브 떡상 채널 발굴 전문가입니다.\n"
            "구독자 1만 이하 + 조회수 10만 이상 채널을 찾아 분석합니다.\n"
            "바이럴 지수(조회수/구독자 ≥ 5)를 기준으로 필터링합니다.\n"
            "정주행 신호 댓글('끝까지', '또 봤' 등)이 많은 채널을 우선 추천합니다."
        )

    def execute(self, context: dict) -> dict:
        keyword = context.get("keyword", context.get("topic", ""))
        return {"channels": self.find_explosive_channels(keyword)}

    def find_explosive_channels(self, keyword: str, profile: dict = None) -> list:
        """
        떡상 채널 발굴 전체 파이프라인.

        Returns: 점수 내림차순 정렬된 채널 목록 (최대 5개)
        """
        if not keyword:
            return []

        profile = profile or self.profile
        self.log(f"떡상 채널 탐색 시작: '{keyword}'")

        # 1. YouTube/Tavily 검색
        candidates = self._search_channels(keyword, profile)
        if not candidates:
            self.log("후보 채널 없음")
            return []

        # 2. 떡상 지수 계산 + 필터링
        explosive = []
        for ch in candidates:
            subs  = max(ch.get("subscribers", 1), 1)
            views = ch.get("views", 0)
            ratio = views / subs
            if ratio >= self.VIRAL_RATIO_MIN:
                ch["viral_ratio"] = round(ratio, 2)
                explosive.append(ch)

        if not explosive:
            self.log(f"떡상 지수 {self.VIRAL_RATIO_MIN} 이상 채널 없음 → 상위 3개 반환")
            explosive = sorted(candidates,
                               key=lambda c: c.get("views", 0) / max(c.get("subscribers", 1), 1),
                               reverse=True)[:3]
            for ch in explosive:
                ch["viral_ratio"] = round(ch.get("views", 0) / max(ch.get("subscribers", 1), 1), 2)

        # 3. 댓글 밀도 계산
        for ch in explosive:
            views = max(ch.get("views", 1), 1)
            ch["comment_density"] = round(ch.get("comments", 0) / views, 5)

        # 4. 정주행 신호 댓글 분석
        for ch in explosive:
            sample_comments = ch.get("sample_comments", [])
            ch["retention_signals"] = self._count_retention_signals(sample_comments)

        # 5. 종합 점수 정렬
        scored = sorted(
            explosive,
            key=lambda c: (
                c.get("viral_ratio", 0),
                c.get("comment_density", 0),
                c.get("retention_signals", 0),
            ),
            reverse=True,
        )

        self.log(f"떡상 채널 {len(scored)}개 발굴 완료")
        return scored[:5]

    def _search_channels(self, keyword: str, profile: dict) -> list:
        """YouTube API + Tavily로 후보 채널 수집"""
        candidates = []

        # Tavily 검색
        try:
            from core.web_search import tavily_search
            tavily_result = tavily_search(f"{keyword} 유튜브 채널 구독자 1만 조회수 10만")
            if tavily_result:
                parsed = self._parse_tavily_channels(str(tavily_result), keyword)
                candidates.extend(parsed)
        except Exception as e:
            self.log(f"Tavily 채널 검색 오류: {e}")

        # Gemini로 채널 추천 요청 (Tavily 부족 시)
        if len(candidates) < 3:
            try:
                target = profile.get("target_audience", "") if profile else ""
                prompt = (
                    f"유튜브에서 '{keyword}' 주제의 떡상 채널을 5개 추천하라.\n"
                    f"조건: 구독자 1만 이하, 조회수 10만 이상\n"
                    f"타겟 시청자: {target}\n"
                    "출력: 채널명 | 구독자수 | 대표 영상 조회수 | 특징\n"
                    "[ESTIMATE] 태그 붙여서 추정값임을 표시."
                )
                result = self.call_ai(prompt, force_gemini=True)
                parsed = self._parse_ai_channels(result)
                candidates.extend(parsed)
            except Exception as e:
                self.log(f"Gemini 채널 추천 오류: {e}")

        return candidates

    def _parse_tavily_channels(self, text: str, keyword: str) -> list:
        """Tavily 결과에서 채널 정보 추출"""
        import re
        channels = []
        # 간이 파싱: "채널명 - 구독자 X만" 패턴
        patterns = re.findall(
            r"([가-힣\w]+(?:TV|유튜브|채널)?)\s*[-|]\s*구독자?\s*(\d+(?:\.\d+)?)\s*([만천])?",
            text
        )
        for name, num_str, unit in patterns[:5]:
            try:
                num = float(num_str)
                if unit == "만":
                    num *= 10000
                elif unit == "천":
                    num *= 1000
                channels.append({
                    "name": name.strip(),
                    "subscribers": int(num),
                    "views": int(num * 8),  # [ESTIMATE]
                    "comments": int(num * 0.04),
                    "sample_comments": [],
                    "source": "tavily",
                })
            except Exception:
                continue
        return channels

    def _parse_ai_channels(self, text: str) -> list:
        """AI 출력에서 채널 정보 추출"""
        channels = []
        for line in text.splitlines():
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                try:
                    name = parts[0].lstrip("0123456789.-) ").strip()
                    subs_text = parts[1].replace(",", "").replace("만", "0000").replace("천", "000")
                    import re
                    subs = int(re.sub(r"[^\d]", "", subs_text) or "5000")
                    views = subs * 8  # [ESTIMATE]
                    channels.append({
                        "name": name,
                        "subscribers": subs,
                        "views": views,
                        "comments": int(views * 0.005),
                        "sample_comments": [],
                        "source": "ai_estimate",
                        "estimated": True,
                    })
                except Exception:
                    continue
        return channels[:5]

    def _count_retention_signals(self, comments: list) -> int:
        """정주행 신호 댓글 키워드 카운트"""
        count = 0
        for c in comments:
            text = str(c.get("text", c) if isinstance(c, dict) else c)
            count += sum(1 for kw in self.RETENTION_KEYWORDS if kw in text)
        return count

    def format_result(self, channels: list) -> str:
        """UI 표시용 텍스트 생성"""
        if not channels:
            return "떡상 채널을 찾지 못했습니다."
        lines = ["## 🚀 떡상 채널 발굴 결과"]
        for i, ch in enumerate(channels, 1):
            est = " [추정]" if ch.get("estimated") else ""
            lines.append(
                f"\n### {i}. {ch.get('name', '?')} {est}\n"
                f"- 구독자: {ch.get('subscribers', '?'):,} | 조회수: {ch.get('views', '?'):,}\n"
                f"- 바이럴 지수: {ch.get('viral_ratio', 0):.1f} | "
                f"댓글 밀도: {ch.get('comment_density', 0):.4f} | "
                f"정주행 신호: {ch.get('retention_signals', 0)}개"
            )
        return "\n".join(lines)
