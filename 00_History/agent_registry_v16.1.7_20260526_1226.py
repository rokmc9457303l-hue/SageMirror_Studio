# -*- coding: utf-8 -*-
"""
agent_registry.py — Agent Layer Tool Registry (중앙 에이전트 도구 정보 및 레지스트리 모듈) v1.0
이 모듈은 순수 Python 모듈로 작성되었으며 Streamlit UI 의존성이 전혀 없습니다.
"""

AGENT_TOOL_REGISTRY = {
    "SEARCH_WEB": {
        "aliases": ["NEED_RESEARCH", "SEARCH_WEB"],
        "pattern": r"\[(?:NEED_RESEARCH|SEARCH_WEB):\s*(.+?)\]",
        "description": "Tavily 기반 실시간 웹 검색 및 리서치 자료 수집",
        "category": "research",
        "requires_web": True,
        "enabled": True,
    },
    "SEARCH_YOUTUBE": {
        "aliases": ["SEARCH_YOUTUBE"],
        "pattern": r"\[SEARCH_YOUTUBE:\s*(.+?)\]",
        "description": "YouTube API 연동 실시간 영상 및 채널 정보 검색",
        "category": "research",
        "requires_web": True,
        "enabled": True,
    },
    "CHECK_SOURCE": {
        "aliases": ["CHECK_SOURCE"],
        "pattern": r"\[CHECK_SOURCE:\s*(.+?)\]",
        "description": "Tavily 기반 특정 성경/철학 인용 및 지식 출처의 팩트체크",
        "category": "verify",
        "requires_web": True,
        "enabled": True,
    },
    "SAVE_OBSIDIAN": {
        "aliases": ["SAVE_MEMORY", "SAVE_OBSIDIAN"],
        "pattern": r"\[(?:SAVE_MEMORY|SAVE_OBSIDIAN):\s*(.+?)\]",
        "description": "분석 완료 데이터의 옵시디언 자동 영구 저장",
        "category": "storage",
        "requires_web": False,
        "enabled": True,
    },
    "SAVE_REFERENCE": {
        "aliases": ["SAVE_REFERENCE"],
        "pattern": r"\[SAVE_REFERENCE:\s*(.+?)\]",
        "description": "업로드 데이터나 RAG용 파일 백업 저장",
        "category": "storage",
        "requires_web": False,
        "enabled": True,
    },
    "BUILD_PACKET": {
        "aliases": ["BUILD_PACKET"],
        "pattern": r"\[BUILD_PACKET:\s*(.+?)\]",
        "description": "Gemma 출력 구조의 포맷 정합성 체크 및 인덱스 패킷 생성",
        "category": "system",
        "requires_web": False,
        "enabled": True,
    },
    "SAVE_MEMORY": {
        "aliases": ["SAVE_MEMORY", "SAVE_OBSIDIAN"],
        "pattern": r"\[(?:SAVE_MEMORY|SAVE_OBSIDIAN):\s*(.+?)\]",
        "description": "옵시디언 자동 저장을 위한 레거시 도구 명칭 (SAVE_OBSIDIAN으로 맵핑됨)",
        "category": "storage",
        "requires_web": False,
        "enabled": True,
    },
    "NEED_RESEARCH": {
        "aliases": ["NEED_RESEARCH", "SEARCH_WEB"],
        "pattern": r"\[(?:NEED_RESEARCH|SEARCH_WEB):\s*(.+?)\]",
        "description": "웹 검색 리서치 자동보완을 위한 레거시 도구 명칭 (SEARCH_WEB으로 맵핑됨)",
        "category": "research",
        "requires_web": True,
        "enabled": True,
    }
}

def get_agent_tool_registry() -> dict:
    """
    중앙 에이전트 도구 레지스트리 딕셔너리를 반환합니다.
    """
    return AGENT_TOOL_REGISTRY

def normalize_registry_tool_name(name: str) -> str:
    """
    입력된 도구 명칭 또는 별칭(alias)을 레지스트리 표준 대표 이름으로 정규화합니다.
    """
    if not name:
        return ""
    cleaned = name.strip().upper()
    
    # 1차 직접 이름 매핑 확인
    if cleaned in AGENT_TOOL_REGISTRY:
        # 단, 레거시 키는 정식 대표 키로 포인팅
        if cleaned == "NEED_RESEARCH":
            return "SEARCH_WEB"
        if cleaned == "SAVE_MEMORY":
            return "SAVE_OBSIDIAN"
        return cleaned
        
    # 2차 aliases 탐색 확인
    for key, metadata in AGENT_TOOL_REGISTRY.items():
        if cleaned in metadata.get("aliases", []):
            if key == "NEED_RESEARCH":
                return "SEARCH_WEB"
            if key == "SAVE_MEMORY":
                return "SAVE_OBSIDIAN"
            return key
            
    return cleaned

def get_enabled_tools() -> list[str]:
    """
    활성화(enabled=True) 상태인 툴 이름(대표 정규화 명칭)의 고유 목록을 반환합니다.
    """
    enabled_keys = set()
    for key, metadata in AGENT_TOOL_REGISTRY.items():
        if metadata.get("enabled", True):
            enabled_keys.add(normalize_registry_tool_name(key))
    return sorted(list(enabled_keys))

def get_tool_metadata(tool_name: str) -> dict | None:
    """
    특정 도구의 메타데이터 딕셔너리를 반환합니다.
    """
    norm_name = normalize_registry_tool_name(tool_name)
    # 정규화된 툴 이름이 레지스트리에 없으면 원래 키로 직접 검색해보고 둘 다 없으면 None 반환
    if norm_name in AGENT_TOOL_REGISTRY:
        return AGENT_TOOL_REGISTRY[norm_name]
    
    upper_name = tool_name.strip().upper()
    if upper_name in AGENT_TOOL_REGISTRY:
        return AGENT_TOOL_REGISTRY[upper_name]
        
    return None

def get_tool_description(tool_name: str) -> str:
    """
    특정 도구의 설명(description)을 반환합니다.
    """
    meta = get_tool_metadata(tool_name)
    if meta:
        return meta.get("description", "")
    return ""

def get_tool_category(tool_name: str) -> str:
    """
    특정 도구의 카테고리(category)를 반환합니다.
    """
    meta = get_tool_metadata(tool_name)
    if meta:
        return meta.get("category", "")
    return ""
