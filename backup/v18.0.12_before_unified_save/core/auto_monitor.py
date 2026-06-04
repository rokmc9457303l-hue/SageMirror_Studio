# -*- coding: utf-8 -*-
"""
core/auto_monitor.py — 우측 패널 자동 모니터링 시스템

3트랙 분리 운영 (대화 절대 방해 안 함):
- 대화 트랙:  사용자 메시지 (즉시 응답)
- 자료 트랙:  RAG 검색 (백그라운드)
- 저장 트랙:  옵시디언 저장 (백그라운드)
- 모니터 트랙: 상태 체크 (별도, 사용자 명시 시에만)

작동 원칙:
1. 자동 작동은 사용자가 명시한 시점에만 (페이지 로드, 파트 시작)
2. 결과는 상태 표시줄에 색깔로만 표시
3. 사용자 클릭 시에만 상세 보고
4. 절대 자동으로 대화창 점유 안 함
"""

import time
from datetime import datetime, timedelta
from core.state import get_state, set_state
from core.config import OBSIDIAN_PATH


# ── 모니터링 상태 캐시 (5분 유효) ────────────────
_MONITOR_CACHE = {}
_CACHE_TTL = 300  # 5분


def get_cached_status(key: str):
    """캐시된 상태 가져오기 (5분 이내)"""
    if key in _MONITOR_CACHE:
        cached_time, value = _MONITOR_CACHE[key]
        if (datetime.now() - cached_time).seconds < _CACHE_TTL:
            return value
    return None


def set_cache(key: str, value):
    """캐시 저장"""
    _MONITOR_CACHE[key] = (datetime.now(), value)


# ── 1. RAG 충분도 모니터 ─────────────────────────
def monitor_rag_status(force_refresh: bool = False) -> dict:
    """현재 작업 파트의 RAG 자료 충분도 체크"""
    
    cache_key = f"rag_p{get_state('current_part', 1)}"
    if not force_refresh:
        cached = get_cached_status(cache_key)
        if cached:
            return cached
    
    current_part = get_state("current_part", 1)
    
    # 이전 파트 패킷에서 주제 추출
    prev_packet = get_state(f"p{current_part - 1}_packet") if current_part > 1 else None
    
    if not prev_packet and current_part > 1:
        result = {
            "status":  "WAITING",
            "color":   "🟡",
            "message": f"Part {current_part - 1} 미완료",
            "files":   0,
        }
        set_cache(cache_key, result)
        return result
    
    # 옵시디언 자료 카운트
    try:
        from core.config import OBSIDIAN_CHANNEL
        part_folder_pattern = f"Part{current_part}_*"
        matching_folders = list(OBSIDIAN_CHANNEL.glob(part_folder_pattern))
        
        total_files = 0
        for folder in matching_folders:
            total_files += len(list(folder.glob("*.md")))
        
        if total_files >= 5:
            result = {
                "status":  "SUFFICIENT",
                "color":   "🟢",
                "message": f"자료 {total_files}건 확보",
                "files":   total_files,
            }
        elif total_files >= 2:
            result = {
                "status":  "MODERATE",
                "color":   "🟡",
                "message": f"자료 {total_files}건 (보충 권장)",
                "files":   total_files,
            }
        else:
            result = {
                "status":  "INSUFFICIENT",
                "color":   "🔴",
                "message": "자료 부족 (자동 보완 권장)",
                "files":   total_files,
            }
        
        set_cache(cache_key, result)
        return result
    
    except Exception as e:
        return {
            "status":  "ERROR",
            "color":   "⚪",
            "message": f"확인 불가",
            "files":   0,
        }


# ── 2. 인용 검증 모니터 ──────────────────────────
def monitor_citation_status(force_refresh: bool = False) -> dict:
    """현재 파트 결과물의 인용 신뢰도"""
    
    current_part = get_state("current_part", 1)
    cache_key = f"cite_p{current_part}"
    
    if not force_refresh:
        cached = get_cached_status(cache_key)
        if cached:
            return cached
    
    result = get_state(f"p{current_part}_result")
    
    if not result:
        ret = {
            "status":  "NO_DATA",
            "color":   "⚪",
            "message": "결과물 없음",
            "score":   0,
        }
        set_cache(cache_key, ret)
        return ret
    
    try:
        from safety.citation_validator import validate_citations
        text = result if isinstance(result, str) else str(result)
        
        validation = validate_citations(text)
        score = validation["trust_score"]
        
        if score >= 0.8:
            ret = {
                "status":  "VERIFIED",
                "color":   "🟢",
                "message": f"신뢰도 {score:.0%}",
                "score":   score,
                "verified": len(validation["verified"]),
                "suspicious": len(validation["suspicious"]),
            }
        elif score >= 0.5:
            ret = {
                "status":  "PARTIAL",
                "color":   "🟡",
                "message": f"신뢰도 {score:.0%} (검증 권장)",
                "score":   score,
                "verified": len(validation["verified"]),
                "suspicious": len(validation["suspicious"]),
            }
        else:
            ret = {
                "status":  "WEAK",
                "color":   "🔴",
                "message": f"신뢰도 낮음 {score:.0%}",
                "score":   score,
                "verified": len(validation["verified"]),
                "suspicious": len(validation["suspicious"]),
            }
        
        set_cache(cache_key, ret)
        return ret
    
    except Exception as e:
        return {
            "status":  "ERROR",
            "color":   "⚪",
            "message": "검증 불가",
            "score":   0,
        }


# ── 3. AI 냄새 모니터 ────────────────────────────
def monitor_ai_smell_status(force_refresh: bool = False) -> dict:
    """현재 파트 결과물의 AI 냄새 검출"""
    
    current_part = get_state("current_part", 1)
    cache_key = f"smell_p{current_part}"
    
    if not force_refresh:
        cached = get_cached_status(cache_key)
        if cached:
            return cached
    
    result = get_state(f"p{current_part}_result")
    
    if not result:
        ret = {
            "status":  "NO_DATA",
            "color":   "⚪",
            "message": "결과물 없음",
            "count":   0,
        }
        set_cache(cache_key, ret)
        return ret
    
    try:
        from safety.tone_filter import filter_ai_smell
        text = result if isinstance(result, str) else str(result)
        
        smell = filter_ai_smell(text)
        count = smell["count"]
        
        if count == 0:
            ret = {
                "status":  "CLEAN",
                "color":   "🟢",
                "message": "AI 냄새 없음",
                "count":   0,
            }
        elif count <= 2:
            ret = {
                "status":  "MILD",
                "color":   "🟡",
                "message": f"{count}건 검출",
                "count":   count,
                "detected": smell["detected"],
            }
        else:
            ret = {
                "status":  "HEAVY",
                "color":   "🔴",
                "message": f"{count}건 검출 (정리 필요)",
                "count":   count,
                "detected": smell["detected"],
            }
        
        set_cache(cache_key, ret)
        return ret
    
    except Exception as e:
        return {
            "status":  "ERROR",
            "color":   "⚪",
            "message": "검사 불가",
            "count":   0,
        }


# ── 통합 모니터링 ─────────────────────────────────
def get_all_status(force_refresh: bool = False) -> dict:
    """3개 모니터 통합 결과"""
    return {
        "rag":    monitor_rag_status(force_refresh),
        "cite":   monitor_citation_status(force_refresh),
        "smell":  monitor_ai_smell_status(force_refresh),
        "timestamp": datetime.now().isoformat(),
    }


def has_alerts() -> bool:
    """경고 알림이 있는지 (🔴 가 하나라도 있으면 True)"""
    status = get_all_status()
    for key in ["rag", "cite", "smell"]:
        if status[key]["color"] == "🔴":
            return True
    return False


def get_alert_summary() -> list:
    """경고 요약 목록"""
    status = get_all_status()
    alerts = []
    
    for key, label in [("rag", "RAG"), ("cite", "인용"), ("smell", "AI냄새")]:
        s = status[key]
        if s["color"] == "🔴":
            alerts.append({
                "type": label,
                "color": s["color"],
                "message": s["message"],
            })
    
    return alerts
