# -*- coding: utf-8 -*-
"""
panel/components.py — 공통 UI 컴포넌트
"""

import streamlit as st
from core.state import get_state, set_state


def model_selector(key_suffix: str = "global") -> str:
    """모델 선택 위젯 (Claude 스타일)"""
    from core.config import MODELS, DEFAULT_MODEL
    
    options = list(MODELS.keys())
    current = get_state("current_model", DEFAULT_MODEL)
    
    selected = st.selectbox(
        "🤖 모델",
        options,
        index=options.index(current) if current in options else 0,
        format_func=lambda x: f"{MODELS[x]['label']} — {MODELS[x]['desc']}",
        key=f"model_sel_{key_suffix}",
    )
    
    if selected != current:
        set_state("current_model", selected)
    
    return selected


def copy_button(text: str, key: str, label: str = "📋 복사"):
    """복사 버튼"""
    if st.button(label, key=key):
        try:
            esc = text.replace("`", "\\`").replace("$", "\\$")
            st.html(f"<script>navigator.clipboard.writeText(`{esc}`);</script>")
            st.toast("📋 복사됨")
        except Exception:
            pass


def result_display(result, title: str = "결과", height: int = 300):
    """결과 표시 + 액션 버튼들"""
    if not result:
        return
    
    with st.container(border=True):
        st.markdown(f"**{title}**")
        text = result if isinstance(result, str) else str(result)
        st.text_area("", value=text, height=height, label_visibility="collapsed", key=f"display_{hash(text[:50])}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            copy_button(text, f"copy_{hash(text[:50])}")
        with c2:
            if st.button("👁 보기", key=f"view_{hash(text[:50])}"):
                with st.expander("전체 내용", expanded=True):
                    st.markdown(text)
        with c3:
            if st.button("💾 다운로드", key=f"down_{hash(text[:50])}"):
                st.download_button(
                    "텍스트 다운로드",
                    text,
                    file_name=f"{title}.txt",
                    key=f"dl_{hash(text[:50])}",
                )


def status_indicator(label: str, status: str):
    """상태 표시 (대기·진행·완료)"""
    colors = {"대기": "⬜", "진행": "🔄", "완료": "✅", "오류": "❌"}
    icon = colors.get(status, "⬜")
    st.markdown(f"{icon} **{label}**: `{status}`")
