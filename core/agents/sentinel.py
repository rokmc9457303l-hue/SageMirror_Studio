# -*- coding: utf-8 -*-
"""
core/agents/sentinel.py — Sentinel 에이전트 (Tasks 48~53)

역할: 벤치마킹 채널 24시간 추적 + 6대 해부 분석 + 트렌드 감지
"""

from .base import BaseAgent


class SentinelAgent(BaseAgent):
    name = "Sentinel"
    role = "벤치마킹 채널 자동 추적 + 매일 정찰 보고"

    def __init__(self):
        super().__init__()
        self._watchlist = None

    def specific_instructions(self) -> str:
        p = self.profile
        return (
            "당신은 벤치마킹 채널 추적 전문가입니다.\n"
            "실제 데이터만 사용하고 복제는 절대 금지합니다.\n"
            "구조와 패턴만 추출하여 우리 채널 관점에서 응용 방안을 제안합니다.\n"
            f"우리 채널 프로필: {p.get('channel_name', '')} / "
            f"타겟: {p.get('target_audience', '')} / "
            f"톤: {p.get('tone', '')}"
        )

    def execute(self, context: dict) -> dict:
        """단일 영상 6대 해부 분석"""
        video = context.get("video", {})
        if not video:
            return {"error": "video 데이터 없음"}
        return self.full_dissection(video)

    # ── 워치리스트 ─────────────────────────────────────────────────────

    @property
    def watchlist(self) -> list:
        if self._watchlist is None:
            self._watchlist = self._load_watchlist()
        return self._watchlist

    def _load_watchlist(self) -> list:
        """profiles/{channel}/sentinel_watchlist.yaml 로드"""
        import yaml
        try:
            from core.profile_loader import get_channel_path
            ch = self.profile.get("channel_name", "")
            p  = get_channel_path(ch) / "sentinel_watchlist.yaml"
            if p.exists():
                return yaml.safe_load(p.read_text(encoding="utf-8")).get("tracked_channels", [])
        except Exception as e:
            self.log(f"워치리스트 로드 오류: {e}")
        return []

    def save_watchlist(self, channels: list):
        """워치리스트 저장"""
        import yaml
        try:
            from core.profile_loader import get_channel_path
            ch = self.profile.get("channel_name", "")
            p  = get_channel_path(ch) / "sentinel_watchlist.yaml"
            p.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "tracked_channels": channels,
                "watch_settings": {
                    "check_frequency": "daily_3am",
                    "comment_collection_limit": 200,
                    "performance_tracking_hours": [1, 6, 24, 72, 168],
                    "auto_save_obsidian": True,
                    "notify_user": True,
                },
            }
            p.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
            self._watchlist = channels
        except Exception as e:
            self.log(f"워치리스트 저장 오류: {e}")

    # ── 일일 정찰 ──────────────────────────────────────────────────────

    def daily_patrol(self) -> dict:
        """매일 자동 실행 — 추적 채널 신규 영상 감지 + 6대 해부"""
        from core.agents.curator import CuratorAgent
        from core.agents.researcher import ResearcherAgent

        curator    = CuratorAgent()
        researcher = ResearcherAgent()
        new_videos = []
        our_channel = self.profile.get("channel_name", "")

        for ch in self.watchlist:
            try:
                videos = self._check_new_videos(ch)
                for video in videos:
                    analysis = self.full_dissection(video)
                    paths = curator.auto_save(
                        content=str(analysis),
                        source_type="sentinel_dissection",
                        channel=ch.get("name", ""),
                    )
                    connections = researcher.find_connections(str(analysis))
                    new_videos.append({
                        "video": video,
                        "analysis": analysis,
                        "paths": paths,
                        "connections": connections,
                    })
            except Exception as e:
                self.log(f"채널 {ch.get('name', '')} 정찰 오류: {e}")

        report = self._generate_daily_report(new_videos)
        return {"new_videos": len(new_videos), "report": report}

    def _check_new_videos(self, channel_info: dict) -> list:
        """YouTube API로 신규 영상 확인 (24시간 이내)"""
        try:
            from core.youtube_api import get_recent_videos
            return get_recent_videos(
                channel_id=channel_info.get("channel_id", ""),
                hours=24,
            )
        except Exception as e:
            self.log(f"YouTube API 오류: {e}")
            return []

    # ── 6대 해부 분석 ──────────────────────────────────────────────────

    def full_dissection(self, video: dict) -> dict:
        """6대 해부: 제목/썸네일/도입/댓글/성과/응용"""
        return {
            "video_id": video.get("id", ""),
            "title": video.get("title", ""),
            "title_analysis": self._analyze_title(video),
            "thumbnail_analysis": self._analyze_thumbnail(video),
            "opening_5sec": self._analyze_opening(video),
            "comment_emotion": self._analyze_comments(video),
            "performance_tracking": self._track_performance(video),
            "application_points": self.find_application_points(
                {
                    "title_analysis": self._analyze_title(video),
                    "comment_emotion": self._analyze_comments(video),
                }
            ),
        }

    def _analyze_title(self, video: dict) -> dict:
        prompt = self.build_base_prompt(
            f"다음 영상 제목을 분석하세요.\n"
            f"제목: {video.get('title', '')}\n"
            "분석: 공식(어떤 패턴?), 클릭 유도 요소, 감정 키워드\n"
            "JSON: {formula, click_triggers, emotion_keywords}"
        )
        raw = self.call_ai(prompt)
        return _parse_json_safe(raw, {"formula": "", "click_triggers": [], "emotion_keywords": []})

    def _analyze_thumbnail(self, video: dict) -> dict:
        return {
            "url": video.get("thumbnail", ""),
            "text_elements": video.get("thumbnail_text", ""),
            "visual_analysis": "썸네일 분석 (이미지 접근 필요)",
        }

    def _analyze_opening(self, video: dict) -> dict:
        transcript = video.get("transcript", "")[:500]
        if not transcript:
            return {"hook": "", "technique": ""}
        prompt = self.build_base_prompt(
            f"다음 영상 도입부(첫 500자)를 분석하세요.\n{transcript}\n"
            "분석: 어떻게 시청자를 멈추게 하는가? 어떤 기법?\n"
            "JSON: {hook_sentence, technique, emotion_trigger}"
        )
        raw = self.call_ai(prompt)
        return _parse_json_safe(raw, {"hook_sentence": "", "technique": "", "emotion_trigger": ""})

    def _analyze_comments(self, video: dict) -> dict:
        comments = video.get("top_comments", [])
        if not comments:
            return {"top_emotions": [], "pain_patterns": [], "count": 0}
        sample = "\n".join(str(c) for c in comments[:20])
        prompt = self.build_base_prompt(
            f"다음 댓글 20개를 분석하세요.\n{sample}\n"
            "분석: 시청자가 무엇을 느꼈는가? 공통 감정/상황?\n"
            "JSON: {top_emotions(list), pain_patterns(list), avg_sentiment}"
        )
        raw = self.call_ai(prompt)
        return _parse_json_safe(raw, {"top_emotions": [], "pain_patterns": [], "avg_sentiment": 0})

    def _track_performance(self, video: dict) -> dict:
        return {
            "views_24h": video.get("views_24h", 0),
            "views_total": video.get("views", 0),
            "likes": video.get("likes", 0),
            "comments": video.get("comment_count", 0),
            "is_explosive": video.get("views_24h", 0) > 10000,
        }

    # ── 응용 주제 발굴 ─────────────────────────────────────────────────

    def find_application_points(self, dissection: dict) -> list:
        """벤치마킹 분석에서 우리 채널 응용 주제 발굴"""
        p = self.profile
        top_emotions = dissection.get("comment_emotion", {}).get("top_emotions", [])
        original = dissection.get("title_analysis", {}).get("formula", "")

        topics = []
        for emotion in top_emotions[:5]:
            prompt = self.build_base_prompt(
                f"벤치마킹 채널이 '{emotion}' 감정으로 떡상했습니다.\n"
                f"원본 제목 패턴: {original}\n"
                f"우리 채널 톤: {p.get('tone', '')}\n"
                "우리 채널 방식으로 같은 감정을 다루는 주제를 제안하세요.\n"
                "JSON: {our_angle, differentiation, estimated_score(0-10)}"
            )
            raw = self.call_ai(prompt)
            parsed = _parse_json_safe(raw, {
                "our_angle": emotion + " 관련 주제",
                "differentiation": "",
                "estimated_score": 5,
            })
            parsed["source_emotion"] = emotion
            topics.append(parsed)

        return sorted(topics, key=lambda x: -x.get("estimated_score", 0))

    # ── 트렌드 동시 폭발 감지 ──────────────────────────────────────────

    def detect_trend_explosion(self, days: int = 7) -> list:
        """여러 채널에서 동시에 떡상한 주제 클러스터 감지"""
        try:
            explosions = self._get_recent_explosive_videos(days)
            clusters   = self._cluster_by_topic(explosions)
            trending   = [c for c in clusters if c.get("channel_count", 0) >= 2]
            return [
                {
                    "trend": c.get("common_theme", ""),
                    "channels": c.get("channels", []),
                    "total_views": c.get("sum_views", 0),
                    "urgency": "high" if c.get("days_old", 99) < 3 else "medium",
                    "recommendation": "지금 이 주제로 영상 제작 시 알고리즘 추천 가능성 높음",
                }
                for c in trending
            ]
        except Exception as e:
            self.log(f"트렌드 감지 오류: {e}")
            return []

    def _get_recent_explosive_videos(self, days: int) -> list:
        results = []
        for ch in self.watchlist:
            try:
                from core.youtube_api import get_recent_videos
                videos = get_recent_videos(ch.get("channel_id", ""), hours=days * 24)
                explosive = [v for v in videos if v.get("views_24h", 0) > 10000]
                results.extend(explosive)
            except Exception:
                pass
        return results

    def _cluster_by_topic(self, videos: list) -> list:
        """간단 키워드 기반 클러스터링"""
        from collections import defaultdict
        clusters: dict = defaultdict(lambda: {"videos": [], "channels": set(), "sum_views": 0})

        emotion_keywords = ["고독", "외로움", "후회", "상실", "배신", "가족", "관계", "은퇴"]
        for v in videos:
            title = v.get("title", "")
            for kw in emotion_keywords:
                if kw in title:
                    c = clusters[kw]
                    c["videos"].append(v)
                    c["channels"].add(v.get("channel_name", ""))
                    c["sum_views"] += v.get("views_24h", 0)

        return [
            {
                "common_theme": theme,
                "channel_count": len(data["channels"]),
                "channels": list(data["channels"]),
                "sum_views": data["sum_views"],
                "days_old": 1,
            }
            for theme, data in clusters.items()
            if len(data["channels"]) >= 2
        ]

    # ── 보고서 생성 ────────────────────────────────────────────────────

    def _generate_daily_report(self, new_videos: list) -> str:
        """일일 정찰 보고서 텍스트 생성"""
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"# 🛰️ Sentinel 일일 정찰 보고 ({date_str})",
            f"신규 영상 분석: {len(new_videos)}건",
            "",
        ]
        for i, item in enumerate(new_videos[:10], 1):
            video = item.get("video", {})
            analysis = item.get("analysis", {})
            perf = analysis.get("performance_tracking", {})
            apps = analysis.get("application_points", [])
            lines.append(
                f"## {i}. {video.get('title', '제목 없음')}\n"
                f"- 24시간 조회: {perf.get('views_24h', 0):,}\n"
                f"- 응용 주제 발굴: {len(apps)}개\n"
                f"- 채널: {video.get('channel_name', '')}"
            )

        report_text = "\n".join(lines)

        # 옵시디언 04_Sentinel 폴더에 저장
        try:
            from core.config import OBSIDIAN_PATH
            sentinel_dir = OBSIDIAN_PATH / "04_Sentinel" / "daily_reports"
            sentinel_dir.mkdir(parents=True, exist_ok=True)
            (sentinel_dir / f"{date_str}.md").write_text(report_text, encoding="utf-8")
        except Exception as e:
            self.log(f"보고서 저장 오류: {e}")

        return report_text


def _parse_json_safe(raw: str, default: dict) -> dict:
    import json, re
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return default
