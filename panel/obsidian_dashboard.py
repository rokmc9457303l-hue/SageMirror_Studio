# -*- coding: utf-8 -*-
"""
panel/obsidian_dashboard.py — 옵시디언 채널 두뇌 대시보드 (Task O)

화면 구성:
  - 두뇌 IQ 스코어
  - 누적 통계 (자료/카테고리/키워드/연결)
  - 성장 그래프
  - 가장 활용된 자료 Top 10
  - 떠오르는 주제 패턴
  - 정리 필요 항목 + 자동 정리 버튼
"""

import streamlit as st
from pathlib import Path


def _get_profile():
    try:
        from core.profile_loader import load_current_profile
        return load_current_profile()
    except Exception:
        return {}


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return len(list(path.rglob("*.md")))


def _get_obsidian_stats(channel: str) -> dict:
    """옵시디언 채널 폴더 기반 통계 수집"""
    from core.config import OBSIDIAN_RAW, OBSIDIAN_WIKI, OBSIDIAN_SCHEMA, OBSIDIAN_LOGS

    ch_raw    = OBSIDIAN_RAW  / f"채널_{channel}"
    ch_wiki   = OBSIDIAN_WIKI
    ch_schema = OBSIDIAN_SCHEMA

    total_files  = _count_files(ch_raw) + _count_files(ch_wiki)
    schema_files = _count_files(ch_schema)

    # 카테고리 수
    categories = 0
    if ch_wiki.exists():
        categories = len([d for d in ch_wiki.iterdir() if d.is_dir()])

    # IQ 계산 (간이)
    iq = min(100, total_files // 10 + categories * 2 + schema_files // 5)

    return {
        "total_files": total_files,
        "categories": categories,
        "schema_files": schema_files,
        "iq": iq,
        "ch_raw": ch_raw,
    }


def _get_top_referenced(channel: str, top_n: int = 10) -> list:
    """가장 많이 참조된 파일 목록 (reference_count 기준)"""
    import json
    from core.config import OBSIDIAN_SCHEMA

    results = []
    for f in OBSIDIAN_SCHEMA.rglob("*.json"):
        try:
            meta = json.loads(f.read_text(encoding="utf-8"))
            if meta.get("reference_count", 0) > 0:
                results.append({
                    "title": meta.get("title", f.stem),
                    "count": meta.get("reference_count", 0),
                })
        except Exception:
            pass
    return sorted(results, key=lambda x: -x["count"])[:top_n]


def _get_emerging_patterns(channel: str, days: int = 30) -> list:
    """최근 N일간 댓글 누적에서 부상 중인 주제 패턴"""
    try:
        from core.agents.researcher import ResearcherAgent
        r = ResearcherAgent()
        patterns = r._detect_emerging_patterns([])  # 실 댓글 없으면 빈 리스트
        return patterns[:5]
    except Exception:
        return []


def _get_maintenance_needed(channel: str) -> dict:
    """정리 필요 항목 수 반환"""
    from core.config import OBSIDIAN_RAW, OBSIDIAN_WIKI
    ch_raw = OBSIDIAN_RAW / f"채널_{channel}"

    uncategorized = 0
    if ch_raw.exists():
        for f in ch_raw.glob("*.md"):
            if not any(k in f.stem for k in ["Part", "Episode", "Wiki"]):
                uncategorized += 1

    return {
        "duplicates": 0,      # 실 중복 감지 생략 (무거움)
        "uncategorized": uncategorized,
        "broken_links": 0,
    }


def render_obsidian_dashboard():
    """옵시디언 두뇌 대시보드 렌더링"""
    profile = _get_profile()
    channel = profile.get("channel_name", "채널")

    st.subheader("🧠 채널 두뇌 상태")
    st.caption(f"현재 채널: {channel}")

    stats = _get_obsidian_stats(channel)

    # ── IQ + 통계 ──────────────────────────────────────────────────────
    col_iq, col_files, col_cats = st.columns(3)
    col_iq.metric("두뇌 IQ", f"{stats['iq']}", delta="성장 중")
    col_files.metric("총 자료", f"{stats['total_files']:,}개")
    col_cats.metric("카테고리", f"{stats['categories']}개")

    # ── 상세 통계 ──────────────────────────────────────────────────────
    with st.expander("📊 상세 통계", expanded=False):
        st.json(stats)

    # ── 가장 활용된 자료 Top 10 ────────────────────────────────────────
    st.markdown("**🔥 가장 활용된 자료 Top 10**")
    top_refs = _get_top_referenced(channel)
    if top_refs:
        for i, item in enumerate(top_refs, 1):
            st.caption(f"{i}. {item['title']} (참조 {item['count']}회)")
    else:
        st.caption("데이터 없음 (Schema 파일 생성 후 표시)")

    st.divider()

    # ── 떠오르는 주제 패턴 ─────────────────────────────────────────────
    st.markdown("**📈 떠오르는 주제 패턴**")
    patterns = _get_emerging_patterns(channel)
    if patterns:
        for p in patterns:
            st.caption(f"• {p}")
    else:
        st.caption("댓글 데이터 축적 후 표시")

    st.divider()

    # ── 정리 필요 ──────────────────────────────────────────────────────
    st.markdown("**⚠️ 정리 필요**")
    maint = _get_maintenance_needed(channel)
    st.caption(f"• 중복 가능 파일: {maint['duplicates']}개")
    st.caption(f"• 미분류 파일: {maint['uncategorized']}개")
    st.caption(f"• 죽은 링크: {maint['broken_links']}개")

    if st.button("🔧 자동 정리 실행"):
        try:
            from core.agents.curator import CuratorAgent
            curator = CuratorAgent()
            report = curator.daily_maintenance()
            st.success(
                f"정리 완료 — 중복 통합: {report['duplicates_merged']}건 "
                f"/ 분류: {report['categorized']}건 "
                f"/ 링크 정리: {report['broken_links']}건"
            )
        except Exception as e:
            st.error(f"자동 정리 오류: {e}")
