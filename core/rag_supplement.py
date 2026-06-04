# -*- coding: utf-8 -*-
"""
core/rag_supplement.py — RAG 충분도 판단 + Tavily 자동 보완

작동 흐름:
1. 옵시디언 RAG 검색
2. 충분도 자동 평가 (SUFFICIENT / INSUFFICIENT / EMPTY)
3. 부족 시 Tavily 자동 보완 (백그라운드)
4. 옵시디언 듀얼 자동 저장
5. RAG 재검색 (이제 풍부함)
"""

import requests
import streamlit as st
from datetime import datetime
from core.obsidian import search_rag, save_dual


# ── 충분도 평가 ────────────────────────────────
def evaluate_rag_sufficiency(rag_result: str, query: str = "") -> dict:
    """RAG 결과가 충분한지 자동 판단"""
    
    if not rag_result or len(rag_result.strip()) == 0:
        return {
            "status":  "EMPTY",
            "score":   0,
            "files":   0,
            "message": "옵시디언에 관련 자료 없음",
            "needs_supplement": True,
        }
    
    file_count = rag_result.count("[")
    total_chars = len(rag_result)
    
    if file_count < 3 or total_chars < 500:
        return {
            "status":  "INSUFFICIENT",
            "score":   0.3,
            "files":   file_count,
            "message": f"자료 {file_count}건 (부족 — 자동 보완 권장)",
            "needs_supplement": True,
        }
    
    if "Gemma 추론" in rag_result and total_chars < 1000:
        return {
            "status":  "WEAK",
            "score":   0.5,
            "files":   file_count,
            "message": "추론 위주 (출처 보강 권장)",
            "needs_supplement": True,
        }
    
    return {
        "status":  "SUFFICIENT",
        "score":   1.0,
        "files":   file_count,
        "message": f"충분 ({file_count}건 자료 확보)",
        "needs_supplement": False,
    }


# ── Tavily 자동 보완 ────────────────────────────
def tavily_search(query: str, api_key: str, max_results: int = 5) -> list:
    """Tavily 웹 검색"""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return []
        return resp.json().get("results", [])
    except Exception as e:
        st.error(f"Tavily 오류: {e}")
        return []


def auto_supplement_rag(query: str, part_num: int = None,
                        api_key: str = None) -> dict:
    """RAG 자동 보완 — Tavily 검색 + 옵시디언 저장"""
    
    if not api_key:
        api_key = st.session_state.get("api_tavily", "")
    
    if not api_key:
        return {
            "success": False,
            "message": "Tavily API 키 필요",
            "saved_count": 0,
        }
    
    # 1. Tavily 검색
    results = tavily_search(query, api_key, max_results=5)
    
    if not results:
        return {
            "success": False,
            "message": "Tavily 결과 없음",
            "saved_count": 0,
        }
    
    # 2. 결과 자동 옵시디언 저장
    saved_count = 0
    for item in results:
        title = item.get("title", "보완자료")
        content = item.get("content", "")
        url = item.get("url", "")
        
        if not content or len(content) < 50:
            continue
        
        full_content = f"""
{content}

[원문 출처] {url}
[자동 수집] {datetime.now().strftime('%Y-%m-%d %H:%M')}
[수집 키워드] {query}
"""
        
        try:
            save_dual(
                content=full_content,
                title=f"[자동수집] {title[:50]}",
                part_num=part_num,
                source_type="Tavily 자동 보완",
            )
            saved_count += 1
        except Exception as e:
            print(f"[저장 실패] {e}")
    
    return {
        "success": True,
        "message": f"{saved_count}건 자동 수집·저장 완료",
        "saved_count": saved_count,
        "query": query,
    }


# ── 통합 함수: 검색 → 평가 → 보완 → 재검색 ────────
def smart_rag_search(query: str, part_num: int = None,
                     auto_supplement: bool = True,
                     max_files: int = 5) -> dict:
    """스마트 RAG 검색 (자동 보완 포함)"""
    
    # 1차 검색
    initial_result = search_rag(query, max_files=max_files)
    evaluation = evaluate_rag_sufficiency(initial_result, query)
    
    response = {
        "query":      query,
        "rag_result": initial_result,
        "evaluation": evaluation,
        "supplemented": False,
    }
    
    if not evaluation["needs_supplement"] or not auto_supplement:
        return response
    
    # 자동 보완 실행
    supplement = auto_supplement_rag(query, part_num=part_num)
    response["supplement"] = supplement
    
    if supplement["success"] and supplement["saved_count"] > 0:
        # 보완 후 재검색
        new_result = search_rag(query, max_files=max_files)
        new_evaluation = evaluate_rag_sufficiency(new_result, query)
        
        response["rag_result"] = new_result
        response["evaluation"] = new_evaluation
        response["supplemented"] = True
    
    return response
