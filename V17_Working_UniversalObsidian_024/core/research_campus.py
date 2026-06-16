import json

def get_default_campus_state():
    return {
        "campus_name": "현자의 거울 학교 연구기관",
        "current_research_topic": "대기 중",
        "current_research_task": "자료 접수 대기",
        "campus_status": "idle",
        "watchtower_status": "standby",
        "incoming_queue_count": 0,
        "obsidian_save_status": "대기",
        "last_update": "",
        "agents": [
            {
                "agent_id": "data_reception_agent",
                "name": "자료 접수 Agent",
                "lab": "자료 접수실",
                "status": "idle",
                "current_task": "자료 접수 대기",
                "skills": ["외부 자료 수집", "URL 파싱", "파일 형식 분류", "기초 메타데이터 추출"],
                "mcp_tools": ["File System", "Web Scraper"],
                "prompt_md": "prompts/campus/data_reception_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "00_Raw"
            },
            {
                "agent_id": "channel_dissection_agent",
                "name": "채널 해부 연구원",
                "lab": "채널 해부 연구실",
                "status": "idle",
                "current_task": "대기 중",
                "skills": ["채널 전체 구조 분석", "영상 제목 패턴 분석", "스크립트 구조 분석", "댓글 반응 분석"],
                "mcp_tools": ["YouTube API", "File System", "Obsidian Writer", "RAG Search"],
                "prompt_md": "prompts/campus/channel_dissection_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "00_Raw / 01_Wiki / 02_Schema / 03_Logs"
            },
            {
                "agent_id": "script_structure_agent",
                "name": "스크립트 구조 연구원",
                "lab": "스크립트 구조 연구실",
                "status": "idle",
                "current_task": "대기 중",
                "skills": ["문장 흐름 분석", "논리 구조 해체", "설득 기법 도출", "핵심 메시지 추출"],
                "mcp_tools": ["File System", "Obsidian Writer", "RAG Search"],
                "prompt_md": "prompts/campus/script_structure_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "01_Wiki / 02_Schema"
            },
            {
                "agent_id": "comment_emotion_agent",
                "name": "댓글 감정 연구원",
                "lab": "댓글 감정 연구실",
                "status": "idle",
                "current_task": "대기 중",
                "skills": ["시청자 감정 분석", "키워드 클러스터링", "결핍 요소 추출", "페인 포인트 도출"],
                "mcp_tools": ["YouTube API", "File System", "Obsidian Writer"],
                "prompt_md": "prompts/campus/comment_emotion_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "01_Wiki / 02_Schema"
            },
            {
                "agent_id": "hook_intro_agent",
                "name": "후킹/인트로 공식 연구원",
                "lab": "후킹/인트로 연구실",
                "status": "idle",
                "current_task": "대기 중",
                "skills": ["초반 1분 분석", "시선 집중 공식 도출", "호기심 유발 패턴 분석", "시청 지속율 연관성 분석"],
                "mcp_tools": ["File System", "Obsidian Writer", "RAG Search"],
                "prompt_md": "prompts/campus/hook_intro_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "01_Wiki / 02_Schema"
            },
            {
                "agent_id": "obsidian_classification_agent",
                "name": "Obsidian 분류 저장원",
                "lab": "Obsidian 분류 저장실",
                "status": "idle",
                "current_task": "대기 중",
                "skills": ["마크다운 포맷팅", "데이터 정합성 검사", "태그 자동 분류", "폴더 구조화"],
                "mcp_tools": ["File System", "Obsidian Writer"],
                "prompt_md": "prompts/campus/obsidian_classification_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "00_Raw / 01_Wiki / 02_Schema / 03_Logs"
            },
            {
                "agent_id": "24h_watchtower_agent",
                "name": "24시간 감시망 Agent",
                "lab": "24시간 감시탑",
                "status": "idle",
                "current_task": "감시 대기 중",
                "skills": ["키워드 모니터링", "채널 알림 트래킹", "트렌드 감지", "초기 자료 수집"],
                "mcp_tools": ["YouTube API", "Web Scraper", "File System"],
                "prompt_md": "prompts/campus/24h_watchtower_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "00_Raw / 03_Logs"
            },
            {
                "agent_id": "quality_review_agent",
                "name": "연구 품질 검수원",
                "lab": "품질 검수실",
                "status": "idle",
                "current_task": "대기 중",
                "skills": ["연구 결과 검토", "논리적 비약 확인", "자료 부족 판정", "피드백 생성"],
                "mcp_tools": ["File System", "Obsidian Writer", "RAG Search"],
                "prompt_md": "prompts/campus/quality_review_agent.md",
                "input_packet": "대기",
                "output_packet": "대기",
                "obsidian_target": "03_Logs"
            }
        ]
    }
