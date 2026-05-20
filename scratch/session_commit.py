# -*- coding: utf-8 -*-
import os
from datetime import datetime
from git import Repo

def main():
    repo_path = r"C:\SageMirror_Production"
    version = "13.26"
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    
    # 1. Save Obsidian Session file
    obsidian_dir = os.path.join(repo_path, "00_Obsidian", "sessions")
    os.makedirs(obsidian_dir, exist_ok=True)
    session_filename = f"session_{ts}_v{version}.md"
    session_filepath = os.path.join(obsidian_dir, session_filename)
    
    summary = f"""# Sage Mirror Studio Session Summary - v{version}
- **Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
- **Version:** v{version}

## 변경 사항 요약
- Part 1 Librarian 3단 분석 엔진 영속성 보존 및 상태 무결성 확보 완료.
- 각 스텝의 입력 텍스트 영역에 `on_change` 콜백을 적용하여 탭 전환 및 앱 Rerun 시에도 입력값이 안정적으로 보존되도록 구현.
- 벤치마킹, 자료조사, 최종 기획안 단계의 시작 버튼 클릭 시 기존 결과 및 인디케이터 상태가 올바르게 초기화되도록 세션 관리 적용.
- 시작/로컬저장/옵시디언 백업의 3단 동적 상태 표시(인디케이터) 레이아웃을 Streamlit 정렬에 맞게 개선하여 시각적 직관성 확보.
- `RUN_APP.bat` 및 앱 내부 실행 버전을 `app_v13_26.py`로 갱신.

## 수정된 함수 목록
- `render_part1()` (입력 필드 콜백 정의 및 tab_bench, tab_research, tab_plan UI 3단 버튼 레이아웃 구조 개편)
- `extract_keywords_via_gemma()` (새로운 자동 키워드 세분화 추출 헬퍼 함수 추가)
- `init_session_state()` (신규 인디케이터 및 태그 세션 키 추가)
- `save_workspace_state()` (저장 키 리스트 업데이트)

## 다음 작업 예정
- Part 2 Alchemist 또는 타 파트에 이와 동일한 3단 자동 저장 & RAG 백업 레이아웃 및 영속성 메커니즘 전파 적용.
"""
    with open(session_filepath, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Obsidian session backup completed: {session_filepath}")

    # 2. Git Commit and Push
    try:
        repo = Repo(repo_path)
        repo.git.add("--all")
        commit_msg = f"v{version}: Part 1 Textarea State Persistence & 3-Button Alignment — {ts}"
        repo.index.commit(commit_msg)
        print(f"Git commit successful: {commit_msg}")
        
        origin = repo.remote("origin")
        origin.push()
        print("Git push completed successfully!")
    except Exception as e:
        print(f"Git execution failed: {e}")

if __name__ == "__main__":
    main()
