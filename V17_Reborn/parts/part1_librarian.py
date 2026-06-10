# -*- coding: utf-8 -*-
"""
Part 1 - Librarian
자료수집 / 벤치마킹 / 성공 영상 스크립트 분석 UI
"""

import streamlit as st

from core.config import YOUTUBE_API_KEY


def render():
    st.header("Part 1 - 자료수집 / 벤치마킹")
    st.caption("유튜브 채널 분석, 성공 영상 스크립트 분석, 자료조사를 담당하는 시작 파트입니다.")

    st.subheader("1. 유튜브 API 연결 상태")

    if YOUTUBE_API_KEY:
        st.success("유튜브 API 키가 연결되어 있습니다.")
        st.write(f"키 앞 6글자: `{YOUTUBE_API_KEY[:6]}`")
        st.write(f"키 뒤 4글자: `{YOUTUBE_API_KEY[-4:]}`")
        st.write(f"키 길이: `{len(YOUTUBE_API_KEY)}`")
    else:
        st.error("유튜브 API 키가 없습니다. .env 파일을 확인하세요.")

    st.divider()

    st.subheader("2. 벤치마킹 입력")
    channel_url = st.text_input(
        "분석할 유튜브 채널 URL",
        placeholder="예: https://www.youtube.com/@channelname"
    )

    video_url = st.text_input(
        "성공 영상 URL",
        placeholder="예: https://www.youtube.com/watch?v=..."
    )

    topic_keyword = st.text_input(
        "분석 키워드",
        placeholder="예: 도파민 중독, 자존감 붕괴, 관계 피로"
    )

    st.divider()

    st.subheader("3. Part 2 전달 패킷 미리보기")

    packet = {
        "part_id": "part1_librarian",
        "channel_url": channel_url,
        "video_url": video_url,
        "topic_keyword": topic_keyword,
        "youtube_api_connected": bool(YOUTUBE_API_KEY),
    }

    st.json(packet)

    if st.button("Part 1 결과 생성"):
        st.success("Part 1 기본 결과가 생성되었습니다.")
        st.session_state["p1_packet"] = packet