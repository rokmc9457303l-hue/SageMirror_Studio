# -*- coding: utf-8 -*-
"""
ui/result_box.py
V17 Reborn 공통 결과창 UI
"""

import streamlit as st
from core.obsidian import save_all


def render_result_box(
    title: str,
    content: str,
    packet: dict = None,
    tags=None,
    source: str = "V17 Reborn",
    height: int = 300,
):
    """
    모든 Part에서 공통으로 쓰는 결과창.
    보기 / 다운로드 / 앱 저장 / 옵시디언 저장을 제공한다.
    """

    if not content:
        st.info("아직 결과가 없습니다.")
        return

    tags = tags or []

    with st.container(border=True):
        st.markdown(f"### {title}")

        st.text_area(
            "결과",
            value=content,
            height=height,
            key=f"result_{abs(hash(title))}",
            label_visibility="collapsed",
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("👁 보기", key=f"view_{abs(hash(title))}", use_container_width=True):
                st.markdown(content)

        with c2:
            st.download_button(
                "📋 다운로드",
                data=content,
                file_name=f"{title}.md",
                mime="text/markdown",
                key=f"download_{abs(hash(title))}",
                use_container_width=True,
            )

        with c3:
            if st.button("💾 앱 저장", key=f"appsave_{abs(hash(title))}", use_container_width=True):
                st.session_state[f"saved_{title}"] = content
                st.toast("앱 상태에 저장했습니다.")

        with c4:
            if st.button("🧠 옵시디언 저장", key=f"obs_{abs(hash(title))}", use_container_width=True):
                paths = save_all(
                    title=title,
                    content=content,
                    packet=packet,
                    tags=tags,
                    source=source,
                )
                st.success("옵시디언 저장 완료")
                st.caption(paths)