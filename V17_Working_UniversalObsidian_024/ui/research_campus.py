import streamlit as st
import json
from core.research_campus import get_default_campus_state

@st.dialog("📋 Agent 상세 정보", width="large")
def popup_agent_details(agent_info):
    st.subheader(f"[{agent_info['name']}] 상세 정보")
    
    st.write(f"**연구실:** {agent_info['lab']}")
    st.write(f"**현재 상태:** {agent_info['status']}")
    st.write(f"**현재 연구 과제:** {agent_info['current_task']}")
    
    st.markdown("#### 보유 Skill")
    for skill in agent_info['skills']:
        st.write(f"- {skill}")
        
    st.markdown("#### 사용 MCP / Provider")
    for tool in agent_info['mcp_tools']:
        st.write(f"- {tool}")
        
    st.write(f"**사용 Prompt MD:** {agent_info['prompt_md']}")
    st.write(f"**입력 Packet:** {agent_info['input_packet']}")
    st.write(f"**출력 Packet:** {agent_info['output_packet']}")
    st.write(f"**Obsidian 저장 대상:** {agent_info['obsidian_target']}")
    
    st.divider()
    if st.button("닫기", use_container_width=True, key=f"close_{agent_info['agent_id']}"):
        st.rerun()

def render_research_campus():
    if "campus_state" not in st.session_state:
        st.session_state["campus_state"] = get_default_campus_state()
        
    c_state = st.session_state["campus_state"]
    
    # 상단 헤더
    if st.button("← 학교 나가기 / Part 화면으로 복귀", use_container_width=True):
        st.session_state["current_view"] = "part"
        st.session_state["show_settings_modal"] = False
        st.rerun()
        
    st.title("🏫 현자의 거울 학교 연구기관")
    st.markdown("""
        <p style="font-size: 0.9em; color: #f5e9d3; opacity: 0.85;">
        학교 연구기관은 Part 1~8 제작 공정과 분리된 독립 연구소입니다.<br>
        Part 1 떡상 채널 발굴은 현재 영상 제작용 벤치마킹 공정입니다.<br>
        24시간 감시망은 사전 등록 채널 감시 후 자료를 학교로 전달합니다.
        </p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 상태 표시
    st.markdown("### 📊 연구기관 현황")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**현재 연구 주제:** {c_state['current_research_topic']}")
        st.write(f"**현재 연구과제:** {c_state['current_research_task']}")
    with col2:
        st.write(f"**학교 상태:** {c_state['campus_status']}")
        st.write(f"**24시간 감시망:** {c_state['watchtower_status']}")
    with col3:
        st.write(f"**자료 접수 대기:** {c_state['incoming_queue_count']}건")
        st.write(f"**Obsidian 저장 상태:** {c_state['obsidian_save_status']}")
    st.write(f"**마지막 업데이트:** {c_state.get('last_update', 'N/A')}")
    
    st.divider()
    
    # 24시간 감시망 섹션 (감시탑)
    st.markdown("### 📡 24시간 감시탑")
    st.info("사전 등록된 채널과 키워드를 감시하다가 새 영상, 새 댓글, 채널 변화가 발견되면 자료를 수집해 학교 연구기관 자료 접수실로 전달한다. Part 1 떡상 채널 발굴에는 관여하지 않는다.")
    # TODO: watchtower events should enqueue into campus incoming_research_queue
    
    st.divider()
    
    # Agent 연구실 카드 그리드
    st.markdown("### 🧪 연구실 카드 그리드")
    
    agents = c_state.get("agents", [])
    
    # 3개씩 끊어서 컬럼으로 표시
    cols = st.columns(3)
    for i, agent in enumerate(agents):
        col = cols[i % 3]
        with col:
            with st.container(border=True):
                st.markdown(f"**{agent['name']}**")
                st.caption(agent['lab'])
                st.write(f"상태: {agent['status']}")
                
                # 버튼을 눌러서 팝업 호출
                if st.button("자세히 보기", key=f"btn_agent_{agent['agent_id']}", use_container_width=True):
                    popup_agent_details(agent)
                    
    st.divider()
    
    # 하단 섹션
    st.markdown("### 📥 자료 주입 및 대기열")
    st.write(" **+ 버튼 자료 주입 대기** (수동 자료 접수 가능 / 감시망 자료 접수 가능)")
    # TODO: right assistant + menu uploaded files should enqueue into campus incoming_research_queue
    
    with st.expander("최근 연구 로그 및 Packet 흐름", expanded=False):
        st.write("아직 기록된 로그가 없습니다.")
        # TODO: campus research result should save to Obsidian Raw/Wiki/Schema/Logs

