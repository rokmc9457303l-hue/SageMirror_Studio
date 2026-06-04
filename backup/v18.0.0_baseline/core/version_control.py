# -*- coding: utf-8 -*-
"""
core/version_control.py — Lock·Revision·GitHub Push 공통
"""

import streamlit as st
import subprocess
from datetime import datetime
from pathlib import Path
from core.state import get_state, set_state
from core.config import PART_NAMES


def lock_final(part_num: int) -> bool:
    """파트 최종본 잠금"""
    result = get_state(f"p{part_num}_result")
    if not result:
        st.warning(f"Part {part_num} 결과가 없습니다")
        return False
    
    set_state(f"p{part_num}_locked", True)
    set_state(f"p{part_num}_lock_time", datetime.now().isoformat())
    st.success(f"🔒 Part {part_num} 최종본 잠금 완료")
    return True


def create_revision(part_num: int) -> bool:
    """수정본 생성 (잠금 해제)"""
    if not get_state(f"p{part_num}_locked"):
        st.info(f"Part {part_num} 는 잠금되지 않았습니다")
        return False
    
    set_state(f"p{part_num}_locked", False)
    revision_count = get_state(f"p{part_num}_revision_count", 0) + 1
    set_state(f"p{part_num}_revision_count", revision_count)
    st.success(f"🔓 Part {part_num} 수정본 v{revision_count} 생성")
    return True


def github_push(message: str = None) -> bool:
    """GitHub 자동 푸시"""
    from core.config import BASE_PATH
    
    try:
        message = message or f"Auto-save {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if not (BASE_PATH / ".git").exists():
            st.info("Git 저장소가 초기화되지 않았습니다")
            return False
        
        subprocess.run(["git", "add", "."], cwd=BASE_PATH, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=BASE_PATH, check=True, capture_output=True)
        subprocess.run(["git", "push"], cwd=BASE_PATH, check=True, capture_output=True)
        
        st.success(f"🚀 GitHub Push 완료: {message}")
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"GitHub Push 실패: {e}")
        return False
    except Exception as e:
        st.error(f"오류: {e}")
        return False


def render_action_buttons(part_num: int):
    """파트 하단 공통 액션 버튼"""
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    
    locked = get_state(f"p{part_num}_locked", False)
    
    with c1:
        if not locked:
            if st.button(f"🔒 Part {part_num} 최종본 잠금",
                         key=f"lock_{part_num}", use_container_width=True):
                lock_final(part_num)
                st.rerun()
        else:
            st.info("🔒 잠금됨")
    
    with c2:
        if locked:
            if st.button(f"🔓 수정본 생성",
                         key=f"rev_{part_num}", use_container_width=True):
                create_revision(part_num)
                st.rerun()
    
    with c3:
        if st.button(f"🚀 GitHub Push",
                     key=f"push_{part_num}", use_container_width=True):
            github_push(f"Part {part_num} {PART_NAMES[part_num]} update")
