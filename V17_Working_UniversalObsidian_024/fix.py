import codecs

with codecs.open('app_v17_2_4.py', 'r', 'utf-8-sig') as f:
    content = f.read()

# Mod 1 & 3: Remove EP001 prefix and add top padding reduction CSS
old_css = '''        /* 각 파트별 메인 헤더 타이틀에 [EPXXX] 접두사 강제 주입 */
        div[data-testid="stAppViewContainer"] h3::before {
            content: "[{ep_name}] " !important;
        }
        </style>'''
        
new_css = '''        /* 상단 패딩 축소 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        header[data-testid="stHeader"] {
            height: 0rem;
        }
        </style>'''

content = content.replace(old_css, new_css)

# Mod 2: Fix render_top_panel f-string bug and variable bindings
old_top_panel = '''    project_name = st.session_state.get("project_name", "Universal Obsidian Studio")
    profile_name = st.session_state.get("profile_name", "기본 Profile")
    current_step = st.session_state.get("current_step", "초기화")'''
    
new_top_panel = '''    project_name = st.session_state.get("project_name", "기본 프로젝트")
    profile_name = st.session_state.get("selected_profile", st.session_state.get("profile_name", "기본 Profile"))
    current_step = st.session_state.get("current_step", "파트 1: 벤치마킹 & 자료조사")'''

content = content.replace(old_top_panel, new_top_panel)

with codecs.open('app_v17_2_4.py', 'w', 'utf-8-sig') as f:
    f.write(content)

print('Modifications applied.')
