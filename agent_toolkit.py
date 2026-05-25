# -*- coding: utf-8 -*-
"""
agent_toolkit.py — Agent Layer Tool Toolkit (비-UI 에이전트 도구 실행 보조 및 결과 포맷팅 모듈) v1.0
이 모듈은 순수 Python 모듈로 작성되었으며 Streamlit UI 의존성이 전혀 없습니다.
"""

import re
from datetime import datetime

# 지원 도구 목록 및 정규식 패턴 사전 반환 함수
def get_supported_agent_tools() -> dict:
    """
    에이전트가 지원하는 도구와 해당 정규식 패턴 딕셔너리를 반환합니다.
    """
    return {
        "NEED_RESEARCH":  r"\[NEED_RESEARCH:\s*(.+?)\]",
        "READ_OBSIDIAN":  r"\[READ_OBSIDIAN:\s*(.+?)\]",
        "SAVE_MEMORY":    r"\[SAVE_MEMORY:\s*(.+?)\]",
        "VERIFY":         r"\[VERIFY:\s*(.+?)\]",
        "ANALYZE":        r"\[ANALYZE:\s*(.+?)\]",
        "CHECK_SOURCE":   r"\[CHECK_SOURCE:\s*(.+?)\]",
        "SEARCH_WEB":     r"\[SEARCH_WEB:\s*(.+?)\]",
        "SEARCH_YOUTUBE": r"\[SEARCH_YOUTUBE:\s*(.+?)\]",
        "SAVE_OBSIDIAN":  r"\[SAVE_OBSIDIAN:\s*(.+?)\]",
        "SAVE_REFERENCE": r"\[SAVE_REFERENCE:\s*(.+?)\]",
        "BUILD_PACKET":   r"\[BUILD_PACKET:\s*(.+?)\]",
    }

# tool 이름 정규화 함수
def normalize_tool_name(name: str) -> str:
    """
    입력된 도구 명을 정규화합니다.
    예: NEED_RESEARCH -> SEARCH_WEB 등 클렌징 및 정규화
    """
    if not name:
        return ""
    cleaned = name.strip().upper()
    # 하위 호환성 및 정규화 매핑
    if cleaned == "NEED_RESEARCH":
        return "SEARCH_WEB"
    if cleaned == "SAVE_MEMORY":
        return "SAVE_OBSIDIAN"
    return cleaned

# tool 명령 파싱 헬퍼
def parse_tool_command(text: str) -> dict | None:
    """
    텍스트 내에서 첫 번째로 발견되는 에이전트 도구 명령을 추출 및 파싱합니다.
    반환 형식: {"tool": "TOOL_NAME", "param": "파라미터"} 또는 None
    """
    if not text or not isinstance(text, str):
        return None
    
    tools = get_supported_agent_tools()
    for tool_name, pattern in tools.items():
        match = re.search(pattern, text)
        if match:
            return {
                "tool": normalize_tool_name(tool_name),
                "param": match.group(1).strip()
            }
    return None

# tool 실행 결과 포맷터 (공통)
def format_tool_result(tool_name: str, success: bool, data: str, error_msg: str = "") -> str:
    """
    도구 실행 결과를 마크다운 형태로 통일되게 래핑하여 포맷팅합니다.
    """
    norm_name = normalize_tool_name(tool_name)
    if not success:
        return f"[{norm_name} 실행 실패: {error_msg if error_msg else '알 수 없는 오류'}]"
    return data

# 개별 도구 결과 포맷터 군
def format_check_source_result(param: str, results: list, citation_formatter=None) -> str:
    """
    CHECK_SOURCE 실행 결과를 포맷팅합니다.
    """
    result_header = f"\n[✅ 출처 검증 — {param}]\n"
    if not results:
        return f"[⚠️ 출처 미확인: {param} — Gemma 추론으로 표기 필요]"
    
    lines = []
    for r in results[:3]:
        title = r.get("title", "")
        url = r.get("url", "")
        if citation_formatter:
            citation = citation_formatter(url, title=title)
        else:
            citation = f"[SOURCE: {url} — 검색일: {datetime.now().strftime('%Y-%m-%d')}]"
        lines.append(f"- {title}: {url} {citation}")
    
    return result_header + "\n".join(lines)

def format_search_web_result(query: str, results: list, results_formatter=None) -> str:
    """
    SEARCH_WEB (NEED_RESEARCH) 실행 결과를 포맷팅합니다.
    """
    result_header = f"\n[🌐 웹 검색 결과 — {query}]\n"
    if not results:
        return result_header + "(검색 결과가 비어 있습니다.)"
    
    if results_formatter:
        return result_header + results_formatter(results[:4])
    
    formatted_items = []
    for idx, r in enumerate(results[:4], 1):
        title = r.get("title", "제목 없음").strip()
        url = r.get("url", "").strip()
        content = r.get("content", "").strip()
        formatted_items.append(f"[{idx}] 제목: {title}\nURL: {url}\n내용: {content}")
    return result_header + "\n\n".join(formatted_items)

def format_search_youtube_result(query: str, results: list) -> str:
    """
    SEARCH_YOUTUBE 실행 결과를 포맷팅합니다.
    """
    result_header = f"\n[📺 YouTube 검색 결과 — {query}]\n"
    if not results:
        return result_header + "(YouTube 검색 결과가 비어 있습니다.)"
    
    lines = []
    for idx, r in enumerate(results[:3], 1):
        title = r.get("title", "제목 없음").strip()
        url = r.get("url", "").strip()
        content = r.get("content", "").strip()
        lines.append(f"[{idx}] 제목: {title}\nURL: {url}\n설명: {content[:200]}")
    return result_header + "\n\n".join(lines)

def format_save_obsidian_result(param: str, success: bool, error_msg: str = "") -> str:
    """
    SAVE_OBSIDIAN (SAVE_MEMORY) 실행 결과를 포맷팅합니다.
    """
    if success:
        return f"[✅ 옵시디언 저장 완료: {param}]"
    return f"[저장 실패: {error_msg if error_msg else '알 수 없는 오류'}]"

def format_save_reference_result(param: str, success: bool, error_msg: str = "") -> str:
    """
    SAVE_REFERENCE 실행 결과를 포맷팅합니다.
    """
    if success:
        return f"[✅ References 저장 완료: {param}]"
    return f"[References 저장 실패: {error_msg if error_msg else '알 수 없는 오류'}]"

def format_build_packet_result(param: str, success: bool, error_msg: str = "") -> str:
    """
    BUILD_PACKET 실행 결과를 포맷팅합니다.
    """
    if success:
        return f"[✅ 패킷 빌드 완료: {param}]"
    return f"[패킷 빌드 실패: {error_msg if error_msg else '알 수 없는 오류'}]"
