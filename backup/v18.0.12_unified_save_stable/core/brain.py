# -*- coding: utf-8 -*-
"""
core/brain.py — Gemma·Gemini 호출 통합 인터페이스
"""

import json
import requests
import streamlit as st
from core.config import DEFAULT_MODEL


def call_gemma(prompt: str, system: str = "", model: str = None,
               max_tokens: int = 512, temperature: float = 0.3) -> str:
    """Ollama Gemma 동기 호출 (전체 응답)"""
    model = model or DEFAULT_MODEL
    full = (system.strip() + "\n\n" + prompt) if system.strip() else prompt
    payload = {
        "model": model,
        "prompt": full,
        "stream": False,
        "keep_alive": "10m",
        "options": {"num_predict": max_tokens, "temperature": temperature, "top_p": 0.9},
    }
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json=payload, timeout=180
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"[Gemma 오류] {e}"


def stream_gemma(prompt: str, system: str = "", model: str = None):
    """Ollama Gemma 스트리밍 (제너레이터)"""
    model = model or DEFAULT_MODEL
    full = (system.strip() + "\n\n" + prompt) if system.strip() else prompt
    payload = {
        "model": model, "prompt": full, "stream": True, "keep_alive": "10m",
        "options": {"num_predict": 512, "temperature": 0.3, "top_p": 0.9},
    }
    try:
        with requests.post(
            "http://localhost:11434/api/generate",
            json=payload, stream=True, timeout=180
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line: continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                except Exception: continue
                token = chunk.get("response", "")
                if token: yield token
                if chunk.get("done", False): break
    except Exception as e:
        yield f"\n[스트리밍 오류] {e}"


def call_gemini(prompt: str, system: str = "", model: str = "gemini-2.5-flash") -> str:
    """Gemini API 호출"""
    try:
        import google.generativeai as genai
        api_key = st.session_state.get("api_gemini", "")
        if not api_key:
            return "[Gemini API 키 없음]"
        genai.configure(api_key=api_key)
        gmodel = genai.GenerativeModel(model)
        full = (system + "\n\n" + prompt) if system else prompt
        resp = gmodel.generate_content(full)
        return resp.text or ""
    except Exception as e:
        return f"[Gemini 오류] {e}"


def call_model(prompt: str, system: str = "", model: str = None) -> str:
    """모델 자동 라우팅"""
    model = model or DEFAULT_MODEL
    if model.startswith("gemma"):
        return call_gemma(prompt, system, model)
    elif model.startswith("gemini"):
        return call_gemini(prompt, system, model)
    else:
        return f"[지원하지 않는 모델: {model}]"
