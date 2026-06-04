# -*- coding: utf-8 -*-
"""
core/auto_save.py — 자동 저장 + 백그라운드 작업 큐

3트랙 분리 운영:
- 대화 트랙: 즉시 응답
- 자료 트랙: 백그라운드
- 저장 트랙: 백그라운드
"""

import threading
import queue
import time
from datetime import datetime
from pathlib import Path
from core.config import BASE_PATH, PART_NAMES
from core.obsidian import save_dual, classify_tags


# ── 백그라운드 큐 ─────────────────────────────────
_background_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


def _background_worker():
    """백그라운드 워커 — 자동 저장·정리 작업"""
    while True:
        try:
            task = _background_queue.get(timeout=60)
            if task is None:
                break
            
            task_type = task.get("type")
            data = task.get("data", {})
            
            if task_type == "auto_save_part":
                _process_part_save(data)
            elif task_type == "auto_save_chat":
                _process_chat_save(data)
            elif task_type == "auto_supplement":
                _process_supplement(data)
            
            _background_queue.task_done()
        
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Background worker error] {e}")


def _ensure_worker():
    """워커 한 번만 시작"""
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            t = threading.Thread(target=_background_worker, daemon=True)
            t.start()
            _worker_started = True


def schedule_part_save(part_num: int, content: str, title: str = None):
    """파트 결과물 백그라운드 자동 저장"""
    _ensure_worker()
    _background_queue.put({
        "type": "auto_save_part",
        "data": {
            "part_num": part_num,
            "content": content,
            "title": title or f"Part{part_num}_{PART_NAMES.get(part_num, '')}_{datetime.now().strftime('%Y%m%d_%H%M')}",
        }
    })


def schedule_chat_save(user_input: str, ai_response: str, part_context: int = None):
    """대화 백그라운드 자동 저장 (Chat 폴더)"""
    _ensure_worker()
    _background_queue.put({
        "type": "auto_save_chat",
        "data": {
            "user_input": user_input,
            "ai_response": ai_response,
            "part_context": part_context,
            "timestamp": datetime.now().isoformat(),
        }
    })


def _process_part_save(data: dict):
    """파트 저장 실행"""
    try:
        result = save_dual(
            content=data["content"],
            title=data["title"],
            part_num=data["part_num"],
            source_type="파트 결과물 (자동 저장)",
        )
        _log(f"파트 {data['part_num']} 듀얼 저장 완료: 규칙서 + 범용 {len(result['범용'])}개")
    except Exception as e:
        _log(f"[저장 실패] 파트 {data['part_num']}: {e}")


def _process_chat_save(data: dict):
    """대화 저장 실행 (Chat 폴더 + 범용 카테고리)"""
    try:
        from core.config import OBSIDIAN_SYSTEM
        
        chat_dir = OBSIDIAN_SYSTEM / "Chat"
        chat_dir.mkdir(parents=True, exist_ok=True)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_q = data["user_input"][:30].replace("/", "_").replace("\\", "_")
        chat_file = chat_dir / f"{ts}_{safe_q}.md"
        
        md = f"""# 대화 기록

## 메타
- **시각**: {data['timestamp']}
- **파트 컨텍스트**: {PART_NAMES.get(data.get('part_context'), '없음')}

## 사용자
{data['user_input']}

## AI 응답
{data['ai_response']}
"""
        chat_file.write_text(md, encoding="utf-8")
        _log(f"대화 저장: {chat_file.name}")
        
        # 의미 있는 대화는 범용 카테고리에도 자동 분류
        if len(data["ai_response"]) > 200:
            tags = classify_tags(data["ai_response"], data["user_input"])
            if tags:
                from core.config import OBSIDIAN_UNIVERSAL
                for category in list(tags.keys())[:3]:
                    cat_dir = OBSIDIAN_UNIVERSAL / category
                    cat_dir.mkdir(parents=True, exist_ok=True)
                    cat_file = cat_dir / f"{ts}_{safe_q}.md"
                    cat_file.write_text(md, encoding="utf-8")
                _log(f"대화 카테고리 분류 저장: {list(tags.keys())[:3]}")
    
    except Exception as e:
        _log(f"[대화 저장 실패] {e}")


def _process_supplement(data: dict):
    """자료 보완 실행 (Tavily 검색 결과 저장)"""
    try:
        from core.obsidian import save_dual
        for item in data.get("results", []):
            save_dual(
                content=item.get("content", ""),
                title=item.get("title", "보완자료"),
                part_num=data.get("part_num"),
                source_type="자동 수집 (Tavily)",
            )
        _log(f"자동 보완 자료 {len(data.get('results', []))}건 저장")
    except Exception as e:
        _log(f"[자동 보완 실패] {e}")


def _log(message: str):
    """로그 기록"""
    try:
        from core.config import OBSIDIAN_SYSTEM
        log_dir = OBSIDIAN_SYSTEM / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"auto_save_{datetime.now().strftime('%Y%m%d')}.log"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
    except Exception:
        pass


def get_queue_status() -> dict:
    """큐 상태 확인"""
    return {
        "pending": _background_queue.qsize(),
        "worker_running": _worker_started,
    }
