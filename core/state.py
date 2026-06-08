# -*- coding: utf-8 -*-
"""
core/state.py — session_state 통합 관리
"""

import streamlit as st
import json
from pathlib import Path
from core.config import BASE_PATH, DEFAULT_MODEL, API_KEYS

STATE_FILE = BASE_PATH / "data" / "workspace_state.json"


def init_state():
    """앱 시작 시 session_state 초기화"""
    defaults = {
        # 공통
        "current_part":     1,
        "current_episode":  "EP001",
        "current_model":    DEFAULT_MODEL,
        
        # 8파트 표준 패킷
        "p1_packet": None,
        "p2_packet": None,
        "p3_packet": None,
        "p4_packet": None,
        "p5_packet": None,
        "p6_packet": None,
        "p7_packet": None,
        "p8_packet": None,
        
        # 8파트 작업 상태
        **{f"p{i}_status": "대기" for i in range(1, 9)},
        
        # API 키
        **{f"api_{k}": v for k, v in API_KEYS.items()},
        
        # 우측 패널 (별도 관리)
        "rp_history":       [],
        "rp_hub_open":      False,
        "rp_hub_tab":       "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key, default=None):
    return st.session_state.get(key, default)


def set_state(key, value):
    st.session_state[key] = value


def save_workspace():
    """파일로 영구 저장"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _WIDGET_PREFIXES = ("sb_", "req_", "btn_", "show_", "display_", "tab_")
        save_data = {
            k: v for k, v in st.session_state.items()
            if not k.startswith("_")
            and not k.startswith(_WIDGET_PREFIXES)
            and not callable(v)
        }
        for k, v in save_data.items():
            try:
                json.dumps(v)
            except (TypeError, ValueError):
                save_data[k] = str(v)
        STATE_FILE.write_text(
            json.dumps(save_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        print(f"[state save error] {e}")
        return False


def load_workspace():
    """파일에서 복원"""
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k not in st.session_state:
                    st.session_state[k] = v
            return True
    except Exception as e:
        print(f"[state load error] {e}")
    return False
