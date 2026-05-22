import sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target_file = r'C:\SageMirror_Production\app_v15_9_2.py'

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[로드] 총 줄 수: {len(content.splitlines())}")

# =============================================================================
# 작업 1: 버전 헤더 업데이트 v15.9.1 → v15.9.2
# =============================================================================
content = content.replace('Master App v15.9.1', 'Master App v15.9.2', 1)
print("[1] 버전 헤더 업데이트 완료")

# =============================================================================
# 작업 2: 사이드바에 Gemini API Key 입력창 추가
# =============================================================================
old_sidebar_apikey = '        st.session_state.youtube_api_key = st.text_input("YouTube API Key", value=st.session_state.get("youtube_api_key", ""), type="password")'
new_sidebar_apikey = (
    '        st.session_state.youtube_api_key = st.text_input("YouTube API Key", value=st.session_state.get("youtube_api_key", ""), type="password")\n'
    '        st.session_state.gemini_api_key = st.text_input("🤖 Gemini API Key", value=st.session_state.get("gemini_api_key", "AIzaSyAhLlLIgnFXNwZY5ARLXYvOMsPHvK82X7Q"), type="password", help="파트1 채널 탐색기에서 사용합니다.")'
)
sidebar_count = content.count(old_sidebar_apikey)
content = content.replace(old_sidebar_apikey, new_sidebar_apikey)
print(f"[2] 사이드바 Gemini API Key 추가: {sidebar_count}개")

# =============================================================================
# 작업 3: 세션스테이트 초기화 블록에 Gemini 관련 키 추가
# =============================================================================
old_init_youtube = '"youtube_api_key": "",'
new_init_youtube = (
    '"youtube_api_key": "",\n'
    '        "gemini_api_key": "AIzaSyAhLlLIgnFXNwZY5ARLXYvOMsPHvK82X7Q",\n'
    '        "p1_gemini_model": "gemini-2.0-flash-exp",\n'
    '        "p1_channel_top10": [],\n'
    '        "p1_benchmark_channel": {},\n'
    '        "p1_search_keywords": [],'
)
init_count = content.count(old_init_youtube)
content = content.replace(old_init_youtube, new_init_youtube)
print(f"[3] 세션스테이트 초기화 키 추가: {init_count}개")

# =============================================================================
# 작업 4: c_right 섹션 — 채널 탐색기 전면 교체
# 기존: Tavily 5채널 + 라디오 리스트
# 신규: 제미나이+Tavily 10채널 자동화 + 팝업 카드
# =============================================================================

# 교체 대상 범위: "##### [SEARCH] 떡상 채널 발굴용 탐색기" 부터
# "##### [TARGET] 분석 대상 확정" 버튼까지 (st.divider() 전까지)
old_search_section = '''        st.markdown("##### [SEARCH] 떡상 채널 발굴용 탐색기")

        st.caption("AI 카피를 배제한 순수 인간 운영의 최고 조회수 채널 여러 개를 검색하여 검토합니다.")



        search_kw = st.text_input(

              "검색 키워드 (가이드라인 기반 자동 세팅)", 

              value=st.session_state.get(

                    "p1_search_keyword",

                    "human operated psychology philosophy life advice channel for age 40 50 60 70 high engagement longform"

               ),

              disabled=is_locked

         )



        st.session_state.p1_search_keyword = search_kw

        

  

        if st.button("🌐 전 세계 채널 5개 탐색 및 리스트업 (Tavily)", disabled=is_locked, use_container_width=True):

            if not st.session_state.tavily_api_key:

                st.error("좌측 사이드바 '⚙️ 설정 변경'에서 Tavily API Key를 먼저 입력하세요.")

            else:

                with st.spinner("최고 떡상 원본 채널 5개를 심층 탐색 중..."):

                    from sage_engine import tavily_search



                    q = search_kw + " YouTube psychology philosophy life advice channel OR video human storytelling older adults high views comments"



                    res = tavily_search(q, st.session_state.tavily_api_key, max_results=20)

                    

                    if "error" in res: st.error(res["error"])



                    else:

                        raw = res.get("results", [])



                        filtered_results = [

                            r for r in raw

                            if "youtube.com" in r.get("url", "")

                        ]



                        st.session_state.p1_channel_search_results = filtered_results



                        st.session_state.pipeline_state["channel_search_results"] = filtered_results

                        st.success("[TARGET] 채널 검색 완료! 아래 목록에서 가장 적합한 채널을 선택하세요.")

        

        if st.session_state.p1_channel_search_results:

            with st.container(border=True):

                st.markdown("**[TARGET] 분석할 채널을 선택하세요 (선택 시 아래 URL에 자동 입력됨):**")



                options = []



                for i, r in enumerate(st.session_state.p1_channel_search_results):

                    options.append(

                          f"[{i+1}] {r.get('title', '제목없음')} - {r.get('url', '#')}"

                    )

                

                selected_channel = st.radio(

                      "검색된 채널 리스트",

                      options,

                      key="p1_selected_channel_radio",

                      label_visibility="collapsed",

                      disabled=is_locked

                )

                

                if selected_channel:

                    selected_url = selected_channel.split(" - ")[-1]



                    st.session_state.p1_channel_url = selected_url



                    st.session_state.pipeline_state["selected_channel"] = selected_channel



                    st.session_state.pipeline_state["selected_channel_url"] = selected_url



                   

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("##### [TARGET] 분석 대상 확정")

        st.session_state.p1_channel_url = st.text_input("타겟 유튜브 URL (위에서 선택 시 자동 입력됨)", value=st.session_state.p1_channel_url, disabled=is_locked)

        st.session_state.p1_region = st.selectbox("타겟 지역", ["국내+국외 모두", "국내 우선", "국외 우선"], disabled=is_locked)'''

new_search_section = '''        # ═══════════════════════════════════════════════════════
        # 🔍 제미나이 기반 떡상 채널 발굴기 (v15.9.2)
        # ═══════════════════════════════════════════════════════
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(212,175,106,0.12),rgba(30,15,5,0.8));
                    border:1.5px solid rgba(212,175,106,0.35);border-radius:12px;padding:12px 16px;margin-bottom:8px;">
            <span style="color:#d4af6a;font-size:1.05em;font-weight:700;">🔍 떡상 채널 발굴기</span>
            <span style="color:#94a3b8;font-size:0.78em;margin-left:8px;">제미나이 AI 큐레이션</span>
        </div>
        """, unsafe_allow_html=True)

        # 모델 선택
        col_model, col_region = st.columns([1, 1])
        with col_model:
            gemini_models = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
            cur_gm = st.session_state.get("p1_gemini_model", "gemini-2.0-flash-exp")
            gm_idx = gemini_models.index(cur_gm) if cur_gm in gemini_models else 0
            sel_gm = st.selectbox("🤖 제미나이 모델", gemini_models, index=gm_idx,
                                   key="p1_gemini_model_select", disabled=is_locked,
                                   help="할당량 초과 시 다른 모델로 전환하세요")
            st.session_state.p1_gemini_model = sel_gm
        with col_region:
            st.session_state.p1_region = st.selectbox("🌏 탐색 지역", ["국내+국외 모두", "국내 우선", "국외 우선"],
                                                        key="p1_region_select", disabled=is_locked)

        # 검색 키워드 미리보기 (자동 생성 + 수동 수정 가능)
        search_kw = st.text_area(
            "📡 검색 키워드 (제미나이 자동 생성 / 직접 수정 가능)",
            value=st.session_state.get("p1_search_keyword",
                "psychology philosophy life advice human NOT AI longform YouTube trending 2025 high retention views"),
            height=68,
            key="p1_search_kw_ta",
            disabled=is_locked,
            help="제미나이가 탐색 시작 시 자동으로 최적 키워드를 생성합니다."
        )
        st.session_state.p1_search_keyword = search_kw

        # ── 채널 탐색 시작 버튼 ──────────────────────────────────
        if st.button("🚀 채널 탐색 시작 (제미나이 + Tavily 자동화)",
                     disabled=is_locked, use_container_width=True,
                     type="primary", key="p1_channel_search_btn"):

            if not st.session_state.get("gemini_api_key"):
                st.error("🔑 사이드바 ⚙️ 설정 변경에서 Gemini API Key를 먼저 입력하세요.")
            elif not st.session_state.get("tavily_api_key"):
                st.error("🔑 사이드바 ⚙️ 설정 변경에서 Tavily API Key를 먼저 입력하세요.")
            else:
                try:
                    import google.generativeai as genai
                    from sage_engine import tavily_search
                    import json as _json
                    import re as _re

                    genai.configure(api_key=st.session_state.gemini_api_key)
                    gemini_model = genai.GenerativeModel(st.session_state.p1_gemini_model)
                    region_hint = st.session_state.p1_region

                    # ── Step 1: 키워드 생성 ──────────────────────────
                    prog = st.progress(0, text="⚙️ Step 1/4 — 제미나이: 정밀 검색 키워드 생성 중...")
                    kw_prompt = f"""
당신은 유튜브 채널 전문 큐레이터입니다.
다음 조건에 맞는 유튜브 채널을 Tavily 웹 검색으로 찾기 위한 **7개의 정밀 검색 키워드**를 생성하세요.

[채널 조건]
- 심리학/철학/인생조언 롱폼 콘텐츠 (10분 이상)
- 인간이 직접 운영 (AI 생성 영상 배제, 편집본 배제, 표절 배제)
- 구독자는 적어도 무방하나 최근 조회수와 시청지속시간이 급상승 중
- 40~70대 감성 타겟 (삶의 지혜, 심리적 통찰)
- 탐색 지역: {region_hint}

[출력 형식] JSON 배열만 출력하세요:
["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7"]
"""
                    kw_resp = gemini_model.generate_content(kw_prompt)
                    kw_text = kw_resp.text.strip()
                    kw_match = _re.search(r'\[.*?\]', kw_text, _re.DOTALL)
                    if kw_match:
                        keywords = _json.loads(kw_match.group())
                    else:
                        keywords = [search_kw, "psychology YouTube channel rising views longform human 2025",
                                    "심리학 유튜브 채널 조회수 급상승 2025", "philosophy life advice NOT AI YouTube trending",
                                    "underrated psychology creator original content rising",
                                    "human storytelling psychology channel high retention views 2025",
                                    "인생조언 철학 유튜브 롱폼 채널 급성장"]
                    st.session_state.p1_search_keywords = keywords
                    prog.progress(25, text="✅ Step 1 완료 — 키워드 7종 생성")

                    # ── Step 2: Tavily 채널 후보 수집 ────────────────
                    prog.progress(30, text="🌐 Step 2/4 — Tavily: 국내외 채널 후보 수집 중...")
                    all_results = []
                    for kw in keywords[:5]:
                        q = kw + " site:youtube.com/channel OR site:youtube.com/@"
                        try:
                            res = tavily_search(q, st.session_state.tavily_api_key, max_results=6)
                            raw = res.get("results", [])
                            yt_filtered = [r for r in raw if "youtube.com" in r.get("url", "")]
                            all_results.extend(yt_filtered)
                        except Exception:
                            pass
                    # 중복 URL 제거
                    seen_urls = set()
                    unique_results = []
                    for r in all_results:
                        url = r.get("url", "")
                        if url not in seen_urls:
                            seen_urls.add(url)
                            unique_results.append(r)
                    st.session_state.p1_channel_candidates = unique_results
                    prog.progress(55, text=f"✅ Step 2 완료 — 후보 {len(unique_results)}개 수집")

                    # ── Step 3+4: 제미나이 필터링 & TOP10 선정 ────────
                    prog.progress(60, text="🤖 Step 3/4 — 제미나이: AI 복제 배제 및 TOP10 선정 중...")

                    candidates_text = ""
                    for i, r in enumerate(unique_results[:30]):
                        candidates_text += f"[{i+1}] 제목: {r.get('title','')}\n URL: {r.get('url','')}\n 내용: {r.get('content','')[:200]}\n\n"

                    filter_prompt = f"""
당신은 유튜브 채널 분석 전문가입니다.
아래 채널 후보 목록에서 다음 기준으로 엄격하게 필터링하여 **상위 10개 채널**을 선정하세요.

[필터링 기준 — 반드시 준수]
1. ✅ 인간이 직접 운영하는 채널 (AI 생성 영상, AI 나레이션, 컴필레이션, 표절 채널 제외)
2. ✅ 심리학/철학/인생조언/자기계발 롱폼 콘텐츠 (Shorts 전문 채널 제외)
3. ✅ 최근 조회수와 시청지속시간이 상승세인 채널 우선 선정
4. ✅ 구독자 수는 무관 — 소규모여도 급성장 중이면 포함
5. ✅ {region_hint} 채널 탐색

[후보 채널 목록]
{candidates_text}

[출력 형식] 반드시 아래 JSON 형식으로만 출력하세요 (다른 텍스트 금지):
{{
  "top10": [
    {{
      "rank": 1,
      "name": "채널명",
      "url": "유튜브 URL",
      "region": "국내/국외",
      "category": "심리학/철학/인생조언 등",
      "reason": "선정 이유 (30자 이내)",
      "trend": "급상승/상승/안정",
      "score": 95
    }}
  ],
  "best": {{
    "rank": 1,
    "name": "최고 추천 채널명",
    "url": "유튜브 URL",
    "reason": "최종 선정 이유 (50자 이내)"
  }}
}}
"""
                    filter_resp = gemini_model.generate_content(filter_prompt)
                    filter_text = filter_resp.text.strip()
                    # JSON 추출
                    json_match = _re.search(r'\{.*\}', filter_text, _re.DOTALL)
                    if json_match:
                        result_data = _json.loads(json_match.group())
                        top10 = result_data.get("top10", [])
                        best = result_data.get("best", {})
                    else:
                        top10 = []
                        best = {}

                    st.session_state.p1_channel_top10 = top10
                    st.session_state.p1_benchmark_channel = best
                    prog.progress(90, text="✅ Step 3+4 완료 — TOP10 선정 & 1순위 확정")

                    # 분석 대상 URL 자동 입력
                    if best.get("url"):
                        st.session_state.p1_channel_url = best["url"]
                        st.session_state.pipeline_state["selected_channel_url"] = best["url"]
                        st.session_state.pipeline_state["benchmark_channel"] = best

                    prog.progress(100, text="🏆 탐색 완료! 아래 결과를 확인하세요.")
                    save_workspace_state()
                    st.toast("🏆 채널 탐색 완료! 10개 채널이 선정되었습니다.", icon="🎯")

                except Exception as e:
                    st.error(f"채널 탐색 오류: {e}\n→ API Key 확인 또는 다른 모델을 선택해 보세요.")

        # ── TOP10 결과 표시 ───────────────────────────────────────
        if st.session_state.get("p1_channel_top10"):
            top10 = st.session_state.p1_channel_top10
            best = st.session_state.get("p1_benchmark_channel", {})

            with st.popover("🏆 탐색된 채널 10개 보기 (클릭)", use_container_width=True):
                st.markdown(f"""
                <div style="padding:8px 0;border-bottom:1px solid rgba(212,175,106,0.3);margin-bottom:10px;">
                    <span style="color:#d4af6a;font-size:1.0em;font-weight:700;">🏆 제미나이 큐레이션 TOP10</span>
                    <span style="color:#94a3b8;font-size:0.78em;margin-left:8px;">클릭 → 유튜브 채널 열림</span>
                </div>
                """, unsafe_allow_html=True)

                for ch in top10:
                    rank = ch.get("rank", "?")
                    name = ch.get("name", "채널명")
                    url = ch.get("url", "#")
                    region = ch.get("region", "")
                    trend = ch.get("trend", "")
                    reason = ch.get("reason", "")
                    score = ch.get("score", "")
                    is_best = (best.get("name") == name)

                    badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
                    trend_col = "#34d399" if trend == "급상승" else ("#fbbf24" if trend == "상승" else "#94a3b8")

                    st.markdown(f"""
                    <div style="background:rgba(30,15,5,{'0.95' if is_best else '0.6'});
                                border:1.5px solid rgba(212,175,106,{'0.7' if is_best else '0.2'});
                                border-radius:10px;padding:10px 14px;margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:0.95em;font-weight:700;color:{'#d4af6a' if is_best else '#f5e9d3'};">
                                {badge} {name}
                            </span>
                            <span style="color:{trend_col};font-size:0.78em;font-weight:600;">▲ {trend}</span>
                        </div>
                        <div style="color:#94a3b8;font-size:0.76em;margin-top:4px;">
                            {region} | {reason} | 점수: {score}
                        </div>
                        <a href="{url}" target="_blank" style="color:#60a5fa;font-size:0.76em;text-decoration:none;">
                            ▶ {url[:55]}...
                        </a>
                        {'<div style="color:#10B981;font-size:0.75em;font-weight:700;margin-top:4px;">✅ 벤치마킹 1순위 자동 확정</div>' if is_best else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"📌 [{rank}위] {name[:20]} 선택", key=f"p1_ch_select_{rank}", use_container_width=True):
                        st.session_state.p1_channel_url = url
                        st.session_state.p1_benchmark_channel = ch
                        st.session_state.pipeline_state["selected_channel_url"] = url
                        save_workspace_state()
                        st.toast(f"✅ [{rank}위] {name} 선택 완료!", icon="📌")
                        st.rerun()

        # ── 분석 대상 확정 ────────────────────────────────────────
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(30,15,5,0.8));
                    border:1.5px solid rgba(16,185,129,0.3);border-radius:10px;
                    padding:10px 14px;margin-top:8px;margin-bottom:4px;">
            <span style="color:#10B981;font-size:0.95em;font-weight:700;">🎯 [TARGET] 분석 대상 확정</span>
        </div>
        """, unsafe_allow_html=True)

        st.session_state.p1_channel_url = st.text_input(
            "타겟 유튜브 URL (탐색 완료 시 자동 입력)",
            value=st.session_state.get("p1_channel_url", ""),
            disabled=is_locked,
            key="p1_target_url_input"
        )
        st.session_state.p1_region = st.session_state.get("p1_region", "국내+국외 모두")

        if st.session_state.get("p1_channel_url"):
            if st.button("📊 벤치마킹 Step1 시작 →",
                         use_container_width=True, type="primary",
                         key="p1_to_benchmark_btn",
                         disabled=is_locked):
                st.session_state.pipeline_state["start_benchmarking"] = True
                st.session_state.pipeline_state["selected_channel_url"] = st.session_state.p1_channel_url
                save_workspace_state()
                st.toast("📊 벤치마킹 분석을 시작합니다!", icon="🚀")'''

old_count = content.count(old_search_section[:80])
print(f"[4] c_right 탐색기 섹션 검색: {'발견' if old_count > 0 else '미발견'}")

if old_count > 0:
    content = content.replace(old_search_section, new_search_section)
    print("[4] c_right 섹션 교체 완료!")
else:
    # 정확한 시작점만 찾아서 끝까지 교체
    start_marker = '        st.markdown("##### [SEARCH] 떡상 채널 발굴용 탐색기")'
    end_marker = '        st.session_state.p1_region = st.selectbox("타겟 지역", ["국내+국외 모두", "국내 우선", "국외 우선"], disabled=is_locked)'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx >= 0 and end_idx >= 0:
        end_pos = end_idx + len(end_marker)
        old_block = content[start_idx:end_pos]
        print(f"[4] 대안 방법 — 블록 크기: {len(old_block)}자")
        content = content[:start_idx] + new_search_section + content[end_pos:]
        print("[4] c_right 섹션 교체 완료 (대안)!")
    else:
        print(f"[4] 시작: {start_idx}, 끝: {end_idx}")

# =============================================================================
# 저장
# =============================================================================
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n[저장] 줄 수: {len(content.splitlines())}")

# 컴파일
result = subprocess.run(
    ['C:\\Python314\\python.exe', '-m', 'py_compile', target_file],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if result.returncode == 0:
    print("COMPILE: OK!")
else:
    print(f"COMPILE ERROR: {result.stderr[:600]}")
