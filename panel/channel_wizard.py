# -*- coding: utf-8 -*-
"""
panel/channel_wizard.py — 새 채널 만들기 마법사 (Task 25)

6단계 폼으로 새 채널 생성:
1. Profile YAML 자동 저장
2. prompts/channels/{key}/ + 5개 MD 자동 생성
3. 옵시디언 Raw 채널 폴더 자동 생성
4. 사이드바 드롭다운 자동 반영
"""

import streamlit as st
from core.profile_loader import save_new_profile, select_profile, list_available_profiles
from core.channel_setup import create_channel_with_md


TARGET_OPTIONS = [
    "전 연령",
    "청년 (10~30대)",
    "중장년 (30~50대)",
    "시니어 (50~70대)",
    "직접 입력",
]

TONE_OPTIONS = [
    "차분함 / 절제된",
    "따뜻함 / 공감적",
    "활기참 / 에너지",
    "진지함 / 철학적",
    "직접 입력",
]

VISUAL_OPTIONS = [
    "영화적 (시네마틱)",
    "따뜻한 자연광",
    "미니멀 / 클린",
    "빈티지 / 아날로그",
    "직접 입력",
]


def render_channel_wizard():
    """새 채널 만들기 마법사 UI"""
    st.markdown("## ✨ 새 채널 만들기")
    st.caption("6단계 입력 → Profile YAML + 5개 MD 파일 + 옵시디언 폴더 자동 생성")

    with st.form("channel_wizard_form", clear_on_submit=False):
        st.markdown("### 1단계 — 채널 기본 정보")
        col1, col2 = st.columns(2)
        with col1:
            channel_name = st.text_input(
                "채널 이름 *",
                placeholder="예: 내 마음의 정원",
                help="유튜브 채널명과 동일하게 입력"
            )
        with col2:
            channel_key = st.text_input(
                "채널 키 (영문+숫자, 공백 없이) *",
                placeholder="예: my_garden",
                help="profiles/{key}.yaml 파일명으로 사용됨"
            )

        st.markdown("### 2단계 — 타겟 시청자")
        target_sel = st.selectbox("타겟 시청자 *", TARGET_OPTIONS)
        target_custom = ""
        if target_sel == "직접 입력":
            target_custom = st.text_input("직접 입력", placeholder="예: 40~60대 자영업자")
        target_audience = target_custom if target_sel == "직접 입력" else target_sel

        st.markdown("### 3단계 — 채널 톤")
        tone_sel = st.selectbox("채널 톤 *", TONE_OPTIONS)
        tone_custom = ""
        if tone_sel == "직접 입력":
            tone_custom = st.text_input("직접 입력", placeholder="예: 담담하고 건조한")
        tone = tone_custom if tone_sel == "직접 입력" else tone_sel

        st.markdown("### 4단계 — 자주 다룰 주제")
        typical_topics_raw = st.text_area(
            "자주 다룰 주제 (줄바꿈으로 구분)",
            placeholder="고독\n후회\n가족 관계\n은퇴 후 삶\n의미 찾기",
            height=100,
        )
        typical_topics = [t.strip() for t in typical_topics_raw.splitlines() if t.strip()]

        st.markdown("### 5단계 — 시각 스타일")
        col3, col4 = st.columns(2)
        with col3:
            visual_sel = st.selectbox("시각 스타일", VISUAL_OPTIONS)
            visual_custom = ""
            if visual_sel == "직접 입력":
                visual_custom = st.text_input("직접 입력 (시각 스타일)")
            visual_style = visual_custom if visual_sel == "직접 입력" else visual_sel

        with col4:
            core_symbols_raw = st.text_input(
                "핵심 상징 (쉼표 구분)",
                placeholder="예: 거울, 촛불, 서재",
            )
            core_symbols = [s.strip() for s in core_symbols_raw.split(",") if s.strip()]

        narrator_style = st.text_input(
            "나레이터 스타일",
            placeholder="예: 50대 후반 남성, 낮고 묵직한 중저음, 느린 속도",
        )

        st.markdown("### 6단계 — 금지 / 선호 표현")
        col5, col6 = st.columns(2)
        with col5:
            forbidden_raw = st.text_area(
                "금지 표현 (줄바꿈 구분)",
                placeholder="힘내세요\n응원합니다\n긍정적으로",
                height=80,
            )
            forbidden_expressions = [f.strip() for f in forbidden_raw.splitlines() if f.strip()]

        with col6:
            preferred_raw = st.text_area(
                "선호 표현 (줄바꿈 구분)",
                placeholder="조용히 바라보다\n그 사람도 알까\n말없이",
                height=80,
            )
            preferred_expressions = [p.strip() for p in preferred_raw.splitlines() if p.strip()]

        # 고급 옵션
        with st.expander("⚙️ 고급 옵션 (선택)"):
            philosophy_raw = st.text_input(
                "철학적 앵커 (쉼표 구분)",
                placeholder="예: 스토아, 칼 융, 성경",
            )
            philosophy_anchor = [p.strip() for p in philosophy_raw.split(",") if p.strip()]

            typical_cats_raw = st.text_input(
                "주요 카테고리 (쉼표 구분)",
                placeholder="예: 심리, 철학, 인간관계",
            )
            typical_categories = [c.strip() for c in typical_cats_raw.split(",") if c.strip()]

            color_palette = st.text_input(
                "색채 방향",
                placeholder="예: 어두운 금빛 + 딥 브라운",
            )

        submitted = st.form_submit_button("✅ 채널 생성", type="primary", use_container_width=True)

    if submitted:
        # 필수 검증
        errors = []
        if not channel_name.strip():
            errors.append("채널 이름을 입력하세요")
        if not channel_key.strip():
            errors.append("채널 키를 입력하세요")
        else:
            # 키 유효성 (영문·숫자·언더스코어만)
            import re
            if not re.match(r'^[a-zA-Z0-9_가-힣]+$', channel_key.strip()):
                errors.append("채널 키는 영문, 숫자, 언더스코어(_), 한글만 사용 가능합니다")
        if not target_audience:
            errors.append("타겟 시청자를 선택하세요")
        if not typical_topics:
            errors.append("자주 다룰 주제를 1개 이상 입력하세요")

        # 중복 확인
        existing = list_available_profiles()
        if any(p["key"] == channel_key.strip() for p in existing):
            errors.append(f"채널 키 '{channel_key.strip()}'는 이미 사용 중입니다")

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        else:
            _create_channel(
                channel_name=channel_name.strip(),
                channel_key=channel_key.strip(),
                target_audience=target_audience,
                tone=tone,
                typical_topics=typical_topics,
                visual_style=visual_style,
                core_symbols=core_symbols,
                narrator_style=narrator_style.strip(),
                forbidden_expressions=forbidden_expressions,
                preferred_expressions=preferred_expressions,
                philosophy_anchor=philosophy_anchor,
                typical_categories=typical_categories,
                color_palette=color_palette.strip(),
            )


def _create_channel(**kwargs):
    """채널 생성 실행"""
    key  = kwargs["channel_key"]
    name = kwargs["channel_name"]

    with st.spinner(f"🔧 '{name}' 채널 생성 중..."):
        # 1. Profile YAML 저장
        profile_data = {
            "channel_name":          name,
            "channel_key":           key,
            "target_audience":       kwargs.get("target_audience", ""),
            "tone":                  kwargs.get("tone", ""),
            "narrator_age":          "",
            "narrator_style":        kwargs.get("narrator_style", ""),
            "visual_style":          kwargs.get("visual_style", ""),
            "core_symbols":          kwargs.get("core_symbols", []),
            "philosophy_anchor":     kwargs.get("philosophy_anchor", []),
            "typical_topics":        kwargs.get("typical_topics", []),
            "typical_categories":    kwargs.get("typical_categories", []),
            "forbidden_expressions": kwargs.get("forbidden_expressions", []),
            "preferred_expressions": kwargs.get("preferred_expressions", []),
            "color_palette":         kwargs.get("color_palette", ""),
            "obsidian_channel_dir":  f"채널_{name}",
        }
        save_new_profile(key, profile_data)

        # 2. MD 파일 5개 + 옵시디언 폴더 생성
        md_result = create_channel_with_md(key, profile_data)

        # 3. 채널 선택 적용
        select_profile(key)

    # 결과 표시
    st.success(f"✅ '{name}' 채널 생성 완료!")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**생성된 MD 파일:**")
        for f in md_result.get("md_files", []):
            st.write(f"  ✅ {f}")
    with col2:
        st.markdown("**옵시디언 폴더:**")
        obs = md_result.get("obsidian_folder", "")
        if obs:
            st.code(obs, language=None)

    st.info("사이드바 채널 선택에 자동으로 추가되었습니다. 이제 '시작'을 입력하세요!")
    if st.button("🚀 시작하기", type="primary", use_container_width=True):
        st.rerun()
