# -*- coding: utf-8 -*-
"""
sage_engine.py — Gemma4 + Tavily 엔진 & 파일 I/O 유틸리티
"""

import streamlit as st
import os
import json
import csv
from pathlib import Path
from sage_config import OLLAMA_MODEL, SAGE_PERSONA

try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

import requests


# =====================================================================
# 안전한 파일 I/O
# =====================================================================
def safe_makedirs(path):
    try:
        if path:
            Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        st.error(f"폴더 생성 실패: {path} → {e}")
        return False


def save_markdown(filepath, content):
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"마크다운 저장 실패: {e}")
        return False


def save_json(filepath, data):
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"JSON 저장 실패: {e}")
        return False


def save_csv(filepath, rows, headers):
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)
        return True
    except Exception as e:
        st.error(f"CSV 저장 실패: {e}")
        return False


def save_txt(filepath, content):
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"TXT 저장 실패: {e}")
        return False


# =====================================================================
# Gemma4:e4b 호출 (ollama 패키지 + HTTP 폴백)
# =====================================================================
def call_gemma(prompt: str, system: str = "", model: str = OLLAMA_MODEL) -> str:
    """
    gemma4:e2b / e4b 모델 호출.
    1차: ollama 패키지 사용 (빈 응답 시 HTTP 폴백)
    2차: HTTP 직접 호출 (Ollama REST API)

    주의: @st.cache_data 제거됨 —
      팝업 다이얼로그(@st.dialog) 내부에서 Streamlit 컨텍스트 없이
      캐시 함수가 호출되면 빈 응답이 캐싱되어 반복 에러가 발생하므로
      캐싱을 완전히 제거하고 매번 새로 호출합니다.
    """
    # 방법 1: ollama 패키지
    if OLLAMA_AVAILABLE:
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = ollama.chat(model=model, messages=messages)
            result_text = resp["message"]["content"]
            # 빈 응답 감지 → HTTP 폴백으로 재시도
            if result_text and result_text.strip():
                return result_text
            # 빈 응답이면 HTTP 폴백으로 진행
        except Exception:
            pass  # 패키지 실패 → HTTP 폴백

    # 방법 2: HTTP 직접 호출 (Ollama REST API)
    try:
        ollama_url = "http://localhost:11434/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        resp = requests.post(ollama_url, json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        # 빈 응답 방어: 빈 문자열이면 에러 메시지 반환
        if not content or not content.strip():
            return (
                f"[ERROR] 모델 '{model}'이 빈 응답을 반환했습니다.\n"
                f"→ Ollama 재시작 후 재시도하십시오: ollama serve\n"
                f"→ 모델 재설치: ollama pull {model}"
            )
        return content
    except requests.exceptions.ConnectionError:
        return (
            f"[ERROR] Ollama 서버 연결 불가\n"
            f"→ 터미널에서 `ollama serve` 실행 후 재시도\n"
            f"→ 모델 확인: `ollama list` ('{model}' 필요)"
        )
    except Exception as e:
        return f"[ERROR] Ollama 호출 실패: {e}\n→ `ollama serve` 실행 및 모델 '{model}' 설치 확인"


def call_gemma_stream(prompt: str, system: str = "", model: str = OLLAMA_MODEL):
    """
    gemma4:e4b 스트리밍 호출 (실시간 출력용).
    Generator로 토큰을 yield.
    """
    try:
        ollama_url = "http://localhost:11434/api/chat"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        with requests.post(ollama_url, json=payload, timeout=300, stream=True) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
    except Exception as e:
        yield f"\n[ERROR] 스트리밍 실패: {e}"


# =====================================================================
# Tavily 웹 검색
# =====================================================================
@st.cache_data(ttl=600, show_spinner=False)
def tavily_search(query: str, api_key: str, max_results: int = 5) -> dict:
    if not api_key:
        return {"error": "Tavily API 키를 사이드바에 입력하세요."}
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": True,
                "search_depth": "advanced",
            },
            timeout=25,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"Tavily 호출 실패: {e}"}


# =====================================================================
# Ollama 연결 상태 확인
# =====================================================================
@st.cache_data(ttl=30, show_spinner=False)
def check_ollama_status(target_model: str = OLLAMA_MODEL) -> dict:
    """Ollama 서버 & 지정된 모델 상태 확인"""
    result = {"server": False, "model": False, "models": [], "error": None}
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        result["server"] = True
        models = [m.get("name", "") for m in data.get("models", [])]
        result["models"] = models
        # 설정된 모델 존재 여부 확인
        for m in models:
            if target_model.lower() in m.lower() or m.lower().startswith(target_model.lower().split(":")[0]):
                result["model"] = True
                break
    except requests.exceptions.ConnectionError:
        result["error"] = "Ollama 서버 미실행 (ollama serve 필요)"
    except Exception as e:
        result["error"] = str(e)
    return result

def youtube_search_channels(query: str, api_key: str, max_results: int = 5) -> list:
    """구독자 적고 조회수 높은 심리/철학 채널 검색"""
    try:
        import requests
        # 채널 검색
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": max_results * 3,
            "key": api_key,
            "relevanceLanguage": "ko"
        }
        res = requests.get(search_url, params=search_params, timeout=10)
        items = res.json().get("items", [])
        channel_ids = [i["snippet"]["channelId"] for i in items]
        if not channel_ids:
            return []
        # 채널 통계 조회
        stats_url = "https://www.googleapis.com/youtube/v3/channels"
        stats_params = {
            "part": "snippet,statistics",
            "id": ",".join(channel_ids),
            "key": api_key
        }
        stats_res = requests.get(stats_url, params=stats_params, timeout=10)
        channels = []
        for ch in stats_res.json().get("items", []):
            stats = ch.get("statistics", {})
            subs = int(stats.get("subscriberCount", 0))
            views = int(stats.get("viewCount", 0))
            if subs == 0:
                continue
            ratio = views / subs
            channels.append({
                "title": ch["snippet"]["title"],
                "url": f"https://www.youtube.com/channel/{ch['id']}",
                "subscribers": subs,
                "views": views,
                "ratio": round(ratio, 1),
                "description": ch["snippet"].get("description", "")[:100]
            })
        # 구독자 적고 조회수 비율 높은 순 정렬
        channels.sort(key=lambda x: x["ratio"], reverse=True)
        return channels[:max_results]
    except Exception as e:
        return [{"error": str(e)}]
