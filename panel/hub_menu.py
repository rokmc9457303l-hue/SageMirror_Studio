# -*- coding: utf-8 -*-
"""
panel/hub_menu.py — 우측 패널 [+] 자료수집 허브 메뉴

6개 카테고리:
🔍 외부 리서치 / 🎬 미디어 / ☁️ 클라우드 / 📂 직접 추가 / 💾 저장 옵션 / ⚙️ 설정

Day 11: 골격 + UI
Day 12~15: 각 기능 실제 구현
"""

import streamlit as st
from datetime import datetime
from core.state import get_state, set_state
from core.config import PART_NAMES


# ── 6개 카테고리 정의 ────────────────────────────
HUB_CATEGORIES = {
    "research": {
        "icon": "🔍",
        "label": "외부 리서치",
        "color": "#3B82F6",
        "items": [
            {"id": "tavily",      "icon": "🌐", "label": "Tavily 웹 검색",       "ready": True},
            {"id": "gemini",      "icon": "✨", "label": "Gemini Deep Research", "ready": False},
            {"id": "notebooklm",  "icon": "📓", "label": "NotebookLM 열기",     "ready": False},
        ],
    },
    "media": {
        "icon": "🎬",
        "label": "미디어",
        "color": "#EF4444",
        "items": [
            {"id": "yt_channel",   "icon": "📺", "label": "YouTube 채널 분석",      "ready": False},
            {"id": "yt_video",     "icon": "🎥", "label": "YouTube 영상·스크립트",  "ready": False},
            {"id": "yt_comments",  "icon": "💬", "label": "YouTube 댓글 수집",      "ready": False},
        ],
    },
    "cloud": {
        "icon": "☁️",
        "label": "클라우드 자동 동기화",
        "color": "#10B981",
        "items": [
            {"id": "gdrive_sync",  "icon": "📁", "label": "Google Drive 동기화 시작",  "ready": True},
            {"id": "gdrive_test",  "icon": "🔍", "label": "즉시 한 번 동기화",         "ready": True},
            {"id": "gdrive_status","icon": "📊", "label": "동기화 상태 보기",          "ready": True},
            {"id": "gdrive_stop",  "icon": "⏸️", "label": "동기화 정지",                "ready": True},
        ],
    },
    "direct": {
        "icon": "📂",
        "label": "직접 추가",
        "color": "#F59E0B",
        "items": [
            {"id": "upload",  "icon": "💻", "label": "PC 파일 업로드",       "ready": False},
            {"id": "text",    "icon": "📋", "label": "텍스트 직접 입력",      "ready": True},
            {"id": "url",     "icon": "🔗", "label": "URL 자료 가져오기",    "ready": False},
        ],
    },
    "save": {
        "icon": "💾",
        "label": "저장 옵션",
        "color": "#8B5CF6",
        "items": [
            {"id": "rule_save", "icon": "📁", "label": "옵시디언 규칙서 저장",  "ready": True},
            {"id": "univ_save", "icon": "🏷️", "label": "옵시디언 범용 저장",   "ready": True},
            {"id": "raw_wiki",  "icon": "🏛️", "label": "Raw/Wiki/Schema 자동", "ready": True},
            {"id": "rag_direct","icon": "⚡", "label": "RAG 직접 전달",        "ready": False},
        ],
    },
    "config": {
        "icon": "⚙️",
        "label": "설정",
        "color": "#6B7280",
        "items": [
            {"id": "api_keys",   "icon": "🔑", "label": "API 키 관리",        "ready": True},
            {"id": "classify",   "icon": "🏷️", "label": "자동 분류 규칙",     "ready": False},
            {"id": "sync_freq",  "icon": "⏱️", "label": "동기화 주기",        "ready": False},
        ],
    },
}


# ── 메인 렌더링 ──────────────────────────────────
def render_hub_menu():
    """[+] 버튼 클릭 시 펼쳐지는 허브 메뉴"""
    
    hub_open = get_state("rp_hub_open", False)
    
    # [+] 토글 버튼
    button_label = "✕ 닫기" if hub_open else "➕ 자료 수집"
    
    if st.button(button_label, key="hub_toggle", use_container_width=True):
        set_state("rp_hub_open", not hub_open)
        st.rerun()
    
    if not hub_open:
        return
    
    # 허브 메뉴 펼침
    st.markdown("---")
    st.markdown("#### 🛠️ 자료수집 허브")
    
    # 보완 요청 알림 (좌측 RAG 박스에서 트리거된 경우)
    request = get_state("rp_supplement_request")
    if request:
        with st.container(border=True):
            st.warning(
                f"📥 **Part {request['part_num']} ({request['part_name']})** 자료 보완 요청"
            )
            if st.button("✕ 알림 닫기", key="close_supplement_req"):
                set_state("rp_supplement_request", None)
                st.rerun()
    
    # 6개 카테고리 탭으로
    cat_keys = list(HUB_CATEGORIES.keys())
    cat_labels = [f"{HUB_CATEGORIES[k]['icon']} {HUB_CATEGORIES[k]['label']}" for k in cat_keys]
    
    tabs = st.tabs(cat_labels)
    
    for i, key in enumerate(cat_keys):
        with tabs[i]:
            render_category(key)


def render_category(category_key: str):
    """카테고리별 메뉴 항목 표시"""
    
    cat = HUB_CATEGORIES[category_key]
    
    st.markdown(f"#### {cat['icon']} {cat['label']}")
    
    for item in cat["items"]:
        ready = item.get("ready", False)
        
        with st.container(border=True):
            cols = st.columns([4, 1])
            
            with cols[0]:
                st.markdown(f"{item['icon']} **{item['label']}**")
                if not ready:
                    st.caption("🔜 Day 12~15에서 구현 예정")
            
            with cols[1]:
                if ready:
                    if st.button("실행", key=f"hub_{category_key}_{item['id']}",
                                 use_container_width=True, type="primary"):
                        handle_hub_action(category_key, item['id'])
                else:
                    st.button("대기", key=f"hub_{category_key}_{item['id']}",
                             disabled=True, use_container_width=True)


def handle_hub_action(category: str, item_id: str):
    """카테고리 + 아이템 ID 에 따른 액션 처리"""
    
    # 임시 구현 — Day 12~15 에 각 기능 채워짐
    
    if item_id == "tavily":
        set_state("hub_action", {"type": "tavily_search", "ready": True})
        st.toast("🌐 Tavily 검색 패널 (Day 15 구현)")
    
    elif item_id == "text":
        set_state("hub_action", {"type": "text_input", "ready": True})
        st.toast("📋 텍스트 입력 패널 (즉시 사용 가능)")
    
    elif item_id == "rule_save":
        st.toast("📁 옵시디언 규칙서 저장 (이미 자동 작동 중)")
    
    elif item_id == "univ_save":
        st.toast("🏷️ 옵시디언 범용 저장 (이미 자동 작동 중)")
    
    elif item_id == "raw_wiki":
        st.toast("🏛️ Raw/Wiki/Schema 자동 분류 (Day 9 완료)")
    
    elif item_id == "api_keys":
        set_state("hub_action", {"type": "api_keys", "ready": True})
        st.toast("🔑 API 키 설정 (사이드바에서 가능)")
    
    elif item_id == "gdrive_sync":
        from core.gdrive_sync import start_auto_sync
        success = start_auto_sync()
        if success:
            st.toast("✅ Google Drive 자동 동기화 시작 (5분 주기)")
        else:
            st.toast("⚠️ 이미 동기화 진행 중")
    
    elif item_id == "gdrive_test":
        from core.gdrive_sync import sync_drive_folder
        with st.spinner("Google Drive 폴더 확인 중..."):
            result = sync_drive_folder()
        if result.get("success"):
            new_count = result.get("new_files", 0)
            if new_count > 0:
                st.toast(f"✅ 새 파일 {new_count}건 옵시디언에 저장")
            else:
                st.toast(result.get("message", "새 파일 없음"))
        else:
            st.toast(f"❌ {result.get('error', '동기화 실패')}")
    
    elif item_id == "gdrive_status":
        from core.gdrive_sync import get_sync_status
        status = get_sync_status()
        set_state("show_gdrive_status", status)
        st.rerun()
    
    elif item_id == "gdrive_stop":
        from core.gdrive_sync import stop_auto_sync
        stop_auto_sync()
        st.toast("⏸️ 자동 동기화 정지")

    else:
        st.toast(f"🔜 '{item_id}' 기능 Day 12~15 구현 예정")


def render_text_input_panel():
    """텍스트 직접 입력 패널 (즉시 사용 가능)"""
    
    action = get_state("hub_action", {})
    if action.get("type") != "text_input":
        return
    
    with st.expander("📋 텍스트 직접 입력", expanded=True):
        title = st.text_input("제목", key="hub_text_title")
        content = st.text_area("내용", height=150, key="hub_text_content")
        
        col1, col2 = st.columns(2)
        
        save_choice = col1.selectbox(
            "저장 위치",
            ["옵시디언 (Raw + 범용)", "옵시디언 (Raw만)", "RAG 직접 전달"],
            key="hub_text_save_choice",
        )
        
        if col2.button("💾 저장", key="hub_text_save", type="primary", use_container_width=True):
            if not title or not content:
                st.error("제목과 내용을 모두 입력하세요")
                return
            
            from core.unified_save import save_anything
            save_anything(
                content=content,
                title=title,
                content_type="external_research",
                extra_meta={"source": "사용자 직접 입력"},
            )
            
            st.success(f"✅ '{title}' 저장 완료")
            set_state("hub_action", None)
            st.rerun()
