import sys

with open('app_v17_2_3.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace st.markdown(..., unsafe_allow_html=True) with st.html()
# Specifically for the right gemma panel
start_idx = content.find('def render_right_gemma_panel():')
end_idx = content.find('if "right_research_history" not in st.session_state:', start_idx)

if start_idx != -1 and end_idx != -1:
    panel_code = content[start_idx:end_idx]
    
    # We will replace st.markdown(textwrap.dedent("""<style> ... </style>"""), unsafe_allow_html=True)
    # with st.html("""<style> ... </style>""")
    # We will just rewrite that specific block completely to be sure it's clean.
    
    new_style_block = """    st.html('''
    <div id="right-gemma-sticky-marker"></div>
    <style>
    /* 우측 패널 고정을 위한 부모 컨테이너 설정 */
    div[data-testid="stHorizontalBlock"]:has(#right-gemma-sticky-marker) {
        align-items: flex-start !important;
        overflow: visible !important;
    }
    div[data-testid="column"]:has(#right-gemma-sticky-marker) {
        position: sticky !important;
        top: 2rem !important;
        align-self: flex-start !important;
        height: calc(100vh - 4rem) !important;
        overflow-y: auto !important;
        padding-right: 5px;
        z-index: 999;
    }
    
    /* 둥근 통합 박스 (Gemini 스타일 단일 행) - border wrapper 기준 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) {
        background-color: #252525 !important;
        border: 1px solid #333 !important;
        border-radius: 30px !important;
        padding: 5px 15px !important;
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) > div {
        background-color: transparent !important;
        padding: 0 !important;
    }
    
    /* 내부 컬럼 수직 중앙 정렬 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0.5rem !important;
    }
    
    /* 입력창 내부 투명화 및 여백 제거 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) div[data-testid="stTextInput"] {
        margin-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) div[data-testid="stTextInput"] input {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        padding: 10px 5px !important;
        font-size: 1rem !important;
        color: #fff !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) div[data-testid="stTextInput"] > div > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 모델 선택기 콤팩트화 및 투명화 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) div[data-baseweb="select"] {
        margin-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) div[data-baseweb="select"] > div {
        border: none !important;
        background-color: transparent !important;
        color: #aaa !important;
        box-shadow: none !important;
        cursor: pointer;
        padding-right: 0 !important;
    }
    
    /* ＋ 버튼 (secondary) 투명화 및 V 아이콘 제거 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) button[data-testid="baseButton-secondary"] {
        border: none !important;
        background-color: transparent !important;
        color: #aaa !important;
        font-size: 1.4rem !important;
        padding: 0 !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
        min-height: 40px !important;
        margin-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) button[data-testid="baseButton-secondary"] svg {
        display: none !important;
    }
    
    /* ↑ 버튼 (primary) 스타일 */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) button[kind="primary"] {
        border-radius: 50% !important;
        background-color: #e50914 !important;
        color: white !important;
        border: none !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: 0.2s;
        margin-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(#chatbar-marker) button[kind="primary"]:hover {
        background-color: #ff1c2a !important;
    }
    </style>
    ''')
"""
    
    # We find where `st.markdown("<h4>🔍 리서치</h4>", unsafe_allow_html=True)` is.
    h4_idx = panel_code.find('st.markdown("<h4>🔍 리서치</h4>", unsafe_allow_html=True)')
    if h4_idx != -1:
        # Construct the new panel_code top part
        new_panel_code = panel_code[:h4_idx] + 'st.markdown("<h4>🔍 리서치</h4>", unsafe_allow_html=True)\n' + new_style_block
        content = content[:start_idx] + new_panel_code + content[end_idx:]
        
        with open('app_v17_2_3.py', 'w', encoding='utf-8-sig') as f:
            f.write(content)
        print("Replaced st.markdown with st.html to completely fix CSS leakage.")
    else:
        print("Could not find h4 tag.")
else:
    print("Could not find boundaries.")
