# -*- coding: utf-8 -*-
"""
core/scheduler.py — 자동 실행 스케줄러 (Task 55)

Sentinel 일일 정찰, Curator 정리, 진화 보고를 백그라운드 스레드로 실행한다.
Streamlit 세션 내에서는 daemon thread로 동작하므로 앱 종료 시 자동 소멸한다.
"""

import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_scheduler_started = False
_scheduler_lock = threading.Lock()


def _run_daily_patrol():
    """매일 새벽 3시 Sentinel 정찰 실행"""
    from core.agents.sentinel import SentinelAgent
    try:
        s = SentinelAgent()
        result = s.daily_patrol()
        logger.info(f"[Scheduler] Sentinel 정찰 완료 — 신규 {result.get('new_videos', 0)}건")
    except Exception as e:
        logger.error(f"[Scheduler] Sentinel 오류: {e}")


def _run_curator_maintenance():
    """매주 월요일 Curator 일일 정리 실행"""
    from core.agents.curator import CuratorAgent
    try:
        c = CuratorAgent()
        report = c.daily_maintenance()
        logger.info(f"[Scheduler] Curator 정리 완료 — {report}")
    except Exception as e:
        logger.error(f"[Scheduler] Curator 오류: {e}")


def _ensure_sentinel_folders():
    """04_Sentinel 폴더 구조 자동 생성 (Task 54)"""
    from core.config import OBSIDIAN_PATH
    folders = [
        OBSIDIAN_PATH / "04_Sentinel" / "tracked_channels",
        OBSIDIAN_PATH / "04_Sentinel" / "daily_reports",
        OBSIDIAN_PATH / "04_Sentinel" / "trend_analysis",
    ]
    for f in folders:
        f.mkdir(parents=True, exist_ok=True)


def _scheduler_loop():
    """스케줄러 메인 루프 (daemon thread)"""
    _ensure_sentinel_folders()
    logger.info("[Scheduler] 시작됨")

    while True:
        now = datetime.now()

        # 새벽 3시 정찰
        if now.hour == 3 and now.minute == 0:
            _run_daily_patrol()
            time.sleep(61)  # 중복 실행 방지

        # 매주 월요일 새벽 4시 정리
        if now.weekday() == 0 and now.hour == 4 and now.minute == 0:
            _run_curator_maintenance()
            time.sleep(61)

        time.sleep(30)  # 30초마다 체크


def init_scheduler():
    """
    스케줄러 초기화 — app.py에서 1회 호출.

    Streamlit은 매 렌더 시 모듈을 재실행하므로 _scheduler_started 전역 플래그로 중복 방지.
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _ensure_sentinel_folders()
        t = threading.Thread(target=_scheduler_loop, daemon=True, name="SentinelScheduler")
        t.start()
        _scheduler_started = True
        logger.info("[Scheduler] 데몬 스레드 시작 완료")
