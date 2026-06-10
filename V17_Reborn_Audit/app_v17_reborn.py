# -*- coding: utf-8 -*-
"""
현자의 거울 V17 Reborn
Streamlit 메인 앱

기능:
1. 좌측바 상단 현자의 거울 표시
2. Episode: EP001 표시
3. 글로벌 모델 선택: gemma4:e2b / gemma4:e4b
4. API 키 상태 확인
5. API 키 수정 후 .env 저장
6. 옵시디언 Vault 경로 확인/수정
7. Windows 파일 탐색기로 옵시디언 Vault 폴더 선택
8. 옵시디언 기본 폴더 생성
9. Part 1 화면 연결
"""

from pathlib import Path

import streamlit as st

from core.config import (
    PART_NAMES,
    DEFAULT_MODEL,
    MODELS,
    load_env_value,
)
from parts import part1_librarian
from ui.right_assistant import render_right_assistant


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

DEFAULT_OBSIDIAN_VAULT_PATH = r"C:\SageMirror_Production\00_Obsidian\V17_Reborn"


st.set_page_config(
    page_title="현자의 거울 V17 Reborn",
    page_icon="🪞",
    layout="wide",
)


def mask_secret(value: str) -> str:
    """API 키 전체를 보여주지 않고 앞/뒤만 보여준다."""
    if not value:
        return "미연결"

    value = value.strip()

    if len(value) <= 10:
        return "연결됨"

    return f"{value[:6]}...{value[-4:]} / 길이 {len(value)}"


def read_env_dict() -> dict:
    """.env 파일을 dict로 읽는다."""
    env_data = {}

    if not ENV_PATH.exists():
        return env_data

    try:
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = ENV_PATH.read_text(encoding="cp949").splitlines()

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            env_data[key.strip()] = value.strip()

    return env_data


def write_env_dict(env_data: dict):
    """.env 파일에 KEY=VALUE 형식으로 저장한다."""
    preferred_order = [
        "YOUTUBE_API_KEY",
        "GEMINI_API_KEY",
        "TAVILY_API_KEY",
        "GITHUB_TOKEN",
        "OBSIDIAN_VAULT_PATH",
    ]

    lines = []

    for key in preferred_order:
        if key in env_data:
            lines.append(f"{key}={env_data[key]}")

    for key, value in env_data.items():
        if key not in preferred_order:
            lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_env_value(key_name: str, value: str):
    """.env에 특정 값을 저장한다."""
    env_data = read_env_dict()
    env_data[key_name] = value.strip()
    write_env_dict(env_data)


def open_folder_dialog(initial_path: str) -> str:
    """Windows 파일 탐색기로 폴더를 선택한다."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        start_path = initial_path
        if not Path(start_path).exists():
            start_path = str(BASE_DIR)

        selected_path = filedialog.askdirectory(
            title="옵시디언 Vault 폴더 선택",
            initialdir=start_path,
        )

        root.destroy()
        return selected_path

    except Exception as error:
        st.error(f"폴더 선택창을 열 수 없습니다: {error}")
        return ""


def render_api_editor(key_name: str, label: str):
    """API 키 상태 표시 + 새 값 저장 UI"""
    current_value = load_env_value(key_name)

    st.write(f"**{label} 상태:** {mask_secret(current_value)}")

    new_value = st.text_input(
        f"{label} 새 값 입력",
        value="",
        type="password",
        placeholder="새 키를 붙여넣으세요. 비워두면 변경하지 않습니다.",
        key=f"input_{key_name}",
    )

    if st.button(f"{label} 저장", key=f"save_{key_name}"):
        if new_value.strip():
            save_env_value(key_name, new_value.strip())
            st.success(f"{label} 저장 완료. 앱을 새로고침하거나 재실행하면 반영됩니다.")
        else:
            st.warning("새 값이 비어 있어 저장하지 않았습니다.")


def render_connection_center():
    """좌측바 API 키 / 옵시디언 저장소 관리창"""
    with st.expander("🔐 API 키 / 저장소 관리", expanded=False):
        st.markdown("### API 키 상태 및 수정")

        render_api_editor("YOUTUBE_API_KEY", "YouTube API")
        st.divider()

        render_api_editor("GEMINI_API_KEY", "Gemini API")
        st.divider()

        render_api_editor("TAVILY_API_KEY", "Tavily API")
        st.divider()

        render_api_editor("GITHUB_TOKEN", "GitHub Token")

        st.caption("전체 API 키는 화면에 표시하지 않습니다. 저장된 값은 루트 폴더의 .env 파일에 기록됩니다.")

        st.divider()

        st.markdown("### 🧠 옵시디언 저장소")

        obsidian_path_text = load_env_value(
            "OBSIDIAN_VAULT_PATH",
            DEFAULT_OBSIDIAN_VAULT_PATH,
        )

        obsidian_vault_path = Path(obsidian_path_text)

        st.write("**현재 Vault 경로:**")
        st.code(str(obsidian_vault_path), language="text")

        new_obsidian_path = st.text_input(
            "옵시디언 Vault 경로 수정",
            value=str(obsidian_vault_path),
            key="input_obsidian_vault_path",
        )

        if st.button("📂 파일 탐색기로 Vault 폴더 선택"):
            selected_folder = open_folder_dialog(str(obsidian_vault_path))

            if selected_folder:
                save_env_value("OBSIDIAN_VAULT_PATH", selected_folder)
                st.success("선택한 옵시디언 경로를 저장했습니다. 앱을 새로고침하면 반영됩니다.")
                st.code(selected_folder, language="text")

        if st.button("옵시디언 경로 저장"):
            if new_obsidian_path.strip():
                save_env_value("OBSIDIAN_VAULT_PATH", new_obsidian_path.strip())
                st.success("옵시디언 경로 저장 완료. 앱을 새로고침하거나 재실행하면 반영됩니다.")
            else:
                st.warning("경로가 비어 있어 저장하지 않았습니다.")

        if obsidian_vault_path.exists():
            st.success("옵시디언 Vault 폴더가 연결되어 있습니다.")
        else:
            st.warning("옵시디언 Vault 폴더가 아직 없습니다.")

        raw_path = obsidian_vault_path / "00_Raw"
        wiki_path = obsidian_vault_path / "01_Wiki"
        schema_path = obsidian_vault_path / "02_Schema"

        st.write("00_Raw:", "있음" if raw_path.exists() else "없음")
        st.write("01_Wiki:", "있음" if wiki_path.exists() else "없음")
        st.write("02_Schema:", "있음" if schema_path.exists() else "없음")

        if st.button("옵시디언 기본 폴더 생성"):
            raw_path.mkdir(parents=True, exist_ok=True)
            wiki_path.mkdir(parents=True, exist_ok=True)
            schema_path.mkdir(parents=True, exist_ok=True)

            (obsidian_vault_path / "03_Channels").mkdir(parents=True, exist_ok=True)
            (obsidian_vault_path / "04_References").mkdir(parents=True, exist_ok=True)
            (obsidian_vault_path / "05_Assets").mkdir(parents=True, exist_ok=True)
            (obsidian_vault_path / "99_Logs").mkdir(parents=True, exist_ok=True)

            st.success("옵시디언 기본 폴더를 생성했습니다. 새로고침하면 상태가 반영됩니다.")


def main():
    """메인 앱 실행 함수"""

    if "episode_id" not in st.session_state:
        st.session_state["episode_id"] = "EP001"

    if "global_model" not in st.session_state:
        st.session_state["global_model"] = DEFAULT_MODEL

    st.title("🪞 현자의 거울 V17 Reborn")
    st.caption("Part 1~8 AI 제작 운영체제 / 성경 · 철학 · 심리학 · 감정 기반 제작 파이프라인")

    with st.sidebar:
        st.markdown(
            """
            <div style="font-size: 30px; font-weight: 800; line-height: 1.25;">
                🪞 현자의 거울
            </div>
            <div style="font-size: 15px; margin-top: 8px; opacity: 0.85;">
                Episode: EP001
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.header("공장장 메뉴")

        model_keys = list(MODELS.keys())

        selected_model = st.selectbox(
            "🤖 글로벌 모델 선택",
            options=model_keys,
            index=(
                model_keys.index(st.session_state["global_model"])
                if st.session_state["global_model"] in model_keys
                else model_keys.index(DEFAULT_MODEL)
            ),
            format_func=lambda key: f"{key} - {MODELS[key]['label']}",
        )

        st.session_state["global_model"] = selected_model

        st.caption(f"현재 선택 모델: {selected_model}")
        st.caption(MODELS[selected_model]["desc"])

        st.divider()

        render_connection_center()

        st.divider()

        selected_part = st.radio(
            "작업 파트 선택",
            options=list(PART_NAMES.keys()),
            format_func=lambda x: PART_NAMES[x],
        )

        st.divider()
        st.caption(f"기본 모델: {DEFAULT_MODEL}")
        st.caption(f"전체 앱 적용 모델: {st.session_state['global_model']}")

    main_col, assistant_col = st.columns([0.72, 0.28], gap="large")

    with main_col:
        if selected_part == 1:
            part1_librarian.render()
        else:
            st.header(PART_NAMES[selected_part])
            st.info("이 파트는 아직 기본 화면 준비 전입니다.")
            st.write("현재 전체 앱 적용 모델:", st.session_state["global_model"])
            st.write("현재 Episode:", st.session_state["episode_id"])

    with assistant_col:
        render_right_assistant(
            current_part=str(st.session_state.get("selected_part", st.session_state.get("sidebar_part", "Part 1"))),
            episode_id=str(st.session_state.get("episode_id", "EP001")),
        )


if __name__ == "__main__":
    main()