# -*- coding: utf-8 -*-
"""
sage_popups.py — 팝업 다이얼로그 v2.0
[세이지 팝업 전면 업그레이드]
- 파트 인식 컨텍스트 주입 (각 파트에서 열면 해당 파트 데이터 자동 주입)
- 젬마 모델 선택 (gemma4:e2b / gemma4:e4b)
- 정직한 응답 (모를 때 → Tavily 자동 검색 → 답변)
- 대화 완료 시 옵시디언 키워드/태그 자동 저장
- 채팅 UI: 마크다운 링크, 드래그 복사, 수정 가능
- 파트 작업 지시 모드 (팝업에서 파트 데이터 직접 수정 지시)
"""

import streamlit as st
from datetime import datetime
from sage_config import (
    DEFAULT_OBSIDIAN_RULES, DEFAULT_BASE_PROMPT,
    SAGE_PERSONA, OLLAMA_MODEL,
)
from sage_engine import call_gemma, call_gemma_stream, tavily_search, check_ollama_status

# 사용 가능한 모델 목록
AVAILABLE_MODELS = ["gemma4:e2b", "gemma4:e4b"]

# 파트별 컨텍스트 맵
PART_CONTEXT_MAP = {
    "part1": {
        "name": "Part 1 — Librarian (벤치마킹 & 타겟 분석)",
        "keys": ["p1_topic_selection", "p1_bench_result", "p1_research_result", "p1_planning_result"],
        "desc": "유튜브 채널 벤치마킹, 타겟 분석, 주제 선정, 기획안 작성 파트",
    },
    "part2": {
        "name": "Part 2 — Alchemist (철학·감정 융합)",
        "keys": ["p2_topic_selection", "p2_research_result", "p2_planning_result"],
        "desc": "성경-철학-에세이 3원 융합 자료조사 및 총괄 기획안 작성 파트",
    },
    "part34": {
        "name": "Part 3-4 — Architect & Writer (대본 설계)",
        "keys": ["p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data"],
        "desc": "112씬 구조 설계, 나레이션/이미지/캡컷 대본 집필 파트",
    },
    "part5": {
        "name": "Part 5 — Image Consistency (구글 플로우 연동)",
        "keys": ["p5_a_result", "p5_b_result", "p5_c_results"],
        "desc": "@Protagonist 일관성 확보 및 이미지 프롬프트 최종 검증 파트",
    },
    "part5img": {
        "name": "Part 5 — Image Generation (이미지 생성)",
        "keys": ["p5_a_result", "p5_c_results"],
        "desc": "이미지 생성 및 검증 파트",
    },
    "part6": {
        "name": "Part 6 — Narration & BGM (나레이션 & BGM)",
        "keys": ["p34_narration_script"],
        "desc": "CosyVoice 나레이션 생성 및 BGM 배분 파트",
    },
    "part7": {
        "name": "Part 7 — CapCut Bridge (캡컷 자동 조립)",
        "keys": ["p34_capcut_data", "p34_image_script"],
        "desc": "캡컷 에셋 자동 조립 및 타임라인 배분 파트",
    },
    "part8": {
        "name": "Part 8 — Final Assembly (최종 완성)",
        "keys": [],
        "desc": "전체 파이프라인 결과물 최종 검토 및 업로드 준비 파트",
    },
}

def _get_current_part() -> str:
    """현재 선택된 파트를 세션 스테이트에서 읽어옴"""
    sidebar_part = st.session_state.get("sidebar_part", "")
    if "part1" in sidebar_part.lower() or "librarian" in sidebar_part.lower():
        return "part1"
    elif "part2" in sidebar_part.lower() or "alchemist" in sidebar_part.lower():
        return "part2"
    elif "part3" in sidebar_part.lower() or "architect" in sidebar_part.lower():
        return "part34"
    elif "part4" in sidebar_part.lower() or "writer" in sidebar_part.lower():
        return "part34"
    elif "image consistency" in sidebar_part.lower():
        return "part5"
    elif "image" in sidebar_part.lower() and "part5" in sidebar_part.lower():
        return "part5img"
    elif "part6" in sidebar_part.lower() or "narration" in sidebar_part.lower() or "bgm" in sidebar_part.lower():
        return "part6"
    elif "part7" in sidebar_part.lower() or "capcut" in sidebar_part.lower():
        return "part7"
    elif "part8" in sidebar_part.lower() or "final" in sidebar_part.lower():
        return "part8"
    return "part1"


def _build_part_context(part_key: str) -> str:
    """현재 파트의 데이터를 컨텍스트 문자열로 변환"""
    info = PART_CONTEXT_MAP.get(part_key, PART_CONTEXT_MAP["part1"])
    ctx = f"[현재 작업 파트: {info['name']}]\n{info['desc']}\n\n"
    ctx += "[현재 파트 세션 데이터 (작업 참조용)]\n"
    for k in info["keys"]:
        val = st.session_state.get(k, "")
        if val:
            val_str = str(val)[:500] + ("..." if len(str(val)) > 500 else "")
            ctx += f"- {k}: {val_str}\n"
    return ctx


def _build_obsidian_rag_context() -> str:
    """옵시디언 저장 자료 중 최근 세션 데이터를 컨텍스트로 읽어옴"""
    import os
    from pathlib import Path

    ctx = "[옵시디언 RAG 최근 자료 요약]\n"
    vault_root = Path(r"C:\SageMirror_Production\00_Obsidian")

    if not vault_root.exists():
        return ctx + "(옵시디언 자료 없음)\n"

    try:
        md_files = list(vault_root.rglob("*.md"))
        md_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        loaded = 0
        for mf in md_files[:5]:  # 최근 5개 파일
            try:
                content = mf.read_text(encoding="utf-8", errors="ignore")
                ctx += f"\n### [{mf.parent.name}/{mf.stem}]\n{content[:300]}...\n"
                loaded += 1
            except Exception:
                continue
        if loaded == 0:
            ctx += "(최근 저장된 옵시디언 파일 없음)\n"
    except Exception as e:
        ctx += f"(옵시디언 파일 읽기 오류: {e})\n"

    return ctx


def _auto_save_chat_to_obsidian(chat_history: list, part_name: str, model_name: str):
    """대화 기록을 옵시디언에 자동 저장 (키워드/태그 세분화)"""
    import os
    from pathlib import Path

    if not chat_history:
        return

    try:
        all_text = "\n".join([f"[{m['role'].upper()}] {m['content']}" for m in chat_history])

        # 간단 키워드 추출 (젬마 호출)
        kw_prompt = f"""아래 대화에서 핵심 키워드 4~5개를 쉼표로만 출력하라. 설명 금지.
예: 외로움, 쇼펜하우어, 자아성찰, 심리치유

[대화 내용]
{all_text[:800]}

[KEYWORDS]:"""
        try:
            keywords_raw = call_gemma(kw_prompt, model=model_name)
            tag_list = [t.strip() for t in keywords_raw.replace("#","").split(",") if t.strip()][:5]
        except Exception:
            tag_list = ["세이지대화", "현자의거울", "심리치유"]

        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
        tag_hashes = " ".join([f"#{t}" for t in tag_list])

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"[Sage Chat] {part_name} — {ts}"

        content_md = f"""# 🤖 세이지 팝업 대화 기록

## 📌 기본 정보
- 파트: {part_name}
- 모델: {model_name}
- 저장 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🎯 핵심 키워드 / RAG 태그
- 연결 개념 링크: {tag_links if tag_links else '[[세이지대화]], [[현자의거울]]'}
- 태그: {tag_hashes if tag_hashes else '#세이지대화'}

## 💬 대화 내용

"""
        for msg in chat_history:
            role_icon = "🧑 **사용자**" if msg["role"] == "user" else f"🤖 **Sage ({model_name})**"
            content_md += f"### {role_icon}\n{msg['content']}\n\n---\n\n"

        content_md += f"""## 🔗 파이프라인 연결
- 출처: {part_name} 팝업 대화
- 저장 모델: {model_name}
- Tavily 검색 병행 여부: 자동

---
*[SOURCE: 출처 미확인 — {model_name} 생성, {ts}]*
"""
        save_dir = Path(r"C:\SageMirror_Production\00_Obsidian\ChatMemory")
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"chat_{ts}.md"
        save_path.write_text(content_md, encoding="utf-8")
        return str(save_path)
    except Exception as e:
        return None


def _apply_part_action(part_key: str, instruction: str, response: str):
    """젬마 지시에 따라 해당 파트 세션 데이터를 직접 수정"""
    inst_lower = instruction.lower()
    info = PART_CONTEXT_MAP.get(part_key, {})

    # 나레이션 대본 교체 지시
    if any(k in inst_lower for k in ["나레이션", "narration", "나레"]):
        if "p34_narration_script" in info.get("keys", []):
            if len(response) > 50:
                st.session_state.p34_narration_script = response
                return "✅ 나레이션 대본이 업데이트되었습니다."

    # 기획안 교체 지시
    if any(k in inst_lower for k in ["기획안", "planning", "기획"]):
        if "p2_planning_result" in info.get("keys", []):
            if len(response) > 50:
                st.session_state.p2_planning_result = response
                return "✅ 총괄 기획안이 업데이트되었습니다."
        elif "p1_planning_result" in info.get("keys", []):
            if len(response) > 50:
                st.session_state.p1_planning_result = response
                return "✅ 기획안이 업데이트되었습니다."

    # 이미지 대본 교체 지시
    if any(k in inst_lower for k in ["이미지", "image script", "c-1"]):
        if "p34_image_script" in info.get("keys", []):
            if len(response) > 50:
                st.session_state.p34_image_script = response
                return "✅ 이미지 대본이 업데이트되었습니다."

    return None


def _on_popup_send():
    q = st.session_state.get("popup_chat_input_ta", "")
    if q.strip():
        st.session_state.popup_history.append({"role": "user", "content": q})
        st.session_state.pending_stream = q
        st.session_state.popup_chat_input_ta = ""


# =====================================================================
# 옵시디언 규칙서 편집 팝업
# =====================================================================
@st.dialog("📚 옵시디언 규칙서 — 상세 편집", width="large")
def popup_edit_obsidian():
    st.caption("성경·철학·에세이 참조 원칙 (모든 파트의 Gemma 호출 시스템 컨텍스트로 주입)")
    st.markdown("##### 📖 현재 내용 (스크롤 + 드래그 복사)")
    with st.container(height=350, border=True):
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;"
            f"padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>"
            f"{st.session_state.obsidian_rules}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("##### ✏️ 편집 (마우스로 세로 크기 자유 조절)")
    new_val = st.text_area(
        "옵시디언 규칙서 본문",
        value=st.session_state.obsidian_rules,
        height=280,
        key="popup_obsidian_edit_ta",
        label_visibility="collapsed",
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💾 저장", use_container_width=True, type="primary", key="ob_save"):
            st.session_state.obsidian_history.append(st.session_state.obsidian_rules)
            st.session_state.obsidian_rules = new_val
            st.toast("✅ 옵시디언 규칙서 저장", icon="✅")
            st.rerun()
    with c2:
        if st.button(
            f"⬅️ 뒤로 ({len(st.session_state.obsidian_history)})",
            use_container_width=True, key="ob_back",
            disabled=len(st.session_state.obsidian_history) == 0,
        ):
            st.session_state.obsidian_rules = st.session_state.obsidian_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 기본값", use_container_width=True, key="ob_reset"):
            st.session_state.obsidian_history.append(st.session_state.obsidian_rules)
            st.session_state.obsidian_rules = DEFAULT_OBSIDIAN_RULES
            st.rerun()
    with c4:
        st.download_button(
            "📥 .md",
            data=st.session_state.obsidian_rules,
            file_name=f"obsidian_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            use_container_width=True, key="ob_dl",
        )


# =====================================================================
# 기본 프롬프트 편집 팝업
# =====================================================================
@st.dialog("🎯 기본 프롬프트 (타겟 선정 원칙) — 상세 편집", width="large")
def popup_edit_prompt():
    st.caption("Part 1 Librarian의 채널 선정 1·2순위 규칙.")
    st.markdown("##### 📖 현재 내용 (스크롤 + 드래그 복사)")
    with st.container(height=350, border=True):
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;"
            f"padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>"
            f"{st.session_state.base_prompt_rules}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("##### ✏️ 편집")
    new_val = st.text_area(
        "기본 프롬프트 본문",
        value=st.session_state.base_prompt_rules,
        height=280,
        key="popup_prompt_edit_ta",
        label_visibility="collapsed",
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💾 저장", use_container_width=True, type="primary", key="pr_save"):
            st.session_state.prompt_history.append(st.session_state.base_prompt_rules)
            st.session_state.base_prompt_rules = new_val
            st.toast("✅ 기본 프롬프트 저장", icon="✅")
            st.rerun()
    with c2:
        if st.button(
            f"⬅️ 뒤로 ({len(st.session_state.prompt_history)})",
            use_container_width=True, key="pr_back",
            disabled=len(st.session_state.prompt_history) == 0,
        ):
            st.session_state.base_prompt_rules = st.session_state.prompt_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 기본값", use_container_width=True, key="pr_reset"):
            st.session_state.prompt_history.append(st.session_state.base_prompt_rules)
            st.session_state.base_prompt_rules = DEFAULT_BASE_PROMPT
            st.rerun()
    with c4:
        st.download_button(
            "📥 .txt",
            data=st.session_state.base_prompt_rules,
            file_name=f"base_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            use_container_width=True, key="pr_dl",
        )


# =====================================================================
# Sage Pop-up v2.0 — 파트 인식 + 모델 선택 + 정직 응답 + 옵시디언 자동저장
# =====================================================================

@st.dialog("🤖 세이지 팝업 — Gemma × Tavily × Obsidian RAG", width="large")
def popup_assistant():
    # ── 상태 초기화 ──
    if "popup_selected_model" not in st.session_state:
        st.session_state.popup_selected_model = OLLAMA_MODEL
    if "popup_history" not in st.session_state:
        st.session_state.popup_history = []
    if "popup_search_history" not in st.session_state:
        st.session_state.popup_search_history = []
    if "pending_stream" not in st.session_state:
        st.session_state.pending_stream = None
    if "popup_chat_input_ta" not in st.session_state:
        st.session_state.popup_chat_input_ta = ""

    # ── 파트 인식 ──
    current_part_key = _get_current_part()
    current_part_info = PART_CONTEXT_MAP.get(current_part_key, PART_CONTEXT_MAP["part1"])
    current_part_name = current_part_info["name"]

    # ── 연결 상태 표시 ──
    status = check_ollama_status()
    c_stat1, c_stat2 = st.columns(2)
    with c_stat1:
        sel_model = st.session_state.popup_selected_model
        if status["server"] and status["model"]:
            st.success(f"🟢 연결 정상: {sel_model}")
        else:
            st.error(f"🔴 연결 에러: {sel_model} 미확인")
    with c_stat2:
        if st.session_state.get("tavily_api_key"):
            st.success("🟢 Tavily API (인터넷) 연결 정상")
        else:
            st.warning("🟡 Tavily API Key 미입력 (인터넷 검색 불가)")

    # ── 파트 인식 배지 ──
    st.markdown(
        f"<div style='display:flex;gap:8px;align-items:center;margin:4px 0 8px 0;'>"
        f"<span style='background:#1a3a5c;color:#d4af6a;padding:3px 12px;border-radius:20px;"
        f"font-size:0.82rem;font-weight:700;'>📍 {current_part_name}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── 모델 선택 및 설정 행 ──
    col_model, col_obsidian_btn = st.columns([3, 2])
    with col_model:
        selected_model = st.selectbox(
            "🧠 젬마 모델 선택",
            AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(st.session_state.popup_selected_model)
            if st.session_state.popup_selected_model in AVAILABLE_MODELS else 0,
            key="popup_model_selector",
            label_visibility="collapsed",
        )
        st.session_state.popup_selected_model = selected_model
    with col_obsidian_btn:
        if st.button("💾 대화 기록 옵시디언 저장", use_container_width=True, key="popup_obs_save_btn",
                     disabled=not st.session_state.popup_history):
            saved_path = _auto_save_chat_to_obsidian(
                st.session_state.popup_history,
                current_part_name,
                st.session_state.popup_selected_model
            )
            if saved_path:
                st.toast(f"🧠 옵시디언 저장 완료!", icon="💾")
            else:
                st.error("옵시디언 저장 실패")

    st.divider()

    # ── 탭 구성 ──
    tab_chat, tab_tavily, tab_part_action = st.tabs([
        "💬 Gemma 대화",
        "🌐 Tavily 웹 리서치",
        "⚙️ 파트 작업 지시"
    ])

    # ══════════════════════════════════════════════════════
    # 탭 1: Gemma 대화
    # ══════════════════════════════════════════════════════
    with tab_chat:
        # 대화 기록 컨테이너
        st.markdown("##### 💬 대화 기록 (스크롤 / 드래그 복사)")
        chat_container = st.container(height=360, border=True)

        # 질문 입력창
        st.markdown("##### ✏️ 질문 입력")
        user_input = st.text_area(
            "질문 입력",
            key="popup_chat_input_ta",
            placeholder="현자에게 물어보세요... (전송 버튼 클릭)\n\n예: '이 파트의 나레이션을 더 감성적으로 수정해줘' 또는 '빅터 프랭클의 의미치료에 대해 설명해줘'",
            height=120,
            label_visibility="collapsed",
        )

        # 옵션: 인터넷 검색 자동 병행 여부
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            auto_search = st.checkbox(
                "🌐 모를 때 Tavily 자동 검색",
                value=st.session_state.get("popup_auto_search", True),
                key="popup_auto_search_cb"
            )
            st.session_state.popup_auto_search = auto_search
        with col_opt2:
            use_rag = st.checkbox(
                "🧠 옵시디언 RAG 컨텍스트 주입",
                value=st.session_state.get("popup_use_rag", True),
                key="popup_use_rag_cb"
            )
            st.session_state.popup_use_rag = use_rag

        # 버튼 행
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            send_btn = st.button("📤 전송", use_container_width=True, key="popup_send",
                                  type="primary", on_click=_on_popup_send)
        with c2:
            back = st.button(
                f"⬅️ 뒤로 ({len(st.session_state.popup_history) // 2})",
                use_container_width=True, key="popup_back",
                disabled=len(st.session_state.popup_history) < 2,
            )
        with c3:
            clear = st.button("🗑️ 초기화", use_container_width=True, key="popup_clear")
        with c4:
            if st.session_state.popup_history:
                all_chat = "\n\n".join(
                    f"### [{m['role'].upper()}]\n{m['content']}"
                    for m in st.session_state.popup_history
                )
                st.download_button(
                    "📥 .md", data=all_chat,
                    file_name=f"sage_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    use_container_width=True, key="popup_dl",
                )

        if back and len(st.session_state.popup_history) >= 2:
            st.session_state.popup_history = st.session_state.popup_history[:-2]
            st.rerun()
        if clear:
            st.session_state.popup_history = []
            st.session_state.pending_stream = None
            st.rerun()

        # 대화 기록 렌더링
        with chat_container:
            if not st.session_state.popup_history and not st.session_state.get("pending_stream"):
                st.markdown(
                    "<div style='color:#888;padding:20px;text-align:center;'>"
                    "💭 아직 대화가 없습니다.<br>아래에 질문을 입력하고 전송 버튼을 누르세요.<br><br>"
                    "<small style='color:#d4af6a;'>• 마우스로 텍스트를 드래그하여 복사할 수 있습니다<br>"
                    "• 모를 때는 자동으로 인터넷에서 검색합니다<br>"
                    "• 모든 대화는 옵시디언에 자동 저장됩니다</small>"
                    "</div>",
                    unsafe_allow_html=True
                )

            for i, msg in enumerate(st.session_state.popup_history):
                if msg["role"] == "user":
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,#1a3a5c,#0d2440);"
                        f"border-left:3px solid #d4af6a;padding:10px 14px;margin:6px 0;"
                        f"border-radius:0 8px 8px 0;font-size:0.92rem;'>"
                        f"<b style='color:#d4af6a;'>🧑 사용자</b><br>"
                        f"<span style='color:#f5e9d3;white-space:pre-wrap;'>{msg['content']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    model_used = msg.get("model", st.session_state.popup_selected_model)
                    source_info = msg.get("source", "")
                    rendered_content = msg['content'].replace('\n', '  \n')
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,#2d1b00,#1a1000);"
                        f"border-left:3px solid #10B981;padding:10px 14px;margin:6px 0;"
                        f"border-radius:0 8px 8px 0;font-size:0.92rem;'>"
                        f"<b style='color:#10B981;'>🤖 Sage ({model_used})</b>"
                        f"{(' <small style=\"color:#666;\">' + source_info + '</small>') if source_info else ''}"
                        f"<br></div>",
                        unsafe_allow_html=True,
                    )
                    # 실제 마크다운 렌더링 (링크 포함)
                    st.markdown(msg['content'])
                    with st.expander("📋 복사용 텍스트 (드래그 선택)", expanded=False):
                        st.code(msg["content"], language="markdown")

            # 대기 중인 스트리밍 처리
            if st.session_state.get("pending_stream"):
                q_stream = st.session_state.pending_stream
                current_model = st.session_state.popup_selected_model

                # 시스템 컨텍스트 구성
                sys_ctx = SAGE_PERSONA + "\n\n"
                sys_ctx += "[중요 지침: 현자의 거울 시스템 운영 원칙]\n"
                sys_ctx += "1. 모르는 것은 '자료가 부족하여 확실한 답변이 어렵습니다'라고 솔직하게 말하라.\n"
                sys_ctx += "2. 절대로 추측이나 꾸며낸 정보를 사실인 것처럼 답변하지 마라.\n"
                sys_ctx += "3. 모를 때는 '인터넷 검색이 필요합니다 — Tavily 탭에서 검색해 주세요'라고 안내하라.\n"
                sys_ctx += "4. 답변 시 [SOURCE: 출처]를 반드시 명기하라.\n"
                sys_ctx += "5. 마크다운 형식([[링크]], **강조**, ## 제목)을 적극 활용하라.\n\n"
                sys_ctx += "[옵시디언 규칙서]\n" + st.session_state.obsidian_rules + "\n\n"
                sys_ctx += "[현재 파트 컨텍스트]\n" + _build_part_context(current_part_key) + "\n"

                if st.session_state.get("popup_use_rag", True):
                    sys_ctx += "\n" + _build_obsidian_rag_context()

                with st.status("🔮 젬마가 깊은 사유에 빠졌습니다...", expanded=True) as status_widget:
                    st.write(f"모델: {current_model} | 파트: {current_part_name}")

                    full_response = ""
                    ans_placeholder = st.empty()

                    try:
                        for token in call_gemma_stream(q_stream, system=sys_ctx, model=current_model):
                            full_response += token
                            ans_placeholder.markdown(full_response + "▌")
                        ans_placeholder.markdown(full_response)

                        # "모른다" 키워드 감지 → Tavily 자동 검색
                        unsure_keywords = ["자료가 부족", "확실하지 않", "모르겠", "알 수 없", "정보가 없"]
                        if any(kw in full_response for kw in unsure_keywords) and st.session_state.get("popup_auto_search", True):
                            st.write("⚠️ 자료 부족 감지 → Tavily 자동 검색 시작...")
                            if st.session_state.get("tavily_api_key"):
                                try:
                                    search_res = tavily_search(q_stream, st.session_state.tavily_api_key, max_results=3)
                                    if "results" in search_res and search_res["results"]:
                                        tavily_ctx = "\n\n[인터넷 검색 결과 — Tavily]\n"
                                        for r in search_res["results"][:3]:
                                            tavily_ctx += f"- **{r.get('title','')}**: {r.get('content','')[:200]}... [SOURCE: {r.get('url','')}]\n"

                                        followup_prompt = f"""[이전 답변에서 자료 부족을 언급했습니다. 아래 인터넷 검색 결과를 참고하여 보완 답변을 제공하세요.]

[원래 질문]
{q_stream}

[Tavily 검색 결과]
{tavily_ctx}

위 검색 결과를 바탕으로 정확한 정보만 마크다운 형식으로 답변하세요. [SOURCE: URL] 형식으로 출처를 반드시 명기하세요."""

                                        st.write("🌐 검색 결과를 바탕으로 보완 답변 생성 중...")
                                        supplement = call_gemma(followup_prompt, model=current_model)
                                        full_response += f"\n\n---\n### 🌐 인터넷 검색 보완 답변\n{supplement}"
                                        ans_placeholder.markdown(full_response)
                                        st.session_state.popup_search_history.append({"q": q_stream, "res": search_res})
                                except Exception as e:
                                    st.warning(f"Tavily 자동 검색 실패: {e}")
                            else:
                                st.info("💡 Tavily API Key를 설정하면 자동으로 인터넷 검색을 통해 보완 답변을 제공합니다.")

                        status_widget.update(label="✅ 사유 완료", state="complete", expanded=False)

                    except Exception as e:
                        full_response = f"[오류] 젬마 응답 실패: {e}\n→ Ollama 서버가 실행 중인지 확인하세요."
                        ans_placeholder.markdown(full_response)
                        status_widget.update(label="❌ 오류 발생", state="error", expanded=False)

                    # 대화 기록 저장
                    st.session_state.popup_history.append({
                        "role": "assistant",
                        "content": full_response,
                        "model": current_model,
                        "part": current_part_name,
                    })
                    st.session_state.pending_stream = None

                    # 옵시디언 자동 저장 (대화 완료 시)
                    if len(st.session_state.popup_history) >= 2:
                        try:
                            saved_path = _auto_save_chat_to_obsidian(
                                st.session_state.popup_history[-2:],  # 마지막 Q&A만
                                current_part_name,
                                current_model
                            )
                            if saved_path:
                                st.toast("🧠 대화 자동 옵시디언 저장 완료!", icon="💾")
                        except Exception:
                            pass

                    st.rerun()

    # ══════════════════════════════════════════════════════
    # 탭 2: Tavily 웹 리서치
    # ══════════════════════════════════════════════════════
    with tab_tavily:
        st.markdown("##### 🌐 인터넷 리서치 (Tavily)")
        st.caption("모르는 내용을 직접 검색하거나, 젬마와 함께 분석합니다.")

        sq = st.text_area(
            "검색어", key="tavily_q_ta",
            placeholder="예: 빅터 프랭클 의미치료 사례\n예: 쇼펜하우어 의지와 표상으로서의 세계\n예: 4070 세대 유튜브 심리학 채널 트렌드",
            height=100, label_visibility="collapsed",
        )

        # 젬마 분석 옵션
        analyze_with_gemma = st.checkbox(
            "🤖 검색 결과를 젬마로 분석하여 옵시디언 형식으로 정리",
            value=True, key="tavily_gemma_analyze"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            do_search = st.button("🔍 인터넷 검색", key="tavily_search_btn",
                                  use_container_width=True, type="primary")
        with c2:
            sback = st.button(
                f"⬅️ 이전 ({len(st.session_state.popup_search_history)})",
                key="tavily_back", use_container_width=True,
                disabled=len(st.session_state.popup_search_history) == 0,
            )
        with c3:
            sclear = st.button("🗑️ 초기화", key="tavily_clear", use_container_width=True)

        if sback and st.session_state.popup_search_history:
            st.session_state.popup_search_history.pop()
            st.rerun()
        if sclear:
            st.session_state.popup_search_history = []
            st.rerun()

        if do_search and sq.strip():
            if not st.session_state.get("tavily_api_key"):
                st.error("⚠️ Tavily API Key가 없습니다. 사이드바 설정에서 입력해 주세요.")
            else:
                with st.spinner("🌐 Tavily 인터넷 검색 중..."):
                    try:
                        res = tavily_search(sq, st.session_state.tavily_api_key)

                        # 젬마로 분석 후 저장
                        if analyze_with_gemma and res.get("results"):
                            raw_results = "\n".join([
                                f"[{r.get('title','')}] {r.get('content','')[:300]} (URL: {r.get('url','')})"
                                for r in res.get("results", [])[:5]
                            ])
                            analysis_prompt = f"""[지시] 아래 인터넷 검색 결과를 현자의 거울 스튜디오 옵시디언 형식으로 정리하라.

[검색어]
{sq}

[검색 결과 원문]
{raw_results}

[출력 형식]
## 🔎 검색 요약
(핵심 내용 3줄 요약)

## 📖 상세 분석
(내용 분석 및 현자의 거울 주제와의 연관성)

## 💡 활용 방안
(이 정보를 어떤 파트에서 어떻게 활용할 수 있는지)

## 🔗 출처
(URL 목록)

[SOURCE: Tavily 검색 — {datetime.now().strftime('%Y-%m-%d')}]"""
                            gemma_analysis = call_gemma(
                                analysis_prompt,
                                model=st.session_state.popup_selected_model
                            )
                            res["gemma_analysis"] = gemma_analysis

                        st.session_state.popup_search_history.append({"q": sq, "res": res})

                        # 옵시디언 자동 저장
                        if res.get("results"):
                            from pathlib import Path
                            save_dir = Path(r"C:\SageMirror_Production\00_Obsidian\WebResearch")
                            save_dir.mkdir(parents=True, exist_ok=True)
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            save_path = save_dir / f"tavily_{ts}.md"
                            md_content = f"# 🌐 웹 리서치: {sq}\n\n"
                            md_content += f"- 검색 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            md_content += f"- 파트: {current_part_name}\n\n"
                            if res.get("gemma_analysis"):
                                md_content += res["gemma_analysis"] + "\n\n"
                            md_content += "## 📄 원문 결과\n"
                            for r in res.get("results", [])[:5]:
                                md_content += f"### [{r.get('title','')}]({r.get('url','')})\n{r.get('content','')[:500]}\n\n"
                            save_path.write_text(md_content, encoding="utf-8")
                            st.toast("🧠 검색 결과 옵시디언 자동 저장 완료!", icon="🌐")

                        st.rerun()
                    except Exception as e:
                        st.error(f"검색 실패: {e}")

        # 검색 결과 표시
        st.markdown("##### 📊 검색 결과")
        with st.container(height=400, border=True):
            if not st.session_state.popup_search_history:
                st.markdown(
                    "<div style='color:#888;padding:20px;text-align:center;'>"
                    "🔍 아직 검색 기록이 없습니다.<br>위에 검색어를 입력하고 검색 버튼을 누르세요."
                    "</div>",
                    unsafe_allow_html=True
                )
            else:
                latest = st.session_state.popup_search_history[-1]
                st.markdown(f"**🔎 검색어:** `{latest['q']}`")
                res = latest["res"]

                if "error" in res:
                    st.error(res["error"])
                else:
                    # 젬마 분석 결과 먼저 표시
                    if res.get("gemma_analysis"):
                        st.markdown("### 🤖 젬마 분석 결과")
                        st.markdown(res["gemma_analysis"])
                        with st.expander("📋 복사용 텍스트", expanded=False):
                            st.code(res["gemma_analysis"], language="markdown")
                        st.divider()

                    if res.get("answer"):
                        st.info(f"💡 **즉시 답변:** {res['answer']}")
                        st.divider()

                    for idx, r in enumerate(res.get("results", []), 1):
                        st.markdown(f"**{idx}. [{r.get('title','')}]({r.get('url','')})**")
                        st.write(r.get("content", ""))
                        st.caption(f"[SOURCE: {r.get('url','')}]")
                        st.divider()

    # ══════════════════════════════════════════════════════
    # 탭 3: 파트 작업 지시
    # ══════════════════════════════════════════════════════
    with tab_part_action:
        st.markdown(f"##### ⚙️ 현재 파트 직접 작업 지시")
        st.info(
            f"📍 현재 파트: **{current_part_name}**\n\n"
            "젬마에게 파트 데이터를 수정하거나 생성하도록 직접 지시할 수 있습니다.\n"
            "예: '나레이션 대본의 첫 씬을 더 감성적으로 수정해줘' / '기획안에 빅터 프랭클 인용구를 추가해줘'"
        )

        # 현재 파트 데이터 미리보기
        st.markdown("##### 📋 현재 파트 데이터 현황")
        with st.container(height=150, border=True):
            part_ctx = _build_part_context(current_part_key)
            st.code(part_ctx[:800], language="markdown")

        # 작업 지시 입력
        action_instruction = st.text_area(
            "🎯 작업 지시 입력",
            placeholder="예: Part 3-4 나레이션 대본의 첫 번째 씬을 더 따뜻한 톤으로 다시 작성해줘\n예: 총괄 기획안에 시편 23편 구절을 추가해줘\n예: 이미지 대본의 씬 001 한글 묘사를 수정해줘",
            height=120,
            key="part_action_input",
            label_visibility="collapsed",
        )

        apply_to_session = st.checkbox(
            "✅ 젬마 결과를 해당 파트 세션 데이터에 자동 적용",
            value=False,
            key="part_action_apply_cb"
        )

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            run_action = st.button("🚀 작업 실행 (AI)", type="primary",
                                    use_container_width=True, key="part_action_run_btn")
        with col_act2:
            if st.button("📋 현재 파트 데이터 전체 보기", use_container_width=True, key="part_action_view_btn"):
                st.session_state.popup_show_full_context = not st.session_state.get("popup_show_full_context", False)

        if st.session_state.get("popup_show_full_context"):
            with st.container(height=300, border=True):
                st.code(_build_part_context(current_part_key), language="markdown")

        if run_action and action_instruction.strip():
            current_model = st.session_state.popup_selected_model

            sys_ctx = SAGE_PERSONA + "\n\n"
            sys_ctx += "[중요 지침]\n"
            sys_ctx += "1. 사용자가 지시한 작업을 정확하게 수행하라.\n"
            sys_ctx += "2. 모르는 것은 솔직하게 말하고 추측하지 마라.\n"
            sys_ctx += "3. 결과물은 즉시 사용 가능한 완성 형태로만 출력하라.\n"
            sys_ctx += "4. 마크다운 형식([[링크]], **강조**, ## 제목)을 적극 활용하라.\n\n"
            sys_ctx += "[현재 파트 컨텍스트]\n" + _build_part_context(current_part_key)
            sys_ctx += "\n[옵시디언 규칙서]\n" + st.session_state.obsidian_rules

            action_prompt = f"""[파트 작업 지시]
파트: {current_part_name}

[지시 내용]
{action_instruction}

위 지시를 정확히 수행하여 완성된 결과물만 출력하라. 설명, 서론, 결론 불필요."""

            with st.spinner(f"🔮 {current_model}이 작업 중..."):
                try:
                    action_result = call_gemma(action_prompt, system=sys_ctx, model=current_model)

                    st.markdown("##### 🎯 작업 결과")
                    st.markdown(action_result)

                    with st.expander("📋 복사용 텍스트", expanded=False):
                        st.code(action_result, language="markdown")

                    # 세션 데이터 자동 적용
                    if apply_to_session:
                        apply_msg = _apply_part_action(current_part_key, action_instruction, action_result)
                        if apply_msg:
                            st.success(apply_msg)
                        else:
                            st.info("💡 자동 적용 조건이 맞지 않습니다. 위 결과를 직접 복사하여 해당 파트에 붙여넣으세요.")

                    # 대화 기록에도 추가
                    st.session_state.popup_history.append({"role": "user", "content": f"[파트 작업 지시] {action_instruction}"})
                    st.session_state.popup_history.append({
                        "role": "assistant",
                        "content": action_result,
                        "model": current_model,
                        "part": current_part_name,
                        "source": f"파트 작업 지시 — {current_part_name}"
                    })

                    # 옵시디언 자동 저장
                    _auto_save_chat_to_obsidian(
                        st.session_state.popup_history[-2:],
                        current_part_name,
                        current_model
                    )
                    st.toast("🧠 작업 결과 옵시디언 자동 저장 완료!", icon="💾")

                except Exception as e:
                    st.error(f"[오류] 작업 실패: {e}\n→ Ollama 서버가 실행 중인지 확인하세요.")
