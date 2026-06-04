# -*- coding: utf-8 -*-
"""
core/rag_status_box.py — 좌측 메인 영역 RAG 자료 상태 박스

각 파트 상단에 표시:
- 옵시디언 자료 카운트
- 색상 표시 (🟢/🟡/🔴)
- 우측에 보완 요청 버튼
- 상세 보기
"""

import streamlit as st
from pathlib import Path
from core.config import (
    PART_NAMES, OBSIDIAN_CHANNEL, OBSIDIAN_UNIVERSAL, OBSIDIAN_SYSTEM,
)
from core.state import get_state, set_state


# ── 파트별 관련 카테고리 매핑 ────────────────────
PART_RELATED_CATEGORIES = {
    1: ["감정", "유튜브전략", "채널운영", "출처자료"],
    2: ["철학", "성경·신앙", "심리학", "다크심리학"],
    3: ["문학·에세이", "고전소설", "한국문학", "감정"],
    4: ["제작자료"],
    5: ["제작자료"],
    6: ["제작자료"],
    7: ["유튜브전략", "제작자료"],
    8: ["채널운영", "유튜브전략"],
}


def count_files_in_path(path: Path) -> int:
    """폴더의 .md 파일 수"""
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob("*.md"))


def get_color(count: int, threshold_low: int = 2, threshold_mid: int = 5) -> str:
    """카운트에 따른 색상"""
    if count == 0:
        return "🔴"
    elif count < threshold_low:
        return "🔴"
    elif count < threshold_mid:
        return "🟡"
    else:
        return "🟢"


def get_rag_status(part_num: int) -> dict:
    """파트별 RAG 자료 상태 종합 조회"""
    
    part_name = PART_NAMES.get(part_num, "?")
    
    # 1. 채널 규칙서 자료
    channel_folder = OBSIDIAN_CHANNEL / f"Part{part_num}_{part_name}"
    channel_count = count_files_in_path(channel_folder)
    
    # 2. 시스템/10_Wiki 전체
    wiki_base = OBSIDIAN_SYSTEM / "10_Wiki"
    wiki_count = 0
    if wiki_base.exists():
        wiki_count = sum(1 for _ in wiki_base.rglob("*.md") if not _.name.startswith("_"))
    
    # 3. 시스템/00_Raw 전체
    raw_base = OBSIDIAN_SYSTEM / "00_Raw"
    raw_count = 0
    if raw_base.exists():
        raw_count = sum(1 for _ in raw_base.rglob("*.md") if not _.name.startswith("_"))
    
    # 4. 관련 범용 카테고리
    related_cats = PART_RELATED_CATEGORIES.get(part_num, [])
    universal_status = []
    for cat in related_cats:
        cat_folder = OBSIDIAN_UNIVERSAL / cat
        count = count_files_in_path(cat_folder)
        universal_status.append({
            "category": cat,
            "count": count,
            "color": get_color(count, 2, 5),
        })
    
    # 5. 총 자료
    total = channel_count + wiki_count + raw_count + sum(c["count"] for c in universal_status)
    
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
    """좌측 메인 영역에 RAG 자료 상태 박스 표시"""
    
    status = get_rag_status(part_num)
    
    with st.container(border=True):
        st.markdown(f"### 🧠 RAG 자료 상태  &nbsp; {status['total_color']} 총 {status['total']}건")
        
        # 상세 정보 (2열)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📁 채널 자료**")
            ch = status["channel"]
            st.caption(f"{ch['color']} {ch['path']}: {ch['count']}건")
            
            st.markdown("**📚 시스템 자료**")
            st.caption(f"{status['wiki']['color']} 시스템/10_Wiki: {status['wiki']['count']}건")
            st.caption(f"{status['raw']['color']} 시스템/00_Raw: {status['raw']['count']}건")
        
        with col2:
            st.markdown("**🏷️ 관련 범용 카테고리**")
            for cat_info in status["universal"]:
                st.caption(f"{cat_info['color']} 범용/{cat_info['category']}: {cat_info['count']}건")
        
        # 액션 버튼
        st.markdown("")
        b1, b2, b3 = st.columns(3)
        
        with b1:
            if st.button("📥 우측에 자료 보완 요청", key=f"req_supplement_{part_num}", use_container_width=True):
                set_state("rp_supplement_request", {
                    "part_num": part_num,
                    "part_name": status["part_name"],
                    "status": status,
                })
                st.toast("✅ 우측 작업창에 보완 요청 전달됨")
        
        with b2:
            if st.button("📊 자료 상세 보기", key=f"show_detail_{part_num}", use_container_width=True):
                set_state(f"show_rag_detail_{part_num}", True)
        
        with b3:
            if st.button("🔄 새로 고침", key=f"refresh_rag_{part_num}", use_container_width=True):
                st.rerun()
        
        # 상세 보기
        if get_state(f"show_rag_detail_{part_num}", False):
            with st.expander("📊 자료 상세", expanded=True):
                st.json(status)
                if st.button("닫기", key=f"close_detail_{part_num}"):
                    set_state(f"show_rag_detail_{part_num}", False)
                    st.rerun()
