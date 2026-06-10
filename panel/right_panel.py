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


BRAIN_SYSTEM_PROMPT = """너는 현자의 거울 스튜디오의 공장장 젬마다.

[채널 정체성]
- 채널명: 현자의 거울 (@Ethan Cinematic Video)
- 타겟: 4070세대 (고독·상실·공허·관계단절·인생의 의미 고민)
- 스타일: 17세기 렘브란트풍 시네마틱 다큐멘터리
- 지식 체계: 칼 융·빅터 프랭클(심리학) / 쇼펜하우어·스토아(철학) / 성경(시편·잠언·전도서)

[CRITICAL]
- 한국어로만 답변
- 즉시 본론, 부연 설명 없음
- "Thinking", "Process" 단어 사용 금지

[역할] 현자(60대 콘텐츠 크리에이터)의 비서
[금지] AI 냄새 표현, 추측 인용, 영어 답변
"""


def call_gemini_with_messages(messages: list, model_key: str, _retry: int = 3) -> str:
    """Gemini API 멀티턴 호출 — 503/429 재시도 + Ollama 폴백"""
    import time
    try:
        from google import genai as _genai
        api_key = st.session_state.get("api_gemini", "")
        if not api_key:
            return "Gemini API 키가 없습니다."
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
        resp = client.models.generate_content(
            model=model_key,
            contents=gemini_contents,
            config=cfg_obj,
        )
        return resp.text or "응답 없음"
    except Exception as e:
        err_str = str(e)
        # 503(과부하) / 429(쿼터) → 재시도
        if _retry > 0 and ("503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str):
            wait = (4 - _retry) * 5  # 5초 → 10초 → 15초
            time.sleep(wait)
            return call_gemini_with_messages(messages, model_key, _retry - 1)
        # 재시도 소진 → Ollama 폴백
        user_content = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        system_content = next((m["content"] for m in messages if m["role"] == "system"), "")
        _, fallback, _ = call_ollama_sync(user_content, system_content)
        if fallback:
            return f"[Gemini 불가 — Gemma 대체 응답]\n{fallback}"
        return f"[Gemini 오류] {e}"


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
            "num_predict": 400,
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
    
    # [+] 허브 메뉴 (새로 추가)
    from panel.hub_menu import render_hub_menu, render_text_input_panel
    render_hub_menu()
    render_text_input_panel()
    
    # 모델 선택
    models = list(MODELS.keys())
    cur_model = get_state("rp_model", DEFAULT_MODEL)
    sel = st.selectbox(
        "모델",
        models,
        index=models.index(cur_model) if cur_model in models else 0,
        format_func=lambda x: MODELS[x]["label"],
        key="rp_model_sel",
    )
    if sel != cur_model:
        set_state("rp_model", sel)
    
    st.markdown("---")
    
    render_chat_with_response()
    
    user_input = st.chat_input("메시지를 입력하세요...")
    
    if user_input:
        history = get_state("rp_history", [])
        history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat(),
        })
        set_state("rp_history", history)
        st.rerun()


def _extract_yt_urls(text: str) -> list:
    """응답 텍스트에서 YouTube 채널 URL 중복 없이 추출"""
    import re
    urls = re.findall(
        r'https://www\.youtube\.com/(?:channel|c|@)[^\s)\]"\'<>]+',
        text
    )
    return list(dict.fromkeys(url.rstrip('/.,') for url in urls))


def render_chat_with_response():
    """대화 표시 + 응답 생성 (모두 컨테이너 안)"""
    history = get_state("rp_history", [])

    box = st.container(height=700, border=True)

    with box:
        if not history:
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

    # ── 채팅 컨테이너 밖: 채널 벤치마킹 바로 적용 버튼 ────────────
    # 마지막 assistant 응답에서 추출한 채널 URL이 있으면 버튼 표시
    last_urls = get_state("rp_last_channel_urls", [])
    if not last_urls and history and history[-1]["role"] == "assistant":
        last_urls = _extract_yt_urls(history[-1]["content"])
        if last_urls:
            set_state("rp_last_channel_urls", last_urls)

    if last_urls:
        st.markdown("##### 📌 채널 벤치마킹 바로 적용")
        n = min(len(last_urls), 3)
        cols = st.columns(n)
        for idx, url in enumerate(last_urls[:6]):
            short = url.rstrip('/').split('/')[-1][:28]
            col = cols[idx % n]
            if col.button(f"📤 {short}", key=f"rp_bench_{idx}", help=url, use_container_width=True):
                set_state("p1_channel_url", url)
                set_state("rp_last_channel_urls", [])
                st.toast(f"✅ 벤치마킹 탭에 적용됨: {url}")
                st.rerun()


KO_QUERIES = [
    "4070 심리 상담",
    "인문학 다큐멘터리",
    "쇼펜하우어 에세이 유튜브",
    "관계 심리학 인간관계",
    "실존주의 철학 채널",
]

EN_QUERIES = [
    "Philosophy documentary 40s 50s",
    "Jungian psychology channel",
    "Stoicism for life advice",
    "Existential crisis video essay",
    "Psychology of relationships deep dive",
]


def _is_recently_active(channel_id: str, api_key: str, days: int = 15) -> bool:
    """최근 days일 이내 영상 업로드 여부 확인 (YouTube search API)"""
    from datetime import datetime, timedelta, timezone
    import requests as _req
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        url = (
            f"https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&channelId={channel_id}&type=video"
            f"&order=date&maxResults=1&publishedAfter={cutoff}&key={api_key}"
        )
        items = _req.get(url, timeout=10).json().get("items", [])
        return len(items) > 0
    except Exception:
        return True  # 오류 시 필터링 생략


def _fetch_channels(queries: list, api_key: str, lang: str, max_results: int = 10) -> list:
    """여러 키워드로 YouTube 채널 검색 후 중복 제거 + 통계 + 최근 15일 활동 반환"""
    import requests as _req
    seen_ids = set()
    all_items = []
    for q in queries:
        params = f"part=snippet&q={q}&type=channel&maxResults={max_results}&key={api_key}"
        if lang == "ko":
            params += "&relevanceLanguage=ko&regionCode=KR"
        items = _req.get(
            f"https://www.googleapis.com/youtube/v3/search?{params}", timeout=15
        ).json().get("items", [])
        for item in items:
            cid = item["id"]["channelId"]
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_items.append(cid)

    if not all_items:
        return []

    # 50개씩 나눠서 통계 조회 (API 제한)
    channels = []
    for i in range(0, len(all_items), 50):
        batch = ",".join(all_items[i:i+50])
        resp = _req.get(
            f"https://www.googleapis.com/youtube/v3/channels"
            f"?part=snippet,statistics&id={batch}&key={api_key}", timeout=15
        ).json().get("items", [])
        channels.extend(resp)

    result = []
    for ch in channels:
        stats = ch.get("statistics", {})
        snippet = ch.get("snippet", {})
        hidden = stats.get("hiddenSubscriberCount", False)
        subs = int(stats.get("subscriberCount", 0)) if not hidden else 0
        views = int(stats.get("viewCount", 0))
        if (hidden or subs <= 10000) and views >= 100000:
            ch_id = ch["id"]
            recently_active = _is_recently_active(ch_id, api_key, days=15)
            result.append({
                "id": ch_id,
                "name": snippet.get("title", ""),
                "url": f"https://www.youtube.com/channel/{ch_id}",
                "subs": "비공개" if hidden else f"{subs:,}명",
                "views": f"{views:,}회",
                "desc": snippet.get("description", "")[:120],
                "recent": "✅ 15일내 업로드" if recently_active else "⚠️ 장기 미업로드",
            })
    # 최근 활동 채널 우선 정렬
    result.sort(key=lambda x: 0 if x["recent"].startswith("✅") else 1)
    return result


def search_youtube_channels(query: str, api_key: str, max_results: int = 10) -> str:
    """국내 5개 + 국외 5개 심리학·철학 채널 검색"""
    try:
        domestic = _fetch_channels(KO_QUERIES, api_key, "ko", max_results)
        foreign  = _fetch_channels(EN_QUERIES, api_key, "en", max_results)

        lines = ["[YouTube 채널 검색결과 — 구독자 1만↓ + 조회수 10만↑]"]

        lines.append("\n■ 국내 채널")
        if domestic:
            for i, ch in enumerate(domestic[:5], 1):
                lines.append(
                    f"{i}. {ch['name']} {ch.get('recent', '')}\n"
                    f"   구독자: {ch['subs']} | 총조회수: {ch['views']}\n"
                    f"   URL: {ch['url']}\n"
                    f"   {ch['desc']}"
                )
        else:
            lines.append("   (API 조건 충족 채널 없음 — Gemini 지식으로 직접 추천)")

        lines.append("\n■ 국외 채널")
        if foreign:
            for i, ch in enumerate(foreign[:5], 1):
                lines.append(
                    f"{i}. {ch['name']} {ch.get('recent', '')}\n"
                    f"   구독자: {ch['subs']} | 총조회수: {ch['views']}\n"
                    f"   URL: {ch['url']}\n"
                    f"   {ch['desc']}"
                )
        else:
            lines.append("   (API 조건 충족 채널 없음 — Gemini 지식으로 직접 추천)")

        return "\n".join(lines)
    except Exception as e:
        return f"[YouTube 검색 오류] {e}"


def generate_response_sync(user_msg: str, history: list, model_key: str) -> str:
    """Tavily 검색 우선 → Gemini/Ollama 분석 응답 생성"""
    import requests as _req

    # 0. YouTube 채널 검색 감지
    yt_context = ""
    is_yt_channel_query = False
    yt_keywords = ["유튜브 채널", "youtube 채널", "채널 찾", "채널 추천", "채널 국내", "채널 국외", "채널 선정", "벤치마킹 채널"]
    if any(kw in user_msg.lower() for kw in yt_keywords):
        is_yt_channel_query = True
        yt_key = st.session_state.get("api_youtube", "")
        if yt_key:
            # 문장에서 핵심 검색 키워드만 추출 (YouTube API용)
            import re as _re
            domain_keywords = ["심리학", "철학", "성경", "명상", "자존감", "힐링", "psychology",
                               "감정", "인문학", "라이프", "동기", "치유", "상담"]
            yt_query = next((k for k in domain_keywords if k in user_msg), "심리학 유튜브")
            yt_context = search_youtube_channels(yt_query, yt_key)

    # 1. Tavily 실시간 검색 시도
    tavily_context = ""
    tavily_key = st.session_state.get("api_tavily", "")
    if tavily_key:
        try:
            tv_res = _req.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": user_msg,
                    "search_depth": "advanced",
                    "max_results": 5,
                    "include_answer": True
                },
                timeout=15
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
                tavily_context = "\n".join(lines)
        except Exception:
            tavily_context = ""

    # 2. 시스템 프롬프트 구성
    system_prompt = (
        "당신은 현자의 거울 스튜디오 공장장 젬마입니다.\n"
        "현자님(60대 유튜브 크리에이터)을 보좌합니다.\n\n"
        "[채널 정체성]\n"
        "채널명: 현자의 거울 (@Ethan Cinematic Video)\n"
        "타겟: 4070세대 — 고독, 상실, 공허, 관계 단절, 인생의 의미를 고민하는 세대\n"
        "스타일: 17세기 렘브란트풍 시네마틱 다큐멘터리\n"
        "핵심 지식 체계:\n"
        "  - 심리학: 칼 융(그림자 자아·개성화), 빅터 프랭클(로고테라피·의미치료)\n"
        "  - 철학: 쇼펜하우어(의지·고통), 스토아(절제·내면의 자유)\n"
        "  - 성경적 통찰: 시편·잠언·전도서·욥기 중심\n\n"
        "답변은 반드시 한국어로, 존댓말로 작성하세요.\n"
    )
    if is_yt_channel_query:
        system_prompt += (
            "\n[역할] 당신은 유튜브 채널 발굴 전문가입니다.\n"
            "아래 채널 정체성과 동일한 방향성을 가진 채널을 국내 5개·국외 5개 찾아 분석하세요.\n"
            "YouTube API 결과가 부족하면 당신의 학습 지식으로 직접 추천하세요.\n\n"
            "[벤치마킹 기준 채널 정체성]\n"
            "- 타겟: 4070세대 (고독·상실·공허·관계단절·인생의 의미 고민)\n"
            "- 스타일: 시네마틱 다큐멘터리, 긴 호흡 롱폼, 인간 중심 나레이션\n"
            "- 지식 체계: 칼 융·빅터 프랭클 / 쇼펜하우어·스토아 / 성경(시편·잠언·전도서)\n"
            "- 다크심리학(가스라이팅·나르시시즘·정서적 착취) 콘텐츠 우대\n\n"
        )
        if yt_context:
            system_prompt += (
                "[YouTube API 실시간 검색결과]\n"
                + yt_context + "\n\n"
            )
        system_prompt += (
            "[채널 선정 기준 — 엄격 준수]\n"
            "1. 구독자 1만↓ '숨은 보석' 또는 10만↓ '급성장 채널'\n"
            "   ★ 최근 15일 이내 영상을 꾸준히 업로드하는 '활성 채널' 최우선 선정\n"
            "   (API 결과에 ✅ 15일내 업로드 표시된 채널 우선, ⚠️ 장기 미업로드 채널 감점)\n"
            "2. 지식 나열 아닌 시청자 '내면 결핍'을 공감으로 치유하는 서사 중심 채널\n"
            "3. 2025~2026 트렌드 부합 (긴 호흡 롱폼, 인간 중심 나레이션)\n"
            "4. 다크심리학(가스라이팅/나르시시즘/정서적 착취) 다루는 채널 우대\n"
            "5. 표절·재사용·컴필레이션 채널 철저 배제 — 오리지널 기획력 채널만\n\n"
            "[분석 기준]\n"
            "- 구독자 대비 조회수 비율 (떡상 지수)\n"
            "- 4070 감정·철학·심리 콘텐츠 적합성\n"
            "- 현자의 거울 채널 방향성 유사도 (렘브란트풍·시네마틱·철학·성경)\n\n"
            "[출력 형식]\n"
            "국내 5개 / 국외 5개 각각: 채널명, URL, 구독자수, 대표 조회수, 선정이유\n"
            "마지막에 최종 벤치마킹 추천 1개를 아래 형식으로 반드시 기재:\n"
            "[선정채널URL: https://www.youtube.com/channel/CHANNEL_ID]\n"
        )
    if tavily_context:
        system_prompt += (
            "\n[실시간 트렌드 검색 결과]\n"
            + tavily_context + "\n"
        )

    # 3. 대화 히스토리 구성
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    # 4. 모델 라우팅 — YouTube 채널 분석 시 Gemini 강제 사용
    cur_model = st.session_state.get("current_model", DEFAULT_MODEL)
    model_info = MODELS.get(cur_model, {})
    model_type = model_info.get("type", "local")

    if is_yt_channel_query:
        # YouTube 채널 분석은 데이터 유무와 관계없이 Gemini 강제 라우팅
        gemini_model = next(
            (k for k, v in MODELS.items() if v.get("type") == "remote"),
            "gemini-2.5-flash"
        )
        result = call_gemini_with_messages(messages, gemini_model)
    elif model_type == "remote":
        result = call_gemini_with_messages(messages, cur_model)
    else:
        success, result, _ = call_ollama_sync(user_msg, system_prompt, cur_model)
        if not success:
            result = result or "응답을 생성하지 못했습니다."

    # 5. 선정 채널 URL 자동 추출 → 벤치마킹 탭 푸시
    if is_yt_channel_query and result:
        import re
        url_match = re.search(r'\[선정채널URL:\s*(https://[^\]\s]+)\]', result)
        if url_match:
            selected_url = url_match.group(1).strip()
            set_state("p1_channel_url", selected_url)
            set_state("p1_bench_auto_selected", selected_url)

    if not result or result.strip() == "":
        return f"[디버그] model_type={model_type}, yt_context길이={len(yt_context)}, tavily_context길이={len(tavily_context)}"
    return result
