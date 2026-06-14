import os
import shutil
from pathlib import Path
import glob

source_dir = Path(r"C:\SageMirror_Production\V17_Working_RightGemma_001")
base_dest_dir = r"C:\SageMirror_Production\V17_Completed_RightResearchPanel_UICheckpoint_{:03d}_20260610"

# 1. Determine folder name
idx = 1
while True:
    dest_dir = Path(base_dest_dir.format(idx))
    if not dest_dir.exists():
        break
    idx += 1

print(f"Creating backup directory: {dest_dir}")

# Define a function to ignore unwanted files during copy
def ignore_forbidden(dir, contents):
    forbidden = {
        '.env', 'local_secrets.json', 'google_token.json', 
        'credentials.json', 'client_secret.json', '__pycache__'
    }
    ignore_list = [c for c in contents if c in forbidden or c.endswith('.env') or c.endswith('.token') or c.endswith('.key') or c.endswith('.pem') or c.endswith('.pyc')]
    return ignore_list

# Copy the directory
shutil.copytree(source_dir, dest_dir, ignore=ignore_forbidden)
print("Files copied successfully.")

# Double check removal of __pycache__ and .pyc just in case
for root, dirs, files in os.walk(dest_dir, topdown=False):
    for name in files:
        if name.endswith('.pyc') or name.endswith('.token') or name.endswith('.key') or name.endswith('.pem') or name.endswith('.env'):
            os.remove(os.path.join(root, name))
    for name in dirs:
        if name == '__pycache__':
            shutil.rmtree(os.path.join(root, name))

# 4. File-level backup
history_file = Path(r"C:\SageMirror_Production\00_History\app_v17_2_3_right_research_panel_ui_checkpoint_{:03d}_20260610.py".format(idx))
shutil.copy2(dest_dir / "app_v17_2_3.py", history_file)
print(f"History file created: {history_file}")

# 5. Create VERSION_NOTE
note_content = """# V17 Right Research Panel UI Checkpoint 001

**상태**: 현재 기준 완성본 / 다음 UI 개선 전 복귀점

### 완료
* Part 0 실제 삭제
* 기존 젬마 어시스턴트 진입 UI 제거
* popup_assistant 호출부 비활성화
* 우측 🔍 리서치 패널 단일화
* 상단 GEMMA 모델/PIN UI 제거
* right_research_history 분리
* RUNNING VERSION 중앙 문구 제거
* py_compile 통과

### 남은 작업
* 우측 입력창 UI 안정형 재수술
* st.text_area 기반 입력창 전환 검토
* ＋ 메뉴 파일 탐색기 연결
* Google Drive / Docs 연결
* Raw / Wiki / Schema 백그라운드 저장 연결

### 주의
* 이 버전은 다음 작업 전 안전 복귀점이다.
* GitHub push 하지 않음.
* 토큰/시크릿 파일 포함하지 않음.
"""
note_file = dest_dir / f"VERSION_NOTE_RightResearchPanel_UICheckpoint_{idx:03d}.md"
note_file.write_text(note_content, encoding="utf-8-sig")
print(f"Version note created: {note_file}")

print(f"DONE_DEST_DIR={dest_dir}")
