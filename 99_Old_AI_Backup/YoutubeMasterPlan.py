import requests
import json
import os
import time
from datetime import datetime

# --- 1. 설정 (P-Reinforce 규격 & API 주소) ---
BASE_URL = "http://127.0.0.1:1234/v1"   # LM Studio (대본 뇌)
ACE_API_URL = "http://localhost:8001"   # ACE-Step (음악 감성)
VAULT_PATH = r"C:\Users\admin\Downloads\AI-Project\10_Wiki\🛠️ Projects"

def get_active_model():
    """LM Studio에서 현재 로드된 모델의 ID를 자동으로 가져옵니다."""
    try:
        response = requests.get(f"{BASE_URL}/models", timeout=5)
        response.raise_for_status()
        models = response.json().get('data', [])
        if models:
            model_id = models[0]['id']
            print(f"🤖 [연결 완료] 현재 사용 중인 뇌(대본): {model_id}")
            return model_id
        else:
            print("⚠️ 로드된 모델이 없습니다. LM Studio에서 모델을 먼저 로드해주세요.")
            return None
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("💡 안내: LM Studio가 실행 중인지, 서버 포트(1234)가 맞는지 확인해주세요.")
        return None

def run_analysis(topic, urls, model_id, comments_data=""):
    print(f"\n🚀 [P-Reinforce Engine] '{topic}' 분석 및 독창적 가치 합성 중...")
    prompt = f"""
    너는 최고의 유튜브 전략가이자 심리학자이며, 특히 40-70대 시청자의 심리를 꿰뚫고 있다.
    단순한 AI 생성 콘텐츠가 아닌, 실제 인간의 경험과 철학이 융합된 '살아있는' 콘텐츠 전략을 짜라.

    [분석 대상]
    - 주제: {topic}
    - 벤치마킹 URL: {urls}
    - 시청자 실제 반응(댓글 데이터): {comments_data if comments_data else "데이터 없음 (일반적 시청자 고민 기반 분석 요망)"}

    [필수 포함 구조]
    1. Human Insight (댓글 분석 기반)
    2. Philosophical Synthesis (철학적 융합)
    3. Anti-AI Content Strategy (독창성 확보)
    4. Hook & Storytelling Flow
    5. Actionable Master Plan

    응답은 반드시 전문적인 마크다운 형식으로 작성하라.
    """
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}], "temperature": 0.8}

    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content']
        
        filename = f"독창적_유튜브_전략_{datetime.now().strftime('%m%d_%H%M')}.md"
        filepath = os.path.join(VAULT_PATH, filename)
        
        template = f"""---
id: {datetime.now().timestamp()}
category: "[[10_Wiki/🛠️ Projects]]"
topic: "{topic}"
strategy_type: "Human-Centric Synthesis"
last_reinforced: {datetime.now().strftime('%Y-%m-%d')}
---
# [[{topic} - 독창적 유튜브 전략 리포트]]
> **전략적 핵심**: 실제 인간의 고통(댓글)과 시대를 초월한 지혜(철학)의 융합
{result}
## 🔗 지식 연결
- Related: [[유튜브_롱폼_마스터_워크플로우]]
- Target Audience: [[4070_심리_프로파일링]]
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)
            
        print(f"✅ 분석 완료! 독창적 전략 리포트가 생성되었습니다: {filepath}")
        return result
    except Exception as e:
        print(f"\n❌ 분석 오류 발생: {e}")
        return None

def generate_script(topic, analysis_result, model_id):
    print(f"\n🎬 [Script Engine] '{topic}' 기반 시네마틱 대본 생성 중...")
    script_prompt = f"""
    너는 40-70대 시청자들에게 깊은 울림을 주는 최고의 스토리텔러이자 영상 작가다.
    다음 분석 전략을 바탕으로, 시청자의 영혼을 흔드는 유튜브 대본을 작성하라.
    [분석 전략 데이터]
    {analysis_result}
    
    [대본 작성 가이드라인]
    1. 대상: 40~70대 (차분하고, 품격 있으며, 진정성 있는 어조)
    2. 구조 (4-Act Structure):
       - Act 1. Hook (0~1분)
       - Act 2. The Struggle (1~3분)
       - Act 3. Philosophical Solution (3~7분)
       - Act 4. Outro (7분~)
    3. 비주얼 큐 (Visual Cues): [장면: 실루엣이 비치는 창가] 등. 거울 연출 포함.
    
    응답은 반드시 '최종 대본' 본문만 마크다운으로 작성하라.
    """
    payload = {"model": model_id, "messages": [{"role": "user", "content": script_prompt}], "temperature": 0.7}

    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload, timeout=150)
        response.raise_for_status()
        script_content = response.json()['choices'][0]['message']['content']
        
        filename = f"최종_대본_{datetime.now().strftime('%m%d_%H%M')}.md"
        filepath = os.path.join(VAULT_PATH, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {topic} 유튜브 대본\n\n{script_content}")
            
        print(f"✨ 대본 생성이 완료되었습니다: {filepath}")
        return script_content
    except Exception as e:
        print(f"\n❌ 대본 생성 오류: {e}")
        return None

def generate_music(topic):
    print(f"\n🎵 [BGM Engine] '{topic}' 테마곡 작곡을 시작합니다...")
    
    # 우리가 함께 다듬은 '현자의 거울' 전용 시네마틱 감성 프롬프트
    prompt = "Sweet yet heavy and calm cinematic piano, clear and distinct melody, deeply emotional and soul-stirring, perfect for profound storytelling."
    duration = 30
    payload = {"prompt": prompt, "duration": duration, "thinking": False}
    
    try:
        response = requests.post(f"{ACE_API_URL}/release_task", json=payload)
        response.raise_for_status()
        resp_data = response.json()
        
        if "data" in resp_data and "task_id" in resp_data["data"]:
            task_id = resp_data["data"]["task_id"]
        else:
            return None
            
        print("⏳ 딥러닝 작곡가가 피아노 건반을 두드리고 있습니다... (약 2~5분 소요)")

        while True:
            status_resp = requests.post(f"{ACE_API_URL}/query_result", json={"task_id": task_id})
            full_result = status_resp.json()
            data = full_result.get("data", {})
            
            if isinstance(data, list) and len(data) > 0:
                status_info = data[0]
            else:
                time.sleep(5)
                continue
            
            status = status_info.get("status")
            
            if status == 1:
                audio_url = status_info.get("audio_url")
                audio_resp = requests.get(f"{ACE_API_URL}{audio_url}")
                
                # 프로젝트 폴더에 대본과 같은 시간대로 자동 저장
                filename = f"배경음악_{datetime.now().strftime('%m%d_%H%M')}.mp3"
                filepath = os.path.join(VAULT_PATH, filename)
                
                with open(filepath, "wb") as f:
                    f.write(audio_resp.content)
                
                print(f"🎉 성공! [현자의 거울] 배경음악이 저장되었습니다: {filepath}")
                return filepath
            elif status == 2:
                print("❌ 음악 생성 실패")
                return None
            
            time.sleep(5)
    except Exception as e:
        print(f"❌ BGM 생성 오류: {e}")
        return None

if __name__ == "__main__":
    print("===================================================")
    print("   🚀 TubeBench AI: [현자의 거울] 풀오토 공장 가동   ")
    print("===================================================")
    
    # 1. 뇌(LM Studio) 체크
    active_model = get_active_model()
    if not active_model:
        exit()

    u_topic = input("분석할 주제(예: 노년의 고독, 쇼펜하우어): ")
    u_urls = input("벤치마킹할 실제 휴먼 채널 URL: ")
    u_comments = input("분석할 주요 댓글들(선택사항, 복사해서 붙여넣기 가능): ")
    
    # 1단계: 분석 및 전략 생성
    analysis_res = run_analysis(u_topic, u_urls, active_model, u_comments)
    
    # 2단계: 대본 및 음악 동시 생성 라인
    if analysis_res:
        choice = input("\n📝 전략이 마음에 드십니까? 대본과 배경음악을 동시에 생성할까요? (y/n): ")
        if choice.lower() == 'y':
            # 대본 생성 (LM Studio 작동)
            generate_script(u_topic, analysis_res, active_model)
            
            # 음악 생성 (ACE-Step 작동)
            generate_music(u_topic)
            
            print("\n===================================================")
            print(" 🎁 축하합니다! 대본과 맞춤형 배경음악이 모두 준비되었습니다!")
            print(f" 📂 저장 위치: {VAULT_PATH}")
            print("===================================================")
        else:
            print("\n👋 전략 리포트 생성으로 작업을 종료합니다.")

