# -*- coding: utf-8 -*-
"""
현자의 거울 스튜디오 v18.0.4
Sage Mirror Studio — 메인 진입점 (우측 브레인 패널 통합)
"""

import streamlit as st
from pathlib import Path

# ── Streamlit 설정 (반드시 최상단) ───────────────
st.set_page_config(
    page_title="현자의 거울 v18",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── core import ──────────────────────────────────
from core.config import (
    APP_NAME, APP_VERSION, PART_NAMES,
    OBSIDIAN_PATH, MODELS, DEFAULT_MODEL, API_KEYS,
)
from core.state import init_state, get_state, set_state, save_workspace, load_workspace

# ── 8파트 import ─────────────────────────────────
from parts.part1_자료수집 import render_part1
from parts.part2_총괄기획 import render_part2
from parts.part3_대본작성 import render_part3
from parts.part4_이미지생성 import render_part4
from parts.part5_영상생성 import render_part5
from parts.part6_나레이션 import render_part6
from parts.part7_숏폼 import render_part7
from parts.part8_최종조립 import render_part8


# ─────────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f"### ⬡ {APP_NAME}")
        st.caption(f"`{APP_VERSION}`")
        st.markdown("---")
        
        # 에피소드
        st.markdown("#### 🎬 에피소드")
        episode = st.text_input(
            "현재 작업 에피소드",
            value=get_state("current_episode", "EP001"),
            key="sb_episode",
        )
        if episode != get_state("current_episode"):
            set_state("current_episode", episode)
            save_workspace()
        
        st.markdown("---")
        
        # 파트 선택
        st.markdown("#### 📂 작업 파트")
        part_options = [f"{i}. {PART_NAMES[i]}" for i in range(1, 9)]

        # 채널 버튼 클릭 등으로 파트 이동 요청 시 → radio 위젯 렌더 전에 처리
        nav_target = get_state("p1_nav_pending", 0)
        if nav_target:
            st.session_state.pop("sb_part_radio", None)  # radio 위젯 state 초기화
            set_state("current_part", nav_target)
            set_state("p1_nav_pending", 0)

        current = get_state("current_part", 1)

        selected = st.radio(
            "이동할 파트",
            part_options,
            index=current - 1,
            key="sb_part_radio",
            label_visibility="collapsed",
        )
        new_part = int(selected.split(".")[0])
        if new_part != current:
            set_state("current_part", new_part)
        
        st.markdown("---")
        
        # 모델 선택
        st.markdown("#### 🤖 모델")
        model_options = list(MODELS.keys())
        cur_model = get_state("current_model", DEFAULT_MODEL)
        
        sel_model = st.selectbox(
            "기본 모델",
            model_options,
            index=model_options.index(cur_model) if cur_model in model_options else 0,
            format_func=lambda x: MODELS[x]["label"],
            key="sb_model",
            label_visibility="collapsed",
        )
        if sel_model != cur_model:
            set_state("current_model", sel_model)
        st.caption(f"{MODELS[sel_model]['desc']}")
        
        st.markdown("---")
        
        # API 키
        with st.expander("⚙️ API 키 설정"):
            for key_name in API_KEYS.keys():
                state_key = f"api_{key_name}"
                current_val = get_state(state_key, "")
                new_val = st.text_input(
                    key_name.capitalize(),
                    value=current_val,
                    type="password",
                    key=f"sb_api_{key_name}",
                )
                if new_val != current_val:
                    set_state(state_key, new_val)
        
        st.markdown("---")
        
        # 시스템 상태
        st.markdown("#### 🔗 시스템 연동")
        
        obs_ok = OBSIDIAN_PATH.exists()
        st.write(f"{'🟢' if obs_ok else '🔴'} 옵시디언")
        if obs_ok:
            st.caption(f"`{OBSIDIAN_PATH.name}`")
        
        st.markdown("---")
        
        # 진행 상황
        st.markdown("#### 📊 8파트 진행")
        for i in range(1, 9):
            packet = get_state(f"p{i}_packet")
            status = get_state(f"p{i}_status", "대기")
            icon = "✅" if packet else ("🔄" if status != "대기" else "⬜")
            st.caption(f"{icon} Part {i}: {PART_NAMES[i]}")
        
        st.markdown("---")
        
        # 저장
        if st.button("💾 작업 상태 저장", key="sb_save", use_container_width=True):
            if save_workspace():
                st.toast("💾 저장 완료")
            else:
                st.toast("⚠️ 저장 실패")


# ─────────────────────────────────────────────────
# 메인 디스패치
# ─────────────────────────────────────────────────
def render_main():
    current_part = get_state("current_part", 1)
    
    # 헤더
    episode = get_state("current_episode", "EP001")
    st.markdown(f"### `[{episode}]`  ⬡ 현자의 거울 스튜디오")
    st.markdown("---")
    
    # 메인 영역(좌) + 우측 패널 구조
    main_col, panel_col = st.columns([7, 3], gap="medium")
    
    with main_col:
        # 파트별 라우팅
        if current_part == 1:
            render_part1()
        elif current_part == 2:
            render_part2()
        elif current_part == 3:
            render_part3()
        elif current_part == 4:
            render_part4()
        elif current_part == 5:
            render_part5()
        elif current_part == 6:
            render_part6()
        elif current_part == 7:
            render_part7()
        elif current_part == 8:
            render_part8()
    
    with panel_col:
        from panel.right_panel import render_right_panel
        render_right_panel()


# ─────────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────────
def main():
    # secrets.toml API 키 자동 로드
    for key, field in [("api_youtube", "youtube"), ("api_gemini", "gemini"),
                       ("api_github", "github"), ("api_tavily", "tavily")]:
        if key not in st.session_state:
            st.session_state[key] = st.secrets.get("api_keys", {}).get(field, "")

    # session_state 초기화
    init_state()
    
    # 작업 상태 복원
    if not get_state("_workspace_loaded"):
        load_workspace()
        set_state("_workspace_loaded", True)
    
    # 사이드바 + 메인
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
