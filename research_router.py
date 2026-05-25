# -*- coding: utf-8 -*-
"""
research_router.py — Agent Layer Research Router (비-UI 코어 검색 관리 모듈) v1.0
이 모듈은 순수 Python 모듈로 작성되었으며 Streamlit UI 의존성이 전혀 없습니다.
"""

import re
import json
from datetime import datetime

# 1. NEED_RESEARCH 판단 및 검색어 추출
def should_trigger_research(text: str) -> str | None:
    """
    텍스트 본문에서 [NEED_RESEARCH: 검색어] 형태의 태그가 있는지 감지하고
    검색할 핵심 키워드를 반환합니다.
    """
    if not text or not isinstance(text, str):
        return None
    match = re.search(r"\[NEED_RESEARCH:\s*(.+?)\]", text)
    if match:
        return match.group(1).strip()
    return None

# 2. Tavily 검색 래퍼
def run_tavily_research(query: str, api_key: str, max_results: int = 5) -> dict:
    """
    tavily_search API를 호출하여 웹 검색 결과를 가져옵니다.
    에러 발생 시 {"error": "에러 내용"}을 반환합니다.
    """
    if not api_key:
        return {"error": "Tavily API Key가 제공되지 않았습니다."}
    try:
        from sage_engine import tavily_search
        res = tavily_search(query, api_key, max_results=max_results)
        if not res:
            return {"error": "검색 결과가 비어 있습니다."}
        return res
    except Exception as e:
        return {"error": str(e)}

# 3. 검색어 정리 및 정화
def clean_search_query(query: str) -> str:
    """
    검색어에 포함될 수 있는 필요 없는 개행이나 특수 문자들을 필터링하고 공백을 정돈합니다.
    """
    if not query or not isinstance(query, str):
        return ""
    # 개행 제거
    cleaned = query.replace("\n", " ").replace("\r", " ")
    # 불필요한 NEED_RESEARCH 대괄호 감싸기 해제
    cleaned = re.sub(r"\[NEED_RESEARCH:\s*(.+?)\]", r"\1", cleaned)
    # 다중 공백 제거
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()

# 4. 검색 결과 포맷터 (Tavily 결과 등)
def format_search_results_markdown(web_results: list) -> str:
    """
    Tavily 등 웹 검색 결과 리스트([{title, url, content}])를 깔끔한 마크다운 텍스트로 가공합니다.
    """
    if not web_results:
        return ""
    formatted_items = []
    for idx, r in enumerate(web_results, 1):
        title = r.get("title", "제목 없음").strip()
        url = r.get("url", "").strip()
        content = r.get("content", "").strip()
        formatted_items.append(
            f"[{idx}] 제목: {title}\nURL: {url}\n내용: {content}"
        )
    return "\n\n".join(formatted_items)

# 5. Tavily 결과 context builder
def build_tavily_rag_context_core(search_history: list) -> str:
    """
    최근 Tavily 검색 이력 목록을 기반으로 젬마에 주입할 컨텍스트 텍스트를 작성합니다.
    """
    if not search_history:
        return ""
    ctx = "\n[인터넷 리서치 자료 (Tavily — 자동 수집)]\n"
    for item in search_history[-5:]:  # 최근 5개 검색 참조
        q = item.get("q", "")
        res = item.get("res", {})
        ctx += f"\n🔎 검색어: {q}\n"
        if res.get("answer"):
            ctx += f"  즉시답변: {res['answer'][:200]}\n"
        for r in res.get("results", [])[:3]:
            ctx += f"  - [{r.get('title','')}]: {r.get('content','')[:200]}\n"
            ctx += f"    [SOURCE: {r.get('url','')}]\n"
        if res.get("gemma_analysis"):
            ctx += f"  젬마 분석: {res['gemma_analysis'][:300]}\n"
    return ctx

# 6. Gemini 검색 결과 context builder
def build_gemini_search_context_core(grounding_results: list, summary: str = "") -> str:
    """
    Gemini 구글 서치 그라운딩의 검색 결과를 받아 RAG 컨텍스트 텍스트로 가공합니다.
    """
    ctx = "\n[실시간 구글 검색 결과 (Gemini Grounding)]\n"
    if summary:
        ctx += f"요약 정보: {summary}\n"
    if grounding_results:
        for idx, r in enumerate(grounding_results, 1):
            title = r.get("title", "제목 없음")
            url = r.get("url", "")
            content = r.get("content", "")
            ctx += f"[{idx}] {title}\n  - URL: {url}\n"
            if content:
                ctx += f"  - 내용: {content[:200]}\n"
    else:
        ctx += "(검색 상세 결과 없음)\n"
    return ctx

# 7. YouTube 검색 결과 context builder
def build_youtube_search_context_core(yt_results: list) -> str:
    """
    유튜브 검색 결과 리스트를 받아 RAG 컨텍스트로 가공합니다.
    """
    if not yt_results:
        return ""
    ctx = "\n[유튜브 검색 자료]\n"
    for idx, r in enumerate(yt_results, 1):
        title = r.get("title", "제목 없음")
        video_id = r.get("video_id", "")
        desc = r.get("description", "")
        ch_title = r.get("channel_title", "")
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else "링크 없음"
        ctx += f"[{idx}] {title}\n  - 채널: {ch_title}\n  - 링크: {url}\n"
        if desc:
            ctx += f"  - 설명: {desc[:150]}\n"
    return ctx

# 8. Research markdown builder
def build_research_markdown_document(
    query: str,
    obs_results: list,
    web_search_text: str,
    final_summary: str,
    model_name: str,
    part_key: str,
    part_label: str,
    classification_md: str
) -> str:
    """
    Part RAG 검색 결과 저장용 최종 마크다운 문서를 빌드합니다.
    """
    part_num = part_key[-1] if part_key and len(part_key) > 0 else "1"
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md_content = f"# [[Part {part_num} RAG 검색 — {query}]]\n\n"
    md_content += f"## 📌 검색 목적\n{part_label} 작업 보완용 옵시디언 RAG 검색\n\n"
    md_content += f"## 🔎 검색 키워드\n{query}\n\n"
    md_content += f"## 🤖 사용 모델\n{model_name}\n\n"
    md_content += classification_md + "\n"
    
    md_content += "## 📚 옵시디언 검색 결과\n"
    if obs_results:
        for idx, r in enumerate(obs_results, 1):
            md_content += f"- **제목**: {r.get('title')}\n"
            md_content += f"  - **경로**: {r.get('path')}\n"
            md_content += f"  - **요약**: {r.get('preview', '')[:200].strip()}...\n"
    else:
        md_content += "- 검색 결과 없음\n"
    md_content += "\n"
    
    md_content += "## 🌐 보완 웹 리서치 결과\n"
    if web_search_text:
        md_content += f"```text\n{web_search_text}\n```\n"
    else:
        md_content += "- 웹 검색 결과 없음\n"
    md_content += "\n"
    
    md_content += "## 🤖 최종 요약 및 검수\n"
    md_content += f"{final_summary}\n\n"
    md_content += f"*[SOURCE: RAG 통합 리서치 — {model_name} 분석, {today_str}]*\n"
    
    return md_content

# 9. Source citation formatter
def format_source_citation(url: str, title: str = "", author: str = "", date_str: str = "") -> str:
    """
    [SOURCE: ...] 인용구 표기를 표준화하여 생성합니다.
    """
    if not url:
        return "[SOURCE: 출처 미확인]"
    
    today_str = date_str if date_str else datetime.now().strftime("%Y-%m-%d")
    
    if "bible" in url.lower() or "성경" in url:
        return f"[SOURCE: 성경 — {title if title else '구절'}]"
    
    if "philosophy" in url.lower() or "철학" in url:
        author_part = f" — {author}" if author else ""
        return f"[SOURCE: {title if title else '철학 인용'}{author_part}]"
        
    title_part = f" — {title}" if title else ""
    return f"[SOURCE: {url}{title_part} — 검색일: {today_str}]"
