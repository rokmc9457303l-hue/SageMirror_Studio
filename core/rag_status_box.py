# -*- coding: utf-8 -*-
"""
core/rag_status_box.py — 좌측 메인 영역 RAG 자료 상태 박스
"""

import streamlit as st
from pathlib import Path
from core.config import (
    PART_NAMES,
    OBSIDIAN_WIKI,
    OBSIDIAN_RAW,
    OBSIDIAN_ARCHIVE,
)
from core.state import get_state, set_state
from core.obsidian import get_channel_path


_DEFAULT_PART_CATEGORIES = {
    1: ["감정", "유튜브전략", "채널운영", "출처자료"],
    2: ["철학", "성경·신앙", "심리학", "다크심리학"],
    3: ["문학·에세이", "고전소설", "한국문학", "감정"],
    4: ["제작자료"],
    5: ["제작자료"],
    6: ["제작자료"],
    7: ["유튜브전략", "제작자료"],
    8: ["채널운영", "유튜브전략"],
}


def get_part_categories(part_num: int) -> list:
    """Profile YAML의 typical_categories 필드 우선, 없으면 기본값"""
    try:
        from core.profile_loader import load_current_profile
        p = load_current_profile()
        cats = p.get("typical_categories", {})
        if isinstance(cats, dict) and part_num in cats:
            return cats[part_num]
        if isinstance(cats, dict) and str(part_num) in cats:
            return cats[str(part_num)]
    except Exception:
        pass
    return _DEFAULT_PART_CATEGORIES.get(part_num, ["제작자료"])


# 하위 호환
PART_RELATED_CATEGORIES = _DEFAULT_PART_CATEGORIES


def count_files_in_path(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob("*.md"))


def get_color(count: int, threshold_low: int = 2, threshold_mid: int = 5) -> str:
    if count == 0:
        return "🔴"
    elif count < threshold_low:
        return "🔴"
    elif count < threshold_mid:
        return "🟡"
    else:
        return "🟢"


def get_rag_status(part_num: int) -> dict:
    part_name = PART_NAMES.get(part_num, "?")

    # 1. 채널 자료
    channel_folder = get_channel_path() / f"Part{part_num}_{part_name}"
    channel_count = count_files_in_path(channel_folder)

    # 2. Wiki 전체
    wiki_count = 0
    if OBSIDIAN_WIKI.exists():
        wiki_count = sum(1 for _ in OBSIDIAN_WIKI.rglob("*.md")
                        if not _.name.startswith("_"))

    # 3. Raw 전체
    raw_count = 0
    if OBSIDIAN_RAW.exists():
        raw_count = sum(1 for _ in OBSIDIAN_RAW.rglob("*.md")
                       if not _.name.startswith("_"))

    # 4. 관련 범용 카테고리 (Profile 동적 로드)
    related_cats = get_part_categories(part_num)
    universal_status = []
    for cat in related_cats:
        cat_folder = OBSIDIAN_WIKI / cat
        count = count_files_in_path(cat_folder)
        universal_status.append({
            "category": cat,
            "count": count,
            "color": get_color(count, 2, 5),
        })

    total = (channel_count + wiki_count + raw_count
             + sum(c["count"] for c in universal_status))

    return {
        "part_num": part_num,
        "part_name": part_name,
        "channel": {
            "count": channel_count,
            "color": get_color(channel_count, 2, 5),
            "path": f"Part{part_num}_{part_name}",
        },
        "wiki": {
            "count": wiki_count,
            "color": get_color(wiki_count, 5, 20),
        },
        "raw": {
            "count": raw_count,
            "color": get_color(raw_count, 3, 10),
        },
        "universal": universal_status,
        "total": total,
        "total_color": get_color(total, 5, 15),
    }


def render_rag_status_box(part_num: int):
    status = get_rag_status(part_num)

    with st.container(border=True):
        st.markdown(
            f"### 🧠 RAG 자료 상태  &nbsp; "
            f"{status['total_color']} 총 {status['total']}건"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📁 채널 자료**")
            ch = status["channel"]
            st.caption(f"{ch['color']} {ch['path']}: {ch['count']}건")

            st.markdown("**📚 전체 자료**")
            st.caption(
                f"{status['wiki']['color']} Wiki: {status['wiki']['count']}건"
            )
            st.caption(
                f"{status['raw']['color']} Raw: {status['raw']['count']}건"
            )

        with col2:
            st.markdown("**🏷️ 관련 카테고리**")
            for cat_info in status["universal"]:
                st.caption(
                    f"{cat_info['color']} "
                    f"{cat_info['category']}: {cat_info['count']}건"
                )

        st.markdown("")
        b1, b2, b3 = st.columns(3)

        with b1:
            if st.button(
                "📥 자료 보완 요청",
                key=f"req_supplement_{part_num}",
                use_container_width=True,
            ):
                set_state("rp_supplement_request", {
                    "part_num": part_num,
                    "part_name": status["part_name"],
                    "status": status,
                })
                st.toast("✅ 우측 작업창에 보완 요청 전달됨")

        with b2:
            if st.button(
                "📊 상세 보기",
                key=f"show_detail_{part_num}",
                use_container_width=True,
            ):
                set_state(f"show_rag_detail_{part_num}", True)

        with b3:
            if st.button(
                "🔄 새로고침",
                key=f"refresh_rag_{part_num}",
                use_container_width=True,
            ):
                st.rerun()

        if get_state(f"show_rag_detail_{part_num}", False):
            with st.expander("📊 자료 상세", expanded=True):
                st.json(status)
                if st.button("닫기", key=f"close_detail_{part_num}"):
                    set_state(f"show_rag_detail_{part_num}", False)
                    st.rerun()
