# -*- coding: utf-8 -*-
"""
parts/_template.py — 표준 파트 템플릿 (모든 8파트의 베이스)

각 파트는 이 파일을 복사해서 만든다.
파트별 고유 로직만 _generate() 함수에 구현.
나머지 (RAG, 검증, 저장, 패킷)는 자동 처리.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path

from core.config import PART_NAMES, PROMPTS_PATH
from core.state import get_state, set_state, save_workspace
from core.brain import call_model
from core.obsidian import search_rag, save_dual
from safety.tone_filter import filter_ai_smell
from safety.citation_validator import validate_citations
from safety.protagonist_check import check_protagonist_voice


def load_prompt(part_num: int) -> str:
    """파트별 프롬프트 파일 로드"""
    master = (PROMPTS_PATH / "_master_protocol.md").read_text(encoding="utf-8")
    part_files = list(PROMPTS_PATH.glob(f"part{part_num}_*.md"))
    if part_files:
        part_prompt = part_files[0].read_text(encoding="utf-8")
        return master + "\n\n" + part_prompt
    return master


def get_part_context(part_num: int) -> dict:
    """현재 파트의 컨텍스트 + RAG 자료 수집"""
    prev_packet = get_state(f"p{part_num - 1}_packet") if part_num > 1 else None
    
    rag_query = ""
    if prev_packet and isinstance(prev_packet, dict):
        rag_query = str(prev_packet.get("topic", "")) + " " + \
                   " ".join(prev_packet.get("emotion_keywords", []))
    
    obsidian_rag = search_rag(rag_query, max_files=5, max_chars=400) if rag_query else ""
    
    return {
        "part_num":     part_num,
        "part_name":    PART_NAMES.get(part_num, "?"),
        "prev_packet":  prev_packet,
        "obsidian_rag": obsidian_rag,
        "current_episode": get_state("current_episode", "EP001"),
    }


def render_part_template(part_num: int, generate_fn=None):
    """
    표준 파트 렌더링 (모든 파트 공통)
    
    Args:
        part_num: 1~8
        generate_fn: 파트별 고유 생성 함수 (없으면 기본 처리)
    """
    part_name = PART_NAMES.get(part_num, "?")
    
    # ── 헤더 ──────────────────────────────────────
    st.markdown(f"## 📍 Part {part_num} — {part_name}")
    
    # ── 이전 파트 패킷 확인 ───────────────────────
    if part_num > 1:
        prev_packet = get_state(f"p{part_num - 1}_packet")
        if not prev_packet:
            st.warning(f"⚠️ Part {part_num - 1} ({PART_NAMES.get(part_num - 1)}) 를 먼저 완료하세요")
            return
        else:
            with st.expander(f"📥 Part {part_num - 1} 전달 패킷 확인"):
                st.json(prev_packet)
    
    # ── 작업 탭 ──────────────────────────────────
    tabs = st.tabs(["🎬 작업", "🔍 검증", "📤 전달 패킷", "📊 상태"])
    
    with tabs[0]:
        render_work_tab(part_num, generate_fn)
    
    with tabs[1]:
        render_validation_tab(part_num)
    
    with tabs[2]:
        render_packet_tab(part_num)
    
    with tabs[3]:
        render_status_tab(part_num)


def render_work_tab(part_num: int, generate_fn=None):
    """작업 탭 — 생성·실행"""
    st.markdown("### 🎬 작업 실행")
    
    context = get_part_context(part_num)
    
    if context["obsidian_rag"]:
        with st.expander(f"🧠 옵시디언 RAG 자료 (자동 주입됨)"):
            st.markdown(context["obsidian_rag"][:1000])
    
    user_input = st.text_area(
        "추가 지시사항 (선택)",
        placeholder="기본 프롬프트 외 추가하고 싶은 지시사항을 입력하세요...",
        height=80,
        key=f"p{part_num}_user_input",
    )
    
    if st.button(f"🚀 Part {part_num} 작업 시작", key=f"p{part_num}_start", type="primary", use_container_width=True):
        if generate_fn:
            with st.spinner("⚙️ 작업 중..."):
                result = generate_fn(context, user_input)
            if result:
                set_state(f"p{part_num}_result", result)
                set_state(f"p{part_num}_status", "완료")
                st.success(f"✅ Part {part_num} 작업 완료")
                st.rerun()
        else:
            st.info("이 파트의 생성 함수가 아직 구현되지 않았습니다.")
    
    result = get_state(f"p{part_num}_result")
    if result:
        st.markdown("---")
        st.markdown("### 📋 작업 결과")
        st.markdown(result if isinstance(result, str) else str(result))


def render_validation_tab(part_num: int):
    """검증 탭 — 안전 시스템 적용"""
    st.markdown("### 🔍 안전 검증")
    
    result = get_state(f"p{part_num}_result")
    if not result:
        st.info("먼저 작업 탭에서 결과를 생성하세요")
        return
    
    text = result if isinstance(result, str) else str(result)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**AI 냄새 검사**")
        tone_result = filter_ai_smell(text)
        if tone_result["clean"]:
            st.success("✅ 통과")
        else:
            st.error(f"❌ {tone_result['count']}건 검출")
            with st.expander("상세"):
                for item in tone_result["detected"]:
                    st.write(f"- {item}")
    
    with col2:
        st.markdown("**인용 검증**")
        cite_result = validate_citations(text)
        score = cite_result["trust_score"]
        if score >= 0.8:
            st.success(f"✅ 신뢰도 {score:.0%}")
        elif score >= 0.5:
            st.warning(f"⚠️ 신뢰도 {score:.0%}")
        else:
            st.error(f"❌ 신뢰도 {score:.0%}")
        
        with st.expander("상세"):
            st.write(f"검증됨: {len(cite_result['verified'])}건")
            st.write(f"확인 필요: {len(cite_result['suspicious'])}건")
    
    with col3:
        st.markdown("**화자 일관성**")
        voice_result = check_protagonist_voice(text)
        if voice_result["consistent"]:
            st.success("✅ @Protagonist 일관성 유지")
        else:
            st.error("❌ 일관성 문제 발견")
            with st.expander("상세"):
                for issue in voice_result["issues"]:
                    st.write(f"- {issue}")


def render_packet_tab(part_num: int):
    """전달 패킷 탭 — 다음 파트로 전달"""
    st.markdown(f"### 📤 Part {part_num + 1} 전달 패킷")
    
    result = get_state(f"p{part_num}_result")
    if not result:
        st.info("먼저 작업을 완료하세요")
        return
    
    existing_packet = get_state(f"p{part_num}_packet")
    
    if not existing_packet:
        if st.button("📦 전달 패킷 생성", key=f"p{part_num}_packet_create", type="primary"):
            packet = {
                "packet_type": f"P{part_num}_PACKET",
                "part_num":    part_num,
                "part_name":   PART_NAMES.get(part_num),
                "timestamp":   datetime.now().isoformat(),
                "episode":     get_state("current_episode"),
                "result":      result if isinstance(result, str) else str(result),
            }
            set_state(f"p{part_num}_packet", packet)
            
            saved = save_dual(
                content=str(result),
                title=f"Part{part_num}_{PART_NAMES[part_num]}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                part_num=part_num,
                source_type="파트 결과물",
            )
            st.success("✅ 패킷 생성 + 옵시디언 듀얼 저장 완료")
            st.json({
                "규칙서 저장": saved["규칙서"],
                "범용 저장 수": len(saved["범용"]),
            })
            save_workspace()
            st.rerun()
    else:
        st.success("✅ 전달 패킷 준비됨")
        st.json(existing_packet)
        
        if st.button("🔄 패킷 재생성", key=f"p{part_num}_packet_redo"):
            set_state(f"p{part_num}_packet", None)
            st.rerun()


def render_status_tab(part_num: int):
    """상태 탭 — 진행 상황·통계"""
    st.markdown("### 📊 파트 상태")
    
    status = get_state(f"p{part_num}_status", "대기")
    packet = get_state(f"p{part_num}_packet")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("작업 상태", status)
    c2.metric("패킷", "완료" if packet else "미생성")
    c3.metric("다음 파트", PART_NAMES.get(part_num + 1, "(최종)"))
    
    st.markdown("---")
    st.markdown("**8파트 전체 진행 상황**")
    for i in range(1, 9):
        s = get_state(f"p{i}_status", "대기")
        p = get_state(f"p{i}_packet")
        icon = "✅" if s == "완료" and p else ("🔄" if s != "대기" else "⬜")
        st.write(f"{icon} Part {i} — {PART_NAMES[i]} : {s}")
