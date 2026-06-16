# Sage Mirror Studio - Agent School Registry & Core Structure
import json
from datetime import datetime

# --- School Registry Structure ---
def get_default_school():
    return {
        "status": "초기화 필요",
        "gemma_factory": {
            "id": "gemma_orchestrator",
            "prompt_md_path": "prompts/gemma/gemma_factory_master_protocol.md"
        },
        "departments": {
            "part1": {
                "name": "떡상 채널 발굴 / 벤치마킹 학과",
                "agents": {
                    "rising_channel_discovery_agent": {"prompt_md_path": "prompts/part1/01_떡상_채널_발굴기.md", "status": "idle"},
                    "youtube_channel_research_agent": {"prompt_md_path": "prompts/part1/02_유튜브_채널_조사.md", "status": "idle"},
                    "benchmark_video_analysis_agent": {"prompt_md_path": "prompts/part1/03_성공영상_벤치마킹.md", "status": "idle"},
                    "comment_emotion_analysis_agent": {"prompt_md_path": "prompts/part1/04_댓글_감정_분석.md", "status": "idle"},
                    "topic_title_candidate_agent": {"prompt_md_path": "prompts/part1/05_주제_제목_후보_생성.md", "status": "idle"},
                    "part1_packet_builder_agent": {"prompt_md_path": "prompts/part1/06_part1_packet_생성.md", "status": "idle"},
                    "part1_quality_review_agent": {"prompt_md_path": "prompts/part1/07_part1_품질_검수.md", "status": "idle"}
                }
            },
            "part2": {
                "name": "총괄 기획 학과",
                "agents": {
                    "planning_architect_agent": {"prompt_md_path": "prompts/part2/01_기획_아키텍트.md", "status": "idle"},
                    "emotional_flow_agent": {"prompt_md_path": "prompts/part2/02_감정_흐름_설계.md", "status": "idle"},
                    "source_alignment_agent": {"prompt_md_path": "prompts/part2/03_자료_정합성_검증.md", "status": "idle"},
                    "part2_packet_builder_agent": {"prompt_md_path": "prompts/part2/04_part2_packet_생성.md", "status": "idle"},
                    "part2_quality_review_agent": {"prompt_md_path": "prompts/part2/05_part2_품질_검수.md", "status": "idle"}
                }
            },
            "part3": {
                "name": "대본 학과",
                "agents": {
                    "longform_script_agent": {"prompt_md_path": "prompts/part3/01_장문_대본_작성.md", "status": "idle"},
                    "opening_hook_agent": {"prompt_md_path": "prompts/part3/02_오프닝_훅_생성.md", "status": "idle"},
                    "narrative_depth_agent": {"prompt_md_path": "prompts/part3/03_서사_깊이_강화.md", "status": "idle"},
                    "script_style_review_agent": {"prompt_md_path": "prompts/part3/04_문체_검토.md", "status": "idle"},
                    "part3_packet_builder_agent": {"prompt_md_path": "prompts/part3/05_part3_packet_생성.md", "status": "idle"}
                }
            },
            "part4": {
                "name": "이미지 학과",
                "agents": {
                    "image_prompt_agent": {"prompt_md_path": "prompts/part4/01_이미지_프롬프트_작성.md", "status": "idle"},
                    "reference_asset_agent": {"prompt_md_path": "prompts/part4/02_레퍼런스_에셋_선정.md", "status": "idle"},
                    "scene_visual_agent": {"prompt_md_path": "prompts/part4/03_씬_비주얼_구성.md", "status": "idle"},
                    "image_quality_review_agent": {"prompt_md_path": "prompts/part4/04_이미지_품질_검토.md", "status": "idle"},
                    "part4_packet_builder_agent": {"prompt_md_path": "prompts/part4/05_part4_packet_생성.md", "status": "idle"}
                }
            },
            "part5": {
                "name": "영상 JSON 학과",
                "agents": {
                    "opal_json_agent": {"prompt_md_path": "prompts/part5/01_오팔_JSON_생성.md", "status": "idle"},
                    "scene_timing_agent": {"prompt_md_path": "prompts/part5/02_씬_타이밍_계산.md", "status": "idle"},
                    "video_sequence_review_agent": {"prompt_md_path": "prompts/part5/03_영상_시퀀스_검토.md", "status": "idle"},
                    "part5_packet_builder_agent": {"prompt_md_path": "prompts/part5/04_part5_packet_생성.md", "status": "idle"}
                }
            },
            "part6": {
                "name": "오디오 학과",
                "agents": {
                    "tts_ssml_agent": {"prompt_md_path": "prompts/part6/01_TTS_SSML_생성.md", "status": "idle"},
                    "bgm_prompt_agent": {"prompt_md_path": "prompts/part6/02_BGM_프롬프트_생성.md", "status": "idle"},
                    "audio_mood_review_agent": {"prompt_md_path": "prompts/part6/03_오디오_무드_검토.md", "status": "idle"},
                    "part6_packet_builder_agent": {"prompt_md_path": "prompts/part6/04_part6_packet_생성.md", "status": "idle"}
                }
            },
            "part7": {
                "name": "숏폼 학과",
                "agents": {
                    "shorts_hook_agent": {"prompt_md_path": "prompts/part7/01_숏폼_훅_생성.md", "status": "idle"},
                    "shorts_script_agent": {"prompt_md_path": "prompts/part7/02_숏폼_대본_요약.md", "status": "idle"},
                    "shorts_caption_agent": {"prompt_md_path": "prompts/part7/03_숏폼_자막_구성.md", "status": "idle"},
                    "part7_packet_builder_agent": {"prompt_md_path": "prompts/part7/04_part7_packet_생성.md", "status": "idle"}
                }
            },
            "part8": {
                "name": "최종 검수 / CapCut 학과",
                "agents": {
                    "final_review_agent": {"prompt_md_path": "prompts/part8/01_최종_품질_검수.md", "status": "idle"},
                    "capcut_layout_agent": {"prompt_md_path": "prompts/part8/02_캡컷_레이아웃_설계.md", "status": "idle"},
                    "publish_checklist_agent": {"prompt_md_path": "prompts/part8/03_업로드_체크리스트.md", "status": "idle"},
                    "final_packet_builder_agent": {"prompt_md_path": "prompts/part8/04_최종_packet_생성.md", "status": "idle"}
                }
            }
        },
        "packet_queue": [],
        "last_command": None
    }

def ensure_agent_school_state(session_state):
    if "agent_school" not in session_state:
        session_state["agent_school"] = get_default_school()
        session_state["agent_school"]["status"] = "준비됨"

def get_school_status_summary(session_state):
    school = session_state.get("agent_school", get_default_school())
    return school.get("status", "오류")

def get_part_agents(session_state, part_id):
    school = session_state.get("agent_school", get_default_school())
    return school.get("departments", {}).get(part_id, {}).get("agents", {})

def get_total_agent_count(session_state):
    school = session_state.get("agent_school", get_default_school())
    count = 0
    for part, data in school.get("departments", {}).items():
        count += len(data.get("agents", {}))
    return count

def get_packet_queue_summary(session_state):
    school = session_state.get("agent_school", get_default_school())
    queue = school.get("packet_queue", [])
    return f"{len(queue)}건"

def route_school_command(command_text, session_state):
    cmd = command_text.strip().lower()
    session_state.setdefault("agent_school", get_default_school())
    session_state["agent_school"]["last_command"] = command_text

    part1_triggers = ["시작해", "시작", "part 1 시작", "떡상 채널 발굴 시작", "유튜브 조사 시작", "채널 조사 시작"]

    if any(trigger in cmd for trigger in part1_triggers):
        return {
            "recognized": True,
            "target_part": "part1",
            "target_agent": "rising_channel_discovery_agent",
            "action": "prepare_part1_research",
            "message": "Part 1 떡상 채널 발굴 작업 준비 완료"
        }
    
    return {
        "recognized": False,
        "message": "명령을 인식할 수 없습니다."
    }

def build_empty_packet(source_part, target_part, command):
    return {
        "packet_id": f"PKT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "source_part": source_part,
        "target_part": target_part,
        "command": command,
        "status": "pending",
        "payload": {}
    }
