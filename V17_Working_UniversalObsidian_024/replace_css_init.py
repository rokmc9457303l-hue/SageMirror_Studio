import codecs
import re

with codecs.open('app_v17_2_4.py', 'r', 'utf-8') as f:
    content = f.read()

target = '''# =====================================================================
# 1.1 동적 테마 CSS 주입
# =====================================================================
_app_settings = st.session_state.get("app_settings", {})
_bg_color = _app_settings.get("background_color", "#FFFFFF")
_sidebar_color = _app_settings.get("sidebar_color", "#F7F7F7")
_accent_color = _app_settings.get("accent_color", "#B8860B")
_text_color = _app_settings.get("text_color", "#111111")

_btn_bg = _app_settings.get("button_background_color", "#1E293B")
_btn_txt = _app_settings.get("button_text_color", _accent_color)
_btn_brd = _app_settings.get("button_border_color", "#B8860B")
_btn_edit = _app_settings.get("edit_button_background_color", "#1E293B")
_btn_save = _app_settings.get("save_button_background_color", "#B8860B")
_btn_send = _app_settings.get("send_button_background_color", "#059669")
_card_bg = _app_settings.get("card_background_color", "#1E293B")
_inp_bg = _app_settings.get("input_background_color", "#0F172A")
_inp_txt = _app_settings.get("input_text_color", "#F5E9D3")
_pop_bg = _app_settings.get("popup_background_color", "#1E293B")
_pop_txt = _app_settings.get("popup_text_color", "#F5E9D3")'''

replacement = '''# =====================================================================
# 1.1 동적 테마 CSS 주입 및 조기 설정 로드
# =====================================================================
def load_app_settings_early():
    import json
    from pathlib import Path

    default_settings = {
        "project_name": "기본 프로젝트",
        "channel_name": "현자의 거울",
        "profile_name": "기본 Profile",
        "background_color": "#111827",
        "sidebar_color": "#3F3F3F",
        "text_color": "#FFFFFF",
        "sidebar_text_color": "#FFFFFF",
        "button_background_color": "#111827",
        "button_text_color": "#FFFFFF",
        "button_border_color": "#B8860B",
        "card_background_color": "#1F2937",
        "card_text_color": "#FFFFFF",
        "accent_color": "#B8860B",
        "edit_button_background_color": "#1E293B",
        "save_button_background_color": "#B8860B",
        "send_button_background_color": "#059669",
        "input_background_color": "#0F172A",
        "input_text_color": "#F5E9D3",
        "popup_background_color": "#1E293B",
        "popup_text_color": "#F5E9D3"
    }

    settings = dict(default_settings)
    
    # workspace_state.json은 현재 실행 디렉토리나 00_Session_States 하위에 있을 수 있음.
    # 앱 상단에서 정확한 경로를 추적하기 어려울 수 있으나, 보통 작업 폴더 최상위나 
    # C:\\SageMirror_Outputs\\00_Session_States 에 저장됨.
    # 우선 작업 폴더 내 workspace_state.json을 확인.
    state_path = Path("workspace_state.json")
    if not state_path.exists():
        # 혹시 SageMirror_Outputs에 있다면 가장 최근 파일 시도
        try:
            out_dir = Path(r"C:\SageMirror_Outputs\00_Session_States")
            if out_dir.exists():
                files = list(out_dir.glob("workspace_state_*.json"))
                if files:
                    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    state_path = files[0]
        except Exception:
            pass

    if state_path.exists():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            saved = data.get("app_settings", {})
            if isinstance(saved, dict):
                for key, value in saved.items():
                    if key in settings and isinstance(value, str):
                        settings[key] = value
        except Exception:
            pass

    return settings

if "app_settings" not in st.session_state:
    st.session_state["app_settings"] = load_app_settings_early()
else:
    early_settings = load_app_settings_early()
    for key, value in early_settings.items():
        st.session_state["app_settings"].setdefault(key, value)

_app_settings = st.session_state.get("app_settings", {})

_bg_color = _app_settings.get("background_color", "#111827")
_sidebar_color = _app_settings.get("sidebar_color", "#3F3F3F")
_accent_color = _app_settings.get("accent_color", "#B8860B")
_text_color = _app_settings.get("text_color", "#FFFFFF")
_sidebar_text_color = _app_settings.get("sidebar_text_color", "#FFFFFF")

_btn_bg = _app_settings.get("button_background_color", "#111827")
_btn_txt = _app_settings.get("button_text_color", "#FFFFFF")
_btn_brd = _app_settings.get("button_border_color", "#B8860B")
_btn_edit = _app_settings.get("edit_button_background_color", "#1E293B")
_btn_save = _app_settings.get("save_button_background_color", "#B8860B")
_btn_send = _app_settings.get("send_button_background_color", "#059669")
_card_bg = _app_settings.get("card_background_color", "#1F2937")
_card_text = _app_settings.get("card_text_color", "#FFFFFF")
_inp_bg = _app_settings.get("input_background_color", "#0F172A")
_inp_txt = _app_settings.get("input_text_color", "#F5E9D3")
_pop_bg = _app_settings.get("popup_background_color", "#1E293B")
_pop_txt = _app_settings.get("popup_text_color", "#F5E9D3")'''

if target in content:
    content = content.replace(target, replacement)
    with codecs.open('app_v17_2_4.py', 'w', 'utf-8') as f:
        f.write(content)
    print("Replaced CSS init variables")
else:
    print("Target not found.")

