# -*- coding: utf-8 -*-
"""
panel/setup_wizard.py — 첫 실행 마법사

앱 최초 실행(setup_completed=False) 시 채널 프로필을 생성하고
이후부터는 드롭다운에 표시된다.
"""

import streamlit as st
import re
from core.state import get_state, set_state, save_workspace


# 드롭다운 선택지
TARGET_OPTIONS = ["전 연령", "청년 (10~30대)", "중장년 (30~50대)", "시니어 (50~70대)", "직접 입력"]
TONE_OPTIONS   = ["따뜻함", "차분함", "활기참", "진지함 / 철학적", "직접 입력"]


def should_show_wizard() -> bool:
    """첫 실행 마법사를 표시해야 하는지 판단"""
    if get_state("setup_completed", False):
        return False
    try:
        from core.profile_loader import list_available_profiles
        profiles = list_available_profiles()
        return len(profiles) == 0
    except Exception:
        return False


def render_setup_wizard():
    """첫 실행 환영 + 채널 생성 마법사"""
    st.markdown("---")
    st.markdown(
        "## ⬡ SAGE Studio에 오신 것을 환영합니다\n"
        "### 첫 번째 채널을 만들어 보세요"
    )
    st.caption("이 마법사는 처음 한 번만 실행됩니다. 언제든 사이드바에서 채널을 추가할 수 있습니다.")
    st.markdown("---")

    with st.form("setup_wizard_form"):
        st.markdown("#### 1️⃣ 채널 기본 정보")

        ch_name = st.text_input(
            "채널명 *",
            placeholder="예: 지혜의 서재 / 마음의 쉼터 / 우리엄마요리",
            help="유튜브 채널 이름 또는 내부 프로젝트명",
        )

        ch_key_raw = st.text_input(
            "채널 키 (영문, 내부 식별용) *",
            placeholder="예: wisdom_shelf / mom_cooking",
            help="파일명으로 사용됩니다. 영문+숫자+_만 가능",
        )

        st.markdown("#### 2️⃣ 타겟 시청자")
        target_sel = st.selectbox("타겟 연령대", TARGET_OPTIONS, index=0)
        target_custom = ""
        if target_sel == "직접 입력":
            target_custom = st.text_input("직접 입력", placeholder="예: 30~40대 직장인")

        st.markdown("#### 3️⃣ 채널 톤")
        tone_sel = st.selectbox("콘텐츠 톤", TONE_OPTIONS, index=0)
        tone_custom = ""
        if tone_sel == "직접 입력":
            tone_custom = st.text_input("직접 입력 (톤)", placeholder="예: 유머러스하고 실용적인")

        st.markdown("#### 4️⃣ 주요 카테고리 (쉼표로 구분)")
        typical_topics_raw = st.text_input(
            "주요 영상 주제 카테고리",
            placeholder="예: 일상 요리, 추억의 음식, 엄마의 레시피",
            help="채널에서 주로 다룰 주제들",
        )

        st.markdown("#### 5️⃣ 표현 규칙 (선택)")
        forbidden_raw = st.text_input(
            "금지 표현 (쉼표로 구분, 선택)",
            placeholder="예: 너무 쉬워요, 실패해도 괜찮아요",
        )
        preferred_raw = st.text_input(
            "선호 표현 (쉼표로 구분, 선택)",
            placeholder="예: 정성껏, 엄마처럼, 손맛",
        )

        submitted = st.form_submit_button(
            "✅ 채널 생성 후 시작하기",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        errors = _validate_wizard(ch_name, ch_key_raw)
        if errors:
            for e in errors:
                st.error(e)
            return

        # 키 정규화
        ch_key = re.sub(r"[^a-z0-9_]", "_", ch_key_raw.strip().lower())

        target  = target_custom.strip() if target_sel == "직접 입력" else target_sel
        tone    = tone_custom.strip()   if tone_sel   == "직접 입력" else tone_sel
        topics  = [t.strip() for t in typical_topics_raw.split(",") if t.strip()]
        forbidden = [t.strip() for t in forbidden_raw.split(",") if t.strip()]
        preferred = [t.strip() for t in preferred_raw.split(",") if t.strip()]

        profile_data = {
            "channel_name":           ch_name.strip(),
            "channel_key":            ch_key,
            "target_audience":        target,
            "tone":                   tone,
            "narrator_age":           "",
            "narrator_style":         "",
            "core_symbols":           [],
            "visual_style":           "",
            "philosophy_anchor":      [],
            "forbidden_expressions":  forbidden,
            "preferred_expressions":  preferred,
            "typical_topics":         topics,
            "obsidian_channel_dir":   f"채널_{ch_name.strip()}",
        }

        try:
            from core.profile_loader import save_new_profile, select_profile
            save_new_profile(ch_key, profile_data)
            select_profile(ch_key)
            set_state("setup_completed", True)
            save_workspace()
            st.success(f"✅ '{ch_name}' 채널이 생성됐습니다! 사이드바에서 확인하세요.")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"채널 생성 오류: {e}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("기본 채널(현자의거울)로 시작", use_container_width=True, key="wiz_skip_sage"):
            _activate_default_profile("sage_mirror")
    with col2:
        if st.button("마법사 건너뛰기", use_container_width=True, key="wiz_skip"):
            set_state("setup_completed", True)
            save_workspace()
            st.rerun()


def _validate_wizard(ch_name: str, ch_key: str) -> list:
    errors = []
    if not ch_name or not ch_name.strip():
        errors.append("채널명을 입력하세요")
    if not ch_key or not ch_key.strip():
        errors.append("채널 키를 입력하세요")
    elif not re.match(r"^[a-zA-Z0-9_]+$", ch_key.strip()):
        errors.append("채널 키는 영문, 숫자, 밑줄(_)만 사용 가능합니다")
    return errors


def _activate_default_profile(key: str):
    """기본 프로필 선택 후 마법사 종료"""
    try:
        from core.profile_loader import select_profile
        select_profile(key)
    except Exception:
        pass
    set_state("setup_completed", True)
    save_workspace()
    st.rerun()
