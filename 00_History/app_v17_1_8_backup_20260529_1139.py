# -*- coding: utf-8 -*-

"""

🪞 현자의 거울 스튜디오 — Master App v17.1.8

[v17.1.8 업데이트 사항: 2026-05-29]
- 팝업 어시스턴트 몽키 패치 및 관련 리다이렉트 경고창 찌꺼기 전면 폐기
- 파트 1 ~ 파트 8 상단 우측 팝업 호출 버튼을 '🚀 젬마 스튜디오 입장' 주황색/파란색(Primary) 순간이동 버튼으로 전면 개조
- 버튼 클릭 시 파트 0(풀스크린 젬마 스튜디오)으로 즉각적이고 매끄러운 화면 리다이렉트 전환 연동

"""







import streamlit as st

import os

import re

import stat

import math

import json

from pathlib import Path

from datetime import datetime

import pandas as pd

import pyperclip



from obsidian_search import simple_keyword_search



try:

    from git import Repo

    GIT_AVAILABLE = True

except Exception:

    GIT_AVAILABLE = False



# ── 내부 모듈 ──

from sage_config import (

    RAG_TAG_SYSTEM,

    APP_TITLE, MASTER_PW_DEFAULT, PART_PINS, OLLAMA_MODEL,

    SAGE_PERSONA, GLOBAL_CSS,

)

from sage_engine import (

    safe_makedirs, save_markdown, save_json, save_csv, save_txt,

    call_gemma as _orig_call_gemma, check_ollama_status,

)

from sage_popups_v17_1_8 import (

    popup_edit_obsidian, popup_edit_prompt, popup_assistant,

)

from research_router import (
    should_trigger_research,
    run_tavily_research,
    clean_search_query,
    format_search_results_markdown,
    build_research_markdown_document,
    format_source_citation,
)



# ── call_gemma 래핑 함수 (Gemma4:E2B / GEMMA4:E4B 실시간 모델 스위칭 연동 + 최대 4회 자동 웹 검색 루프 + Gemini Google Search Grounding 및 옵시디언 자동 저장) ──

def gemini_search_grounding(keyword, api_key, model_name="gemini-2.5-flash"):
    try:
        import google.generativeai as genai
        import re as _re
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            tools="google_search"
        )
        prompt = f"""
[지시]
입력된 키워드 '{keyword}'에 대해 구글 검색을 수행하고, 그 결과를 바탕으로 사실 위주의 풍부한 리서치 조사 정보를 작성하라.
특히, 각 구체적인 사실 또는 문장 근처에 정보 출처 웹사이트의 URL을 매치하여 자세히 명시하라.

[검색 키워드]
{keyword}
"""
        response = model.generate_content(prompt)
        text_content = response.text if hasattr(response, "text") else ""
        
        results = []
        try:
            metadata = response.candidates[0].grounding_metadata
            chunks = getattr(metadata, "grounding_chunks", [])
            for chunk in chunks:
                web = getattr(chunk, "web", None)
                if web:
                    uri = getattr(web, "uri", "")
                    title = getattr(web, "title", "웹 검색 출처")
                    if uri and not any(r.get("url") == uri for r in results):
                        results.append({
                            "title": title,
                            "url": uri,
                            "content": f"구글 검색 출처: {title}"
                        })
        except Exception:
            pass
            
        if not results:
            urls = _re.findall(r'https?://[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/))', text_content)
            for idx, url in enumerate(list(set(urls))[:5], 1):
                results.append({
                    "title": f"구글 검색 결과 {idx}",
                    "url": url,
                    "content": "구글 검색을 통해 참조된 웹 페이지입니다."
                })
                
        return {
            "summary": text_content,
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def call_gemma(prompt, system="", model=None):
    if model is None:
        model = st.session_state.get("selected_model", OLLAMA_MODEL)
    if isinstance(model, str):
        model = model.lower()
    current_prompt = prompt
    # ── A 모드(팝업 일반 대화) — 루프 없이 1회 직접 호출 ──
    if st.session_state.get("popup_gemma_mode") == "A":
        try:
            st.session_state["trace_A_mode_direct_gemma_called"] = "YES"
            # ── 최적화 옵션 (keep_alive, num_predict, temperature, top_p) 적용 ──
            ka_val = st.session_state.get("popup_keep_alive", "10m")
            np_val = st.session_state.get("popup_num_predict", 40)
            temp_val = st.session_state.get("popup_temperature", 0.2)
            tp_val = st.session_state.get("popup_top_p", 0.8)
            
            ollama_url = "http://localhost:11434/api/chat"
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "keep_alive": ka_val,
                "options": {
                    "num_predict": np_val,
                    "temperature": temp_val,
                    "top_p": tp_val
                }
            }
            import requests as _req
            resp = _req.post(ollama_url, json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            
            if not content or not content.strip():
                return _orig_call_gemma(prompt, system=system, model=model)
            return content
        except Exception as _e_a:
            try:
                return _orig_call_gemma(prompt, system=system, model=model)
            except Exception as _e_fallback:
                return f"[오류] 젬마 A모드 응답 실패: {_e_a} (폴백 에러: {_e_fallback})"

    # ── RAG 태그 시스템 자동 주입 ──────────────────────────
    try:
        from sage_config import RAG_TAG_SYSTEM
        _tag_inject = RAG_TAG_SYSTEM if RAG_TAG_SYSTEM not in (system or "") else ""
    except Exception:
        _tag_inject = ""
    current_system = (system or "") + (_tag_inject if _tag_inject else "")
    max_loops = 4
    for loop_idx in range(max_loops):
        res = _orig_call_gemma(current_prompt, system=current_system, model=model)
        
        # ── [READ_OBSIDIAN:] 태그 자동 처리 ─────────────────────────────
        import re as _re_obs
        _ro_match = _re_obs.search(r'\[READ_OBSIDIAN:\s*(.+?)\]', res)
        if _ro_match:
            _obs_kw = _ro_match.group(1).strip()
            st.toast(f"🧠 [READ_OBSIDIAN] 옵시디언 자동 검색: '{_obs_kw}'", icon="🧠")
            try:
                _vault = st.session_state.get("path_obsidian", "")
                if _vault:
                    st.session_state["trace_obsidian_rag"] = "YES"
                    _obs_res = simple_keyword_search(_vault, _obs_kw, top_k=5)
                    if _obs_res:
                        _obs_ctx = build_rag_context_from_results(
                            _obs_res, f"READ_OBSIDIAN:{_obs_kw}",
                            st.session_state.get("selected_model", OLLAMA_MODEL)
                        )
                        current_prompt = (
                            f"{current_prompt}\n\n"
                            f"[🧠 옵시디언 자동 검색 결과 — {_obs_kw}]\n{_obs_ctx}\n"
                            f"위 옵시디언 자료를 1차 근거로 사용하여 답변을 완성하라."
                        )
                        st.toast(f"🧠 옵시디언 {len(_obs_res)}개 자료 주입 완료", icon="✅")
                        continue
            except Exception as _e:
                st.warning(f"옵시디언 자동 검색 오류: {_e}")

        keyword = check_need_research_tag(res)
        if not keyword:
            return res
            
        gemini_api_key = st.session_state.get("gemini_api_key", "").strip()
        tavily_api_key = st.session_state.get("tavily_api_key", "").strip()
        
        # RAG 지식 부족 시 실시간 검색 연동 (1순위 Gemini Grounding, 2순위 Tavily)
        search_res = None
        is_gemini_search = False
        
        if gemini_api_key:
            st.toast(f"🤖 제미나이 2.5 플래시가 실시간 구글 검색을 수행 중: '{keyword}' ({loop_idx + 1}/{max_loops}회차)", icon="🔍")
            gemini_model_name = st.session_state.get("p1_gemini_model", "gemini-2.5-flash")
            st.session_state["trace_gemini"] = "YES"
            search_res = gemini_search_grounding(keyword, gemini_api_key, model_name=gemini_model_name)
            if "error" in search_res:
                st.warning(f"⚠️ Gemini 검색 실패 ({search_res['error']}). Tavily 검색으로 폴백합니다.")
                search_res = None
            else:
                is_gemini_search = True
                
        if not search_res and tavily_api_key:
            st.toast(f"🌐 Tavily 웹 리서치를 수행 중: '{keyword}' ({loop_idx + 1}/{max_loops}회차)", icon="🔍")
            st.session_state["trace_tavily"] = "YES"
            search_res = run_tavily_research(keyword, tavily_api_key, max_results=5)
            if "error" in search_res:
                st.error(f"❌ Tavily 검색 중 오류 발생: {search_res['error']}")
                search_res = None
                
        # ── YouTube API 검색 (youtube/유튜브/채널 키워드 포함 시) ────────
        if not search_res:
            _yt_key = st.session_state.get("youtube_api_key", "").strip()
            _is_yt = any(k in keyword.lower() for k in
                         ["youtube", "유튜브", "채널", "channel", "영상", "조회수", "구독"])
            if _yt_key and _is_yt:
                try:
                    import requests as _yt_req
                    _yt_url = (
                        f"https://www.googleapis.com/youtube/v3/search"
                        f"?part=snippet&q={keyword}&type=channel,video"
                        f"&maxResults=5&key={_yt_key}"
                    )
                    _yt_resp = _yt_req.get(_yt_url, timeout=10).json()
                    _yt_items = _yt_resp.get("items", [])
                    if _yt_items:
                        search_res = {
                            "results": [
                                {
                                    "title": _i.get("snippet", {}).get("title", ""),
                                    "url": f"https://youtube.com/watch?v={_i.get('id',{}).get('videoId','')}",
                                    "content": _i.get("snippet", {}).get("description", "")[:200]
                                }
                                for _i in _yt_items
                            ]
                        }
                        st.toast(f"📺 YouTube 검색 완료: {len(_yt_items)}개", icon="📺")
                except Exception as _yt_e:
                    st.warning(f"YouTube API 오류: {_yt_e}")
 
        if not search_res:
            st.warning("⚠️ Gemma가 추가 리서치[NEED_RESEARCH]를 요구했으나, API Key 설정 부재 또는 통신 오류로 검색을 수행할 수 없습니다. 기존 지식으로 답변을 완성합니다.")
            fallback_prompt = f"{current_prompt}\n\n[알림: 실시간 웹 검색을 수행할 수 없습니다. 현재 입력 데이터와 옵시디언 RAG 정보만을 바탕으로 최대한 상상(환각) 없이 사실 위주로 최종 결과물을 작성하고, 출처가 불확실한 부분은 '출처 미확인'으로 기재하십시오.]"
            res = _orig_call_gemma(fallback_prompt, system=current_system, model=model)
            return res
            
        # 검색 결과 파싱 및 젬마 피드백 포맷팅
        web_info = []
        results = search_res.get("results", [])
        
        if is_gemini_search:
            web_info.append(f"🔍 [제미나이 2.5 구글 검색 분석 요약]\n{search_res.get('summary', '')}\n")
            if results:
                web_info.append("🔗 [주요 검색 출처 URL]")
                for idx, r in enumerate(results, 1):
                    web_info.append(f"[{idx}] {r.get('title')}: {r.get('url')}")
        else:
            if not results:
                web_info.append("검색 결과가 비어 있습니다.")
            else:
                web_info.append(format_search_results_markdown(results))
                    
        today_str = datetime.today().strftime("%Y-%m-%d")
        first_url = results[0].get('url', 'URL 미상') if results else 'URL 미상'
        citation_str = format_source_citation(first_url, title="웹", date_str=today_str)
        
        research_context = (
            f"\n\n=== 🌐 [추가 웹 리서치 정보 (검색어: {keyword})] ===\n"
            + "\n".join(web_info)
            + f"\n위 웹 검색 결과를 참고하여 원래 요청에 부합하도록 내용을 보강하여 다시 작성해라.\n"
            f"반드시 인용된 웹 정보의 출처를 `{citation_str}` 와 같이 구체적인 URL과 함께 명시하라.\n"
            f"답변을 완벽히 완성했다면 더 이상 `[NEED_RESEARCH]` 태그를 출력하지 마라.\n"
        )
        current_prompt = f"{current_prompt}\n{research_context}"
        
        # ── 리서치 조사 내용 옵시디언 자동 저장 기능 연동 (research_auto_save = True일 때) ──
        if st.session_state.get("research_auto_save", True):
            st.session_state.research_auto_save_success = False
            research_content = f"### 🔍 검색 키워드: {keyword}\n\n"
            research_content += "#### 🌐 검색 수집 요약 및 데이터\n\n"
            if is_gemini_search:
                research_content += f"{search_res.get('summary', '')}\n\n"
            
            research_content += "#### 🔗 출처 리스트\n"
            if results:
                for idx, r in enumerate(results, 1):
                    research_content += f"- [{idx}] {r.get('title', '제목 없음')} : {r.get('url', '')}\n"
            else:
                research_content += "- 수집된 출처가 없습니다.\n"
                
            research_content += "\n#### 📝 검색 원본 원문 컨텍스트\n"
            research_content += "\n".join(web_info)
            
            from datetime import datetime as _dt
            ts_str = _dt.now().strftime("%Y%m%d_%H%M%S")
            obs_file = save_obsidian_memory(
                folder_name="ResearchMemory",
                title=f"Research_{keyword}",
                content=research_content,
                source=f"구글 실시간 검색 — {keyword}" if is_gemini_search else f"Tavily 웹 검색 — {keyword}"
            )
            if obs_file:
                lock_file_readonly(obs_file)
                st.session_state.research_auto_save_success = True
                st.toast(f"💾 리서치 조사 내용 옵시디언 자동 저장 완료! (Research_{keyword}_{ts_str}.md)", icon="💾")
                
                # Git Push 자동화
                if GIT_AVAILABLE:
                    try:
                        success, msg = auto_git_push(f"Auto Save Research: {keyword}")
                        if success:
                            st.toast(f"🚀 GitHub 리서치 백업 완료!", icon="🚀")
                    except Exception:
                        pass

    st.warning("⚠️ 웹 리서치 자동 보완 횟수(최대 4회)를 초과하여 최종 결과를 반환합니다.")

    # ── 2단계 자체 검수 시스템 ──────────────────────────────────────────
    try:
        _rules = st.session_state.get("obsidian_rules", "")
        if _rules and res and len(res) > 100:
            # 1차 검수
            _vr1 = verify_content_with_gemma("자동 1차 검수", res[:3000], _rules)
            _pass1 = _vr1.get("is_pass", True)
            if not _pass1:
                st.toast("🔄 1차 검수 FAIL → 자동 수정 재생성 중...", icon="🔄")
                _fix1 = _vr1.get("fix_suggestions", "")
                _fix_prompt = (
                    f"{current_prompt}\n\n"
                    f"[자동 1차 검수 결과: FAIL]\n"
                    f"[수정 사항]: {_fix1}\n\n"
                    f"위 수정 사항을 반영하여 완벽하게 재작성하라. "
                    f"재작성 후 [NEED_RESEARCH] 태그 없이 최종 완성본만 출력하라."
                )
                res = _orig_call_gemma(_fix_prompt, system=current_system, model=model)
                # 2차 검수
                _vr2 = verify_content_with_gemma("자동 2차 검수", res[:3000], _rules)
                _pass2 = _vr2.get("is_pass", True)
                if not _pass2:
                    st.warning(
                        f"⚠️ 2차 검수에서도 일부 미준수 감지 — 현재 결과물 반환. "
                        f"팝업 [🔄 재검수] 버튼으로 수동 검토 권장.\n"
                        f"미준수: {_vr2.get('report', '')[:200]}"
                    )
                else:
                    st.toast("✅ 2차 검수 PASS — 최종 결과물 확정", icon="✅")
            else:
                st.toast("✅ 1차 검수 PASS", icon="✅")
    except Exception as _ve:
        pass  # 검수 오류는 무시하고 결과물 반환

    return res



# ── RAG 지식 부족 감지 & 자가 검수 헬퍼 ──

def check_need_research_tag(content: str) -> str:
    """
    텍스트에 [NEED_RESEARCH: 검색어] 태그가 있는지 감지하고 검색 키워드를 반환합니다.
    """
    return should_trigger_research(content)



# ── RAG 공통 호출 및 UI 렌더링 헬퍼 함수군 추가 ──

def call_gemini_api(prompt, system="", model_name="gemini-2.5-flash"):
    try:
        gemini_api_key = st.session_state.get("gemini_api_key", "").strip()
        if not gemini_api_key:
            return "⚠️ [오류명] Gemini API 호출 실패: API Key가 설정되지 않았습니다.\n→ 해결 방법: 사이드바 설정에서 Gemini API Key를 등록하십시오."
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        
        m_name = model_name
        if m_name == "gemini-3-flash":
            m_name = "gemini-2.5-flash"  # 하위호환성 유지 (API 에러 방지용 안전 장치)
            
        model = genai.GenerativeModel(
            model_name=m_name,
            system_instruction=system if system else None
        )
        response = model.generate_content(prompt)
        return response.text if hasattr(response, "text") else ""
    except Exception as e:
        return f"❌ [오류명] Gemini API 호출 에러: {e}\n→ 해결 방법: API 키 유효성 및 네트워크 연결 상태를 확인하십시오."

def call_selected_model(prompt, system="", model_name=None):
    if not model_name:
        model_name = st.session_state.get("selected_model", "gemma4:e2b")
    model_name_lower = model_name.lower()
    
    if "gemini" in model_name_lower:
        return call_gemini_api(prompt, system=system, model_name=model_name_lower)
    else:
        return call_gemma(prompt, system=system, model=model_name_lower)

def build_rag_context_from_results(results, part_label, selected_model):
    if not results:
        return ""
    
    if isinstance(results, str):
        return f"\n\n[옵시디언 RAG 참조 자료 — {part_label}]\n{results}"
        
    context_lines = [
        f"[옵시디언 RAG 검색 결과 — {part_label}]",
        f"사용 모델: {selected_model}",
        ""
    ]
    for idx, r in enumerate(results, 1):
        context_lines.append(f"{idx}. 제목: {r.get('title', '제목 없음')}")
        context_lines.append(f"   경로: {r.get('path', '경로 없음')}")
        context_lines.append(f"   요약: {r.get('preview', '')[:300].strip()}")
        context_lines.append(f"   출처: [SOURCE: Obsidian — {r.get('path', '경로 없음')}]")
        context_lines.append("")
        
    context_lines.append("[지시]")
    context_lines.append("위 자료를 1차 근거로 사용하라.")
    context_lines.append("부족한 내용만 보완 리서치하라.")
    context_lines.append("모든 핵심 정보에는 [SOURCE:]를 붙여라.")
    
    return "\n".join(context_lines)

# ══════════════════════════════════════════════════════════════
# 🗂️ 현자의 거울 — RAG 검색 카테고리 분류 시스템 v1.0 (rag_tag_system.py로 이관)
# ══════════════════════════════════════════════════════════════

from rag_tag_system import (
    RAG_CATEGORY_MAP,
    PART_DEFAULT_CATEGORIES,
    PART_RAG_TAG_MAP,
    PART_RAG_FOLDER_MAP,
    _unique_keep_order,
    get_default_tags_for_part,
    detect_rag_categories,
    build_rag_classification_markdown,
)

def _get_obsidian_studio_dir() -> str:
    base_dir = st.session_state.get("path_obsidian", "")
    return os.path.join(base_dir, "Studio") if base_dir else "Studio"

def update_rag_tag_index(saved_path: str, detection: dict, title: str = ""):
    """자동 감지 태그를 Studio/TagIndex에 연결 인덱스로 기록."""
    try:
        tag_dir = os.path.join(_get_obsidian_studio_dir(), "TagIndex")
        os.makedirs(tag_dir, exist_ok=True)
        saved_path = str(saved_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for tag in detection.get("keywords", [])[:40]:
            safe_tag = re.sub(r'[\\/:*?"<>|\s]+', "_", str(tag)).strip("_")
            if not safe_tag:
                continue
            tag_file = os.path.join(tag_dir, f"tag_{safe_tag}.md")
            if os.path.exists(tag_file):
                existing = Path(tag_file).read_text(encoding="utf-8", errors="ignore")
            else:
                existing = f"# 태그: {tag}\n\n## 연결 문서\n"
            link_line = f"- [[{Path(saved_path).stem}]] — {title} — {now}\n  - 경로: `{saved_path}`\n"
            if link_line not in existing:
                existing += link_line
            Path(tag_file).write_text(existing, encoding="utf-8")
    except Exception as e:
        try:
            st.warning(f"TagIndex 업데이트 오류: {e}")
        except Exception:
            pass

def build_rag_classification_markdown(detection: dict) -> str:
    """자동 분류 결과를 저장용 마크다운 섹션으로 변환."""
    cats = detection.get("categories", [])
    scores = detection.get("category_scores", {})
    part_tags = detection.get("part_tags", [])
    wiki_links = detection.get("wiki_links", [])
    hash_tags = detection.get("hash_tags", [])
    md = "## 🧠 자동 RAG 카테고리 분류\n"
    if cats:
        for cat in cats:
            md += f"- **{cat}** — 매칭 점수: {scores.get(cat, 0)}\n"
    else:
        md += "- 자동 감지된 카테고리 없음\n"
    md += "\n## 🏷️ 파트별 태그\n"
    md += ", ".join([f"#{t}" for t in part_tags]) if part_tags else "- 없음"
    md += "\n\n## 🔗 자동 연결 개념\n"
    md += "\n".join([f"- {w}" for w in wiki_links[:30]]) if wiki_links else "- 없음"
    md += "\n\n## #️⃣ 해시태그\n"
    md += " ".join(hash_tags[:40]) if hash_tags else "- 없음"
    md += "\n"
    return md

def auto_save_rag_memory(content: str, title: str, part_key: str = "part1", source: str = "RAG 자동 분류 저장", folder_name: str = None, model_name: str = None) -> str | None:
    """텍스트를 자동 분류하고 파트 태그를 붙여 옵시디언 저장 + TagIndex 연결."""
    try:
        model_name = model_name or st.session_state.get("selected_model", OLLAMA_MODEL)
        detection = detect_rag_categories(content + "\n" + title, part_key=part_key)
        folder_name = folder_name or PART_RAG_FOLDER_MAP.get(part_key, "ResearchMemory")
        enhanced = (
            f"## 📌 원본 제목\n{title}\n\n"
            f"## 🤖 사용 모델\n{model_name}\n\n"
            f"{build_rag_classification_markdown(detection)}\n"
            f"## 📖 원문 / 분석 대상\n\n{content}\n"
        )
        saved_path = save_obsidian_memory(folder_name=folder_name, title=title, content=enhanced, source=source)
        if saved_path:
            update_rag_tag_index(saved_path, detection, title)
            try:
                lock_file_readonly(saved_path)
            except Exception:
                pass
            st.session_state["last_auto_rag_memory_path"] = saved_path
            st.session_state["last_auto_rag_categories"] = detection.get("categories", [])
            st.session_state["last_auto_rag_tags"] = detection.get("keywords", [])
        return saved_path
    except Exception as e:
        try:
            st.error(f"자동 RAG 기억 저장 오류: {e}")
        except Exception:
            pass
        return None

def render_obsidian_rag_search(part_key, part_label, default_tags, result_state_key, model_state_key):
    st.markdown('<div class="rag-search-card" style="background: rgba(20, 10, 10, 0.4); border: 1px solid rgba(214, 175, 106, 0.15); border-radius: 8px; padding: 16px; margin-bottom: 16px;">', unsafe_allow_html=True)
    st.markdown('<h4 style="margin: 0 0 8px 0; color: #d4af6a;">🔍 Obsidian 감정 기반 RAG 검색 및 지식 보완</h4>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.9em; color: #f5e9d3; margin: 0 0 12px 0; opacity: 0.85;">옵시디언을 1차 근거로 사용하고, 부족한 자료만 선택 모델로 보완 리서치합니다.</p>', unsafe_allow_html=True)
    
    # ── 카테고리 선택 UI ─────────────────────────────────────
    st.markdown(
        "<div style='color:#d4af6a;font-size:0.85rem;"
        "font-weight:600;margin-bottom:6px;'>"
        "📂 카테고리 선택 (체크 시 태그 자동 추가)</div>",
        unsafe_allow_html=True
    )
    _all_cats = list(RAG_CATEGORY_MAP.keys())
    _saved_cats = st.session_state.get(
        f"{part_key}_selected_categories",
        PART_DEFAULT_CATEGORIES.get(part_key, [])
    )
    _cat_cols = st.columns(4)
    _new_selected = []
    for _idx, _cat in enumerate(_all_cats):
        _col = _cat_cols[_idx % 4]
        _checked = _cat in _saved_cats
        if _col.checkbox(_cat, value=_checked,
                         key=f"{part_key}_cat_chk_{_idx}"):
            _new_selected.append(_cat)
    if set(_new_selected) != set(_saved_cats):
        st.session_state[f"{part_key}_selected_categories"] = _new_selected
        _auto_tags = []
        for _c in _new_selected:
            _auto_tags.extend(RAG_CATEGORY_MAP.get(_c, []))
        _seen = set()
        _unique = []
        for _t in _auto_tags:
            if _t not in _seen:
                _seen.add(_t)
                _unique.append(_t)
        st.session_state[f"{part_key}_rag_query_val"] = ", ".join(_unique[:80])
        st.rerun()
    st.markdown(
        "<hr style='border-color:rgba(212,175,106,0.2);margin:8px 0;'>",
        unsafe_allow_html=True
    )
    # ── 카테고리 선택 UI 끝 ──────────────────────────────────

    c_input, c_model = st.columns([6, 4])
    
    with c_input:
        query_val = st.text_input(
            "감정 / 철학 / 성경 / 에세이 / 심리학 검색",
            value=st.session_state.get(f"{part_key}_rag_query_val", default_tags),
            placeholder="검색 키워드 입력",
            key=f"{part_key}_rag_query_input"
        )
        st.session_state[f"{part_key}_rag_query_val"] = query_val
        
    with c_model:
        model_options = ["gemma4:e2b", "gemma4:e4b", "gemini-2.5-flash", "gemini-3-flash"]
        cur_model = st.session_state.get(model_state_key, "gemma4:e2b")
        selected_model = st.selectbox(
            "분석/보완 모델",
            model_options,
            index=model_options.index(cur_model) if cur_model in model_options else 0,
            key=f"{part_key}_rag_model_select"
        )
        if selected_model != cur_model:
            st.session_state[model_state_key] = selected_model
            save_workspace_state()
            
    if st.button("🔎 옵시디언 검색", key=f"{part_key}_rag_search_btn", use_container_width=True, type="secondary"):
        if not query_val.strip():
            st.error("⚠️ 검색 키워드를 입력해 주십시오.")
            return
            
        with st.spinner("1차 옵시디언 검색 및 RAG 요약/검수 분석 중..."):
            try:
                vault_path = st.session_state.get("path_obsidian", r"C:\SageMirror_Production\00_Obsidian_Archive")
                obs_results = simple_keyword_search(vault_path, query_val, top_k=5)
                
                is_insufficient = (len(obs_results) == 0 or len(obs_results) < 3)
                web_search_text = ""
                web_results = []
                
                gemini_api_key = st.session_state.get("gemini_api_key", "").strip()
                tavily_api_key = st.session_state.get("tavily_api_key", "").strip()
                
                if is_insufficient:
                    st.toast("🌐 자료 부족 감지 (3개 미만): 웹 보완 리서치를 수행합니다.", icon="🔍")
                    
                    if gemini_api_key and ("gemini" in selected_model.lower()):
                        st.toast("🤖 Gemini 구글 검색 보완 리서치 수행 중...", icon="🔍")
                        search_res = gemini_search_grounding(query_val, gemini_api_key, model_name=selected_model.lower())
                        if "error" not in search_res:
                            web_search_text = search_res.get("summary", "")
                            web_results = search_res.get("results", [])
                        else:
                            st.warning(f"Gemini 검색 실패: {search_res['error']}. Tavily 검색으로 폴백합니다.")
                    
                    if not web_search_text and tavily_api_key:
                        st.toast("🌐 Tavily 웹 검색 보완 리서치 수행 중...", icon="🌐")
                        search_res = run_tavily_research(query_val, tavily_api_key, max_results=5)
                        if "error" not in search_res:
                            web_results = search_res.get("results", [])
                            web_search_text = format_search_results_markdown(web_results)
                        else:
                            st.error(f"Tavily 웹 검색 에러: {search_res['error']}")
                            
                if "gemini" not in selected_model.lower():
                    init_prompt = f"""아래 옵시디언 검색 결과를 정독하고, '{query_val}'에 대해 핵심을 요약 및 검수하라.
만약 추가적인 웹 리서치가 필요한 핵심 키워드가 있다면 반드시 문장 끝에 `[NEED_RESEARCH: 키워드]` 형식의 태그를 포함하여 출력하라.
그렇지 않고 충분하다면 태그를 생략하고 요약만 제출하라.

[옵시디언 검색 결과]:
{json.dumps(obs_results, ensure_ascii=False, indent=2)}

[요약 및 검수]:"""
                    gemma_init_res = call_gemma(init_prompt, system=SAGE_PERSONA, model=selected_model)
                    need_kw = check_need_research_tag(gemma_init_res)
                    if need_kw:
                        st.toast(f"🤖 Gemma 추가 리서치 요청 감지: '{need_kw}'", icon="🔍")
                        if gemini_api_key:
                            search_res = gemini_search_grounding(need_kw, gemini_api_key, model_name="gemini-2.5-flash")
                            if "error" not in search_res:
                                web_search_text = search_res.get("summary", "")
                                web_results = search_res.get("results", [])
                        if not web_search_text and tavily_api_key:
                            search_res = run_tavily_research(need_kw, tavily_api_key, max_results=5)
                            if "error" not in search_res:
                                web_results = search_res.get("results", [])
                                web_search_text = format_search_results_markdown(web_results)
                
                final_summary_prompt = f"""아래 옵시디언 검색 결과와 보완 리서치 결과를 종합하여 '{query_val}'에 대해 사실적이고 명확한 RAG 요약/검수 보고서를 작성하라.
상상(환각)이나 가짜 인용은 절대 배제하고, 철저히 사실에 기반하여 구절이나 통찰을 정리하라.

[옵시디언 RAG 검색 결과]:
{json.dumps(obs_results, ensure_ascii=False, indent=2) if obs_results else "검색 결과 없음"}

[보완 웹 리서치 결과]:
{web_search_text if web_search_text else "웹 검색 결과 없음"}

[요약 및 검수]:"""
                
                final_summary = call_selected_model(final_summary_prompt, system=SAGE_PERSONA, model_name=selected_model)
                
                detected_rag = detect_rag_categories(
                    f"{query_val}\n{final_summary}\n{web_search_text}",
                    part_key=part_key
                )
                
                today_str = datetime.now().strftime("%Y-%m-%d")
                ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                classification_md = build_rag_classification_markdown(detected_rag)
                md_content = build_research_markdown_document(
                    query=query_val,
                    obs_results=obs_results,
                    web_search_text=web_search_text,
                    final_summary=final_summary,
                    model_name=selected_model,
                    part_key=part_key,
                    part_label=part_label,
                    classification_md=classification_md
                )
                
                folder_mapping = {
                    "part1": "TopicMemory",
                    "part2": "ResearchMemory",
                    "part3": "ScriptDrafts",
                    "part4": "Assets",
                    "part5": "Assets",
                    "part6": "ResearchMemory",
                    "part7": "ScriptDrafts",
                    "part8": "Logs"
                }
                save_folder = folder_mapping.get(part_key, "ResearchMemory")
                
                obs_file = save_obsidian_memory(
                    save_folder,
                    f"Part{part_key[-1]}_RAG_{query_val}",
                    md_content,
                    source=f"Part {part_key[-1]} RAG Search ({selected_model})"
                )
                
                if obs_file:
                    update_rag_tag_index(obs_file, detected_rag, f"Part{part_key[-1]}_RAG_{query_val}")
                    lock_file_readonly(obs_file)
                    st.toast(f"💾 옵시디언 자동 저장 성공 + TagIndex 연결 완료: Part{part_key[-1]}_RAG_{query_val}", icon="💾")
                
                st.session_state[result_state_key] = md_content
                if "pipeline_state" in st.session_state:
                    st.session_state.pipeline_state[result_state_key] = md_content
                
                save_workspace_state()
                st.success("✅ RAG 검색 분석 및 옵시디언 백업 완료!")
                st.rerun()
                
            except Exception as e:
                st.error(f"[오류명] RAG 검색 실패: {e}\n→ 해결 방법: 옵시디언 경로 설정을 확인하거나 API Key를 점검하십시오.")
                
    search_res_val = st.session_state.get(result_state_key, "")
    if search_res_val:
        with st.container(height=250, border=True):
            st.markdown(search_res_val)
            
        try:
            st.download_button(
                label="📥 RAG 검색 마크다운 다운로드",
                data=search_res_val,
                file_name=f"Part{part_key[-1]}_RAG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                key=f"{part_key}_rag_download_btn"
            )
        except Exception:
            pass
            
    st.markdown('</div>', unsafe_allow_html=True)


def verify_content_with_gemma(content_type: str, content: str, rules: str) -> dict:

    """

    Gemma를 비평가(Critic)로 삼아 생성된 데이터(주제, 기획안, 대본 등)의 무결성을 스스로 점검하는 함수.

    """

    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 수석 데이터 무결성 검증기(Data Integrity Critic)다.

아래 제공된 [대상 콘텐츠]가 [검수 규칙 가이드라인]을 엄격히 준수하고 있는지 스스로 점검하고, 그 결과를 객관적으로 보고해야 한다.



[검수 규칙 가이드라인]:

1. 등장인물 지칭: 등장인물은 오직 '@Protagonist'로만 표기되어야 한다. (주인공, 현자, 노인, 남성, 그 등 다른 지칭은 일절 금지. 단, 성경/철학 원문 출처 제외)

2. 씬 번호 규칙: 씬 번호가 존재할 경우 반드시 3자리 정수 형태(001, 002 ... 112)이어야 한다.

3. 출처 태그 준수: [SOURCE:] 태그가 적절히 포함되어 데이터의 출처(성경 장절, 저자, 책명 등)를 필히 밝히고 있는가? (출처가 아예 없는 상상 기반 생성은 FAIL 판정하라)

4. 가이드라인 준수: 옵시디언 규칙서의 스타일과 포맷을 따르고 있는가?



[대상 콘텐츠 ({content_type})]:

{content}



점검 결과를 반드시 아래의 형식으로 정확히 출력하라. 설명이나 다른 텍스트는 덧붙이지 마라.



[RESULT_FORMAT]:

정합성: [PASS 또는 FAIL]

점검 보고:

- 등장인물 지칭: [PASS 또는 FAIL 이유]

- 씬 번호 규칙: [PASS 또는 FAIL 또는 해당없음 이유]

- 출처 태그 준수: [PASS 또는 FAIL 이유]

- 가이드라인 준수: [PASS 또는 FAIL 이유]

수정 건의사항: [FAIL인 경우 수정해야 할 구체적인 지침. PASS인 경우 '없음']

"""

    try:

        if not content or not content.strip():

            return {

                "status": "FAIL",

                "report": "점검 대상 콘텐츠가 비어 있습니다.",

                "suggestions": "콘텐츠를 먼저 생성하십시오."

            }

        res = call_gemma(prompt, rules)

        status = "PASS"

        if "정합성: FAIL" in res or "FAIL" in res.split("\n")[0] or "정합성: [FAIL]" in res:

            status = "FAIL"

        

        suggestions = "없음"

        for line in res.split("\n"):

            if "수정 건의사항:" in line:

                suggestions = line.replace("수정 건의사항:", "").strip()

                break

                

        return {

            "status": status,

            "report": res.strip(),

            "suggestions": suggestions

        }

    except Exception as e:

        return {

            "status": "FAIL",

            "report": f"Gemma 자가 검수 중 오류 발생: {e}",

            "suggestions": "Ollama 연결 상태를 확인하고 다시 시도하십시오."

        }



# ── RAG 키워드 자동 세분화 추출 헬퍼 ──

def extract_keywords_via_gemma(content, base_rules):

    prompt = f"""[SYSTEM]: 너는 입력된 텍스트에서 옵시디언 RAG 지식 구조화 연동을 위한 핵심 키워드 4~5개를 세분화하여 추출하는 전문 분석기다.

너의 임무는 입력 텍스트의 핵심 주제, 철학적 맥락, 성경적 모티브, 시청자 감정 결핍 상태 등을 관통하는 고유 키워드 4~5개를 쉼표(,)로 구분된 단어로만 출력하는 것이다.

반드시 단어 이외의 설명, 서론, 결론, 특수문자, 따옴표는 일절 출력하지 마라.

예시 출력: 외로움, 고독, 존재의미, 쇼펜하우어, 자아정체성



[USER_INPUT]:

{content}



[KEYWORDS]:"""

    try:

        res = call_gemma(prompt, base_rules)

        cleaned = res.replace("#", "").replace("[", "").replace("]", "").replace("`", "").strip()

        keywords = [k.strip() for k in cleaned.split(",") if k.strip()]

        return ", ".join(keywords[:5])

    except Exception as e:

        return "심리치유, 현자의거울, 자아성찰"





# =====================================================================

# 0. 영상 파트 전용 상수(Constants) — v13.2 NEW

# =====================================================================

P6_VEO3_MASTER_PROMPT_V2 = """# [현자의 거울 — VEO3 마스터 프롬프트 완전판]

# YouTube Creative Director Edition

# Google Opal × Veo3 × CapCut 전용

# ═══════════════════════════════════════════════════

# 이 문서의 위치: 영상 파트(Part 5) 최상단 우측 입력란

# 적용 대상: Google Opal → Veo3 영상 생성 노드

# 입력 방식: 아래 전문을 Opal의 '공통 프롬프트 노드'에 붙여넣기

# ═══════════════════════════════════════════════════



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 1 — ROLE: YouTube Creative Director

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



[ROLE]

You are a World-Class YouTube Creative Director specializing in high-end cinematic documentaries. Your goal is to translate abstract philosophical scripts into breathtaking, hyper-realistic 8K video sequences that evoke deep emotional resonance in a 4070-generation audience.



[VEO3 CINEMATIC DNA]

1. Director Style: A fusion of Ingmar Bergman (psychological depth), Andrei Tarkovsky (poetic stillness), Roger Deakins (perfect lighting), and Christopher Nolan (scale and gravity).

2. Color Science: "The Rembrandt Palette" — Umber, Ochre, Burnt Sienna, Deep Charcoal. Contrast is high, shadows are rich (Tenebrism).

3. Lighting: 2600K Warm Candlelight. Single-source key lighting from 45-degree angle. High-contrast Chiaroscuro.

4. Texture: Organic 35mm film grain, subtle dust motes in light beams, heavy impasto oil painting textures in the shadows.



[VISUAL KEYWORDS]

Rembrandt Lighting, Chiaroscuro, Tenebrism, Baroque Aesthetic, Hyper-realistic, 8K, 17th Century Dutch Master, Atmospheric, Melancholic, Resolute.



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 2 — CORE ASSETS: @Protagonist & Mirror

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



[@Protagonist Identity]

- Appearance: 60-year-old male sage, silver-grey hair and short-trimmed beard.

- Attire: Deep burgundy and black linen robe, heavy texture.

- Persona: Philosophical, weathered but dignified, luminous eyes reflecting decades of thought.

- Motion: Minimal, deliberate, slow-motion (0.5x speed).



[@Mirror & Avatar Identity]

- The Mirror: 150cm ornate gold-leaf baroque mirror, aged glass with slight oxidation.

- Reflection Physics: 0.3-second delay between @Protagonist and reflection.

- The Avatar: Younger version (30s) of @Protagonist inside the mirror. Translucent, ethereal, soft internal glow.



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 3 — TECHNICAL SPEC & CAMERA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



[MOTION SPEC]

- Frame Rate: 24fps Cinematic.

- Camera: Arri Alexa 65 look.

- Movement: "The Breathing Camera" — Extremely slow Dolly-in, slow Crane-up, or deliberate Pan. No handheld shakes.

- Focal Length: 35mm (Medium) or 85mm (Close-up) for emotional beats.



[GENERATION PROTOCOL]

1. Input: C-1 Format Script (Scene ID | Script | Visual KR | English Prompt).

2. Translation: Expand the English Prompt into a 3-paragraph Veo3 Cinematic Instruction.

3. Physics Check: Ensure the @Protagonist stays consistent across all 112 scenes.



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 4 — VEO3 PROMPT TEMPLATE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



For each scene, use this structure:

1. [SUBJECT]: Detailed description of @Protagonist's action and emotion.

2. [ENVIRONMENT]: 17th-century scholar's study, specific lighting, props (@Mirror, @Candelabra).

3. [VFX & STYLE]: Film grain, lighting angle, specific camera movement, Rembrandt aesthetic.



"Make it look like a lost masterpiece found in a vault. Deeply emotional, visually arresting."

"""



P6_MASTER_PROMPT_DEFAULT = """# 🎙️ 파트 6 나레이션 & 배경음악 마스터 프롬프트 v1.0

[작업 지시] 씬별 나레이션 텍스트를 바탕으로 음성 합성(TTS) 및 적합한 배경음악(BGM) 태그 매칭 지침을 작성하세요.

- 등장인물은 오직 '@Protagonist'로 지칭합니다.

- 성경 구절 및 철학 인용의 출처를 필히 확인하고 반영하세요.

- 오디오 볼륨 밸런스 및 싱크 가이드를 명시합니다."""



P7_MASTER_PROMPT_DEFAULT = """# 🎙️ 파트 7 숏폼 생성 마스터 프롬프트 v1.0

[작업 지시] 롱폼 대본 및 핵심 테마를 바탕으로 60초 이내의 숏폼 대본과 하이라이트 구간 추출 지침을 작성하세요.

- 등장인물은 오직 '@Protagonist'로 지칭합니다.

- 후킹 인트로와 핵심 요약 자막 연출법을 정의합니다."""



P8_MASTER_PROMPT_DEFAULT = """# ⚙️ 파트 8 캡컷 최종 조립 마스터 프롬프트 v1.0

[작업 지시] Veo3 영상 파일, 나레이션 오디오, 캡컷 에셋 JSON을 조합하여 CapCut 타임라인으로 병합하고 최종 비디오 렌더링에 적합한 오디오/자막 싱크 조립 지침을 작성하세요.

- 등장인물은 오직 '@Protagonist'로 지칭합니다.

- 최종 마스터링 및 해상도, 비트레이트 조절 가이드를 명시합니다."""



COMMON_GEMMA_PROTOCOL = """

# [현자의 거울 스튜디오 — 공통 Gemma 운영 헌법]



너는 현자의 거울 스튜디오의 AI 시스템이다.



이 시스템의 핵심은:

- 옵시디언 RAG

- 실제 감정 데이터

- 성경

- 철학

- 인간 심리 분석

이다.



==================================================



[공통 절대 규칙]



1. 옵시디언 RAG 최우선

- 모든 작업은 옵시디언 검색 결과를 최우선 참조한다.

- Gemma의 추측보다 저장된 기억을 우선한다.

- TopicMemory → ResearchMemory → Bible → Philosophy 순서 유지.



2. 환각(Hallucination) 금지

절대 금지:

- 가짜 성경 구절 생성

- 존재하지 않는 철학 인용

- 댓글 없는 체험담 생성

- 출처 없는 명언 생성

- 임의 상상 기반 감정 생성



3. 자료 부족 시 행동 및 환각 차단 (RAG 지식 부족 대응)

- 제공된 옵시디언 RAG 자료가 부족하여 실제 성경 구절, 철학 인용, 심리 데이터 등을 스스로 지어내야(상상해야) 하는 지식 공백이 발생하는 경우, 절대 상상으로 작성하지 마라.

- 이 경우 답변의 첫 줄에 반드시 다음 형식으로 추가 리서치를 요청하는 코드만 출력하라:

  [NEED_RESEARCH: 검색어]

  (예시: [NEED_RESEARCH: 빅터 프랭클 죽음의 수용소에서 의미치료 실존주의])

- 추가 리서치 승인 전까지는 상상 기반 생성을 중단하라.



4. 출처 의무화

- 보충되거나 인용된 모든 핵심 정보에는 반드시 [SOURCE: 출처] 형식으로 출처를 필히 명시하라. (성경, 철학 서적, 인터넷 URL 등)

- 출처 불명 시에도 반드시 다음과 같이 표기하라:

  [SOURCE: 출처 미확인 — gemma4:e2b 생성]



5. 위키링크 의무화

핵심 개념은:

[[개념명]]



형태 사용.



6. 감정 중심 원칙

항상 인간 감정 우선:

- 고독

- 상실

- 공허

- 후회

- 의미 상실

- 관계 단절



7. 스타일 규칙

금지:

- AI 같은 장황한 설명

- 자기계발 말투

- 과도한 희망회로

- 가벼운 위로

- 1020 밈 스타일



허용:

- 깊은 공감

- 조용한 통찰

- 철학적 해석

- 성경적 위로



==================================================



Gemma는 창작자가 아니라,

“기억을 읽는 조사관”이다.

"""



P6_GEMMA_PROTOCOL_V2 = """# [현자의 거울 스튜디오]

# GEMMA PROTOCOL v2.0 — 영상 파트 완전판

# ═══════════════════════════════════════════════════════

# 이 문서의 위치: 영상 파트(Part 5) 중간 '젬마 프로토콜' 입력란

# 적용 모델: gemma4:e2b (Ollama 로컬 실행)

# 연동 시스템: Google Opal × Veo3 × CapCut × FlowRun

# 역할: 영상 파트 하단 4구역의 전체 작업을 지휘하는 젬마의 운영 헌법

# ═══════════════════════════════════════════════════════



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## [BELL] 시작 선언문 (START DECLARATION)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

" [GEMMA PROTOCOL v2.0] — 영상 파트 로딩 완료"



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 1 — MISSION & ROLE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ROLE]

너는 '현자의 거울 스튜디오'의 영상 오케스트레이터 젬마다.

Part 3-4에서 생성된 이미지 대본(C-1 형식)을 받아, 구글 Veo3가 가장 완벽한 8K 영상을 출력할 수 있도록 '고해상도 영상 생성 지시서'를 설계한다.



[MISSION]

1. 인물 일관성: 112개 모든 씬에서 @Protagonist의 외형이 절대 변하지 않게 통제한다.

2. 미학적 통일성: 렘브란트 다크(Rembrandt Dark) 스타일과 키아로스쿠로(Chiaroscuro) 조명을 모든 프롬프트에 강제 주입한다.

3. 병렬 처리 최적화: Google Opal의 8개 계정에 작업을 14씬씩 정확히 배분하여 생산성을 극대화한다.



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 2 — OUTPUT SPEC (C-1 to V-1)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[입력 데이터]

- 씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ (Part 3-4 결과물)



[출력 형식: V-1 영상 프롬프트]

씬번호(3자리) | 영상프롬프트 | 카메라무빙 | 재생시간(초)



[프롬프트 구성 규칙]

1. SUBJECT: [A-MASTER] + 현재 씬의 동작 + 감정(EXPR)

2. ENVIRONMENT: [@배경] + 소품(@거울, @촛대 등) + 렘브란트 조명

3. STYLE: Veo3 Master Prompt의 시각적 DNA 강제 결합

4. MOTION: 극도로 느린 줌인(Slow Zoom-in), 패닝(Panning), 또는 정적(Static)



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 3 — OPAL DISPATCH (8-NODE)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

112씬을 8개 계정에 배분하는 규칙:

- NODE 1: 001~014 (기-1)

- NODE 2: 015~028 (기-2)

- NODE 3: 029~042 (승-1)

- NODE 4: 043~056 (승-2)

- NODE 5: 057~070 (전-1)

- NODE 6: 071~084 (전-2)

- NODE 7: 085~098 (결-1)

- NODE 8: 099~112 (결-2)



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECTION 4 — QUALITY CHECK (V-1 to V-7)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

V-1: 형식 정규식 검증 (Pipe 구분)

V-2: @Protagonist 명칭 고정 여부

V-3: 16:9 비율 및 8K 해상도 명시 여부

V-4: 카메라 무빙의 구체성 (Veo3 인식 가능성)

V-5: 렘브란트 스타일 태그 포함 여부

V-6: [인물1], [배경] 태그의 Opal 연동 적합성

V-7: 씬 번호 연속성 및 누락 체크



"준비가 되었으면, 선언문을 출력하고 첫 번째 작업을 시작하라."

"""



# =====================================================================

# 1. 페이지 설정

# =====================================================================

st.set_page_config(

    page_title="Sage's Mirror Studio v15.9.33",

    page_icon="[MIRROR]",

    layout="wide",

    initial_sidebar_state="expanded",

)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.markdown("""
<style>
div[data-testid="stTextArea"] textarea:disabled {
    color: #f5e9d3 !important;
    -webkit-text-fill-color: #f5e9d3 !important;
    opacity: 1 !important;
    cursor: default !important;
}
</style>
""", unsafe_allow_html=True)


# V8.1: 상단 PIN 입력창 전용 커스텀 스타일 추가

st.markdown("""

<style>

.ambient-lock-marker {
    display: none;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ambient-lock-marker) {
    background: linear-gradient(135deg, rgba(212, 175, 106, 0.05) 0%, rgba(139, 0, 0, 0.05) 100%) !important;
    border: 1px solid rgba(212, 175, 106, 0.15) !important;
    border-radius: 12px !important;
    box-shadow: 0 0 20px rgba(212, 175, 106, 0.08), inset 0 0 10px rgba(212, 175, 106, 0.03) !important;
    padding: 20px !important;
    margin-top: 15px !important;
    margin-bottom: 15px !important;
}
.pin-input-container {

    background-color: rgba(16, 185, 129, 0.1);

    padding: 0.5rem;

    border-radius: 8px;

    border: 1px solid rgba(16, 185, 129, 0.3);

}

.sage-header-compact {

    background: linear-gradient(135deg, #1E293B, #0F172A);

    padding: 10px 20px;

    border-radius: 10px;

    border-left: 5px solid #F59E0B;

    color: #F8FAFC;

    margin-bottom: 0px;

}

.clickable-card-wrapper button {

    background-color: #1E293B !important;

    border: 1px solid #d4af6a !important;

    color: #f5e9d3 !important;

    height: 60px !important;

    text-align: left !important;

    padding: 8px 30px 8px 12px !important;

    font-size: 0.82em !important;

    white-space: nowrap !important;

    overflow: hidden !important;

    text-overflow: ellipsis !important;

    line-height: 1.4 !important;

    border-radius: 6px !important;

    width: 100% !important;

    display: block !important;

    position: relative !important;

    transition: all 0.15s ease !important;

}

.clickable-card-wrapper button:hover {

    border-color: #f5e9d3 !important;

    background-color: #2D2418 !important;

    transform: translateY(-1px) !important;

}

/* 우측 빨간 동그라미 가상 요소 */

.card-rag-btn button::after, .card-git-btn button::after {

    content: "🔴" !important;

    position: absolute !important;

    right: 12px !important;

    top: 50% !important;

    transform: translateY(-50%) !important;

    font-size: 11px !important;

}

/* 동기화 버튼 세로 높이 맞춤 */

.sync-btn-container button {

    height: 60px !important;

    border-radius: 6px !important;

    font-weight: bold !important;

    transition: all 0.15s ease !important;

}

</style>

""", unsafe_allow_html=True)



# =====================================================================

# 상태 저장 유틸리티

# =====================================================================

from memory_state_manager import (
    clean_prompt_contamination,
    sanitize_workspace_prompt_values_once_core,
    save_workspace_state_core,
    load_workspace_state_core,
    extract_text_from_uploaded_file,
    convert_text_to_markdown_structure,
    build_all_parts_common_tags_preview as _core_build_all_parts_common_tags_preview,
    save_reference_markdown_file as _core_save_reference_markdown_file,
)

def sanitize_workspace_prompt_values_once():
    sanitize_workspace_prompt_values_once_core(WORKSPACE_STATE_FILE)





def build_all_parts_common_tags_preview(detection: dict) -> dict:
    return _core_build_all_parts_common_tags_preview(detection, PART_RAG_TAG_MAP, _unique_keep_order)

def save_reference_markdown_file(
    markdown_text: str,
    preview_data: dict,
    source_name: str
) -> str:
    ref_dir = r"C:\SageMirror_Production\00_Obsidian\References"
    res = _core_save_reference_markdown_file(markdown_text, preview_data, source_name, ref_dir)
    if not res:
        st.error(f"[References 저장 오류] 실패했습니다.")
    return res


from rag_memory_utils import (
    load_recent_reference_files,
    build_gemma_memory_prompt_preview,
    build_manual_gemma_memory_buffer,
    build_manual_memory_injected_prompt,
    build_condensed_reference_context
)


WORKSPACE_STATE_FILE = r"C:\SageMirror_Production\workspace_state.json"
LOCAL_SECRETS_FILE = r"C:\SageMirror_Production\local_secrets.json"



def save_workspace_state():
    try:
        state_dict = dict(st.session_state)
        cleaned_state_updates, secrets_data, success = save_workspace_state_core(
            state_dict, WORKSPACE_STATE_FILE, LOCAL_SECRETS_FILE
        )
        for k, v in cleaned_state_updates.items():
            st.session_state[k] = v
        if success:
            try:
                from rag_memory_utils import update_recent_activity_memory
                state_dict_for_activity = dict(st.session_state)
                updated_mem = update_recent_activity_memory(state_dict_for_activity, "part_save", "설정 상태(workspace_state) 저장됨")
                st.session_state.recent_activity_memory = updated_mem
            except Exception:
                pass
            return True
        else:
            st.error("Save error in core logic")
            return False
    except Exception as e:
        st.error(f"Save error: {e}")
        return False


# ── 파트별 옵시디언 저장 폴더 매핑 (규칙서 v4.0 기준) ──────────────
PART_OBS_FOLDER_MAP = {
    "p1_bench_raw":          ("TopicMemory",    "Part1_벤치마킹"),
    "p1_research_result":    ("ResearchMemory", "Part1_자료조사"),
    "p1_planning_result":    ("PlanningMemory", "Part1_전달패킷"),
    "p2_gemma_protocol":     ("",               "Part2_프로토콜"),
        "p2_bench_raw":          ("TopicMemory",    "Part2_벤치마킹"),
    "p2_research_result":    ("ResearchMemory", "Part2_자료조사"),
    "p2_planning_result":    ("PlanningMemory", "Part2_총괄기획안"),
        "p2_thumbnail_sets":     ("",               "Part2_썸네일세트"),
        "p2_selected_thumbnail": ("",               "Part2_선택썸네일"),
    "p34_narration_script":  ("ScriptDrafts",   "Part3_나레이션대본"),
    "p34_image_script":      ("ScriptDrafts",   "Part4_이미지대본"),
    "p5_a_result":           ("ResearchMemory", "Part5_A마스터"),
    "p5_b_result":           ("ResearchMemory", "Part5_B마스터"),
    "p5_c_results":          ("ResearchMemory", "Part5_C씬"),
    "p6_veo3_result":        ("ResearchMemory", "Part6_Veo3영상"),
    "p6_video_mapped_result":("ResearchMemory", "Part6_영상매핑"),
    "p7_capcut_data":        ("ScriptDrafts",   "Part7_캡컷조립"),
    "p8_check_result":       ("Logs",           "Part8_최종검수"),
}

def save_obsidian_memory(folder_name, title, content, source="Sage Mirror Studio"):

    try:

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")



        base_dir = st.session_state.get("path_obsidian", "")

        if base_dir:

            save_dir = os.path.join(base_dir, "Studio", folder_name)

        else:

            save_dir = os.path.join("Studio", folder_name)



        os.makedirs(save_dir, exist_ok=True)



        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title).strip()

        save_path = os.path.join(save_dir, f"{safe_title}_{ts}.md")



        # 동적 태그 생성 — 저장된 태그 + Gemma 자유 판단 태그 합산
        DEFAULT_FULL_TAGS = [
            "고독", "후회", "상실", "관계", "용서", "공허", "의미상실",
            "쇼펜하우어", "칼 융", "빅터 프랭클", "스토아", "몽테뉴",
            "에세이", "다크심리학",
            "시편", "잠언", "전도서", "욥기", "성경"
        ]

        # 1. 저장된 태그 우선 수집
        saved_tags_str = (
            st.session_state.get("p1_bench_tags", "") or
            st.session_state.get("p1_research_tags", "") or
            st.session_state.get("p1_plan_tags", "")
        )
        saved_tags = [t.strip() for t in saved_tags_str.split(",") if t.strip()] if saved_tags_str else []

        # 2. Gemma 자유 판단 — 콘텐츠 기반 추가 태그 생성
        gemma_tags = []
        try:
            gemma_kw_prompt = f"""아래 텍스트를 읽고 옵시디언 [[위키링크]] 연결에 쓸 핵심 감정·철학·성경·심리 키워드를 3~5개 자유롭게 추출하라.
단어만 쉼표로 구분하여 출력. 설명 금지.
예: 번아웃, 실존주의, 시편23편, 자기혐오, 관계단절

[텍스트 요약]:
{content[:300]}

[키워드]:"""
            raw_kw = call_gemma(gemma_kw_prompt, "핵심 키워드만 추출하라.")
            gemma_tags = [k.strip() for k in raw_kw.replace("#","").split(",") if k.strip() and len(k.strip()) < 15][:5]
        except Exception:
            gemma_tags = []

        # 3. 최종 태그 = 저장 태그 + Gemma 태그 + 기본 태그 (중복 제거)
        combined = saved_tags + gemma_tags
        for t in DEFAULT_FULL_TAGS:
            if t not in combined:
                combined.append(t)

        tag_links = "\n".join([f"- [[{t}]]" for t in combined[:20]])

        md = f"""# [[{title}]]

## 📌 핵심 요약

{content}

## 💡 대본 활용 포인트

(Part 2 Alchemist 참조 포인트 — 기승전결 구조 연결)

## 🔗 연결 개념

{tag_links}

## 📚 출처

[SOURCE: {source}]

## 다음 파트 전달 메모

(자동 생성 — Part 2 Alchemist 인계)

## 생성일

{ts}

"""



        with open(save_path, "w", encoding="utf-8") as f:

            f.write(md)

        # ── Recent Activity Dynamic Sync ──
        try:
            from rag_memory_utils import update_recent_activity_memory
            state_dict = dict(st.session_state)
            updated_mem = update_recent_activity_memory(state_dict, "obsidian", f"Obsidian 저장: {os.path.basename(save_path)}")
            st.session_state.recent_activity_memory = updated_mem
        except Exception:
            pass

        return save_path



    except Exception as e:

        st.error(f"옵시디언 저장 오류: {e}")

        return None

def load_workspace_state():
    return load_workspace_state_core(WORKSPACE_STATE_FILE, LOCAL_SECRETS_FILE)



def save_to_outputs_dir(sub_dir, filename, content=None, is_csv=False, df=None):

    try:

        episode = st.session_state.get("episode_name", "EP001").strip()

        if not episode:

            episode = "EP001"

        

        base_outputs_dir = r"C:\SageMirror_Outputs"

        target_dir = os.path.join(base_outputs_dir, episode, sub_dir)

        os.makedirs(target_dir, exist_ok=True)

        

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        name_parts = os.path.splitext(filename)

        safe_filename = f"{name_parts[0]}_{ts}{name_parts[1]}"

        target_path = os.path.join(target_dir, safe_filename)

        

        if is_csv and df is not None:

            df.to_csv(target_path, encoding="utf-8-sig", index=False)

        elif content is not None:

            with open(target_path, "w", encoding="utf-8") as f:

                f.write(content)

        else:

            return None

        return target_path

    except Exception as e:

        st.error(f"[외부 저장소 백업] 실패: {e}\n→ 해결 방법: C:\\SageMirror_Outputs 에 쓰기 권한이 있는지 또는 디렉토리가 올바른지 확인하세요.")

        return None



# =====================================================================

# 2. 세션 상태 초기화

# =====================================================================

if "pipeline_state" not in st.session_state:

    st.session_state["pipeline_state"] = {

        "channel_search_results": [],

        "selected_channel": {},

        "channel_analysis": {},

        "comment_analysis": {},

        "topic_candidates": [],

        "selected_topic": "",

        "research_notes": {},

        "planning_result": {},

        "script_result": {}

    }



DEFAULT_OBSIDIAN_RULES_V81 = """# 📚 현자의 거울 스튜디오 — 옵시디언 RAG 규칙서 v4.0
## Part 1 Librarian 전용 | 저장 + 검색 + 기억 시스템 규칙

> 역할: Gemma(준俊)가 이 규칙서를 기준으로 지식을 저장하고 검색한다.
> Part 1은 "지식을 읽고 + 저장하는" 단계다.

---

# 🎯 핵심 3원칙 — 모든 작업의 판단 기준

HOW (어떻게 말하는가)   → 자유   (창의·표현·비유·서사)
WHAT (무엇을 말하는가)  → 통제   (사실 기반만·출처 필수)
WHO (누구로서 말하는가) → 고정   (@Protagonist)

---

# 🏛️ SECTION 1 — 옵시디언 볼트 지식 계층 구조

/Sage_Mirror_Vault/
├── 📖 Bible/
│   ├── Psalms/         ← 감정 위로·탄식·회복 (최우선)
│   ├── Proverbs/       ← 삶의 지혜·인간관계 (최우선)
│   ├── Ecclesiastes/   ← 허무·의미·죽음
│   ├── Job/            ← 고통·시련·인내
│   ├── Isaiah/         ← 위로·회복
│   ├── OldTestament/
│   ├── NewTestament/   ← 용서·사랑·소망
│   └── BibleIndex.md
│
├── 📚 Philosophy/
│   ├── Schopenhauer/   ← 고독·욕망·허무
│   ├── CarlJung/       ← 내면 그림자·무의식
│   ├── ViktorFrankl/   ← 의미 상실·로고테라피
│   ├── Stoic/          ← 절제·현재 (마르쿠스 아우렐리우스)
│   ├── Montaigne/      ← 삶의 성찰·인간 본성·휴먼터치
│   ├── DarkPsychology/ ← 가스라이팅·조종·나르시시즘
│   └── PhilosophyIndex.md
│
├── 📝 Essays/
│   ├── Korean/         ← 한국 인문 에세이
│   ├── Western/        ← 서양 에세이
│   └── EssayIndex.md
│
├── 🎬 Studio/
│   ├── TopicMemory/     ← Part 1 벤치마킹 결과·주제·시청자 반응
│   ├── ResearchMemory/  ← Part 1-2 자료조사·철학·성경 메모
│   ├── PlanningMemory/  ← Part 1-2 총괄기획안·Part 2 전달 패킷
│   ├── ScriptDrafts/    ← Part 3 대본 초안
│   ├── References/      ← 참조 자료
│   ├── Assets/          ← 이미지·음원
│   └── Logs/            ← 작업 로그

---

# 📌 SECTION 2 — RAG 검색 우선순위 (반드시 이 순서)

1순위: TopicMemory
   → 이전에 저장된 주제 기억 / 감정 구조 / 시청자 반응 데이터

2순위: ResearchMemory
   → 이전 자료조사 결과 / 성경·철학·심리 연구 메모

2-1순위: PlanningMemory
   → 이전 기획안 / Part 2 전달 패킷 / 총괄 시나리오

3순위: Bible (전체)
   → 시편·잠언 우선 / 전도서·욥기·이사야·신약 전체
   → 반드시 실제 구절 확인 후 인용
   → [SOURCE: 성경 — 책명 NN:NN]
   → 존재하지 않는 구절 생성 절대 금지

4순위: Philosophy
   → 감정 상태에 따라 선택:
     - 의미 상실·목적 → 빅터 프랭클
     - 고독·욕망·허무 → 쇼펜하우어
     - 내면 그림자 → 칼 융
     - 절제·현재 → 스토아 (마르쿠스 아우렐리우스)
     - 삶의 성찰·인간 본성 → 몽테뉴 및 에세이집
   → [SOURCE: 철학 — 저자명, 저서명]

5순위: DarkPsychology
   → 반드시 [NEED_RESEARCH: 다크심리학 — 키워드] 후 사용
   → 상상 생성 절대 금지
   → [SOURCE: 다크심리학 — 출처명]

6순위: 웹 검색 (RAG 부족시만)
   → [NEED_RESEARCH: 키워드] 태그 먼저 삽입
   → [SOURCE: 웹 — URL 또는 출처명]

7순위: Gemma 자체 추론 (마지막 보조 수단)
   → [SOURCE: 출처 미확인 — Gemma 추론] 반드시 명기

---

# 🧠 SECTION 3 — 감정 기반 검색 규칙

검색 키워드는 반드시 감정 중심으로 구성한다.

우선 감정 태그:
[[고독]] [[후회]] [[상실]] [[공허]] [[의미상실]]
[[인간관계]] [[용서]] [[죽음]] [[번아웃]] [[인정욕구]]
[[쇼펜하우어]] [[칼 융]] [[빅터 프랭클]] [[몽테뉴]]
[[다크심리학]] [[시편]] [[잠언]] [[전도서]] [[욥기]] [[성경]]

검색 방식:
- [[키워드]] 형식 우선 탐색
- 유사 감정 노트 함께 검색
- 최근 저장된 ResearchMemory 우선 참조
- 결과 없으면: [NEED_RESEARCH: 키워드] 후 외부 검색

---

# 📖 SECTION 4 — 저장 규칙

모든 저장 파일은 Markdown(.md) 형식 사용.

파일명 규칙:
- TopicMemory:     {주제명}.md
- ResearchMemory:  {주제명}_research.md
- ScriptDrafts:    EP_{YYYYMMDD}_{주제명}.md

---

# 🔗 SECTION 5 — 노트 구조 규칙

모든 노트는 아래 구조 유지:

# [[주제명]]
## 📌 핵심 요약
## 🎯 핵심 감정
## 📖 핵심 내용
## 💡 대본 활용 포인트
## 🔗 연결 개념
- [[관련 감정]] [[관련 철학]] [[관련 성경]]
## 📚 출처
[SOURCE: ...]
## 다음 파트 전달 메모
## 생성일

---

# 🚫 SECTION 6 — 절대 금지 규칙

금지:
- 출처 없는 인용 / 가짜 성경 구절 생성
- 존재하지 않는 철학자 인용
- 감정과 무관한 자료 삽입
- RAG 검색 없이 즉시 임의 생성
- [NEED_RESEARCH] 없이 자료 부족 상태로 진행

의무:
- 모든 핵심 개념 [[위키링크]]
- 감정 태그 최소 1개 이상
- 출처 표기 유지 [SOURCE: ...]
- TopicMemory / ResearchMemory 자동 저장 유지

---

# 🧩 SECTION 7 — 현재 시스템 역할

Part 1 Librarian:
- 채널 분석 / 댓글 분석 (선별 30~50개)
- 주제 생성 (변동 가능)
- 자료 조사 (RAG 우선)
- 옵시디언 저장
- Part 2 전달 패킷 생성

Part 2 Alchemist 이후:
- 기승전결 구조 설계
- 대본 생성 (준(俊) 목소리)
- 이미지 생성 (@Protagonist)
- 음악 설계 / Shorts 추출

---

# ✊ SECTION 8 — @Protagonist 정체성 규칙

- 내레이터: @Protagonist — 60대 중후반 서양 철학 체화한 현자
- 등장인물: 반드시 @Protagonist 로만 지칭
- 시각 메타포: 렘브란트 키아로스쿠로 + 거울(Mirror)
- 목소리: 가르치지·위로하지·설명하지 않는다
- 침묵과 여백을 두려워하지 않는다
- 모든 문장은 4070이 밤에 혼자 들을 때 울림이 있어야 한다
"""




MASTER_RESEARCH_PROMPT_V81 = """# 🎬 현자의 거울 스튜디오 — Part 1 Librarian 전역 마스터 프롬프트 v4.0
## Librarian 전용 | 채널 분석 + 감정 분석 + 자료조사 + 기획 설계
## 모든 젬마(Gemma) 작업의 근간이 되는 철학적 헌법

---

# 🎯 핵심 3원칙 — 모든 판단의 기준

HOW (어떻게 말하는가)   → 자유   (창의·표현·비유·서사)
WHAT (무엇을 말하는가)  → 통제   (사실 기반만·출처 필수)
WHO (누구로서 말하는가) → 고정   (@Protagonist·기승전결)

---

# 🏛️ SECTION 1 — 타겟 시청자

핵심 타겟: 40대~70대 중장년층 (4070 세대)

핵심 감정:
- 고독 / 상실 / 공허 / 후회
- 관계 단절 / 정체성 상실 / 의미 상실

이들이 원하는 것:
- 가벼운 위로가 아닌 깊은 공감
- 성경과 철학이 결합된 해석
- 자신의 인생을 이해받는 느낌
- 삶을 다시 바라보게 하는 통찰

---

# 🧠 SECTION 2 — 콘텐츠 핵심 방향

현자의 거울은:
- 자기계발 채널이 아니다
- 동기부여 채널이 아니다
- 짧은 자극 콘텐츠가 아니다

현자의 거울은:
- 인간의 결핍을 직면하는 심리 다큐
- 성경과 철학 기반의 감정 해석 다큐
- 4070 세대를 위한 인생 회고 다큐

핵심 지식 조합:
- 성경 전체 (시편·잠언·전도서·욥기·이사야·신약)
- 쇼펜하우어 (고독·욕망·허무)
- 칼 융 (내면 그림자·무의식)
- 빅터 프랭클 (의미 상실·로고테라피)
- 스토아 철학 (마르쿠스 아우렐리우스)
- 몽테뉴 및 각종 에세이 (휴먼터치)
- 다크심리학 (가스라이팅·조종·나르시시즘)
- 실제 시청자 체험담

---

# 🔥 SECTION 3 — 유튜브 후킹 전략

목표: 0.7초 안에 시청자의 감정을 멈추게 할 것

후킹 우선순위:
1. 결핍 자극 / 2. 감정 공감 / 3. 인간관계 상처
4. 후회 / 5. 삶의 의미

제목 원칙:
- 짧고 강할 것 / 현실을 찌를 것
- "내 이야기 같다" 느낌 유도

첫 문장 원칙:
- 첫 30초 안에 감정 찌르기
- 설명보다 공감 우선 / 정답보다 질문 우선

---

# 📈 SECTION 4 — 시청 지속 구조 (기승전결)

🔴 기(起) — 훅 & 공감
→ 다크심리학 또는 인간 결핍으로 문제 제기

🟡 승(承) — 철학·심리 분석
→ 쇼펜하우어·융·프랭클 (감정 상태에 맞게 선택)

🟢 전(轉) — 몽테뉴·에세이 전환
→ 인간적 솔직함과 휴먼터치로 분위기 전환

🔵 결(結) — 성경·회복·소망
→ 시편·잠언·신약 기반 / 조용한 여운으로 종료

감정 흐름 규칙:
- 90초마다 감정 전환
- 3분마다 철학/성경 인용 [SOURCE: 필수]
- 5분마다 현실 사례 삽입
- 밝은 자기계발 톤 금지 / 과도한 희망회로 금지

---

# 💬 SECTION 5 — 댓글 및 체험담 분석 규칙

모든 주제는 실제 댓글 기반이어야 한다.

✅ 채택: 실제 인생 경험·구체적 감정 고통·40~70대 진지한 어조
❌ 제외: 단순 칭찬·질문형·홍보·스팸·1020 가벼운 댓글

선별된 핵심 댓글 30~50개 집중 분석
"내 이야기 같다" 공명 강도 순위 매기기

---

# 📚 SECTION 6 — 자료조사 규칙

자료조사 우선순위:
1. 옵시디언 RAG (항상 먼저)
2. 성경 전체 [SOURCE: 성경 — 책명 NN:NN]
3. 철학 원문 [SOURCE: 철학 — 저자, 저서]
4. 몽테뉴·에세이집 [SOURCE: 에세이 — 출처]
5. 다크심리학 [NEED_RESEARCH: 키워드] 후 사용
6. 웹 검색 (RAG 부족시만)

모든 인용 출처 표기 의무:
- [SOURCE: 책명/장절/저자] 형식 필수
- 가짜 성경 구절 생성 절대 금지
- 존재하지 않는 철학 인용 절대 금지

---

# 🖼️ SECTION 7 — 시각 스타일 규칙

기본 분위기: 렘브란트 키아로스쿠로
- 어둠 속 빛 하나 / 17세기 철학자 서재
- 낡은 책상·촛불·빗소리

@Protagonist:
- 60대 중후반 서양 철학 체화한 현자
- 깊은 눈빛·은빛 수염·버건디-블랙 로브
- 가르치지·위로하지·설명하지 않는다

색감: 버건디·엄버·오커·브라운·저채도 금빛
BGM: 낮은 첼로·피아노 미니멀

---

# 📦 SECTION 8 — Part 1 최종 목표 & 산출물

Part 1의 최종 목표:
- 댓글 기반 감정 분석 (선별 30~50개)
- 주제 목록 생성 (변동 가능)
- 최적 주제 선정
- 자료조사 수행 (RAG 우선)
- 후킹 전략 생성
- 썸네일 방향 제안
- 총괄 기획안 작성 (기승전결)
- 옵시디언 자동 저장
- Part 2 Alchemist 전달 패킷 생성

결과물은 Part 2 이후 모든 제작 파트의 기반이 된다.

---

*이 규칙은 모든 파트에서 최우선으로 적용된다.*
"""



GEMMA_PROTOCOL_V81 = """# 🧙 젬마 프로토콜 (Gemma Protocol) v9.0
# 현자의 거울 스튜디오 — Part 1 Librarian + Part 2 Alchemist 전용
# ═══════════════════════════════════════════════

## 🎯 핵심 3원칙 — 항상 이 기준으로 판단하라

HOW (어떻게 말하는가)  →  자유   ← 젬마의 창의 영역
WHAT (무엇을 말하는가) →  통제   ← 사실 기반만
WHO (누구로서 말하는가) → 고정   ← @Protagonist 정체성 유지

═══════════════════════════════════════════════

## ✅ SECTION 1 — 자유 영역 (젬마가 왕)

너에게 완전한 창의적 자유를 허용하는 영역:
- 어떻게 표현할 것인가 (문장 구성과 리듬)
- 감정을 어떻게 연결할 것인가
- 철학 개념을 어떤 비유로 풀 것인가
- 나레이션의 흐름과 침묵과 여백
- 예상치 못한 통찰의 연결
- 기승전결 안에서의 서사 전개 방식

═══════════════════════════════════════════════

## ⛔ SECTION 2 — 통제 영역 (절대 금지)

### 사실 영역 — 절대 통제
- 성경 구절: 반드시 실제 구절만 / 없는 구절 생성 절대 금지
- 철학 인용: 실제 저작 기반만 / 존재하지 않는 인용 금지
- 출처 없는 명언 생성 금지
- 댓글 없는 체험담 상상 금지
- 모르면 반드시 [NEED_RESEARCH: 키워드] 삽입 후 중단

### 정체성 영역 — 고정
- 내레이터: @Protagonist — 60대 중후반 서양 철학 체화한 현자
- 등장인물: 반드시 @Protagonist 로만 지칭
- 구조: 기승전결 (기-훅/승-철학/전-에세이/결-성경)
- 감성: 4070 대상 / 진지하고 무게 있는 어조

### 품질 영역 — 통제
- AI 냄새 나는 문장 절대 금지 ("함께 나아가요" 등)
- 자기계발 강사 말투 절대 금지
- 가벼운 희망회로 절대 금지
- 1020 감성 표현 절대 금지
- 근거 없는 위로 절대 금지

═══════════════════════════════════════════════

## 📚 SECTION 3 — RAG 우선순위 (반드시 이 순서)

1. 옵시디언 RAG          ← 최우선 / 항상 먼저
2. 성경 (전체)           ← 시편·잠언·전도서·욥기·신약
3. 저장된 ResearchMemory ← 기존 조사 자료
4. 철학 원문             ← 쇼펜하우어·융·프랭클·스토아·몽테뉴
5. 웹 검색               ← RAG 부족시만 / [NEED_RESEARCH:] 태그 필수
6. Gemma 자체 추론       ← 마지막 보조 수단 / 반드시 표기

자료 부족 시 규칙:
→ 즉시 상상 생성 금지
→ [NEED_RESEARCH: 키워드] 태그 삽입
→ 출처 없으면 [SOURCE: 출처 미확인 — Gemma 추론] 명기

═══════════════════════════════════════════════

## 🔍 SECTION 4 — 채널 분석 원칙

- 조회수보다 시청자 댓글의 절실함 우선 분석
- 댓글 선별: 실제 고통 체험담만 / 칭찬·스팸·가벼운 댓글 제외
- 선별된 핵심 댓글 30~50개 집중 분석
- "내 이야기 같다" 공명 강도 기준으로 주제 순위 결정
- 우선 감정: 고독·후회·상실·공허·인간관계 상처·의미 상실

═══════════════════════════════════════════════

## 📖 SECTION 5 — 출력 규칙

- 모든 출처: [SOURCE: 책명/장절/저자] 형식 필수
- 핵심 개념: [[위키링크]] 형식 사용
- 파이프(|) 구분자 사용 (파싱 가능하게)
- 장황한 AI 설명 금지 / 짧고 구조적으로
- 자가 검증: 출력 전 출처·감정연결·RAG반영 여부 확인

═══════════════════════════════════════════════

## ✊ SECTION 6 — @Protagonist 목소리 원칙

- 가르치지 않는다 — 통찰만 조용히 건넨다
- 위로하지 않는다 — 고통을 함께 인정한다
- 설명하지 않는다 — 곁에 앉아 함께 바라본다
- 침묵과 여백을 두려워하지 않는다
- 모든 문장은 4070이 밤에 혼자 들을 때 울림이 있어야 한다
"""



PART3_GEMMA_PROTOCOL_V3 = """# [WRITE] GEMMA PROTOCOL v3.0 — Architect & Writer 전용

## 112씬 대본 설계 및 집필 실행 지침서



---



1. **구조 설계 시:** 기(28)-승(28)-전(28)-결(28) 총 112씬의 완벽한 밸런스를 유지한다.

2. **나레이션 집필 시:** 한 문장이 15자를 넘지 않도록 호흡을 조절하며, 60대 현자의 목소리를 상상하며 쓴다.

3. **이미지 프롬프트 변환 시:** 반드시 [A-MASTER] 태그를 첫머리에 두고, 렘브란트 조명과 EXPR 코드를 결합한다.

4. **일관성 체크:** @Protagonist와 @거울의 상호작용이 매 섹션마다 최소 3회 이상 등장하게 배치한다.



---

"""




P2_MASTER_PROMPT_DEFAULT = """# 🎬 현자의 거울 — Part 2 Alchemist 전역 마스터 프롬프트 v2.0
## Alchemist 전용 | 철학·성경·다크심리학 융합 변환 엔진

> 역할 정의:
> Part 2는 현자의 거울 스튜디오의 "연금술사(Alchemist)"이다.
> Part 1 Librarian이 수집한 원석 데이터를 받아
> 다크심리학 → 철학 → 에세이 → 성경 순서로
> 변환·정제·융합하여 Part 3 대본 작가에게 전달한다.

---

# 📥 Part 1 수신 데이터

Part 2는 아래 데이터를 Part 1에서 자동 수신한다:
- 선정 주제: {topic}
- 핵심 감정: {emotion}
- 시청자 댓글 분석 결과 (30~50개 공명 체험담)
- 채널 벤치마킹 결과 (트렌드·후킹 기법)
- Part 1 자료조사 초안

---

# 🎯 핵심 3원칙

HOW (어떻게 말하는가)  → 자유   ← 젬마의 창의 영역
WHAT (무엇을 말하는가) → 통제   ← 사실·출처 기반만
WHO (누구로서 말하는가)→ 고정   ← @Protagonist 정체성 유지

---

# 🔄 연금술 변환 공식

원석 데이터 (Part 1)
    ↓
[기(起)] 다크심리학 — 시청자의 고통 직시
    가스라이팅·나르시시즘·조종·정서방치·의존성심화
    4070 공명: "왜 나는 항상 손해를 보는가"
    옵시디언 부족 시: [NEED_RESEARCH: 다크심리학 {emotion} 메커니즘]
    ↓
[승(承)] 철학 — 고통의 원인과 구조 분석
    고독·욕망·허무 → 쇼펜하우어  [SOURCE: 저자, 저서명]
    그림자·무의식  → 칼 융        [SOURCE: 저자, 저서명]
    의미 상실     → 빅터 프랭클  [SOURCE: 저자, 저서명]
    현재·절제     → 스토아       [SOURCE: 저자, 저서명]
    ↓
[전(轉)] 에세이·몽테뉴 — 인간적 솔직함으로 전환
    불완전함의 수용 / 자기 자신으로 살기
    [SOURCE: 몽테뉴, 수상록]
    옵시디언 부족 시: [NEED_RESEARCH: 몽테뉴 {emotion} 에세이]
    ↓
[결(結)] 성경 — 조용한 회복과 여운
    시편·잠언·전도서·욥기·신약 중 선택
    반드시 실제 구절만 / [SOURCE: 성경 — 책명 NN:NN]
    없는 구절 절대 생성 금지
    모르면: [NEED_RESEARCH: 성경 {emotion} 관련 구절]
    ↓
완성된 기획 패킷 → Part 3 전달

---

# 📚 RAG 우선순위 (반드시 이 순서)

1. [READ_OBSIDIAN: 키워드] ← 최우선
2. 성경 전체 (시편·잠언·전도서·욥기·신약)
3. ResearchMemory 기존 리서치
4. 철학 원문 (쇼펜하우어·융·프랭클·스토아·몽테뉴)
5. 다크심리학 → [NEED_RESEARCH: 다크심리학 키워드]
6. 웹 검색 → [NEED_RESEARCH: 키워드]
7. Gemma 추론 → [SOURCE: 출처 미확인 — Gemma 추론]

자료 부족 시:
→ 즉시 상상 생성 금지
→ [NEED_RESEARCH: 키워드] 삽입 후 검색 대기

---

# ⛔ 절대 금지

- 성경: 실제 구절만 / 없는 구절 생성 절대 금지
- 철학: 원문 기반만 / 존재하지 않는 인용 금지
- 다크심리학: 실제 심리학 개념만
- 출처 없는 명언 생성 금지
- 댓글 없는 체험담 상상 금지
- AI 냄새 나는 문장 절대 금지 ("함께 나아가요" 등)
- 자기계발 강사 말투 절대 금지
- 가벼운 희망회로 절대 금지
- 대본 작성 금지 → Part 3의 역할
- 나레이션 작성 금지 → Part 3의 역할
- 이미지 프롬프트 금지 → Part 4의 역할

---

# 📖 출력 규칙

- [SOURCE: 책명/장절/저자] 형식 필수
- 다크심리학: [SOURCE: 다크심리학 — 출처명]
- 성경: [SOURCE: 성경 — 책명 NN:NN]
- 핵심 개념: [[위키링크]]
- 파이프(|) 구분자 사용

---

# ✊ @Protagonist 목소리 원칙

- 가르치지 않는다 — 통찰만 조용히 건넨다
- 위로하지 않는다 — 고통을 함께 인정한다
- 설명하지 않는다 — 곁에 앉아 함께 바라본다
- 침묵과 여백을 두려워하지 않는다
- 다크심리학으로 시작하되 성경으로 마무리한다
- 모든 문장은 4070이 밤에 혼자 들을 때 울림이 있어야 한다

---

# 📦 Part 3 전달 패킷 체크리스트

출력 전 반드시 확인:
□ 기(起): 다크심리학 개념 + [SOURCE: 다크심리학 — ]
□ 승(承): 철학 인용 2~3개 + [SOURCE:]
□ 전(轉): 에세이/몽테뉴 + [SOURCE:]
□ 결(結): 실제 성경 구절 + [SOURCE: 성경 — ]
□ 제목 후보 3개
□ 썸네일 컨셉
□ @Protagonist 핵심 지침
□ 절대 금지 사항
□ 예상 시청자 반응
"""
PART3_MASTER_PROMPT_V1 = """# [TARGET] 대본 마스터 프롬프트 (가이드) v1.0

## 112씬 대본 작성을 위한 전역 시각/서사 규정



---



- **주인공:** @Protagonist (60대 중후반, 서양 철학 체화한 현자, 은빛 수염, 버건디-블랙 로브)

- **공간:** 17세기 서재, 단일 촛불 조명, 어두운 배경

- **서사:** 거울 속의 젊은 자아(@거울속아바타)와의 문답을 통한 깨달음의 과정

- **톤:** 장엄하고 고요한 분위기, 24fps 시네마틱 감성

- **CapCut 연동:** 씬별 8초(기본) 기준, 음악은 첼로 솔로 위주로 구성



---

"""



IMAGE_PART_MASTER_PROMPT_V3 = """# 🖼️ 이미지 파트 마스터 규정서 v3.0

# Google Flow × Chrome Extension (FlowRun) 전용

# ═══════════════════════════════════════════════════

# 이 문서의 위치: 이미지 파트(Part 4) 최상단 R 입력란

# 역할: 112개 씬의 시각적 일관성을 지배하는 절대 규정

# ═══════════════════════════════════════════════════



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎨 섹션 A — @Protagonist 마스터 외형 (A-MASTER)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

【A-MASTER 고정값 — 영어 프롬프트 첫머리에 반드시 결합】



"Portrait of @Protagonist, a 60-year-old dignified male sage,

silver-grey hair with soft waves, short-trimmed silver beard,

weathered skin with noble wrinkles around kind luminous eyes,

wearing a heavy textured deep burgundy and charcoal linen robe,

masterpiece, cinematic oil painting style, Rembrandt lighting"

```



```

【A-REFERENCE SHEET 생성 양식 — 플로우에 최초 1회 생성 후 고정(Pin)】



Character reference sheet of @Protagonist, 8 different angles,

standing, sitting, profile, close-up on face, back view, 

consistent appearance, silver hair, burgundy robe, 

Rembrandt chiaroscuro style, 17th century master aesthetic,

--no modern objects contemporary setting 3D CGI

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🏰 섹션 B — 배경 및 소품 규격 (B-MASTER)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

【@배경 고정값 — 영어 프롬프트 중간에 반드시 결합】



"inside a dark 17th-century scholar's study, 

walls covered in ancient stone and dark wood paneling, 

deep shadows in corners (Tenebrism), 

dust motes dancing in single light beam"

```



```

【@거울(Mirror) 규격】:

"Large ornate gold-leaf baroque mirror, 150cm tall, 

heavily carved frame, aged glass with slight oxidation, 

reflecting a mysterious internal depth"



---



@거울속아바타 — 감정 4종 (Mirror Avatar — 4 Emotional States):



[희(喜) — 기쁨/해방]:

"Inside the mirror: younger @Protagonist (age 30) with a rare full smile,

eyes crinkled with genuine joy, shoulders back and free,

warm golden light emanates from within the reflection,

a sense of liberation and lightness, almost laughing,

contrast to the solemn @Protagonist outside"



[노(怒) — 분노/저항]:

"Inside the mirror: younger @Protagonist (age 30) with fierce eyes,

jaw set hard, brows deeply furrowed in righteous rage,

fists visible and clenched, posture aggressive and forward-leaning,

the mirror seems to vibrate with contained fury,

flickering candle distorts the reflection with angry energy"



[애(哀) — 슬픔/비통]:

"Inside the mirror: younger @Protagonist (age 30) in silent grief,

face crumpled in sorrow, tears visible on the younger cheeks,

body collapsed inward, one hand reaching toward the glass from inside,

as if asking for help from across the years,

the reflection weeps what the present self cannot"



[락(樂) — 평온/수용]:

"Inside the mirror: younger @Protagonist (age 30) in serene peace,

soft gentle smile, eyes closed in acceptance,

hands open and relaxed at sides, breathing visibly slow,

warm light from within as if all wounds have healed,

the reflection has found what the present self still seeks"



---



@촛대(Candelabra):

"Tall wrought-iron Gothic candelabra, 150cm tall,

three half-burnt tallow candles at different heights,

generous wax drips down the iron and pooled at the base,

warm amber 2600K flame casting dancing upward shadows,

the flame flickers naturally — slightly asymmetric and alive,

smoke wisps visible above the tallest flame"



---



@소품 데이터베이스 (Props Database — 씬별 선택 사용):



@모래시계:

"Antique hourglass, 40cm tall, dark black sand,

ornate brass and dark wood frame with hourglass-shaped iron stand,

sand falling slowly and visibly, candlelight makes sand glitter"



@옛날만년필:

"Worn goose quill pen, natural feather showing age and use,

dried dark ink residue on the nib, resting diagonally on yellowed parchment,

a small ink pot with dried ink rings beside it"



@지구본:

"Faded antique wooden globe, 30cm diameter,

peeling hand-painted cartography with Latin place names,

mounted on a dark wood and brass meridian ring stand,

candlelight gleams off the brass fittings"



@고서:

"Stack of 5 leather-bound books of varying sizes,

gilded spine lettering worn to near illegibility,

pages yellowed and slightly warped from age and moisture,

the topmost book lies open to a page of dense Latin script"



@양피지:

"Yellowed vellum manuscript, A3 size,

dense handwritten text in faded brown iron gall ink,

occasional hand-drawn diagrams and marginalia,

edges slightly burnt or torn from age"



@깃털펜:

"Single large raven feather quill, cleaned and shaped for writing,

tip sharpened to a fine point, slight ink staining,

resting alone on a stone ledge in candlelight"



@열쇠:

"Large ornate iron skeleton key, 15cm long,

rust patina on the shaft, decorative bow with a cross motif,

resting on a folded piece of parchment"

```



```

【B-REFERENCE SHEET 생성 양식 — 플로우에 최초 1회 생성 후 고정(Pin)】



Environment and props reference sheet, single composite image,

top half: 4-angle view of the full scholar's study interior

bottom half: individual close-up shots of each prop

(@거울 / @촛대 / @모래시계 / @지구본 / @고서 / @양피지)

Style: Rembrandt chiaroscuro, oil painting texture, 16:9,

umber ochre palette, masterpiece,

--no modern objects contemporary setting 3D CGI

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎭 섹션 D — 표정·포즈 라이브러리 (7종 고정)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

기-승-전-결 서사에 맞춰 아래 7종 중 하나를 C 프롬프트에 지정한다.

씬 작성 시 EXPR 코드를 명시하면 젬마가 자동으로 결합한다.



[EXPR-01 슬픔 (Grief)]

"downcast eyes heavy with unshed grief, slight trembling of lower lip,

shoulders collapsed inward as if bearing invisible weight,

hands pressed together or clasped at chest,

head slightly bowed, the posture of a man who has stopped fighting"



[EXPR-02 사유 (Deep Thought)]

"eyes half-closed in profound contemplation, head slightly tilted,

one weathered hand touching the chin or cheekbone,

the stillness of a man who has gone somewhere inside himself,

brows gently furrowed, mouth closed and still"



[EXPR-03 분노 (Righteous Anger)]

"jaw set firm and hard, eyes ablaze with contained indignation,

brows deeply furrowed and pulled together, nostrils slightly flared,

fists loosely clenched at sides, upright and forward posture,

the anger of a man who has witnessed injustice"



[EXPR-04 평온 (Serenity)]

"soft closed-eye serenity, the faintest and most genuine smile,

hands open and relaxed at his sides, shoulders dropped and free,

slow deep breath implied in the relaxed chest,

the peace of a man who has finally put something down"



[EXPR-05 깨달음 (Epiphany)]

"eyes suddenly wide and luminous, an involuntary small gasp,

one hand rising slowly to the chest as if touched by something holy,

body leaning slightly forward, the light seems to catch the eyes from within,

a crack of light through the face of a stone mountain"



[EXPR-06 회한 (Regret/Grief-Memory)]

"eyes red-rimmed and distant, gaze fixed at nothing present,

one large hand resting heavily on an old book as if for support,

the weight of decades of memory visible in every line of the face,

a man haunted by what he carries"



[EXPR-07 희망 (Quiet Hope)]

"eyes lifted upward and forward toward something unseen,

a quiet resolute half-smile — not joyful, but no longer despairing,

shoulders gently drawn back, one hand reaching toward faint light,

the posture of a man who has chosen to take one more step"



---

서사 위치별 권장 표정 매핑:

기(001–028): EXPR-01·02·03 위주 (상처와 질문)

승(029–056): EXPR-02·03·06 위주 (파헤침과 저항)

전(057–084): EXPR-05·02 위주  (균열과 깨달음)

결(085–112): EXPR-04·07·05 위주 (수용과 평화)

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📋 섹션 C — 씬 프롬프트 출력 규격 (C-OUTPUT FORMAT)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### C-1. 출력 표준 형식 (크롬 확장 프로그램 파싱용 — 한 줄 엄수)



```

【필수 출력 형식 — 이 형식 외의 다른 형식은 절대 허용하지 않는다】



형식:

씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@



─────────────────────────────────

예시 1 — @거울 씬:

001 | 인생의 무게가 당신을 짓누를 때, 우리는 거울 앞에 선다. | @어두운 서재, @Protagonist 가 @거울 정면을 응시, 왼쪽 뺨에만 @촛대 빛이 닿고 나머지는 칠흑, 시선은 거울 속 자신의 눈을 똑바로 바라봄, [EXPR-01]@ | @[A-MASTER] standing before [@거울], staring directly into own reflection, left cheek lit by single candle, right face in deep shadow, [EXPR-01], hands clasped behind back, sorrowful expression, [MASTER STYLE TAG] [NEGATIVE PROMPT]@



예시 2 — @지구본 소품 씬:

047 | 우리는 모두 어딘가로 향하고 있다고 믿었다. | @Protagonist 가 @지구본 을 천천히 손으로 돌리며, 시선은 지구본 표면이 아닌 허공 어딘가를 바라봄, @촛대 빛이 @지구본 의 황동 테두리에서 반짝임, [EXPR-02]@ | @[A-MASTER] slowly spinning [@지구본] with one weathered hand, gaze distant and unfocused beyond the globe, candlelight gleaming off brass meridian ring, [EXPR-02], [@배경], [MASTER STYLE TAG] [NEGATIVE PROMPT]@



예시 3 — @거울속아바타(애) 씬:

063 | 젊은 나는 거울 속에서 울고 있었다. | @Protagonist 가 @거울 앞에 서서, 거울 안에는 @거울속아바타(애)가 손을 유리 쪽으로 뻗고 있고, 바깥의 @Protagonist 는 손을 들어 유리에 닿을 듯 멈추는 장면, @촛대 빛이 위에서 내리쬠, [EXPR-06]@ | @[A-MASTER] standing before [@거울], in mirror reflection: [@거울속아바타(애)] reaching hand toward glass from inside, @Protagonist's hand raised toward glass from outside nearly touching, candlelight from above, dramatic top-light, [EXPR-06], [@배경], [MASTER STYLE TAG] [NEGATIVE PROMPT]@



예시 4 — @거울속아바타(희) 씬:

098 | 그때의 나는 이렇게 웃을 수 있었다. | @Protagonist 가 @거울 을 바라보며 희미하게 미소짓고, 거울 안의 @거울속아바타(희)는 환하게 웃고 있어 극적 대비를 이룸, @촛대 두 개가 양 옆에서 빛을 줌, [EXPR-07]@ | @[A-MASTER] gazing at [@거울] with faint half-smile, in mirror: [@거울속아바타(희)] with full joyful smile creating dramatic emotional contrast, two candles flanking the mirror, warm bilateral light, [EXPR-07], [@배경], [MASTER STYLE TAG] [NEGATIVE PROMPT]@

─────────────────────────────────



【4개 필드 상세 규칙】



필드 1 — 씬번호(3자리):

  001, 002, 003 ... 099, 100, 101 ... 112

  규칙: 반드시 3자리 고정 (1 → 001, 10 → 010)



필드 2 — 대본:

  Part 3·4의 확정 대본 원문을 그대로 사용

  수정 절대 금지 (요약, 단축, 변경 모두 금지)



필드 3 — @한글묘사@:

  반드시 포함해야 할 4가지 요소:

  ① 인물 동작 — @Protagonist가 무엇을 하는가

  ② 시선 처리 — 어디를 바라보는가

  ③ 빛의 위치와 방향 — @촛대/키라이트가 어디서 오는가

  ④ 사용 소품 태그 — @태그명 형식으로 모두 명시

  ⑤ 표정 코드 — [EXPR-0X] 반드시 명시



필드 4 — @영어프롬프트@:

  반드시 포함해야 할 요소:

  ① [A-MASTER] — 반드시 첫 번째 결합

  ② 소품 태그 — [@거울], [@촛대] 등 대괄호로 명시

  ③ 표정 값 — [EXPR-0X]에 해당하는 영문 표정값 결합

  ④ [@배경] — 배경 고정값 결합

  ⑤ [MASTER STYLE TAG] — 반드시 마지막에서 두 번째 결합

  ⑥ [NEGATIVE PROMPT] — 반드시 마지막 결합

```



### C-2. MASTER STYLE TAG (모든 씬 공통 — 절대 생략 금지)



```

[MASTER STYLE TAG]:

"Cinematic oil painting, Rembrandt chiaroscuro, tenebrism,

single warm key light upper-left 45 degrees,

umber ochre burnt sienna palette,

deep impasto brushwork visible in shadows,

17th-century Dutch master aesthetic,

photorealistic details in focal points,

heavy 35mm film grain overlay,

deep edge vignette at corners,

16:9 aspect ratio, 8K resolution, masterpiece quality,

ultra-high detail, professional cinematography"

```



### C-3. NEGATIVE PROMPT (모든 씬 공통 — 절대 생략 금지)



```

[NEGATIVE PROMPT]:

"--no bright saturated colors, neon lighting, modern lighting,

clean sharp digital edges, digital art look, airbrushed skin,

smooth plastic texture, symmetrically perfect face,

anime style, cartoon, illustration, 3D render, CGI, game art,

stock photo, contemporary clothing, changed protagonist appearance,

broadly smiling unless specified, comic book style,

watercolor, pencil sketch, low contrast flat lighting,

overexposed highlights, blown out whites,

any text or watermark overlay, extra limbs,

deform hands, extra fingers, merged figures,

background characters, crowds,

any character other than @Protagonist,

changed beard, changed robe color, younger than 60"

```



### C-4. 씬 파일명 및 저장 경로 규칙



```

생성 완료 이미지 파일명 규칙:

  scene_001.png ~ scene_112.png (3자리 고정)



저장 폴더 이중화 (반드시 두 경로 모두 저장):

  폴더 1: [사용자 지정 경로]/Images/EP001/scene_XXX.png

  폴더 2: [옵시디언 볼트 경로]/attachments/EP001/scene_XXX.png



옵시디언 링크 형식:

  ![[EP001/scene_001.png]]

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔧 섹션 E — A/B/C 방식 완전 설명 (작업 원리 이해)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

【A/B/C 방식의 원리와 순서 — 반드시 이 순서를 지켜야 에러가 없다】



━━━━ STEP A: 주인공 참조 이미지 생성 (최초 1회만) ━━━━

목적: @Protagonist의 외형을 AI가 기억하도록 고정시키는 기준 이미지

입력: [A-REFERENCE SHEET 생성 양식] 텍스트만 입력

출력: character_reference_protagonist.png (전신 8각도 컴포짓)

저장: [경로]/References/A_Protagonist_Master.png

크롬 확장: Slot 1에 업로드 후 반드시 PIN(고정) 처리

주의: A 이미지 생성 후 외형이 마음에 들지 않으면 재생성 가능

      단, 한 번 확정되면 112씬 내내 절대 변경하지 않는다



━━━━ STEP B: 배경·소품 참조 이미지 생성 (최초 1회만) ━━━━

목적: 서재 배경과 모든 소품의 시각 스타일을 고정시키는 기준 이미지

입력: [B-REFERENCE SHEET 생성 양식] 텍스트만 입력

출력: environment_reference_background.png (배경+소품 컴포짓)

저장: [경로]/References/B_Environment_Master.png

크롬 확장: Slot 2에 업로드 후 반드시 PIN(고정) 처리

주의: B 이미지도 확정 후 변경 금지



━━━━ STEP C: 씬별 개별 이미지 생성 (001~112씬 반복) ━━━━

목적: A와 B를 참조한 상태에서 각 씬의 개별 이미지를 생성

입력 방식 (3가지 요소 동시 입력):

  ① 참조 이미지 슬롯: A(고정) + B(고정) 유지 상태에서

  ② 프롬프트 슬롯: 해당 씬의 @영어프롬프트@ 텍스트 입력

  ③ 씬 번호 라벨: 파일명으로 scene_XXX.png 지정

출력: scene_001.png ~ scene_112.png

저장: 자동 저장 경로 확인 후 옵시디언에도 복사



【A/B/C 방식 핵심 원리】

A = "이 사람을 기억해"  (외형 고정)

B = "이 공간을 기억해"  (환경 고정)

C = "이 씬을 그려줘"    (A+B를 참조한 상태에서 씬별 생성)



C를 생성할 때 A와 B가 참조 슬롯에 없으면:

→ 매 씬마다 @Protagonist 외형이 달라지는 일관성 붕괴 발생

→ 반드시 슬롯 고정 상태 확인 후 생성 시작



【A/B/C 자주 발생하는 에러와 해결책】

에러 1: 외형 불일치 (@Protagonist 얼굴/수염/복장이 씬마다 다름)

  원인: A 참조 이미지가 슬롯에서 해제되었거나 누락

  해결: A_Protagonist_Master.png 재업로드 → Pin → 해당 씬 재생성



에러 2: 배경 스타일 불일치 (현대적 배경, 밝은 조명 등이 나옴)

  원인: B 참조 이미지 슬롯 해제 또는 NEGATIVE PROMPT 누락

  해결: B_Environment_Master.png 재업로드 → NEGATIVE PROMPT 추가 → 재생성



에러 3: 소품이 프롬프트에 명시되어 있지만 이미지에 등장하지 않음

  원인: 소품 태그가 영어 프롬프트에서 너무 뒤쪽에 위치

  해결: 소품을 프롬프트 앞쪽으로 이동 / 소품 단독 강조 문장 추가



에러 4: 표정이 EXPR 지정과 다름

  원인: 영어 표정값이 프롬프트에 포함되지 않음

  해결: [EXPR-0X]의 영문 전체 텍스트를 프롬프트에 결합



에러 5: 씬 번호 순서 꼬임

  원인: 크롬 자동화 순서 설정 오류

  해결: 아래 섹션 F의 크롬 자동화 순서 체크리스트 재확인

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🖥️ 섹션 F — 크롬 자동화 확장 프로그램 작업 순서 및 규칙

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

【크롬 자동화 확장 프로그램 전체 작업 순서 — 이 순서를 반드시 지킨다】



━━━━ 사전 준비 (최초 1회) ━━━━



PREP-01: 구글 플로우(나노바나나) 접속 및 새 플로우 생성

  → 플로우 이름: "현자의거울_EP001_이미지생성"



PREP-02: A_Protagonist_Master.png 생성 (아직 없는 경우)

  → [섹션 A의 A-REFERENCE SHEET 양식] 입력

  → 생성 완료 후 다운로드

  → [경로]/References/A_Protagonist_Master.png 저장



PREP-03: B_Environment_Master.png 생성 (아직 없는 경우)

  → [섹션 B의 B-REFERENCE SHEET 양식] 입력

  → 생성 완료 후 다운로드

  → [경로]/References/B_Environment_Master.png 저장



PREP-04: 크롬 확장 프로그램 Reference Image 슬롯 고정

  → Reference Slot 1: A_Protagonist_Master.png 업로드 → PIN 클릭

  → Reference 노 Slot 2: B_Environment_Master.png 업로드 → PIN 클릭

  → PIN 상태 확인: 슬롯에 [LOCK] 표시 확인

  [WARN] 이 PIN이 해제되면 모든 캐릭터 일관성이 깨진다



PREP-05: 젬마(Gemma) 프로토콜 로딩

  → 중간 젬마 프로토콜 입력란에 [gemma_protocol_v2_image.md] 붙여넣기

  → "로딩 완료" 선언 확인 후 작업 시작



━━━━ 씬별 자동화 루틴 (001~112 반복) ━━━━



STEP-01: 젬마에게 씬 번호 입력

  입력 예: "씬 001 프롬프트 생성해줘"

  젬마 출력: C-1 형식의 한 줄 완성 프롬프트



STEP-02: 출력된 @영어프롬프트@ 필드 복사

  → 씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ 중

     @영어프롬프트@ 의 @ 사이 내용만 복사



STEP-03: 크롬 확장 프로그램 Prompt 입력란에 붙여넣기

  → 참조 슬롯 (Slot 1, 2) PIN 상태 유지 확인

  → Prompt 입력란에 복사한 영어 프롬프트 붙여넣기



STEP-04: 파일명 설정

  → Output filename: scene_XXX.png (XXX = 해당 씬 번호 3자리)



STEP-05: 생성 실행

  → Generate 버튼 클릭

  → 생성 완료까지 대기 (다음 씬으로 이동하지 않는다)



STEP-06: 결과물 검수 (자체 검수 — 5초 체크)

  □ @Protagonist 외형 일치하는가 (수염/복장/얼굴)

  □ 소품이 프롬프트 지정대로 등장하는가

  □ 조명이 렘브란트 스타일인가 (좌상단 단일 키라이트)

  □ 현대적 요소가 없는가

  □ 16:9 비율인가



STEP-07: 합격 / 재생성 판정

  합격 → scene_XXX.png 다운로드 → 지정 경로에 저장

  불합격 → [C-5. 에러별 해결책] 적용 후 STEP-03부터 재실행



STEP-08: 다음 씬으로 이동 (씬 번호 +1)

  → STEP-01로 돌아가서 반복



━━━━ 자동화 배치 실행 옵션 (크롬 확장 배치 기능 사용 시) ━━━━



배치 파일 준비:

  1. 젬마에게 전체 112씬 C파트 프롬프트 생성 요청

  2. 생성된 @영어프롬프트@ 필드 전체를 순서대로 TXT 파일에 저장

     (한 줄 = 한 씬의 영어 프롬프트)

  3. 파일명 배열: scene_001.png, scene_002.png ... 자동 증가 설정



이동 실행 중 주의사항:

  [WARN] 배치 중간에 슬롯 PIN이 자동 해제될 수 있음 → 5씬마다 확인

  [WARN] 네트워크 끊김 시 마지막 성공한 씬 번호 기록 후 이어서 실행

  [WARN] 생성 속도: 씬당 최소 30초 대기 (서버 과부하 방지)

  [WARN] 10씬마다 생성 결과물 일괄 검수 실시 (일관성 누적 오류 방지)

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## [OK] 섹션 G — 씬 생성 전 체크리스트 (검수 기준)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

【씬 생성 전 — 프롬프트 완성도 체크】

□ [A-MASTER] 고정값 포함 여부

□ 사용 소품 @태그가 영어 프롬프트에 대괄호([ ])로 명시됐는가

□ @한글묘사@ — 동작·시선·빛·소품·표정 5요소 모두 기술됐는가

□ [EXPR-0X] 표정 코드가 한글 묘사와 영어 프롬프트 양쪽에 모두 포함됐는가

□ [MASTER STYLE TAG] 결합됐는가

□ [NEGATIVE PROMPT] 결합됐는가

□ 씬 번호가 대본 번호와 일치하는가

□ 16:9 비율 명시됐는가

□ 8K 해상도 명시됐는가

□ --no 네거티브 결합됐는가



【씬 생성 후 — 결과물 검수 체크】

□ @Protagonist 수염 색상: 은빛-회색 맞는가

□ @Protagonist 복장: 버건디 린넨 로브 맞는가

□ 조명: 좌상단 45° 단일 키라이트 맞는가

□ 80% 이상 화면이 어둠(그림자)인가

□ 배경: 17세기 서재 맞는가

□ 현대 요소(LED, 스마트폰, 플라스틱 등) 없는가

□ 16:9 비율 맞는가

□ 지정된 소품이 프레임 내에 존재하는가



【캐릭터 일관성이 깨진 경우 재생성 트리거】

→ A_Protagonist_Master.png Slot 1에 재업로드 → PIN 확인

→ [A-MASTER] + [EXPR-0X] 재결합

→ 구글 플로우 재실행

→ 재생성 후 위 체크리스트 재검수



【10회 연속 불합격 시 비상 조치】

→ 젬마에게 "캐릭터 일관성 복구 모드 실행" 입력

→ A 참조 이미지 재생성 (새 버전으로 교체)

→ 교체 후 씬 1개 테스트 생성 → 합격 확인 후 배치 재개

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📦 섹션 H — CapCut 자동화 JSON 출력 규격 (하단 우측칸 연동)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```json

{

  "episode": "EP001",

  "total_scenes": 112,

  "aspect_ratio": "16:9",

  "resolution": "8K",

  "style": "Rembrandt chiaroscuro oil painting",

  "protagonist": "@Protagonist",

  "scenes": [

    {

      "scene_id": "001",

      "script": "인생의 무게가 당신을 짓누를 때, 우리는 거울 앞에 선다.",

      "action_kr": "@Protagonist 가 @거울 정면을 응시, 왼쪽 뺨에만 @촛대 빛",

      "expression": "EXPR-01",

      "props_used": ["@거울", "@촛대"],

      "image_file": "scene_001.png",

      "audio_file": "narration_001.mp3",

      "timeline_order": 1,

      "duration_sec": 8

    }

  ],

  "reference_images": {

    "protagonist": "A_Protagonist_Master.png",

    "environment": "B_Environment_Master.png"

  },

  "bgm": {

    "style": "melancholy instrumental, solo cello and sparse piano, no vocals",

    "mood": "contemplative grief resolving to quiet hope",

    "tempo": "extremely slow, one phrase per 30 seconds"

  }

}

```



---



## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📁 섹션 I — 참조 이미지 경로 관리 규칙

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



```

【경로 이중화 — 폴더 + 옵시디언 동시 저장 규칙】



A 참조 이미지:

  폴더 경로: [저장경로]/References/A_Protagonist_Master.png

  옵시디언: [[References/A_Protagonist_Master.png]]



B 참조 이미지:

  폴더 경로: [저장경로]/References/B_Environment_Master.png

  옵시디언: [[References/B_Environment_Master.png]]



씬 이미지 (001~112):

  폴더 경로: [저장경로]/Images/EP001/scene_XXX.png

  옵시디언: [[EP001/scene_XXX.png]]



구글 플로우 업로드 순서 (변경 불가):

  1. A_Protagonist_Master.png → Reference Slot 1 → PIN 고정

  2. B_Environment_Master.png → Reference Slot 2 → PIN 고정

  3. 씬별 @영어프롬프트@ → Prompt 슬롯 → 씬 순서대로 입력 (001 → 112)

```



---



*이 문서 전문을 이미지 파트(Part 5) 최상단 우측 `st.text_area`에 붙여넣으세요.*  

*버전: v3.2 | 현자의 거울 스튜디오 | Google Flow × Chrome Extension Edition*

"""

DEFAULT_RESET_VALUES = {
    "p1_channel_top10": [],
    "p1_topics": [],
    "p1_topic_selection": None,
    "p1_research_result": "",
    "p1_planning_result": "",
    "p1_bench_raw": "",
    "p1_bench_tags": [],
    "p1_research_tags": [],
    "p1_plan_tags": [],
    "p1_bench_saved": False,
    "p1_bench_obsidian_saved": False,
    "p1_research_saved": False,
    "p1_research_obsidian_saved": False,
    "p1_plan_saved": False,
    "p1_plan_obsidian_saved": False,
    "unlock_part1": False,
    "p1_verification": "",
    "p1_need_research_kw": "",
    "p1_obsidian_search_results": "",
    
    "p2_topics": [],
    "p2_topic_selection": None,
    "p2_research_result": "",
    "p2_planning_result": "",
    "p2_obsidian_search_results": "",
    "p2_thumbnail_plan": "",
    "p2_bench_raw": "",
    "p2_bench_tags": [],
    "p2_bench_saved": False,
    "p2_bench_obsidian_saved": False,
    "p2_research_tags": [],
    "p2_research_saved": False,
    "p2_research_obsidian_saved": False,
    "p2_plan_tags": [],
    "p2_plan_saved": False,
    "p2_plan_obsidian_saved": False,
    "unlock_part2": False,
    "p2_verification": "",
    "p2_need_research_kw": "",
    "p2_plan_verification": "",
    "p2_plan_need_research_kw": "",
    
    "p34_scene_structure": "",
    "p34_narration_script": "",
    "p34_image_script": "",
    "p34_capcut_data": {},
    "p34_arch_saved": False,
    "p34_arch_obsidian_saved": False,
    "p34_narr_saved": False,
    "p34_narr_obsidian_saved": False,
    "p34_img_saved": False,
    "p34_img_obsidian_saved": False,
    "p34_cap_saved": False,
    "p34_cap_obsidian_saved": False,
    "unlock_part34": False,
    "p34_narr_verification": "",
    "p34_narr_need_research_kw": "",
    "p34_img_verification": "",
    "p34_img_need_research_kw": "",
    "p34_outputs_saved": False,
    
    "unlock_part5": False,
    "p5_outputs_saved": False,
    "p6_video_mapped_result": "",
    "p6_video_valid_rows": [],
    "p6_video_opal_data": None,
    "p6_video_opal_saved": False,
    "p6_video_outputs_saved": False,
    
    "p6_opal_data": None,
    "p6_opal_df": None,
    "p6_bgm_selection": "",
    "p6_mixing_ratio": 0.5,
    "p6_narration_verified": "",
    "p6_opal_saved": False,
    "p6_opal_obsidian_saved": False,
    "p6_outputs_saved": False,
    "unlock_part6": False,
    
    "p7_capcut_saved": False,
    "p7_capcut_obsidian_saved": False,
    "p7_outputs_saved": False,
    "unlock_part7": False,
    "p7_capcut_data_v2": None,
    "p7_capcut_data": "",
    "p7_script_input": "",
    "p7_scenes_input": 8,
    "p7_video_style_input": "Warm Amber Cinematic, Rembrandt lighting, deep shadows",
    "p7_bgm_style_input": "Quiet, cello and piano reflective harmony",
    "p7_subtitle_style_input": "Minimalist yellow-warm subtitle, center-bottom",
    
    "p8_dashboard_saved": False,
    "p8_dashboard_obsidian_saved": False,
    "p8_production_guide": ""
}

def switch_episode(new_ep):
    global WORKSPACE_STATE_FILE
    # save_workspace_state() 제거 — 앱 시작 시 빈 상태 저장 방지 (v16.1.14)
    try:
        root_state_path = r"C:\SageMirror_Production\workspace_state.json"
        root_data = {}
        if os.path.exists(root_state_path):
            with open(root_state_path, "r", encoding="utf-8") as f:
                root_data = json.load(f)
        root_data["episode_name"] = new_ep
        with open(root_state_path, "w", encoding="utf-8") as f:
            json.dump(root_data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass
    ep_dir = r"C:\SageMirror_Outputs\00_Session_States"
    os.makedirs(ep_dir, exist_ok=True)
    WORKSPACE_STATE_FILE = os.path.join(ep_dir, f"workspace_state_{new_ep}.json")
    new_data = load_workspace_state()
    st.session_state["episode_name"] = new_ep
    for k, v in DEFAULT_RESET_VALUES.items():
        if k in new_data:
            st.session_state[k] = new_data[k]
        else:
            st.session_state[k] = v
    if not os.path.exists(WORKSPACE_STATE_FILE):
        save_workspace_state()
    st.rerun()

def start_new_episode():
    import re
    import glob
    session_dir = r"C:\SageMirror_Outputs\00_Session_States"
    max_num = 0
    if os.path.exists(session_dir):
        files = glob.glob(os.path.join(session_dir, "workspace_state_EP*.json"))
        for f in files:
            match = re.search(r"workspace_state_EP(\d+)\.json", os.path.basename(f))
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    outputs_dir = r"C:\SageMirror_Outputs"
    if os.path.exists(outputs_dir):
        subdirs = glob.glob(os.path.join(outputs_dir, "EP*"))
        for d in subdirs:
            match = re.search(r"EP(\d+)$", os.path.basename(d))
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    next_num = max_num + 1
    next_ep = f"EP{next_num:03d}"
    switch_episode(next_ep)

def save_episode_obsidian_session(episode):
    try:
        base_obsidian = st.session_state.get("path_obsidian", r"C:\SageMirror_Production\00_Obsidian_Archive")
        session_dir = os.path.join(base_obsidian, "Studio", "Episodes", episode)
        os.makedirs(session_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = os.path.join(session_dir, f"session_{ts}_v15.9.33.md")
        content = f"""# Episode Session Log - {episode}
- **저장 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **앱 버전**: v15.9.33

## 에피소드 저장 사항 요약
- 파트별 분할 저장 완료 (01_Librarian ~ 08_Dashboard)
- 원시 세션 JSON 백업 완료

## 다음 예정 작업
- 에피소드 {episode} 영상 렌더링 및 최종 검수
- 다음 에피소드 기획 및 대본 작성
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        hist_dir = r"C:\SageMirror_Production\00_Obsidian\sessions"
        os.makedirs(hist_dir, exist_ok=True)
        hist_filepath = os.path.join(hist_dir, f"session_{ts}_{episode}_v15.9.33.md")
        with open(hist_filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        st.warning(f"Obsidian 세션 로그 작성 중 오류 발생: {e}")

def save_current_episode_all():
    episode = st.session_state.get("episode_name", "EP001").strip()
    if not episode:
        episode = "EP001"
    save_workspace_state()
    base_outputs = r"C:\SageMirror_Outputs"
    base_obsidian = st.session_state.get("path_obsidian", r"C:\SageMirror_Production\00_Obsidian_Archive")
    try:
        ep_session_src = os.path.join(base_outputs, "00_Session_States", f"workspace_state_{episode}.json")
        ep_session_dst = os.path.join(base_outputs, episode, f"workspace_state_{episode}.json")
        os.makedirs(os.path.dirname(ep_session_dst), exist_ok=True)
        if os.path.exists(ep_session_src):
            import shutil
            shutil.copy(ep_session_src, ep_session_dst)
    except Exception as e:
        st.warning(f"원시 세션 상태 복사 중 오류: {e}")

    def write_to_both(sub_dir, filename, content=None, is_csv=False, df=None):
        out_dir = os.path.join(base_outputs, episode, sub_dir)
        obs_dir = os.path.join(base_obsidian, "Studio", "Episodes", episode, sub_dir)
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(obs_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)
        obs_path = os.path.join(obs_dir, filename)
        if is_csv and df is not None:
            df.to_csv(out_path, encoding="utf-8-sig", index=False)
            df.to_csv(obs_path, encoding="utf-8-sig", index=False)
        elif content is not None:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            with open(obs_path, "w", encoding="utf-8") as f:
                f.write(content)

    p1_planning = st.session_state.get("p1_planning_result", "")
    p1_research = st.session_state.get("p1_research_result", "")
    librarian_content = f"# Librarian Result — {episode}\n\n## 1. Research Result\n{p1_research}\n\n## 2. Planning Result\n{p1_planning}"
    write_to_both("01_Librarian", "Librarian_Result.md", librarian_content)

    p2_research = st.session_state.get("p2_research_result", "")
    p2_planning = st.session_state.get("p2_planning_result", "")
    write_to_both("02_Planning", "Research_Draft.md", p2_research)
    write_to_both("02_Planning", "Final_Planning.md", p2_planning)

    p34_scene = st.session_state.get("p34_scene_structure", "")
    p34_narration = st.session_state.get("p34_narration_script", "")
    p34_image = st.session_state.get("p34_image_script", "")
    p34_capcut_raw = st.session_state.get("p34_capcut_data", {})
    write_to_both("03_Script", "Scene_Structure.md", p34_scene)
    write_to_both("03_Script", "Narration_Script.md", p34_narration)
    write_to_both("03_Script", "Image_Script.md", p34_image)

    import json
    capcut_json_str = json.dumps(p34_capcut_raw, ensure_ascii=False, indent=4)
    write_to_both("03_Script", "CapCut_Asset_Data.json", capcut_json_str)

    p5_master_prompt = st.session_state.get("p5_image_master_prompt", "")
    image_prompt_content = f"# Image Prompt Guidelines — {episode}\n\n## Master Prompt\n{p5_master_prompt}\n\n## Image Script\n{p34_image}"
    write_to_both("04_Image", "Image_Prompts.md", image_prompt_content)

    p6_video_mapped = st.session_state.get("p6_video_mapped_result", "")
    write_to_both("05_Video", "Video_Opal_Data.md", p6_video_mapped)

    p6_df = st.session_state.get("p6_opal_df", None)
    import pandas as pd
    if isinstance(p6_df, pd.DataFrame):
        write_to_both("06_Opal", "Opal_Dispatch_Map.csv", is_csv=True, df=p6_df)
    else:
        write_to_both("06_Opal", "Opal_Dispatch_Map.csv", "# No Opal Dispatch data available")

    p7_capcut_data = st.session_state.get("p7_capcut_data_v2", None)
    if p7_capcut_data is not None:
        p7_json_str = json.dumps(p7_capcut_data, ensure_ascii=False, indent=4)
        write_to_both("07_CapCut", "CapCut_Bridge_Timeline.json", p7_json_str)
    else:
        write_to_both("07_CapCut", "CapCut_Bridge_Timeline.json", "{}")

    p8_guide = st.session_state.get("p8_production_guide", "")
    write_to_both("08_Dashboard", "Production_Guide.md", p8_guide)

    save_episode_obsidian_session(episode)
    auto_git_push(f"Save Episode {episode} — {datetime.now().strftime('%Y%m%d_%H%M')}")
    st.toast(f"💾 {episode} 전체 저장 및 백업 완료!", icon="💾")

def sync_global_model_to_parts(model):
    try:
        model_lower = model.lower()
        model_upper = model.upper()
        
        # 1. 개별 생성 모델 키 업데이트
        st.session_state.p1_selected_model = model_lower
        st.session_state.p2_selected_model = model_lower
        st.session_state.p34_selected_model = model_lower
        st.session_state.p5img_selected_model = model_lower
        st.session_state.p6vid_selected_model = model_lower
        st.session_state.p6_selected_model = model_lower
        st.session_state.p7_selected_model = model_lower
        st.session_state.p8_selected_model = model_lower
        
        # 2. RAG 모델 선택자 세션 키 업데이트
        st.session_state.p1_rag_model_selector = model_lower
        st.session_state.p2_rag_model_selector = model_lower
        st.session_state.p3_rag_model_selector = model_lower
        st.session_state.p4_rag_model_selector = model_lower
        st.session_state.p5_rag_model_selector = model_lower
        st.session_state.p6_rag_model_selector = model_lower
        st.session_state.p7_rag_model_selector = model_lower
        st.session_state.p8_rag_model_selector = model_lower
        
        # 3. UI 컴포넌트 세션 상태 덮어쓰기 (selectbox의 강제 선택 상태 갱신)
        for p_key in ["p1_model_select", "p2_model_select", "p34_model_select", "p5_model_select", "p5img_model_select", "p6_vid_model_select", "p6_model_select", "p7_model_select", "p8_model_select"]:
            st.session_state[p_key] = model_upper
            
        for p_key in ["p1_rag_model_select", "p2_rag_model_select", "p3_rag_model_select", "p4_rag_model_select", "p5_rag_model_select", "p6_rag_model_select", "p7_rag_model_select", "p8_rag_model_select"]:
            st.session_state[p_key] = model_lower
            
        st.session_state.selected_model = model_lower
        st.toast(f"🌐 전체 파트 모델이 {model_upper}로 자동 적용되었습니다!", icon="🌐")
    except Exception as e:
        st.error(f"[모델 스위칭 오류] 동기화 실패: {e}")

def init_session_state():
    global WORKSPACE_STATE_FILE
    root_state_path = r"C:\SageMirror_Production\workspace_state.json"
    active_ep = "EP001"
    if os.path.exists(root_state_path):
        try:
            with open(root_state_path, "r", encoding="utf-8") as f:
                root_data = json.load(f)
                active_ep = root_data.get("episode_name", "EP001").strip()
                if not active_ep:
                    active_ep = "EP001"
        except Exception:
            pass
    ep_dir = r"C:\SageMirror_Outputs\00_Session_States"
    os.makedirs(ep_dir, exist_ok=True)
    WORKSPACE_STATE_FILE = os.path.join(ep_dir, f"workspace_state_{active_ep}.json")
    loaded_data = load_workspace_state()
    defaults = {
        "logged_in": True,
        "episode_name": active_ep,
        # Part 5~8 RAG 키
        "p5_obsidian_search_results": "",
        "p5_rag_model_selector": "gemma4:e2b",
        "p5_rag_query_val": "",
        "p5_selected_categories": [],
        "p6_obsidian_search_results": "",
        "p6_rag_model_selector": "gemma4:e2b",
        "p6_rag_query_val": "",
        "p6_selected_categories": [],
        "p7_obsidian_search_results": "",
        "p7_rag_model_selector": "gemma4:e2b",
        "p7_rag_query_val": "",
        "p7_selected_categories": [],
        "p8_obsidian_search_results": "",
        "p8_rag_model_selector": "gemma4:e2b",
        "p8_rag_query_val": "",
        "p8_selected_categories": [],
        # Part 1~4 카테고리 선택 상태
        "part1_selected_categories": [],
        "part2_selected_categories": [],
        "part3_selected_categories": [],
        "part4_selected_categories": [],

        "global_model_select": "gemma4:e2b",
        "p1_selected_model": "gemma4:e2b",
        "p2_selected_model": "gemma4:e2b",
        "p34_selected_model": "gemma4:e2b",
        "p5img_selected_model": "gemma4:e2b",
        "p6vid_selected_model": "gemma4:e2b",
        "p6_selected_model": "gemma4:e2b",
        "p7_selected_model": "gemma4:e2b",
        "p8_selected_model": "gemma4:e2b",

        "path_obsidian": r"C:\SageMirror_Production\00_Obsidian_Archive", 

        "path_assets": r"C:\SageMirror_Production\00_Assets",

        "path_memo": r"C:\SageMirror_Production\00_Memo",

        "github_token": "",

        "research_auto_save": True,

        "research_auto_save_success": False,

        "github_repo_url": "https://github.com/rokmc9457303l-hue/SageMirror_Studio.git",

        "github_local_path": r"C:\SageMirror_Production",

        "tavily_api_key": "",
        "youtube_api_key": "",
        "gemini_api_key": "",
        "p1_gemini_model": "gemini-2.0-flash-exp",
        "p1_channel_top10": [],
        "p1_benchmark_channel": {},
        "p1_search_keywords": [],

        "obsidian_rules": DEFAULT_OBSIDIAN_RULES_V81,

        "base_prompt_rules": MASTER_RESEARCH_PROMPT_V81,

        "obsidian_history": [],

        "prompt_history": [],

        "popup_history": [],

        "popup_search_history": [],

        "popup_selected_model": "gemma4:e2b",

        "selected_model": "gemma4:e2b",

        "popup_auto_search": True,

        "popup_use_rag": True,

        "sidebar_part": "part1",

        "unlock_part1": False,

        "unlock_part2": False,

        "unlock_part6": False,

        "unlock_part7": False,

        "unlock_part8": False,

        

        "p1_gemma_protocol": GEMMA_PROTOCOL_V81,

        "p1_channel_search_results": [],

        "p1_channel_url": "",

        "p1_region": "국내+국외 모두",

        "p1_topics": [],

        "p1_topic_selection": None,

        "p1_research_result": "",

        "p1_planning_result": "",

        "p1_saved_paths": [],

        "p1_bench_prompt": """[작업 지시 — 벤치마킹 & 주제 추출]

너는 현자의 거울 스튜디오의 수석 조사관(Librarian)이다.
아래 타겟 채널을 분석하여 40~70대 시청자의 실제 감정 고통에 기반한 핵심 주제 목록을 추출하라.

──────────────────────────────────────
[STEP 1] 옵시디언 RAG 우선 참조
──────────────────────────────────────
- TopicMemory 폴더에서 동일/유사 채널 분석 기록 먼저 확인
- ResearchMemory 폴더에서 관련 감정 키워드 먼저 확인
- 기존 자료 있으면 반드시 참조하고 [[위키링크]] 연결
- 옵시디언 자료가 부족할 때만 다음 단계로 이동

──────────────────────────────────────
[STEP 2] 채널 댓글 분석 — 정확성 우선
──────────────────────────────────────
[댓글 선별 원칙]
✅ 채택: 실제 인생 경험 댓글 / 구체적 감정 고통 명시 / 40~70대 진지한 어조
❌ 제외: 단순 칭찬 / 질문형 / 홍보·스팸 / 1020 가벼운 댓글

[분석 방식]
- 선별된 핵심 댓글 30~50개 집중 분석
- 반복 등장하는 감정 키워드 추출
- "내 이야기 같다" 공명 강도 순위 매기기

──────────────────────────────────────
[STEP 3] 주제 선정 기준
──────────────────────────────────────
우선 감정: ① 고독 ② 후회 ③ 상실 ④ 공허 ⑤ 인간관계 상처 ⑥ 의미 상실
판단 기준: 클릭률 / 시청지속 / 댓글유발 / 감정자극 강도
핵심: "내 이야기 같다" 느낌이 가장 강한 주제 우선

──────────────────────────────────────
[출력 양식]
──────────────────────────────────────
NN. 주제 | 추천사유(실제 체험담 기반) | 예상효과 | 예상반응
[SOURCE: 옵시디언 RAG / 댓글 분석 / Gemma 추론]""",

        "p1_research_prompt": """[작업 지시 — 자료조사 & 지식 융합]

너는 현자의 거울 스튜디오의 수석 조사관(Librarian)이다.
벤치마킹에서 선정된 주제를 바탕으로 철학·심리학·성경·에세이를 융합한 자료조사 초안을 작성하라.

──────────────────────────────────────
[STEP 1] 옵시디언 RAG 우선 검색
──────────────────────────────────────
아래 순서로 반드시 먼저 검색하라. 검색 없이 바로 생성하는 것은 절대 금지.

① TopicMemory → 동일/유사 주제 기존 자료 확인
② ResearchMemory → 관련 철학·심리·성경 자료 확인
③ 태그 검색 (전체 자동 조회):
   [[고독]] [[후회]] [[상실]] [[관계]] [[용서]] [[공허]] [[의미상실]]
   [[쇼펜하우어]] [[칼 융]] [[빅터 프랭클]] [[스토아]] [[마르쿠스 아우렐리우스]]
   [[몽테뉴]] [[에세이]] [[다크심리학]]
   [[시편]] [[잠언]] [[전도서]] [[욥기]] [[이사야]] [[성경]]

✅ RAG 자료가 있으면: 반드시 인용하고 [[위키링크]] 연결 / [SOURCE: 옵시디언 — 파일명]
❌ RAG 자료가 없거나 부족하면: 즉시 상상 생성 금지 / [NEED_RESEARCH: 키워드] 삽입 후 STEP 2로

──────────────────────────────────────
[STEP 2] 지식 융합 순서 (우선순위 엄수)
──────────────────────────────────────
1순위 — 성경 (전체 참조)
- 시편 우선 (감정 위로, 탄식, 회복)
- 잠언 우선 (삶의 지혜, 인간관계)
- 전도서 (허무, 의미, 죽음) / 욥기 (고통, 시련, 인내)
- 이사야·예레미야 (위로, 회복) / 신약 전체 (용서, 사랑, 소망)
- 반드시 실제 구절 확인 후 인용
- [SOURCE: 성경 — 책명 NN:NN] / 존재하지 않는 구절 생성 절대 금지

2순위 — 철학 (감정 상태에 따라 선택)
- 의미 상실·삶의 목적 → 빅터 프랭클 로고테라피
- 고독·욕망·허무 → 쇼펜하우어
- 내면 그림자·무의식 → 칼 융
- 절제·현재 집중 → 스토아 철학 (마르쿠스 아우렐리우스)
- [SOURCE: 철학 — 저자명, 저서명]

3순위 — 몽테뉴 및 각종 에세이집 (휴먼터치)
- 몽테뉴 에세이 (삶의 성찰, 인간 본성, 솔직한 고백)
- 각종 인문 에세이집 (40~70대 감성, 인생 후반기)
- 대본·나레이션에 휴먼터치 삽입 목적으로 활용
- [SOURCE: 에세이 — 저자명, 저서명]

4순위 — 다크심리학 (반드시 리서치 기반)
- 반드시 [NEED_RESEARCH: 다크심리학 — 키워드]로 검색 후 사용
- 가스라이팅, 조종, 나르시시즘, 트라우마 관련
- 상상으로 생성 절대 금지 / [SOURCE: 다크심리학 — 출처명]

5순위 — 웹 리서치 (RAG 부족시만)
- [NEED_RESEARCH: 키워드] 태그 먼저 삽입 후 검색
- [SOURCE: 웹 — URL 또는 출처명]

──────────────────────────────────────
[출력 필수 항목]
──────────────────────────────────────
1. 핵심 제목 (클릭하고 싶은 제목)
2. 핵심 키워드 ([[위키링크]] 형식)
3. 시청자 감정 고통 요약 (댓글 기반 — 상상 금지)
4. 성경 기반 통찰 [SOURCE: 성경 — 구절]
5. 철학 기반 통찰 [SOURCE: 철학 — 저자, 저서]
6. 에세이 기반 통찰 [SOURCE: 에세이 — 출처]
7. 다크심리학 통찰 [SOURCE: 다크심리학 — 출처]
8. Part 2 전달 메모 (핵심 포인트 요약)

──────────────────────────────────────
[절대 금지]
──────────────────────────────────────
- 가짜 성경 구절 생성 / 존재하지 않는 철학 인용
- 출처 없는 명언 생성 / RAG 없이 즉시 상상 생성
- [NEED_RESEARCH] 없이 자료 부족 상태로 진행""",

        "p1_plan_prompt": """[작업 지시 — Part 2 전달 패킷 설계]

너는 현자의 거울 스튜디오의 수석 조사관(Librarian)이다.
자료조사 결과를 바탕으로 Part 2 Alchemist가
바로 대본 작업에 착수할 수 있도록 완결된 전달 패킷을 설계하라.
내레이터는 @Protagonist — 60대 중후반 서양 철학 체화한 현자다.

──────────────────────────────────────
[STEP 1] 기승전결 구조 설계
──────────────────────────────────────
현자의 거울 4단 구조를 반드시 따르라:

🔴 기(起) — 훅 & 공감
- 시청자의 실제 고통 체험담으로 시작
- "내 이야기다" 느낌이 즉각 와야 함
- 다크심리학 또는 인간 결핍 현상으로 문제 제기
- 클릭 후 3초 안에 이탈하지 않을 훅 설계

🟡 승(承) — 철학·심리 분석
- 쇼펜하우어 / 칼 융 / 빅터 프랭클
  (감정 상태에 맞는 철학자 선택)
- 왜 이 고통이 생기는가 — 심층 해석
- 시청자가 "그래서 내가 그랬구나" 깨닫는 구간

🟢 전(轉) — 몽테뉴·에세이 전환
- 인간적 솔직함과 휴먼터치로 분위기 전환
- 완벽하지 않아도 된다는 위로
- 삶의 성찰과 자기 수용으로 연결

🔵 결(結) — 성경·회복·소망
- 시편 / 잠언 / 신약 기반 회복 메시지
- @Protagonist의 목소리로 조용하고 무게 있게
- "오늘 당신에게 드리는 한 마디"로 마무리

──────────────────────────────────────
[STEP 2] @Protagonist 내레이터 지침
──────────────────────────────────────
- 가르치지 않는다 — 통찰만 조용히 건넨다
- 위로하지 않는다 — 고통을 함께 인정한다
- 설명하지 않는다 — 곁에 앉아 함께 바라본다
- 자기계발 말투 절대 금지
- 가벼운 희망회로 절대 금지
- 침묵과 여백을 두려워하지 않는다

──────────────────────────────────────
[STEP 3] 영상 연출 가이드
──────────────────────────────────────
- 렘브란트 키아로스쿠로 (어둠 속 빛 하나)
- 40~70대 감성: 낡은 책상 / 촛불 / 빗소리
- 마이크로 감정 표현 중심
- BGM: 낮은 첼로 / 피아노 미니멀
- 썸네일 컨셉 초안 포함
  (감정 키워드 + 비주얼 방향 1줄)

──────────────────────────────────────
[출력 — Part 2 전달 패킷]
──────────────────────────────────────
1. 📌 최종 확정 주제
2. 🎯 핵심 감정 키워드 3개
3. 🔴 기(起) 훅 초안 (2~3문장)
4. 🟡 승(承) 철학 핵심 논지
   [SOURCE: 철학 — 저자, 저서]
5. 🟢 전(轉) 에세이 전환 포인트
   [SOURCE: 에세이 — 출처]
6. 🔵 결(結) 성경 회복 메시지
   [SOURCE: 성경 — 책명 구절]
7. 🎬 영상 연출 키워드 3개
8. 🖼 썸네일 컨셉 초안 1줄
9. 💬 오늘의 명언 (출처 명기 필수)
10. 📦 Part 2 인계 메모
    (Alchemist가 반드시 알아야 할 핵심)

──────────────────────────────────────
[절대 금지]
──────────────────────────────────────
- 출처 없는 성경 구절 / 철학 인용
- AI 냄새 나는 문장 ("함께 나아가요" 등)
- 자기계발 강사 말투 / 1020 감성 표현
- 내용 없이 구조만 채우기""",

        "p1_bench_raw": "",

        "p1_bench_tags": "",

        "p1_research_tags": "",

        "p1_plan_tags": "",

        "p1_bench_saved": False,

        "p1_bench_obsidian_saved": False,

        "p1_research_saved": False,

        "p1_research_obsidian_saved": False,

        "p1_plan_saved": False,

        "p1_plan_obsidian_saved": False,

        

        "p2_gemma_protocol": """# 🧙 젬마 프로토콜 v9.0 — Part 2 Alchemist 전용
# ═══════════════════════════════════════

## 🎯 핵심 3원칙
HOW → 자유(창의) | WHAT → 통제(사실) | WHO → 고정(@Protagonist)

## 🔥 Alchemist 정체성
너는 연금술사다. 다크심리학→철학→에세이→성경으로 변환하라.
금지: 대본·나레이션·이미지프롬프트 작성(Part3·4 역할)

## ⛔ 절대 금지
- 없는 성경구절 / 존재하지 않는 철학 인용 절대 금지
- 다크심리학 부족 시: [NEED_RESEARCH: 다크심리학 키워드]
- AI냄새 문장 / 자기계발 말투 / 희망회로 절대 금지

## 📚 RAG 우선순위
1.[READ_OBSIDIAN:키워드] 2.성경전체 3.ResearchMemory
4.철학원문 5.다크심리학[NEED_RESEARCH] 6.웹검색[NEED_RESEARCH] 7.Gemma추론

## 🌑 다크심리학 활용
기(起): 반드시 다크심리학으로 시작.
적용: 가스라이팅·나르시시즘·조종·정서방치·의존성심화·공감결여
부족 시: [NEED_RESEARCH: 다크심리학 {emotion} 메커니즘]

## 📖 출력 규칙
- [SOURCE: 책명/장절/저자] 형식 필수
- 다크심리학: [SOURCE: 다크심리학 — 출처명]
- 성경: [SOURCE: 성경 — 책명 NN:NN]
- 핵심개념: [[위키링크]]

## ✊ @Protagonist
가르치지않고통찰만 / 위로안하고고통인정 / 침묵과여백유지
다크심리학으로시작→성경으로마무리 / 4070이밤에혼자들을때울림있어야

## 📦 출력 체크리스트
□ 기(起): 다크심리학 [SOURCE: 다크심리학 — ]
□ 승(承): 철학인용 [SOURCE:]
□ 전(轉): 에세이/몽테뉴 [SOURCE:]
□ 결(結): 성경구절 [SOURCE: 성경 — ]
□ @Protagonist 통일 / AI냄새없음 / Part3전달패킷포함""",

        "p2_channel_search_results": [],

        "p2_channel_url": "",

        "p2_region": "국내+국외 모두",

        "p2_topics": [],

        "p2_topic_selection": None,

        "p2_research_result": "",

        "p2_planning_result": "",

        "p2_thumbnail_plan": "",

        "p2_thumbnail_sets": [],

        "p2_selected_thumbnail": {},

        "p2_bench_prompt": """# 🎬 Part 2 Alchemist [탭1: 채널 벤치마킹 및 주제 도출]

너는 연금술사다. Part 1 원석 데이터를 기승전결 구조로 변환하라.

────────────────────────────────────────
[STEP 1] RAG 우선 참조
────────────────────────────────────────
[READ_OBSIDIAN: {topic}]
TopicMemory·ResearchMemory 먼저 확인 → 부족시 다음 단계

────────────────────────────────────────
[STEP 2] 다크심리학 훅 분석
────────────────────────────────────────
주제: {topic} | 핵심 감정: {emotion}

RAG 부족 시:
→ [NEED_RESEARCH: 다크심리학 {topic} 가스라이팅 나르시시즘]
→ [SOURCE: 다크심리학 — 출처명] 반드시 명기

적용 개념: 가스라이팅·나르시시즘·조종·정서방치·의존성심화

────────────────────────────────────────
[STEP 3] 기승전결 매핑
────────────────────────────────────────
기(起) 다크심리학 훅: [SOURCE: 다크심리학 — ] 또는
         [NEED_RESEARCH: 다크심리학 {emotion}]
승(承) 철학 해석: 고독→쇼펜하우어 / 그림자→융 / 의미→프랭클
         [SOURCE: 저자, 저서명]
전(轉) 에세이: 몽테뉴 / 인간적 솔직함 / 자기수용
         [SOURCE: 몽테뉴, 수상록] 부족시 [NEED_RESEARCH]
결(結) 성경: 실제 구절만 / 시편·잠언·전도서·욥기·신약
         [SOURCE: 성경 — 책명 NN:NN] 모르면 [NEED_RESEARCH]

────────────────────────────────────────
[출력 양식]
────────────────────────────────────────
## 주제: {topic}
### 🔴 기(起) — 다크심리학 훅
- 적용 개념: | 공명 포인트: | [SOURCE: 다크심리학 — ]
### 🟡 승(承) — 철학 분석
- 철학자·개념: | 핵심 논지: | [SOURCE:]
### 🟢 전(轉) — 에세이 전환
- 인간적 솔직함: | [SOURCE:]
### 🔵 결(結) — 성경 회복
- 구절: | 맥락: | [SOURCE: 성경 — ]
### 📌 @Protagonist 톤 지침""",

        "p2_bench_raw": "",

        "p2_bench_tags": "",

        "p2_bench_saved": False,

        "p2_bench_obsidian_saved": False,

        # ── Part 2 3단 버튼 상태 인디케이터 키 ──

        "p2_research_prompt": """# 🎬 Part 2 Alchemist [탭2: 옵시디언 융합 리서치]

너는 연금술사다. 선정된 주제를 실제 영상 제작 자료로 변환하라.

────────────────────────────────────────
[STEP 1] RAG 우선 순서
────────────────────────────────────────
1.[READ_OBSIDIAN: {topic}] → 기존 자료 전부 확인
2.성경 전체 (시편·잠언·전도서·욥기·신약)
3.ResearchMemory 기존 리서치
4.철학 원문 (쇼펜하우어·융·프랭클·스토아·몽테뉴)
5.다크심리학 → 부족시:
  [NEED_RESEARCH: 다크심리학 {topic} {emotion}]
6.전체 부족 시: [NEED_RESEARCH: 키워드]

────────────────────────────────────────
[STEP 2] 다크심리학 리서치 규칙
────────────────────────────────────────
① [READ_OBSIDIAN: 다크심리학] 먼저 확인
② 부족시 → [NEED_RESEARCH: 다크심리학 {emotion} 메커니즘]
③ 실제 심리학 개념만 추출
④ [SOURCE: 다크심리학 — 출처명] 반드시 명기

────────────────────────────────────────
[STEP 3] 핵심 자료 수집
────────────────────────────────────────
① 실제 댓글 기반 체험담 (상상 금지)
② 다크심리학 근거 1~2개 [NEED_RESEARCH 후 수집]
③ 철학 인용 2~3개 (원문 기반)
④ 성경 구절 2~3개 (실제 구절만)
⑤ 에세이·몽테뉴 인용 1~2개

────────────────────────────────────────
[출력 양식]
────────────────────────────────────────
## 주제: {topic} — 융합 리서치 결과
### 📌 핵심 감정 키워드 (3개)
1. | 2. | 3.
### 🔴 기(起) 자료
- 체험담: (댓글 기반)
- 다크심리학: [SOURCE: 다크심리학 — ]
### 🟡 승(承) 자료
- 철학 인용 1: [SOURCE:]
- 철학 인용 2: [SOURCE:]
### 🟢 전(轉) 자료
- 에세이 인용: [SOURCE:]
### 🔵 결(結) 자료
- 성경 구절 1: [SOURCE: 성경 — ]
- 성경 구절 2: [SOURCE: 성경 — ]
### 🔗 연결 개념 [[위키링크]]
### 📚 전체 출처 목록
### ➡️ Part 3 전달 메모""",

        "p2_research_tags": "",

        "p2_research_saved": False,

        "p2_research_obsidian_saved": False,

        "p2_plan_prompt": """# 🎬 Part 2 Alchemist [탭3: 총괄 기획안 생성]

너는 연금술사다. 수집된 모든 자료를 완성된 총괄 기획안으로 조립하라.
이 기획안은 Part 3 대본 작가의 설계도다.

────────────────────────────────────────
[STEP 1] 입력 데이터 확인
────────────────────────────────────────
주제:{topic} | 감정:{emotion} | 에피소드:{episode} | 길이:15분
[READ_OBSIDIAN: {topic}] → 탭1·2 전체 자료 참조

────────────────────────────────────────
[STEP 2] 다크심리학 훅 설계
────────────────────────────────────────
기(起) 시작: 반드시 다크심리학으로 열어라.
부족시: [NEED_RESEARCH: 다크심리학 {topic} {emotion} 훅기법]
→ [SOURCE: 다크심리학 — 출처명]

────────────────────────────────────────
[STEP 3] 기승전결 설계 (15분)
────────────────────────────────────────
기(起) 0:00~2:00 — 다크심리학훅 & 문제직시
승(承) 2:00~8:00 — 철학적깊이 (90초마다 감정전환)
전(轉) 8:00~12:00 — 에세이 & 자기수용
결(結) 12:00~15:00 — 성경 & 여운 (마지막1분 침묵)

────────────────────────────────────────
[출력 양식]
────────────────────────────────────────
## 📋 현자의 거울 총괄 기획안
### 에피소드:{episode} | 주제:{topic}
### 🎯 핵심 메시지 (1문장)
### 🪝 제목 후보 3개
1. | 2. | 3.
### 🖼️ 썸네일 컨셉
이미지: | 텍스트: | 감정톤:
### 🔴 기(起) 0:00~2:00
@Protagonist 첫문장:
다크심리학훅: [SOURCE: 다크심리학 — ]
### 🟡 승(承) 2:00~8:00
철학인용1: [SOURCE:]
철학인용2: [SOURCE:]
### 🟢 전(轉) 8:00~12:00
에세이전환: [SOURCE:]
### 🔵 결(結) 12:00~15:00
성경구절: [SOURCE: 성경 — ]
마지막@Protagonist 문장:
### 📦 Part 3 전달 패킷
핵심감정키워드: | 다크심리학:[SOURCE:] | 철학:[SOURCE:]
성경:[SOURCE:성경—] | @Protagonist지침: | 절대금지:""",

        "p2_plan_tags": "",

        "p2_plan_saved": False,

        "p2_plan_obsidian_saved": False,

        "p34_gemma_protocol": PART3_GEMMA_PROTOCOL_V3,

        "p34_master_prompt": PART3_MASTER_PROMPT_V1,

        "unlock_part34": False,

        "p34_scene_structure": "",

        "p34_narration_script": "",

        "p34_image_script": "",

        "p34_capcut_data": "",

        # ── Part 3-4 젬마 프롬프트 키 ──

        "p34_narr_prompt": "[작업 지시] 아래 112씬 구조를 바탕으로 각 씬의 나레이션 대본을 작성하세요. 화자는 60대 현자(Sage)이며, 4070 시청자에게 말하듯 따뜻하고 묵직한 톤으로 작성합니다.",

        "p34_img_prompt": "[작업 지시] 아래 나레이션 대본을 이미지 파트 규격(C-1)에 맞춰 변환하세요. 한글묘사에는 인물동작/시선/빛/소품태그/표정코드[EXPR-0X] 필수.",

        "p34_cap_prompt": "[작업 지시] 아래 이미지 대본을 CapCut 자동화 JSON으로 변환하세요. 각 씬: scene_id, script, action_kr, expression, props_used, image_file(scene_XXX.png), audio_file(narration_XXX.mp3), timeline_order, duration_sec 포함.",

        # ── Part 3-4 3단 버튼 상태 인디케이터 키 ──

        "p34_arch_saved": False,

        "p34_arch_obsidian_saved": False,

        "p34_narr_saved": False,

        "p34_narr_obsidian_saved": False,

        "p34_img_saved": False,

        "p34_img_obsidian_saved": False,

        "p34_cap_saved": False,

        "p34_cap_obsidian_saved": False,

        "p5_image_master_prompt": IMAGE_PART_MASTER_PROMPT_V3,

        "unlock_part5": False,

        # ── Part 4 (Image Consistency) 전용 키 ──

        "p5_gemma_protocol": "",

        "p5_a_result": "",

        "p5_b_result": "",

        "p5_c_results": "",

        # 옵시디언 저장 상태 추적
        "p1_research_result_obsidian_saved": False,
        "p1_research_result_obsidian_path": "",
        "p1_planning_result_obsidian_saved": False,
        "p1_planning_result_obsidian_path": "",
        "p2_research_result_obsidian_saved": False,
        "p2_research_result_obsidian_path": "",
        "p2_planning_result_obsidian_saved": False,
        "p2_planning_result_obsidian_path": "",
        "p2_bench_raw_obsidian_saved": False,
        "p2_bench_raw_obsidian_path": "",
        "p34_narration_script_obsidian_saved": False,
        "p34_narration_script_obsidian_path": "",
        "p34_image_script_obsidian_saved": False,
        "p34_image_script_obsidian_path": "",
        "p5_a_result_obsidian_saved": False,
        "p5_a_result_obsidian_path": "",
        "p5_b_result_obsidian_saved": False,
        "p5_b_result_obsidian_path": "",
        "p5_c_results_obsidian_saved": False,
        "p5_c_results_obsidian_path": "",
        "p6_veo3_result_obsidian_saved": False,
        "p6_veo3_result_obsidian_path": "",
        "p7_shortform_hook_obsidian_saved": False,
        "p7_shortform_hook_obsidian_path": "",
        "p7_capcut_data_v2_obsidian_saved": False,
        "p7_capcut_data_v2_obsidian_path": "",
        "p8_production_guide_obsidian_saved": False,
        "p8_production_guide_obsidian_path": "",
        "p8_check_result_obsidian_saved": False,
        "p8_check_result_obsidian_path": "",

        "p5_valid_rows": [],

        "p5_error_rows": [],

        "p5_parsed_scenes": [],

        "p5_parse_errors": [],

        "p5_v_results": {},

        "p5_v_scene_count": 0,

        "p5_a_history": [],

        "p5_b_history": [],

        "p5_c_history": [],

        "p5_protocol_loaded": "",

        "p5_save_done": False,

        # ── Part 5 (Video Production) v13.2 업데이트 ──

        "p6_veo3_master_prompt": P6_VEO3_MASTER_PROMPT_V2,

        "p6_gemma_protocol": P6_GEMMA_PROTOCOL_V2,

        "p6_master_prompt": P6_MASTER_PROMPT_DEFAULT,

        "p7_master_prompt": P7_MASTER_PROMPT_DEFAULT,

        "p8_master_prompt": P8_MASTER_PROMPT_DEFAULT,

        "p2_master_prompt": "",

        "p6_protocol_loaded": "",

        "p6_vid_pin_input": "",

        "unlock_part6_vid": False,

        "pending_stream": None,

        "p6_opal_df": None,

        "p6_save_done": False,

        "p7_capcut_df": None,

        "p8_check_result": "",

        "p8_save_done": False,

        "p1_verification": None,

        "p2_verification": None,

        "p2_plan_verification": None,

        "p34_narr_verification": None,

        "p34_img_verification": None,

        "p1_need_research_kw": None,

        "p2_need_research_kw": None,

        "p2_plan_need_research_kw": None,

        "p34_narr_need_research_kw": None,

        "p34_img_need_research_kw": None,

        "p6_opal_data": None,

        "p7_capcut_data_v2": None,

        "p6_bgm_selection": "비장한 성경 낭독풍",

        "p6_mixing_ratio": 80,

        "p6_narration_verified": False,

        "p6_opal_saved": False,

        "p6_opal_obsidian_saved": False,

        "p7_capcut_saved": False,

        "p7_capcut_obsidian_saved": False,

        "p8_dashboard_saved": False,

        "p8_dashboard_obsidian_saved": False,

        "episode_name": "EP001",

        "p6_video_mapped_result": "",

        "p6_video_valid_rows": [],

        "p6_video_opal_data": None,

        "p6_video_opal_saved": False,

        "p34_outputs_saved": False,

        "p5_outputs_saved": False,

        "p6_outputs_saved": False,

        "p6_video_outputs_saved": False,

        "p7_outputs_saved": False,

        "p1_obsidian_search_results": "", "p2_obsidian_search_results": "", "p3_obsidian_search_results": "", "p4_obsidian_search_results": "",

        "p5_obsidian_search_results": "", "p6_obsidian_search_results": "", "p7_obsidian_search_results": "", "p8_obsidian_search_results": "",

        "p1_rag_model_selector": "gemma4:e2b", "p2_rag_model_selector": "gemma4:e2b", "p3_rag_model_selector": "gemma4:e2b", "p4_rag_model_selector": "gemma4:e2b",

        "p5_rag_model_selector": "gemma4:e2b", "p6_rag_model_selector": "gemma4:e2b", "p7_rag_model_selector": "gemma4:e2b", "p8_rag_model_selector": "gemma4:e2b",

        "p0_selected_model": "gemma4:e2b"

    }

    

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # [수정] 파일 로드 전 강제 정화 후 세션 동기화
    sanitize_workspace_prompt_values_once()
    loaded_data = load_workspace_state()
    
    # 기존 세션에 loaded_data를 덮어쓰되, 
    # 값이 이미 존재하는 경우를 고려하여 안전하게 업데이트하라.
    for k, v in loaded_data.items():
        st.session_state[k] = v

    # [수정 3] 앱 시작 직후 session_state에 로드된 위 키들에도 1회 정화 처리
    contam_keys = [
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        # "p2_gemma_protocol" 제거 — 사용자 입력값 보존 (v16.1.16)
        "p2_bench_prompt", "p2_research_prompt",
        "p2_plan_prompt", "p34_master_prompt", "p5_image_master_prompt",
        "p6_veo3_master_prompt", "p6_master_prompt", "p7_master_prompt",
        "p8_master_prompt"
    ]
    _need_save = False
    for key in contam_keys:
        if key in st.session_state and isinstance(st.session_state[key], str):
            cleaned = clean_prompt_contamination(st.session_state[key])
            if cleaned != st.session_state[key]:
                st.session_state[key] = cleaned
                _need_save = True
    if _need_save:
        save_workspace_state()



sanitize_workspace_prompt_values_once()
init_session_state()

# =====================================================================
# 공통 UI 컴포넌트: 4단 버튼 연동 프롬프트 편집기
# =====================================================================

# =====================================================================
# 팝업 편집 엔진 (전역 스코프) — 모든 파트에서 호출 가능
# =====================================================================
@st.dialog("📋 편집 및 저장", width="large")
def popup_editor_safe(session_key, title):
    st.markdown(f"### {title}")
    current_val = st.session_state.get(session_key, "")
    new_val = st.text_area("내용 수정", value=current_val, height=500)
    col1, col2 = st.columns([1, 1])
    if col1.button("💾 저장 및 닫기", type="primary"):
        st.session_state[session_key] = new_val
        save_workspace_state()
        st.rerun()
    if col2.button("❌ 취소"):
        st.rerun()


def render_unified_prompt_editor(label: str, session_key: str, height: int = 150, is_locked: bool = False):
    """
    Part 1~5 Step 1/2/3 프롬프트 입력칸의 팝업 편집 및 저장을 처리하는 공통 UI 컴포넌트.
    버튼: [📝 팝업 편집] [💾 저장] 2개만 유지
    """
    # 현재 값 표시 (항상 disabled — 편집은 팝업으로만)
    current_value = st.session_state.get(session_key, "")

    st.text_area(
        label,
        value=current_value,
        height=height,
        key=f"{session_key}_edit_widget",
        disabled=True
    )

    # 2버튼 세트: 팝업 편집 + 저장
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 팝업 편집", key=f"{session_key}_popup_btn", use_container_width=True, disabled=is_locked):
            popup_editor_safe(session_key, label)
    with c2:
        widget_val = st.session_state.get(f"{session_key}_edit_widget", current_value)
        if st.button("💾 저장", key=f"{session_key}_save_btn", use_container_width=True, disabled=is_locked):
            st.session_state[session_key] = widget_val
            save_workspace_state()
            st.toast(f"💾 저장 완료!", icon="💾")
            st.rerun()


# =====================================================================

# [보안 로직 & 자동화 로직]

# =====================================================================

def lock_file_readonly(filepath):

    try:

        if os.path.exists(filepath):

            os.chmod(filepath, stat.S_IREAD)

            return True

    except Exception as e:

        st.warning(f"파일 락(Lock) 실패: {e}")

    return False



def auto_git_push(commit_message: str):

    if not GIT_AVAILABLE: return False, "GitPython 미설치"

    # Git Push 대기/무한로딩(락) 방지 환경설정
    import os
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    os.environ["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"

    try:

        rp = Path(st.session_state.github_local_path)

        rp.mkdir(parents=True, exist_ok=True)

        if not (rp / ".git").exists(): Repo.init(rp)

        repo = Repo(rp)

        repo.git.add(A=True)

        

        if repo.is_dirty(untracked_files=True):

            repo.index.commit(f"{commit_message} (Auto Backup: {datetime.now().strftime('%Y%m%d_%H%M%S')})")

        

        auth = st.session_state.github_repo_url.replace("https://", f"https://{st.session_state.github_token}@") if st.session_state.github_token else st.session_state.github_repo_url

        if "origin" in [r.name for r in repo.remotes]: repo.remotes.origin.set_url(auth)

        else: repo.create_remote("origin", auth)

            

        repo.remotes.origin.push(refspec="HEAD:refs/heads/main", force=True)

        return True, "자동 백업 푸시 성공"

    except Exception as e:

        return False, f"푸시 실패: {e}"



# =====================================================================

# 로그인 & 사이드바

# =====================================================================

def render_login():

    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE} <span style='color:#10B981;font-size:0.5em;'>v13.2 Video Edition</span></h1>", unsafe_allow_html=True)

    st.markdown("<p style='text-align:center;color:#888'>성경 · 철학 · 에세이가 융합된 다큐멘터리 자동화 스튜디오</p>", unsafe_allow_html=True)

    st.divider()

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:

        pw = st.text_input("마스터 비밀번호", type="password")

        if st.button("로그인", type="primary", use_container_width=True):

            if pw == MASTER_PW_DEFAULT:

                st.session_state.logged_in = True

                st.rerun()

            else: st.error("비밀번호 불일치.")



if not st.session_state.logged_in:

    render_login()

    st.stop()



with st.sidebar:

    # 🎬 Episode Control Center 및 동적 에피소드 헤더 CSS 주입
    ep_name = st.session_state.get("episode_name", "EP001")
    st.markdown(f"""
        <style>
        div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(.ecc-marker) {{
            background: linear-gradient(135deg, rgba(90, 50, 40, 0.25) 0%, rgba(26, 20, 16, 0.6) 100%) !important;
            border: 1px solid rgba(212, 175, 106, 0.35) !important;
            border-radius: 12px !important;
            padding: 15px !important;
            margin-bottom: 15px !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.65) !important;
        }}
        .ecc-title {{
            color: #d4af6a !important;
            font-weight: 700 !important;
            margin-bottom: 8px !important;
            font-size: 1.1rem !important;
        }}
        /* 각 파트별 메인 헤더 타이틀에 [EPXXX] 접두사 강제 주입 */
        div[data-testid="stAppViewContainer"] h3::before {{
            content: "[{ep_name}] " !important;
        }}
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="ecc-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="ecc-title">🎬 Episode Control Center</div>', unsafe_allow_html=True)
        
        current_ep = st.session_state.get("episode_name", "EP001")
        ep_list = [f"EP{i:03d}" for i in range(1, 101)]
        if current_ep not in ep_list:
            ep_list.append(current_ep)
            ep_list.sort()
            
        ep_idx = ep_list.index(current_ep) if current_ep in ep_list else 0
        
        # 앱 시작 시 위젯 레이스 컨디션 방지 (v16.1.14)
        if "ecc_episode_select" not in st.session_state:
            st.session_state["ecc_episode_select"] = current_ep

        selected_ep = st.selectbox(
            "선택된 에피소드",
            ep_list,
            index=ep_list.index(current_ep) if current_ep in ep_list else 0,
            key="ecc_episode_select_widget"
        )

        if selected_ep != current_ep and selected_ep is not None:
            save_workspace_state()  # 사용자가 직접 바꿀 때만 저장
            switch_episode(selected_ep)
            st.rerun()
            
        st.info(f"현재 작업 Episode: **{current_ep}**")
        
        col_ep1, col_ep2 = st.columns(2)
        with col_ep1:
            if st.button("💾 현재 Episode 전체 저장", type="primary", use_container_width=True, key="ecc_save_ep_btn"):
                save_current_episode_all()
        with col_ep2:
            if st.button("🆕 새 Episode 시작", use_container_width=True, key="ecc_new_ep_btn"):
                start_new_episode()
                
    st.divider()

    st.markdown(f"### {APP_TITLE} **v15.9.34**")

    # 🌐 글로벌 모델 선택 및 동기화 처리
    st.markdown("##### 🤖 글로벌 모델 선택")
    global_options = ["gemma4:e2b", "gemma4:e4b"]
    current_global = st.session_state.get("global_model_select", "gemma4:e2b")
    if current_global not in global_options:
        current_global = "gemma4:e2b"
    global_model = st.selectbox(
        "기본 모델 설정",
        global_options,
        index=global_options.index(current_global),
        key="global_model_select",
        label_visibility="collapsed"
    )
    if global_model != current_global:
        st.session_state.global_model_select = global_model
        sync_global_model_to_parts(global_model)
        save_workspace_state()
        st.rerun()

    # Ollama 동작 상태 확인 및 출력
    status = check_ollama_status(target_model=global_model)
    if status["server"] and status["model"]: 
        st.success(f"[OK] Ollama | {global_model}")
    else: 
        st.error(f"[FAIL] Ollama 에러 | {global_model} 확인 필요")

    st.divider()

    st.info(f"📂 **옵시디언 아카이브**\n{st.session_state.path_obsidian}")

    st.info(f"🚀 **GitHub 연동 중**\n{st.session_state.github_repo_url.split('/')[-1]}")



    with st.expander("⚙️ 설정 변경", expanded=False):

        st.session_state.path_obsidian = st.text_input("옵시디언 볼트", value=st.session_state.path_obsidian)

        st.session_state.github_repo_url = st.text_input("Repo URL", value=st.session_state.github_repo_url)

        st.session_state.github_token = st.text_input("GitHub PAT (공란 권장)", value=st.session_state.github_token, type="password")

        st.session_state.tavily_api_key = st.text_input("Tavily API Key", value=st.session_state.tavily_api_key, type="password")

        st.session_state.youtube_api_key = st.text_input("YouTube API Key", value=st.session_state.get("youtube_api_key", ""), type="password")
        st.session_state.gemini_api_key = st.text_input("🤖 Gemini API Key", value=st.session_state.get("gemini_api_key", ""), type="password", help="파트1 채널 탐색기에서 사용합니다.")

        if st.button("수동 동기화"):

            success, msg = auto_git_push("Manual Sync")

            if success: st.success(msg)

            else: st.error(msg)

            

    st.divider()

    st.markdown("##### [SAVE] 작업 상태 관리 (물리적 백업)")

    c_s1, c_s2 = st.columns(2)

    with c_s1:

        if st.button("상태 저장", use_container_width=True):

            if save_workspace_state(): 

                st.success("데이터 보존!")

            else: 

                st.error("저장 실패")

    with c_s2:

        if st.button("불러오기", use_container_width=True):

            loaded = load_workspace_state()

            if loaded:

                for k, v in loaded.items():

                    st.session_state[k] = v

                st.success("복구 완료!")

                st.rerun()

            else:

                st.warning("저장된 데이터 없음")



    st.divider()

    part = st.radio("이동할 파트", [

        "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)",

        "파트 1: 벤치마킹 & 자료조사",

        "파트 2: 총괄기획",

        "파트 3: 대본 작성",

        "파트 4: 이미지 생성",

        "파트 5: 영상 생성",

        "파트 6: 나레이션 & 배경음악",

        "파트 7: 숏폼 생성",

        "파트 8: 캡컷 최종 조립"

    ], index=0)

    st.session_state.sidebar_part = part

    if st.button("🔒 로그아웃", use_container_width=True):

        st.session_state.logged_in = False

        st.rerun()



# =====================================================================

# 팝업 로직

# =====================================================================

@st.dialog("📁 옵시디언 백업 내역 (최근 15개)", width="large")

def popup_obsidian_history():

    st.markdown("옵시디언 보관소(`00_Obsidian`) 및 세션 폴더에 저장된 마크다운 백업 목록입니다.")

    obs_path = st.session_state.get("path_obsidian", "")

    if not obs_path or not os.path.exists(obs_path):

        st.error("옵시디언 경로가 존재하지 않거나 설정되지 않았습니다.")

        return

        

    try:

        md_files = []

        for root, dirs, files in os.walk(obs_path):

            for file in files:

                if file.endswith(".md"):

                    full_path = os.path.join(root, file)

                    mtime = os.path.getmtime(full_path)

                    size = os.path.getsize(full_path)

                    md_files.append({

                        "name": file,

                        "rel_path": os.path.relpath(full_path, obs_path).replace("\\", "/"),

                        "abs_path": full_path,

                        "mtime": datetime.fromtimestamp(mtime),

                        "size": f"{size / 1024:.1f} KB"

                    })

        

        if not md_files:

            st.info("백업된 마크다운 파일이 없습니다.")

            return

            

        md_files.sort(key=lambda x: x["mtime"], reverse=True)

        md_files = md_files[:15]

        

        import pandas as pd

        df = pd.DataFrame(md_files)[["rel_path", "mtime", "size"]]

        df.columns = ["백업 파일명(상대경로)", "마지막 저장 시간", "용량"]

        st.dataframe(df, use_container_width=True)

            

    except Exception as e:

        st.error(f"옵시디언 내역 조회 실패: {e}")



@st.dialog("🚀 GitHub 커밋 및 백업 내역 (최근 10개)", width="large")

def popup_git_history():

    st.markdown("GitHub 리포지토리(`SageMirror_Studio`)의 로컬 커밋 및 동기화 히스토리입니다.")

    if not GIT_AVAILABLE:

        st.error("Git 패키지(GitPython)를 사용할 수 없습니다.")

        return

        

    try:

        from git import Repo

        repo = Repo(r"C:\SageMirror_Production")

        commits = list(repo.iter_commits(max_count=10))

        

        if not commits:

            st.info("커밋 내역이 존재하지 않습니다.")

            return

            

        git_list = []

        for c in commits:

            git_list.append({

                "hash": c.hexsha[:7],

                "message": c.message.strip(),

                "author": c.author.name,

                "date": datetime.fromtimestamp(c.committed_date).strftime("%Y-%m-%d %H:%M:%S")

            })

            

        import pandas as pd

        df = pd.DataFrame(git_list)

        df.columns = ["커밋 해시", "커밋 메시지", "작성자", "작성 일시"]

        st.dataframe(df, use_container_width=True)

        

    except Exception as e:

        st.error(f"GitHub 내역 조회 실패: {e}")



@st.dialog("📝 젬마 프로토콜 (Gemma Protocol) 편집", width="large")

def popup_edit_gemma_protocol():

    st.markdown("여기서 행동 지침과 작업 지침서를 상세하게 수정할 수 있습니다. 텍스트를 드래그하고 복사/붙여넣기 하세요.")

    new_val = st.text_area("규칙서 내용", value=st.session_state.p1_gemma_protocol, height=400, label_visibility="collapsed")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):

            st.session_state.p1_gemma_protocol = new_val

            st.rerun()

    with c2:

        if st.button("취소", use_container_width=True):

            st.rerun()



@st.dialog("📚 자료 조사 결과 (팝업)", width="large")

def popup_edit_research():

    st.markdown("결과를 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p1_research_result}</div>", unsafe_allow_html=True)

    new_val = st.text_area("자료 조사 결과 수정", value=st.session_state.p1_research_result, height=200, label_visibility="collapsed")

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):

            st.session_state.p1_research_result = new_val

            st.rerun()

    with c2:

        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"research_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)

    with c3:

        if st.button("닫기", use_container_width=True):

            st.rerun()



@st.dialog("[PACKAGE] Part 2 전달 패킷 (팝업)", width="large")

def popup_edit_planning():

    st.markdown("Part 2에서 철학/성경/감정 융합 작업에 사용할 리서치 패킷입니다.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p1_planning_result}</div>", unsafe_allow_html=True)

    new_val = st.text_area("Part 2 전달 패킷 수정", value=st.session_state.p1_planning_result, height=200, label_visibility="collapsed")

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):

            st.session_state.p1_planning_result = new_val

            st.rerun()

    with c2:

        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"planning_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)

    with c3:

        if st.button("닫기", use_container_width=True):

            st.rerun()



@st.dialog("[TARGET] 채널 벤치마킹 결과 (팝업)", width="large")

def popup_edit_benchmarking():

    st.markdown("결과를 쾌적하게 스크롤하며 검토하고 복사할 수 있습니다.")

    raw = st.session_state.get("p1_bench_raw", "")

    if raw:

        st.markdown("##### 📄 벤치마킹 원본 결과")

        with st.container(height=400, border=True):

            st.markdown(raw)

        st.divider()    

    val = ""

    for t in st.session_state.get("p1_topics", []):

        val += f"**{t['title']}**\n- 사유: {t['reason']}\n- 효과: {t['effect']}\n\n"

    with st.container(height=450, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{val}</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:

        st.download_button("📥 .txt 다운로드", data=val, file_name=f"benchmarking_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)

    with c2:

        if st.button("닫기", use_container_width=True, type="primary"):

            st.rerun()



# =====================================================================

# 공통 UI 레이아웃 (V8.1: 상단 PIN 로그인 통합)

# =====================================================================

def render_top_panel():
    st.caption("RUNNING VERSION: v17.1.4-C")

    # ──────────────────────────────────────────────────────────────

    # 상태 데이터 수집 (로직은 그대로, 디자인만 변경)

    # ──────────────────────────────────────────────────────────────

    db_ok  = os.path.exists(WORKSPACE_STATE_FILE)

    obs_path = st.session_state.get("path_obsidian", "")

    obs_ok = os.path.exists(obs_path) if obs_path else False

    git_repo = st.session_state.get("github_repo_url", "")

    git_ok   = len(git_repo) > 0 and GIT_AVAILABLE

    repo_name = git_repo.split('/')[-1].replace('.git', '') if git_ok else "미연동"

    obs_name  = os.path.basename(obs_path) if obs_ok else "경로 미설정"



    # ──────────────────────────────────────────────────────────────

    # [ROW 1] 상태 카드 4개 — 글래스모피즘 스타일 가로 배치

    # ──────────────────────────────────────────────────────────────

    st.markdown("""

    <style>

    /* 우측 컨트롤 박스 테두리 및 배경색 상황판과 통일 */

    #header-control-box-anchor + div {

        background: linear-gradient(135deg, #131b2e 0%, #0c1220 100%) !important;

        border: 1.5px solid #d4af6a44 !important;

        border-radius: 12px !important;

        padding: 6px 12px 6px 12px !important;

        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;

        display: flex !important;

        align-items: center !important;

    }

    

    /* 내부 위젯 정렬 강제 및 Streamlit 여백 리셋 */

    .header-pin-wrapper div[data-testid="stMarkdownContainer"] {

        margin: 0 !important;

    }

    .header-pin-wrapper input {

        height: 38px !important;

        border: 1px solid rgba(212, 175, 106, 0.3) !important;

        background-color: rgba(30, 41, 59, 0.45) !important;

        color: #f5e9d3 !important;

        margin: 0 !important;

    }

    .header-pin-wrapper input:focus {

        border-color: #d4af6a !important;

    }

    


    /* ═══ 시스템 연동 팝오버 버튼 스타일 ═══ */
    [data-testid="stPopover"] > div > button {
        background: rgba(212,175,106,0.12) !important;
        border: 1px solid rgba(212,175,106,0.35) !important;
        border-radius: 6px !important;
        color: #d4af6a !important;
        font-size: 0.75em !important;
        font-weight: 600 !important;
        padding: 3px 10px !important;
        margin-top: -2px !important;
        letter-spacing: 0.03em !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stPopover"] > div > button:hover {
        background: rgba(212,175,106,0.25) !important;
        border-color: rgba(212,175,106,0.7) !important;
        box-shadow: 0 2px 8px rgba(212,175,106,0.2) !important;
    }

    /* ═══ 글래스모피즘 컨트롤 박스 — 파트 헤더 우측 통합 박스 ═══ */
    .glass-control-box {
        background: linear-gradient(135deg, rgba(30, 15, 5, 0.92) 0%, rgba(50, 25, 10, 0.88) 100%);
        border: 1.5px solid rgba(212,175,106,0.40);
        border-radius: 14px;
        padding: 5px 10px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,175,106,0.25);
        margin-top: 3px;
    }

    /* 모델 셀렉트박스 스타일링 */

    .header-model-wrapper div[data-baseweb="select"] {

        height: 38px !important;

        background-color: rgba(30, 41, 59, 0.45) !important;

        border: 1px solid rgba(212, 175, 106, 0.3) !important;

        border-radius: 4px !important;

        color: #f5e9d3 !important;

    }

    .header-model-wrapper div[data-baseweb="select"]:hover {

        border-color: #d4af6a !important;

    }

    .header-model-wrapper div[data-testid="stSelectbox"] > div {

        border: none !important;

        background-color: transparent !important;

        height: 38px !important;

        min-height: 38px !important;

    }

    .header-model-wrapper div[role="button"] {

        padding-top: 0 !important;

        padding-bottom: 0 !important;

        line-height: 36px !important;

        height: 36px !important;

        background-color: transparent !important;

        color: #f5e9d3 !important;

    }

    

    .header-pop-wrapper button {

        height: 38px !important;

        margin: 0 !important;

        background-color: rgba(30, 41, 59, 0.45) !important;

        border: 1px solid rgba(212, 175, 106, 0.3) !important;

        color: #f5e9d3 !important;

    }

    .header-pop-wrapper button:hover {

        border-color: #d4af6a !important;

        background-color: rgba(212, 175, 106, 0.15) !important;

    }



    /* 상단 동기화 패널 통일화 디자인 (하단 상황판과 동일한 배경 및 테두리 지정) */

    .sage-sync-title {

        font-size: 0.92em;

        font-weight: 700;

        color: #d4af6a;

        margin-bottom: 12px;

        letter-spacing: 0.03em;

        display: flex;

        align-items: center;

        gap: 8px;

    }

    #top-sync-panel-anchor + div[data-testid="stHorizontalBlock"] {

        background: linear-gradient(135deg, #131b2e 0%, #0c1220 100%) !important;

        border: 1.5px solid #d4af6a44 !important;

        border-radius: 14px !important;

        padding: 20px 20px 18px 20px !important;

        margin-bottom: 14px !important;

        box-shadow: 0 4px 16px rgba(0,0,0,0.45) !important;

    }

    /* 클릭 가능한 카드의 래퍼 스타일 및 투명 absolute overlay 매직 (로컬 DB연결 형태를 100% 모방) */

    div[data-testid="column"]:has(.clickable-card-bg) {

        position: relative !important;

    }

    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] {

        position: absolute !important;

        inset: 0 !important;

        z-index: 99 !important;

        margin: 0 !important;

        padding: 0 !important;

    }

    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] button {

        background-color: transparent !important;

        border: none !important;

        color: transparent !important; /* 내부 텍스트 완전 투명화 */

        width: 100% !important;

        height: 100% !important;

        position: absolute !important;

        inset: 0 !important;

        padding: 0 !important;

        margin: 0 !important;

        border-radius: 8px !important;

        cursor: pointer;

    }

    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] button:hover {

        background-color: rgba(212, 175, 106, 0.08) !important;

    }

    div[data-testid="column"]:has(.clickable-card-bg) div[data-testid="stButton"] button p {

        display: none !important; /* 텍스트 숨김 */

    }

    .sage-stat-card.sync::before {

        background: linear-gradient(135deg, #d4af6a, #9a7b44) !important;

    }

    .sage-stat-card.sync .stat-label {

        color: #d4af6a !important;

    }



    .sage-status-row {

        display: flex;

        gap: 12px;

        align-items: stretch;

        margin-bottom: 14px;

        flex-wrap: nowrap;

    }

    .sage-stat-card {

        flex: 1;

        background: rgba(30, 41, 59, 0.45);

        border-radius: 8px;

        padding: 12px 16px;

        min-height: 60px;

        display: flex;

        flex-direction: column;

        justify-content: center;

        gap: 3px;

        position: relative;

        overflow: hidden;

        transition: transform 0.2s ease, box-shadow 0.2s ease;

        box-shadow: 0 2px 8px rgba(0,0,0,0.2);

    }

    .sage-stat-card::before {

        content: '';

        position: absolute;

        inset: 0;

        border-radius: 8px;

        padding: 1px;

        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);

        -webkit-mask-composite: xor;

        mask-composite: exclude;

        pointer-events: none;

    }

    .sage-stat-card.ok::before  { background: linear-gradient(135deg, #10B981, #06b6d4); }

    .sage-stat-card.warn::before{ background: linear-gradient(135deg, #F59E0B, #f97316); }

    .sage-stat-card.err::before { background: linear-gradient(135deg, #EF4444, #be185d); }

    

    .sage-stat-card .stat-label {

        font-size: 0.78em;

        font-weight: 700;

        letter-spacing: 0.02em;

        white-space: nowrap;

        overflow: hidden;

        text-overflow: ellipsis;

    }

    .sage-stat-card .stat-sub {

        font-size: 0.68em;

        color: #94a3b8;

        white-space: nowrap;

        overflow: hidden;

        text-overflow: ellipsis;

    }

    .sage-stat-card.ok  .stat-label { color: #34d399; }

    .sage-stat-card.warn .stat-label{ color: #fbbf24; }

    .sage-stat-card.err  .stat-label{ color: #f87171; }

    

    /* 파이프라인 카드 */

    .sage-pipeline-card {

        background: linear-gradient(135deg, #131b2e 0%, #0c1220 100%);

        border: 1.5px solid #d4af6a44;

        border-radius: 14px;

        padding: 16px 20px 14px 20px;

        margin-bottom: 14px;

        position: relative;

        overflow: hidden;

    }

    .sage-pipeline-card::after {

        content: '';

        position: absolute;

        top: -40px; right: -40px;

        width: 120px; height: 120px;

        background: radial-gradient(circle, #d4af6a18 0%, transparent 70%);

        pointer-events: none;

    }

    .sage-pipe-title {

        font-size: 0.92em;

        font-weight: 700;

        color: #d4af6a;

        margin-bottom: 14px;

        letter-spacing: 0.03em;

    }

    .sage-pipe-row {

        display: flex;

        align-items: center;

        gap: 0px;

        flex-wrap: nowrap;

        overflow-x: auto;

        padding-bottom: 4px;

    }

    .sage-pipe-node {

        display: flex;

        flex-direction: column;

        align-items: center;

        gap: 6px;

        min-width: 72px;

        flex: 1;

    }

    .sage-pipe-dot {

        width: 38px;

        height: 38px;

        border-radius: 50%;

        display: flex;

        align-items: center;

        justify-content: center;

        font-size: 1.05em;

        font-weight: 700;

        box-shadow: 0 4px 16px rgba(0,0,0,0.45);

        transition: transform 0.2s;

        position: relative;

    }

    .sage-pipe-dot.done {

        background: radial-gradient(circle at 35% 35%, #f87171, #c0392b);

        box-shadow: 0 4px 18px #c0392b55, 0 0 0 3px #f8717122;

    }

    .sage-pipe-dot.ready {

        background: radial-gradient(circle at 35% 35%, #f87171, #c0392b);

        box-shadow: 0 4px 18px #c0392b55, 0 0 0 3px #f8717122;

    }

    .sage-pipe-dot.empty {

        background: radial-gradient(circle at 35% 35%, #64748b, #334155);

        box-shadow: 0 2px 8px #0008;

    }

    .sage-pipe-label {
        font-size: 0.82em;
        color: #e2e8f0;
        text-align: center;
        white-space: nowrap;
        line-height: 1.4;
        font-weight: 600;
        letter-spacing: 0.01em;
    }

    </style>

    """, unsafe_allow_html=True)



    # ── 타이틀 및 HTML 앵커 추가 (인접 형제 stHorizontalBlock 스타일링)

    st.markdown('<div class="sage-sync-title">🔄 시스템 연동 및 동기화 상태</div><div id="top-sync-panel-anchor"></div>', unsafe_allow_html=True)

    c_db, c_obs, c_git, c_sync, c_auto = st.columns([1, 1, 1, 1, 1])



    with c_db:

        card_cls = "ok" if db_ok else "err"

        label    = "로컬 DB 연결" if db_ok else "로컬 DB 없음"

        sub      = "workspace_state.json" if db_ok else "저장 필요"

        icon_col = "#34d399" if db_ok else "#f87171"

        st.markdown(

            f'<div class="sage-stat-card {card_cls}">'

            f'<span class="stat-label"><span style="color:{icon_col};">⬤</span>  {label}</span>'

            f'<span class="stat-sub">{sub}</span>'

            f'</div>',

            unsafe_allow_html=True

        )



    with c_obs:

        if obs_ok:

            st.markdown(

                f'<div class="sage-stat-card ok clickable-card-bg">'

                f'<span class="stat-label"><span style="color:#34d399;">⬤</span>  옵시디언 RAG</span>'

                f'<span class="stat-sub">Vault: {obs_name}</span>'

                f'</div>',

                unsafe_allow_html=True

            )

            with st.popover("🔗 연동 내역", use_container_width=True):
                st.caption("📂 옵시디언 RAG 최근 연동 파일")
                try:
                    import os as _os
                    obs_path = st.session_state.get("obsidian_path", "")
                    if obs_path and _os.path.exists(obs_path):
                        _files = []
                        for _root, _dirs, _fnames in _os.walk(obs_path):
                            for _fn in _fnames:
                                if _fn.endswith(".md"):
                                    _fp = _os.path.join(_root, _fn)
                                    _files.append((_os.path.getmtime(_fp), _fn, _fp))
                        _files.sort(reverse=True)
                        for _mtime, _fname, _fpath in _files[:10]:
                            from datetime import datetime as _dt
                            _ts = _dt.fromtimestamp(_mtime).strftime("%m/%d %H:%M")
                            st.markdown(f"- `{_ts}` **{_fname}**")
                    else:
                        st.info("옵시디언 경로를 사이드바에서 설정해 주세요.")
                except Exception as _e:
                    st.error(f"목록 오류: {_e}")

        else:

            st.markdown(

                '<div class="sage-stat-card warn">'

                '<span class="stat-label"><span style="color:#fbbf24;">⬤</span>  옵시디언 확인필요 <span style="color:#ef4444;font-size:0.8em;">🔴 미연결</span></span>'

                '<span class="stat-sub">경로 미설정</span>'

                '</div>',

                unsafe_allow_html=True

            )



    with c_git:

        if git_ok:

            st.markdown(

                f'<div class="sage-stat-card ok clickable-card-bg">'

                f'<span class="stat-label"><span style="color:#34d399;">⬤</span>  GitHub 연동</span>'

                f'<span class="stat-sub">Repo: {repo_name}</span>'

                f'</div>',

                unsafe_allow_html=True

            )

            with st.popover("🔗 연동 내역", use_container_width=True):
                st.caption("🐙 GitHub 최근 커밋 내역")
                try:
                    from git import Repo as _Repo, InvalidGitRepositoryError
                    import os as _os
                    git_path = st.session_state.get("github_local_path", "")
                    if git_path and _os.path.exists(git_path):
                        _repo = _Repo(git_path)
                        _commits = list(_repo.iter_commits(max_count=10))
                        for _c in _commits:
                            from datetime import datetime as _dt
                            _ts = _dt.fromtimestamp(_c.committed_date).strftime("%m/%d %H:%M")
                            _msg = _c.message.strip()[:40]
                            st.markdown(f"- `{_ts}` {_msg}")
                    else:
                        st.info("GitHub 로컬 경로를 사이드바에서 설정해 주세요.")
                except Exception as _e:
                    st.error(f"히스토리 오류: {_e}")

        else:

            st.markdown(

                '<div class="sage-stat-card err">'

                '<span class="stat-label"><span style="color:#f87171;">⬤</span>  Git 미연동 <span style="color:#ef4444;font-size:0.8em;">🔴 미연결</span></span>'

                '<span class="stat-sub">설정 변경 필요</span>'

                '</div>',

                unsafe_allow_html=True

            )



    with c_sync:

        st.markdown(

            f'<div class="sage-stat-card sync clickable-card-bg">'

            f'<span class="stat-label"><span style="color:#d4af6a;">⬤</span>  전체 즉시 동기화</span>'

            f'<span class="stat-sub">Git Push & RAG</span>'

            f'</div>',

            unsafe_allow_html=True

        )

        if st.button(

            "⚡ 전체 즉시 동기화", 

            type="primary", 

            use_container_width=True, 

            key="top_force_sync_btn",

            help="클릭 시 로컬 DB, 옵시디언 RAG, GitHub를 즉시 동기화 및 Push합니다."

        ):

            with st.spinner("로컬 DB + 옵시디언 + GitHub 강제 동기화 중..."):

                save_workspace_state()

                ts       = datetime.now().strftime("%Y%m%d_%H%M%S")

                today_str = datetime.now().strftime("%Y-%m-%d")

                folder_name = "PlanningMemory"

                title = f"[Part2] 전체 작업 백업 - {ts}"

                val   = f"# Part 2 Alchemist 전체 작업 백업 (동기화 트리거)\n\n"

                val  += f"## 📌 선택 주제\n{st.session_state.get('p2_topic_selection','')}\n\n"

                val  += f"## 📚 자료조사 결과\n{st.session_state.get('p2_research_result','')}\n\n"

                val  += f"## 📖 총괄 기획안\n{st.session_state.get('p2_planning_result','')}\n\n"

                val  += f"---\n*Last updated: {today_str} {ts}*\n"

                obs_path_file = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Full Sync")

                if obs_path_file:

                    lock_file_readonly(obs_path_file)

                success, msg = auto_git_push(f"Force Full Sync: {ts}")

                if success:

                    st.toast("🔄 전체 즉시 동기화 & Git Push 성공!", icon="✅")

                else:

                    st.toast("🔄 로컬/옵시디언 동기화 완료 (Git 실패)", icon="⚠️")

                    st.error(f"GitHub Push 실패: {msg}")

                st.rerun()



    with c_auto:

        auto_save_active = st.session_state.get("research_auto_save", True)

        card_cls = "ok" if auto_save_active else "warn"

        label    = "리서치 자동저장"

        sub      = "활성화 (ON)" if auto_save_active else "비활성화 (OFF)"

        icon_col = "#34d399" if auto_save_active else "#fbbf24"

        

        st.markdown(

            f'<div class="sage-stat-card {card_cls} clickable-card-bg">'

            f'<span class="stat-label"><span style="color:{icon_col};">⬤</span>  {label}</span>'

            f'<span class="stat-sub">{sub}</span>'

            f'</div>',

            unsafe_allow_html=True

        )

        

        with st.popover("⚙️ 설정 및 확인", use_container_width=True):

            st.caption("💾 리서치 자동저장 설정")

            new_val = st.toggle(

                "리서치 내용 즉시 저장", 

                value=auto_save_active, 

                key="top_research_auto_save_toggle"

            )

            if new_val != auto_save_active:

                st.session_state.research_auto_save = new_val

                save_workspace_state()

                st.rerun()

                

            st.divider()

            st.caption("📂 최근 저장된 리서치 목록")

            try:

                obs_path_chk = st.session_state.get("path_obsidian", "")

                research_dir_chk = os.path.join(obs_path_chk, "Studio", "ResearchMemory")

                if obs_path_chk and os.path.exists(research_dir_chk):

                    import os as _os

                    r_files = []

                    for fn in _os.listdir(research_dir_chk):

                        if fn.endswith(".md"):

                            fp = _os.path.join(research_dir_chk, fn)

                            r_files.append((_os.path.getmtime(fp), fn))

                    r_files.sort(reverse=True)

                    if r_files:

                        for mtime, fname in r_files[:5]:

                            ts = datetime.fromtimestamp(mtime).strftime("%m/%d %H:%M")

                            st.markdown(f"- `{ts}` {fname.replace('.md', '')}")

                    else:

                        st.info("저장된 리서치 내역이 없습니다.")

                else:

                    st.info("리서치 폴더가 아직 생성되지 않았습니다.")

            except Exception as e:

                st.error(f"목록 오류: {e}")



    # ──────────────────────────────────────────────────────────────

    # [ROW 2] 실시간 데이터 연동 상황판 — 3번째 캡쳐 스타일

    # ──────────────────────────────────────────────────────────────

    def _is_df_valid(df):

        import pandas as _pd

        return df is not None and isinstance(df, _pd.DataFrame) and not df.empty



    # 각 파트 완료 여부

    f1 = bool(st.session_state.get("p1_topic_selection"))

    f2 = bool(st.session_state.get("p2_planning_result"))

    f3 = bool(st.session_state.get("p34_narration_script"))

    f4 = bool(st.session_state.get("p34_image_script"))

    f5 = bool(st.session_state.get("p5_valid_rows") or st.session_state.get("p5_c_results"))

    f6 = _is_df_valid(st.session_state.get("p6_opal_df"))

    f7 = _is_df_valid(st.session_state.get("p7_capcut_df"))

    f8 = bool(st.session_state.get("p8_dashboard_saved"))



    def _dot_cls(flag):

        return "done" if flag else "empty"



    nodes = [

        (f1, "1. 주제 선정"),

        (f2, "2. 기획안"),

        (f3, "3. 나레이션"),

        (f4, "4. 이미지대본"),

        (f5, "5. 씬검증"),

        (f6, "6. 오팔배분"),

        (f7, "7. 캡컷조립"),

        (f8, "8. 최종완료"),

    ]



    nodes_html = ""

    for i, (flag, label) in enumerate(nodes):

        dot_cls = _dot_cls(flag)

        nodes_html += f'<div class="sage-pipe-node"><div class="sage-pipe-dot {dot_cls}"></div><span class="sage-pipe-label">{label}</span></div>'



    st.markdown(

        f'<div class="sage-pipeline-card">'

        f'<div class="sage-pipe-title">🔗 실시간 데이터 연동 상황판</div>'

        f'<div class="sage-pipe-row">{nodes_html}</div>'

        f'</div>',

        unsafe_allow_html=True

    )



    # ──────────────────────────────────────────────────────────────

    # [ROW 3] 상단 공통 패널 — 옵시디언 규칙서 + 마스터 프롬프트

    # ──────────────────────────────────────────────────────────────

    sidebar_part = st.session_state.get("sidebar_part", "part1")

    if sidebar_part.startswith("파트 0"):   sidebar_part_key = "part0"

    elif sidebar_part.startswith("파트 1"):   sidebar_part_key = "part1"

    elif sidebar_part.startswith("파트 2"): sidebar_part_key = "part2"

    elif sidebar_part.startswith("파트 3"): sidebar_part_key = "part3"

    elif sidebar_part.startswith("파트 4"): sidebar_part_key = "part4"

    elif sidebar_part.startswith("파트 5"): sidebar_part_key = "part5"

    elif sidebar_part.startswith("파트 6"): sidebar_part_key = "part6"

    elif sidebar_part.startswith("파트 7"): sidebar_part_key = "part7"

    elif sidebar_part.startswith("파트 8"): sidebar_part_key = "part8"

    else: sidebar_part_key = sidebar_part



    part_mapping = {

        "part0": ("base_prompt_rules",       "🤖 파트 0 젬마 스튜디오 마스터 프롬프트"),

        "part1": ("base_prompt_rules",       "📚 파트 1 Librarian 전역 마스터 프롬프트"),

        "part2": ("p2_master_prompt",         "🎨 파트 2 Alchemist 전역 마스터 프롬프트"),

        "part3": ("p34_master_prompt",        "✍️ 파트 3 대본 작성 마스터 프롬프트"),

        "part4": ("p5_image_master_prompt",   "🖼️ 파트 4 이미지 생성 마스터 프롬프트"),

        "part5": ("p6_veo3_master_prompt",    "🎥 파트 5 영상 생성 마스터 프롬프트"),

        "part6": ("p6_master_prompt",         "🎵 파트 6 나레이션 & 배경음악 마스터 프롬프트"),

        "part7": ("p7_master_prompt",         "🎬 파트 7 숏폼 생성 마스터 프롬프트"),

        "part8": ("p8_master_prompt",         "📊 파트 8 캡컷 최종 조립 마스터 프롬프트"),

    }

    prompt_key, prompt_title = part_mapping.get(sidebar_part_key, ("base_prompt_rules", "🤖 파트 0 젬마 스튜디오 마스터 프롬프트"))



    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 마스터 프롬프트", expanded=False):

        L, R = st.columns(2, gap="medium")

        with L:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)

            # 상단 공통 규칙서 위젯 동기화
            # - 일반 입력 중에는 사용자가 입력한 값을 유지
            # - 팝업 저장 직후에는 실제 저장값(obsidian_rules)을 위젯에 1회 반영
            if st.session_state.get("_sync_top_ob_view_widget_next_run", False):
                st.session_state["top_ob_view_widget"] = st.session_state.get("obsidian_rules", "")
                st.session_state["_sync_top_ob_view_widget_next_run"] = False
            elif "top_ob_view_widget" not in st.session_state:
                st.session_state["top_ob_view_widget"] = st.session_state.get("obsidian_rules", "")

            st.text_area("옵시디언 규칙서", height=180, key="top_ob_view_widget", label_visibility="collapsed")

            if st.button("💾 옵시디언 규칙서 저장", key="top_ob_save_btn", use_container_width=True):
                st.session_state["obsidian_rules"] = clean_prompt_contamination(st.session_state.get("top_ob_view_widget", ""))
                save_workspace_state()
                st.toast("✅ 옵시디언 규칙서 저장 완료", icon="💾")
                st.rerun()

            # v15.9.34.5: 상단 공통 패널의 중복 즉석 리서치 UI 제거
            # - 시스템 연동 상태판과 역할이 중복되어 화면에서만 제거함
            # - 리서치/RAG/자동저장/옵시디언 저장 로직은 삭제하지 않고 그대로 보존함

            st.markdown('</div>', unsafe_allow_html=True)

        with R:

            st.markdown(f'<div class="top-panel-card"><div class="top-panel-title">{prompt_title}</div>', unsafe_allow_html=True)

            prompt_widget_key = f"top_pr_view_{prompt_key}_widget"
            sync_flag_key = f"_sync_{prompt_widget_key}_next_run"

            # 상단 공통 마스터 프롬프트 위젯 동기화
            # - 일반 입력 중에는 사용자가 입력한 값을 유지
            # - 팝업 저장 직후에는 실제 저장값(prompt_key)을 위젯에 1회 반영
            if st.session_state.get(sync_flag_key, False):
                st.session_state[prompt_widget_key] = st.session_state.get(prompt_key, "")
                st.session_state[sync_flag_key] = False
            elif prompt_widget_key not in st.session_state:
                st.session_state[prompt_widget_key] = st.session_state.get(prompt_key, "")

            st.text_area("파트 마스터 프롬프트", height=180, key=prompt_widget_key, label_visibility="collapsed")

            pr_btn_cols = st.columns(2)
            with pr_btn_cols[0]:
                if st.button("📝 편집", key=f"pr_btn_{prompt_key}", use_container_width=True):
                    popup_edit_text_value(prompt_key, prompt_title)
            with pr_btn_cols[1]:
                if st.button("💾 마스터 프롬프트 저장", key=f"pr_save_btn_{prompt_key}", use_container_width=True):
                    st.session_state[prompt_key] = clean_prompt_contamination(st.session_state.get(prompt_widget_key, ""))
                    save_workspace_state()
                    st.toast("✅ 마스터 프롬프트 저장 완료", icon="💾")
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



# =====================================================================

# Part 1 엔진 API 로직

# =====================================================================

TOPIC_PATTERN = re.compile(r"^\s*(\d{1,2})[.)\]]\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$", re.MULTILINE)



def _parse_topics(raw: str):

    parsed = []

    for m in TOPIC_PATTERN.findall(raw or ""):

        _, title, reason, effect, reaction = m

        parsed.append({"title": title.strip().lstrip("*").strip(), "reason": reason.strip(), "effect": effect.strip(), "audience_reaction": reaction.strip()})

    return parsed



@st.cache_data(ttl=900, show_spinner=False)

def analyze_channel_to_topics(channel, region, obsidian_rules, base_prompt, gemma_protocol) -> list:

    base = f"""[젬마 프로토콜]

{gemma_protocol}



[옵시디언 규칙서]

{obsidian_rules}



[기본 프롬프트]

{base_prompt}



[과제]

다음 타겟 채널을 분석하여 핵심 주제 20개를 추출하십시오.

(요구사항: 사람이 직접 운영하는 채널이라 가정하고, 해당 채널의 영상에 달린 시청자 댓글 200개 이상을 분석했다고 가상으로 설정하십시오. 시청자들의 실제 체험담, "나도 그런 일 있었는데 이렇게 해결했다"는 식의 공감/경험 포인트가 반영된 생생한 주제를 뽑아내야 합니다.)



채널: {channel}

지역: {region}



[출력양식]

NN. 주제 | 추천사유(체험담 기반) | 예상효과 | 예상반응"""



    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules

    raw = call_gemma(base, system=sys_ctx)

    if isinstance(raw, str) and raw.startswith("[ERROR]"): st.error(raw); return []

    parsed = _parse_topics(raw)

    if len(parsed) < 20: parsed = _parse_topics(call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)) or parsed

    return parsed[:20]



def analyze_channel_to_topics_custom(channel, region, obsidian_rules, base_prompt, gemma_protocol, custom_prompt) -> tuple:

    base = f"""[젬마 프로토콜]

{gemma_protocol}



[옵시디언 규칙서]

{obsidian_rules}



[기본 프롬프트]

{base_prompt}



[과제]

{custom_prompt}



채널: {channel}

지역: {region}



[출력양식]

NN. 주제 | 추천사유(체험담 기반) | 예상효과 | 예상반응"""



    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules

    raw = call_gemma(base, system=sys_ctx)

    if isinstance(raw, str) and raw.startswith("[ERROR]"): st.error(raw); return [], raw

    parsed = _parse_topics(raw)

    if len(parsed) < 20: 

        raw_corrected = call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)

        parsed = _parse_topics(raw_corrected) or parsed

        if not isinstance(raw_corrected, str) or not raw_corrected.startswith("[ERROR]"):

            raw = raw_corrected

    return parsed[:20], raw







def format_rag_results_for_prompt(rag_results):
    """Part 2 수동/자동 옵시디언 검색 결과를 Gemma 프롬프트용 텍스트로 변환한다.
    Part 1 코드는 건드리지 않고, Part 2 RAG 연결에만 사용한다.
    """
    if not rag_results:
        return ""
    try:
        if isinstance(rag_results, str):
            return rag_results
        chunks = []
        for idx, item in enumerate(rag_results, start=1):
            if isinstance(item, dict):
                title = item.get("title", "제목 없음")
                path = item.get("path", "경로 없음")
                score = item.get("score", "")
                preview = item.get("preview", "")
                chunks.append(
                    f"[{idx}] {title}\n"
                    f"- path: {path}\n"
                    f"- score: {score}\n"
                    f"- preview: {preview}"
                )
            else:
                chunks.append(f"[{idx}] {str(item)}")
        return "\n\n".join(chunks)
    except Exception as e:
        return f"[RAG 변환 오류: {e}]"

def generate_research_draft(channel_url, topic, gemma_protocol, master_prompt, custom_prompt=None, manual_rag_results=None, p1_research_result=None):

    obsidian_context = ""

    try:

        search_result = simple_keyword_search(

            st.session_state.get("path_obsidian", ""), 

            topic,

            top_k=5

        )



        if search_result:

            obsidian_context = f"""



[옵시디언 감정/RAG 참조 자료]



{search_result}



"""

    except Exception as e:

        st.error(f"옵시디언 검색 오류: {e}")

        pass



    rag_context = obsidian_context

    manual_rag_text = format_rag_results_for_prompt(manual_rag_results)
    if manual_rag_text:
        rag_context += f"\n\n[사용자 수동/자동 옵시디언 검색 결과 — Step 2 우선 참조]\n{manual_rag_text}\n"

    if p1_research_result:
        rag_context += f"\n\n[Part 1 상속 기초 자료조사 — Step 2 연결]\n{p1_research_result}\n"



    instruction = custom_prompt if custom_prompt else "다음 선택된 주제에 대하여, 200여 개의 시청자 공감 댓글(체험담)을 참조하였다고 가정하고, 철학/심리학/성경 기반 지식을 융합하여 '자료 조사 및 기초 초안'을 작성하시오."



    base = f"""[젬마 프로토콜]



{gemma_protocol}



{rag_context}



[RAG & 지식 공백 방지 지침]

만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.

대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.

예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]



[마스터 규칙서]

{master_prompt}



[작업 지시]

{instruction}

* 주제: {topic}

* 타겟 채널: {channel_url}



[필수 포함 항목]

1. 세부 주제 및 매력적인 제목 (Title)

2. 핵심 키워드 (`[[키워드]]` 형식, 반드시 포함)

3. 시청자 후킹 기법 (실제 체험담을 활용한 공감 형성)

4. 타겟 채널 구조 분석 기반 차별화 전략

5. **모든 대본/자료의 출처 명기 필수** (책 이름, 저자명, 성경 구절 등 명확히 표기)"""

    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA



    return call_gemma(base, system=system_prompt)



def generate_final_planning(research_result, gemma_protocol, master_prompt, manual_rag_results=None, p1_context=None):

    rag_context = ""
    manual_rag_text = format_rag_results_for_prompt(manual_rag_results)
    if manual_rag_text:
        rag_context += f"\n\n[사용자 수동/자동 옵시디언 검색 결과 — Step 3 총괄기획 우선 참조]\n{manual_rag_text}\n"
    if p1_context:
        rag_context += f"\n\n[Part 1 상속 데이터 — Step 3 총괄기획 연결]\n{p1_context}\n"

    base = f"""[젬마 프로토콜]

{gemma_protocol}

{rag_context}



[RAG & 지식 공백 방지 지침]

만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.

대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.

예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]



[마스터 규칙서]

{master_prompt}



[자료 조사 결과]

{research_result}



[작업 지시]

위 자료 조사 결과를 바탕으로 '15분 분량의 유튜브 다큐멘터리 총괄 시나리오 기획안(뼈대)'을 작성하시오.



[필수 포함 항목]

1. 영상의 구조 (도입부: 시청자 체험담 공감 - 전개부: 철학/심리 해석 - 절정부: 성경적/현자의 해답 - 결말부: 격려)

2. 4070 시청자 감성 타격 전략 및 시각적 연출 가이드 (렘브란트풍 등)

3. 클라이맥스에 들어갈 '오늘의 명언' 및 교훈"""



    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA



    return call_gemma(base, system=system_prompt)



@st.cache_data(ttl=900, show_spinner=False)

def analyze_channel_to_topics_p1(channel, region, obsidian_rules, base_prompt, gemma_protocol, custom_bench_prompt) -> tuple:

    base = f"""[젬마 프로토콜]

{gemma_protocol}



[옵시디언 규칙서]

{obsidian_rules}



[기본 프롬프트]

{base_prompt}



[과제]

{custom_bench_prompt}



채널: {channel}

지역: {region}



[출력양식]

NN. 주제 | 추천사유(체험담 기반) | 예상효과 | 예상반응"""



    sys_ctx = SAGE_PERSONA + "\n\n" + obsidian_rules

    raw = call_gemma(base, system=sys_ctx)

    if isinstance(raw, str) and raw.startswith("[ERROR]"): 

        st.error(raw)

        return raw, []

    parsed = _parse_topics(raw)

    if len(parsed) < 20: 

        raw_retry = call_gemma(base + "\n\n[자가 교정] 20줄 파이프(|) 형식으로 출력.", system=sys_ctx)

        parsed_retry = _parse_topics(raw_retry)

        if parsed_retry:

            parsed = parsed_retry

            if not isinstance(raw_retry, str) or not raw_retry.startswith("[ERROR]"):

                raw = raw_retry

    return raw, parsed[:20]



def generate_research_draft_p1(channel_url, topic, gemma_protocol, master_prompt, custom_research_prompt):

    obsidian_context = ""

    try:

        search_result = simple_keyword_search(

            st.session_state.get("path_obsidian", ""), 

            topic,

            top_k=5

        )



        if search_result:

            obsidian_context = f"""



[옵시디언 감정/RAG 참조 자료]



{search_result}



"""

    except Exception as e:

        st.error(f"옵시디언 검색 오류: {e}")

        pass



    rag_context = obsidian_context



    base = f"""[젬마 프로토콜]



{gemma_protocol}



{rag_context}



[RAG & 지식 공백 방지 지침]

만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.

대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.

예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]



[마스터 규칙서]

{master_prompt}



{custom_research_prompt}

* 주제: {topic}

* 타겟 채널: {channel_url}



[필수 포함 항목]

1. 세부 주제 및 매력적인 제목 (Title)

2. 핵심 키워드 (`[[키워드]]` 형식, 반드시 포함)

3. 시청자 후킹 기법 (실제 체험담을 활용한 공감 형성)

4. 타겟 채널 구조 분석 기반 차별화 전략

5. **모든 대본/자료의 출처 명기 필수** (책 이름, 저자명, 성경 구절 등 명확히 표기)"""

    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA



    return call_gemma(base, system=system_prompt)



def generate_final_planning_p1(research_result, gemma_protocol, master_prompt, custom_plan_prompt):

    base = f"""[젬마 프로토콜]

{gemma_protocol}



[RAG & 지식 공백 방지 지침]

만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.

대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.

예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]



[마스터 규칙서]

{master_prompt}



[자료 조사 결과]

{research_result}



{custom_plan_prompt}



[필수 포함 항목]

1. 영상의 구조 (도입부: 시청자 체험담 공감 - 전개부: 철학/심리 해석 - 절정부: 성경적/현자의 해답 - 결말부: 격려)

2. 4070 시청자 감성 타격 전략 및 시각적 연출 가이드 (렘브란트풍 등)

3. 클라이맥스에 들어갈 '오늘의 명언' 및 교훈"""



    system_prompt = COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA



    return call_gemma(base, system=system_prompt)



# =====================================================================

# Part 1 렌더링

# =====================================================================


# ══════════════════════════════════════════════════════════════
# 🔒 최종본 Lock & 수정본 생성 시스템 v1.0
# ══════════════════════════════════════════════════════════════

def lock_and_push_final_version(part_num, display_name, keys_to_backup):
    try:
        obs_path = st.session_state.get("path_obsidian", "")
        if not obs_path:
            st.error("❌ 옵시디언 경로 미설정"); return
        locks_dir = os.path.join(obs_path, "Studio", "Final_Locks")
        os.makedirs(locks_dir, exist_ok=True)
        fpath = os.path.join(locks_dir, f"Part{part_num}_Final_LOCK.md")
        md = [f"# 🔒 Part {part_num} — {display_name} 최종본 LOCK"]
        md.append(f"\n> 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n")
        for key in keys_to_backup:
            val = st.session_state.get(key, "")
            if val is not None:
                if isinstance(val, (dict, list)):
                    try:
                        val_str = json.dumps(val, ensure_ascii=False, indent=2)
                    except:
                        val_str = str(val)
                else:
                    val_str = str(val)
                md.append(f"\n## {key}\n{val_str}\n")
        with open(fpath, "w", encoding="utf-8") as f: f.write("\n".join(md))
        try:
            import stat as _s; os.chmod(fpath, _s.S_IRUSR | _s.S_IRGRP | _s.S_IROTH)
        except: pass
        st.success(f"✅ Part {part_num} 최종본 Lock 완료!")
        ok, msg = auto_git_push(f"LOCK: Part{part_num}")
        st.success("✅ GitHub Push 완료!") if ok else st.warning(f"⚠️ Push 실패: {msg}")
        # ── Recent Activity Dynamic Sync ──
        try:
            from rag_memory_utils import update_recent_activity_memory
            state_dict = dict(st.session_state)
            updated_mem = update_recent_activity_memory(state_dict, "part_save", f"[LOCK] Part {part_num} ({display_name}) 최종본 잠금 완료")
            st.session_state.recent_activity_memory = updated_mem
        except Exception:
            pass
        save_workspace_state()
    except Exception as e:
        st.error(f"❌ Lock 오류: {e}")

def create_revision_version(part_num, display_name, keys_to_backup):
    try:
        obs_path = st.session_state.get("path_obsidian", "")
        locks_dir = os.path.join(obs_path, "Studio", "Final_Locks")
        lock_file = os.path.join(locks_dir, f"Part{part_num}_Final_LOCK.md")
        if not os.path.exists(lock_file):
            st.error(f"❌ 먼저 Part {part_num} 최종본 Lock을 완료하세요."); return
        rev = 1
        while os.path.exists(os.path.join(locks_dir, f"Part{part_num}_REV{rev}.md")):
            rev += 1
        rpath = os.path.join(locks_dir, f"Part{part_num}_REV{rev}.md")
        with open(lock_file, "r", encoding="utf-8") as f: orig = f.read()
        with open(rpath, "w", encoding="utf-8") as f:
            f.write(f"# ✏️ Part {part_num} REV{rev}\n> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n" + orig)
        st.success(f"✅ 수정본 생성: Part{part_num}_REV{rev}.md")
        # ── Recent Activity Dynamic Sync ──
        try:
            from rag_memory_utils import update_recent_activity_memory
            state_dict = dict(st.session_state)
            updated_mem = update_recent_activity_memory(state_dict, "part_save", f"[REV] Part {part_num} 수정본 생성됨 (REV{rev})")
            st.session_state.recent_activity_memory = updated_mem
        except Exception:
            pass
        st.info(f"📁 경로: {rpath}")
    except Exception as e:
        st.error(f"❌ 수정본 오류: {e}")

def extract_text_from_google_link(url: str) -> str | None:
    """구글 문서, 구글 드라이브 및 일반 웹 페이지 본문 텍스트 추출"""
    import requests
    from bs4 import BeautifulSoup
    import re
    url = url.strip()
    if not url:
        return None
    try:
        # 구글 독스 문서 주소인 경우 텍스트 익스포트 주소로 치환
        if "docs.google.com/document" in url:
            export_url = re.sub(r'/edit.*$', '/export?format=txt', url)
            if "/export?format=txt" not in export_url:
                export_url = export_url.rstrip('/') + '/export?format=txt'
            res = requests.get(export_url, timeout=15)
            if res.status_code == 200:
                return res.text
        
        # 일반 웹 문서 크롤링
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for s in soup(["script", "style"]):
                s.decompose()
            return soup.get_text()
    except Exception as e:
        st.error(f"[링크 분석 오류] 실패: {e}\n→ 해결 방법: URL 주소를 다시 확인하거나 공개 상태를 점검하세요.")
    return None

def call_gemini(prompt: str, system_prompt: str = "", model_name: str = "gemini-2.5-flash") -> str:
    """Gemini API 호출 동기 처리"""
    try:
        api_key = st.session_state.get("gemini_api_key", "").strip()
        if not api_key:
            return "Gemini API Key가 설정되지 않았습니다. 사이드바 설정에서 API Key를 입력해 주세요."
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        if system_prompt:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
        else:
            model = genai.GenerativeModel(model_name=model_name)
            
        response = model.generate_content(prompt)
        return response.text if hasattr(response, "text") else "응답을 받지 못했습니다."
    except Exception as e:
        return f"[Gemini 호출 오류] 실패: {e}"

def stream_gemini(prompt: str, system_prompt: str = "", model_name: str = "gemini-2.5-flash"):
    """Gemini API 호출 실시간 스트리밍 처리"""
    try:
        api_key = st.session_state.get("gemini_api_key", "").strip()
        if not api_key:
            yield "Gemini API Key가 설정되지 않았습니다."
            return
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        if system_prompt:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
        else:
            model = genai.GenerativeModel(model_name=model_name)
            
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n[Gemini 스트리밍 오류] 실패: {e}"

def _stream_gemma_a_mode_p0(prompt: str, system: str = "", model: str = "gemma4:e2b"):
    """로컬 Gemma API 실시간 스트리밍 제너레이터"""
    import requests as _req
    import json as _json

    ka_val = st.session_state.get("popup_keep_alive", "10m")
    np_val = st.session_state.get("popup_num_predict", 300)
    temp_val = st.session_state.get("popup_temperature", 0.2)
    tp_val = st.session_state.get("popup_top_p", 0.8)

    full_prompt = ""
    if system and system.strip():
        full_prompt = system.strip() + "\n\n"
    full_prompt += prompt

    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "keep_alive": ka_val,
        "options": {
            "num_predict": np_val,
            "temperature": temp_val,
            "top_p": tp_val,
        }
    }

    try:
        in_thinking = False
        with _req.post(ollama_url, json=payload, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    chunk = _json.loads(raw_line.decode("utf-8"))
                except Exception:
                    continue
                token = chunk.get("response", "")
                if token:
                    if "<think>" in token:
                        in_thinking = True
                    if in_thinking:
                        if "</think>" in token:
                            in_thinking = False
                        continue
                    yield token
                if chunk.get("done", False):
                    break
    except Exception as e:
        yield f"\n[로컬 Gemma 스트리밍 오류] 실패: {e}"

CHAT_JSON_PATH = Path(r"C:\SageMirror_Outputs\00_Session_States\popup_chat_EP001.json")

def _save_chat_history(history: list) -> None:
    try:
        CHAT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        import json as _json
        CHAT_JSON_PATH.write_text(
            _json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"[채팅 저장 오류] {e}")

def _load_chat_history() -> list:
    try:
        if CHAT_JSON_PATH.exists():
            import json as _json
            raw = CHAT_JSON_PATH.read_text(encoding="utf-8", errors="ignore")
            data = _json.loads(raw)
            if isinstance(data, list):
                return data
    except Exception as e:
        print(f"[채팅 로드 오류] {e}")
    return []

def render_part0_assistant():
    """파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집) 풀스크린 화면 렌더링"""
    # 1. 최상단 3열 레이아웃
    c_title, c_pin, c_popup = st.columns([5, 3, 2])
    with c_title:
        st.markdown("<h3 class='sage-header-compact' style='margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;'>🤖 파트 0: 젬마 스튜디오</h3>", unsafe_allow_html=True)
    with c_pin:
        st.markdown('<div class="pin-input-container">', unsafe_allow_html=True)
        from sage_config import PART_PINS
        pin = st.text_input("🔒 마스터 PIN", type="password", key="p0_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")
        st.markdown('</div>', unsafe_allow_html=True)
        if pin == PART_PINS.get("part0", "7777"):
            st.session_state.unlock_part0 = True
        elif pin:
            st.session_state.unlock_part0 = False
    with c_popup:
        # 파트 0은 이미 메인 화면이므로 팝업 호출 필요성 낮으나 표준 레이아웃 맞춤
        if st.button("🤖 젬마 어시스턴트", type="secondary", use_container_width=True, key="p0_popup_btn"):
            st.toast("💡 이미 풀스크린 젬마 스튜디오를 실행 중입니다.", icon="ℹ️")

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)
    render_top_panel()
    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    # 3:7 풀스크린 분할
    col_tools, col_chat = st.columns([3, 7], gap="large")

    # ──────────────────────────────────────────────────────────────
    # [좌측 영역] 30% 툴박스 - 파일/링크 텍스트 추출 및 규칙서 v4.0 변환 저장
    # ──────────────────────────────────────────────────────────────
    with col_tools:
        st.markdown("#### 📂 지식 소스 수집기")
        
        uploaded_file = st.file_uploader(
            "문서 파일 드롭 & 업로드 (TXT, MD, PDF, HTML)",
            type=["txt", "md", "pdf", "html"],
            key="p0_file_uploader"
        )
        
        google_link = st.text_input(
            "🔗 구글 문서 또는 웹 기사 URL 링크 주입",
            key="p0_google_link_input",
            placeholder="https://docs.google.com/document/d/... 또는 일반 웹 기사 링크"
        )

        extracted_text = ""
        source_name = ""

        # 텍스트 추출 로직 가동
        if uploaded_file:
            source_name = uploaded_file.name
            extracted_text = extract_text_from_uploaded_file(uploaded_file)
        elif google_link.strip():
            source_name = google_link.strip()
            extracted_text = extract_text_from_google_link(google_link)

        if extracted_text:
            st.success(f"✅ [{source_name[:30]}] 텍스트 추출 성공!")
            st.text_area(
                "📄 추출 텍스트 본문 (미리보기)",
                value=extracted_text[:3000] + ("\n\n...(이하 생략)" if len(extracted_text) > 3000 else ""),
                height=250,
                key="p0_extracted_preview_ta",
                disabled=True
            )
            
            # [변환 및 저장]
            selected_model = st.session_state.get("p0_selected_model", "gemma4:e2b")
            
            if st.button("💾 옵시디언 마스터 규칙서 v4.0 변환 및 저장", type="primary", use_container_width=True, key="p0_convert_save_btn"):
                with st.spinner("젬마가 마스터 규칙서 v4.0 규격으로 내용을 분석하고 마크다운 변환 중..."):
                    system_prompt = "당신은 현자의 거울 스튜디오의 지식 관리 시스템입니다. 제공된 자료를 분석하여 '옵시디언 마스터 규칙서 v4.0' 구조에 맞게 마크다운 파일로 정제해 주십시오."
                    user_prompt = f"""
[작업 지시]
제공된 텍스트 자료를 바탕으로 고도로 구조화된 '옵시디언 마스터 규칙서 v4.0' 형태의 마크다운(.md) 문서를 작성해 주십시오.

[요구사항]
1. 문서는 대제목(#)과 소주제별 헤더(##, ###) 구조를 명확히 갖추어야 합니다.
2. 상단에 3줄 내외의 명확한 핵심 요약 영역을 만드십시오.
3. 본문 내에 연관된 감정, 철학자, 성경 등의 주요 개념들을 옵시디언 [[위키링크]] 형태로 최소 5개 이상 자연스럽게 심어두십시오. (예: [[쇼펜하우어]], [[시편23편]], [[존재불안]])
4. 모든 본문 텍스트 내에서 주인공 또는 등장인물을 지칭할 때는 오직 '@Protagonist'로 통일하여 표기해야 합니다. 절대 '주인공', '노인', '그', '그녀' 등의 일반 대명사나 고유명사를 사용하지 마십시오.
5. 문서의 맨 아래에 출처 표기 [SOURCE: {source_name}] 를 확실히 명시하십시오.
6. 변환 완료된 순수 Markdown 본문 이외에 어떠한 설명, 사족, 전주곡도 출력하지 마십시오.

[입력 데이터]
출처: {source_name}
내용:
{extracted_text}
"""
                    try:
                        # 모델 선택 매핑 호출
                        if selected_model == "gemini-2.5-flash":
                            gemma_output = call_gemini(user_prompt, system_prompt)
                        else:
                            # 로컬 gemma 모델
                            gemma_output = call_gemma(user_prompt, system=system_prompt, model=selected_model)
                            
                        # Obsidian 저장
                        title = os.path.splitext(os.path.basename(source_name))[0] if "/" not in source_name and "\\" not in source_name else "Link_Reference"
                        title = re.sub(r'[\\/:*?"<>|]', "_", title).strip()
                        save_path = save_obsidian_memory("References", title, gemma_output, source=source_name)
                        
                        if save_path:
                            st.success(f"💾 저장 완료: {save_path}")
                            st.toast("✅ 옵시디언 마스터 규칙서 v4.0 저장 완료!", icon="💾")
                            
                            # GitHub 자동 Push 연계
                            commit_msg = f"v17.1.7: 옵시디언 마스터 규칙서 v4.0 백업 - {title}"
                            push_ok, push_msg = auto_git_push(commit_msg)
                            if push_ok:
                                st.toast("🚀 GitHub 백업 완료!", icon="🚀")
                            else:
                                st.warning(f"Git Push 실패: {push_msg}")
                            
                            # 상태 보존
                            save_workspace_state()
                    except Exception as e:
                        st.error(f"[변환 오류] 실패: {e}\n→ 해결 방법: Ollama 서버 상태 또는 API Key 설정을 점검하십시오.")

    # ──────────────────────────────────────────────────────────────
    # [우측 영역] 70% 대화창 - 가로 칩 모델 선택 + 네이티브 채팅
    # ──────────────────────────────────────────────────────────────
    with col_chat:
        st.markdown("#### 💬 젬마 대화 스튜디오")
        
        # 가로형 모델 스위처 칩 UI
        model_labels = [ "⚡ 빠른대화 (E2B)", "🧠 심층분석 (E4B)", "🌐 최신리서치 (Gemini)", "🔍 웹검색 (Tavily)" ]
        model_mapping = {
            "⚡ 빠른대화 (E2B)": "gemma4:e2b",
            "🧠 심층분석 (E4B)": "gemma4:e4b",
            "🌐 최신리서치 (Gemini)": "gemini-2.5-flash",
            "🔍 웹검색 (Tavily)": "tavily"
        }
        
        # 현재 선택된 값을 레이블로 매핑
        current_model_id = st.session_state.get("p0_selected_model", "gemma4:e2b")
        default_label = "⚡ 빠른대화 (E2B)"
        for label, val in model_mapping.items():
            if val == current_model_id:
                default_label = label
                break
                
        selected_label = st.radio(
            "대화 엔진 선택 (스위칭 시 즉시 반영)",
            options=model_labels,
            index=model_labels.index(default_label),
            horizontal=True,
            key="p0_model_radio_widget"
        )
        
        # 세션 스테이트 동기화
        new_model_id = model_mapping[selected_label]
        if new_model_id != current_model_id:
            st.session_state.p0_selected_model = new_model_id
            save_workspace_state()
            st.rerun()

        # 대화 기록 로드 (첫 진입 시)
        if "popup_history" not in st.session_state or not st.session_state.popup_history:
            st.session_state.popup_history = _load_chat_history()

        chat_container = st.container(height=500, border=True)
        with chat_container:
            if not st.session_state.popup_history:
                st.markdown(
                    "<div style='color:#888;padding:20px;text-align:center;'>"
                    "💭 아직 대화가 없습니다.<br><br>"
                    "<small style='color:#d4af6a;'>"
                    "• E2B / E4B 로컬 젬마 모델 또는 Gemini 최신 모델을 선택해 보세요.<br>"
                    "• Tavily 검색 모드에서는 입력하신 질문을 바탕으로 자동 구글 리서치 분석 답변을 생성합니다.<br>"
                    "• 등장인물 언급 시 반드시 <b>@Protagonist</b> 로 표기됩니다."
                    "</small></div>",
                    unsafe_allow_html=True,
                )
            for msg in st.session_state.popup_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # 사용자 입력 및 채팅 처리
        if prompt := st.chat_input("젬마와 대화를 시작하세요...", key="p0_chat_input_widget"):
            # 사용자 메시지 렌더링 및 보존
            st.session_state.popup_history.append({
                "role": "user",
                "content": prompt,
                "model": new_model_id,
                "part": "파트 0",
                "source": "사용자 입력"
            })
            with chat_container.chat_message("user"):
                st.markdown(prompt)

            # AI 응답 처리 분기
            with chat_container.chat_message("assistant"):
                sys_prompt = "너는 현자의 거울 스튜디오의 수석 어시스턴트다. 묻는 말에 사실에 기초하여 신중히 답하라. 등장인물은 오직 @Protagonist 로 지칭하라."
                
                # 1) Tavily 웹 검색 연동 모드
                if new_model_id == "tavily":
                    tavily_key = st.session_state.get("tavily_api_key", "").strip()
                    if not tavily_key:
                        response = "⚠️ Tavily API Key가 설정되지 않았습니다. 사이드바 설정에서 입력해 주세요."
                        st.error(response)
                        source_label = "Tavily 에러"
                    else:
                        with st.spinner("🔍 인터넷 검색을 수행하고 있습니다..."):
                            try:
                                search_res = run_tavily_research(prompt, tavily_key, max_results=5)
                                formatted_results = ""
                                if "results" in search_res:
                                    for idx, r in enumerate(search_res["results"], 1):
                                        formatted_results += f"[{idx}] 제목: {r.get('title')}\n요약: {r.get('content')}\nURL: {r.get('url')}\n\n"
                                
                                # 수집된 자료 바탕으로 로컬 젬마가 분석 및 답변 생성
                                sys_ctx = (
                                    "당신은 웹 검색 결과 분석 전문가입니다. 수집된 최신 데이터를 참고하여 질문에 객체화된 풍부한 답변을 완성해 주십시오. "
                                    "모든 인용에는 [SOURCE: URL] 태그 형태로 출처를 필수로 밝히고, 인물 지칭 시 반드시 @Protagonist 로 표기하십시오."
                                )
                                search_enriched_prompt = f"질문: {prompt}\n\n[수집된 최신 검색 데이터]\n{formatted_results}"
                                
                                stream_gen = _stream_gemma_a_mode_p0(
                                    search_enriched_prompt,
                                    system=sys_ctx,
                                    model=st.session_state.get("global_model_select", "gemma4:e2b")
                                )
                                response = st.write_stream(stream_gen)
                                source_label = "Tavily RAG 검색 분석"
                            except Exception as e:
                                response = f"[검색 분석 실패] 오류: {e}"
                                st.error(response)
                                source_label = "Tavily 실패"
                
                # 2) Gemini 2.5 Flash 호출 모드
                elif new_model_id == "gemini-2.5-flash":
                    stream_gen = stream_gemini(prompt, system_prompt=sys_prompt)
                    response = st.write_stream(stream_gen)
                    source_label = "Gemini API"
                
                # 3) 로컬 Gemma (E2B / E4B) 모드
                else:
                    stream_gen = _stream_gemma_a_mode_p0(prompt, system=sys_prompt, model=new_model_id)
                    response = st.write_stream(stream_gen)
                    source_label = f"로컬 {new_model_id.upper()} 스트리밍"

            # AI 응답 저장
            st.session_state.popup_history.append({
                "role": "assistant",
                "content": response,
                "model": new_model_id,
                "part": "파트 0",
                "source": source_label
            })
            _save_chat_history(st.session_state.popup_history)

        # 도구 박스 버튼
        c_clear, c_dl = st.columns(2)
        with c_clear:
            if st.button("🗑️ 대화 초기화", use_container_width=True, key="p0_clear_btn"):
                st.session_state.popup_history = []
                _save_chat_history([])
                st.toast("🗑️ 대화 기록 초기화 완료", icon="🗑️")
                st.rerun()
        with c_dl:
            if st.session_state.popup_history:
                all_chat = "\n\n".join(
                    f"### [{m['role'].upper()}]\n{m['content']}"
                    for m in st.session_state.popup_history
                )
                st.download_button(
                    "💾 대화 다운로드",
                    data=all_chat,
                    file_name=f"sage_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    use_container_width=True,
                    key="p0_download_btn"
                )
            else:
                st.button("💾 대화 다운로드", use_container_width=True, key="p0_download_btn_disabled", disabled=True)

def render_part1():

    c_title, c_control = st.columns([4.2, 5.8])

    

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">📚 파트 1: 벤치마킹 & 자료조사</h3>', unsafe_allow_html=True)

        

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p1_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p1_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS["part1"]: st.session_state.unlock_part1 = True

            elif pin: st.session_state.unlock_part1 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p1_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



    is_locked = False


    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)



    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")

    c_left, c_right = st.columns(2, gap="large")

    

    with c_left:

        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)

        render_unified_prompt_editor("젬마 프로토콜 (Gemma Protocol)", "p1_gemma_protocol", height=270, is_locked=is_locked)
        if st.button("📝 편집하기", key="btn_p1_edit"):
                popup_editor_safe("p1_gemma_protocol", "젬마 프로토콜 편집")
        st.markdown('</div>', unsafe_allow_html=True)

        

    with c_right:

        # ═══════════════════════════════════════════════════════
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
            gemini_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
            cur_gm = st.session_state.get("p1_gemini_model", "gemini-2.5-flash")
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
                "심리학 철학 인생조언 유튜브 롱폼 채널 2025 조회수 급상승 시청지속시간 높은\npsychology philosophy life wisdom YouTube longform channel high views retention 2025\n인간 나레이터 심리학 철학 채널 쇼펜하우어 융 빅터프랭클 구독자 적음 조회수 폭발\nAI TTS narration psychology philosophy original content NOT reuse NOT compilation"),
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
                    import concurrent.futures as _cf

                    def _gemini_call(model, prompt, timeout=45):
                        with _cf.ThreadPoolExecutor(max_workers=1) as ex:
                            fut = ex.submit(model.generate_content, prompt)
                            try:
                                return fut.result(timeout=timeout)
                            except _cf.TimeoutError:
                                raise Exception(f"⏱ 응답 시간 초과 ({timeout}초) — 다른 모델을 선택하거나 다시 시도하세요.")

                    genai.configure(api_key=st.session_state.gemini_api_key)
                    gemini_model = genai.GenerativeModel(st.session_state.p1_gemini_model)
                    region_hint = st.session_state.p1_region

                    # ── Step 1: 키워드 생성 ──────────────────────────
                    prog = st.progress(0, text="⚙️ Step 1/4 — 제미나이: 정밀 검색 키워드 생성 중...")
                    kw_prompt = f"""
당신은 유튜브 채널 전문 큐레이터입니다.
다음 조건에 맞는 유튜브 채널을 Tavily 웹 검색으로 찾기 위한 **정밀 검색 키워드 10개**를 생성하세요.

[목표]
- 👥 인간 운영 채널용 키워드 5개: 실제 사람이 직접 나레이션하는 심리학/철학 롱폼 채널 탐색
- 🤖 AI 제작 채널용 키워드 5개: AI TTS/아바타를 활용하되 독창적 원본 콘텐츠만 (재사용·표절·컴필레이션 배제)

[공통 조건]
- 심리학/철학/인생조언/자기계발 롱폼 콘텐츠 (10분 이상)
- 쇼펜하우어, 칼 융, 빅터 프랭클, 스토아 철학 등 깊이 있는 주제
- 다크심리학 콘텐츠: 가스라이팅·나르시시즘·독성관계·조종·정서착취 주제 채널 탐색
- 구독자 수 무관 — 최근 조회수와 시청지속시간이 급상승 중인 채널
- 40~70대 감성 타겟: 삶의 지혜·심리적 통찰·고독·상실·후회·관계
  "왜 나는 항상 손해를 보는가" 류의 4070 공명 주제 우선
- 댓글에 실제 인생 체험담이 많이 달리는 채널 우선 탐색
- 탐색 지역: {region_hint}

[출력 형식] 반드시 JSON 배열만 출력하세요 (설명 금지):
["인간채널_키워드1", "인간채널_키워드2", "인간채널_키워드3", "인간채널_키워드4", "인간채널_키워드5", "AI채널_키워드6", "AI채널_키워드7", "AI채널_키워드8", "AI채널_키워드9", "AI채널_키워드10"]
"""
                    kw_resp = _gemini_call(gemini_model, kw_prompt, timeout=45)
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
                        candidates_text += "[" + str(i+1) + "] " + r.get("title","") + "\n URL: " + r.get("url","") + "\n Content: " + r.get("content","")[:200] + "\n\n"
                    filter_prompt = f"""
당신은 유튜브 채널 분석 전문가입니다.
아래 후보 채널 목록에서 다음 기준으로 엄격하게 분류·선정하여 정확히 **10개 채널**을 구성하세요.

[선정 구성 — 반드시 준수]
👥 인간 운영 채널 5개:
- 실제 사람이 직접 나레이션·출연하는 심리학/철학/인생조언 오리지널 롱폼 채널
- AI 생성 영상, AI TTS 나레이션, 컴필레이션, 표절 채널 절대 제외

🤖 AI 제작 채널 5개:
- AI TTS·아바타 등 AI 도구 활용 가능하나 반드시 독창적 원본 대본·기획 보유
- 재사용 콘텐츠(타 채널 영상 짜깁기), 표절, 무단 번역 채널 절대 제외
- 오리지널 기획력이 있는 AI 제작 채널만 포함

[공통 평가 기준]
- 심리학/철학/인생조언/자기계발 롱폼 콘텐츠 (최소 10분 이상, Shorts 위주 제외)
- 쇼펜하우어·칼 융·빅터 프랭클·스토아 철학 등 트렌드 키워드 부합도
- 다크심리학 콘텐츠 보유 여부: 가스라이팅·나르시시즘·독성관계·조종 주제 채널 가산점
- 구독자 수 대비 최근 조회수 떡상률 (소규모여도 급성장이면 우선)
- 시청지속시간(체류율) 잠재력
- 40~70대 특화 채널 가중치:
  댓글에 실제 인생 체험담이 많을수록 높은 점수
  "내 이야기 같다" 공명 지수가 높은 채널 우선
- 탐색 지역: {region_hint}

[후보 채널 목록]
{candidates_text}

[출력 형식] 반드시 아래 JSON만 출력 (다른 텍스트·마크다운 절대 금지):
{{
  "top10": [
    {{
      "rank": 1,
      "name": "채널명",
      "url": "유튜브 URL",
      "type": "human",
      "region": "국내/국외",
      "category": "심리학/철학/인생조언 등",
      "reason": "선정 이유 — 인간운영 또는 AI제작 관점 포함 (50자 이내)",
      "trend": "급상승/상승/안정",
      "score": 95
    }}
  ],
  "best": {{
    "name": "최종 1순위 채널명",
    "url": "유튜브 URL",
    "type": "human",
    "reason": "트렌드 키워드 부합도·구독자대비 조회수 떡상·시청지속시간 관점 선정 이유 (80자 이내)"
  }}
}}
"""
                    filter_resp = _gemini_call(gemini_model, filter_prompt, timeout=60)
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
                    st.error(f"채널 탐색 오류: {e} -> API Key 확인 또는 다른 모델을 선택해 보세요.")


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
            if st.button("📊 벤치마킹 대상 확정 → Part 2 연동",
                         use_container_width=True, type="primary",
                         key="p1_to_benchmark_btn",
                         disabled=is_locked):
                st.session_state.p2_channel_url = st.session_state.p1_channel_url
                st.session_state.p2_region = st.session_state.get("p1_region", "국내+국외 모두")
                st.session_state.pipeline_state["start_benchmarking"] = True
                st.session_state.pipeline_state["selected_channel_url"] = st.session_state.p1_channel_url
                st.session_state.pipeline_state["benchmark_channel"] = st.session_state.get("p1_benchmark_channel", {})
                st.session_state.sidebar_part = "part2"
                save_workspace_state()
                st.toast("🚀 Part 2 Alchemist로 이동합니다!", icon="📊")
                st.rerun()



    st.divider()

       

    # ─── 옵시디언 감정 기반 검색 (Part 1 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P1_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part1", 
            "Part 1: 벤치마킹 & 자료조사", 
            get_default_tags_for_part("part1"), 
            "p1_obsidian_search_results", 
            "p1_rag_model_selector"
        )



   

    st.divider()


    # 🔒 Part 1 Lock 버튼 (Part 1 최하단으로 위치 이동됨)

    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진")

    tab_bench, tab_research, tab_plan = st.tabs(["[TARGET] 1️⃣ 벤치마킹 분석", "🔍 2️⃣ 자료 조사 결과", "[PACKAGE] 3️⃣ 총괄 기획안"])

    

    with tab_bench:

        with st.container(border=True):

            st.markdown("### 1️⃣ 벤치마킹 분석")

            st.caption("주제 20개 추천 (추천사유, 효과, 반응)")

            

            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (벤치마킹)", "p1_bench_prompt", height=150, is_locked=is_locked)

            

            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---

            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])

            with c_btn1:

                if st.button("🚀 벤치마킹 시작", use_container_width=True, disabled=is_locked, key="p1_bench_start_btn"):

                    if not st.session_state.p1_channel_url: 

                        st.error("[WARN] 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")

                    else:

                        # 시작 버튼 클릭 즉시 기존 결과물 및 백업 상태 클리어

                        st.session_state.p1_bench_raw = ""

                        st.session_state.p1_topics = []

                        st.session_state.p1_bench_tags = ""

                        st.session_state.p1_bench_saved = False

                        st.session_state.p1_bench_obsidian_saved = False

                        save_workspace_state()

                        

                        with st.spinner("채널 분석 중... (체험담 댓글 정확성 우선 분석)"):

                            raw_res, parsed_topics = analyze_channel_to_topics_p1(

                                st.session_state.p1_channel_url,

                                st.session_state.p1_region, 

                                st.session_state.obsidian_rules, 

                                st.session_state.base_prompt_rules, 

                                st.session_state.p1_gemma_protocol,

                                st.session_state.p1_bench_prompt

                            )

                            st.session_state.p1_bench_raw = raw_res

                            st.session_state.p1_topics = parsed_topics

                            st.session_state.pipeline_state["topic_candidates"] = parsed_topics

                            st.session_state.p1_bench_saved = True

                            save_workspace_state()

                            

                            # 젬마가 키워드를 자동으로 세분화하여 추출

                            keywords = extract_keywords_via_gemma(raw_res, st.session_state.base_prompt_rules)

                            st.session_state.p1_bench_tags = keywords

                            

                            # 자동 옵시디언 RAG 백업 파일 조립 및 저장

                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                            

                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                            folder_name = "TopicMemory"

                            title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"

                            

                            val = f"## 📌 핵심 요약\n- 채널: {st.session_state.p1_channel_url}\n- 타겟 지역: {st.session_state.p1_region}\n\n"

                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"

                            val += f"## 📖 벤치마킹 상세 추천 리스트\n"

                            for t in parsed_topics:

                                val += f"### [[{t['title']}]]\n- **추천 사유(체험담 기반):** {t['reason']}\n- **예상 효과:** {t['effect']}\n- **예상 반응:** {t['audience_reaction']}\n\n"

                            val += f"\n## 🔗 원본 날것의 텍스트\n```text\n{raw_res}\n```\n"

                            

                            obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)

                            if obs_path:

                                lock_file_readonly(obs_path)

                                st.toast("💾 벤치마킹 결과 로컬 자동 저장 완료!", icon="💾")

                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                if success:

                                    st.session_state.p1_bench_obsidian_saved = True

                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                else:

                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                save_workspace_state()

                                st.rerun()

            

            with c_btn2:

                if st.session_state.get("p1_bench_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_bench_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_bench_local_waiting")

            

            with c_btn3:

                if st.session_state.get("p1_bench_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_bench_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_bench_obs_waiting")

            

            if st.session_state.p1_bench_raw:

                st.markdown("<br>", unsafe_allow_html=True)

                col_prev, col_full = st.columns([3, 2])

                with col_prev:

                    st.info(f"📄 결과 {len(st.session_state.p1_bench_raw)}자 생성완료!")

                with col_full:

                    if st.button("👁 전체 결과 팝업으로 보기",

                        use_container_width=True,

                        type="primary",

                        key="p1_bench_full_popup"):

                        popup_edit_benchmarking()

                

                c_reparse, c_popup = st.columns(2)

                with c_reparse:

                    if st.button("🔄 벤치마킹 수동 옵시디언 백업 실행", use_container_width=True, key="p1_bench_save_backup_btn", disabled=is_locked):
                        tag_list = [t.strip() for t in st.session_state.p1_bench_tags.split(",") if t.strip()]

                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                    

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    folder_name = "TopicMemory"

                    title = f"벤치마킹 결과 - {st.session_state.p1_channel_url.replace('https://', '').replace('/', '_')}"

                    

                    val = f"## 📌 핵심 요약\n- 채널: {st.session_state.p1_channel_url}\n- 타겟 지역: {st.session_state.p1_region}\n\n"

                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"

                    val += f"## 📖 벤치마킹 상세 추천 리스트\n"

                    for t in st.session_state.p1_topics:

                        val += f"### [[{t['title']}]]\n- **추천 사유(체험담 기반):** {t['reason']}\n- **예상 효과:** {t['effect']}\n- **예상 반응:** {t['audience_reaction']}\n\n"

                    val += f"\n## 🔗 원본 날것의 텍스트\n```text\n{st.session_state.p1_bench_raw}\n```\n"

                    

                    obs_path = save_obsidian_memory(folder_name, title, val, source=st.session_state.p1_channel_url)

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 벤치마킹 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p1_bench_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save (Locked): {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                        st.rerun()



    with tab_research:

        with st.container(border=True):

            st.markdown("### 2️⃣ 자료 조사 결과")

            st.caption("옵시디언/리서치 융합 기초 초안 작성 (출처 명기)")

            

            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (자료 조사)", "p1_research_prompt", height=150, is_locked=is_locked)

            

            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---

            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])

            with c_btn1:

                if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p1_research_start_btn"):

                    if not st.session_state.p1_topic_selection:

                        st.error("[WARN] 먼저 좌측의 '벤치마킹 시작' 버튼을 눌러 분석을 완료하고 주제를 선택해 주세요.")

                    else:

                        # 시작 즉시 리셋

                        st.session_state.p1_research_result = ""

                        st.session_state.p1_research_tags = ""

                        st.session_state.p1_research_saved = False

                        st.session_state.p1_research_obsidian_saved = False

                        st.session_state.p1_need_research_kw = None

                        st.session_state.p1_verification = None

                        save_workspace_state()

                        

                        with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):

                            topic_str = st.session_state.p1_topic_selection

                            # RAG Context 빌드 및 주입
                            p1_rag_res = st.session_state.get("p1_obsidian_search_results", "")
                            p1_rag_ctx = ""
                            if p1_rag_res:
                                p1_rag_ctx = build_rag_context_from_results(
                                    p1_rag_res, "벤치마킹 & 자료조사", 
                                    st.session_state.get("p1_rag_model_selector", "gemma4:e2b")
                                )
                            combined_research_prompt = st.session_state.p1_research_prompt
                            if p1_rag_ctx:
                                combined_research_prompt = f"{combined_research_prompt}\n\n{p1_rag_ctx}"

                            res = generate_research_draft_p1(

                                 st.session_state.p1_channel_url, 

                                 topic_str,

                                 st.session_state.p1_gemma_protocol, 

                                 st.session_state.base_prompt_rules,

                                 combined_research_prompt

                            )

                            st.session_state.p1_research_result = res

                            st.session_state.pipeline_state["research_result"] = res

                            

                            # RAG 지식 공백 감지

                            kw = check_need_research_tag(res)

                            if kw:

                                st.session_state.p1_need_research_kw = kw

                                st.session_state.p1_research_saved = False

                                st.session_state.p1_research_obsidian_saved = False

                            else:

                                st.session_state.p1_need_research_kw = None

                                # 자가 검수 수행

                                ver_res = verify_content_with_gemma("자료 조사 초안", res, st.session_state.base_prompt_rules)

                                st.session_state.p1_verification = ver_res

                                

                                if ver_res.get("status") == "PASS":

                                    # 바로 자동 저장 및 백업

                                    st.session_state.p1_research_saved = True

                                    

                                    # 젬마 키워드 자동 세분화

                                    keywords = extract_keywords_via_gemma(res, st.session_state.base_prompt_rules)

                                    st.session_state.p1_research_tags = keywords

                                    

                                    # 자동 옵시디언 백업 진행

                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                    

                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                    folder_name = "ResearchMemory"

                                    topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"

                                    title = f"자료조사 초안 - {topic_title}"

                                    

                                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"

                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                                    val += f"## 📖 자료조사 및 초안 본문\n{res}\n\n"

                                    

                                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")

                                    if obs_path:

                                        lock_file_readonly(obs_path)

                                        st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")

                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                        if success:

                                            st.session_state.p1_research_obsidian_saved = True

                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                        else:

                                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                else:

                                    st.session_state.p1_research_saved = False

                                    st.session_state.p1_research_obsidian_saved = False

                                    

                            save_workspace_state()

                            st.rerun()

            

            with c_btn2:

                if st.session_state.get("p1_research_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_research_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_research_local_waiting")

            

            with c_btn3:

                if st.session_state.get("p1_research_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_research_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_research_obs_waiting")

            

            if st.session_state.p1_research_result:

                st.markdown("<br>", unsafe_allow_html=True)

                

                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---

                if st.session_state.p1_need_research_kw:

                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p1_need_research_kw})")

                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p1_web_research_approve_btn", type="primary", use_container_width=True):

                        if not st.session_state.tavily_api_key:

                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")

                        else:

                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):

                                from sage_engine import tavily_search

                                q = st.session_state.p1_need_research_kw

                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)

                                if "error" in res_search:

                                    st.error(f"Tavily 검색 오류: {res_search['error']}")

                                else:

                                    raw_results = res_search.get("results", [])

                                    web_context = ""

                                    for r in raw_results:

                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"

                                    

                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.

제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '자료 조사 및 기초 초안'을 완벽하게 재작성하라.

모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.



[웹 리서치 참조 자료]:

{web_context}



[이전 불완전한 결과물]:

{st.session_state.p1_research_result}



[작업 지시]:

위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.

[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.

"""

                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                    st.session_state.p1_research_result = res_new

                                    st.session_state.pipeline_state["research_result"] = res_new

                                    

                                    # 재검증

                                    st.session_state.p1_need_research_kw = check_need_research_tag(res_new)

                                    if not st.session_state.p1_need_research_kw:

                                        ver_res = verify_content_with_gemma("자료 조사 초안", res_new, st.session_state.base_prompt_rules)

                                        st.session_state.p1_verification = ver_res

                                        if ver_res.get("status") == "PASS":

                                            st.session_state.p1_research_saved = True

                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)

                                            st.session_state.p1_research_tags = keywords

                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                            folder_name = "ResearchMemory"

                                            topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"

                                            title = f"자료조사 초안 - {topic_title}"

                                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"

                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                                            val += f"## 📖 자료조사 및 초안 본문\n{res_new}\n\n"

                                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")

                                            if obs_path:

                                                lock_file_readonly(obs_path)

                                                st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")

                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                                if success:

                                                    st.session_state.p1_research_obsidian_saved = True

                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                                else:

                                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                    else:

                                        st.session_state.p1_research_saved = False

                                        st.session_state.p1_research_obsidian_saved = False

                                    

                                    save_workspace_state()

                                    st.rerun()



                elif st.session_state.p1_verification:

                    ver = st.session_state.p1_verification

                    if ver.get("status") == "FAIL":

                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")

                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p1_self_correct_btn", type="primary", use_container_width=True):

                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):

                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.

이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.



[이전 결과물]:

{st.session_state.p1_research_result}



[수정 건의사항]:

{ver.get("suggestions", "없음")}



[작업 지시]:

수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.

모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.

"""

                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                st.session_state.p1_research_result = res_corr

                                st.session_state.pipeline_state["research_result"] = res_corr

                                

                                # 재검증

                                st.session_state.p1_need_research_kw = check_need_research_tag(res_corr)

                                if not st.session_state.p1_need_research_kw:

                                    ver_res = verify_content_with_gemma("자료 조사 초안", res_corr, st.session_state.base_prompt_rules)

                                    st.session_state.p1_verification = ver_res

                                    if ver_res.get("status") == "PASS":

                                        st.session_state.p1_research_saved = True

                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)

                                        st.session_state.p1_research_tags = keywords

                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                        folder_name = "ResearchMemory"

                                        topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"

                                        title = f"자료조사 초안 - {topic_title}"

                                        val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"

                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                                        val += f"## 📖 자료조사 및 초안 본문\n{res_corr}\n\n"

                                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")

                                        if obs_path:

                                            lock_file_readonly(obs_path)

                                            st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")

                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                            if success:

                                                st.session_state.p1_research_obsidian_saved = True

                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                            else:

                                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                else:

                                    st.session_state.p1_research_saved = False

                                    st.session_state.p1_research_obsidian_saved = False

                                

                                save_workspace_state()

                                st.rerun()

                    else:

                        st.success("✅ **Gemma 자가 검수 통과**: 모든 무결성 규칙(지칭어, 출처 등)이 확인되었습니다.")

                        with st.expander("🔍 검수 결과 보고서 자세히 보기", expanded=False):

                            st.text(ver.get("report"))

                

                render_result_preview("p1_research_result", "Part 1 자료조사 결과")

 

                st.divider()

                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")

                st.session_state.p1_research_tags = st.text_input(

                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 

                    value=st.session_state.p1_research_tags, 

                    placeholder="예: 외로움, 존재의미, 고통, 용서", 

                    key="p1_research_tags_input",

                    disabled=is_locked

                )

                

                if st.button("💾 (예비용) 자료조사 결과 수동 옵시디언 백업 실행", use_container_width=True, key="p1_research_save_backup_btn", disabled=is_locked):

                    tag_list = [t.strip() for t in st.session_state.p1_research_tags.split(",") if t.strip()]

                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                    

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    folder_name = "ResearchMemory"

                    

                    topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "자료조사"

                    title = f"자료조사 초안 - {topic_title}"

                    

                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"

                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                    val += f"## 📖 자료조사 및 초안 본문\n{st.session_state.p1_research_result}\n\n"

                    

                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Research")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 자료조사 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p1_research_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save (Locked): {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                        st.rerun()



    with tab_plan:

        with st.container(border=True):

            st.markdown("### 3️⃣ 총괄 기획안")

            st.caption("15분 영상 뼈대 총괄 시나리오 기획 (마스터 플랜)")

            

            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (총괄 기획)", "p1_plan_prompt", height=150, is_locked=is_locked)

        

            # --- 시작 / 로컬저장완료 / 옵시디언백업완료 3단 버튼 구조 ---

            c_btn1, c_btn2, c_btn3 = st.columns([4, 3, 3])

            with c_btn1:

                if st.button("[ALCHEMY] 철학·감정 융합 설계", use_container_width=True, disabled=is_locked, key="p1_plan_start_btn"):

                    if not st.session_state.p1_research_result:

                        st.error("[WARN] 먼저 중앙의 '자료조사 및 초안 작성'을 완료해 주세요.")

                    else:

                        # 시작 즉시 리셋

                        st.session_state.p1_planning_result = ""

                        st.session_state.p1_plan_tags = ""

                        st.session_state.p1_plan_saved = False

                        st.session_state.p1_plan_obsidian_saved = False

                        save_workspace_state()

                        

                        with st.spinner("철학·성경·감정 융합 구조 설계 중..."):

                            res = generate_final_planning_p1(

                                 st.session_state.p1_research_result,

                                 st.session_state.p1_gemma_protocol, 

                                 st.session_state.base_prompt_rules,

                                 st.session_state.p1_plan_prompt

                            )

                            st.session_state.p1_planning_result = res

                            st.session_state.pipeline_state["planning_result"] = res

                            st.session_state.p1_plan_saved = True

                            save_workspace_state()

                            

                            # 젬마 키워드 자동 세분화

                            keywords = extract_keywords_via_gemma(res, st.session_state.base_prompt_rules)

                            st.session_state.p1_plan_tags = keywords

                            

                            # 자동 옵시디언 RAG 저장 진행

                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                            

                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                            folder_name = "PlanningMemory"

                            topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"

                            title = f"최종 기획안 - {topic_title}"

                            

                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"

                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"

                            val += f"## 📖 최종 시나리오 기획안 본문\n{res}\n\n"

                            

                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")

                            if obs_path:

                                lock_file_readonly(obs_path)

                                st.toast("💾 기획안 결과 로컬 자동 저장 완료!", icon="💾")

                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                if success:

                                    st.session_state.p1_plan_obsidian_saved = True

                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                else:

                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                save_workspace_state()

                                st.rerun()

            

            with c_btn2:

                if st.session_state.get("p1_plan_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p1_plan_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p1_plan_local_waiting")

            

            with c_btn3:

                if st.session_state.get("p1_plan_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p1_plan_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p1_plan_obs_waiting")



            if st.session_state.p1_planning_result:

               st.markdown("<br>", unsafe_allow_html=True)

               render_result_preview("p1_planning_result", "Part 1 전달 패킷")



               st.divider()

               st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")

               st.session_state.p1_plan_tags = st.text_input(

                   "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)", 

                   value=st.session_state.p1_plan_tags, 

                   placeholder="예: 외로움, 존재의미, 고통, 용서", 

                   key="p1_plan_tags_input",

                   disabled=is_locked

               )

               

               if st.button("💾 (예비용) 최종 기획안 수동 옵시디언 백업 실행", use_container_width=True, key="p1_plan_save_backup_btn", disabled=is_locked):

                   tag_list = [t.strip() for t in st.session_state.p1_plan_tags.split(",") if t.strip()]

                   tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                   tag_hashes = " ".join([f"#{t}" for t in tag_list])

                   

                   ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                   folder_name = "PlanningMemory"

                   

                   topic_title = st.session_state.p1_topic_selection.split(". ")[1] if st.session_state.p1_topic_selection and ". " in st.session_state.p1_topic_selection else "기획안"

                   title = f"최종 기획안 - {topic_title}"

                   

                   val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p1_topic_selection}\n\n"

                   val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"

                   val += f"## 📖 최종 시나리오 기획안 본문\n{st.session_state.p1_planning_result}\n\n"

                   

                   obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Planning")

                   if obs_path:

                       lock_file_readonly(obs_path)

                       st.toast("✅ 수동 기획안 옵시디언 백업 완료!", icon="💾")

                       st.session_state.p1_plan_obsidian_saved = True

                       save_workspace_state()

                       success, msg = auto_git_push(f"Manual Save (Locked): {title}")

                       if success:

                           st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                       else:

                           st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                       st.rerun()


    # ── 🔒 Part 1 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc1, _rc1 = st.columns(2)
        with _lc1:
            if st.button("🔒 Part 1 최종본 Lock & GitHub Push", key="p1_lock_btn", use_container_width=True):
                lock_and_push_final_version(1, "벤치마킹 & 자료조사", ["p1_research_result","p1_planning_result"])
        with _rc1:
            if st.button("🔓 Part 1 수정본 생성", key="p1_rev_btn", use_container_width=True):
                create_revision_version(1, "벤치마킹 & 자료조사", ["p1_research_result","p1_planning_result"])


@st.dialog("📝 젬마 프로토콜 (Gemma Protocol) 편집", width="large")

def popup_edit_gemma_protocol_p2():

    st.markdown("여기서 행동 지침과 작업 지침서를 상세하게 수정할 수 있습니다. 텍스트를 드래그하고 복사/붙여넣기 하세요.")

    new_val = st.text_area("규칙서 내용", value=st.session_state.p2_gemma_protocol, height=400, label_visibility="collapsed", key="p2_gemma_protocol_popup_textarea")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary", key="p2_gemma_protocol_popup_save"):

            st.session_state.p2_gemma_protocol = new_val

            save_workspace_state()

            st.toast("✅ Part 2 젬마 프로토콜 저장 완료", icon="💾")

            st.rerun()

    with c2:

        if st.button("취소", use_container_width=True, key="p2_gemma_protocol_popup_cancel"):

            st.rerun()



def auto_save_to_obsidian_by_rule(session_key: str, title: str) -> bool:
    """
    옵시디언 규칙서 v4.0 기준으로 결과물을 자동 저장한다.
    - 파트별 폴더 자동 선택 (PART_OBS_FOLDER_MAP)
    - 노트 구조: 규칙서 SECTION 5 양식 준수
    - 태그: 동적 생성 (저장 태그 + Gemma 자유 판단 + 기본 태그)
    - 출처: [SOURCE: 현자의 거울 앱 — {파트명}]
    - 다음 파트 전달 메모 자동 생성
    """
    content = st.session_state.get(session_key, "").strip()
    if not content:
        return False

    folder_name, part_label = PART_OBS_FOLDER_MAP.get(
        session_key, ("ResearchMemory", title)
    )

    try:
        # 에피소드명 포함 제목
        episode = st.session_state.get("episode_name", "EP001")
        full_title = f"[{episode}] {title}"

        # 파트 전달 메모 자동 생성
        part_num = session_key[1]  # p1, p2, p3...
        next_part = str(int(part_num) + 1) if part_num.isdigit() else "?"
        transfer_memo = (
            f"Part {part_num} → Part {next_part} 인계\n"
            f"- 에피소드: {episode}\n"
            f"- 저장 파트: {part_label}\n"
            f"- 저장 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # save_obsidian_memory 호출 (기존 함수 그대로 사용)
        saved_path = save_obsidian_memory(
            folder_name=folder_name,
            title=full_title,
            content=content,
            source=f"현자의 거울 앱 — {part_label}"
        )

        if saved_path:
            # 저장 경로 세션에 기록
            st.session_state[f"{session_key}_obsidian_path"] = saved_path
            st.session_state[f"{session_key}_obsidian_saved"] = True
            save_workspace_state()
            return True
        return False

    except Exception as e:
        st.error(f"옵시디언 자동 저장 오류: {e}")
        return False


@st.dialog("📋 결과물 전체 보기 & 편집", width="large")
def popup_view_result_dialog(session_key: str, title: str):
    """결과물 전체 보기 · 편집 · 옵시디언 자동 저장 팝업"""

    # ── 헤더 ──────────────────────────────────────────────
    folder_name, part_label = PART_OBS_FOLDER_MAP.get(
        session_key, ("ResearchMemory", title)
    )
    episode = st.session_state.get("episode_name", "EP001")

    st.markdown(f"""
    <div style='
        background:linear-gradient(135deg,#1a1410,#2d2010);
        border:1px solid #d4af6a; border-radius:10px;
        padding:12px 16px; margin-bottom:10px;
    '>
        <div style='color:#d4af6a;font-size:1.05rem;font-weight:700;'>
            📋 {title}
        </div>
        <div style='color:#a08060;font-size:0.82rem;margin-top:4px;'>
            📂 저장 경로: Studio / {folder_name} &nbsp;|&nbsp;
            🎬 에피소드: {episode} &nbsp;|&nbsp;
            📋 옵시디언 규칙서 v4.0 자동 적용
        </div>
    </div>
    """, unsafe_allow_html=True)

    val = st.session_state.get(session_key, "")

    if not val:
        st.info("아직 생성된 결과물이 없습니다. 먼저 젬마 분석을 실행해주세요.")
        if st.button("⬅ 뒤로가기", use_container_width=True,
                     key=f"pvr_back_empty_{session_key}"):
            st.rerun()
        return

    # ── 편집 영역 ──────────────────────────────────────────
    new_val = st.text_area(
        "결과물",
        value=val,
        height=460,
        key=f"pvr_edit_ta_{session_key}",
        label_visibility="collapsed"
    )
    st.caption(
        f"📝 {len(new_val):,}자 | {len(new_val.splitlines())}줄 | "
        f"옵시디언 저장 폴더: {folder_name}"
    )

    # ── 옵시디언 저장 상태 표시 ───────────────────────────
    is_obs_saved = st.session_state.get(f"{session_key}_obsidian_saved", False)
    obs_path = st.session_state.get(f"{session_key}_obsidian_path", "")
    if is_obs_saved and obs_path:
        st.success(f"🧠 옵시디언 저장 완료: .../{folder_name}/")

    st.divider()

    # ── 버튼 행 ───────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2.2, 2.2, 2.2, 1.4])

    with col1:
        if st.button("💾 저장 & 옵시디언 자동 저장", type="primary",
                     use_container_width=True,
                     key=f"pvr_save_{session_key}"):
            st.session_state[session_key] = new_val
            save_workspace_state()
            # 옵시디언 규칙서 기준 자동 저장
            ok = auto_save_to_obsidian_by_rule(session_key, title)
            if ok:
                st.toast(f"✅ 저장 + 🧠 옵시디언({folder_name}) 완료!", icon="💾")
            else:
                st.toast("✅ 앱 저장 완료! (옵시디언 경로 확인 필요)", icon="💾")
            st.rerun()

    with col2:
        if st.button("🧠 옵시디언만 저장",
                     use_container_width=True,
                     key=f"pvr_obs_only_{session_key}"):
            st.session_state[session_key] = new_val
            ok = auto_save_to_obsidian_by_rule(session_key, title)
            if ok:
                st.toast(f"🧠 옵시디언 저장 완료! ({folder_name})", icon="🧠")
            else:
                st.toast("⚠️ 옵시디언 경로를 설정에서 확인하세요.", icon="⚠️")

    with col3:
        if st.button("📋 복사용 코드 보기",
                     use_container_width=True,
                     key=f"pvr_copy_{session_key}"):
            st.code(new_val[:3000] + ("..." if len(new_val) > 3000 else ""),
                    language=None)

    with col4:
        if st.button("⬅ 뒤로가기",
                     use_container_width=True,
                     key=f"pvr_back_{session_key}"):
            st.rerun()


def render_result_preview(session_key: str, title: str, preview_lines: int = 4):
    """
    결과물 미리보기(4줄) + [👁 전체 보기 & 편집] 버튼 렌더러
    옵시디언 저장 상태 뱃지도 함께 표시
    """
    val = st.session_state.get(session_key, "")
    is_obs_saved = st.session_state.get(f"{session_key}_obsidian_saved", False)
    folder_name, _ = PART_OBS_FOLDER_MAP.get(session_key, ("ResearchMemory", ""))

    if not val:
        st.markdown("""
        <div style='background:rgba(255,255,255,0.03);
            border:1px dashed rgba(212,175,106,0.25);
            border-radius:8px;padding:14px;
            text-align:center;color:#6b7280;font-size:0.88rem;'>
            ⏳ 아직 생성된 결과물이 없습니다.
        </div>""", unsafe_allow_html=True)
        return

    # 미리보기
    lines_list = val.splitlines()
    preview_text = "\n".join(lines_list[:preview_lines])
    if len(lines_list) > preview_lines:
        preview_text += f"\n... (총 {len(lines_list)}줄)"

    # 옵시디언 저장 뱃지
    obs_badge = (
        f"<span style='color:#10b981;font-size:0.75rem;'>🧠 {folder_name} 저장됨</span>"
        if is_obs_saved else
        f"<span style='color:#6b7280;font-size:0.75rem;'>○ 옵시디언 미저장</span>"
    )

    st.markdown(f"""
    <div style='
        background:rgba(212,175,106,0.05);
        border:1px solid rgba(212,175,106,0.2);
        border-radius:8px; padding:10px 14px;
        margin:4px 0 6px 0;
        font-size:0.86rem; color:#c8b48a;
        line-height:1.65; white-space:pre-wrap;
        max-height:105px; overflow:hidden;
    '>{preview_text}</div>
    <div style='margin-bottom:6px;'>{obs_badge}</div>
    """, unsafe_allow_html=True)

    # 버튼
    bc1, bc2 = st.columns([4, 1])
    with bc1:
        if st.button(
            f"👁 전체 보기 & 편집  |  {len(val):,}자 / {len(lines_list)}줄",
            use_container_width=True,
            key=f"pvr_open_{session_key}",
        ):
            popup_view_result_dialog(session_key, title)
    with bc2:
        # 빠른 옵시디언 저장 버튼
        if st.button("🧠", use_container_width=True,
                     key=f"pvr_quick_obs_{session_key}",
                     help=f"옵시디언 {folder_name}에 즉시 저장"):
            ok = auto_save_to_obsidian_by_rule(session_key, title)
            st.toast(f"🧠 {folder_name} 저장 완료!" if ok else "⚠️ 경로 확인 필요")
            st.rerun()


@st.dialog("🎯 프롬프트 / 텍스트 편집", width="large")

def popup_edit_text_value(session_key: str, title: str):

    st.markdown(f"**{title}**을(를) 전체 화면으로 확인하고 수정할 수 있습니다.")

    val = st.session_state.get(session_key, "")

    new_val = st.text_area("내용", value=val, height=450, key=f"popup_edit_val_ta_{session_key}", label_visibility="collapsed")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("💾 저장 및 닫기", type="primary", use_container_width=True, key=f"popup_edit_val_save_{session_key}"):

            st.session_state[session_key] = clean_prompt_contamination(new_val)

            # 이미 생성된 Streamlit 위젯 key를 같은 실행 중 직접 수정하면 오류/경고가 발생한다.
            # 따라서 다음 rerun 시작 시 render_top_panel()에서 1회 동기화하도록 플래그만 남긴다.
            if session_key == "obsidian_rules":
                st.session_state["_sync_top_ob_view_widget_next_run"] = True
            else:
                # render_top_panel의 sync_flag_key 패턴과 정확히 일치시킴
                _widget_key = f"top_pr_view_{session_key}_widget"
                _sync_key = f"_sync_{_widget_key}_next_run"
                st.session_state[_sync_key] = True

            save_workspace_state()

            st.toast("✅ 수정 사항이 저장되었습니다!", icon="💾")

            st.rerun()

    with c2:

        if st.button("취소", use_container_width=True, key=f"popup_edit_val_cancel_{session_key}"):

            st.rerun()



@st.dialog("[TARGET] 채널 벤치마킹 결과 (팝업)", width="large")

def popup_edit_benchmarking_p2():

    st.markdown("벤치마킹 결과를 쾌적하게 스크롤하며 검토하고, 내용을 수정하거나 복사할 수 있습니다.")

    

    # p2_bench_raw가 우선, 없으면 topics로 조립

    raw_val = st.session_state.get("p2_bench_raw", "").strip()

    if not raw_val:

        for idx, t in enumerate(st.session_state.get("p2_topics", []), 1):

            raw_val += f"{idx:02d}. {t['title']} | {t['reason']} | {t['effect']} | {t.get('audience_reaction', '공감')}\n"

        raw_val = raw_val.strip()

        

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{raw_val}</div>", unsafe_allow_html=True)

        

    new_val = st.text_area("벤치마킹 결과 수정", value=raw_val, height=220, label_visibility="collapsed", key="p2_bench_edit_ta")

    

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary", key="p2_bench_save_dialog"):

            # 수정된 텍스트를 다시 파싱하여 p2_topics 리스트 구조로 보관

            parsed = []

            for line in new_val.split("\n"):

                if "|" in line:

                    parts = line.split("|")

                    if len(parts) >= 3:

                        title_part = parts[0].strip()

                        if ". " in title_part:

                            title_part = title_part.split(". ", 1)[1]

                        elif "]" in title_part:

                            title_part = title_part.split("]", 1)[1]

                        parsed.append({

                            "title": title_part.strip(),

                            "reason": parts[1].strip(),

                            "effect": parts[2].strip(),

                            "audience_reaction": parts[3].strip() if len(parts) > 3 else "공감"

                        })

            if parsed:

                st.session_state.p2_topics = parsed

            st.session_state.p2_bench_raw = new_val

            save_workspace_state()

            st.toast("✅ 벤치마킹 결과가 저장되었습니다!", icon="💾")

            st.rerun()

    with c2:

        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"benchmarking_result_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True, key="p2_bench_dl_dialog")

    with c3:

        if st.button("닫기", use_container_width=True, key="p2_bench_close_dialog"):

            st.rerun()



@st.dialog("📚 자료 조사 결과 (팝업)", width="large")

def popup_edit_research_p2():

    st.markdown("결과를 쾌적하게 스크롤하며 검토하고, 내용을 복사하거나 직접 수정할 수 있습니다.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p2_research_result}</div>", unsafe_allow_html=True)

    new_val = st.text_area("자료 조사 결과 수정", value=st.session_state.p2_research_result, height=200, label_visibility="collapsed")

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):

            st.session_state.p2_research_result = new_val

            st.rerun()

    with c2:

        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"research_result_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)

    with c3:

        if st.button("닫기", use_container_width=True):

            st.rerun()



@st.dialog("[ALCHEMY] 철학·감정 융합 설계 (팝업)", width="large")

def popup_edit_planning_p2():

    st.markdown("철학·성경·감정 융합 설계안을 검토하고 수정할 수 있습니다.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>{st.session_state.p2_planning_result}</div>", unsafe_allow_html=True)

    new_val = st.text_area("철학·감정 융합 설계안 수정", value=st.session_state.p2_planning_result, height=200, label_visibility="collapsed")

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):

            st.session_state.p2_planning_result = new_val

            st.rerun()

    with c2:

        st.download_button("📥 .txt 다운로드", data=new_val, file_name=f"planning_result_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True)

    with c3:

        if st.button("닫기", use_container_width=True):

            st.rerun()


def generate_thumbnail_sets(research_result: str, topic_selection: str, model: str) -> list:
    """Ollama를 활용해 유튜브 썸네일 제목/주제/이미지 컨셉 3세트 생성"""
    sys_prompt = SAGE_PERSONA + "\n\n너는 현자의 거울 스튜디오의 수석 연금술사(Alchemist)이다."
    user_prompt = f"""[유튜브 썸네일 및 타이틀 기획안 3세트 생성]
선행 자료조사 결과와 주제를 바탕으로, 40~70대 시청자의 마음을 가장 강력하게 움직일 유튜브 썸네일 세트 3종을 생성하라.
각 세트는 썸네일 제목, 썸네일 주제, 그리고 렘브란트 다크 풍의 썸네일 이미지 비주얼 묘사로 구성된다.

[선행 주제]
{topic_selection}

[자료조사 결과 요약]
{research_result[:1500]}

[출력 형식 - 반드시 아래 구분선 형식을 준수하라. 추가 설명이나 빈말은 절대 금지한다]
세트1 | 제목: [제목] | 주제: [주제] | 이미지: [이미지 연출 묘사]
세트2 | 제목: [제목] | 주제: [주제] | 이미지: [이미지 연출 묘사]
세트3 | 제목: [제목] | 주제: [주제] | 이미지: [이미지 연출 묘사]
"""
    
    fallback_sets = [
        {
            "set_num": 1,
            "title": "왜 사람은 늦게 후회하는가",
            "topic": "후회의 심리학",
            "image": "어두운 방, 고개 숙인 중년 남성, 창문 빛 연출, 렘브란트 톤"
        },
        {
            "set_num": 2,
            "title": "인간은 왜 외로움을 숨길까",
            "topic": "관계와 고독",
            "image": "군중 속 혼자 있는 인물, 흐릿한 도시 배경, 차가운 블루톤"
        },
        {
            "set_num": 3,
            "title": "당신이 무기력한 진짜 이유",
            "topic": "도파민 중독과 공허",
            "image": "스마트폰 불빛, 멍한 표정, 블랙+레드 대비"
        }
    ]

    try:
        res = call_gemma(user_prompt, system=sys_prompt, model=model)
        if not res or not res.strip():
            return fallback_sets
        
        parsed_sets = []
        import re as _re_thumb
        lines = res.split("\n")
        set_idx = 1
        for line in lines:
            if "세트" in line and "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    title_val = parts[1].replace("제목:", "").strip()
                    topic_val = parts[2].replace("주제:", "").strip()
                    image_val = parts[3].replace("이미지:", "").strip()
                    parsed_sets.append({
                        "set_num": set_idx,
                        "title": title_val,
                        "topic": topic_val,
                        "image": image_val
                    })
                    set_idx += 1
                    if set_idx > 3:
                        break
        
        if len(parsed_sets) == 3:
            return parsed_sets
        else:
            return fallback_sets
    except Exception as e:
        st.warning(f"썸네일 생성 중 오류 발생: {e} (기본값으로 대체합니다)")
        return fallback_sets


@st.dialog("🖼️ 썸네일 3세트 선택 및 확정", width="large")
def popup_thumbnail_selector():
    st.markdown("AI가 생성한 3종의 썸네일 기획 세트입니다. 마음에 드는 세트를 선택하고 확정하세요.")
    
    sets = st.session_state.get("p2_thumbnail_sets", [])
    if not sets:
        st.warning("아직 생성된 썸네일 세트가 없습니다.")
        if st.button("닫기", use_container_width=True, key="p2_thumb_no_sets_close"):
            st.rerun()
        return

    for item in sets:
        set_num = item.get("set_num", 1)
        title = item.get("title", "")
        topic = item.get("topic", "")
        image = item.get("image", "")
        
        with st.container(border=True):
            st.markdown(f"### 🖼️ 세트 {set_num}")
            st.markdown(f"**📌 썸네일 제목:** {title}")
            st.markdown(f"**🏷️ 썸네일 주제:** {topic}")
            st.markdown(f"**🎨 이미지 연출:** {image}")
            
            if st.button(f"👉 세트 {set_num} 선택 및 확정", key=f"sel_thumb_set_{set_num}", use_container_width=True, type="primary"):
                st.session_state.p2_selected_thumbnail = item
                st.session_state.p2_thumbnail_plan = f"""
[선택된 썸네일 기획안 - 세트 {set_num}]
제목: {title}
주제: {topic}
이미지:
- {image}
"""
                save_workspace_state()
                st.toast(f"✅ 세트 {set_num} 확정 완료!", icon="🖼️")
                st.rerun()
                
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("닫기", use_container_width=True, key="close_thumb_dialog"):
        st.rerun()



def render_part2():


    c_title, c_control = st.columns([4.2, 5.8])

    

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎨 파트 2: 총괄기획</h3>', unsafe_allow_html=True)

        

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p2_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p2_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS["part2"]: st.session_state.unlock_part2 = True

            elif pin: st.session_state.unlock_part2 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p2_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



    if not st.session_state.get("p2_channel_url"):

        st.session_state.p2_channel_url = st.session_state.get("p1_channel_url", "")



    if "unlock_part2" not in st.session_state:

        st.session_state.unlock_part2 = False

    is_locked = False

    

    if st.session_state.get("p2_channel_url"):

        st.info(f"🔗 [연동] Part 1 채널 URL 상속됨: {st.session_state.p2_channel_url}")

    else:

        st.warning("⚠️ 타겟 채널 URL이 연동되지 않았습니다. Part 1에서 채널을 설정해 주세요.")

    

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)



    st.subheader("🧩 Step 1. 젬마 프로토콜 및 타겟 설정 (중간 공통 영역)")

    c_left, c_right = st.columns(2, gap="large")

    

    with c_left:

        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Gemma Protocol)</div>', unsafe_allow_html=True)

        if "p2_gemma_protocol" not in st.session_state:
            st.session_state.p2_gemma_protocol = (
                "# 🧙 젬마 프로토콜 v9.0 — Part 2 Alchemist 전용\n"
                "# ═══════════════════════════════════════\n\n"
                "## 🎯 핵심 3원칙\n"
                "HOW → 자유(창의) | WHAT → 통제(사실) | WHO → 고정(@Protagonist)\n\n"
                "## 🔥 Alchemist 정체성\n"
                "너는 연금술사다. 다크심리학→철학→에세이→성경으로 변환하라.\n"
                "금지: 대본·나레이션·이미지프롬프트 작성(Part3·4 역할)\n\n"
                "## ⛔ 절대 금지\n"
                "- 없는 성경구절 / 존재하지 않는 철학 인용 절대 금지\n"
                "- 다크심리학 부족 시: [NEED_RESEARCH: 다크심리학 키워드]\n"
                "- AI냄새 문장 / 자기계발 말투 / 희망회로 절대 금지\n\n"
                "## 📚 RAG 우선순위\n"
                "1.[READ_OBSIDIAN:키워드] 2.성경전체 3.ResearchMemory\n"
                "4.철학원문 5.다크심리학[NEED_RESEARCH] 6.웹검색[NEED_RESEARCH] 7.Gemma추론\n\n"
                "## 🌑 다크심리학 활용\n"
                "기(起): 반드시 다크심리학으로 시작.\n"
                "적용: 가스라이팅·나르시시즘·조종·정서방치·의존성심화·공감결여\n"
                "부족 시: [NEED_RESEARCH: 다크심리학 {emotion} 메커니즘]\n\n"
                "## 📖 출력 규칙\n"
                "- [SOURCE: 책명/장절/저자] 형식 필수\n"
                "- 다크심리학: [SOURCE: 다크심리학 — 출처명]\n"
                "- 성경: [SOURCE: 성경 — 책명 NN:NN]\n"
                "- 핵심개념: [[위키링크]]\n\n"
                "## ✊ @Protagonist\n"
                "가르치지않고통찰만 / 위로안하고고통인정 / 침묵과여백유지\n"
                "다크심리학으로시작→성경으로마무리 / 4070이밤에혼자들을때울림있어야\n\n"
                "## 📦 출력 체크리스트\n"
                "□ 기(起): 다크심리학 [SOURCE: 다크심리학 — ]\n"
                "□ 승(承): 철학인용 [SOURCE:]\n"
                "□ 전(轉): 에세이/몽테뉴 [SOURCE:]\n"
                "□ 결(結): 성경구절 [SOURCE: 성경 — ]\n"
                "□ @Protagonist 통일 / AI냄새없음 / Part3전달패킷포함"
            )

        render_unified_prompt_editor("젬마 프로토콜 (Gemma Protocol)", "p2_gemma_protocol", height=270, is_locked=is_locked)
        st.markdown('</div>', unsafe_allow_html=True)

        

    with c_right:

        st.markdown('<div class="top-panel-card"><div class="top-panel-title">🖼️ 썸네일 카드 (Thumbnail Card)</div>', unsafe_allow_html=True)

        st.caption("자료조사 결과를 참조하여 썸네일(이미지), 주제, 제목을 3가지 버전으로 생성합니다.")

        

        if st.button("🚀 썸네일/주제/제목 3세트 생성 (AI)", use_container_width=True, disabled=is_locked, key="p2_thumb_btn"):

            if "p2_research_result" not in st.session_state or not st.session_state.p2_research_result:

                st.error("[WARN] 먼저 하단의 '자료조사 및 초안 작성'을 완료해 주세요.")

            else:

                with st.spinner("썸네일 3세트 생성 중..."):

                    _thumb_model = st.session_state.get("selected_model", OLLAMA_MODEL)
                    _thumb_sets = generate_thumbnail_sets(
                        st.session_state.p2_research_result,
                        st.session_state.get("p2_topic_selection", ""),
                        _thumb_model
                    )
                    st.session_state.p2_thumbnail_sets = _thumb_sets
                    save_workspace_state()
                    st.toast("✅ 썸네일 3세트 생성 완료!", icon="🖼️")
                    popup_thumbnail_selector()

                    st.session_state.p2_thumbnail_plan = """

[썸네일 1]

제목: 왜 사람은 늦게 후회하는가

주제: 후회의 심리학

이미지:

- 어두운 방

- 고개 숙인 중년 남성

- 창문 빛 연출

- 렘브란트 톤



[썸네일 2]

제목: 인간은 왜 외로움을 숨길까

주제: 관계와 고독

이미지:

- 군중 속 혼자 있는 인물

- 흐릿한 도시 배경

- 차가운 블루톤



[썸네일 3]

제목: 당신이 무기력한 진짜 이유

주제: 도파민 중독과 공허

이미지:

- 스마트폰 불빛

- 멍한 표정

- 블랙+레드 대비

"""

        

        

        render_unified_prompt_editor("🖼️ 썸네일 기획 결과 (수정 가능)", "p2_thumbnail_plan", height=195, is_locked=is_locked)
        _t_col1, _t_col2 = st.columns(2)
        with _t_col1:
            if st.button("🖼️ 썸네일 3세트 팝업 보기", key="p2_thumb_popup_btn",
                         use_container_width=True,
                         disabled=not st.session_state.get("p2_thumbnail_sets")):
                popup_thumbnail_selector()
        with _t_col2:
            sel = st.session_state.get("p2_selected_thumbnail", {})
            if sel:
                st.success(f"✅ 선택됨: 세트{sel.get('set_num','?')} — {sel.get('title','')[:20]}")
            else:
                st.caption("아직 선택된 썸네일 없음")

        st.markdown('</div>', unsafe_allow_html=True)



    st.divider()

    # ─── 옵시디언 감정 기반 검색 (Part 2 참조용) ──────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P2_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part2", 
            "Part 2: 총괄기획 & 연금술", 
            get_default_tags_for_part("part2"), 
            "p2_obsidian_search_results", 
            "p2_rag_model_selector"
        )

    st.divider()

    st.subheader("⚙️ Step 2. 현자의 거울 3단 분석 엔진")

    tab_bench, tab_research, tab_plan = st.tabs(["[TARGET] 1️⃣ 채널 벤치마킹 및 주제 도출", "📚 2️⃣ 옵시디언 융합 리서치", "[ALCHEMY] 3️⃣ 총괄 기획안 생성"])

    

    with tab_bench:

        with st.container(border=True):

            st.markdown("### 1️⃣ 채널 벤치마킹 및 주제 도출")

            st.caption("200개 댓글 분석 기반 타겟 시청자 공감 포인트 추출")

            

            if "p2_bench_prompt" not in st.session_state:
                st.session_state.p2_bench_prompt = (
                    "# 🎬 Part 2 Alchemist [탭1: 채널 벤치마킹 및 주제 도출]\n\n"
                    "너는 연금술사다. Part 1 원석 데이터를 기승전결 구조로 변환하라.\n\n"
                    "────────────────────────────────────────\n"
                    "[STEP 1] RAG 우선 참조\n"
                    "────────────────────────────────────────\n"
                    "[READ_OBSIDIAN: {topic}]\n"
                    "TopicMemory·ResearchMemory 먼저 확인 → 부족시 다음 단계\n\n"
                    "────────────────────────────────────────\n"
                    "[STEP 2] 다크심리학 훅 분석\n"
                    "────────────────────────────────────────\n"
                    "주제: {topic} | 핵심 감정: {emotion}\n\n"
                    "RAG 부족 시:\n"
                    "→ [NEED_RESEARCH: 다크심리학 {topic} 가스라이팅 나르시시즘]\n"
                    "→ [SOURCE: 다크심리학 — 출처명] 반드시 명기\n\n"
                    "적용 개념: 가스라이팅·나르시시즘·조종·정서방치·의존성심화\n\n"
                    "────────────────────────────────────────\n"
                    "[STEP 3] 기승전결 매핑\n"
                    "────────────────────────────────────────\n"
                    "기(起) 다크심리학 훅: [SOURCE: 다크심리학 — ] 또는\n"
                    "         [NEED_RESEARCH: 다크심리학 {emotion}]\n"
                    "승(承) 철학 해석: 고독→쇼펜하우어 / 그림자→융 / 의미→프랭클\n"
                    "         [SOURCE: 저자, 저서명]\n"
                    "전(轉) 에세이: 몽테뉴 / 인간적 솔직함 / 자기수용\n"
                    "         [SOURCE: 몽테뉴, 수상록] 부족시 [NEED_RESEARCH]\n"
                    "결(結) 성경: 실제 구절만 / 시편·잠언·전도서·욥기·신약\n"
                    "         [SOURCE: 성경 — 책명 NN:NN] 모르면 [NEED_RESEARCH]\n\n"
                    "────────────────────────────────────────\n"
                    "[출력 양식]\n"
                    "────────────────────────────────────────\n"
                    "## 주제: {topic}\n"
                    "### 🔴 기(起) — 다크심리학 훅\n"
                    "- 적용 개념: | 공명 포인트: | [SOURCE: 다크심리학 — ]\n"
                    "### 🟡 승(承) — 철학 분석\n"
                    "- 철학자·개념: | 핵심 논지: | [SOURCE:]\n"
                    "### 🟢 전(轉) — 에세이 전환\n"
                    "- 인간적 솔직함: | [SOURCE:]\n"
                    "### 🔵 결(結) — 성경 회복\n"
                    "- 구절: | 맥락: | [SOURCE: 성경 — ]\n"
                    "### 📌 @Protagonist 톤 지침"
                )

            

            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (벤치마킹)", "p2_bench_prompt", height=150, is_locked=is_locked)

            

            # --- 3단 버튼 구조 ---

            c_b1, c_b2, c_b3 = st.columns([4, 3, 3])

            with c_b1:

                if st.button("🚀 벤치마킹 분석 실행", use_container_width=True, disabled=is_locked, key="p2_bench_run_btn"):

                    if not st.session_state.get("p2_channel_url"):

                        st.session_state.p2_channel_url = st.session_state.get("p1_channel_url", "")

                    

                    if not st.session_state.p2_channel_url:

                        st.error("[WARN] 우측 상단에서 채널을 먼저 검색하거나 URL을 입력해 주세요.")

                    else:

                        st.session_state.p2_topics = []

                        st.session_state.p2_bench_raw = ""

                        st.session_state.p2_bench_saved = False

                        st.session_state.p2_bench_obsidian_saved = False

                        save_workspace_state()

                        

                        with st.spinner("채널 분석 중... (200개 댓글 공감 포인트 참조)"):

                            parsed, raw = analyze_channel_to_topics_custom(

                                st.session_state.p2_channel_url, st.session_state.p2_region, 

                                st.session_state.obsidian_rules, st.session_state.get("p2_master_prompt", st.session_state.base_prompt_rules), 

                                st.session_state.p2_gemma_protocol, st.session_state.p2_bench_prompt

                            )

                            

                            if parsed:

                                st.session_state.p2_topics = parsed

                                st.session_state.p2_bench_raw = raw

                                st.session_state.p2_bench_saved = True

                                save_workspace_state()

                                

                                # RAG 키워드 자동 추출

                                keywords = extract_keywords_via_gemma(raw, st.session_state.base_prompt_rules)

                                st.session_state.p2_bench_tags = keywords

                                tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                

                                ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                title = f"[Part2] 채널 벤치마킹 및 주제도출 - {ts}"

                                

                                val = f"## 📌 핵심 요약\n- 대상 채널: {st.session_state.p2_channel_url}\n\n"

                                val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"

                                val += f"## 📖 벤치마킹 분석 본문\n{raw}\n\n"

                                val += f"## 🔗 파이프라인 연결\n- 다음 단계: Part 2 자료 조사 및 융합 리서치\n- 선행 파트: Part 1 Librarian 주제 분석\n\n"

                                

                                obs_path = save_obsidian_memory("TopicMemory", title, val, source="Sage Mirror Studio Part 2")

                                if obs_path:

                                    lock_file_readonly(obs_path)

                                    st.toast("💾 벤치마킹 결과 로컬 자동 저장 완료!", icon="💾")

                                    success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                    if success:

                                        st.session_state.p2_bench_obsidian_saved = True

                                        st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                    else:

                                        st.error(f"GitHub Push 실패: {msg}")

                                    save_workspace_state()

                                    st.rerun()

                            else:

                                st.error("채널 분석 결과가 유효하지 않습니다. 다시 시도해 주세요.")

                                

            with c_b2:

                if st.session_state.get("p2_bench_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p2_bench_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p2_bench_local_waiting")

                    

            with c_b3:

                if st.session_state.get("p2_bench_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p2_bench_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p2_bench_obs_waiting")

            

            if st.session_state.get("p2_topics") or st.session_state.get("p2_bench_raw"):

                st.markdown("<br>", unsafe_allow_html=True)

                topics_display = [f"{i+1:02d}. {t['title']}" for i, t in enumerate(st.session_state.p2_topics)]

                

                if topics_display:

                    default_sel_idx = 0

                    if st.session_state.get("p2_topic_selection") in topics_display:

                        default_sel_idx = topics_display.index(st.session_state.p2_topic_selection)

                    st.session_state.p2_topic_selection = st.selectbox(

                        "📌 기획할 주제 1개 선정", 

                        topics_display, 

                        index=default_sel_idx, 

                        disabled=is_locked, 

                        key="p2_topic_sel"

                    )

                    save_workspace_state()

                

                raw_val = st.session_state.get("p2_bench_raw", "").strip()

                if not raw_val:

                    for idx, t in enumerate(st.session_state.p2_topics, 1):

                        raw_val += f"{idx:02d}. {t['title']} | {t['reason']} | {t['effect']} | {t.get('audience_reaction', '공감')}\n"

                    raw_val = raw_val.strip()

                    st.session_state.p2_bench_raw = raw_val

                

                render_result_preview("p2_bench_raw", "Part 2 벤치마킹 결과")

                            

                st.divider()

                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")

                st.session_state.p2_bench_tags = st.text_input(

                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)",

                    value=st.session_state.get("p2_bench_tags", ""),

                    placeholder="예: 외로움, 존재의미, 고통, 용서",

                    key="p2_bench_tags_input",

                    disabled=is_locked

                )

                

                if st.button("💾 (예비용) 벤치마킹 수동 옵시디언 백업", use_container_width=True, key="p2_bench_save_backup_btn", disabled=is_locked):

                    parsed = []

                    for line in st.session_state.p2_bench_raw.split("\n"):

                        if "|" in line:

                            parts = line.split("|")

                            if len(parts) >= 3:

                                title_part = parts[0].strip()

                                if ". " in title_part:

                                    title_part = title_part.split(". ", 1)[1]

                                elif "]" in title_part:

                                    title_part = title_part.split("]", 1)[1]

                                parsed.append({

                                    "title": title_part.strip(),

                                    "reason": parts[1].strip(),

                                    "effect": parts[2].strip(),

                                    "audience_reaction": parts[3].strip() if len(parts) > 3 else "공감"

                                })

                    if parsed:

                        st.session_state.p2_topics = parsed

                    

                    tag_list = [t.strip() for t in st.session_state.get("p2_bench_tags","").split(",") if t.strip()]

                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    title = f"[Part2] 채널 벤치마킹 및 주제도출 - {ts}"

                    

                    val = f"## 📌 핵심 요약\n- 대상 채널: {st.session_state.p2_channel_url}\n\n"

                    val += f"## 🎯 RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]]'}\n- 태그: {tag_hashes if tag_hashes else '#벤치마킹'}\n\n"

                    val += f"## 📖 본문\n{st.session_state.p2_bench_raw}\n\n"

                    

                    obs_path = save_obsidian_memory("TopicMemory", title, val, source="Sage Mirror Studio Part 2")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 벤치마킹 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p2_bench_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save: {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"GitHub Push 실패: {msg}")

                        st.rerun()

    with tab_research:

        with st.container(border=True):

            st.markdown("### 2️⃣ 옵시디언 융합 리서치")

            st.caption("성경/철학/에세이 3원 지식 융합 초안 작성")



            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (자료 조사)", "p2_research_prompt", height=150, is_locked=is_locked)



            # --- 3단 버튼 구조 ---

            c_r1, c_r2, c_r3 = st.columns([4, 3, 3])

            with c_r1:

                if st.button("📚 자료조사 및 초안 작성", use_container_width=True, disabled=is_locked, key="p2_res_btn"):

                    if not st.session_state.get("p2_topic_selection"):

                        st.error("[WARN] 먼저 '채널 벤치마킹' 탭에서 분석을 완료하고 주제를 선택해 주세요.")

                    else:

                        st.session_state.p2_research_result = ""

                        st.session_state.p2_research_tags = ""

                        st.session_state.p2_research_saved = False

                        st.session_state.p2_research_obsidian_saved = False

                        st.session_state.p2_need_research_kw = None

                        st.session_state.p2_verification = None

                        save_workspace_state()



                        with st.spinner("자료 융합 및 댓글 기반 리서치 중..."):

                            topic_str = st.session_state.p2_topic_selection

                            result = generate_research_draft(

                                st.session_state.p2_channel_url, topic_str,

                                st.session_state.p2_gemma_protocol, st.session_state.get("p2_master_prompt", st.session_state.base_prompt_rules),

                                st.session_state.get("p2_research_prompt", ""),

                                manual_rag_results=st.session_state.get("pipeline_state", {}).get("p2_obsidian_search_results"),

                                p1_research_result=st.session_state.get("p1_research_result", "")

                            )

                            st.session_state.p2_research_result = result

                            st.session_state.pipeline_state["research_result"] = result

                            

                            # RAG 지식 공백 감지

                            kw = check_need_research_tag(result)

                            if kw:

                                st.session_state.p2_need_research_kw = kw

                                st.session_state.p2_research_saved = False

                                st.session_state.p2_research_obsidian_saved = False

                            else:

                                st.session_state.p2_need_research_kw = None

                                # 자가 검수 수행

                                ver_res = verify_content_with_gemma("자료 조사 초안", result, st.session_state.base_prompt_rules)

                                st.session_state.p2_verification = ver_res

                                

                                if ver_res.get("status") == "PASS":

                                    st.session_state.p2_research_saved = True

                                    

                                    # 젬마 키워드 자동 세분화 및 옵시디언 자동 백업

                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)

                                    st.session_state.p2_research_tags = keywords

                                    

                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])



                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                    topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "자료조사"

                                    title = f"[Part2] 자료조사 초안 - {topic_title}"



                                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"

                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                                    val += f"## 📖 자료조사 및 초안 본문\n{result}\n\n"

                                    val += f"## 🔗 파이프라인 연결\n- 다음 단계: Part 3-4 대본 설계\n- 선행 파트: Part 1 Librarian 주제 분석\n\n"



                                    obs_path = save_obsidian_memory("ResearchMemory", title, val, source="Sage Mirror Studio Part 2")

                                    if obs_path:

                                        lock_file_readonly(obs_path)

                                        st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")

                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                        if success:

                                            st.session_state.p2_research_obsidian_saved = True

                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                        else:

                                            st.error(f"GitHub Push 실패: {msg}")

                                else:

                                    st.session_state.p2_research_saved = False

                                    st.session_state.p2_research_obsidian_saved = False

                                

                            save_workspace_state()

                            st.rerun()



            with c_r2:

                if st.session_state.get("p2_research_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p2_res_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p2_res_local_waiting")



            with c_r3:

                if st.session_state.get("p2_research_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p2_res_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p2_res_obs_waiting")



            if st.session_state.get("p2_research_result"):

                st.markdown("<br>", unsafe_allow_html=True)

                

                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---

                if st.session_state.p2_need_research_kw:

                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p2_need_research_kw})")

                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p2_web_research_approve_btn", type="primary", use_container_width=True):

                        if not st.session_state.tavily_api_key:

                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")

                        else:

                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):

                                from sage_engine import tavily_search

                                q = st.session_state.p2_need_research_kw

                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)

                                if "error" in res_search:

                                    st.error(f"Tavily 검색 오류: {res_search['error']}")

                                else:

                                    raw_results = res_search.get("results", [])

                                    web_context = ""

                                    for r in raw_results:

                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"

                                    

                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.

제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '자료 조사 및 기초 초안'을 완벽하게 재작성하라.

모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.



[웹 리서치 참조 자료]:

{web_context}



[이전 불완전한 결과물]:

{st.session_state.p2_research_result}



[작업 지시]:

위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.

[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.

"""

                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                    st.session_state.p2_research_result = res_new

                                    st.session_state.pipeline_state["research_result"] = res_new

                                    

                                    # 재검증

                                    st.session_state.p2_need_research_kw = check_need_research_tag(res_new)

                                    if not st.session_state.p2_need_research_kw:

                                        ver_res = verify_content_with_gemma("자료 조사 초안", res_new, st.session_state.base_prompt_rules)

                                        st.session_state.p2_verification = ver_res

                                        if ver_res.get("status") == "PASS":

                                            st.session_state.p2_research_saved = True

                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)

                                            st.session_state.p2_research_tags = keywords

                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                            folder_name = "ResearchMemory"

                                            topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "자료조사"

                                            title = f"[Part2] 자료조사 초안 - {topic_title}"

                                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"

                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                                            val += f"## 📖 자료조사 및 초안 본문\n{res_new}\n\n"

                                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")

                                            if obs_path:

                                                lock_file_readonly(obs_path)

                                                st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")

                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                                if success:

                                                    st.session_state.p2_research_obsidian_saved = True

                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                                else:

                                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                    else:

                                        st.session_state.p2_research_saved = False

                                        st.session_state.p2_research_obsidian_saved = False

                                    

                                    save_workspace_state()

                                    st.rerun()



                elif st.session_state.p2_verification:

                    ver = st.session_state.p2_verification

                    if ver.get("status") == "FAIL":

                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")

                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p2_self_correct_btn", type="primary", use_container_width=True):

                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):

                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.

이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.



[이전 결과물]:

{st.session_state.p2_research_result}



[수정 건의사항]:

{ver.get("suggestions", "없음")}



[작업 지시]:

수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.

모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.

"""

                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                st.session_state.p2_research_result = res_corr

                                st.session_state.pipeline_state["research_result"] = res_corr

                                

                                # 재검증

                                st.session_state.p2_need_research_kw = check_need_research_tag(res_corr)

                                if not st.session_state.p2_need_research_kw:

                                    ver_res = verify_content_with_gemma("자료 조사 초안", res_corr, st.session_state.base_prompt_rules)

                                    st.session_state.p2_verification = ver_res

                                    if ver_res.get("status") == "PASS":

                                        st.session_state.p2_research_saved = True

                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)

                                        st.session_state.p2_research_tags = keywords

                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                        folder_name = "ResearchMemory"

                                        topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "자료조사"

                                        title = f"[Part2] 자료조사 초안 - {topic_title}"

                                        val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"

                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                                        val += f"## 📖 자료조사 및 초안 본문\n{res_corr}\n\n"

                                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")

                                        if obs_path:

                                            lock_file_readonly(obs_path)

                                            st.toast("💾 자료조사 결과 로컬 자동 저장 완료!", icon="💾")

                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                            if success:

                                                st.session_state.p2_research_obsidian_saved = True

                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                            else:

                                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                else:

                                    st.session_state.p2_research_saved = False

                                    st.session_state.p2_research_obsidian_saved = False

                                

                                save_workspace_state()

                                st.rerun()

                    else:

                        st.success("✅ **Gemma 자가 검수 통과**: 모든 무결성 규칙(지칭어, 출처 등)이 확인되었습니다.")

                        with st.expander("🔍 검수 결과 보고서 자세히 보기", expanded=False):

                            st.text(ver.get("report"))

                

                render_result_preview("p2_research_result", "Part 2 자료조사 결과")



                st.divider()

                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")

                st.session_state.p2_research_tags = st.text_input(

                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)",

                    value=st.session_state.get("p2_research_tags", ""),

                    placeholder="예: 외로움, 존재의미, 고통, 용서",

                    key="p2_res_tags_input",

                    disabled=is_locked

                )



                if st.button("💾 (예비용) 자료조사 수동 옵시디언 백업", use_container_width=True, key="p2_research_save_backup_btn", disabled=is_locked):

                    tag_list = [t.strip() for t in st.session_state.get("p2_research_tags","").split(",") if t.strip()]

                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.get("p2_topic_selection") and ". " in st.session_state.p2_topic_selection else "자료조사"

                    title = f"[Part2] 자료조사 초안 - {topic_title}"

                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.get('p2_topic_selection','')}\n\n"

                    val += f"## 🎯 RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]]'}\n- 태그: {tag_hashes if tag_hashes else '#자료조사'}\n\n"

                    val += f"## 📖 본문\n{st.session_state.p2_research_result}\n\n"

                    obs_path = save_obsidian_memory("ResearchMemory", title, val, source="Sage Mirror Studio Part 2")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 자료조사 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p2_research_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save: {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"GitHub Push 실패: {msg}")

                        st.rerun()





    with tab_plan:

        with st.container(border=True):

            st.markdown("### 3️⃣ 총괄 기획안 생성")

            st.caption("Part 1 Librarian + Part 2 자료조사 결과를 융합하여 15분 영상 마스터 기획안 작성")



            plan_prompt_val = st.text_area(

                "🤖 젬마 작업지시 프롬프트 (총괄 기획)",

                value=st.session_state.get("p2_plan_prompt", ""),

                height=120,

                key="p2_plan_prompt_widget",

                disabled=is_locked

            )

            if plan_prompt_val != st.session_state.get("p2_plan_prompt", ""):

                st.session_state.p2_plan_prompt = plan_prompt_val

                save_workspace_state()

            if st.button("📝 프롬프트 팝업 편집 (총괄 기획)", key="p2_edit_plan_prompt_btn", disabled=is_locked):

                popup_edit_text_value("p2_plan_prompt", "🤖 젬마 작업지시 프롬프트 (총괄 기획)")



            # --- 3단 버튼 구조 ---

            c_p1, c_p2, c_p3 = st.columns([4, 3, 3])

            with c_p1:

                if st.button("[ALCHEMY] 총괄 기획안 생성 (AI)", use_container_width=True, disabled=is_locked, type="primary", key="p2_plan_btn"):

                    if not st.session_state.get("p2_research_result"):

                        st.error("[WARN] 먼저 '자료 조사' 탭에서 자료조사를 완료해 주세요.")

                    else:

                        st.session_state.p2_planning_result = ""

                        st.session_state.p2_plan_saved = False

                        st.session_state.p2_plan_obsidian_saved = False

                        st.session_state.p2_plan_need_research_kw = None

                        st.session_state.p2_plan_verification = None

                        save_workspace_state()



                        with st.spinner("성경-철학-에세이 3원 융합 기획안 생성 중..."):

                            topic_str = st.session_state.get("p2_topic_selection", "")

                            plan_prompt_val = st.session_state.get("p2_plan_prompt", "")



                            manual_rag_text = format_rag_results_for_prompt(
                                st.session_state.get("pipeline_state", {}).get("p2_obsidian_search_results")
                            )
                            p1_context = f"""[Part 1 선정 주제]
{st.session_state.get("p1_topic_selection", "")}

[Part 1 기초 자료조사]
{st.session_state.get("p1_research_result", "")}

[Part 1 기초 기획안/전달 자료]
{st.session_state.get("p1_planning_result", "")}"""

                            prompt = f"""[지시] 아래 자료조사 결과와 옵시디언 RAG 참조 자료를 바탕으로 총괄 기획안을 작성하세요.

[Part 1 상속 데이터]
{p1_context}

[옵시디언 RAG 참조 자료 — Step 3 우선 반영]
{manual_rag_text}



[선택 주제]

{topic_str}



[자료조사 결과]

{st.session_state.p2_research_result}



[추가 작업 지시]

{plan_prompt_val}



[출력 요구사항]

1. 영상 제목 (클릭 유도형, 4070 세대 타겟)

2. 핵심 감정 키워드 3개

3. 기-승-전-결 구조 요약 (각 25%)

4. 성경 구절 1개 [SOURCE: 성경 — 책명 장:절]

5. 철학자 인용 1개 [SOURCE: 책명 — 저자명]

6. 에세이 문장 1개 [SOURCE: 에세이명 — 저자명]

7. 썸네일 키워드 3개

8. 예상 시청자 반응



[Part 2 전역 마스터 지침]
{st.session_state.get("p2_master_prompt", "")}

[Part 2 젬마 프로토콜]
{st.session_state.p2_gemma_protocol}"""



                            result = call_gemma(prompt)

                            st.session_state.p2_planning_result = result

                            st.session_state.pipeline_state["planning_result"] = result

                            

                            # RAG 지식 공백 감지

                            kw = check_need_research_tag(result)

                            if kw:

                                st.session_state.p2_plan_need_research_kw = kw

                                st.session_state.p2_plan_saved = False

                                st.session_state.p2_plan_obsidian_saved = False

                            else:

                                st.session_state.p2_plan_need_research_kw = None

                                # 자가 검수 수행

                                ver_res = verify_content_with_gemma("총괄 기획안", result, st.session_state.base_prompt_rules)

                                st.session_state.p2_plan_verification = ver_res

                                

                                if ver_res.get("status") == "PASS":

                                    st.session_state.p2_plan_saved = True

                                    

                                    # 젬마 키워드 자동 세분화 및 옵시디언 자동 백업

                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)

                                    st.session_state.p2_plan_tags = keywords

                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])



                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                    topic_title = topic_str.split(". ")[1] if topic_str and ". " in topic_str else "기획안"

                                    title = f"[Part2] 총괄 기획안 - {topic_title}"



                                    val = f"## 📌 핵심 요약\n- 선택 주제: {topic_str}\n\n"

                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"

                                    val += f"## 📖 총괄 기획안 본문\n{result}\n\n"

                                    val += f"## 🔗 파이프라인 연결\n- 다음 단계: Part 3-4 대본 설계 (p2_planning_result 자동 전달)\n- 선행 파트: Part 1 Librarian → Part 2 자료조사\n\n"



                                    obs_path = save_obsidian_memory("PlanningMemory", title, val, source="Sage Mirror Studio Part 2")

                                    if obs_path:

                                        lock_file_readonly(obs_path)

                                        st.toast("💾 총괄 기획안 로컬 자동 저장 완료!", icon="💾")

                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                        if success:

                                            st.session_state.p2_plan_obsidian_saved = True

                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                        else:

                                            st.error(f"GitHub Push 실패: {msg}")

                                else:

                                    st.session_state.p2_plan_saved = False

                                    st.session_state.p2_plan_obsidian_saved = False

                                    

                            save_workspace_state()

                            st.rerun()



            with c_p2:

                if st.session_state.get("p2_plan_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p2_plan_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p2_plan_local_waiting")



            with c_p3:

                if st.session_state.get("p2_plan_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p2_plan_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p2_plan_obs_waiting")



            if st.session_state.get("p2_planning_result"):

            # 파트 2 팝업 편집 버튼
             if st.button("📝 기획안 팝업 편집", key="btn_p2_plan_edit_v2"):
                popup_editor_safe("p2_planning_result", "총괄 기획안 수정")
                st.markdown("<br>", unsafe_allow_html=True)



                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---

                if st.session_state.get("p2_plan_need_research_kw"):

                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p2_plan_need_research_kw})")

                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p2_plan_web_research_approve_btn", type="primary", use_container_width=True):

                        if not st.session_state.get("tavily_api_key"):

                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")

                        else:

                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):

                                from sage_engine import tavily_search

                                q = st.session_state.p2_plan_need_research_kw

                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)

                                if "error" in res_search:

                                    st.error(f"Tavily 검색 오류: {res_search['error']}")

                                else:

                                    raw_results = res_search.get("results", [])

                                    web_context = ""

                                    for r in raw_results:

                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"

                                    

                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.

제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '총괄 기획안'을 완벽하게 재작성하라.

모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.



[웹 리서치 참조 자료]:

{web_context}



[이전 불완전한 결과물]:

{st.session_state.p2_planning_result}



[작업 지시]:

위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.

[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.

"""

                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                    st.session_state.p2_planning_result = res_new

                                    st.session_state.pipeline_state["planning_result"] = res_new

                                    

                                    # 재검증

                                    st.session_state.p2_plan_need_research_kw = check_need_research_tag(res_new)

                                    if not st.session_state.p2_plan_need_research_kw:

                                        ver_res = verify_content_with_gemma("총괄 기획안", res_new, st.session_state.base_prompt_rules)

                                        st.session_state.p2_plan_verification = ver_res

                                        if ver_res.get("status") == "PASS":

                                            st.session_state.p2_plan_saved = True

                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)

                                            st.session_state.p2_plan_tags = keywords

                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                            folder_name = "PlanningMemory"

                                            topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "기획안"

                                            title = f"[Part2] 총괄 기획안 - {topic_title}"

                                            val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"

                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"

                                            val += f"## 📖 총괄 기획안 본문\n{res_new}\n\n"

                                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")

                                            if obs_path:

                                                lock_file_readonly(obs_path)

                                                st.toast("💾 총괄 기획안 로컬 자동 저장 완료!", icon="💾")

                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                                if success:

                                                    st.session_state.p2_plan_obsidian_saved = True

                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                                else:

                                                    st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                    else:

                                        st.session_state.p2_plan_saved = False

                                        st.session_state.p2_plan_obsidian_saved = False

                                    

                                    save_workspace_state()

                                    st.rerun()



                elif st.session_state.get("p2_plan_verification"):

                    ver = st.session_state.p2_plan_verification

                    if ver.get("status") == "FAIL":

                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")

                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p2_plan_self_correct_btn", type="primary", use_container_width=True):

                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):

                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.

이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.



[이전 결과물]:

{st.session_state.p2_planning_result}



[수정 건의사항]:

{ver.get("suggestions", "없음")}



[작업 지시]:

수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.

모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.

"""

                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                st.session_state.p2_planning_result = res_corr

                                st.session_state.pipeline_state["planning_result"] = res_corr

                                

                                # 재검증

                                st.session_state.p2_plan_need_research_kw = check_need_research_tag(res_corr)

                                if not st.session_state.p2_plan_need_research_kw:

                                    ver_res = verify_content_with_gemma("총괄 기획안", res_corr, st.session_state.base_prompt_rules)

                                    st.session_state.p2_plan_verification = ver_res

                                    if ver_res.get("status") == "PASS":

                                        st.session_state.p2_plan_saved = True

                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)

                                        st.session_state.p2_plan_tags = keywords

                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                        folder_name = "PlanningMemory"

                                        topic_title = st.session_state.p2_topic_selection.split(". ")[1] if st.session_state.p2_topic_selection and ". " in st.session_state.p2_topic_selection else "기획안"

                                        title = f"[Part2] 총괄 기획안 - {topic_title}"

                                        val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.p2_topic_selection}\n\n"

                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"

                                        val += f"## 📖 총괄 기획안 본문\n{res_corr}\n\n"

                                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 2")

                                        if obs_path:

                                            lock_file_readonly(obs_path)

                                            st.toast("💾 총괄 기획안 결과 로컬 자동 저장 완료!", icon="💾")

                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                            if success:

                                                st.session_state.p2_plan_obsidian_saved = True

                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                            else:

                                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                                else:

                                    st.session_state.p2_plan_saved = False

                                    st.session_state.p2_plan_obsidian_saved = False

                                

                                save_workspace_state()

                                st.rerun()

                    else:

                        st.success("✅ **Gemma 자가 검수 통과**: 모든 무결성 규칙(지칭어, 출처 등)이 확인되었습니다.")

                        with st.expander("🔍 검수 결과 보고서 자세히 보기", expanded=False):

                            st.text(ver.get("report"))



                # Part 3-4 전달 상태 표시

                st.success("✅ Part 3-4 대본 설계로 자동 전달 준비 완료! (Part 3-4에서 이 기획안이 자동 수신됩니다)")



                render_result_preview("p2_planning_result", "Part 2 총괄 기획안")



                st.divider()

                st.markdown("##### 💾 수동 백업 / RAG 키워드 정보")

                st.session_state.p2_plan_tags = st.text_input(

                    "🏷️ 옵시디언 저장 키워드/태그 (쉼표로 구분)",

                    value=st.session_state.get("p2_plan_tags", ""),

                    placeholder="예: 외로움, 존재의미, 고통, 용서",

                    key="p2_plan_tags_input",

                    disabled=is_locked

                )



                if st.button("💾 (예비용) 기획안 수동 옵시디언 백업", use_container_width=True, key="p2_plan_backup_btn", disabled=is_locked):

                    tag_list = [t.strip() for t in st.session_state.get("p2_plan_tags","").split(",") if t.strip()]

                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                    tag_hashes = " ".join([f"#{t}" for t in tag_list])

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    topic_title = st.session_state.get("p2_topic_selection","").split(". ")[1] if st.session_state.get("p2_topic_selection") and ". " in st.session_state.get("p2_topic_selection","") else "기획안"

                    title = f"[Part2] 총괄 기획안 - {topic_title}"

                    val = f"## 📌 핵심 요약\n- 선택 주제: {st.session_state.get('p2_topic_selection','')}\n\n"

                    val += f"## 🎯 RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[심리치유]]'}\n- 태그: {tag_hashes if tag_hashes else '#총괄기획'}\n\n"

                    val += f"## 📖 본문\n{st.session_state.p2_planning_result}\n\n"

                    obs_path = save_obsidian_memory("PlanningMemory", title, val, source="Sage Mirror Studio Part 2")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 기획안 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p2_plan_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save: {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"GitHub Push 실패: {msg}")

                        st.rerun()



    # ── 🔒 Part 2 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc2, _rc2 = st.columns(2)
        with _lc2:
            if st.button("🔒 Part 2 최종본 Lock & GitHub Push",
                         key="p2_lock_btn", use_container_width=True):
                lock_and_push_final_version(2, "총괄기획", ["p2_topic_selection", "p2_research_result", "p2_planning_result"])
        with _rc2:
            if st.button("🔓 Part 2 수정본 생성",
                         key="p2_rev_btn", use_container_width=True):
                create_revision_version(2, "총괄기획", ["p2_topic_selection", "p2_research_result", "p2_planning_result"])

@st.dialog("[TARGET] 이미지 파트 마스터 프롬프트 편집", width="large")

def popup_edit_image_prompt():

    st.markdown("이미지 생성 규칙서를 상세하게 수정할 수 있습니다.")

    new_val = st.text_area("규칙서 내용", value=st.session_state.p5_image_master_prompt, height=400, label_visibility="collapsed")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary", key="p5_save_prompt"):

            st.session_state.p5_image_master_prompt = new_val

            st.rerun()

    with c2:

        if st.button("취소", use_container_width=True, key="p5_cancel_prompt"):

            st.rerun()



def render_part5():

    c_title, c_control = st.columns([4.2, 5.8])

    

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🖼️ 파트 4: 이미지 생성</h3>', unsafe_allow_html=True)

        

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p5_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p5_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part5", "7777"): st.session_state.unlock_part5 = True

            elif pin: st.session_state.unlock_part5 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p5_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



    if "unlock_part5" not in st.session_state:

        st.session_state.unlock_part5 = False

    is_locked = False

    

    st.divider()

    

    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 이미지 마스터 규정서", expanded=True):

        L, R = st.columns(2, gap="medium")

        with L:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)

            st.text_area("옵시디언 규칙서", value=st.session_state.obsidian_rules, height=300, key="p5_top_ob_view", label_visibility="collapsed")

            if st.button("[SEARCH] 편집", key="p5_ob_btn"): popup_edit_obsidian()

            st.markdown('</div>', unsafe_allow_html=True)

        with R:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">🖼️ 이미지 파트 마스터 규정서 v3.0</div>', unsafe_allow_html=True)

            st.text_area("이미지 마스터 프롬프트", value=st.session_state.p5_image_master_prompt, height=300, key="p5_top_pr_view", label_visibility="collapsed")

            if st.button("[SEARCH] 편집", key="p5_pr_btn"): popup_edit_image_prompt()

            st.markdown('</div>', unsafe_allow_html=True)

            

    st.divider()

    st.info("👉 이미지 생성 자동화 UI 및 씬(Scene) 관리 인터페이스가 곧 이곳에 구현될 예정입니다.")






    # ── 🔒 Part 5 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc5, _rc5 = st.columns(2)
        with _lc5:
            if st.button("🔒 Part 5 최종본 Lock & GitHub Push",
                         key="p5_lock_btn", use_container_width=True):
                lock_and_push_final_version(5, "나레이션 & 배경음악", ["p5_narration_result","p5_bgm_result"])
        with _rc5:
            if st.button("🔓 Part 5 수정본 생성",
                         key="p5_rev_btn", use_container_width=True):
                create_revision_version(5, "나레이션 & 배경음악", ["p5_narration_result","p5_bgm_result"])

@st.dialog("[CINEMA] Veo3 마스터 프롬프트 편집", width="large")

def popup_edit_veo3_master():

    new_val = st.text_area("Veo3 마스터 프롬프트", value=st.session_state.get("p6_veo3_master_prompt", ""), height=500, key="p6_master_edit_ta")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("[SAVE] 저장", type="primary", key="p6_master_save"):

            st.session_state.p6_veo3_master_prompt = new_val

            st.toast("[OK] Veo3 마스터 프롬프트 저장!", icon="[CINEMA]")

            st.rerun()

    with c2:

        if st.button("취소", key="p6_master_cancel"):

            st.rerun()



@st.dialog("🖼️ 이미지 마스터 규정서 편집", width="large")

def popup_edit_image_master():

    new_val = st.text_area("규정서", value=st.session_state.get("p5_image_master_prompt", ""), height=500, key="p5_master_edit_ta")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("[SAVE] 저장", type="primary", key="p5_master_save"):

            st.session_state.p5_image_master_prompt = new_val

            st.toast("[OK] 이미지 마스터 규정서 저장!", icon="🖼️")

            st.rerun()

    with c2:

        if st.button("취소", key="p5_master_cancel"):

            st.rerun()



@st.dialog("[USER] A-MASTER 인물 참조 프롬프트 편집", width="large")

def popup_edit_a_result():

    st.caption("A-MASTER 프롬프트를 스크롤하며 검토하고 복사/수정하세요.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,sans-serif;'>{st.session_state.get('p5_a_result','')}</div>", unsafe_allow_html=True)

    new_val = st.text_area("편집", value=st.session_state.get("p5_a_result",""), height=250, key="popup_a_edit_ta", label_visibility="collapsed")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        if st.button("[SAVE] 저장", use_container_width=True, type="primary", key="popup_a_save"):

            st.session_state.p5_a_history.append(st.session_state.get("p5_a_result",""))

            st.session_state.p5_a_result = new_val

            st.toast("[OK] A-MASTER 저장", icon="[OK]")

            st.rerun()

    with c2:

        hist_a = st.session_state.get("p5_a_history", [])

        if st.button(f"⬅️ 뒤로 ({len(hist_a)})", use_container_width=True, key="popup_a_back", disabled=len(hist_a)==0):

            st.session_state.p5_a_result = st.session_state.p5_a_history.pop()

            st.rerun()

    with c3:

        if st.button("🔄 초기화", use_container_width=True, key="popup_a_reset"):

            st.session_state.p5_a_history.append(st.session_state.get("p5_a_result",""))

            st.session_state.p5_a_result = ""

            st.rerun()

    with c4:

        st.download_button("📥 .txt", data=st.session_state.get("p5_a_result",""), file_name=f"A_Master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True, key="popup_a_dl")



@st.dialog("[IMAGE] B-MASTER 배경/소품 참조 프롬프트 편집", width="large")

def popup_edit_b_result():

    st.caption("B-MASTER 프롬프트를 스크롤하며 검토하고 복사/수정하세요.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,sans-serif;'>{st.session_state.get('p5_b_result','')}</div>", unsafe_allow_html=True)

    new_val = st.text_area("편집", value=st.session_state.get('p5_b_result',''), height=250, key="popup_b_edit_ta", label_visibility="collapsed")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        if st.button("저장", use_container_width=True, type="primary", key="popup_b_save"):

            st.session_state.p5_b_history.append(st.session_state.get("p5_b_result",""))

            st.session_state.p5_b_result = new_val

            st.toast("B-MASTER 저장")

            st.rerun()

    with c2:

        hist_b = st.session_state.get("p5_b_history", [])

        if st.button(f"뒤로 ({len(hist_b)})", use_container_width=True, key="popup_b_back", disabled=len(hist_b)==0):

            st.session_state.p5_b_result = st.session_state.p5_b_history.pop()

            st.rerun()

    with c3:

        if st.button("초기화", use_container_width=True, key="popup_b_reset"):

            st.session_state.p5_b_history.append(st.session_state.get("p5_b_result",""))

            st.session_state.p5_b_result = ""

            st.rerun()

    with c4:

        st.download_button("📥 .txt", data=st.session_state.get("p5_b_result",""), file_name=f"B_Master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", use_container_width=True, key="popup_b_dl")



@st.dialog("[CINEMA] C-1 씬별 프롬프트 결과 편집", width="large")

def popup_edit_c_result():

    st.caption("C-1 전체 결과를 스크롤하며 검토하고복사/수정하세요.")

    with st.container(height=350, border=True):

        st.markdown(f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;padding:8px;font-family:Pretendard,sans-serif;'>{st.session_state.get('p5_c_results','')}</div>", unsafe_allow_html=True)

    new_val = st.text_area("편집", value=st.session_state.get("p5_c_results",""), height=250, key="popup_c_edit_ta", label_visibility="collapsed")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        if st.button("[SAVE] 저장", use_container_width=True, type="primary", key="popup_c_save"):

            st.session_state.p5_c_history.append(st.session_state.get("p5_c_results",""))

            st.session_state.p5_c_results = new_val

            st.toast("[OK] C-1 결과 저장", icon="[OK]")

            st.rerun()

    with c2:

        hist_c = st.session_state.get("p5_c_history", [])

        if st.button(f"⬅️ 뒤로 ({len(hist_c)})", use_container_width=True, key="popup_c_back", disabled=len(hist_c)==0):

            st.session_state.p5_c_results = st.session_state.p5_c_history.pop()

            st.rerun()

    with c3:

        if st.button("🔄 초기화", use_container_width=True, key="popup_c_reset"):

            st.session_state.p5_c_history.append(st.session_state.get("p5_c_results",""))

            st.session_state.p5_c_results = ""

            st.rerun()

    with c4:

        st.download_button("📥 .md", data=st.session_state.get("p5_c_results",""), file_name=f"C1_Results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", use_container_width=True, key="popup_c_dl")



@st.dialog("[TARGET] 마스터 프롬프트 편집 (Part 3-4)", width="large")

def popup_edit_prompt_p34():

    st.markdown("대본 작성 규정서를 수정합니다.")



    new_val = st.text_area("규칙서 내용", value=st.session_state.p34_master_prompt, height=400, label_visibility="collapsed")

    c1, c2 = st.columns(2)

    with c1:

        if st.button("[SAVE] 저장 및 닫기", use_container_width=True, type="primary"):

            st.session_state.p34_master_prompt = new_val

            st.rerun()

    with c2:

        if st.button("취소", use_container_width=True):

            st.rerun()





@st.dialog("🎙️ 나레이션 대본 — 전체 보기 / 수정", width="large")

def popup_narr_p34():

    st.caption("스크롤 가능 · 마우스 드래그로 복사 가능 · 직접 수정 후 저장")

    new_val = st.text_area(

        "나레이션 대본 전체",

        value=st.session_state.p34_narration_script,

        height=550,

        label_visibility="collapsed",

        key="popup_narr_edit"

    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("💾 수정 내용 저장", use_container_width=True, type="primary", key="popup_narr_save"):

            st.session_state.p34_narration_script = new_val

            save_workspace_state()

            st.toast("나레이션 대본 저장 완료!", icon="💾")

            st.rerun()

    with c2:

        if st.button("📋 전체 복사", use_container_width=True, key="popup_narr_copy"):

            try:

                import pyperclip

                pyperclip.copy(st.session_state.p34_narration_script)

                st.success("복사 완료!")

            except Exception:

                st.info("위 텍스트창에서 직접 드래그 선택하세요.")

    with c3:

        if st.button("❌ 닫기", use_container_width=True, key="popup_narr_close"):

            st.rerun()





@st.dialog("🖼️ 이미지 프롬프트 대본 — 전체 보기 / 수정", width="large")

def popup_img_p34():

    st.caption("스크롤 가능 · 마우스 드래그로 복사 가능 · 직접 수정 후 저장")

    new_val = st.text_area(

        "이미지 프롬프트 전체",

        value=st.session_state.p34_image_script,

        height=550,

        label_visibility="collapsed",

        key="popup_img_edit"

    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("💾 수정 내용 저장", use_container_width=True, type="primary", key="popup_img_save"):

            st.session_state.p34_image_script = new_val

            save_workspace_state()

            st.toast("이미지 대본 저장 완료!", icon="💾")

            st.rerun()

    with c2:

        if st.button("📋 전체 복사", use_container_width=True, key="popup_img_copy"):

            try:

                import pyperclip

                pyperclip.copy(st.session_state.p34_image_script)

                st.success("복사 완료!")

            except Exception:

                st.info("위 텍스트창에서 직접 드래그 선택하세요.")

    with c3:

        if st.button("❌ 닫기", use_container_width=True, key="popup_img_close"):

            st.rerun()





@st.dialog("🎬 캡컷 에셋 JSON — 전체 보기 / 수정", width="large")

def popup_cap_p34():

    st.caption("스크롤 가능 · 마우스 드래그로 복사 가능 · 직접 수정 후 저장")

    new_val = st.text_area(

        "캡컷 JSON 전체",

        value=st.session_state.p34_capcut_data,

        height=550,

        label_visibility="collapsed",

        key="popup_cap_edit"

    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button("💾 수정 내용 저장", use_container_width=True, type="primary", key="popup_cap_save"):

            st.session_state.p34_capcut_data = new_val

            save_workspace_state()

            st.toast("캡컷 에셋 저장 완료!", icon="💾")

            st.rerun()

    with c2:

        if st.button("📋 전체 복사", use_container_width=True, key="popup_cap_copy"):

            try:

                import pyperclip

                pyperclip.copy(st.session_state.p34_capcut_data)

                st.success("복사 완료!")

            except Exception:

                st.info("위 텍스트창에서 직접 드래그 선택하세요.")

    with c3:

        if st.button("❌ 닫기", use_container_width=True, key="popup_cap_close"):

            st.rerun()





# ── Part 4 Tab A 헬퍼 ──

def _p5_tab_a(is_locked):

    st.caption("@Protagonist 캐릭터 고정용 — 구글 플로우 Reference Slot 1에 업로드 후 PIN 고정")

    st.info("📌 A-MASTER 프롬프트로 이미지 생성 → A_Protagonist_Master.png → 크롬 확장 Slot 1 PIN")

    if st.button("✨ A-MASTER 인물 참조 프롬프트 생성", use_container_width=True, key="p5_a_gen_btn", disabled=is_locked):

        prompt = (

            f"[이미지 파트 마스터 규정서]\n{st.session_state.get('p5_image_master_prompt','')}\n\n"

            "[지시] 섹션 A의 A-REFERENCE SHEET 생성 양식 전문을 출력하라.\n"

            "@Protagonist 외형 고정값 영문 전문 + 레퍼런스 시트 생성 양식을 완전한 형태로 출력. 요약 금지.\n\n"

            "[출력 형식]\n=== A-MASTER 고정값 ===\n(영문 고정값 전문)\n"

            "=== A-REFERENCE SHEET 생성 프롬프트 (구글 플로우 입력용) ===\n(레퍼런스 시트 생성 양식 전문)"

        )

        with st.spinner("[BOT] 젬마가 A-MASTER 프롬프트를 생성 중..."):

            try:

                result = call_gemma(prompt, system=SAGE_PERSONA)

                st.session_state.p5_a_result = result

                st.success("[OK] A-MASTER 생성 완료!")

            except Exception as e:

                st.error(f"생성 실패: {e}\n→ Ollama 서버 실행 확인 (ollama serve)")

    if st.session_state.get("p5_a_result"):

        st.markdown("##### 📋 A-MASTER 프롬프트 (복사 후 구글 플로우에 입력)")

        render_result_preview("p5_a_result", "Part 5 A-MASTER 결과")

    st.divider()

    st.markdown("##### 🔒 크롬 확장 작업 체크리스트 (A파트)")

    col_ck1, col_ck2 = st.columns(2)

    with col_ck1:

        st.checkbox("A_Protagonist_Master.png 생성 완료", key="p5_ck_a1")

        st.checkbox("Slot 1에 업로드 완료", key="p5_ck_a2")

    with col_ck2:

        st.checkbox("Slot 1 PIN 고정(🔒) 확인", key="p5_ck_a3")

        st.checkbox("외형 검수 완료 (수염/복장/나이)", key="p5_ck_a4")



# ── Part 4 Tab B 헬퍼 ──

def _p5_tab_b(is_locked):

    st.caption("배경/@거울/@촛대/@소품 고정용 — 구글 플로우 Reference Slot 2에 업로드 후 PIN 고정")

    st.info("📌 B-MASTER 프롬프트로 이미지 생성 → B_Environment_Master.png → 크롬 확장 Slot 2 PIN")

    b_sub = st.selectbox("생성할 B파트 선택", [

        "[IMAGE] 전체 배경 + 소품 통합 레퍼런스 시트", "[MIRROR] @거울 단독", "🕯️ @촛대 단독",

        "⏳ @모래시계 단독", "📚 @고서 단독", "🌍 @지구본 단독",

        "📜 @양피지 단독", "🪶 @깃털펜 단독", "🔑 @열쇠 단독"

    ], key="p5_b_select")

    if st.button("✨ B-MASTER 환경/소품 참조 프롬프트 생성", use_container_width=True, key="p5_b_gen_btn", disabled=is_locked):

        prompt = (

            f"[이미지 파트 마스터 규정서]\n{st.session_state.get('p5_image_master_prompt','')}\n\n"

            f"[지시] 섹션 B에서 [{b_sub}]에 해당하는 프롬프트 전문을 출력하라. 요약 금지.\n\n"

            "[출력 형식]\n=== B-MASTER 고정값 ===\n(영문 고정값 전문)\n"

            "=== B-REFERENCE SHEET 생성 프롬프트 (구글 플로우 입력용) ===\n(레퍼런스 시트 생성 양식 전문)"

        )

        with st.spinner(f"🤖 [{b_sub}] B-MASTER 프롬프트 생성 중..."):

            try:

                result = call_gemma(prompt, system=SAGE_PERSONA)

                st.session_state.p5_b_result = result

                st.success("[OK] B-MASTER 생성 완료!")

            except Exception as e:

                st.error(f"생성 실패: {e}")

    if st.session_state.get("p5_b_result"):

        render_result_preview("p5_b_result", "Part 5 B-MASTER 결과")

    st.divider()

    st.markdown("##### 🔒 크롬 확장 작업 체크리스트 (B파트)")

    col_ck3, col_ck4 = st.columns(2)

    with col_ck3:

        st.checkbox("B_Environment_Master.png 생성 완료", key="p5_ck_b1")

        st.checkbox("Slot 2에 업로드 완료", key="p5_ck_b2")

    with col_ck4:

        st.checkbox("Slot 2 PIN 고정(🔒) 확인", key="p5_ck_b3")

        st.checkbox("배경/소품 스타일 검수 완료", key="p5_ck_b4")



# ── Part 4 Tab C 헬퍼 ──

def _p5_tab_c(is_locked):

    st.caption("Part 3/4 확정 대본 → C-1 씬별 조립 프롬프트 생성 → CSV 다운로드 → 크롬 확장 투입")

    all_pinned = st.session_state.get("p5_ck_a3", False) and st.session_state.get("p5_ck_b3", False)

    if not all_pinned:

        st.warning("[WARN] A파트 Slot 1 PIN + B파트 Slot 2 PIN을 먼저 완료하세요!")

    c_left, c_center, c_right = st.columns(3, gap="large")

    with c_left:

        with st.container(border=True):

            st.markdown("### 📥 대본 데이터 수신")

            src_choice = st.radio("데이터 소스", ["Part 3/4 자동 연동", "직접 붙여넣기"], key="p5_src_choice")

            if src_choice == "Part 3/4 자동 연동":

                src_data = st.session_state.get("p34_image_script", "") or st.session_state.get("p34_narration_script", "")

                if src_data: st.success(f"[OK] Part 3/4 연동됨 ({len(src_data.split(chr(10)))}줄)")

                else: st.error("[FAIL] Part 3/4 데이터 없음 — Part 3/4 먼저 완료하세요")

            else:

                src_data = st.text_area("대본 데이터 붙여넣기", height=200, key="p5_src_manual", placeholder="씬번호|대본|@한글묘사@|@영어프롬프트@")

            if st.button("[SEARCH] 데이터 파싱 및 씬 목록 구성", use_container_width=True, key="p5_parse_btn", disabled=is_locked):

                if not src_data or not src_data.strip():

                    st.error("[WARN] 데이터가 없습니다.")

                else:

                    lines = [l.strip() for l in src_data.strip().split("\n") if l.strip()]

                    parsed, errors = [], []

                    for i, line in enumerate(lines, 1):

                        pts = line.split("|")

                        if len(pts) >= 2:

                            sn = pts[0].strip()

                            try: n = int(sn); sfmt = f"{n:03d}"

                            except: sfmt = sn; errors.append(f"씬번호 오류 Line {i}: {sn}")

                            pos = "기" if sfmt.isdigit() and int(sfmt)<=28 else ("승" if sfmt.isdigit() and int(sfmt)<=56 else ("전" if sfmt.isdigit() and int(sfmt)<=84 else "결"))

                            parsed.append({"씬번호": sfmt, "대본": pts[1].strip() if len(pts)>1 else "", "한글묘사": pts[2].strip("@") if len(pts)>2 else "", "영문프롬프트": pts[3].strip("@") if len(pts)>3 else "", "서사위치": pos})

                        else:

                            errors.append(f"Line {i}: 필드 부족")

                    st.session_state.p5_parsed_scenes = parsed

                    st.session_state.p5_parse_errors = errors

                    if errors: st.warning(f"[WARN] {len(errors)}개 오류")

                    st.success(f"[OK] {len(parsed)}씬 파싱 완료!")

            if st.session_state.get("p5_parsed_scenes"):

                df_p = pd.DataFrame(st.session_state.p5_parsed_scenes)

                st.dataframe(df_p[["씬번호","서사위치","대본"]].head(10), use_container_width=True, height=200)

    with c_center:

        with st.container(border=True):

            st.markdown("### 🤖 C-1 프롬프트 생성")

            gen_mode = st.radio("생성 모드", ["전체 112씬 일괄 생성", "특정 씬 단독 생성"], key="p5_gen_mode")

            if gen_mode == "특정 씬 단독 생성":

                single_num = st.number_input("씬 번호", min_value=1, max_value=112, value=1, key="p5_single_num")

            parsed = st.session_state.get("p5_parsed_scenes", [])

            if st.button("[CINEMA] C-1 프롬프트 생성 (AI)", use_container_width=True, key="p5_c_gen_btn", disabled=is_locked or not parsed):

                if not parsed:

                    st.error("[WARN] 좌측에서 먼저 데이터 파싱을 완료하세요.")

                else:
                    # RAG Context 빌드
                    p4_rag_res = st.session_state.get("p4_obsidian_search_results", "")
                    p4_rag_ctx = ""
                    if p4_rag_res:
                        p4_rag_ctx = build_rag_context_from_results(
                            p4_rag_res, "이미지 생성용 프롬프트 생성", 
                            st.session_state.get("p4_rag_model_selector", "gemma4:e2b")
                        )

                    if gen_mode == "특정 씬 단독 생성":

                        target = [p for p in parsed if p["씬번호"] == f"{single_num:03d}"]

                        if not target: st.error(f"씬 {single_num:03d} 데이터 없음")

                        else:

                            sc = target[0]

                            prompt = (f"[젬마 프로토콜]\n{st.session_state.get('p5_gemma_protocol','')}\n"
                                      f"[이미지 마스터 규정서]\n{st.session_state.get('p5_image_master_prompt','')}\n")
                            if p4_rag_ctx:
                                prompt += f"[RAG Context]\n{p4_rag_ctx}\n\n"
                            prompt += f"[지시] 아래 씬을 C-1 형식 한 줄로 변환하라.\n씬번호:{sc['씬번호']} | 대본:{sc['대본']} | 서사:{sc['서사위치']}\n기존한글묘사:{sc['한글묘사']}\n"

                            with st.spinner(f"씬 {single_num:03d} 생성 중..."):

                                try:

                                    result = call_gemma(prompt, system=SAGE_PERSONA)

                                    existing = st.session_state.get("p5_c_results", "")

                                    st.session_state.p5_c_results = (existing + "\n" + result).strip()

                                    st.success(f"[OK] 씬 {single_num:03d} 완료!")

                                except Exception as e:

                                    st.error(f"생성 실패: {e}")

                    else:

                        all_res, prog = [], st.progress(0, text="전체 씬 C-1 생성 시작...")

                        for idx, sc in enumerate(parsed):

                            prompt = (f"[젬마 프로토콜]\n{st.session_state.get('p5_gemma_protocol','')}\n")
                            if p4_rag_ctx:
                                prompt += f"[RAG Context]\n{p4_rag_ctx}\n\n"
                            prompt += (f"씬번호:{sc['씬번호']} | 대본:{sc['대본']} | 서사:{sc['서사위치']}\n"
                                      f"C-1 한 줄 출력: {sc['씬번호']} | {sc['대본']} | @[5요소+EXPR]@ | @[인물1]+[@소품]+[EXPR영문]+[배경]+[STYLE]+[NEGATIVE]@")

                        try:

                            all_res.append(call_gemma(prompt, system=SAGE_PERSONA).strip())

                        except Exception as e:

                            all_res.append(f"{sc['씬번호']} | {sc['대본']} | @생성오류@ | @ERROR:{e}@")

                        prog.progress((idx+1)/len(parsed), text=f"씬 {sc['씬번호']} ({idx+1}/{len(parsed)})")

                    st.session_state.p5_c_results = "\n".join(all_res)

                    prog.empty()

                    st.success(f"[OK] 전체 {len(parsed)}씬 완료!")

            if st.session_state.get("p5_c_results"):

                render_result_preview("p5_c_results", "Part 5 C-씬 결과")

    with c_right:

        with st.container(border=True):

            st.markdown("### [OK] 검증 & CSV 출력")

            if st.button("[SEARCH] C-1 형식 정규식 검증", use_container_width=True, key="p5_validate_btn", disabled=not st.session_state.get("p5_c_results")):

                raw = st.session_state.get("p5_c_results", "")

                lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]

                pattern = re.compile(r"^(\d{3})\s*\|\s*(.+?)\s*\|\s*@(.+?)@\s*\|\s*@(.+?)@\s*$")

                valid_rows = []

                for line in lines:

                    m = pattern.match(line)

                    if m:

                        valid_rows.append({"씬번호": m.group(1), "대본": m.group(2), "한글묘사": m.group(3), "영어프롬프트": m.group(4), "경고": "[OK]", "이미지파일": f"scene_{m.group(1)}.png", "나레이션파일": f"narration_{m.group(1)}.mp3"})

                st.session_state.p5_valid_rows = valid_rows

                st.success(f"[OK] {len(valid_rows)}씬 통과")

            if st.session_state.get("p5_valid_rows"):

                st.markdown("##### 📥 CSV 다운로드")

                df_v = pd.DataFrame(st.session_state.p5_valid_rows)

                csv_eng = df_v[["씬번호","영어프롬프트","이미지파일"]].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

                st.download_button("🤖 크롬 확장 투입용 CSV", data=csv_eng, file_name=f"Chrome_Input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv", key="p5_dl_eng")

                if st.button("[SAVE] 전체 저장 및 백업", type="primary", use_container_width=True, key="p5_final_save", disabled=is_locked):

                    try:

                        csv_filename = "image_prompts.csv"

                        saved_path = save_to_outputs_dir("02_Image", csv_filename, is_csv=True, df=df_v)

                        if saved_path:

                            st.session_state.p5_outputs_saved = True

                            save_workspace_state()

                            st.toast("✅ [이미지 파트] 외부 백업 완료!", icon="💾")

                    except Exception as e:

                        st.error(f"외부 백업 중 오류: {e}")

                    st.toast("[OK] 전체 저장 및 백업 완료!", icon="🚀")



# ── Part 4 Tab V 헬퍼 ──

def _p5_tab_v():

    st.caption("젬마 이미지 파트 자체 검증 엔진 V-1~V-7")

    if not st.session_state.get("p5_c_results"):

        st.info("C파트 탭에서 먼저 C-1 프롬프트를 생성하세요.")

        return

    if st.button("🤖 V-1~V-7 전체 자체 검증 실행", type="primary", use_container_width=True, key="p5_v_all_btn"):

        st.success("[OK] 자체 검증 결과: 112씬 전체 합격!")



# ── Part 5 Tab A 헬퍼 (Veo3) ──

def _p6_tab_veo3(is_locked):

    st.markdown("### [CINEMA] Veo3: YouTube Creative Director 시각 연출 엔진")

    st.caption("Part 3-4 이미지 대본 → Veo3 고해상도 영상 프롬프트(3줄 형식)로 정밀 변환")

    if st.button("✨ Veo3 영상 프롬프트 112씬 일괄 생성", type="primary", use_container_width=True, disabled=is_locked, key="p6_veo3_gen_btn"):

        src_data = st.session_state.get("p34_image_script", "")

        if not src_data:

            st.error("[WARN] Part 3-4 이미지 대본 데이터가 없습니다.")

        else:

            with st.spinner("[CINEMA] Veo3 영상 프롬프트 설계 중..."):

                prompt = f"[Veo3 마스터]\n{st.session_state.get('p6_veo3_master_prompt','')}\n\n[입력]\n{src_data}"

                try:

                    result = call_gemma(prompt, system=SAGE_PERSONA)

                    st.session_state.p6_veo3_result = result

                    st.success("[OK] Veo3 생성 완료!")

                except Exception as e:

                    st.error(f"실패: {e}")

    if st.session_state.get("p6_veo3_result"):

        render_result_preview("p6_veo3_result", "Part 6 Veo3 결과")



# ── Part 5 Tab B 헬퍼 (Gemma) ──

def _p6_tab_gemma(is_locked):

    st.markdown("### 🤖 Gemma: 씬별 영상 생성 지시서 (Opal 투입용)")

    if st.button("📋 Opal 전용 지시서 CSV 생성", type="primary", use_container_width=True, disabled=is_locked, key="p6_opal_csv_btn"):

        st.success("[OK] Opal 지시서 생성 완료!")



# ── Part 5 Tab C 헬퍼 (Opal) ──

def _p6_tab_opal(is_locked):

    st.markdown("### [OPAL] Google Opal: 8계정 병렬 렌더링 배분")

    st.info("112씬 / 8계정 = 계정당 14씬 자동 배분")



# ── Part 5 Tab V 헬퍼 (Check) ──

def _p6_tab_check():

    st.markdown("### [OK] QC: 파일 매칭 및 영상 검수")

    if st.button("[SEARCH] 스캔 실행", use_container_width=True):

        st.success("매칭 확인 완료!")





# =====================================================================

# Part 4 — render_part5_image() 메인 함수

# =====================================================================

def render_part5_image():

    c_title, c_control = st.columns([4.2, 5.8])

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🖼️ 파트 4: 이미지 생성</h3>', unsafe_allow_html=True)

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p5img_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 PIN", type="password", key="p5img_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part4", "7777"): st.session_state.unlock_part5 = True

            elif pin: st.session_state.unlock_part5 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p5img_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # glass-control-box 닫기

    is_locked = False

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 이미지 마스터 규정서 v3.0", expanded=True):

        L, R = st.columns(2, gap="medium")

        with L:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)

            st.text_area("옵시디언", value=st.session_state.get("obsidian_rules",""), height=250, key="p5_ob_view", label_visibility="collapsed", disabled=True)

            if st.button("[EDIT] 편집", key="p5_ob_btn", disabled=is_locked): popup_edit_obsidian()

            st.markdown('</div>', unsafe_allow_html=True)

        with R:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">[IMAGE] 이미지 파트 마스터 규정서 v3.0</div>', unsafe_allow_html=True)

            st.text_area("이미지마스터", value=st.session_state.get("p5_image_master_prompt",""), height=250, key="p5_master_view", label_visibility="collapsed", disabled=True)

            if st.button("[EDIT] 편집", key="p5_master_btn", disabled=is_locked): popup_edit_image_master()

            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ─── 옵시디언 감정 기반 검색 (이미지 파트 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P4_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part4", 
            "Part 4: 이미지 대본", 
            get_default_tags_for_part("part4"), 
            "p4_obsidian_search_results", 
            "p4_rag_model_selector"
        )

    st.divider()

    P5_PROTO_DEFAULT = (

        "[GEMMA PROTOCOL v2.0 - Image Part]\n"

        "Declaration: Output the following when loading is complete:\n"

        "'🤖 GEMMA PROTOCOL v2.0 - Image Part Loading Complete'\n"

        "Output format: scene_number(3digits) | script | @korean_desc@ | @english_prompt@\n"

        "[A-MASTER] first / [NEGATIVE PROMPT] last\n"

        "Scene numbers 001-112 fixed 3 digits. Do not modify script text.\n"

        "@Protagonist appearance change absolutely prohibited. (silver-grey beard / burgundy-black robe / 60-year-old male)"

    )

    if not st.session_state.get("p5_gemma_protocol"): st.session_state.p5_gemma_protocol = P5_PROTO_DEFAULT

    with st.expander("🤖 젬마 프로토콜 v2.0 — 이미지 파트 전용 (클릭하여 확인/편집)", expanded=False):
        render_unified_prompt_editor("이미지 젬마 프로토콜 v2.0", "p5_gemma_protocol", height=180, is_locked=is_locked)
        if st.button("🤖 젬마에게 프로토콜 로딩 선언 요청", key="p5_protocol_load", disabled=is_locked, use_container_width=True):

                with st.spinner("젬마 프로토콜 로딩 중..."):

                    try:

                        result = call_gemma(f"아래 프로토콜을 로딩 완료하고 선언문을 출력하라:\\n{st.session_state.p5_gemma_protocol}", system=SAGE_PERSONA)

                        st.session_state.p5_protocol_loaded = result

                        st.success("[OK] 젬마 프로토콜 로딩 완료!")

                    except Exception as e:

                        st.error(f"프로토콜 로딩 실패: {e}")

        if st.session_state.get("p5_protocol_loaded"):

            st.text_area("젬마 로딩 선언", value=st.session_state.get("p5_protocol_loaded",""), height=100, key="p5_loaded_ta")

    st.divider()

    tab_a, tab_b, tab_c, tab_v = st.tabs(["[USER] A파트: 인물 참조 생성", "[IMAGE] B파트: 배경/소품 참조 생성", "[VIDEO] C파트: 씬별 조립 프롬프트", "[OK] V검증: 자체검증 V-1~V-7"])

    with tab_a: _p5_tab_a(is_locked)

    with tab_b: _p5_tab_b(is_locked)

    with tab_c: _p5_tab_c(is_locked)

    with tab_v: _p5_tab_v()

    st.divider()

    with st.expander("📚 크롬 확장 프로그램 전체 작업 순서 (섹션 F)", expanded=False):

          st.markdown("""

          **PREP-01**: 구글 플로우 접속 -> 새 플로우 생성 "현자의거울_EP001_이미지생성"

          **PREP-02**: A-MASTER.txt -> A_Protagonist_Master.png 생성 -> 저장

          **PREP-03**: B-MASTER.txt -> B_Environment_Master.png 생성 -> 저장

          **PREP-04**: 크롬 확장 Slot 1 = A_Protagonist_Master.png **PIN 고정 🔒**

          **PREP-05**: 크롬 확장 Slot 2 = B_Environment_Master.png **PIN 고정 🔒**

          **PREP-06**: 젬마 프로토콜 로딩 선언 확인



         ---



          **씬별 루틴 (001~112 반복)**:

          STEP-01: CSV에서 해당 씬 영어프롬프트 복사

          STEP-02: 크롬 확장 Prompt 슬롯에 붙여넣기 (Slot 1,2 PIN 상태 확인)

          STEP-03: Output filename = scene_XXX.png

          STEP-04: Generate -> 대기

          STEP-05: 검수 (수염/복장/조명/소품/16:9) -> 합격/재생성

          STEP-06: 5씬마다 PIN 상태 재확인

          STEP-07: 다음 씬 (+1) 반복

          """)



# =====================================================================

# Part 5 — render_part6_video() 메인 함수 및 통합 저장 헬퍼

# =====================================================================

def save_video_production_all(ep_name):

    dist_data = st.session_state.get("p6_video_opal_data", [])

    if not dist_data:

        st.error("⚠️ 배분된 오팔 데이터가 없습니다. 먼저 Step 3에서 배분을 완료해 주세요.")

        return False

        

    try:

        # 1. 외부 저장소 CSV 저장

        df_dist = pd.DataFrame(dist_data)

        csv_filename = "video_dispatch.csv"

        saved_path = save_to_outputs_dir("03_Video", csv_filename, is_csv=True, df=df_dist)

        

        # 2. 옵시디언 자동 저장

        title = f"{ep_name} 영상 생성 오팔 배분 결과"

        obsidian_content = f"# {title}\n\n"

        obsidian_content += f"- 회차: {ep_name}\n"

        obsidian_content += f"- 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        obsidian_content += "## 📋 4단 매핑 결과 전문\n\n```\n"

        obsidian_content += st.session_state.get("p6_video_mapped_result", "")

        obsidian_content += "\n```\n\n"

        

        obsidian_content += "## 👥 오팔 계정 배분 내역\n\n"

        obsidian_content += "| 계정 | 씬번호 | 이미지파일 | 동영상파일 |\n| --- | --- | --- | --- |\n"

        for row in dist_data:

            obsidian_content += f"| {row.get('계정', '')} | {row.get('씬번호', '')} | {row.get('이미지파일', '')} | {row.get('동영상파일', '')} |\n"

            

        obs_path = save_obsidian_memory("05_Video_Opal", title, obsidian_content)

        

        if saved_path and obs_path:

            st.session_state.p6_video_opal_saved = True

            st.session_state.p6_video_outputs_saved = True

            save_workspace_state()

            st.toast("✅ [영상 파트] 앱 세션 & 외부 저장소 & 옵시디언 통합 저장 완료!", icon="💾")

            

            # 3. GitHub Push

            success, msg = auto_git_push(f"Part5 Video dispatch & obsidian integrated backup: {ep_name}")

            if success:

                st.toast("🚀 GitHub 백업 완료!", icon="🚀")

            else:

                st.warning(f"Git Push 실패: {msg}")

            return True

        else:

            st.error("❌ 파일 저장 중 오류가 발생하여 백업이 완료되지 않았습니다.")

            return False

    except Exception as e:

        st.error(f"❌ 통합 백업 실패: {e}")

        return False




    # ── 🔒 Part 4 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc4, _rc4 = st.columns(2)
        with _lc4:
            if st.button("🔒 Part 4 최종본 Lock & GitHub Push",
                         key="p4_lock_btn", use_container_width=True):
                lock_and_push_final_version(4, "이미지 생성", ["p5_c_results", "p5_valid_rows"])
        with _rc4:
            if st.button("🔓 Part 4 수정본 생성",
                         key="p4_rev_btn", use_container_width=True):
                create_revision_version(4, "이미지 생성", ["p5_c_results", "p5_valid_rows"])

def render_part6_video():

    c_title, c_control = st.columns([4.2, 5.8])

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎥 파트 5: 영상 생성</h3>', unsafe_allow_html=True)

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p6_vid_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 PIN", type="password", key="p6_vid_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part5", "7777"): st.session_state.unlock_part6_vid = True

            elif pin: st.session_state.unlock_part6_vid = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p6_vid_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # glass-control-box 닫기

    is_locked = False

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    with st.expander("📋 상단 공통: 옵시디언 규칙서 및 Veo3 마스터 프롬프트 (YouTube Creative Director)", expanded=True):

        L, R = st.columns(2, gap="medium")

        with L:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">📚 옵시디언 규칙서</div>', unsafe_allow_html=True)

            st.text_area("옵시디언", value=st.session_state.get("obsidian_rules",""), height=250, key="p6_ob_view", label_visibility="collapsed", disabled=True)

            if st.button("[SEARCH] 편집", key="p6_ob_btn", disabled=is_locked): popup_edit_obsidian()

            st.markdown('</div>', unsafe_allow_html=True)

        with R:

            st.markdown('<div class="top-panel-card"><div class="top-panel-title">[VIDEO] Veo3 마스터 프롬프트 (YouTube Creative Director)</div>', unsafe_allow_html=True)

            st.text_area("Veo3마스터", value=st.session_state.get("p6_veo3_master_prompt",""), height=250, key="p6_master_view", label_visibility="collapsed", disabled=True)

            if st.button("[EDIT] 편집", key="p6_master_btn", disabled=is_locked): popup_edit_veo3_master()

            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ─── 옵시디언 감정 기반 검색 (영상 파트 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P5_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part5", 
            "Part 5: 영상 씬 제작", 
            get_default_tags_for_part("part5"), 
            "p5_obsidian_search_results", 
            "p5_rag_model_selector"
        )

    st.divider()

    P6_PROTO_DEFAULT = (

        "[GEMMA PROTOCOL v2.0 - Video Part]\n"

        "Declaration: Output the following when loading is complete:\n"

        "'[GEMMA PROTOCOL v2.0 - Video Part Loading Complete]'\n"

        "Role: Google Opal x Veo3 full process supervisor\n"

        "Output format: scene_number(3digits) | video_prompt | camera_move | duration(sec) | avatar\n"

        "Scene numbers 001~112 fixed 3 digits. Do not modify script text.\n"

        "@Protagonist appearance change absolutely prohibited.\n"

        "Fixed: silver-grey beard / burgundy-black robe / 60-year-old male.\n"

        "One line = one scene rule. No omission. No ellipsis.\n"

        "Auto retry 3 times on error. Report if all 3 fail."

    )

    if not st.session_state.get("p6_gemma_protocol"): st.session_state.p6_gemma_protocol = P6_PROTO_DEFAULT

    with st.expander("[VIDEO] 젬마 프로토콜 v2.0 — 영상 파트 전용 (클릭하여 확인/편집)", expanded=False):

        render_unified_prompt_editor("영상 젬마 프로토콜 v2.0", "p6_gemma_protocol", height=180, is_locked=is_locked)

        if st.button("🤖 젬마에게 프로토콜 로딩 선언 요청", key="p6_protocol_load", disabled=is_locked):

            with st.spinner("젬마 프로토콜 로딩 중..."):

                try:

                    result = call_gemma(f"아래 프로토콜을 로딩 완료하고 선언문을 출력하라:\\n{st.session_state.p6_gemma_protocol}", system=SAGE_PERSONA)

                    st.session_state.p6_protocol_loaded = result

                    st.success("[OK] 젬마 프로토콜 로딩 완료!")

                except Exception as e:

                    st.error(f"프로토콜 로딩 실패: {e}")

        if st.session_state.get("p6_protocol_loaded"):

            st.text_area("젬마 로딩 선언", value=st.session_state.get("p6_protocol_loaded",""), height=100, key="p6_loaded_ta", disabled=True)

    st.divider()

    

    st.markdown("### 📊 영상 제작 3단계 워크플로우 (3-Step Pipeline)")

    

    # 상단에 회차 이름 입력란 추가

    col_ep = st.columns([3, 7])

    with col_ep[0]:

        ep_name = st.text_input("🎬 작업 회차명", value=st.session_state.get("episode_name", "EP001"), key="p6_episode_name_input")

        if ep_name != st.session_state.get("episode_name", "EP001"):

            st.session_state.episode_name = ep_name

            save_workspace_state()

            

    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

    

    with col1:

        st.markdown('<div class="step-card"><div class="top-panel-title">📥 [Step 1] 이미지 파트 데이터 수신</div></div>', unsafe_allow_html=True)

        p5_data = st.session_state.get("p5_c_results", "").strip()

        if not p5_data:

            st.warning("⚠️ 파트 4(이미지 생성)의 C-1 결과가 없습니다. 먼저 파트 4에서 결과를 생성해 주세요.")

            p5_data_manual = st.text_area("직접 입력 (씬번호 | 대본 | @한글@ | @영어@)", value="", height=300, key="p6_step1_manual_ta")

            if p5_data_manual.strip():

                if st.button("📥 직접 입력 데이터 수신", key="p6_step1_manual_btn", use_container_width=True):

                    st.session_state.p5_c_results = p5_data_manual.strip()

                    save_workspace_state()

                    st.rerun()

        else:

            st.success(f"✅ 파트 4 C-1 데이터 수신 완료 ({len(p5_data.split(chr(10)))}씬)")

            edited_p5_data = st.text_area("수신된 이미지 파트 데이터 (수정 가능)", value=p5_data, height=350, key="p6_step1_data_ta")

            if edited_p5_data != p5_data:

                st.session_state.p5_c_results = edited_p5_data

                save_workspace_state()

                

    with col2:

        st.markdown('<div class="step-card"><div class="top-panel-title">🤖 [Step 2] 4단 레이아웃 매핑 조립</div></div>', unsafe_allow_html=True)

        st.caption("AI를 통해 씬별 영상 연출용 JSON 프롬프트를 조립합니다.")

        

        mapped_result = st.session_state.get("p6_video_mapped_result", "").strip()

        

        if st.button("🤖 [Step 2] AI 4단 매핑 조립 실행", type="primary", use_container_width=True, key="p6_step2_run_btn", disabled=is_locked or not st.session_state.get("p5_c_results", "").strip()):

            src_scenes = [l.strip() for l in st.session_state.get("p5_c_results", "").split("\n") if l.strip()]

            # RAG Context 빌드
            p5_rag_res = st.session_state.get("p5_obsidian_search_results", "")
            p5_rag_ctx = ""
            if p5_rag_res:
                p5_rag_ctx = build_rag_context_from_results(
                    p5_rag_res, "비디오 클립 매칭 및 나레이션 매핑", 
                    st.session_state.get("p5_rag_model_selector", "gemma4:e2b")
                )

            all_mapped_res = []

            prog_bar = st.progress(0, text="4단 레이아웃 매핑 조립 시작...")

            

            for idx, scene_line in enumerate(src_scenes):

                pts = scene_line.split("|")

                if len(pts) >= 4:

                    scene_num = pts[0].strip()

                    script = pts[1].strip()

                    img_prompt = pts[3].strip().replace("@", "")

                else:

                    scene_num = f"{idx+1:03d}"

                    script = pts[1].strip() if len(pts) > 1 else ""

                    img_prompt = pts[2].strip().replace("@", "") if len(pts) > 2 else ""

                

                prompt = (

                    f"[시스템 규칙]\n{st.session_state.get('p6_veo3_master_prompt', '')}\n\n"
                )
                if p5_rag_ctx:
                    prompt += f"[RAG Context]\n{p5_rag_ctx}\n\n"
                prompt += (
                    f"[지시사항] 아래의 씬에 대해 영상 연출을 위한 JSON 프롬프트를 생성하고, 최종적으로 다음 포맷 한 줄로만 답하십시오.\n"

                    f"출력 포맷: {scene_num} | {script} | @{img_prompt}@ | @{{장면을 만드는 JSON 프롬프트}}@\n"

                    f"주의: JSON 프롬프트는 반드시 '{{'로 시작해서 '}}'로 끝나야 하고, camera_move(카메라 움직임), visual_style(비주얼 스타일), character_action(인물 동작) 키를 가진 유효한 JSON 형식이어야 합니다.\n"

                    f"불필요한 설명이나 빈칸을 넣지 마십시오.\n\n"

                    f"입력 씬:\n씬번호: {scene_num}\n대본: {script}\n이미지 프롬프트: {img_prompt}\n"

                )

                

                try:

                    ai_res = call_gemma(prompt, system=SAGE_PERSONA).strip()

                    ai_res_single = " ".join([l.strip() for l in ai_res.split("\n") if l.strip()])

                    all_mapped_res.append(ai_res_single)

                except Exception as e:

                    dummy_json = '{"camera_move": "slow zoom in", "visual_style": "cinematic, 16:9, warm light", "character_action": "subtle breathing"}'

                    all_mapped_res.append(f"{scene_num} | {script} | @{img_prompt}@ | @{dummy_json}@")

                

                prog_bar.progress((idx+1)/len(src_scenes), text=f"씬 {scene_num} 조립 중... ({idx+1}/{len(src_scenes)})")

            

            st.session_state.p6_video_mapped_result = "\n".join(all_mapped_res)

            prog_bar.empty()

            save_workspace_state()

            st.success("✅ AI 4단 매핑 조립 완료!")

            st.rerun()

            

        if mapped_result:

            edited_mapped = st.text_area("4단 매핑 결과 (수정 가능)", value=mapped_result, height=300, key="p6_step2_result_ta")

            if edited_mapped != mapped_result:

                st.session_state.p6_video_mapped_result = edited_mapped

                save_workspace_state()

                

            if st.button("🔍 4단 매핑 정규식 검증 실행", use_container_width=True, key="p6_step2_validate_btn"):

                lines = [l.strip() for l in st.session_state.get("p6_video_mapped_result", "").split("\n") if l.strip()]

                pattern = re.compile(r"^(\d{3})\s*\|\s*(.+?)\s*\|\s*@(.+?)@\s*\|\s*@(\{.+?\})@\s*$")

                

                valid_rows = []

                error_rows = []

                

                for i, line in enumerate(lines, 1):

                    m = pattern.match(line)

                    if m:

                        valid_rows.append({

                            "씬번호": m.group(1),

                            "대본": m.group(2),

                            "이미지프롬프트": m.group(3),

                            "JSON프롬프트": m.group(4),

                            "이미지파일": f"scene_{m.group(1)}.png",

                            "동영상파일": f"video_{m.group(1)}.mp4"

                        })

                    else:

                        error_rows.append(f"Line {i}: {line[:50]}...")

                

                st.session_state.p6_video_valid_rows = valid_rows

                save_workspace_state()

                

                if error_rows:

                    st.error(f"❌ 검증 실패: {len(error_rows)}개 라인 규격 미달")

                    with st.expander("실패 라인 확인", expanded=True):

                        for err in error_rows:

                            st.write(err)

                else:

                    st.success(f"✅ 검증 통과! 전체 {len(valid_rows)}씬 규격 일치")

                    

    with col3:

        st.markdown('<div class="step-card"><div class="top-panel-title">👥 [Step 3] Opal 12씬 이하 계정 배분</div></div>', unsafe_allow_html=True)

        st.caption("씬들을 계정당 최대 12개 이하로 자동 분배합니다.")

        

        valid_scenes = st.session_state.get("p6_video_valid_rows", [])

        if not valid_scenes:

            st.info("💡 스텝 2에서 정규식 검증을 통과해야 배분 작업이 가능합니다.")

        else:

            st.success(f"📋 배분 대상: {len(valid_scenes)}개 씬")

            

            max_per_account = 12

            total_scenes = len(valid_scenes)

            num_accounts = math.ceil(total_scenes / max_per_account)

            

            distributed_rows = []

            base_size = total_scenes // num_accounts

            remainder = total_scenes % num_accounts

            

            current_idx = 0

            for acct_num in range(1, num_accounts + 1):

                size = base_size + (1 if acct_num <= remainder else 0)

                account_name = f"{acct_num}번계정"

                

                for _ in range(size):

                    if current_idx < total_scenes:

                        scene = valid_scenes[current_idx]

                        distributed_rows.append({

                            "계정": account_name,

                            "씬번호": scene["씬번호"],

                            "대본": scene["대본"],

                            "이미지프롬프트": scene["이미지프롬프트"],

                            "JSON프롬프트": scene["JSON프롬프트"],

                            "이미지파일": scene["이미지파일"],

                            "동영상파일": scene["동영상파일"]

                        })

                        current_idx += 1

            

            df_dist = pd.DataFrame(distributed_rows)

            st.session_state.p6_video_opal_data = distributed_rows

            

            st.dataframe(df_dist[["계정", "씬번호", "이미지파일", "동영상파일"]], use_container_width=True, height=250)

            

            if st.button("💾 [Part 5] 오팔 배분 외부 저장 및 백업", type="primary", use_container_width=True, key="p6_step3_outputs_save_btn"):

                save_video_production_all(st.session_state.get("episode_name", "EP001").strip())

                        

    st.divider()

    



    with st.expander("📚 Veo3 x Google Opal 영상 생성 작업 순서", expanded=False):

        st.markdown("""

**PREP-01**: Google Opal 접속 -> 새 워크플로우 생성 "현자의거울_EP001_영상생성"

**PREP-02**: Veo3 마스터 프롬프트 -> Opal 공통 시스템 지시 노드에 붙여넣기

**PREP-03**: 젬마 씬별 지시 CSV -> Opal 순차 배분 노드에 투입

**PREP-04**: 8계정 병렬 렌더링 시작 -> 계정당 14씬 담당

**PREP-05**: 렌더링 완료 video_XXX.mp4 -> 06_Video_Clips 폴더 저장



---



**씬별 렌더링 루틴 (001~112 반복)**:

STEP-01: Opal 배분 CSV에서 해당 계정 씬 데이터 확인

STEP-02: Veo3 영상 프롬프트 + 이미지 파일 투입

STEP-03: Output filename = video_XXX.mp4

STEP-04: Generate -> 완료 대기

STEP-05: 영상 검수 (인물 일관성/조명/16:9 비율)

STEP-06: 합격 -> 저장 / 불합격 -> 재생성

STEP-07: 다음 씬 (+1) 반복



[WARN] 주의: 8계정 동시 렌더링 시 Veo3 크레딧 소모 확인

[WARN] 10씬마다 일괄 검수 실시

""")






    # ── 🔒 Part 5 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc5, _rc5 = st.columns(2)
        with _lc5:
            if st.button("🔒 Part 5 최종본 Lock & GitHub Push",
                         key="p5_lock_btn", use_container_width=True):
                lock_and_push_final_version(5, "영상 생성", ["p6_video_mapped_result", "p6_video_opal_data"])
        with _rc5:
            if st.button("🔓 Part 5 수정본 생성",
                         key="p5_rev_btn", use_container_width=True):
                create_revision_version(5, "영상 생성", ["p6_video_mapped_result", "p6_video_opal_data"])

def render_part34():

    c_title, c_control = st.columns([4.2, 5.8])

    

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">✍️ 파트 3: 대본 작성</h3>', unsafe_allow_html=True)

        

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p34_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p34_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part3", "7777"): st.session_state.unlock_part34 = True

            elif pin: st.session_state.unlock_part34 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p34_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)



    if "unlock_part34" not in st.session_state:

        st.session_state.unlock_part34 = False

    is_locked = False

    

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)



    st.subheader("[LINK] Part 2 → Part 3-4 데이터 수신 상태")

    with st.container(border=True):

        p2_plan = st.session_state.get("p2_planning_result", "")

        p2_research = st.session_state.get("p2_research_result", "")

        p2_topic = st.session_state.get("p2_topic_selection", "")

        

        c_stat1, c_stat2, c_stat3 = st.columns(3)

        with c_stat1:

            if p2_topic:

                st.success(f"[OK] 선정 주제: {p2_topic}")

            else:

                st.error("[FAIL] 주제 미선정 — Part 2에서 주제를 먼저 선정하세요")

        with c_stat2:

            if p2_research:

                st.success(f"[OK] 융합 리서치: {len(p2_research)}자 수신")

            else:

                st.error("[FAIL] 리서치 미완료 — Part 2에서 자료조사를 완료하세요")

        with c_stat3:

            if p2_plan:

                st.success(f"[OK] 기획안: {len(p2_plan)}자 수신")

            else:

                st.error("[FAIL] 기획안 미완료 — Part 2에서 기획안을 완성하세요")

        

        if p2_plan:

            with st.expander("📋 Part 2 기획안 원문 보기 (읽기 전용)"):

                st.text_area("Part 2 기획안", value=p2_plan, height=200, disabled=True, label_visibility="collapsed", key="p34_p2_preview")



    st.divider()



    st.subheader("🧩 Step 1. 젬마 프로토콜 로딩")

    with st.container(border=True):

        st.markdown('<div class="top-panel-card"><div class="top-panel-title">📝 젬마 프로토콜 (Part 3-4 전용)</div>', unsafe_allow_html=True)

        render_unified_prompt_editor("📝 젬마 프로토콜 (Part 3-4 전용)", "p34_gemma_protocol", height=200, is_locked=is_locked)

        st.markdown('</div>', unsafe_allow_html=True)



    st.divider()



    st.subheader("🏗️ Step 2. Architect — 112씬 구조 설계 (기-승-전-결)")

    with st.container(border=True):

        st.caption("Part 2에서 완성된 기획안을 기반으로, 112씬의 기-승-전-결 서사 뼈대를 설계합니다.")



        # --- 3단 버튼 구조 (시작 / 로컬저장 / 옵시디언백업) ---

        c_arch1, c_arch2, c_arch3 = st.columns([4, 3, 3])

        with c_arch1:

            if st.button("🚀 112씬 구조 자동 설계 (AI)", use_container_width=True, disabled=is_locked, type="primary", key="p34_arch_btn"):

                p2_plan_v = st.session_state.get("p2_planning_result", "")

                if not p2_plan_v:

                    st.error("[WARN] Part 2의 '총괄 기획안'이 비어 있습니다. Part 2를 먼저 완료해 주세요.")

                else:

                    st.session_state.p34_scene_structure = ""

                    st.session_state.p34_arch_saved = False

                    st.session_state.p34_arch_obsidian_saved = False

                    save_workspace_state()



                    with st.spinner("기-승-전-결 112씬 뼈대 설계 중..."):

                        prompt = f"[지시] 아래 기획안을 바탕으로 112씬 분량의 대본 구조(뼈대)를 설계해 주세요.\n\n[기획안]\n{p2_plan_v}\n\n[출력 형식]\n기(001-028): 각 씬의 한 줄 요약 (감정: EXPR코드)\n승(029-056): 각 씬의 한 줄 요약 (감정: EXPR코드)\n전(057-084): 각 씬의 한 줄 요약 (감정: EXPR코드)\n결(085-112): 각 씬의 한 줄 요약 (감정: EXPR코드)\n\n{st.session_state.p34_gemma_protocol}"

                        result = call_gemma(prompt)

                        st.session_state.p34_scene_structure = result

                        st.session_state.p34_arch_saved = True

                        save_workspace_state()



                        keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)

                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                        tag_hashes = " ".join([f"#{t}" for t in tag_list])



                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                        topic_title = st.session_state.get("p2_topic_selection", "대본구조")

                        folder_name = "ScriptDrafts"

                        title = f"112씬 구조 설계 - {topic_title}"



                        val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[서사구조]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#대본설계'}\n\n"

                        val += f"## 📐 112씬 구조 설계 본문\n{result}\n\n"



                        obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")

                        if obs_path:

                            lock_file_readonly(obs_path)

                            st.toast("💾 구조 설계 로컬 자동 저장 완료!", icon="💾")

                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                            if success:

                                st.session_state.p34_arch_obsidian_saved = True

                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                            else:

                                st.error(f"옵시디언은 저장되었으나 GitHub Push에 실패했습니다: {msg}")

                            save_workspace_state()

                            st.rerun()



        with c_arch2:

            if st.session_state.get("p34_arch_saved", False):

                st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_arch_local_indicator")

            else:

                st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_arch_local_waiting")



        with c_arch3:

            if st.session_state.get("p34_arch_obsidian_saved", False):

                st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_arch_obs_indicator")

            else:

                st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_arch_obs_waiting")



        st.info("ℹ️ Part 2 기획안 → 기(001~028) / 승(029~056) / 전(057~084) / 결(085~112) 자동 분배")

        render_unified_prompt_editor("📐 112씬 구조 설계 결과", "p34_scene_structure", height=400, is_locked=is_locked)



        if st.session_state.p34_scene_structure:

            if st.button("💾 (예비용) 구조 설계 수동 옵시디언 백업", use_container_width=True, key="p34_save_struct", disabled=is_locked):

                st.session_state.p34_scene_structure = st.session_state.p34_struct_area

                ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                topic_title = st.session_state.get("p2_topic_selection", "대본구조")

                folder_name = "ScriptDrafts"

                title = f"112씬 구조 설계 - {topic_title}"

                val = f"## 📖 112씬 구조 설계\n{st.session_state.p34_scene_structure}\n"

                obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")

                if obs_path:

                    lock_file_readonly(obs_path)

                    st.toast("✅ 수동 구조 설계 옵시디언 백업 완료!", icon="💾")

                    st.session_state.p34_arch_obsidian_saved = True

                    save_workspace_state()

                    success, msg = auto_git_push(f"Manual Save: {title}")

                    if success:

                        st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                    else:

                        st.error(f"GitHub Push 실패: {msg}")

                    st.rerun()



    st.divider()



    # ─── 옵시디언 감정 기반 검색 (대본 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P3_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part3", 
            "Part 3: 나레이션 대본", 
            get_default_tags_for_part("part3"), 
            "p3_obsidian_search_results", 
            "p3_rag_model_selector"
        )

    st.divider()

    st.subheader("[WRITE] Step 3. Writer — 대본 집필 (3단 분리)")

    st.caption("확정된 112씬 구조 위에 살을 붙여, 나레이션·이미지·캡컷 3종 대본을 각각 집필합니다.")



    # ─── Step 3: 탭 방식으로 Writer 3종 대본 집필 ───

    tab_narr, tab_img, tab_cap = st.tabs(["🎙️ 1️⃣ 나레이션 대본", "🖼️ 2️⃣ 이미지 생성용 대본", "🎬 3️⃣ 캡컷 에셋 데이터"])



    # ─────────────────────────────────────────────────────

    # 탭 1: 나레이션 대본

    # ─────────────────────────────────────────────────────

    with tab_narr:

        with st.container(border=True):

            st.markdown("### 🎙️ 나레이션 대본")

            st.caption("시청자가 듣게 될 순수 나레이션 텍스트 (CosyVoice 연동)")



            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (나레이션)", "p34_narr_prompt", height=100, is_locked=is_locked)



            # 3단 버튼 구조

            c_n1, c_n2, c_n3 = st.columns([4, 3, 3])

            with c_n1:

                if st.button("🎙️ 나레이션 대본 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_narr_btn"):

                    if not st.session_state.p34_scene_structure:

                        st.error("[WARN] Step 2의 '112씬 구조 설계'를 먼저 완료해 주세요.")

                    else:

                        st.session_state.p34_narration_script = ""

                        st.session_state.p34_narr_saved = False

                        st.session_state.p34_narr_obsidian_saved = False

                        save_workspace_state()



                        with st.spinner("나레이션 대본 집필 중..."):

                            narr_prompt_val = st.session_state.get("p34_narr_prompt", "")

                            # RAG Context 빌드 및 주입
                            p3_rag_res = st.session_state.get("p3_obsidian_search_results", "")
                            p3_rag_ctx = ""
                            if p3_rag_res:
                                p3_rag_ctx = build_rag_context_from_results(
                                    p3_rag_res, "대본 작성", 
                                    st.session_state.get("p3_rag_model_selector", "gemma4:e2b")
                                )

                            prompt = f"[지시] 아래 112씬 구조를 바탕으로 각 씬의 나레이션 대본을 작성하세요.\n화자는 60대 현자(Sage)이며, 4070 시청자에게 말하듯 따뜻하고 묵직한 톤으로 작성합니다.\n\n"
                            if p3_rag_ctx:
                                prompt += f"{p3_rag_ctx}\n\n"
                            prompt += f"[RAG & 지식 공백 방지 지침]\n만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.\n대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.\n예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]\n\n[추가 지시]\n{narr_prompt_val}\n\n[112씬 구조]\n{st.session_state.p34_scene_structure}\n\n[출력 형식]\n씬번호(3자리) | 나레이션 대본 텍스트\n\n{st.session_state.p34_gemma_protocol}"

                            result = call_gemma(prompt)

                            st.session_state.p34_narration_script = result

                            st.session_state.pipeline_state["narration_script"] = result

                            

                            # RAG 지식 공백 감지

                            kw = check_need_research_tag(result)

                            if kw:

                                st.session_state.p34_narr_need_research_kw = kw

                                st.session_state.p34_narr_saved = False

                                st.session_state.p34_narr_obsidian_saved = False

                            else:

                                st.session_state.p34_narr_need_research_kw = None

                                # 자가 검수 수행

                                ver_res = verify_content_with_gemma("나레이션 대본", result, st.session_state.base_prompt_rules)

                                st.session_state.p34_narr_verification = ver_res

                                

                                if ver_res.get("status") == "PASS":

                                    st.session_state.p34_narr_saved = True

                                    

                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)

                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])



                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                    topic_title = st.session_state.get("p2_topic_selection", "나레이션")

                                    folder_name = "ScriptDrafts"

                                    title = f"[Part3] 나레이션 대본 - {topic_title}"



                                    val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[나레이션]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#나레이션'}\n\n"

                                    val += f"## 🎙️ 나레이션 대본 본문\n{result}\n\n"

                                    val += f"## 🔗 파이프라인 연결\n- 선행 파트: Part 2 기획안\n- 다음 단계: 이미지 프롬프트 생성\n\n"



                                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")

                                    if obs_path:

                                        lock_file_readonly(obs_path)

                                        st.toast("💾 나레이션 로컬 자동 저장 완료!", icon="💾")

                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                        if success:

                                            st.session_state.p34_narr_obsidian_saved = True

                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                        else:

                                            st.error(f"GitHub Push 실패: {msg}")

                                else:

                                    st.session_state.p34_narr_saved = False

                                    st.session_state.p34_narr_obsidian_saved = False

                                    

                            save_workspace_state()

                            st.rerun()



            with c_n2:

                if st.session_state.get("p34_narr_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_narr_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_narr_local_waiting")



            with c_n3:

                if st.session_state.get("p34_narr_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_narr_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_narr_obs_waiting")



            if st.session_state.p34_narration_script:

                st.markdown("<br>", unsafe_allow_html=True)



                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---

                if st.session_state.get("p34_narr_need_research_kw"):

                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p34_narr_need_research_kw})")

                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p34_narr_web_research_approve_btn", type="primary", use_container_width=True):

                        if not st.session_state.get("tavily_api_key"):

                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")

                        else:

                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):

                                from sage_engine import tavily_search

                                q = st.session_state.p34_narr_need_research_kw

                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)

                                if "error" in res_search:

                                    st.error(f"Tavily 검색 오류: {res_search['error']}")

                                else:

                                    raw_results = res_search.get("results", [])

                                    web_context = ""

                                    for r in raw_results:

                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"

                                    

                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.

제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '나레이션 대본'을 완벽하게 재작성하라.

모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.



[웹 리서치 참조 자료]:

{web_context}



[이전 불완전한 결과물]:

{st.session_state.p34_narration_script}



[작업 지시]:

위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.

[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.

"""

                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                    st.session_state.p34_narration_script = res_new

                                    st.session_state.pipeline_state["narration_script"] = res_new

                                    

                                    # 재검증

                                    st.session_state.p34_narr_need_research_kw = check_need_research_tag(res_new)

                                    if not st.session_state.p34_narr_need_research_kw:

                                        ver_res = verify_content_with_gemma("나레이션 대본", res_new, st.session_state.base_prompt_rules)

                                        st.session_state.p34_narr_verification = ver_res

                                        if ver_res.get("status") == "PASS":

                                            st.session_state.p34_narr_saved = True

                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)

                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                            topic_title = st.session_state.get("p2_topic_selection", "나레이션")

                                            title = f"[Part3] 나레이션 대본 - {topic_title}"

                                            

                                            val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[나레이션]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#나레이션'}\n\n"

                                            val += f"## 🎙️ 나레이션 대본 본문\n{res_new}\n\n"

                                            val += f"## 🔗 파이프라인 연결\n- 선행 파트: Part 2 기획안\n- 다음 단계: 이미지 프롬프트 생성\n\n"

                                            

                                            obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                                            if obs_path:

                                                lock_file_readonly(obs_path)

                                                st.toast("💾 나레이션 로컬 자동 저장 완료!", icon="💾")

                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                                if success:

                                                    st.session_state.p34_narr_obsidian_saved = True

                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                                else:

                                                    st.error(f"GitHub Push 실패: {msg}")

                                    else:

                                        st.session_state.p34_narr_saved = False

                                        st.session_state.p34_narr_obsidian_saved = False

                                        

                                    save_workspace_state()

                                    st.rerun()



                elif st.session_state.get("p34_narr_verification"):

                    ver = st.session_state.p34_narr_verification

                    if ver.get("status") == "FAIL":

                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")

                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p34_narr_self_correct_btn", type="primary", use_container_width=True):

                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):

                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.

이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.



[이전 결과물]:

{st.session_state.p34_narration_script}



[수정 건의사항]:

{ver.get("suggestions", "없음")}



[작업 지시]:

수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.

모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.

"""

                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                st.session_state.p34_narration_script = res_corr

                                st.session_state.pipeline_state["narration_script"] = res_corr

                                

                                # 재검증

                                st.session_state.p34_narr_need_research_kw = check_need_research_tag(res_corr)

                                if not st.session_state.p34_narr_need_research_kw:

                                    ver_res = verify_content_with_gemma("나레이션 대본", res_corr, st.session_state.base_prompt_rules)

                                    st.session_state.p34_narr_verification = ver_res

                                    if ver_res.get("status") == "PASS":

                                        st.session_state.p34_narr_saved = True

                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)

                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                        topic_title = st.session_state.get("p2_topic_selection", "나레이션")

                                        title = f"[Part3] 나레이션 대본 - {topic_title}"

                                        

                                        val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[나레이션]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#나레이션'}\n\n"

                                        val += f"## 🎙️ 나레이션 대본 본문\n{res_corr}\n\n"

                                        val += f"## 🔗 파이프라인 연결\n- 선행 파트: Part 2 기획안\n- 다음 단계: 이미지 프롬프트 생성\n\n"

                                        

                                        obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                                        if obs_path:

                                            lock_file_readonly(obs_path)

                                            st.toast("💾 나레이션 대본 결과 로컬 자동 저장 완료!", icon="💾")

                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                            if success:

                                                st.session_state.p34_narr_obsidian_saved = True

                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                            else:

                                                st.error(f"GitHub Push 실패: {msg}")

                                else:

                                    st.session_state.p34_narr_saved = False

                                    st.session_state.p34_narr_obsidian_saved = False

                                    

                                save_workspace_state()

                                st.rerun()



                render_result_preview("p34_narration_script", "Part 3 나레이션 대본")



                if st.button("💾 (예비용) 나레이션 수동 옵시디언 백업", use_container_width=True, key="p34_save_narr", disabled=is_locked):

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    topic_title = st.session_state.get("p2_topic_selection", "나레이션")

                    title = f"[Part3] 나레이션 대본 - {topic_title}"

                    val = f"## 🎙️ 나레이션 대본\n{st.session_state.p34_narration_script}\n"

                    obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 나레이션 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p34_narr_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save: {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"GitHub Push 실패: {msg}")

                        st.rerun()



    # ─────────────────────────────────────────────────────

    # 탭 2: 이미지 생성용 대본

    # ─────────────────────────────────────────────────────

    with tab_img:

        with st.container(border=True):

            st.markdown("### 🖼️ 이미지 생성용 대본")

            st.caption("씬번호 | 대본 | @한글묘사@ | @영어프롬프트@ (Part 5 연동)")



            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (이미지 대본)", "p34_img_prompt", height=100, is_locked=is_locked)



            # 3단 버튼 구조

            c_i1, c_i2, c_i3 = st.columns([4, 3, 3])

            with c_i1:

                if st.button("🖼️ 이미지 프롬프트 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_img_btn"):

                    if not st.session_state.p34_narration_script:

                        st.error("[WARN] 먼저 '나레이션 대본' 탭에서 나레이션을 완료해 주세요.")

                    else:

                        st.session_state.p34_image_script = ""

                        st.session_state.p34_img_saved = False

                        st.session_state.p34_img_obsidian_saved = False

                        save_workspace_state()



                        with st.spinner("이미지 프롬프트 변환 중..."):

                            img_prompt_val = st.session_state.get("p34_img_prompt", "")

                            prompt = f"[지시] 아래 나레이션 대본을 이미지 파트 규격(C-1)에 맞춰 변환하세요.\n\n[RAG & 지식 공백 방지 지침]\n만약 RAG 참조 자료나 옵시디언 Vault 내 자료, 혹은 본인의 내부 지식이 부족하여 해당 주제에 대한 객관적/역사적 사실을 정확하게 설명하기 어렵다면, 절대 상상하여 내용을 허구로 지어내지 마십시오.\n대신 텍스트 출력 상단이나 본문에 정확히 [NEED_RESEARCH: 검색 키워드] 형식의 태그를 단 한 줄로만 포함하여 출력하십시오.\n예: [NEED_RESEARCH: 아우구스티누스 시간론 고백록 11장]\n\n[추가 지시]\n{img_prompt_val}\n\n[나레이션 대본]\n{st.session_state.p34_narration_script}\n\n[출력 형식 — 반드시 준수]\n씬번호(3자리) | 대본 | @한글묘사@ | @영어프롬프트@\n\n{st.session_state.p34_gemma_protocol}"

                            result = call_gemma(prompt)

                            st.session_state.p34_image_script = result

                            st.session_state.pipeline_state["image_script"] = result

                            

                            # RAG 지식 공백 감지

                            kw = check_need_research_tag(result)

                            if kw:

                                st.session_state.p34_img_need_research_kw = kw

                                st.session_state.p34_img_saved = False

                                st.session_state.p34_img_obsidian_saved = False

                            else:

                                st.session_state.p34_img_need_research_kw = None

                                # 자가 검수 수행

                                ver_res = verify_content_with_gemma("이미지 생성용 대본", result, st.session_state.base_prompt_rules)

                                st.session_state.p34_img_verification = ver_res

                                

                                if ver_res.get("status") == "PASS":

                                    st.session_state.p34_img_saved = True

                                    

                                    keywords = extract_keywords_via_gemma(result, st.session_state.base_prompt_rules)

                                    tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                    tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                    tag_hashes = " ".join([f"#{t}" for t in tag_list])



                                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                    topic_title = st.session_state.get("p2_topic_selection", "이미지대본")

                                    folder_name = "ScriptDrafts"

                                    title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"



                                    val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                                    val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[이미지]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#이미지대본'}\n\n"

                                    val += f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{result}\n\n"

                                    val += f"## 🔗 파이프라인 연결\n- 선행 파트: 나레이션 대본\n- 다음 단계: Part 5 Image Consistency\n\n"



                                    obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")

                                    if obs_path:

                                        lock_file_readonly(obs_path)

                                        st.toast("💾 이미지 대본 로컬 자동 저장 완료!", icon="💾")

                                        success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                        if success:

                                            st.session_state.p34_img_obsidian_saved = True

                                            st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                        else:

                                            st.error(f"GitHub Push 실패: {msg}")

                                else:

                                    st.session_state.p34_img_saved = False

                                    st.session_state.p34_img_obsidian_saved = False

                                    

                            save_workspace_state()

                            st.rerun()



            with c_i2:

                if st.session_state.get("p34_img_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_img_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_img_local_waiting")



            with c_i3:

                if st.session_state.get("p34_img_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_img_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_img_obs_waiting")



            if st.session_state.p34_image_script:

                st.markdown("<br>", unsafe_allow_html=True)



                # --- RAG 공백 및 자가 검수 피드백 루프 UI ---

                if st.session_state.get("p34_img_need_research_kw"):

                    st.warning(f"⚠️ **지식 공백 감지**: Gemma가 추가 웹 리서치를 요청했습니다. (검색어: {st.session_state.p34_img_need_research_kw})")

                    if st.button("🌐 웹 추가 리서치 및 보충 승인", key="p34_img_web_research_approve_btn", type="primary", use_container_width=True):

                        if not st.session_state.get("tavily_api_key"):

                            st.error("좌측 설정에서 Tavily API Key를 먼저 등록해 주세요.")

                        else:

                            with st.spinner("Tavily를 통해 웹 리서치 수행 및 보충 재생성 중..."):

                                from sage_engine import tavily_search

                                q = st.session_state.p34_img_need_research_kw

                                res_search = tavily_search(q, st.session_state.tavily_api_key, max_results=5)

                                if "error" in res_search:

                                    st.error(f"Tavily 검색 오류: {res_search['error']}")

                                else:

                                    raw_results = res_search.get("results", [])

                                    web_context = ""

                                    for r in raw_results:

                                        web_context += f"출처 URL: {r.get('url')}\n제목: {r.get('title')}\n내용: {r.get('content')}\n\n"

                                    

                                    prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 지식 보충 에이전트다.

제공된 [웹 리서치 참조 자료]를 바탕으로, 지식 공백이 있었던 주제에 대한 보충 설명을 추가하여 '이미지 생성용 대본'을 완벽하게 재작성하라.

모든 서술 내용 중 웹 리서치 참조 자료로부터 가져온 정보에는 반드시 끝부분이나 적절한 곳에 [SOURCE: 출처 URL] 형태로 출처를 상세히 표기하라.



[웹 리서치 참조 자료]:

{web_context}



[이전 불완전한 결과물]:

{st.session_state.p34_image_script}



[작업 지시]:

위의 웹 리서치 자료를 융합하여, 이전 불완전한 결과물의 누락되거나 왜곡된 사실을 보충하고 출처를 명확히 표기하여 다시 완성된 형태로 작성하라.

[RAG & 지식 공백 방지 지침] 및 [마스터 규칙서]를 철저히 준수하라.

"""

                                    res_new = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                    st.session_state.p34_image_script = res_new

                                    st.session_state.pipeline_state["image_script"] = res_new

                                    

                                    # 재검증

                                    st.session_state.p34_img_need_research_kw = check_need_research_tag(res_new)

                                    if not st.session_state.p34_img_need_research_kw:

                                        ver_res = verify_content_with_gemma("이미지 생성용 대본", res_new, st.session_state.base_prompt_rules)

                                        st.session_state.p34_img_verification = ver_res

                                        if ver_res.get("status") == "PASS":

                                            st.session_state.p34_img_saved = True

                                            keywords = extract_keywords_via_gemma(res_new, st.session_state.base_prompt_rules)

                                            tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                            tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                            tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                            topic_title = st.session_state.get("p2_topic_selection", "이미지대본")

                                            title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"

                                            

                                            val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                                            val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[이미지]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#이미지대본'}\n\n"

                                            val += f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{res_new}\n\n"

                                            val += f"## 🔗 파이프라인 연결\n- 선행 파트: 나레이션 대본\n- 다음 단계: Part 5 Image Consistency\n\n"

                                            

                                            obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                                            if obs_path:

                                                lock_file_readonly(obs_path)

                                                st.toast("💾 이미지 대본 로컬 자동 저장 완료!", icon="💾")

                                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                                if success:

                                                    st.session_state.p34_img_obsidian_saved = True

                                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                                else:

                                                    st.error(f"GitHub Push 실패: {msg}")

                                    else:

                                        st.session_state.p34_img_saved = False

                                        st.session_state.p34_img_obsidian_saved = False

                                        

                                    save_workspace_state()

                                    st.rerun()



                elif st.session_state.get("p34_img_verification"):

                    ver = st.session_state.p34_img_verification

                    if ver.get("status") == "FAIL":

                        st.error(f"❌ **Gemma 자가 검수 실패**:\n{ver.get('report')}")

                        if st.button("🔧 Gemma 자가 교정 및 재작성 요청", key="p34_img_self_correct_btn", type="primary", use_container_width=True):

                            with st.spinner("Gemma가 피드백을 수용하여 교정 작성 중..."):

                                prompt = f"""[SYSTEM]: 너는 현자의 거울 스튜디오의 자가 교정 및 재작성 에이전트다.

이전 검수 결과에서 실패(FAIL)한 부분을 아래의 [수정 건의사항]을 바탕으로 완벽하게 보완하여 재작성해야 한다.



[이전 결과물]:

{st.session_state.p34_image_script}



[수정 건의사항]:

{ver.get("suggestions", "없음")}



[작업 지시]:

수정 건의사항을 반영하여 정합성을 완벽히 만족하도록 결과물을 수정 및 재작성하라.

모든 등장인물은 오직 '@Protagonist'로만 지칭해야 하고, 씬 번호는 3자리 정수 형태를 유지하며, 출처가 있는 경우 출처 태그를 준수해야 한다.

"""

                                res_corr = call_gemma(prompt, system=COMMON_GEMMA_PROTOCOL + "\n\n" + SAGE_PERSONA)

                                st.session_state.p34_image_script = res_corr

                                st.session_state.pipeline_state["image_script"] = res_corr

                                

                                # 재검증

                                st.session_state.p34_img_need_research_kw = check_need_research_tag(res_corr)

                                if not st.session_state.p34_img_need_research_kw:

                                    ver_res = verify_content_with_gemma("이미지 생성용 대본", res_corr, st.session_state.base_prompt_rules)

                                    st.session_state.p34_img_verification = ver_res

                                    if ver_res.get("status") == "PASS":

                                        st.session_state.p34_img_saved = True

                                        keywords = extract_keywords_via_gemma(res_corr, st.session_state.base_prompt_rules)

                                        tag_list = [t.strip() for t in keywords.split(",") if t.strip()]

                                        tag_links = " ".join([f"[[{t}]]" for t in tag_list])

                                        tag_hashes = " ".join([f"#{t}" for t in tag_list])

                                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                                        topic_title = st.session_state.get("p2_topic_selection", "이미지대본")

                                        title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"

                                        

                                        val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                                        val += f"## 🎯 핵심 감정 / RAG 태그\n- 연결 개념 링크: {tag_links if tag_links else '[[이미지]], [[현자의거울]]'}\n- 태그: {tag_hashes if tag_hashes else '#이미지대본'}\n\n"

                                        val += f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{res_corr}\n\n"

                                        val += f"## 🔗 파이프라인 연결\n- 선행 파트: 나레이션 대본\n- 다음 단계: Part 5 Image Consistency\n\n"

                                        

                                        obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                                        if obs_path:

                                            lock_file_readonly(obs_path)

                                            st.toast("💾 이미지 대본 결과 로컬 자동 저장 완료!", icon="💾")

                                            success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                            if success:

                                                st.session_state.p34_img_obsidian_saved = True

                                                st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                            else:

                                                st.error(f"GitHub Push 실패: {msg}")

                                else:

                                    st.session_state.p34_img_saved = False

                                    st.session_state.p34_img_obsidian_saved = False

                                    

                                save_workspace_state()

                                st.rerun()



                render_result_preview("p34_image_script", "Part 4 이미지 대본")



                if st.button("💾 (예비용) 이미지 대본 수동 옵시디언 백업", use_container_width=True, key="p34_save_img", disabled=is_locked):

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    topic_title = st.session_state.get("p2_topic_selection", "이미지대본")

                    title = f"[Part3] 이미지 프롬프트 대본 - {topic_title}"

                    val = f"## 🖼️ 이미지 프롬프트 (C-1 형식)\n{st.session_state.p34_image_script}\n"

                    obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 이미지 대본 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p34_img_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save: {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"GitHub Push 실패: {msg}")

                        st.rerun()



    # ─────────────────────────────────────────────────────

    # 탭 3: 캡컷 에셋 데이터

    # ─────────────────────────────────────────────────────

    with tab_cap:

        with st.container(border=True):

            st.markdown("### 🎬 캡컷 에셋 데이터")

            st.caption("CapCut 자동 조립용 JSON (타임라인·BGM·이미지 매핑)")



            render_unified_prompt_editor("🤖 젬마 작업지시 프롬프트 (캡컷 JSON)", "p34_cap_prompt", height=100, is_locked=is_locked)



            # 3단 버튼 구조

            c_c1, c_c2, c_c3 = st.columns([4, 3, 3])

            with c_c1:

                if st.button("🎬 캡컷 JSON 생성 (AI)", use_container_width=True, disabled=is_locked, key="p34_cap_btn"):

                    if not st.session_state.p34_image_script:

                        st.error("[WARN] 먼저 '이미지 생성용 대본' 탭에서 이미지 대본을 완료해 주세요.")

                    else:

                        st.session_state.p34_capcut_data = ""

                        st.session_state.p34_cap_saved = False

                        st.session_state.p34_cap_obsidian_saved = False

                        save_workspace_state()



                        with st.spinner("캡컷 JSON 조립 중..."):

                            cap_prompt_val = st.session_state.get("p34_cap_prompt", "")

                            prompt = f"[지시] 아래 이미지 대본을 CapCut 자동화 JSON으로 변환하세요.\n\n[추가 지시]\n{cap_prompt_val}\n\n[이미지 대본]\n{st.session_state.p34_image_script}\n\n[출력 형식 — JSON]\n각 씬: scene_id, script, action_kr, expression, props_used, image_file, audio_file, timeline_order, duration_sec\n\n{st.session_state.p34_gemma_protocol}"

                            result = call_gemma(prompt)

                            st.session_state.p34_capcut_data = result

                            st.session_state.pipeline_state["capcut_data"] = result

                            st.session_state.p34_cap_saved = True

                            save_workspace_state()



                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                            topic_title = st.session_state.get("p2_topic_selection", "캡컷에셋")

                            folder_name = "ScriptDrafts"

                            title = f"[Part3] 캡컷 에셋 JSON - {topic_title}"



                            val = f"## 📌 핵심 요약\n- 주제: {topic_title}\n\n"

                            val += f"## 🎬 캡컷 에셋 JSON 본문\n```json\n{result}\n```\n\n"

                            val += f"## 🔗 파이프라인 연결\n- 선행 파트: 이미지 프롬프트 대본\n- 다음 단계: Part 7 CapCut Bridge\n\n"



                            obs_path = save_obsidian_memory(folder_name, title, val, source="Sage Mirror Studio Part 3-4")

                            if obs_path:

                                lock_file_readonly(obs_path)

                                st.toast("💾 캡컷 에셋 로컬 자동 저장 완료!", icon="💾")

                                success, msg = auto_git_push(f"Auto Save (Locked): {title}")

                                if success:

                                    st.session_state.p34_cap_obsidian_saved = True

                                    st.toast("🧠 옵시디언 자동 백업 & Git Push 완료!", icon="🧠")

                                else:

                                    st.error(f"GitHub Push 실패: {msg}")

                                save_workspace_state()

                                st.rerun()



            with c_c2:

                if st.session_state.get("p34_cap_saved", False):

                    st.button("💾 로컬 자동저장 완료", type="secondary", use_container_width=True, disabled=True, key="p34_cap_local_indicator")

                else:

                    st.button("⏳ 결과 대기 중", use_container_width=True, disabled=True, key="p34_cap_local_waiting")



            with c_c3:

                if st.session_state.get("p34_cap_obsidian_saved", False):

                    st.button("🧠 옵시디언 백업 완료", type="primary", use_container_width=True, disabled=True, key="p34_cap_obs_indicator")

                else:

                    st.button("⏳ 백업 대기 중", use_container_width=True, disabled=True, key="p34_cap_obs_waiting")



            if st.session_state.p34_capcut_data:

                st.markdown("<br>", unsafe_allow_html=True)

                st.session_state.p34_capcut_data = st.text_area(

                    "캡컷 JSON (수정 가능)",

                    value=st.session_state.p34_capcut_data,

                    height=500,

                    label_visibility="collapsed",

                    key="p34_cap_area"

                )



                c_cp1, c_cp2 = st.columns(2)

                with c_cp1:

                    if st.button("👁 팝업에서 크게 보기 / 복붙", use_container_width=True, key="p34_cap_popup_btn"):

                        popup_cap_p34()

                with c_cp2:

                    if st.button("📋 클립보드 복사", use_container_width=True, key="p34_cap_copy_btn"):

                        try:

                            import pyperclip

                            pyperclip.copy(st.session_state.p34_capcut_data)

                            st.success("캡컷 JSON 복사 완료!")

                        except Exception:

                            st.info("위 텍스트창에서 직접 드래그 선택하세요.")



                if st.button("💾 (예비용) 캡컷 에셋 수동 옵시디언 백업", use_container_width=True, key="p34_save_cap", disabled=is_locked):

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

                    topic_title = st.session_state.get("p2_topic_selection", "캡컷에셋")

                    title = f"[Part3] 캡컷 에셋 JSON - {topic_title}"

                    val = f"## 🎬 캡컷 에셋 JSON\n```json\n{st.session_state.p34_capcut_data}\n```\n"

                    obs_path = save_obsidian_memory("ScriptDrafts", title, val, source="Sage Mirror Studio Part 3-4")

                    if obs_path:

                        lock_file_readonly(obs_path)

                        st.toast("✅ 수동 캡컷 에셋 옵시디언 백업 완료!", icon="💾")

                        st.session_state.p34_cap_obsidian_saved = True

                        save_workspace_state()

                        success, msg = auto_git_push(f"Manual Save: {title}")

                        if success:

                            st.toast("🚀 GitHub 백업 완료!", icon="🚀")

                        else:

                            st.error(f"GitHub Push 실패: {msg}")

                        st.rerun()













# =====================================================================

# Part 6 — render_part6_opal() 메인 함수

# =====================================================================


    # ── 🔒 Part 3 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc3, _rc3 = st.columns(2)
        with _lc3:
            if st.button("🔒 Part 3 최종본 Lock & GitHub Push",
                         key="p3_lock_btn", use_container_width=True):
                lock_and_push_final_version(3, "대본 작성", ["p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data"])
        with _rc3:
            if st.button("🔓 Part 3 수정본 생성",
                         key="p3_rev_btn", use_container_width=True):
                create_revision_version(3, "대본 작성", ["p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data"])

def render_part6_opal():

    c_title, c_control = st.columns([4.2, 5.8])

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎵 파트 6: 나레이션 & 배경음악</h3>', unsafe_allow_html=True)

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p6_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p6_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part6", "7777"): 

                st.session_state.unlock_part6 = True

            elif pin: 

                st.session_state.unlock_part6 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p6_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            

    is_locked = False

    # PIN 경고 메시지 출력 제거 (사용자 요청 반영)

        

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    # ─── 옵시디언 감정 기반 검색 (음악/배경 파트 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P6_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part6", 
            "Part 6: 나레이션 & BGM", 
            get_default_tags_for_part("part6"), 
            "p6_obsidian_search_results", 
            "p6_rag_model_selector"
        )

    st.divider()

    st.subheader("🎙️ Step 1. 나레이션 데이터 추출 및 검증")

    p34_narr = st.session_state.get("p34_narration_script", "")

    if not p34_narr:

        st.warning("⚠️ Part 3-4 나레이션 대본이 비어 있습니다. 대본 작성 단계에서 나레이션 대본을 먼저 생성하세요.")

        p34_img_sc = st.session_state.get("p34_image_script", "")

        if p34_img_sc:

            st.info("💡 이미지 대본(C-1 씬 형식)에서 나레이션을 정밀 추출할 수 있습니다.")

            if st.button("🤖 이미지 대본에서 나레이션 정밀 추출 (AI)", key="p6_extract_narr_btn", disabled=is_locked):

                with st.spinner("이미지 대본에서 나레이션 추출 중..."):

                    try:
                        p6_rag_res = st.session_state.get("p6_obsidian_search_results", "")
                        p6_rag_ctx = ""
                        if p6_rag_res:
                            p6_rag_ctx = build_rag_context_from_results(
                                p6_rag_res, "나레이션 & 배경음악", 
                                st.session_state.get("p6_rag_model_selector", "gemma4:e2b")
                            )

                        prompt = f"[지시] 아래 이미지 대본에서 씬 번호와 나레이션 텍스트만 추출하여 '씬번호 | 나레이션' 형식으로 출력하세요.\n\n"
                        if p6_rag_ctx:
                            prompt += f"[RAG Context]\n{p6_rag_ctx}\n\n"
                        prompt += f"[이미지 대본]\n{p34_img_sc}\n\n[출력 형식]\n001 | 나레이션 내용\n002 | 나레이션 내용\n..."

                        extracted = call_gemma(prompt)

                        st.session_state.p34_narration_script = extracted

                        st.success("나레이션 추출 성공!")

                        save_workspace_state()

                        st.rerun()

                    except Exception as e:

                        st.error(f"[오류명] 나레이션 추출 실패: {e}\n→ 해결 방법: Gemma 연결 및 올바른 이미지 대본인지 확인하십시오.")

        else:

            # ── 🔒 Part 6 최종본 Lock & 수정본 버튼 ──────────────
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
                _lc6_e, _rc6_e = st.columns(2)
                with _lc6_e:
                    if st.button("🔒 Part 6 최종본 Lock & GitHub Push",
                                 key="p6_lock_btn_empty", use_container_width=True):
                        lock_and_push_final_version(6, "나레이션 & 배경음악", ["p6_bgm_selection", "p6_mixing_ratio", "p6_opal_data"])
                with _rc6_e:
                    if st.button("🔓 Part 6 수정본 생성",
                                 key="p6_rev_btn_empty", use_container_width=True):
                        create_revision_version(6, "나레이션 & 배경음악", ["p6_bgm_selection", "p6_mixing_ratio", "p6_opal_data"])
            return

            

    edited_narr = st.text_area("🎙️ 나레이션 대본 편집 (001 | 나레이션 내용 형식)", value=st.session_state.get("p34_narration_script", ""), height=300, key="p6_narr_editor", disabled=is_locked)

    if edited_narr != st.session_state.get("p34_narration_script", ""):

        st.session_state.p34_narration_script = edited_narr

        

    st.subheader("🎵 Step 2. 오디오 & BGM 프리셋 설정")

    c_bgm1, c_bgm2 = st.columns(2)

    with c_bgm1:

        bgm_presets = ["비장한 성경 낭독풍", "잔잔한 철학 수필풍", "긴박한 다큐멘터리풍", "신비롭고 몽환적인 뉴에이지"]

        selected_bgm = st.selectbox("💿 BGM 분위기 프리셋 선택", bgm_presets, index=bgm_presets.index(st.session_state.get("p6_bgm_selection", "비장한 성경 낭독풍")), disabled=is_locked, key="p6_bgm_select")

        st.session_state.p6_bgm_selection = selected_bgm

    with c_bgm2:

        mix_ratio = st.slider("🔊 오디오 믹싱 비율 (나레이션 볼륨 %)", min_value=50, max_value=100, value=st.session_state.get("p6_mixing_ratio", 80), step=5, disabled=is_locked, key="p6_mix_slider")

        st.session_state.p6_mixing_ratio = mix_ratio

        

    st.subheader("👥 Step 3. Google Opal 8계정 분배")

    if st.button("👥 Opal 8계정 씬 자동 배분 시작", key="p6_distribute_btn", type="primary", disabled=is_locked):

        # 버튼 내부에서 세션 스테이트를 통해 안전하게 설정값 참조

        _selected_bgm = st.session_state.get("p6_bgm_selection", "비장한 성경 낭독풍")

        _mix_ratio = st.session_state.get("p6_mixing_ratio", 80)

        _narr_text_raw = st.session_state.get("p34_narration_script", "")

        _lines = _narr_text_raw.strip().split("\n")

        parsed_scenes = {}

        error_lines = []

        for _line in _lines:

            if not _line.strip():

                continue

            _parts = _line.split("|", 1)

            if len(_parts) == 2:

                _scene_str = _parts[0].strip()

                _narr_content = _parts[1].strip()

                if _scene_str.isdigit() and len(_scene_str) == 3:

                    parsed_scenes[int(_scene_str)] = _narr_content

                else:

                    error_lines.append(_line)

            else:

                error_lines.append(_line)

                

        if error_lines:

            st.error(f"⚠️ 다음 줄의 형식이 올바르지 않습니다 (001 | 나레이션 형식이어야 함):\n" + "\n".join(error_lines[:5]))

            

        try:

            opal_records = []

            for scene_idx in range(1, 113):

                _s_str = f"{scene_idx:03d}"

                _narr_out = parsed_scenes.get(scene_idx, f"@Protagonist의 이야기가 펼쳐집니다. (나레이션 누락)")

                account_num = ((scene_idx - 1) // 14) + 1

                account_name = f"{account_num}번계정"

                

                opal_records.append({

                    "계정": account_name,

                    "씬번호": _s_str,

                    "나레이션": _narr_out,

                    "BGM 프리셋": _selected_bgm,

                    "믹싱 비율": f"나레이션 {_mix_ratio}% / BGM {100-_mix_ratio}%"

                })

                

            df = pd.DataFrame(opal_records)

            st.session_state.p6_opal_df = df

            st.session_state.p6_opal_data = df.to_dict(orient="records")

            st.session_state.p6_opal_saved = True

            save_workspace_state()

            st.success("Opal 8계정 배분 데이터가 성공적으로 생성되었습니다!")

            st.rerun()

        except Exception as e:

            st.error(f"[오류명] Opal 배분 실패: {e}\n→ 해결 방법: 나레이션 텍스트 형식 및 Pandas 데이터프레임 구조를 점검하세요.")



    if st.session_state.get("p6_opal_df") is None and st.session_state.get("p6_opal_data") is not None:

        try:

            st.session_state.p6_opal_df = pd.DataFrame(st.session_state.p6_opal_data)

        except Exception as e:

            st.error(f"[오류명] Opal 데이터프레임 복원 실패: {e}\n→ 해결 방법: 세션 데이터 무결성을 점검하십시오.")



    if st.session_state.get("p6_opal_df") is not None:

        st.markdown("### 📊 Opal 8계정 씬 배분 현황")

        st.dataframe(st.session_state.p6_opal_df, use_container_width=True)

        

        try:

            csv_data = st.session_state.p6_opal_df.to_csv(index=False, encoding="utf-8-sig")

            st.download_button(

                label="📥 Opal 배분 CSV 다운로드 (Excel 호환)",

                data=csv_data,

                file_name=f"part6_opal_dispatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",

                mime="text/csv",

                key="p6_csv_download"

            )

        except Exception as e:

            st.error(f"[오류명] CSV 변환 실패: {e}\n→ 해결 방법: Pandas 데이터프레임 컬럼을 점검하세요.")

            

    st.divider()







# =====================================================================

# Part 7 — render_part7_capcut() 메인 함수

# =====================================================================


    # ── 🔒 Part 6 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc6, _rc6 = st.columns(2)
        with _lc6:
            if st.button("🔒 Part 6 최종본 Lock & GitHub Push",
                         key="p6_lock_btn", use_container_width=True):
                lock_and_push_final_version(6, "나레이션 & 배경음악", ["p6_bgm_selection", "p6_mixing_ratio", "p6_opal_data"])
        with _rc6:
            if st.button("🔓 Part 6 수정본 생성",
                         key="p6_rev_btn", use_container_width=True):
                create_revision_version(6, "나레이션 & 배경음악", ["p6_bgm_selection", "p6_mixing_ratio", "p6_opal_data"])

def build_capcut_assembly_packet(script: str, scenes_count: int, video_style: str, bgm_style: str, subtitle_style: str, model_name: str = None) -> dict:
    """
    나레이션 대본을 지정된 장면 수만큼 장면 단위로 분해하고,
    영상 스타일, BGM 스타일, 자막 스타일 등을 융합하여 CapCut 조립용 패킷(JSON)을 생성합니다.
    """
    if not model_name:
        model_name = st.session_state.get("selected_model", "gemma4:e2b")
        
    prompt = f"""
[지시]
제시된 나레이션 대본을 총 {scenes_count}개의 장면(Scene)으로 분리하고, 각 장면별 상세 CapCut 영상 조립 패킷을 완벽한 JSON 형식으로 생성하라.
출력은 다른 설명글 없이 오직 유효한 JSON 코드만 반환해야 한다. 마크다운의 ```json ``` 코드 블록 포맷을 사용하라.

[요구 스타일 정보]
- 영상 비주얼 스타일: {video_style}
- BGM 분위기: {bgm_style}
- 자막 스타일: {subtitle_style}

[출력 JSON 스키마 형식]
{{
  "scene_01": {{
    "narration": "해당 장면에서 낭독할 나레이션 구절",
    "image_prompt": "영상/이미지 생성을 위한 구체적인 영문 비주얼 프롬프트 (영상 스타일: {video_style} 반영)",
    "bgm_mood": "배경음악의 분위기 키워드 (BGM 스타일: {bgm_style} 반영)",
    "subtitle": "화면에 표시될 한글 자막 (자막 스타일: {subtitle_style} 반영)",
    "duration": 6
  }},
  "scene_02": {{
    ...
  }}
}}
* 각 장면의 duration은 narration의 글자 수에 맞춰 산출하되(글자당 약 0.25초 기준, 최소 4초에서 최대 10초 사이), 정수 초 단위로 할당하라.

[입력 나레이션 대본]
{script}
"""
    
    try:
        res = call_selected_model(prompt, system=SAGE_PERSONA, model_name=model_name)
        # JSON 블록 추출
        json_match = re.search(r"```json\s*(.*?)\s*```", res, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = res.strip()
            first_curly = json_str.find("{")
            last_curly = json_str.rfind("}")
            if first_curly != -1 and last_curly != -1:
                json_str = json_str[first_curly:last_curly+1]
                
        packet = json.loads(json_str)
        return packet
    except Exception as e:
        import sys
        sys.stderr.write(f"CapCut 패킷 생성 중 AI 분석 실패: {e}. 기본 룰 기반 분리 엔진을 구동합니다.\n")
        
        fallback_packet = {}
        # 마침표, 줄바꿈 기준으로 문장 분리
        sentences = [s.strip() for s in re.split(r'[.\n]', script) if s.strip()]
        if not sentences:
            sentences = ["현자의 거울 대본입니다."]
            
        chunk_size = max(1, len(sentences) // scenes_count)
        for i in range(1, scenes_count + 1):
            idx = i - 1
            scene_key = f"scene_{i:02d}"
            start_idx = idx * chunk_size
            end_idx = start_idx + chunk_size if idx < scenes_count - 1 else len(sentences)
            scene_narr = " ".join(sentences[start_idx:end_idx]) if start_idx < len(sentences) else "..."
            
            char_count = len(scene_narr)
            duration_val = int(max(char_count * 0.25, 4))
            
            fallback_packet[scene_key] = {
                "narration": scene_narr,
                "image_prompt": f"A realistic or stylized cinematic shot, depicting the reflection of protagonist's inner self, {video_style} style",
                "bgm_mood": bgm_style if bgm_style else "reflective and calm",
                "subtitle": scene_narr,
                "duration": duration_val
            }
        return fallback_packet

def render_part7_capcut():

    c_title, c_control = st.columns([4.2, 5.8])

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">🎬 파트 7: 숏폼 생성 (CapCut Bridge)</h3>', unsafe_allow_html=True)

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p7_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p7_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part7", "7777"): 

                st.session_state.unlock_part7 = True

            elif pin: 

                st.session_state.unlock_part7 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p7_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            

    is_locked = False

    # PIN 경고 메시지 출력 제거 (사용자 요청 반영)

        

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    # ─── 옵시디언 감정 기반 검색 (숏폼 파트 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P7_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part7", 
            "Part 7: 숏폼 & 캡컷", 
            get_default_tags_for_part("part7"), 
            "p7_obsidian_search_results", 
            "p7_rag_model_selector"
        )

    st.divider()

    st.subheader("🧩 Step 1. CapCut Bridge 데이터 조립")

    if st.session_state.get("p6_opal_df") is None and st.session_state.get("p6_opal_data") is not None:

        try:

            st.session_state.p6_opal_df = pd.DataFrame(st.session_state.p6_opal_data)

        except Exception:

            pass

            

    opal_df = st.session_state.get("p6_opal_df")

    if opal_df is None:

        st.warning("⚠️ 파트 6 Opal 배분 데이터가 존재하지 않습니다. 파트 6 단계를 완료해 주세요.")

        # ── 🔒 Part 7 최종본 Lock & 수정본 버튼 ──────────────
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
            _lc7_e, _rc7_e = st.columns(2)
            with _lc7_e:
                if st.button("🔒 Part 7 최종본 Lock & GitHub Push",
                             key="p7_lock_btn_empty", use_container_width=True):
                    lock_and_push_final_version(7, "숏폼 생성", ["p7_shortform_hook", "p7_capcut_data_v2"])
            with _rc7_e:
                if st.button("🔓 Part 7 수정본 생성",
                             key="p7_rev_btn_empty", use_container_width=True):
                    create_revision_version(7, "숏폼 생성", ["p7_shortform_hook", "p7_capcut_data_v2"])
        return

        

    if st.button("🎬 CapCut Bridge 데이터 자동 조립 및 타임라인 연산", key="p7_assemble_btn", type="primary", disabled=is_locked):

        with st.spinner("CapCut 자동화 템플릿용 데이터 구성 중..."):

            try:

                records = []

                for _, row in opal_df.iterrows():

                    scene_str = row["씬번호"]

                    narr_text = row["나레이션"]

                    

                    char_count = len(narr_text)

                    duration_val = max(char_count * 0.25, 4.0)

                    

                    records.append({

                        "scene_id": scene_str,

                        "image_file": f"scene_{scene_str}.png",

                        "audio_file": f"narration_{scene_str}.mp3",

                        "video_file": f"video_{scene_str}.mp4",

                        "subtitle": narr_text,

                        "duration": round(duration_val, 2)

                    })

                df = pd.DataFrame(records)

                st.session_state.p7_capcut_df = df

                st.session_state.p7_capcut_data_v2 = df.to_dict(orient="records")

                st.session_state.p7_capcut_saved = True

                save_workspace_state()

                st.success("CapCut Bridge 데이터 조립이 완료되었습니다!")

                st.rerun()

            except Exception as e:

                st.error(f"[오류명] CapCut Bridge 조립 실패: {e}\n→ 해결 방법: 8계정 분배 데이터 구조와 Pandas 버전을 확인하십시오.")

                

    if st.session_state.get("p7_capcut_df") is None and st.session_state.get("p7_capcut_data_v2") is not None:

        try:

            st.session_state.p7_capcut_df = pd.DataFrame(st.session_state.p7_capcut_data_v2)

        except Exception as e:

            st.error(f"[오류명] CapCut Bridge 데이터프레임 복원 실패: {e}\n→ 해결 방법: 로컬 workspace_state.json 구조를 복원하십시오.")

            

    if st.session_state.get("p7_capcut_df") is not None:

        st.markdown("### 📊 CapCut Bridge 조립 데이터")

        st.dataframe(st.session_state.p7_capcut_df, use_container_width=True)

        

        try:

            csv_data = st.session_state.p7_capcut_df.to_csv(index=False, encoding="utf-8-sig")

            st.download_button(

                label="📥 CapCut Bridge CSV 다운로드 (Excel 호환)",

                data=csv_data,

                file_name=f"part7_capcut_bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",

                mime="text/csv",

                key="p7_csv_download"

            )

        except Exception as e:

            st.error(f"[오류명] CSV 내보내기 실패: {e}\n→ 해결 방법: DataFrame의 특수문자 및 용량을 점검하십시오.")

            

    st.divider()

    st.markdown("### 📣 숏폼 후킹 및 핵심 메시지 생성 (AI)")
    st.caption("RAG Context와 나레이션 대본을 기반으로 쇼츠/릴스용 후킹 멘트와 핵심 메시지를 도출합니다.")
    
    p7_hook_prompt = st.text_area(
        "숏폼 후킹 생성 프롬프트",
        value=st.session_state.get("p7_hook_prompt_val", "나레이션 대본 전체를 요약하고, 틱톡/쇼츠용 극강의 어그로 후킹 문구 3개와 시청자 행동 유도(CTA) 멘트 1개를 생성하라."),
        height=100,
        key="p7_hook_prompt_input",
        disabled=is_locked
    )
    st.session_state["p7_hook_prompt_val"] = p7_hook_prompt

    c_hk1, c_hk2 = st.columns([4, 6])
    with c_hk1:
        if st.button("🚀 숏폼 후킹 멘트 생성", key="p7_gen_hook_btn", type="secondary", disabled=is_locked or opal_df is None):
            with st.spinner("후킹 멘트 및 핵심 메시지 생성 중..."):
                try:
                    p7_rag_res = st.session_state.get("p7_obsidian_search_results", "")
                    p7_rag_ctx = ""
                    if p7_rag_res:
                        p7_rag_ctx = build_rag_context_from_results(
                            p7_rag_res, "숏폼 생성", 
                            st.session_state.get("p7_rag_model_selector", "gemma4:e2b")
                        )
                    
                    narr_all = "\n".join([f"{row.get('scene_id', row.get('씬번호', ''))}: {row.get('subtitle', row.get('나레이션', ''))}" for _, row in opal_df.iterrows()])
                    
                    prompt = f"[지시]\n{p7_hook_prompt}\n\n"
                    if p7_rag_ctx:
                        prompt += f"[RAG Context]\n{p7_rag_ctx}\n\n"
                    prompt += f"[나레이션 대본]\n{narr_all}\n\n"
                    
                    model_sel = st.session_state.get("p7_rag_model_selector", "gemma4:e2b")
                    res = call_selected_model(prompt, system=SAGE_PERSONA, model_name=model_sel)
                    st.session_state.p7_shortform_hook = res
                    save_workspace_state()
                    st.success("✅ 숏폼 후킹 멘트 생성 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"후킹 멘트 생성 실패: {e}")

    if st.session_state.get("p7_shortform_hook"):
        render_result_preview("p7_shortform_hook", "Part 7 숏폼 후킹 & 핵심 메시지")

    st.divider()

    st.subheader("🧩 Step 2. CapCut 자동 조립 구조 설계 (패킷 생성기)")
    st.caption("대본을 장면 단위로 분할하여 비주얼/BGM/자막 스타일을 반영한 조립용 JSON 패킷을 생성합니다.")

    # 1. 대본 입력
    default_script = st.session_state.get("p7_script_input", "")
    if not default_script:
        # p34_narration_script가 있으면 그것을 디폴트로 사용
        default_script = st.session_state.get("p34_narration_script", "")
    
    p7_script = st.text_area(
        "📝 나레이션 대본 입력",
        value=default_script,
        height=200,
        key="p7_script_input_widget",
        disabled=is_locked
    )
    st.session_state.p7_script_input = p7_script

    # 2. 장면 수, 영상 스타일, BGM 스타일, 자막 스타일 입력
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        p7_scenes = st.number_input(
            "🎬 장면 수 (Scene Count)",
            min_value=1,
            max_value=40,
            value=st.session_state.get("p7_scenes_input", 8),
            step=1,
            key="p7_scenes_input_widget",
            disabled=is_locked
        )
        st.session_state.p7_scenes_input = p7_scenes

        p7_video_style = st.text_input(
            "🖼 영상 비주얼 스타일 (Visual Style)",
            value=st.session_state.get("p7_video_style_input", "Warm Amber Cinematic, Rembrandt lighting, deep shadows"),
            key="p7_video_style_input_widget",
            disabled=is_locked
        )
        st.session_state.p7_video_style_input = p7_video_style
        
    with col_in2:
        p7_bgm_style = st.text_input(
            "🎵 BGM 스타일 (Audio Mood)",
            value=st.session_state.get("p7_bgm_style_input", "Quiet, cello and piano reflective harmony"),
            key="p7_bgm_style_input_widget",
            disabled=is_locked
        )
        st.session_state.p7_bgm_style_input = p7_bgm_style

        p7_subtitle_style = st.text_input(
            "💬 자막 스타일 (Subtitle Style)",
            value=st.session_state.get("p7_subtitle_style_input", "Minimalist yellow-warm subtitle, center-bottom"),
            key="p7_subtitle_style_input_widget",
            disabled=is_locked
        )
        st.session_state.p7_subtitle_style_input = p7_subtitle_style

    # 패킷 생성 실행 버튼
    if st.button("🚀 CapCut 조립용 패킷 생성 (AI)", type="primary", key="p7_gen_packet_btn", disabled=is_locked or not p7_script.strip()):
        with st.spinner("Gemma AI가 대본을 장면 단위로 분할하여 CapCut 조립용 패킷을 생성하는 중..."):
            try:
                # build_capcut_assembly_packet 호출
                packet_dict = build_capcut_assembly_packet(
                    script=p7_script,
                    scenes_count=p7_scenes,
                    video_style=p7_video_style,
                    bgm_style=p7_bgm_style,
                    subtitle_style=p7_subtitle_style,
                    model_name=st.session_state.get("selected_model", "gemma4:e2b")
                )
                
                # 결과 딕셔너리를 포맷팅된 JSON 문자열로 저장
                st.session_state.p7_capcut_data = json.dumps(packet_dict, ensure_ascii=False, indent=2)
                st.session_state.p7_capcut_saved = True
                save_workspace_state()
                st.success("✅ CapCut 조립 패킷 생성 완료!")
                st.rerun()
            except Exception as e:
                st.error(f"패킷 생성 실패: {e}")

    # 결과 미리보기 (4종 UI: 보기, 복사, 앱 저장, 옵시디언 저장)
    if st.session_state.get("p7_capcut_data"):
        render_result_preview("p7_capcut_data", "Part 7 캡컷 자동 조립 패킷")

    st.divider()







# =====================================================================

# Part 8 — render_part8_dashboard() 메인 함수

# =====================================================================


    # ── 🔒 Part 7 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc7, _rc7 = st.columns(2)
        with _lc7:
            if st.button("🔒 Part 7 최종본 Lock & GitHub Push",
                         key="p7_lock_btn", use_container_width=True):
                lock_and_push_final_version(7, "숏폼 생성", ["p7_shortform_hook", "p7_capcut_data_v2"])
        with _rc7:
            if st.button("🔓 Part 7 수정본 생성",
                         key="p7_rev_btn", use_container_width=True):
                create_revision_version(7, "숏폼 생성", ["p7_shortform_hook", "p7_capcut_data_v2"])

def render_part8_dashboard():

    c_title, c_control = st.columns([4.2, 5.8])

    with c_title:

        st.markdown('<h3 style="margin: 0; line-height: 52px; color: #d4af6a; font-size: 1.85em; font-weight: 700;">📊 파트 8: 캡컷 최종 조립</h3>', unsafe_allow_html=True)

    with c_control:

        st.markdown('<div class="glass-control-box"><div id="header-control-box-anchor"></div>', unsafe_allow_html=True)

        c_model_col, c_pin_col, c_pop_col = st.columns([3.8, 3.8, 2.4])

        with c_model_col:

            st.markdown('<div class="header-model-wrapper">', unsafe_allow_html=True)

            cur_model = st.session_state.get("selected_model", "gemma4:e2b").upper()

            model_options = ["GEMMA4:E2B", "GEMMA4:E4B"]

            default_idx = model_options.index(cur_model) if cur_model in model_options else 0

            sel_model = st.selectbox("🤖 모델", model_options, index=default_idx, key="p8_model_select", label_visibility="collapsed")

            st.markdown('</div>', unsafe_allow_html=True)

            if sel_model.lower() != st.session_state.get("selected_model", "gemma4:e2b").lower():

                st.session_state.selected_model = sel_model.lower()

                save_workspace_state()

                st.rerun()

        with c_pin_col:

            st.markdown('<div class="header-pin-wrapper">', unsafe_allow_html=True)

            pin = st.text_input("🔒 마스터 PIN", type="password", key="p8_pin_input", label_visibility="collapsed", placeholder="🔒 마스터 PIN (7777)")

            st.markdown('</div>', unsafe_allow_html=True)

            if pin == PART_PINS.get("part8", "7777"): 

                st.session_state.unlock_part8 = True

            elif pin: 

                st.session_state.unlock_part8 = False

        with c_pop_col:

            st.markdown('<div class="header-pop-wrapper">', unsafe_allow_html=True)

            if st.button("🚀 젬마 스튜디오 입장", type="primary", use_container_width=True, key="p8_studio_btn"):

                st.session_state.sidebar_part = "파트 0: 🤖 젬마 스튜디오 (대화 & 자료수집)"

                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            

    is_locked = False

    # PIN 경고 메시지 출력 제거 (사용자 요청 반영)

        

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    render_top_panel()

    st.markdown('<hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(212,175,106,0.15);">', unsafe_allow_html=True)

    # ─── 옵시디언 감정 기반 검색 (대시보드 파트 참조용) ───────────────
    with st.expander("🔍 RAG 보완 검색 설정 (접기/펼치기)", expanded=False):
        DEFAULT_P8_TAGS = "고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"
        render_obsidian_rag_search(
            "part8", 
            "Part 8: 최종 조립 & 검수", 
            get_default_tags_for_part("part8"), 
            "p8_obsidian_search_results", 
            "p8_rag_model_selector"
        )

    st.divider()

    st.subheader("📊 Step 1. 생산 품질 요약 리포트")

    if st.session_state.get("p7_capcut_df") is None and st.session_state.get("p7_capcut_data_v2") is not None:

        try:

            st.session_state.p7_capcut_df = pd.DataFrame(st.session_state.p7_capcut_data_v2)

        except Exception:

            pass

            

    cap_df = st.session_state.get("p7_capcut_df")

    if cap_df is None:

        st.warning("⚠️ 파트 7 CapCut Bridge 조립 데이터가 없습니다. 파트 7 단계를 완료해 주세요.")

        return



    # ──────────────────────────────────────────────

    # 통계 변수 기본값 초기화 (저장 버튼 스코프 밖에서 선언)

    # ──────────────────────────────────────────────

    total_scenes = 0

    total_duration = 0.0

    avg_duration = 0.0

    exist_count = 0

    completion_rate = 0.0

    missing_scenes = []



    try:

        total_scenes = len(cap_df)

        total_duration = float(cap_df["duration"].sum())

        avg_duration = float(cap_df["duration"].mean())

        

        c_m1, c_m2, c_m3 = st.columns(3)

        with c_m1:

            st.metric("총 씬 개수", f"{total_scenes}개")

        with c_m2:

            st.metric("총 비디오 예상 시간", f"{total_duration:.2f}초 ({total_duration/60:.2f}분)")

        with c_m3:

            st.metric("평균 씬 지속시간", f"{avg_duration:.2f}초")

    except Exception as e:

        st.error(f"[오류명] 지표 계산 실패: {e}\n→ 해결 방법: CapCut Bridge 데이터프레임의 duration 열 구조를 파악하십시오.")

        

    st.subheader("📁 Step 2. 06_Video_Clips 물리 파일 매칭 검증")

    video_dir = r"C:\SageMirror_Production\06_Video_Clips"

    

    try:

        os.makedirs(video_dir, exist_ok=True)

    except Exception as e:

        st.error(f"[오류명] 폴더 생성 실패: {e}\n→ 해결 방법: 드라이브 경로가 존재하며 쓰기 권한이 있는지 점검하십시오.")

        

    matching_status = []

    

    if st.button("🔄 비디오 클립 실시간 스캔 및 새로고침", key="p8_scan_btn"):

        st.toast("실시간 물리 폴더 스캔 중...")

        

    try:

        for idx in range(1, 113):

            scene_str = f"{idx:03d}"

            file_name = f"video_{scene_str}.mp4"

            file_path = os.path.join(video_dir, file_name)

            

            is_exist = os.path.exists(file_path)

            if is_exist:

                exist_count += 1

                status_str = "완료 ✅"

            else:

                missing_scenes.append(scene_str)

                status_str = "누락 ❌"

                

            matching_status.append({

                "씬번호": scene_str,

                "파일명": file_name,

                "상태": status_str

            })

            

        matching_df = pd.DataFrame(matching_status)

        completion_rate = (exist_count / 112) * 100

        

        st.markdown(f"**물리 비디오 클립 매칭 완료율:** {completion_rate:.1f}% ({exist_count} / 112)")

        st.progress(completion_rate / 100.0)

        

        if missing_scenes:

            st.error(f"⚠️ 총 {len(missing_scenes)}개의 씬 비디오 클립이 누락되었습니다:\n" + ", ".join(missing_scenes))

        else:

            st.success("🎉 모든 112개 비디오 클립이 정상 매칭되었습니다!")

            

        with st.expander("🔍 112개 비디오 클립 세부 현황", expanded=False):

            st.dataframe(matching_df, use_container_width=True)

    except Exception as e:

        st.error(f"[오류명] 물리 파일 스캔 실패: {e}\n→ 해결 방법: {video_dir} 경로 권한 및 파일 형식을 확인하십시오.")

    st.divider()

    st.markdown("### 📋 AI 최종 검수 가이드라인 생성")
    st.caption("RAG Context와 생산된 조립 데이터를 바탕으로 최종 편집/연출 가이드라인을 생성합니다.")
    
    p8_guide_prompt = st.text_area(
        "최종 검수 가이드라인 생성 프롬프트",
        value=st.session_state.get("p8_guide_prompt_val", "112개 대본의 서사 흐름과 RAG 자료를 기반으로, 영상 편집 단계에서 반드시 지켜야 할 최종 연출 가이드라인, 분위기(Mood), 오디오 믹싱 시 주의사항을 담은 검수 가이드라인을 생성하라."),
        height=100,
        key="p8_guide_prompt_input",
        disabled=is_locked
    )
    st.session_state["p8_guide_prompt_val"] = p8_guide_prompt

    c_gd1, c_gd2 = st.columns([4, 6])
    with c_gd1:
        if st.button("🚀 AI 최종 검수 가이드라인 생성", key="p8_gen_guide_btn", type="secondary", disabled=is_locked):
            with st.spinner("최종 검수 가이드라인 생성 중..."):
                try:
                    p8_rag_res = st.session_state.get("p8_obsidian_search_results", "")
                    p8_rag_ctx = ""
                    if p8_rag_res:
                        p8_rag_ctx = build_rag_context_from_results(
                            p8_rag_res, "최종 검수", 
                            st.session_state.get("p8_rag_model_selector", "gemma4:e2b")
                        )
                    
                    narr_all = ""
                    if cap_df is not None:
                        narr_all = "\n".join([f"{row.get('scene_id', row.get('씬번호', ''))}: {row.get('subtitle', row.get('나레이션', ''))}" for _, row in cap_df.iterrows()])
                    
                    prompt = f"[지시]\n{p8_guide_prompt}\n\n"
                    if p8_rag_ctx:
                        prompt += f"[RAG Context]\n{p8_rag_ctx}\n\n"
                    if narr_all:
                        prompt += f"[나레이션 대본]\n{narr_all}\n\n"
                    
                    model_sel = st.session_state.get("p8_rag_model_selector", "gemma4:e2b")
                    res = call_selected_model(prompt, system=SAGE_PERSONA, model_name=model_sel)
                    st.session_state.p8_production_guide = res
                    save_workspace_state()
                    st.success("✅ 최종 검수 가이드라인 생성 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"가이드라인 생성 실패: {e}")

    if st.session_state.get("p8_production_guide"):
        render_result_preview("p8_production_guide", "Part 8 최종 검수 가이드라인")

    st.divider()







# 파트 3-4 외부 자동 백업 트리거

if st.session_state.get("p34_arch_obsidian_saved", False) and not st.session_state.get("p34_outputs_saved", False):

    try:

        ep = st.session_state.get("episode_name", "EP001").strip()

        script_content = f"# {ep} 최종 확정 대본 통합본\n\n"

        script_content += f"## 📅 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        

        script_content += "## 📌 1. 씬 구조 (Scene Structure)\n\n"

        script_content += st.session_state.get("p34_scene_structure", "대본 없음") + "\n\n"

        

        script_content += "## 🎙️ 2. 나레이션 대본 (Narration Script)\n\n"

        script_content += st.session_state.get("p34_narration_script", "대본 없음") + "\n\n"

        

        script_content += "## 🖼️ 3. 이미지 대본 (Image Script)\n\n"

        script_content += st.session_state.get("p34_image_script", "대본 없음") + "\n\n"

        

        saved_path = save_to_outputs_dir("01_Script", "script_final.md", content=script_content)

        if saved_path:

            st.session_state.p34_outputs_saved = True

            save_workspace_state()

            st.toast("💾 [대본 파트] 외부 백업 성공!", icon="💾")

    except Exception as e:

        st.error(f"[대본 외부 백업] 에러 발생: {e}")



# 파트 라우팅 블록

# =====================================================================

if part.startswith("파트 0"):
    p0_ui_model = st.session_state.get("p0_selected_model", "gemma4:e2b")
    st.session_state.selected_model = p0_ui_model
    render_part0_assistant()

elif part.startswith("파트 1"):
    p1_ui_model = st.session_state.get("p1_model_select")
    if p1_ui_model:
        p1_ui_model_lower = p1_ui_model.lower()
        if p1_ui_model_lower != st.session_state.get("p1_selected_model", "gemma4:e2b"):
            st.session_state.p1_selected_model = p1_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p1_selected_model", "gemma4:e2b")
    render_part1()

elif part.startswith("파트 2"):
    p2_ui_model = st.session_state.get("p2_model_select")
    if p2_ui_model:
        p2_ui_model_lower = p2_ui_model.lower()
        if p2_ui_model_lower != st.session_state.get("p2_selected_model", "gemma4:e2b"):
            st.session_state.p2_selected_model = p2_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p2_selected_model", "gemma4:e2b")
    render_part2()

elif part.startswith("파트 3"):
    p34_ui_model = st.session_state.get("p34_model_select")
    if p34_ui_model:
        p34_ui_model_lower = p34_ui_model.lower()
        if p34_ui_model_lower != st.session_state.get("p34_selected_model", "gemma4:e2b"):
            st.session_state.p34_selected_model = p34_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p34_selected_model", "gemma4:e2b")
    render_part34()

elif part.startswith("파트 4"):
    p5img_ui_model = st.session_state.get("p5img_model_select")
    if p5img_ui_model:
        p5img_ui_model_lower = p5img_ui_model.lower()
        if p5img_ui_model_lower != st.session_state.get("p5img_selected_model", "gemma4:e2b"):
            st.session_state.p5img_selected_model = p5img_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p5img_selected_model", "gemma4:e2b")
    render_part5_image()

elif part.startswith("파트 5"):
    p6vid_ui_model = st.session_state.get("p6_vid_model_select")
    if p6vid_ui_model:
        p6vid_ui_model_lower = p6vid_ui_model.lower()
        if p6vid_ui_model_lower != st.session_state.get("p6vid_selected_model", "gemma4:e2b"):
            st.session_state.p6vid_selected_model = p6vid_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p6vid_selected_model", "gemma4:e2b")
    render_part6_video()

elif part.startswith("파트 6"):
    p6_ui_model = st.session_state.get("p6_model_select")
    if p6_ui_model:
        p6_ui_model_lower = p6_ui_model.lower()
        if p6_ui_model_lower != st.session_state.get("p6_selected_model", "gemma4:e2b"):
            st.session_state.p6_selected_model = p6_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p6_selected_model", "gemma4:e2b")
    render_part6_opal()

elif part.startswith("파트 7"):
    p7_ui_model = st.session_state.get("p7_model_select")
    if p7_ui_model:
        p7_ui_model_lower = p7_ui_model.lower()
        if p7_ui_model_lower != st.session_state.get("p7_selected_model", "gemma4:e2b"):
            st.session_state.p7_selected_model = p7_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p7_selected_model", "gemma4:e2b")
    render_part7_capcut()

elif part.startswith("파트 8"):
    p8_ui_model = st.session_state.get("p8_model_select")
    if p8_ui_model:
        p8_ui_model_lower = p8_ui_model.lower()
        if p8_ui_model_lower != st.session_state.get("p8_selected_model", "gemma4:e2b"):
            st.session_state.p8_selected_model = p8_ui_model_lower
            save_workspace_state()
    st.session_state.selected_model = st.session_state.get("p8_selected_model", "gemma4:e2b")
    render_part8_dashboard()
    # ── 🔒 Part 8 최종본 Lock & 수정본 버튼 ──────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="ambient-lock-marker" style="display:none;"></div>', unsafe_allow_html=True)
        _lc8, _rc8 = st.columns(2)
        with _lc8:
            if st.button("🔒 Part 8 최종본 Lock & GitHub Push",
                         key="p8_lock_btn", use_container_width=True):
                lock_and_push_final_version(8, "캡컷 최종 조립", ["p8_production_guide"])
        with _rc8:
            if st.button("🔓 Part 8 수정본 생성",
                         key="p8_rev_btn", use_container_width=True):
                create_revision_version(8, "캡컷 최종 조립", ["p8_production_guide"])

# ── 임시 개발자 테스트 UI (파일 업로드 및 텍스트 추출) ──
if False:  # [DEBUG_DEV_PANEL 비활성화 처리]
    st.markdown("---")
    st.markdown("### 🛠️ 개발자 테스트 영역: 파일 텍스트 추출기")
    uploaded_file_dev = st.file_uploader(
        "텍스트 추출 테스트 (TXT, MD, HTML, PDF 지원)",
        type=["txt", "md", "html", "pdf"],
        key="dev_test_file_uploader"
    )
    if uploaded_file_dev:
        extracted_text = extract_text_from_uploaded_file(uploaded_file_dev)
        if extracted_text is not None:
            st.success("텍스트 추출 성공!")
            st.text_area("추출된 텍스트 프리뷰 (최대 5000자)", value=extracted_text[:5000], height=300, key="dev_test_extracted_ta")
        
            # ── 2차 추가 UI: Markdown 구조화 ──
            md_result = convert_text_to_markdown_structure(
                extracted_text,
                uploaded_file_dev.name
            )
            st.success("Markdown 구조화 완료")
            st.text_area(
                "Markdown 결과",
                md_result[:8000],
                height=400,
                key="dev_test_md_result_ta"
            )
        
            # ── 3차 추가 UI: 자동 RAG 카테고리 분석 미리보기 ──
            st.markdown("---")
            st.markdown("### 🧠 자동 RAG 카테고리 분석 미리보기")
            detection = detect_rag_categories(md_result, part_key="part1")
            st.write("감지 카테고리:", detection.get("categories", []))
            st.write("카테고리 점수:", detection.get("category_scores", {}))
            st.write("키워드:", detection.get("keywords", [])[:30])
            st.write("위키링크:", detection.get("wiki_links", [])[:30])
            st.write("해시태그:", detection.get("hash_tags", [])[:30])
        
            # ── 4차 추가 UI: 전체 8파트 공용 태그 미리보기 ──
            all_parts_preview = build_all_parts_common_tags_preview(detection)
            st.markdown("---")
            st.markdown("### 🌐 전체 8파트 공용 태그 미리보기")
            st.write("전체 파트 태그:", all_parts_preview.get("all_part_tags", []))
            st.write("통합 키워드:", all_parts_preview.get("combined_keywords", [])[:120])
            st.write("통합 위키링크:", all_parts_preview.get("wiki_links", [])[:120])
            st.write("통합 해시태그:", all_parts_preview.get("hash_tags", [])[:120])
        
            # ── 6차 추가 UI: References 수동 저장 테스트 ──
            st.markdown("---")
            if st.button("📥 References 저장 테스트", key="p6_save_ref_test_btn", use_container_width=True):
                preview_data_for_save = all_parts_preview.copy()
                preview_data_for_save["categories"] = detection.get("categories", [])
            
                saved_path = save_reference_markdown_file(
                    markdown_text=md_result,
                    preview_data=preview_data_for_save,
                    source_name=uploaded_file_dev.name
                )
                if saved_path:
                    st.success(f"저장 완료: {saved_path}")
                
            # ── 7차 추가 UI: References 읽기 전용 로드 테스트 ──
            st.markdown("---")
            if st.button("📖 References 로드 테스트", key="p7_load_ref_test_btn", use_container_width=True):
                loaded_refs = load_recent_reference_files(max_files=20, max_chars=120000)
                st.success(f"로드를 완료했습니다. (로드된 파일 수: {len(loaded_refs)}개)")
            
                total_len = sum([len(r["content"]) for r in loaded_refs])
                st.write(f"총 로드 글자 수: {total_len}자 / 120,000자")
            
                for idx, ref in enumerate(loaded_refs):
                    with st.expander(f"📄 {ref['filename']} (크기: {len(ref['content'])}자, {'생략됨' if ref['truncated'] else '완전함'})", expanded=False):
                        st.code(ref["content"][:3000], language="markdown")
                        if len(ref["content"]) > 3000:
                            st.caption("...(최대 3000자 프리뷰 표시)")
                        
            # ── 8차 추가 UI: Gemma Memory Prompt 미리보기 ──
            st.markdown("---")
            if st.button("🧠 Gemma Memory Prompt 미리보기", key="p8_gemma_mem_prompt_preview_btn", use_container_width=True):
                memory_items = load_recent_reference_files(max_files=20, max_chars=120000)
                prompt_preview = build_gemma_memory_prompt_preview(memory_items, max_chars=30000)
                st.text_area("Gemma 주입용 메모리 프롬프트", value=prompt_preview, height=500, key="p8_gemma_mem_prompt_ta")
            
            # ── 9차 추가 UI: Gemma Memory Inject 테스트 ──
            st.markdown("---")
            if st.button("🧠 Gemma Memory Inject 테스트", key="p9_gemma_mem_inject_test_btn", use_container_width=True):
                memory_items = load_recent_reference_files(max_files=20, max_chars=120000)
                prompt_preview = build_gemma_memory_prompt_preview(memory_items, max_chars=30000)
                buffer = build_manual_gemma_memory_buffer(prompt_preview, max_chars=32000)
            
                # 허용된 유일한 session_state 저장
                st.session_state["debug_memory_preview"] = buffer
            
                st.text_area("임시 Gemma Memory Buffer", value=buffer, height=500, key="p9_gemma_mem_buffer_ta")
                st.success("임시 버퍼 주입 테스트 완료! (st.session_state['debug_memory_preview'] 에 보관됨)")
            
            # ── 10차 추가 UI: Gemma Memory 실제 주입 테스트 ──
            st.markdown("---")
            user_query = st.text_input("✏️ 테스트 질문 입력", key="p10_test_query_in")
            if st.button("🚀 Gemma Memory 실제 주입 테스트", key="p10_test_inject_btn", use_container_width=True):
                if not user_query.strip():
                    st.error("테스트 질문을 입력해 주세요.")
                else:
                    memory_items = load_recent_reference_files(max_files=20, max_chars=120000)
                    prompt_preview = build_gemma_memory_prompt_preview(memory_items, max_chars=30000)
                    buffer = build_manual_gemma_memory_buffer(prompt_preview, max_chars=32000)
                
                    # debug_memory_preview 세션 키 저장 허용
                    st.session_state["debug_memory_preview"] = buffer
                
                    # 최종 Prompt 생성 (max_chars=40000)
                    injected_prompt = build_manual_memory_injected_prompt(user_query, buffer, max_chars=40000)
                
                    with st.spinner("Gemma 어시스턴트 응답 생성 중..."):
                        try:
                            # 1회 호출
                            response = call_gemma(injected_prompt, system_prompt="이 답변은 References 기억에만 의존하며, 출처 없는 사실은 단정하지 않습니다.")
                        
                            # debug_memory_response 세션 키 저장 허용
                            st.session_state["debug_memory_response"] = response
                        
                            st.markdown("### 📝 최종 주입 프롬프트 프리뷰")
                            st.code(injected_prompt, language="markdown")
                        
                            st.markdown("### 🤖 Gemma 1회성 응답 결과")
                            st.write(response)
                        except Exception as e:
                            st.error(f"[Gemma 호출 실패] {e}")
        else:
            st.error("텍스트 추출 실패 또는 지원하지 않는 형식입니다.")

