# -*- coding: utf-8 -*-
"""
parts/part1_자료수집.py — Part 1: 자료수집 (Librarian)

역할:
- 채널 벤치마킹
- 댓글 감정 분석
- 주제 20개 추천
- 자료조사 (옵시디언 RAG 우선 + Tavily 보조)
- Part 2 전달 패킷 생성
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


# ─────────────────────────────────────────────────
# 메인 렌더링
# ─────────────────────────────────────────────────
def render_part1():
    """Part 1 메인 화면"""
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
        "🔍 검증",
        "📤 전달 패킷",
        "📊 상태"
    ])
    
    with tabs[0]: render_benchmark_tab()
    with tabs[1]: render_topic_tab()
    with tabs[2]: render_research_tab()
    with tabs[3]: render_validation_tab(PART_NUM)
    with tabs[4]: render_packet_tab(PART_NUM)
    with tabs[5]: render_status_tab(PART_NUM)
    
    render_action_buttons(PART_NUM)


# ─────────────────────────────────────────────────
# 탭 1: 벤치마킹
# ─────────────────────────────────────────────────
def render_benchmark_tab():
    st.markdown("### 1️⃣ 채널 벤치마킹")

    # 우측 패널 버튼/자동선정으로 URL이 전달된 경우 위젯 초기화 (widget 렌더 전에 처리)
    pending = get_state("p1_channel_url_pending", "")
    if pending:
        st.session_state.pop("p1_channel_url_input", None)  # 이전 widget state 제거
        set_state("p1_channel_url", pending)
        set_state("p1_channel_url_pending", "")

    channel_url = st.text_input(
        "🔗 벤치마킹 채널 URL 또는 채널 ID",
        value=get_state("p1_channel_url", ""),
        placeholder="예: https://youtube.com/@channelname 또는 UCxxxxxx",
        key="p1_channel_url_input",
    )

    if channel_url:
        set_state("p1_channel_url", channel_url)
    
    yt_key = get_state("api_youtube", "")
    if not yt_key:
        st.warning("⚙️ 우측 패널 설정에서 YouTube API 키를 입력하세요")
    
    if st.button("🚀 벤치마킹 시작", key="p1_bench_start", type="primary", use_container_width=True):
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
    
    bench = get_state("p1_bench_result")
    if bench:
        result_display(bench, title="벤치마킹 결과", height=300)
        if st.button("📤 주제추천으로 전달", key="btn_send_to_topics", use_container_width=True):
            set_state("p1_bench_packet", {
                "bench_raw": get_state("p1_bench_result"),
                "channel_url": get_state("p1_channel_url"),
            })
            st.toast("✅ 벤치마킹 결과가 주제추천 탭으로 전달됐습니다!")


def run_benchmark(channel_url: str, api_key: str) -> str:
    """YouTube API + Gemma 분석"""
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
        
        video_data = []
        for v in videos:
            s = v.get("snippet", {})
            video_data.append({
                "title": s.get("title", ""),
                "desc":  s.get("description", "")[:200],
                "date":  s.get("publishedAt", "")[:10],
            })
        
        prompt = load_prompt(PART_NUM)
        analysis_input = f"""
[채널명] {channel_name}
[최근 영상 10개]
""" + "\n".join([
            f"- {v['date']} | {v['title']} | {v['desc']}"
            for v in video_data
        ])
        
        result = call_model(
            prompt=analysis_input + "\n\n위 채널을 분석하고 4070 시청자 감정 고통 기반 주제 후보를 추출하라.",
            system=prompt,
            model=get_state("current_model"),
        )
        
        return f"## 채널: {channel_name}\n\n## 최근 영상\n{analysis_input}\n\n## 분석\n{result}"
    
    except Exception as e:
        return f"[벤치마킹 오류] {e}"


# ─────────────────────────────────────────────────
# 탭 2: 주제 추천
# ─────────────────────────────────────────────────
def render_topic_tab():
    st.markdown("### 2️⃣ 주제 20개 추천")

    packet = get_state("p1_bench_packet")
    if packet:
        st.info(f"📥 벤치마킹 채널 수신: {packet.get('channel_url','')}")

    bench = get_state("p1_bench_result")
    if not bench:
        st.info("먼저 벤치마킹 탭에서 채널 분석을 완료하세요")
        return
    
    additional = st.text_area(
        "추가 지시 (선택)",
        placeholder="특정 감정 키워드 강조 또는 제외할 주제 등...",
        height=80,
        key="p1_topic_addl",
    )
    
    if st.button("🎯 주제 20개 생성", key="p1_topic_gen", type="primary", use_container_width=True):
        with st.spinner("💡 주제 발굴 중..."):
            topics = generate_topics(get_state("p1_bench_packet", {}).get("bench_raw", ""), additional)
        
        if topics:
            set_state("p1_topics_result", topics)
            st.success("✅ 주제 20개 생성 완료")
    
    topics = get_state("p1_topics_result")
    if topics:
        result_display(topics, title="추천 주제 20개", height=400)
        
        st.markdown("---")
        topic_choice = st.text_input(
            "🎯 작업할 주제 선택 (번호 또는 직접 입력)",
            key="p1_topic_choice",
            placeholder="예: 3번 또는 직접 주제 입력",
        )
        if topic_choice and st.button("주제 확정", key="p1_topic_confirm"):
            set_state("p1_topic_selection", topic_choice)
            st.success(f"✅ 주제 확정: {topic_choice}")


def generate_topics(benchmark: str, additional: str = "") -> str:
    rag = search_rag("주제 감정 고독 후회 상실", max_files=3, max_chars=300)
    prompt = load_prompt(PART_NUM)
    
    user_query = f"""
[벤치마킹 결과]
{benchmark[:1500]}

[옵시디언 RAG 참조]
{rag[:600]}

[추가 지시]
{additional}

위 자료를 바탕으로 4070 시청자 감정 고통에 기반한 주제 20개를 추천하라.
출력 형식: NN. 주제 | 추천사유 | 예상효과 | 예상반응 [SOURCE: ...]
"""
    return call_model(prompt=user_query, system=prompt, model=get_state("current_model"))


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
    
    use_tavily = st.checkbox("Tavily 웹 검색 추가 (옵시디언 부족 시 보조)", value=True, key="p1_use_tavily")
    
    if st.button("📚 자료조사 시작", key="p1_research_start", type="primary", use_container_width=True):
        with st.spinner("📖 자료조사 중..."):
            research = run_research(topic, use_tavily)
        
        if research:
            set_state("p1_research_result", research)
            st.success("✅ 자료조사 완료")
    
    research = get_state("p1_research_result")
    if research:
        result_display(research, title="자료조사 결과", height=400)


def run_research(topic: str, use_tavily: bool = True) -> str:
    """
    Part 1 자료조사 — 스마트 RAG 자동 작동
    
    1. 옵시디언 RAG 검색
    2. 충분도 자동 평가
    3. 부족 시 Tavily 자동 보완 (옵시디언 자동 저장)
    4. 풍부해진 RAG로 자료조사 결과 생성
    """
    from core.rag_supplement import smart_rag_search
    
    # 스마트 RAG (자동 보완 포함)
    rag_response = smart_rag_search(
        query=topic,
        part_num=PART_NUM,
        auto_supplement=use_tavily,
        max_files=8,
    )
    
    # 사용자에게 RAG 상태 보고
    eval_info = rag_response["evaluation"]
    status_message = f"[RAG 상태] {eval_info['status']} - {eval_info['message']}"
    
    if rag_response["supplemented"]:
        supp_info = rag_response.get("supplement", {})
        status_message += f"\n[자동 보완] Tavily 검색 → {supp_info.get('saved_count', 0)}건 옵시디언 저장 완료"
    
    rag_content = rag_response["rag_result"]
    
    prompt = load_prompt(PART_NUM)
    
    user_query = f"""
[주제] {topic}

[RAG 자동 보완 상태]
{status_message}

[옵시디언 RAG 자료 — 자동 검색됨]
{rag_content[:2000] if rag_content else '(자료 없음)'}

위 자료를 바탕으로 다음을 정리하라:
1. 핵심 자료 5~10개 [SOURCE: ...] 표기 필수
2. 감정 키워드 추출
3. 철학·심리 연결점
4. 성경 연결점 (가능 시)

옵시디언 RAG가 충분하므로 추론 위주가 아닌 실제 자료 기반으로 작성하라.
부족한 부분은 [NEED_RESEARCH: 키워드]로 표기.
"""
    
    result = call_model(
        prompt=user_query, 
        system=prompt, 
        model=get_state("current_model")
    )
    
    return f"{status_message}\n\n---\n\n{result}"
