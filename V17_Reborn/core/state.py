# -*- coding: utf-8 -*-
"""
core/state.py
V17 Reborn 상태 저장 엔진
"""

import json
import streamlit as st
from core.config import WORKSPACE_FILE


def init_state():
    defaults = {
        "current_episode": "EP001",
        "current_part": 1,
        "current_model": "gemma4:e2b",

        "p1_packet": {},
        "p2_packet": {},
        "p3_packet": {},
        "p4_packet": {},
        "p5_packet": {},
        "p6_packet": {},
        "p7_packet": {},
        "p8_packet": {},

        "p1_status": "대기",
        "p2_status": "대기",
        "p3_status": "대기",
        "p4_status": "대기",
        "p5_status": "대기",
        "p6_status": "대기",
        "p7_status": "대기",
        "p8_status": "대기",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key, default=None):
    return st.session_state.get(key, default)


def set_state(key, value):
    st.session_state[key] = value


def save_workspace():
    try:
        WORKSPACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = dict(st.session_state)
        safe_data = {}

        for key, value in data.items():
            try:
                json.dumps(value, ensure_ascii=False)
                safe_data[key] = value
            except TypeError:
                safe_data[key] = str(value)

        WORKSPACE_FILE.write_text(
            json.dumps(safe_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except Exception as e:
        st.error(f"작업 상태 저장 실패: {e}")
        return False


def load_workspace():
    try:
        if not WORKSPACE_FILE.exists():
            return False

        data = json.loads(WORKSPACE_FILE.read_text(encoding="utf-8"))
        for key, value in data.items():
            st.session_state[key] = value

        return True
    except Exception as e:
        st.warning(f"작업 상태 복원 실패: {e}")
        return False