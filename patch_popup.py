# -*- coding: utf-8 -*-
"""
popup_assistant 함수 교체 패치 스크립트
UTF-8 인코딩을 유지하면서 함수 전체를 안전하게 교체
"""
import re

INPUT_FILE = "sage_popups_v17_1_13.py"
OUTPUT_FILE = "sage_popups_v17_1_13.py"

# 교체할 새 함수 전체 코드
NEW_FUNC = '''
@st.dialog("🤖 세이지 — Sage Mirror 어시스턴트", width="large")
def popup_assistant():
    """클로드 스타일 심플 채팅 UI"""

    # ── 세션 초기화 ──────────────────────────────────────────
    _defaults = {
        "popup_selected_model": OLLAMA_MODEL,
        "popup_history": [],
        "popup_gemma_mode": "A",
        "popup_search_history": [],
        "tavily_rag_context": "",
    }
    for _k, _v in _defaults.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v

    # ── 대화 영속성 복원 ──────────────────────────────────────
    if not st.session_state.popup_history:
        _loaded = _load_chat_history()
        if _loaded:
            st.session_state.popup_history = _loaded

    current_part_key = _get_current_part()
    current_part_info = PART_CONTEXT_MAP.get(current_part_key, PART_CONTEXT_MAP["part1"])
    current_part_name = current_part_info["name"]
    status_obj = check_ollama_status()

    # ── 2열 레이아웃: 좌측 바 + 대화창 ──────────────────────
    col_left, col_chat = st.columns([1, 3], gap="medium")

    # ══════════════════════════════
    # 좌측 바
    # ══════════════════════════════
    with col_left:
        # 연결 상태
        if status_obj.get("server") and status_obj.get("model"):
            st.success(f"🟢 {st.session_state.popup_selected_model}", icon=None)
        else:
            st.error("🔴 연결 오류")

        if st.session_state.get("tavily_api_key"):
            st.success("🟢 Tavily", icon=None)
        else:
            st.warning("🟡 Tavily 미연결")

        st.divider()

        # 파트 표시
        st.markdown(
            f"<div style=\'background:#1a3a5c;color:#d4af6a;padding:6px 10px;"
            f"border-radius:8px;font-size:0.8rem;font-weight:700;text-align:center;\'>"
            f"📍 {current_part_name}</div>",
            unsafe_allow_html=True,
        )

        st.divider()

        # 기능 버튼들
        if st.button("💾 대화 저장", use_container_width=True, key="sb_obs_save"):
            if st.session_state.popup_history:
                _save_to_obsidian_with_tags(
                    content="\\n".join([
                        f"[{m[\'role\'].upper()}] {m[\'content\']}"
                        for m in st.session_state.popup_history
                    ]),
                    title=f"[Chat] {current_part_name}",
                    source_type="Sage 팝업 대화",
                    part_key=current_part_key,
                    model_name=st.session_state.popup_selected_model,
                )
                st.toast("💾 옵시디언 저장 완료!", icon="💾")

        if st.button("🔎 자료 조사", use_container_width=True, key="sb_research"):
            st.session_state["sidebar_tab"] = "research"

        if st.button("📂 파일 업로드", use_container_width=True, key="sb_upload"):
            st.session_state["sidebar_tab"] = "upload"

        if st.button("🧠 옵시디언", use_container_width=True, key="sb_obsidian"):
            st.session_state["sidebar_tab"] = "obsidian"

        st.divider()

        # 사이드 탭 영역
        _sidebar_tab = st.session_state.get("sidebar_tab", "")

        if _sidebar_tab == "research":
            st.markdown("**🔎 자료 조사**")
            _query = st.text_input("검색어", key="sb_search_query")
            if st.button("검색", key="sb_search_btn") and _query:
                with st.spinner("검색 중..."):
                    _tav_key = st.session_state.get("tavily_api_key", "")
                    _result = tavily_search(_query, _tav_key)
                    if "results" in _result:
                        _ctx = "\\n".join([
                            f"- {r.get(\'title\',\'\')}: {r.get(\'content\',\'\')[:200]}"
                            for r in _result["results"][:3]
                        ])
                        st.session_state.tavily_rag_context = _ctx
                        st.session_state.popup_search_history.append({
                            "query": _query, "context": _ctx
                        })
                        st.success("✅ 자료 수집 완료")
                        st.markdown(_ctx[:500])

        elif _sidebar_tab == "upload":
            st.markdown("**📂 파일 업로드**")
            _uploaded = st.file_uploader(
                "파일 선택",
                type=["txt", "md", "pdf", "docx"],
                key="sb_file_uploader"
            )
            if _uploaded:
                st.caption(f"선택됨: {_uploaded.name}")
                if st.button("분석 및 저장", key="sb_analyze_btn"):
                    with st.spinner("분석 중..."):
                        _text, _ = _read_uploaded_file_text(_uploaded)
                        if _text:
                            _saved = _save_to_obsidian_with_tags(
                                content=_text[:5000],
                                title=f"[업로드] {_uploaded.name}",
                                source_type=f"파일 업로드 — {_uploaded.name}",
                                part_key=current_part_key,
                                model_name=st.session_state.popup_selected_model,
                            )
                            if _saved:
                                st.success("✅ 옵시디언 저장 완료")

        elif _sidebar_tab == "obsidian":
            st.markdown("**🧠 최근 저장 자료**")
            _vault = st.session_state.get("path_obsidian", "")
            if _vault:
                try:
                    from pathlib import Path as _Path
                    _recent = sorted(
                        _Path(_vault).rglob("*.md"),
                        key=lambda f: f.stat().st_mtime,
                        reverse=True
                    )[:5]
                    for _f in _recent:
                        st.caption(f"📄 {_f.name}")
                except Exception:
                    st.caption("자료 없음")
            else:
                st.caption("옵시디언 경로 미설정")

    # ══════════════════════════════
    # 대화창 (우측)
    # ══════════════════════════════
    with col_chat:

        # 대화 기록 표시
        _chat_box = st.container(height=420)
        with _chat_box:
            if not st.session_state.popup_history:
                st.markdown(
                    "<div style=\'color:#666;text-align:center;margin-top:80px;"
                    "font-size:0.9rem;\'>현자에게 무엇이든 물어보세요 🤖</div>",
                    unsafe_allow_html=True,
                )
            for _msg in st.session_state.popup_history:
                with st.chat_message(_msg["role"]):
                    st.markdown(_msg["content"])

        # 모델 선택 (입력창 위 우측)
        _mcol1, _mcol2 = st.columns([3, 1])
        with _mcol2:
            _sel_model = st.selectbox(
                "모델",
                AVAILABLE_MODELS,
                index=AVAILABLE_MODELS.index(st.session_state.popup_selected_model)
                if st.session_state.popup_selected_model in AVAILABLE_MODELS else 0,
                key="popup_model_sel_new",
                label_visibility="collapsed",
            )
            st.session_state.popup_selected_model = _sel_model

        # 입력창 (클로드 스타일)
        _prompt = st.chat_input(
            "현자에게 물어보세요...",
            key="popup_chat_input_new"
        )

        # 젬마 응답 처리
        if _prompt:
            st.session_state.popup_history.append({
                "role": "user",
                "content": _prompt,
                "model": _sel_model,
                "part": current_part_name,
            })

            with _chat_box:
                with st.chat_message("user"):
                    st.markdown(_prompt)

                with st.chat_message("assistant"):
                    # 점 3개 → 스트리밍 응답
                    _sys = "너는 현자의 거울 스튜디오의 어시스턴트다. 묻는 말에 정확하고 짧게 답하라."
                    # Tavily 자료가 있으면 추가
                    if st.session_state.get("tavily_rag_context"):
                        _sys += f"\\n\\n[참조 자료]\\n{st.session_state.tavily_rag_context[:1000]}"
                    with st.spinner("● ● ●"):
                        import time as _time
                        _t0 = _time.perf_counter()
                        _response = st.write_stream(
                            _stream_gemma_a_mode(_prompt, system=_sys, model=_sel_model)
                        )
                        _elapsed = _time.perf_counter() - _t0
                    st.caption(f"⏱️ {_elapsed:.1f}초")

            st.session_state.popup_history.append({
                "role": "assistant",
                "content": _response,
                "model": _sel_model,
                "part": current_part_name,
            })
            _save_chat_history(st.session_state.popup_history)
'''

# 파일 읽기 (UTF-8)
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    content = f.read()

print(f"원본 파일 크기: {len(content)} bytes")

# popup_assistant 함수 시작 위치 탐색
# @st.dialog 데코레이터부터 함수 끝까지 찾기
start_marker = '@st.dialog("🤖 세이지 팝업 — Gemma × Tavily × Obsidian RAG", width="large")\ndef popup_assistant():'

start_idx = content.find(start_marker)
if start_idx == -1:
    print("ERROR: popup_assistant 시작 마커를 찾지 못했습니다!")
    exit(1)

print(f"함수 시작 위치: {start_idx} (라인 ~{content[:start_idx].count(chr(10))+1})")

# 함수 끝 찾기: 다음 최상위 함수/클래스 정의 또는 파일 끝
# popup_assistant 이후에 최상위 def/class가 나오면 거기서 끊음
rest = content[start_idx:]

# 다음 상위 레벨 함수 시작을 찾음 (줄 시작에 def 또는 class)
# popup_assistant 함수 자체의 def 라인 다음부터 탐색
lines_after_start = rest.split('\n')
func_end_line = len(lines_after_start)  # 기본값: 파일 끝

in_func = False
for i, line in enumerate(lines_after_start):
    if i == 0:
        # @st.dialog 데코레이터 라인
        continue
    if i == 1:
        # def popup_assistant(): 라인
        in_func = True
        continue
    if in_func and i > 2:
        # 최상위 레벨 def/class 발견 시 종료
        if (line.startswith('def ') or line.startswith('class ') or
            line.startswith('@') and not line.startswith('    ')):
            func_end_line = i
            print(f"다음 최상위 정의 발견 (라인 {i}): {line[:60]}")
            break

end_idx = start_idx + len('\n'.join(lines_after_start[:func_end_line]))

print(f"함수 끝 위치: {end_idx}")
print(f"교체할 코드 크기: {end_idx - start_idx} bytes")

# 함수 교체
new_content = content[:start_idx] + NEW_FUNC.strip() + '\n' + content[end_idx:]

print(f"새 파일 크기: {len(new_content)} bytes")

# UTF-8로 저장
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"✅ 파일 저장 완료: {OUTPUT_FILE}")
print(f"총 라인 수: {new_content.count(chr(10))+1}")
