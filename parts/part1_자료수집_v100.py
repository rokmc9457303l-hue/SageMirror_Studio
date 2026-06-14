# -*- coding: utf-8 -*-
"""
parts/part1_자료수집_v100.py — Part 1: 자료수집 (Librarian) v100

v100 변경사항:
- LibrarianAgent 완전 통합
- Critic-Scout 자동 루프 UI 노출
- 댓글 200개 수집 + 주제 10개 보장
- p1_packet 표준화
"""

import streamlit as st
import requests
from datetime import datetime

from core.config import PART_NAMES
from core.state import get_state, set_state, save_workspace
from core.brain import call_model
from core.obsidian import search_rag, save_dual
from parts._template import (
    load_prompt, get_part_context,
    render_validation_tab, render_packet_tab, render_status_tab,
)
from panel.components import result_display, copy_button
from core.version_control import render_action_buttons


PART_NUM = 1


def _get_librarian():
    """LibrarianAgent 싱글톤"""
    if "librarian_agent" not in st.session_state:
        from core.agents.librarian import LibrarianAgent
        st.session_state["librarian_agent"] = LibrarianAgent()
    return st.session_state["librarian_agent"]


def _get_critic():
    from core.agents.critic import CriticAgent
    return CriticAgent()


# ─────────────────────────────────────────────────
# 메인 렌더링
# ─────────────────────────────────────────────────
def render_part1():
    """Part 1 메인 화면 (v100)"""
    # 채널 프로필 표시
    try:
        from core.profile_loader import load_current_profile
        profile = load_current_profile()
        ch_name = profile.get("channel_name", "미지정")
        tone = profile.get("tone", "")
        st.markdown(
            f"## 📍 Part 1 — {PART_NAMES[1]} (Librarian)"
            f"&nbsp;&nbsp;<small style='color:gray'>채널: {ch_name}</small>",
            unsafe_allow_html=True,
        )
        if tone:
            st.caption(f"톤: {tone} | 벤치마킹 · 댓글분석 · 주제발굴 · 자료조사")
    except Exception:
        st.markdown(f"## 📍 Part 1 — {PART_NAMES[1]} (Librarian)")
        st.caption("벤치마킹 · 댓글분석 · 주제발굴 · 자료조사")

    # RAG 자료 상태 박스
    from core.rag_status_box import render_rag_status_box
    render_rag_status_box(1)
    st.markdown("")

    tabs = st.tabs([
        "1️⃣ 벤치마킹",
        "2️⃣ 주제 추천",
        "3️⃣ 자료조사",
        "🔍 Critic 검증",
        "📤 전달 패킷",
        "📊 상태"
    ])

    with tabs[0]: render_benchmark_tab()
    with tabs[1]: render_topic_tab()
    with tabs[2]: render_research_tab()
    with tabs[3]: render_critic_tab()
    with tabs[4]: render_packet_tab(PART_NUM)
    with tabs[5]: render_status_tab(PART_NUM)

    render_action_buttons(PART_NUM)


# ─────────────────────────────────────────────────
# 탭 1: 벤치마킹
# ─────────────────────────────────────────────────
def render_benchmark_tab():
    st.markdown("### 1️⃣ 채널 벤치마킹")

    pending = get_state("p1_channel_url_pending", "")
    if pending:
        set_state("p1_channel_url", pending)
        set_state("p1_channel_url_pending", "")
        set_state("p1_url_counter", get_state("p1_url_counter", 0) + 1)
        st.success(f"✅ 채널 적용됨: {pending}")

    current_url = get_state("p1_channel_url", "")
    if current_url:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.info(f"🎯 선정 채널: `{current_url}`")
        with c2:
            st.link_button("🔗 열기", current_url, use_container_width=True)

    url_key = f"p1_channel_url_input_{get_state('p1_url_counter', 0)}"
    channel_url = st.text_input(
        "🔗 채널 URL 직접 입력 또는 수정",
        value=current_url,
        placeholder="예: https://youtube.com/@channelname 또는 UCxxxxxx",
        key=url_key,
    )
    if channel_url and channel_url != current_url:
        set_state("p1_channel_url", channel_url)

    yt_key = get_state("api_youtube", "")
    if not yt_key:
        st.warning("⚙️ 우측 패널 설정에서 YouTube API 키를 입력하세요")

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("🚀 벤치마킹 시작", key="p1v100_bench_start", type="primary", use_container_width=True):
            if not channel_url:
                st.error("채널 URL을 입력하세요")
                return
            if not yt_key:
                st.error("YouTube API 키가 필요합니다")
                return
            with st.spinner("🔍 채널 분석 중..."):
                result = run_benchmark(channel_url, yt_key)
            if result:
                set_state("p1_bench_result", result)
                st.success("✅ 벤치마킹 완료")
    with bc2:
        if st.button("💬 댓글 200개 수집", key="p1v100_collect_comments", use_container_width=True):
            if not channel_url or not yt_key:
                st.error("채널 URL과 YouTube API 키가 필요합니다")
                return
            with st.spinner("💬 댓글 수집 중 (최대 200개)..."):
                ch_id = channel_url.split("/")[-1].replace("@", "")
                agent = _get_librarian()
                comments = agent.collect_comments(ch_id, yt_key, max_count=200)
            if comments:
                set_state("p1_comments_raw", comments)
                st.success(f"✅ 댓글 {len(comments)}개 수집 완료")
            else:
                st.warning("댓글 수집 실패 또는 결과 없음")

    # 댓글 수집 현황
    comments = get_state("p1_comments_raw", [])
    if comments:
        agent = _get_librarian()
        classified = agent._classify_comments(comments)
        top = [c for c in classified[:5] if c["star"] in ("⭐⭐⭐", "⭐⭐")]
        with st.expander(f"💬 수집된 댓글 {len(comments)}개 — 상위 {len(top)}개 미리보기"):
            for c in top:
                st.markdown(f"{c['star']} 👍{c['likes']} — {c['text'][:130]}")

    bench = get_state("p1_bench_result")
    if bench:
        result_display(bench, title="벤치마킹 결과", height=300)
        if st.button("📤 주제추천으로 전달", key="p1v100_send_topics", use_container_width=True):
            set_state("p1_bench_packet", {
                "bench_raw": bench,
                "channel_url": get_state("p1_channel_url"),
            })
            st.toast("✅ 주제추천 탭으로 전달됐습니다!")


def run_benchmark(channel_url: str, api_key: str) -> str:
    """YouTube API + 채널 프로필 기반 Gemma 분석"""
    try:
        channel_id = channel_url.split("/")[-1].replace("@", "")
        search_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&q={channel_id}&type=channel&maxResults=1&key={api_key}"
        )
        ch_resp = requests.get(search_url, timeout=15).json()
        items = ch_resp.get("items", [])
        if not items:
            return "[채널을 찾을 수 없습니다]"

        real_channel_id = items[0]["id"]["channelId"]
        channel_name = items[0]["snippet"]["title"]

        vid_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&channelId={real_channel_id}&order=date"
            f"&maxResults=10&type=video&key={api_key}"
        )
        vid_resp = requests.get(vid_url, timeout=15).json()
        videos = vid_resp.get("items", [])

        video_data = [
            {
                "title": v.get("snippet", {}).get("title", ""),
                "desc":  v.get("snippet", {}).get("description", "")[:200],
                "date":  v.get("snippet", {}).get("publishedAt", "")[:10],
            }
            for v in videos
        ]

        analysis_input = (
            f"[채널명] {channel_name}\n[최근 영상 10개]\n"
            + "\n".join(f"- {v['date']} | {v['title']} | {v['desc']}" for v in video_data)
        )

        # 채널 프로필 기반 프롬프트
        agent = _get_librarian()
        prompt = agent.build_base_prompt(
            analysis_input
            + "\n\n위 채널을 벤치마킹하라. "
            "채널 구조/후킹/썸네일/스크립트/태그/댓글 6개 항목 분석. "
            "타겟 시청자 감정 고통 기반 주제 후보 5개 추출."
        )
        result = call_model(prompt=prompt, model=get_state("current_model"))
        return f"## 채널: {channel_name}\n\n{analysis_input}\n\n---\n\n{result}"

    except Exception as e:
        return f"[벤치마킹 오류] {e}"


# ─────────────────────────────────────────────────
# 탭 2: 주제 추천
# ─────────────────────────────────────────────────
def render_topic_tab():
    st.markdown("### 2️⃣ 주제 추천 (10개 보장)")

    packet = get_state("p1_bench_packet")
    if packet:
        st.info(f"📥 벤치마킹 채널: {packet.get('channel_url','')}")

    bench = get_state("p1_bench_result")
    if not bench:
        st.info("먼저 벤치마킹 탭에서 채널 분석을 완료하세요")
        return

    comments = get_state("p1_comments_raw", [])
    if comments:
        st.success(f"💬 댓글 {len(comments)}개 반영됨")

    additional = st.text_area(
        "추가 지시 (선택)",
        placeholder="특정 감정 키워드 강조 또는 제외할 주제 등...",
        height=80,
        key="p1v100_topic_addl",
    )

    if st.button("🎯 주제 생성 (최소 10개)", key="p1v100_topic_gen", type="primary", use_container_width=True):
        with st.spinner("💡 LibrarianAgent 주제 발굴 중..."):
            result_text = generate_topics(
                get_state("p1_bench_packet", {}).get("bench_raw", bench),
                additional,
            )
        if result_text:
            set_state("p1_topics_result", result_text)
            st.success("✅ 주제 생성 완료")

    topics_text = get_state("p1_topics_result")
    if topics_text:
        result_display(topics_text, title="추천 주제", height=400)

        st.markdown("---")
        topic_choice = st.text_input(
            "🎯 작업할 주제 선택 (번호 또는 직접 입력)",
            key="p1v100_topic_choice",
            placeholder="예: 3번 또는 직접 주제 입력",
        )
        if topic_choice and st.button("주제 확정", key="p1v100_topic_confirm"):
            set_state("p1_topic_selection", topic_choice)
            st.success(f"✅ 주제 확정: {topic_choice}")


def generate_topics(benchmark: str, additional: str = "") -> str:
    agent = _get_librarian()
    comments = get_state("p1_comments_raw", [])
    topics = agent.generate_topics(bench_raw=benchmark, comments=comments, extra=additional)

    if not topics:
        # 폴백
        rag = search_rag("주제 감정 고독 후회 상실", max_files=3, max_chars=300)
        prompt = load_prompt(PART_NUM)
        q = (
            f"[벤치마킹]\n{benchmark[:1500]}\n[RAG]\n{rag[:600]}\n[지시]\n{additional}\n\n"
            "타겟 시청자 감정 고통 기반 주제 최소 10개. 형식: NN. 주제 | 추천사유 | 감정키워드"
        )
        return call_model(prompt=q, system=prompt, model=get_state("current_model"))

    return "\n".join(f"{i+1}. {t}" for i, t in enumerate(topics))


# ─────────────────────────────────────────────────
# 탭 3: 자료조사
# ─────────────────────────────────────────────────
def render_research_tab():
    st.markdown("### 3️⃣ 자료조사")

    topic = get_state("p1_topic_selection")
    if not topic:
        st.info("먼저 주제 추천 탭에서 주제를 확정하세요")
        return

    st.success(f"📌 선택된 주제: **{topic}**")
    use_tavily = st.checkbox("Tavily 웹 검색 보조", value=True, key="p1v100_use_tavily")

    if st.button("📚 자료조사 시작", key="p1v100_research_start", type="primary", use_container_width=True):
        with st.spinner("📖 LibrarianAgent 자료조사 중..."):
            research = run_research(topic, use_tavily)
        if research:
            set_state("p1_research_result", research)
            set_state("p1_research_sources", _extract_sources(research))
            st.success("✅ 자료조사 완료")

    research = get_state("p1_research_result")
    if research:
        result_display(research, title="자료조사 결과", height=400)


def run_research(topic: str, use_tavily: bool = True) -> str:
    agent = _get_librarian()
    sources = agent.search_sources(topic, use_tavily=use_tavily)

    if sources:
        rag_content = "\n\n".join(s.get("content", "")[:500] for s in sources)
        status_message = f"[RAG 소스 {len(sources)}개 확보]"
    else:
        rag_content = "(자료 없음)"
        status_message = "[RAG 자료 없음 — 옵시디언 보강 필요]"

    prompt = load_prompt(PART_NUM)
    q = (
        f"[주제] {topic}\n[상태] {status_message}\n"
        f"[RAG 자료]\n{rag_content[:2000]}\n\n"
        "다음을 정리하라:\n"
        "1. 핵심 자료 5~10개 [SOURCE: ...] 표기 필수\n"
        "2. 감정 키워드 추출\n"
        "3. 철학·심리 연결점\n"
        "4. 성경 연결점 (가능 시)\n"
        "부족한 부분은 [NEED_RESEARCH: 키워드] 표기."
    )
    result = call_model(prompt=q, system=prompt, model=get_state("current_model"))
    return f"{status_message}\n\n---\n\n{result}"


def _extract_sources(research_text: str) -> list:
    """자료조사 결과에서 출처 목록 추출"""
    import re
    sources = re.findall(r"\[SOURCE:\s*([^\]]+)\]", research_text)
    return [{"content": s.strip(), "type": "rag"} for s in sources[:10]]


# ─────────────────────────────────────────────────
# 탭 4: Critic 검증 (v100 신규)
# ─────────────────────────────────────────────────
def render_critic_tab():
    st.markdown("### 🔍 Critic 4층 검증")
    st.caption("사실검증 → 출처검증 → 완성도검증 → 일관성검증 → Scout 자동 보강")

    topic = get_state("p1_topic_selection", "")
    research = get_state("p1_research_result", "")
    sources = get_state("p1_research_sources", [])

    if not topic:
        st.info("주제와 자료조사를 먼저 완료하세요 (탭 2, 3)")
        return

    # 현재 컨텍스트 요약 표시
    with st.expander("📋 검증 대상 컨텍스트", expanded=False):
        st.markdown(f"**주제:** {topic}")
        st.markdown(f"**자료 소스:** {len(sources)}개")
        if research:
            st.text(research[:300] + "...")

    mc1, mc2 = st.columns(2)
    with mc1:
        if st.button("🔍 Critic 검증 실행", key="p1v100_critic_run",
                     type="primary", use_container_width=True):
            context = {
                "part": PART_NUM,
                "topic": topic,
                "research_sources": sources,
                "audience_pain": get_state("p1_comments_raw", []),
                "benchmark_summary": get_state("p1_bench_result", "")[:500],
                "title_candidates": [],
                "core_emotion": "",
                "full_text": research,
            }
            with st.spinner("🔍 4층 검증 중..."):
                critic = _get_critic()
                result = critic.execute(context)
            set_state("p1_critic_result", result)
            st.rerun()

    with mc2:
        if st.button("🤖 Critic-Scout 자동 루프", key="p1v100_loop_run",
                     use_container_width=True):
            context = {
                "part": PART_NUM,
                "topic": topic,
                "research_sources": sources,
                "full_text": research,
                "core_emotion": "",
                "title_candidates": [],
            }
            with st.spinner("🔄 자동 루프 실행 중 (최대 3회)..."):
                from core.agents.loop import critic_scout_loop
                loop_result = critic_scout_loop(
                    context=context,
                    part_runner=lambda ctx: {"research_sources": ctx.get("research_sources", [])},
                    part_num=PART_NUM,
                )
            set_state("p1_loop_result", loop_result)
            set_state("p1_critic_result", {
                "passed": loop_result["passed"],
                "score": 0,
                "summary": loop_result["summary"],
                "data_request": loop_result.get("data_request"),
            })
            st.rerun()

    # 검증 결과 표시
    crit = get_state("p1_critic_result")
    if crit:
        score = crit.get("score", 0)
        passed = crit.get("passed", False)

        # 점수 게이지
        col_s, col_v = st.columns([3, 1])
        with col_s:
            st.progress(min(score / 100, 1.0), text=f"검증 점수: {score:.1f}/100")
        with col_v:
            st.markdown(f"### {'✅ 통과' if passed else '❌ 실패'}")

        # 상세 보고서
        summary = crit.get("summary", "")
        if summary:
            st.markdown("---")
            st.markdown(summary)

        # Scout 자동 보강 가능 여부
        dr = crit.get("data_request", {})
        if dr:
            auto_count = dr.get("auto_fixable_count", 0)
            manual_count = dr.get("manual_needed_count", 0)
            if auto_count > 0:
                st.info(f"🤖 Scout 자동 보강 가능: {auto_count}개 이슈 | 수동 필요: {manual_count}개")
            elif manual_count > 0:
                st.warning(f"✋ 수동 보완 필요: {manual_count}개 이슈")

        # 검증 통과 시 패킷 생성 버튼
        if passed:
            st.success("✅ 검증 통과 — p1_packet 생성 가능")
            if st.button("📦 p1_packet 생성", key="p1v100_make_packet",
                         type="primary", use_container_width=True):
                _create_p1_packet(topic, sources, research)

    # 수동 보강 입력
    with st.expander("✏️ 수동 자료 보강 입력"):
        manual_text = st.text_area(
            "부족한 자료를 직접 입력하세요",
            height=150,
            key="p1v100_manual_supplement",
            placeholder="성경 구절, 철학 인용구, 통계 출처 등...",
        )
        if manual_text and st.button("보강 저장", key="p1v100_manual_save"):
            try:
                save_dual(manual_text, f"수동보강_{topic[:20]}", PART_NUM, "수동입력")
                new_sources = sources + [{"content": manual_text[:500], "type": "manual"}]
                set_state("p1_research_sources", new_sources)
                st.success("✅ 저장 완료. 다시 Critic 검증을 실행하세요.")
            except Exception as e:
                st.error(f"저장 오류: {e}")


def _create_p1_packet(topic: str, sources: list, research: str):
    """Critic 통과 후 표준 p1_packet 생성"""
    agent = _get_librarian()
    comments = get_state("p1_comments_raw", [])
    bench_raw = get_state("p1_bench_result", "")

    packet = agent.execute({
        "topic": topic,
        "bench_raw": bench_raw,
        "comments": comments,
        "research_sources": sources,
    })

    # Packet 상태를 APPROVED로 승격
    packet["status"] = "APPROVED"
    packet["critic_passed"] = True
    packet["created_at"] = datetime.now().isoformat()

    set_state("p1_packet", packet)

    # 옵시디언 저장
    try:
        import json
        save_dual(json.dumps(packet, ensure_ascii=False, indent=2),
                  f"p1_packet_{topic[:20]}", PART_NUM, "packet")
        st.success("✅ p1_packet 생성 + 옵시디언 저장 완료")
    except Exception:
        st.success("✅ p1_packet 생성 완료")

    save_workspace()
    st.rerun()
