# -*- coding: utf-8 -*-
"""
panel/right_panel.py — v5 비스트리밍 안정 버전

핵심 변경:
- stream=True → stream=False (Thinking 모드 무한 대기 방지)
- 명시적 진행 표시 (사용자가 응답 진행 상황 인지)
- timeout 명확히 작동
"""

import streamlit as st
import requests
from datetime import datetime

from core.config import MODELS, DEFAULT_MODEL, PART_NAMES
from core.state import get_state, set_state
from core.auto_save import schedule_chat_save


def _build_brain_prompt() -> str:
    """채널 Profile 기반 동적 시스템 프롬프트 생성"""
    try:
        from core.profile_loader import load_current_profile
        p = load_current_profile()
    except Exception:
        p = {}

    ch_name    = p.get("channel_name", "이 채널")
    target     = p.get("target_audience", "일반 시청자")
    tone       = p.get("tone", "")
    style      = p.get("narrator_style", "")
    philosophy = " / ".join(p.get("philosophy_anchor", []))
    forbidden  = ", ".join(p.get("forbidden_expressions", []))
    preferred  = ", ".join(p.get("preferred_expressions", []))

    lines = [
        f"너는 {ch_name} 스튜디오의 AI 공장장이다.",
        "",
        "[채널 정체성]",
        f"- 채널명: {ch_name}",
        f"- 타겟: {target}",
    ]
    if tone:
        lines.append(f"- 톤: {tone}")
    if style:
        lines.append(f"- 스타일: {style}")
    if philosophy:
        lines.append(f"- 지식 체계: {philosophy}")
    lines += [
        "",
        "[CRITICAL]",
        "- 한국어로만 답변",
        "- 즉시 본론, 부연 설명 없음",
        '- "Thinking", "Process" 단어 사용 금지',
        "",
        f"[역할] {ch_name} 채널 크리에이터의 AI 비서",
        "[금지] AI 냄새 표현, 추측 인용, 영어 답변",
    ]
    if forbidden:
        lines.append(f"[채널 금지 표현] {forbidden}")
    if preferred:
        lines.append(f"[채널 선호 표현] {preferred}")
    return "\n".join(lines)


BRAIN_SYSTEM_PROMPT = ""  # 하위 호환 유지 (동적 빌더 우선)


def _get_default_drive_folder() -> str:
    """Profile의 obsidian_channel_dir 기반 Drive 폴더명"""
    try:
        from core.profile_loader import load_current_profile
        p = load_current_profile()
        return p.get("obsidian_channel_dir", "채널_자료").replace("채널_", "") + "_자료"
    except Exception:
        return "채널_자료"


def call_gemini_with_messages(messages: list, model_key: str, _retry: int = 2) -> str:
    """Gemini API 멀티턴 호출 — 30초 타임아웃 + 503/429 재시도 + Ollama 폴백"""
    import time
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutTimeout

    try:
        from google import genai as _genai
        api_key = st.session_state.get("api_gemini", "")
        if not api_key:
            return "⚠️ Gemini API 키가 없습니다. 우측 설정에서 키를 입력하세요."

        # AQ. / AIza 모두 api_key로 직접 전달 (구 SDK 방식과 동일)
        client = _genai.Client(api_key=api_key)
        system_txt = ""
        gemini_contents = []
        for m in messages:
            if m["role"] == "system":
                system_txt = m["content"]
            elif m["role"] == "user":
                gemini_contents.append(
                    _genai.types.Content(
                        role="user",
                        parts=[_genai.types.Part(text=m["content"])]
                    )
                )
            elif m["role"] == "assistant":
                gemini_contents.append(
                    _genai.types.Content(
                        role="model",
                        parts=[_genai.types.Part(text=m["content"])]
                    )
                )

        cfg_obj = _genai.types.GenerateContentConfig(
            system_instruction=system_txt,
            max_output_tokens=8192,
            temperature=0.7,
        )

        def _do_call():
            return client.models.generate_content(
                model=model_key,
                contents=gemini_contents,
                config=cfg_obj,
            )

        # ── 30초 하드 타임아웃 (SDK 기본 120초 대기 차단) ──
        with ThreadPoolExecutor(max_workers=1) as _ex:
            _fut = _ex.submit(_do_call)
            try:
                resp = _fut.result(timeout=30)
                return resp.text or "응답 없음"
            except _FutTimeout:
                raise Exception("Gemini 30초 시간 초과")

    except Exception as e:
        err_str = str(e)

        # 503 / 429 → 재시도 (최대 2회, 5·10초 대기)
        if _retry > 0 and any(k in err_str for k in ("503", "429", "UNAVAILABLE", "Resource")):
            time.sleep((3 - _retry) * 5)
            return call_gemini_with_messages(messages, model_key, _retry - 1)

        # ── Gemini 오류 로깅 ─────────────────────────────
        gemini_err_short = err_str[:200]

        # ── Ollama 폴백 ──────────────────────────────────
        user_content   = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        system_content = next((m["content"] for m in messages if m["role"] == "system"), "")

        # 시스템프롬프트 + 사용자 메시지 트림 (Ollama 부하 최소화)
        OLLAMA_SYS_LIMIT = 1500
        OLLAMA_USR_LIMIT = 4000
        system_trimmed = (system_content[:OLLAMA_SYS_LIMIT] + "\n...(이하 생략)") if len(system_content) > OLLAMA_SYS_LIMIT else system_content
        user_trimmed   = (user_content[:OLLAMA_USR_LIMIT]   + "\n...(이하 생략)") if len(user_content)   > OLLAMA_USR_LIMIT else user_content

        _, fallback, _ = call_ollama_sync(user_trimmed, system_trimmed, timeout=300)

        # 오류 패턴: "초 시간 초과", "오류", "연결 실패", "빈 응답" 등은 실패로 간주
        _err_tokens = ("시간 초과", "연결 실패", "빈 응답", "HTTP ", "오류:", "Ollama")
        _is_fallback_err = not fallback or any(t in fallback for t in _err_tokens)

        if not _is_fallback_err:
            return f"⚠️ Gemini 오류: `{gemini_err_short}`\n\n[Gemma 대체]\n{fallback}"

        # 둘 다 실패 → Gemini 실제 오류 + 안내 반환
        return (
            f"⚠️ **Gemini 오류**: `{gemini_err_short}`\n\n"
            f"⚠️ **Gemma 오류**: `{fallback[:100]}`\n\n"
            "**해결 방법:**\n"
            "1. Gemini API 키 만료 여부 확인 (AI Studio에서 재발급)\n"
            "2. Ollama 서버 실행 상태 확인\n"
            "3. 잠시 후 재시도"
        )


def call_ollama_sync(prompt: str, system: str = "", model: str = None,
                     timeout: int = 120) -> tuple:
    """Ollama 동기 호출 (비스트리밍) — Thinking 후처리 / Gemini 자동 라우팅"""
    import time
    import re

    current_model = get_state("current_model", DEFAULT_MODEL)
    model = model or current_model

    # ── Gemini 라우팅 ────────────────────────────────
    if "gemini" in model.lower():
        start = time.time()
        try:
            from core.brain import call_gemini
            response = call_gemini(prompt=prompt, system=system, model=model)
            elapsed = time.time() - start
            if not response or response.startswith("[Gemini"):
                return False, response or "(빈 응답)", elapsed
            return True, response, elapsed
        except Exception as e:
            return False, f"(Gemini 오류: {e})", time.time() - start

    # ── Ollama 호출 ──────────────────────────────────
    full = (system.strip() + "\n\n" + prompt) if system.strip() else prompt

    payload = {
        "model": model,
        "prompt": full,
        "stream": False,
        "keep_alive": "30m",
        "think": False,
        "options": {
            "num_predict": 2000,
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
        },
    }

    start = time.time()

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=timeout,
        )
        elapsed = time.time() - start

        if resp.status_code != 200:
            return False, f"오류: HTTP {resp.status_code}", elapsed

        data = resp.json()
        response_text = data.get("response", "")

        if not response_text:
            return False, "(빈 응답 — 모델 재시도 권장)", elapsed

        # ── Thinking 부분 후처리 ────────────────────
        cleaned = clean_thinking_response(response_text)

        if not cleaned.strip():
            return False, "(Thinking 후 빈 응답 — 다시 시도해주세요)", elapsed

        return True, cleaned, elapsed

    except requests.Timeout:
        elapsed = time.time() - start
        return False, f"({timeout}초 시간 초과)", elapsed
    except requests.ConnectionError:
        return False, "(Ollama 서버 연결 실패)", 0
    except Exception as e:
        return False, f"(오류: {e})", 0


def clean_thinking_response(text: str) -> str:
    """Thinking 부분 제거 후 실제 답변만 추출"""
    import re
    
    # 패턴 1: "...done thinking." 이후만 추출
    if "...done thinking." in text:
        parts = text.split("...done thinking.")
        if len(parts) > 1:
            return parts[-1].strip()
    
    # 패턴 2: "</think>" 태그 이후
    if "</think>" in text:
        parts = text.split("</think>")
        if len(parts) > 1:
            return parts[-1].strip()
    
    # 패턴 3: "Thinking Process:" 블록 제거
    text = re.sub(
        r'Thinking(?:\s*Process)?:.*?(?=\n\n)',
        '',
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    
    # 패턴 4: 줄 단위로 "1.", "2." 형식의 thinking 단계 제거
    lines = text.split('\n')
    filtered = []
    in_thinking = False
    
    for line in lines:
        stripped = line.strip()
        if re.match(r'^Thinking', stripped, re.IGNORECASE):
            in_thinking = True
            continue
        if in_thinking and re.match(r'^\d+\.\s+\*\*', stripped):
            continue
        if in_thinking and stripped.startswith('*'):
            continue
        if in_thinking and stripped == '':
            in_thinking = False
            continue
        if not in_thinking:
            filtered.append(line)
    
    result = '\n'.join(filtered).strip()
    return result if result else text.strip()


def render_right_panel():
    """우측 브레인 패널"""
    
    current_part = get_state("current_part", 1)
    part_name = PART_NAMES.get(current_part, "?")
    
    st.markdown("### 🧙 SAGE 브레인")

    # ── Task 24: 시작 버튼 ─────────────────────────────────────────
    try:
        from core.profile_loader import load_current_profile
        _cur_profile = load_current_profile()
        _cur_ch_name = _cur_profile.get("channel_name", "채널")
    except Exception:
        _cur_ch_name = "채널"

    _start_col, _edit_col = st.columns([4, 1])
    with _start_col:
        if st.button(
            f"🚀 시작 — {_cur_ch_name}",
            key="rp_start_btn",
            use_container_width=True,
            type="primary",
            help="현재 채널로 자동 시작 (채널검색 + 댓글분석 + 주제발굴)",
        ):
            _start_response = start_channel_workflow()
            _hist = get_state("rp_history", [])
            _hist.append({"role": "user", "content": "시작",
                          "timestamp": datetime.now().isoformat()})
            _hist.append({"role": "assistant", "content": _start_response,
                          "timestamp": datetime.now().isoformat()})
            set_state("rp_history", _hist)
            set_state("rp_input_counter", get_state("rp_input_counter", 0) + 1)
            st.rerun()
    with _edit_col:
        _md_edit_on = get_state("rp_md_editor_open", False)
        if st.button("✏️", key="rp_md_edit_btn", help="프롬프트 MD 편집",
                     use_container_width=True):
            set_state("rp_md_editor_open", not _md_edit_on)
            st.rerun()

    # MD 편집기 패널
    if get_state("rp_md_editor_open", False):
        with st.container(border=True):
            render_md_editor()

    st.caption(f"📍 Part {current_part} - {part_name}")

    # 자동 모니터링 상태
    from core.auto_monitor import get_all_status, has_alerts, get_alert_summary
    status = get_all_status()
    
    c1, c2, c3 = st.columns(3)
    c1.caption(f"{status['rag']['color']} RAG ({status['rag']['files']})")
    c2.caption(f"{status['cite']['color']} 인용")
    c3.caption(f"{status['smell']['color']} AI냄새")
    
    if has_alerts():
        alerts = get_alert_summary()
        with st.expander(f"⚠️ 알림 {len(alerts)}건", expanded=False):
            for alert in alerts:
                st.warning(f"**{alert['type']}**: {alert['message']}")
    
    render_chat_with_response()

    # + 팝업 (입력창 바로 위, 2×3 그리드)
    if get_state("rp_plus_open", False):
        with st.container(border=True):
            st.caption("📎 추가 도구")
            r1c1, r1c2, r1c3 = st.columns(3)
            r2c1, r2c2, r2c3 = st.columns(3)
            for _col, _label, _key in [
                (r1c1, "🔍 Tavily\n웹검색",      "tavily"),
                (r1c2, "🧠 Gemini\nDeep",         "gemini_deep"),
                (r1c3, "📂 파일\n탐색기",          "file_explorer"),
                (r2c1, "☁️ 구글\n드라이브",        "gdrive"),
                (r2c2, "🎬 YouTube\n영상분석",      "youtube_analyze"),
                (r2c3, "✏️ 직접\n추가",            "manual"),
            ]:
                with _col:
                    if st.button(_label, key=f"rp_tool_{_key}", use_container_width=True):
                        set_state("rp_active_tool", _key)
                        set_state("rp_plus_open", False)
                        st.rerun()

    # ── 파일 탐색기 / 구글 드라이브 도구 UI ──────────
    _active_now = get_state("rp_active_tool", "")

    if _active_now == "file_explorer":
        with st.container(border=True):
            st.caption("📂 파일 업로드 → Gemma 분석 → 옵시디언 3중 저장")
            _uploaded = st.file_uploader(
                "파일 선택",
                type=["md", "txt", "pdf", "docx", "csv"],
                key=f"rp_file_up_{get_state('rp_file_counter', 0)}",
                label_visibility="collapsed",
            )
            _fc1, _fc2 = st.columns(2)
            if _fc1.button("❌ 취소", key="rp_file_cancel", use_container_width=True):
                set_state("rp_active_tool", "")
                st.rerun()
            if _uploaded and _fc2.button("⚡ 분석 시작", key="rp_file_go", use_container_width=True):
                with st.spinner("Gemma 분석 중..."):
                    try:
                        from core.file_processor import extract_text, process_and_save
                        _raw_bytes = _uploaded.read()
                        _content = extract_text(_raw_bytes, _uploaded.name)
                        _part = get_state("current_part")
                        _res = process_and_save(_content, _uploaded.name, _part, "file_upload")
                        _ana = _res["analysis"]
                        _msg = (
                            f"📂 **파일 분석 완료**: `{_uploaded.name}`\n\n"
                            f"**요약**: {_ana['summary']}\n\n"
                            f"**카테고리**: {_ana['category']}  |  "
                            f"**채널 관련성**: {_ana['channel_relevance']:.0%}\n"
                            f"**키워드**: {', '.join(_ana['keywords'])}\n\n"
                            f"✅ 옵시디언 저장 완료 (Raw + Wiki + Schema)"
                        )
                        _hist = get_state("rp_history", [])
                        _hist.append({"role": "assistant", "content": _msg,
                                      "timestamp": datetime.now().isoformat()})
                        set_state("rp_history", _hist)
                        set_state("rp_file_counter", get_state("rp_file_counter", 0) + 1)
                        set_state("rp_active_tool", "")
                        st.rerun()
                    except Exception as _e:
                        st.error(f"분석 오류: {_e}")

    elif _active_now == "gdrive":
        with st.container(border=True):
            st.caption("☁️ Google Drive → Gemma 분석 → 옵시디언 저장")
            _gfolder = st.text_input(
                "Drive 폴더명",
                value=_get_default_drive_folder(),
                key="rp_gdrive_folder", label_visibility="collapsed",
                placeholder="Google Drive 폴더명 입력",
            )
            _gc1, _gc2 = st.columns(2)
            if _gc1.button("❌ 취소", key="rp_gdrive_cancel", use_container_width=True):
                set_state("rp_active_tool", "")
                st.rerun()
            if _gc2.button("🔄 동기화 시작", key="rp_gdrive_sync", use_container_width=True):
                with st.spinner("Drive 동기화 중..."):
                    try:
                        from core.gdrive_sync import sync_drive_folder
                        _gres = sync_drive_folder(_gfolder.strip() or _get_default_drive_folder())
                        if _gres.get("success"):
                            _n = _gres.get("new_files", 0)
                            _gmsg = (
                                f"☁️ **Drive 동기화 완료**\n\n"
                                f"폴더: `{_gfolder}`\n"
                                f"새 파일: {_n}건\n"
                                + ("✅ 옵시디언 저장 완료" if _n > 0 else "ℹ️ 새 파일 없음")
                            )
                        else:
                            _gmsg = f"⚠️ Drive 오류: {_gres.get('error', '알 수 없음')}"
                        _ghist = get_state("rp_history", [])
                        _ghist.append({"role": "assistant", "content": _gmsg,
                                       "timestamp": datetime.now().isoformat()})
                        set_state("rp_history", _ghist)
                        set_state("rp_active_tool", "")
                        st.rerun()
                    except ImportError as _ie:
                        st.error(f"Drive 라이브러리 미설치: {_ie}")
                    except Exception as _ge:
                        st.error(f"Drive 오류: {_ge}")

    # ── 입력 한 줄: [+] [입력창] [모델▼] [▶] (st.form 제거 — 패스워드 팝업 방지)
    _ic = get_state("rp_input_counter", 0)
    models_list = list(MODELS.keys())
    cur_model   = get_state("rp_model", DEFAULT_MODEL)

    c_plus, c_input, c_model, c_send = st.columns([1, 6, 3, 1])

    with c_plus:
        if st.button("➕", key="rp_plus_btn", use_container_width=True, help="추가 도구"):
            set_state("rp_plus_open", not get_state("rp_plus_open", False))

    with c_input:
        user_input = st.text_input(
            "입력",
            placeholder="메시지를 입력하세요...",
            key=f"rp_text_input_{_ic}",
            label_visibility="collapsed",
        )

    with c_model:
        sel = st.selectbox(
            "모델",
            models_list,
            index=models_list.index(cur_model) if cur_model in models_list else 0,
            format_func=lambda x: MODELS[x]["label"],
            key=f"rp_model_sel_{_ic}",
            label_visibility="collapsed",
        )
        if sel != cur_model:
            set_state("rp_model", sel)
            set_state("current_model", sel)

    with c_send:
        send_btn = st.button("▶", key=f"rp_send_{_ic}", use_container_width=True)

    if send_btn and user_input.strip():
        history = get_state("rp_history", [])
        history.append({
            "role": "user",
            "content": user_input.strip(),
            "timestamp": datetime.now().isoformat(),
        })
        set_state("rp_history", history)
        set_state("rp_input_counter", _ic + 1)
        st.rerun()


def _extract_yt_urls(text: str) -> list:
    """응답 텍스트에서 YouTube 채널 URL 중복 없이 추출 (@ / channel / c 형식 모두)"""
    import re
    urls = re.findall(
        r'https?://(?:www\.)?youtube\.com/(?:channel/[A-Za-z0-9_\-]+|@[A-Za-z0-9_.\-]+|c/[A-Za-z0-9_.\-]+)',
        text
    )
    return list(dict.fromkeys(url.rstrip('/.,)') for url in urls))


def render_chat_with_response():
    """대화 표시 + 응답 생성 (모두 컨테이너 안)"""
    st.markdown("""
<style>
/* ── 우측 컬럼 sticky 고정 ──────────────────────────── */
div[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }
div[data-testid="stHorizontalBlock"]
> div[data-testid="column"]:last-child {
    position: sticky !important;
    top: 3.75rem !important;
    max-height: calc(100vh - 3.75rem) !important;
    overflow-y: auto !important;
    padding-bottom: 1rem;
}
/* ── 대화창 높이 calc 적용 ──────────────────────────── */
div[data-testid="stVerticalBlockBorderWrapper"]
> div[style*="height"] {
    height: calc(100vh - 280px) !important;
    min-height: 300px !important;
    overflow-y: auto !important;
}
</style>""", unsafe_allow_html=True)
    history = get_state("rp_history", [])

    box = st.container(height=580, border=True)

    with box:
        if not history:
            set_state("rp_last_channel_urls", [])  # 잔류 URL 클리어
            st.markdown(
                "<div style='color:#888; text-align:center; padding:50px 20px;'>"
                "💬 SAGE 브레인과 대화를 시작하세요"
                "</div>",
                unsafe_allow_html=True
            )
            return

        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if history[-1]["role"] == "user":
            user_msg = history[-1]["content"]
            model_key = get_state("rp_model", DEFAULT_MODEL)
            with st.chat_message("assistant"):
                with st.status("⬡ 생각 중...", expanded=True) as status_box:
                    st.write("📡 모델 호출 중...")
                    response = generate_response_sync(user_msg, history[:-1], model_key)
                    status_box.update(label="✅ 완료", state="complete")
                st.markdown(response)
                auto_url = get_state("p1_bench_auto_selected", "")
                if auto_url:
                    st.success(f"✅ 벤치마킹 탭에 자동 입력됨: {auto_url}")
                    set_state("p1_bench_auto_selected", "")
            history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "model": model_key,
            })
            set_state("rp_history", history)
            # 응답에서 채널 URL 추출 → 버튼용 저장
            extracted = _extract_yt_urls(response)
            if extracted:
                set_state("rp_last_channel_urls", extracted)

    # ── 자동 스크롤 다운 (iframe JS) ─────────────────────
    import streamlit.components.v1 as _stc
    _stc.html(
        """<script>
(function(){
    function s(){
        var doc=window.parent.document;
        var bs=doc.querySelectorAll(
            'div[data-testid="stVerticalBlockBorderWrapper"]>div[style*="height"]');
        if(bs.length>0){var b=bs[bs.length-1];b.scrollTop=b.scrollHeight;}
    }
    setTimeout(s,300); setTimeout(s,900);
})();
</script>""",
        height=0,
    )

    # ── 채팅 컨테이너 밖: 채널 벤치마킹 바로 적용 버튼 ────────────
    last_urls = get_state("rp_last_channel_urls", [])
    if not last_urls and history and history[-1]["role"] == "assistant":
        last_urls = _extract_yt_urls(history[-1]["content"])
        if last_urls:
            set_state("rp_last_channel_urls", last_urls)

    if last_urls:
        st.markdown("#### 📺 발굴 채널 적용")
        st.caption("🔗 = 유튜브 열기 (새 탭)  |  📤 = 벤치마킹 탭에 적용")
        for idx, url in enumerate(last_urls[:8]):
            name = url.rstrip('/').split('/')[-1][:32]
            col1, col2 = st.columns([3, 2])
            with col1:
                st.link_button(f"🔗 {name}", url, use_container_width=True)
            with col2:
                if st.button("📤 벤치마킹", key=f"rp_bench_{idx}", use_container_width=True):
                    new_counter = get_state("p1_url_counter", 0) + 1
                    set_state("p1_url_counter", new_counter)
                    set_state("p1_channel_url", url)
                    set_state("p1_channel_url_pending", url)
                    set_state("p1_nav_pending", 1)
                    set_state("rp_last_channel_urls", [])
                    st.toast(f"✅ 벤치마킹 탭 적용 → Part 1으로 이동합니다")
                    st.rerun()

        # 직접 URL 입력 → 벤치마킹 적용
        st.markdown("---")
        st.caption("✏️ URL 직접 입력 후 적용")
        manual_url = st.text_input(
            "채널 URL 직접 입력",
            placeholder="https://www.youtube.com/@채널명",
            key="rp_manual_url",
            label_visibility="collapsed",
        )
        if st.button("📤 이 URL 벤치마킹 적용", key="rp_manual_apply", use_container_width=True):
            target = manual_url.strip() if manual_url.strip() else get_state("p1_channel_url", "")
            if target:
                new_counter = get_state("p1_url_counter", 0) + 1
                set_state("p1_url_counter", new_counter)
                set_state("p1_channel_url", target)
                set_state("p1_channel_url_pending", target)
                set_state("p1_nav_pending", 1)
                st.toast(f"✅ 적용: {target}")
                st.rerun()


def _get_channel_queries():
    """Profile의 typical_topics 기반 채널 발굴 쿼리 동적 생성"""
    try:
        from core.profile_loader import load_current_profile
        p = load_current_profile()
        topics = p.get("typical_topics", [])
        target = p.get("target_audience", "")
        philosophy = p.get("philosophy_anchor", [])
    except Exception:
        topics, target, philosophy = [], "", []

    ko = []
    if topics:
        ko.append(f"{topics[0] if topics else ''} 유튜브 채널")
    if target:
        ko.append(f"{target} 콘텐츠 채널")
    if philosophy:
        ko.append(f"{philosophy[0] if philosophy else ''} 철학 유튜브")
    if not ko:
        ko = ["심리 인문학 다큐", "철학 유튜브 채널", "라이프 콘텐츠"]

    en = ["psychology philosophy documentary", "life meaning channel", "personal growth youtube"]
    return ko[:3], en[:3]


# 하위 호환 (기존 코드가 KO_QUERIES 직접 참조 시)
KO_QUERIES = ["심리 인문학 다큐", "철학 실존주의 유튜브", "관계 심리학 채널"]
EN_QUERIES = ["psychology existential documentary", "Stoicism philosophy channel", "life meaning relationships"]


def _is_recently_active(channel_id: str, api_key: str, days: int = 15) -> bool:
    """최근 days일 이내 영상 업로드 여부 확인"""
    from datetime import datetime, timedelta, timezone
    import requests as _req
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        url = (
            f"https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&channelId={channel_id}&type=video"
            f"&order=date&maxResults=1&publishedAfter={cutoff}&key={api_key}"
        )
        items = _req.get(url, timeout=5).json().get("items", [])
        return len(items) > 0
    except Exception:
        return True  # 오류 시 통과


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_channels(queries: tuple, api_key: str, lang: str, max_results: int = 5) -> list:
    """병렬 쿼리 + 캐시(30분) — YouTube 채널 검색 및 필터링"""
    import requests as _req
    from concurrent.futures import ThreadPoolExecutor, as_completed

    seen_ids = set()
    all_items = []

    def _search_one(q):
        params = f"part=snippet&q={q}&type=channel&maxResults={max_results}&key={api_key}"
        if lang == "ko":
            params += "&relevanceLanguage=ko&regionCode=KR"
        try:
            return _req.get(
                f"https://www.googleapis.com/youtube/v3/search?{params}", timeout=5
            ).json().get("items", [])
        except Exception:
            return []

    # 쿼리를 병렬 실행 (전체 제한 15초)
    try:
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {ex.submit(_search_one, q): q for q in queries}
            for fut in as_completed(futures, timeout=15):
                try:
                    for item in fut.result():
                        cid = item["id"]["channelId"]
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            all_items.append(cid)
                except Exception:
                    pass
    except Exception:
        pass

    if not all_items:
        return []

    # 통계 조회 (최대 50개 배치)
    channels = []
    try:
        for i in range(0, min(len(all_items), 50), 50):
            batch = ",".join(all_items[i:i+50])
            resp = _req.get(
                f"https://www.googleapis.com/youtube/v3/channels"
                f"?part=snippet,statistics&id={batch}&key={api_key}", timeout=8
            ).json().get("items", [])
            channels.extend(resp)
    except Exception:
        pass

    # 필터링 및 떡상 지수 계산
    result = []
    for ch in channels:
        try:
            stats   = ch.get("statistics", {})
            snippet = ch.get("snippet", {})
            hidden  = stats.get("hiddenSubscriberCount", False)
            subs    = int(stats.get("subscriberCount", 0)) if not hidden else 0
            views   = int(stats.get("viewCount", 0))
            videos  = max(int(stats.get("videoCount", 1)), 1)
            if (hidden or subs <= 10000) and views >= 100000:
                bang  = views / max(subs if not hidden else 500, 1)
                result.append({
                    "id":         ch["id"],
                    "name":       snippet.get("title", ""),
                    "url":        f"https://www.youtube.com/channel/{ch['id']}",
                    "subs":       "비공개" if hidden else f"{subs:,}명",
                    "views":      f"{views:,}회",
                    "avg_views":  f"{views // videos:,}회/영상",
                    "bang_score": bang,
                    "desc":       snippet.get("description", "")[:120],
                    "recent":     "⏳ 확인중",  # 나중에 상위 3개만 체크
                })
        except Exception:
            continue

    # 떡상 지수 기준 정렬 후 상위 5개만 유지
    result.sort(key=lambda x: -x.get("bang_score", 0))
    result = result[:5]

    # _is_recently_active 는 상위 3개만 체크 (API 절약)
    for ch_data in result[:3]:
        active = _is_recently_active(ch_data["id"], api_key, days=15)
        ch_data["recent"] = "✅ 15일내 업로드" if active else "⚠️ 장기 미업로드"
    for ch_data in result[3:]:
        ch_data["recent"] = "—"

    return result


def search_youtube_channels(query: str, api_key: str, max_results: int = 5) -> str:
    """국내 5개 + 국외 5개 심리학·철학 채널 검색 (병렬·캐시)"""
    try:
        # Profile 기반 동적 쿼리 생성
        _ko_q, _en_q = _get_channel_queries()
        domestic = _fetch_channels(tuple(_ko_q), api_key, "ko", max_results)
        foreign  = _fetch_channels(tuple(_en_q), api_key, "en", max_results)

        lines = ["[YouTube 채널 검색결과 — 구독자 1만↓ + 조회수 10만↑]"]

        lines.append("\n■ 국내 채널")
        def _fmt_ch(i, ch):
            bang = ch.get("bang_score", 0)
            bang_label = (
                "🔥🔥 초강력 떡상" if bang >= 500 else
                "🔥 떡상" if bang >= 100 else
                "📈 성장중" if bang >= 30 else "➡️ 일반"
            )
            return (
                f"{i}. {ch['name']} {ch.get('recent', '')} {bang_label}\n"
                f"   구독자: {ch['subs']} | 총조회수: {ch['views']} "
                f"| 영상당평균: {ch.get('avg_views','?')} | 떡상지수: {bang:.0f}x\n"
                f"   URL: {ch['url']}\n"
                f"   {ch['desc']}"
            )

        if domestic:
            for i, ch in enumerate(domestic[:5], 1):
                lines.append(_fmt_ch(i, ch))
        else:
            lines.append("   (API 조건 충족 채널 없음 — Gemini 지식으로 직접 추천)")

        lines.append("\n■ 국외 채널")
        if foreign:
            for i, ch in enumerate(foreign[:5], 1):
                lines.append(_fmt_ch(i, ch))
        else:
            lines.append("   (API 조건 충족 채널 없음 — Gemini 지식으로 직접 추천)")

        return "\n".join(lines)
    except Exception as e:
        return f"[YouTube 검색 오류] {e}"


# ── Task 23/24: "시작" 명령 핸들러 ──────────────────────────────────

_START_KEYWORDS = {"시작", "start", "go", "ㅅㅈ", "출발", "시작!", "시작하자", "시작해"}


def handle_command(user_input: str) -> str:
    """우측 대화창 명령 처리 — 특수 명령 감지 후 라우팅"""
    cmd = user_input.strip().lower().rstrip("!")
    if cmd in _START_KEYWORDS or user_input.strip() in _START_KEYWORDS:
        return start_channel_workflow()
    return ""  # 일반 메시지 → generate_response_sync 에서 처리


def start_channel_workflow() -> str:
    """현재 채널로 자동 시작 — LibrarianAgent 자동 실행"""
    try:
        from core.profile_loader import load_current_profile
        profile = load_current_profile()
    except Exception:
        profile = {}

    channel_name = profile.get("channel_name", "")
    channel_key  = st.session_state.get("current_channel_profile", "")

    if not channel_key or not channel_name:
        return (
            "먼저 채널을 선택해주세요.\n\n"
            "사이드바 **채널 선택** 드롭다운에서 채널을 고르거나,\n"
            "**+ 새 채널 만들기**로 채널을 생성하세요."
        )

    # 채널 MD 파일 로드
    try:
        from core.md_loader import load_channel_md
        identity  = load_channel_md(channel_key, "IDENTITY.md")
        start_cmd = load_channel_md(channel_key, "START_COMMAND.md")
        topic_rules    = load_channel_md(channel_key, "TOPIC_RULES.md")
        benchmark_rules = load_channel_md(channel_key, "BENCHMARK_RULES.md")
    except Exception:
        identity = start_cmd = topic_rules = benchmark_rules = ""

    # 이전 영상 RAG
    prev_context = ""
    try:
        from core.obsidian import search_rag
        channel_dir = profile.get("obsidian_channel_dir", f"채널_{channel_name}")
        prev_context = search_rag(channel_dir, max_files=5, max_chars=600)
    except Exception:
        pass

    # LibrarianAgent 자동 실행
    try:
        from core.agents.librarian import LibrarianAgent
        agent = LibrarianAgent(profile=profile)
        context = {
            "identity":       identity,
            "start_command":  start_cmd,
            "topic_rules":    topic_rules,
            "benchmark_rules": benchmark_rules,
            "previous_context": prev_context,
            "channel_key":    channel_key,
            "auto_start":     True,
        }
        result = agent.execute(context)
        topics = result.get("topics", [])
        if topics:
            lines = [f"## 🚀 {channel_name} — 자동 시작 완료\n"]
            lines.append("### 주제 후보 (댓글 기반)")
            for i, t in enumerate(topics[:10], 1):
                title = t.get("title", t.get("topic", str(t)))
                reason = t.get("reason", "")
                lines.append(f"**{i}.** {title}")
                if reason:
                    lines.append(f"   → {reason}")
            lines.append("\n주제 번호를 입력하면 Part 2로 자동 진입합니다.")
            return "\n".join(lines)
        else:
            return f"## 🚀 {channel_name} — 분석 완료\n\n{str(result)[:800]}"
    except Exception as e:
        # LibrarianAgent 없거나 오류 시 → 프롬프트 기반 시작 안내
        parts = [f"## 🚀 {channel_name} 채널 시작"]
        if identity:
            parts.append(f"\n**채널 정체성 로드 완료**")
            parts.append(f"- 타겟: {profile.get('target_audience', '')}")
            parts.append(f"- 톤: {profile.get('tone', '')}")
        if prev_context:
            parts.append(f"\n**이전 자료 RAG 완료** — 기존 자료 참조 중")
        if start_cmd:
            parts.append(f"\n**실행 계획:**\n{start_cmd[:500]}")
        parts.append(f"\n⚙️ Part 1 탭으로 이동하여 자료수집을 시작하세요.")
        return "\n".join(parts)


# ── Task 35: MD 편집기 UI ─────────────────────────────────────────────

def render_md_editor():
    """프롬프트 MD 파일 편집 UI (사이드바/우측 패널 고급 모드)"""
    st.markdown("#### ⚙️ 프롬프트 편집")
    try:
        from core.md_loader import list_all_prompts, load_md, save_md
        tree = list_all_prompts()
    except Exception as e:
        st.error(f"MD 로더 오류: {e}")
        return

    if not tree:
        st.info("prompts/ 폴더에 MD 파일이 없습니다")
        return

    # 카테고리 선택
    categories = list(tree.keys())
    cat = st.selectbox("카테고리", categories, key="md_edit_cat")
    files = tree.get(cat, [])
    if not files:
        return

    file_names = [f["name"] for f in files]
    sel_name = st.selectbox("파일", file_names, key="md_edit_file")
    sel_file = next((f for f in files if f["name"] == sel_name), None)
    if not sel_file:
        return

    current_content = load_md(sel_file["path"])
    edited = st.text_area(
        f"편집: {sel_file['rel']}",
        value=current_content,
        height=300,
        key=f"md_edit_content_{sel_file['rel']}",
    )

    col1, col2 = st.columns(2)
    if col1.button("💾 저장", key="md_edit_save", use_container_width=True, type="primary"):
        try:
            save_md(sel_file["path"], edited)
            st.success(f"✅ 저장 완료 — 1분 후 자동 반영")
        except Exception as e:
            st.error(f"저장 오류: {e}")
    if col2.button("↩️ 원복", key="md_edit_reset", use_container_width=True):
        st.rerun()


def generate_response_sync(user_msg: str, history: list, model_key: str) -> str:
    """도구 라우팅 → 컨텍스트 수집 → 모델 응답 생성

    기본 동작: 선택된 모델로 직접 질문에 답변 (일반 챗봇)
    + Tavily 도구 활성화 시: 웹검색 결과 컨텍스트 추가
    + Gemini Deep 도구 활성화 시: Gemini 강제 사용
    + 유튜브 채널 키워드 감지 시: YouTube API + Gemini 강제
    + "시작" 명령 감지 시: start_channel_workflow() 직접 실행
    """
    import requests as _req

    # ── "시작" 명령 최우선 감지 ─────────────────────────────────────
    cmd_response = handle_command(user_msg)
    if cmd_response:
        return cmd_response

    active_tool = get_state("rp_active_tool", "")
    extra_context = ""
    force_gemini  = False
    is_yt_channel_query = False
    yt_context    = ""

    # ── 0. + 버튼 도구 처리 ────────────────────────────────
    if active_tool == "tavily":
        tavily_key = st.session_state.get("api_tavily", "")
        if tavily_key:
            try:
                tv_res = _req.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_key, "query": user_msg,
                          "search_depth": "advanced", "max_results": 5,
                          "include_answer": True},
                    timeout=15,
                )
                if tv_res.status_code == 200:
                    tv_data = tv_res.json()
                    lines = []
                    if tv_data.get("answer"):
                        lines.append(f"[검색 요약] {tv_data['answer']}")
                    for r in tv_data.get("results", [])[:5]:
                        lines.append(
                            f"- {r.get('title','')}: {r.get('content','')[:200]} "
                            f"(출처: {r.get('url','')})"
                        )
                    extra_context = "\n".join(lines)
            except Exception:
                pass
        set_state("rp_active_tool", "")

    elif active_tool == "gemini_deep":
        force_gemini = True
        model_key = next(
            (k for k, v in MODELS.items() if v.get("type") == "remote"),
            "gemini-2.5-flash"
        )
        set_state("rp_active_tool", "")

    elif active_tool == "youtube_analyze":
        # YouTube 영상 URL → 메타데이터 추출 후 Gemini 분석
        import re as _re
        _yt_vid = _re.search(
            r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_\-]{11})',
            user_msg
        )
        if _yt_vid:
            _vid_id = _yt_vid.group(1)
            _yt_key = st.session_state.get("api_youtube", "")
            if _yt_key:
                try:
                    _meta_r = _req.get(
                        f"https://www.googleapis.com/youtube/v3/videos"
                        f"?part=snippet,statistics&id={_vid_id}&key={_yt_key}",
                        timeout=5,
                    )
                    if _meta_r.status_code == 200:
                        _items = _meta_r.json().get("items", [])
                        if _items:
                            _snip  = _items[0].get("snippet", {})
                            _stats = _items[0].get("statistics", {})
                            extra_context = (
                                f"[YouTube 영상 정보]\n"
                                f"제목: {_snip.get('title','')}\n"
                                f"채널: {_snip.get('channelTitle','')}\n"
                                f"설명: {_snip.get('description','')[:500]}\n"
                                f"조회수: {_stats.get('viewCount','?')}\n"
                                f"좋아요: {_stats.get('likeCount','?')}\n"
                                f"댓글수: {_stats.get('commentCount','?')}\n"
                            )
                except Exception:
                    pass
        force_gemini = True
        set_state("rp_active_tool", "")

    elif active_tool in ("notebooklm", "manual", "file_explorer", "gdrive"):
        set_state("rp_active_tool", "")

    # ── 1. YouTube 채널 검색 (명시적 키워드 시에만) ──────────
    yt_keywords = ["유튜브 채널", "youtube 채널", "채널 찾", "채널 추천",
                   "채널 국내", "채널 국외", "채널 선정", "벤치마킹 채널"]
    if any(kw in user_msg.lower() for kw in yt_keywords):
        is_yt_channel_query = True
        yt_key = st.session_state.get("api_youtube", "")
        if yt_key:
            domain_keywords = ["심리학", "철학", "성경", "명상", "자존감", "힐링",
                               "psychology", "감정", "인문학", "라이프", "동기", "치유", "상담"]
            yt_query = next((k for k in domain_keywords if k in user_msg), "심리학 유튜브")
            yt_context = search_youtube_channels(yt_query, yt_key)

    # ── 2. 시스템 프롬프트 구성 (Profile 동적 빌드) ─────────────
    system_prompt = _build_brain_prompt() + "\n답변은 반드시 한국어로, 존댓말로 작성하세요.\n"

    if extra_context:
        system_prompt += f"\n[웹 검색 결과]\n{extra_context}\n"

    if is_yt_channel_query:
        system_prompt += (
            "\n[역할] 유튜브 콘텐츠 전략가 / 심리학·철학 다큐 큐레이터\n"
            "현자의 거울과 동일한 방향성의 채널을 국내 5개·국외 5개 발굴·분석하세요.\n"
            "YouTube API 결과가 부족하면 학습 지식으로 직접 추천하세요.\n\n"
            "[벤치마킹 기준]\n"
            "- 타겟: 4070세대 (고독·상실·공허·관계단절)\n"
            "- 스타일: 시네마틱 다큐, 롱폼, 인간 중심 나레이션\n"
            "- 지식 체계: 칼 융·프랭클 / 쇼펜하우어·스토아 / 성경\n"
            "- 다크심리학 콘텐츠 우대\n\n"
        )
        if yt_context:
            system_prompt += f"[YouTube API 실시간 검색결과]\n{yt_context}\n\n"
        system_prompt += (
            "[채널 선정 기준]\n"
            "1. 구독자 1만↓ 숨은 보석 / 10만↓ 급성장 채널\n"
            "2. 떡상 지수(조회수÷구독자) 높은 채널 우선\n"
            "3. 최근 15일내 업로드 활성 채널 우선\n"
            "4. 오리지널 기획력 채널만 (컴필레이션 배제)\n\n"
            "[출력 형식 — 채널당 6개 항목]\n"
            "1. 채널명  2. URL  3. 구독자·평균 조회수\n"
            "4. 현자의 거울과 유사한 점  5. 핵심 후킹 기법  6. 시청자 고통 키워드\n\n"
            "국내 5개, 국외 5개 필수. 마지막에:\n"
            "[선정채널URL: https://www.youtube.com/@채널명]\n"
        )

    # ── 3. 대화 히스토리 구성 ────────────────────────────────
    final_user_msg = user_msg
    if is_yt_channel_query:
        final_user_msg = (
            f"{user_msg}\n\n"
            "반드시 국내 5개, 국외 5개, 총 10개를 모두 출력하세요. 국외 채널 생략 절대 금지."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": final_user_msg})

    # ── 4. 모델 라우팅 ───────────────────────────────────────
    cur_model  = model_key or st.session_state.get("current_model", DEFAULT_MODEL)
    model_info = MODELS.get(cur_model, {})
    model_type = model_info.get("type", "local")

    if is_yt_channel_query or force_gemini or model_type == "remote":
        _m = cur_model if model_type == "remote" else next(
            (k for k, v in MODELS.items() if v.get("type") == "remote"), "gemini-2.5-flash"
        )
        result = call_gemini_with_messages(messages, _m)
    else:
        success, result, _ = call_ollama_sync(user_msg, system_prompt, cur_model)
        if not success:
            result = result or "응답을 생성하지 못했습니다."

    # ── 5. 선정 채널 URL 자동 추출 → 벤치마킹 탭 푸시 ────────
    if is_yt_channel_query and result:
        import re
        url_match = re.search(r'\[선정채널URL:\s*(https?://[^\]\s]+)\]', result)
        if url_match:
            selected_url = url_match.group(1).strip().rstrip('/.,)')
            set_state("p1_url_counter", get_state("p1_url_counter", 0) + 1)
            set_state("p1_channel_url", selected_url)
            set_state("p1_channel_url_pending", selected_url)
            set_state("p1_nav_pending", 1)
            set_state("p1_bench_auto_selected", selected_url)

    if not result or not result.strip():
        return "(빈 응답 — 모델을 확인하세요)"

    # ── 6. 옵시디언 자동 저장 ────────────────────────────────
    try:
        from core.unified_save import save_anything
        part_ctx = st.session_state.get("current_part")
        if extra_context and len(extra_context) > 50:
            save_anything(content=extra_context, title=f"Tavily_{user_msg[:30]}",
                         content_type="tavily_research", part_num=part_ctx)
        if yt_context and len(yt_context) > 50:
            save_anything(content=yt_context, title=f"YouTube채널_{user_msg[:20]}",
                         content_type="youtube_channel", part_num=part_ctx)
        if len(result) > 100:
            save_anything(content=f"## 질문\n{user_msg}\n\n## AI 응답\n{result}",
                         title=user_msg[:40], content_type="gemini_research", part_num=part_ctx)
    except Exception:
        pass

    return result
