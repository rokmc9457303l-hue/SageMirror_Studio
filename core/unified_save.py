# -*- coding: utf-8 -*-
"""
core/unified_save.py — 모든 자료의 통합 자동 저장 엔진

모든 자료가 동일한 흐름으로 저장됨:
1. 파트 결과물 (8개 파트 동일)
2. 우측 대화 (Chat)
3. 외부 자료 (Tavily/유튜브/파일)
4. RAG 보완 자료

저장 형식 (3중):
- 규칙서 (채널_현자의거울/Part?_*/)
- 범용 (범용카테고리/16개 자동분류)
- 로그 (시스템/Logs/저장기록)
"""

import threading
import queue
import json
import hashlib
from datetime import datetime
from pathlib import Path
from core.config import (
    PART_NAMES, OBSIDIAN_CHANNEL, OBSIDIAN_UNIVERSAL, OBSIDIAN_SYSTEM,
)
from core.obsidian import save_dual, classify_tags
from core.obsidian import classify_3layer, format_tags_3layer


HASH_INDEX_PATH = Path(__file__).parent.parent / "data" / "content_hashes.json"

def _load_hash_index():
    if HASH_INDEX_PATH.exists():
        try:
            return json.loads(HASH_INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_hash_index(index):
    HASH_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    HASH_INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def _check_and_register_hash(content, filepath=None):
    """중복 체크 + 등록. 중복이면 기존 경로 반환, 아니면 None."""
    text = (content or "").strip()
    if len(text) < 10:
        return None
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    index = _load_hash_index()
    if content_hash in index:
        return index[content_hash]
    if filepath:
        index[content_hash] = str(filepath)
        _save_hash_index(index)
    return None


# ── 통합 저장 큐 ──────────────────────────────────
_unified_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


# ── 자료 유형 정의 ────────────────────────────────
CONTENT_TYPES = {
    "part_result":       "파트 결과물",
    "part_packet":       "파트 전달 패킷",
    "chat_dialog":       "우측 대화",
    "external_research": "외부 리서치",
    "youtube_data":      "유튜브 자료",
    "youtube_channel":   "유튜브 채널 분석",
    "file_upload":       "파일 업로드",
    "google_drive":      "Google Drive 자료",
    "google_docs":       "Google Docs 자료",
    "rag_supplement":    "RAG 자동 보완",
    "tavily_research":   "Tavily 실시간 검색",
    "gemini_research":   "Gemini AI 분석",
}


# ── 표준 메타데이터 빌더 ──────────────────────────
def build_metadata(content_type: str, **kwargs) -> dict:
    """모든 자료의 표준 메타데이터"""
    return {
        "type":      content_type,
        "type_label": CONTENT_TYPES.get(content_type, "기타"),
        "timestamp": datetime.now().isoformat(),
        "date":      datetime.now().strftime("%Y-%m-%d"),
        "time":      datetime.now().strftime("%H:%M:%S"),
        "version":   "v18.0.18",
        **kwargs,
    }


# ── 백그라운드 워커 ───────────────────────────────
def _worker():
    """모든 저장 작업 처리"""
    while True:
        try:
            task = _unified_queue.get(timeout=60)
            if task is None:
                break
            
            try:
                _process_task(task)
            except Exception as e:
                _log_error(f"저장 실패: {e}", task)
            
            _unified_queue.task_done()
        except queue.Empty:
            continue


def _ensure_worker():
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            _worker_started = True


# ── 통합 저장 함수 ────────────────────────────────
def save_anything(
    content: str,
    title: str,
    content_type: str = "part_result",
    part_num: int = None,
    extra_meta: dict = None,
):
    """
    모든 자료의 통합 저장 엔트리포인트
    
    Args:
        content: 본문
        title: 제목
        content_type: CONTENT_TYPES 의 키
        part_num: 파트 번호 (해당 시)
        extra_meta: 추가 메타데이터
    """
    # === v18.0.18 중복 방지 ===
    _dup = _check_and_register_hash(content)
    if _dup:
        import logging
        logging.getLogger(__name__).info(f"중복 감지 스킵: {_dup}")
        return {"status": "skipped", "reason": "duplicate", "existing_file": _dup}
        
    _ensure_worker()
    
    metadata = build_metadata(content_type, **(extra_meta or {}))
    if part_num:
        metadata["part_num"] = part_num
        metadata["part_name"] = PART_NAMES.get(part_num, "")
    
    _unified_queue.put({
        "content":  content,
        "title":    title,
        "metadata": metadata,
    })


def _process_task(task: dict):
    """저장 작업 실행"""
    content  = task["content"]
    title    = task["title"]
    metadata = task["metadata"]
    
    content_type = metadata["type"]
    part_num     = metadata.get("part_num")
    
    # 1. 규칙서 + 범용 듀얼 저장
    if content_type in ["part_result", "part_packet"]:
        # 파트 결과물 → 채널 폴더 + 범용
        result = save_dual(
            content=content,
            title=title,
            part_num=part_num,
            source_type=metadata["type_label"],
        )
        _log_save("part", title, result, metadata)
        
        # === v18.0.18 해시 등록 ===
        _saved_path = result.get("채널", result.get("규칙서", ""))
        if not _saved_path and result:
            _saved_path = list(result.values())[0]
            if isinstance(_saved_path, list) and _saved_path:
                _saved_path = _saved_path[0]
        if _saved_path:
            _check_and_register_hash(content, filepath=str(_saved_path))
    
    elif content_type == "chat_dialog":
        # 대화 → Chat 폴더 + 의미있는 대화는 범용에도
        _save_chat(content, title, metadata)
    
    elif content_type in [
        "external_research", "youtube_data", "youtube_channel",
        "file_upload", "google_drive", "google_docs", "rag_supplement",
        "tavily_research", "gemini_research",
    ]:
        # 외부 자료 → Raw + Wiki + 범용
        _save_external(content, title, metadata)


def _save_chat(content: str, title: str, metadata: dict):
    """대화 저장 — Chat 폴더 + 범용 카테고리"""
    chat_dir = OBSIDIAN_SYSTEM / "Chat"
    chat_dir.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title[:40] if c.isalnum() or c in " -_").strip()
    chat_file = chat_dir / f"{ts}_{safe_title}.md"
    
    md = _build_chat_md(content, metadata)
    chat_file.write_text(md, encoding="utf-8")
    
    # === v18.0.18 해시 등록 ===
    _check_and_register_hash(content, filepath=str(chat_file))
    
    saved_universal = []
    
    # 의미 있는 대화는 범용에도
    if len(content) > 200:
        tags = classify_tags(content, title)
        for category in list(tags.keys())[:3]:
            cat_dir = OBSIDIAN_UNIVERSAL / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            cat_file = cat_dir / f"{ts}_{safe_title}.md"
            cat_file.write_text(md, encoding="utf-8")
            saved_universal.append(str(cat_file))
    
    _log_save("chat", title, {
        "규칙서": str(chat_file),
        "범용": saved_universal,
    }, metadata)


def _save_external(content: str, title: str, metadata: dict):
    """외부 자료 저장 — Raw + Wiki(분석 자료) + 범용"""
    # ── 00_Raw 서브폴더 (CLAUDE.md 규칙서 기준) ──────
    sub_dir = {
        "external_research": "WebResearch",
        "youtube_data":      "YouTube",
        "youtube_channel":   "YouTube",
        "file_upload":       "UserUploads",
        "google_drive":      "GoogleDrive",
        "google_docs":       "GoogleDrive",
        "rag_supplement":    "TavilyResearch",
        "tavily_research":   "TavilyResearch",
        "gemini_research":   "GeminiResearch",
    }.get(metadata["type"], "_Inbox")

    raw_dir = OBSIDIAN_SYSTEM / "00_Raw" / sub_dir
    raw_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title[:40] if c.isalnum() or c in " -_").strip()
    raw_file = raw_dir / f"{ts}_{safe_title}.md"

    channel_id = metadata.get("channel_id")
    md = _build_external_md(content, metadata, channel_id=channel_id)
    raw_file.write_text(md, encoding="utf-8")
    _check_and_register_hash(content, filepath=str(raw_file))

    # ── 10_Wiki 저장 (AI 분석·채널·리서치 자료) ──────
    saved_wiki = []
    wiki_types = {"gemini_research", "youtube_channel", "external_research", "tavily_research"}
    if metadata["type"] in wiki_types and len(content) > 300:
        wiki_file = _save_wiki(content, title, metadata, ts, safe_title)
        if wiki_file:
            saved_wiki.append(str(wiki_file))

    # ── 범용카테고리 저장 ────────────────────────────
    saved_universal = []
    tags = classify_tags(content, title)
    for category in list(tags.keys())[:3]:
        cat_dir = OBSIDIAN_UNIVERSAL / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        cat_file = cat_dir / f"{ts}_{safe_title}.md"
        cat_file.write_text(md, encoding="utf-8")
        saved_universal.append(str(cat_file))

    _log_save("external", title, {
        "Raw": str(raw_file),
        "Wiki": saved_wiki,
        "범용": saved_universal,
    }, metadata)


def _save_wiki(content: str, title: str, metadata: dict, ts: str, safe_title: str):
    """10_Wiki 정리 저장 — 키워드·태그·카테고리 포함"""
    try:
        wiki_dir = OBSIDIAN_SYSTEM / "10_Wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        wiki_file = wiki_dir / f"{ts}_{safe_title}.md"

        cls = classify_3layer(content, title)
        tags_md = format_tags_3layer(cls)
        hashtags = " ".join(
            "#" + c.replace(" ", "_").replace("·", "_")
            for c in classify_tags(content, title).keys()
        )

        wiki_file.write_text(f"""# {title}

## 메타 정보
- **유형**: {metadata.get('type_label', '')}
- **생성 시각**: {metadata.get('timestamp', '')}
- **파트**: {metadata.get('part_name', '없음')}
- **태그**: {hashtags}

## 핵심 내용

{content}

## 자동 분류 (3계층)
{tags_md}
""", encoding="utf-8")
        return wiki_file
    except Exception:
        return None


def _build_chat_md(content: str, metadata: dict) -> str:
    return f"""# 대화 기록

## 메타
- **유형**: {metadata['type_label']}
- **시각**: {metadata['timestamp']}
- **파트**: {metadata.get('part_name', '없음')}

## 내용

{content}

## 자동 분류 태그
{', '.join(['#' + t for t in classify_tags(content).keys()])}
"""


def _build_external_md(content: str, metadata: dict, channel_id: str = None) -> str:
    src_info = ""
    if "url" in metadata:
        src_info += f"- **원본 URL**: {metadata['url']}\n"
    if "source" in metadata:
        src_info += f"- **출처**: {metadata['source']}\n"
    
    _cls = classify_3layer(content, metadata.get('original_title', ''), channel_id=channel_id)
    _tags_md = format_tags_3layer(_cls, channel_id=channel_id)
    
    return f"""# {metadata.get('original_title', '외부 자료')}

## 메타 정보
- **채널**: {channel_id or '미지정'}
- **유형**: {metadata['type_label']}
- **수집 시각**: {metadata['timestamp']}
{src_info}

## 본문

{content}

## 자동 분류
{_tags_md}
"""


# ── 저장 로그 ─────────────────────────────────────
def _log_save(category: str, title: str, result: dict, metadata: dict):
    """저장 기록 (시스템/Logs/)"""
    try:
        log_dir = OBSIDIAN_SYSTEM / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"save_log_{datetime.now().strftime('%Y%m%d')}.log"
        
        line = f"[{datetime.now().strftime('%H:%M:%S')}] [{category}] {title}"
        if isinstance(result, dict):
            counts = []
            for k, v in result.items():
                if isinstance(v, list):
                    counts.append(f"{k}:{len(v)}")
                elif v:
                    counts.append(f"{k}:1")
            line += f" — {', '.join(counts)}"
        
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _log_error(message: str, task: dict):
    """오류 로그"""
    try:
        log_dir = OBSIDIAN_SYSTEM / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"error_log_{datetime.now().strftime('%Y%m%d')}.log"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            f.write(f"  Task: {task.get('title', '?')}\n\n")
    except Exception:
        pass


# ── 상태 조회 ─────────────────────────────────────
def get_queue_status() -> dict:
    return {
        "pending": _unified_queue.qsize(),
        "worker": _worker_started,
    }


def get_save_stats() -> dict:
    """오늘 저장 통계"""
    try:
        log_file = OBSIDIAN_SYSTEM / "Logs" / f"save_log_{datetime.now().strftime('%Y%m%d')}.log"
        if not log_file.exists():
            return {"total": 0, "by_type": {}}
        
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        stats = {"total": len(lines), "by_type": {}}
        for line in lines:
            for category in ["[part]", "[chat]", "[external]"]:
                if category in line:
                    key = category.strip("[]")
                    stats["by_type"][key] = stats["by_type"].get(key, 0) + 1
        return stats
    except Exception:
        return {"total": 0, "by_type": {}}
