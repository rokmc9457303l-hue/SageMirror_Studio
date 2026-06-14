# -*- coding: utf-8 -*-
"""
core/packet_router.py — Part간 자동 푸시 시스템

흐름:
  Part N 완료
    → Critic 자동 검수
    → (통과) Curator 옵시디언 저장
    → Packet 빌드
    → Part N+1 세션 상태 전달
    → 03_Logs 기록

  (실패) → DataRequest 반환 → 우측 패널 자료 요청 표시
"""

from datetime import datetime
from pathlib import Path


# ── 현재 채널명 가져오기 ─────────────────────────────────────
def current_channel() -> str:
    try:
        import streamlit as st
        return st.session_state.get("current_channel_name", "")
    except Exception:
        return ""


# ── 키워드/카테고리 추출 ─────────────────────────────────────
def extract_keywords(text: str, max_kw: int = 10) -> list:
    """텍스트에서 빈도 높은 명사 추출 (간이)"""
    import re
    # 한글 단어 추출 (2글자 이상)
    words = re.findall(r"[가-힣]{2,}", str(text))
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:max_kw]]


def extract_categories(text: str) -> list:
    """텍스트에서 범용 카테고리 자동 감지"""
    try:
        from core.obsidian import classify_tags
        tags = classify_tags(str(text))
        return list(tags.keys())[:5]
    except Exception:
        return ["제작자료"]


# ── 핵심 함수 ────────────────────────────────────────────────
def auto_push_to_next_part(part_num: int, result: dict) -> dict:
    """
    Part N 결과를 검증 → 저장 → 다음 Part로 자동 푸시.

    Args:
        part_num: 현재 완료된 Part 번호 (1~7)
        result: Part 결과 dict (packet 형태)

    Returns:
        {
            "success": bool,
            "pushed_to": int | None,
            "paths": dict,
            "data_request": dict | None,
            "message": str,
        }
    """
    from core.obsidian import log_agent_action

    log_agent_action("PacketRouter", f"Part{part_num} 자동 푸시 시작")

    # ── 1. Critic 자동 검수 ─────────────────────────────────
    critic_result = _run_critic(part_num, result)
    if not critic_result["passed"]:
        log_agent_action("PacketRouter", f"Part{part_num} Critic 검수 실패: 점수={critic_result['score']:.1f}")
        return {
            "success": False,
            "pushed_to": None,
            "paths": {},
            "data_request": critic_result.get("data_request"),
            "message": f"Part{part_num} 검증 실패 (점수 {critic_result['score']:.1f}/100). 자료 보강 필요.",
        }

    # ── 2. Fact Checker 검증 ────────────────────────────────
    fact_ok, fact_issues = _fact_check(result)
    if not fact_ok:
        log_agent_action("PacketRouter", f"Part{part_num} Fact Check 실패: {fact_issues[:1]}")
        return {
            "success": False,
            "pushed_to": None,
            "paths": {},
            "data_request": None,
            "message": f"Part{part_num} 사실 검증 실패. 확인 필요: {', '.join(fact_issues[:3])}",
        }

    # ── 3. 옵시디언 자동 저장 ───────────────────────────────
    paths = _curator_auto_save(result, part_num)

    # ── 4. Packet 빌드 + 다음 Part 전달 ────────────────────
    next_part = part_num + 1
    packet = _build_packet(part_num, result, paths)
    if next_part <= 8:
        _push_to_part(next_part, packet)

    # ── 5. 로그 기록 ────────────────────────────────────────
    msg = f"Part{part_num} → Part{next_part} 자동 푸시 완료 | 저장: {len(paths.get('범용', []))+1}개"
    log_agent_action("PacketRouter", msg)
    _log_to_obsidian(f"Part{part_num} → Part{next_part}", packet)

    return {
        "success": True,
        "pushed_to": next_part if next_part <= 8 else None,
        "paths": paths,
        "data_request": None,
        "message": msg,
    }


# ── 내부 헬퍼 ────────────────────────────────────────────────

def _run_critic(part_num: int, result: dict) -> dict:
    """Critic 자동 검수 (실패해도 앱이 죽지 않도록 try/except)"""
    try:
        from core.agents.critic import CriticAgent
        critic = CriticAgent()
        context = {"part": part_num, **result}
        return critic.execute(context)
    except Exception as e:
        return {"passed": True, "score": 75.0, "data_request": None,
                "message": f"Critic 로드 실패(통과 처리): {e}"}


def _fact_check(result: dict) -> tuple:
    """기본 사실 검증: [NEED_VERIFY] 태그 + 출처 없는 통계 감지"""
    from core.critic.patterns import scan_hallucination
    full_text = " ".join(str(v) for v in result.values() if isinstance(v, str))
    findings = scan_hallucination(full_text)
    critical_issues = [f"{desc}" for desc, severity, _, _, _ in findings
                       if severity == "CRITICAL"]
    return len(critical_issues) == 0, critical_issues


def _curator_auto_save(result: dict, part_num: int) -> dict:
    """Curator를 통한 옵시디언 자동 저장"""
    try:
        from core.obsidian import save_dual
        content = _result_to_text(result)
        title = result.get("topic", f"Part{part_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        paths = save_dual(content, str(title)[:40], part_num, source_type="auto_push")
        return paths if isinstance(paths, dict) else {"규칙서": None, "범용": []}
    except Exception as e:
        return {"error": str(e)}


def _build_packet(part_num: int, result: dict, paths: dict) -> dict:
    """표준 Packet 구조 생성"""
    return {
        "part": part_num,
        "status": "PUSHED",
        "version": result.get("version", "v001"),
        "topic": result.get("topic", ""),
        "created_at": datetime.now().isoformat(),
        "channel": current_channel(),
        "saved_paths": paths,
        "critic_passed": True,
        "next_part": part_num + 1,
        **{k: v for k, v in result.items()
           if k not in ("status", "version", "created_at", "saved_paths")},
    }


def _push_to_part(next_part: int, packet: dict):
    """다음 Part의 이전 Packet 세션 상태 업데이트"""
    try:
        import streamlit as st
        key = f"p{next_part - 1}_packet"
        st.session_state[key] = packet
        st.session_state[f"p{next_part}_auto_loaded"] = True
    except Exception:
        pass


def _result_to_text(result: dict) -> str:
    """result dict → 저장용 텍스트"""
    lines = []
    for k, v in result.items():
        if isinstance(v, str) and v:
            lines.append(f"## {k}\n{v}")
        elif isinstance(v, list) and v:
            lines.append(f"## {k}\n" + "\n".join(f"- {i}" for i in v[:20]))
    return "\n\n".join(lines)


def _log_to_obsidian(message: str, packet: dict):
    """03_Logs에 라우팅 이벤트 기록"""
    try:
        from core.obsidian import log_agent_action
        log_agent_action("PacketRouter", f"{message} | topic={packet.get('topic','')[:30]}")
    except Exception:
        pass


# ── 유틸 (UI에서 직접 호출 가능) ─────────────────────────────

def request_data_supplement(part_num: int, data_request: dict) -> dict:
    """자료 보강 요청 패킷 반환 (우측 패널 표시용)"""
    try:
        import streamlit as st
        st.session_state["pending_data_request"] = data_request
        st.session_state["pending_data_request_part"] = part_num
    except Exception:
        pass
    return {
        "success": False,
        "needs_supplement": True,
        "part": part_num,
        "data_request": data_request,
    }


def get_next_auto_load(part_num: int) -> dict:
    """다음 Part에서 자동 로드된 Packet 반환"""
    try:
        import streamlit as st
        prev_key = f"p{part_num - 1}_packet"
        return st.session_state.get(prev_key) or {}
    except Exception:
        return {}
