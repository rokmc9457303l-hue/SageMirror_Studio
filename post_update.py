import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from datetime import datetime
import os

# CHANGELOG 업데이트
changelog_path = r'C:\SageMirror_Production\00_History\CHANGELOG.md'
now = datetime.now().strftime("%Y-%m-%d %H:%M")

new_entry = f"""
## v15.9.1 — {now}
### 변경 내용
- 버튼 명칭 변경: "🤖 Sage Pop-up" → "🤖 젬마 어시스턴트" (파트 1~8 전체, 9개 버튼)
- CSS 개선: .sage-pipe-label 폰트 크기 0.70em → 0.82em (가독성 강화)
- CSS 개선: .glass-control-box 글래스모피즘 스타일 추가 (파트 헤더 우측 컨트롤 박스)
- 버전 헤더: v15.9 → v15.9.1 업데이트
### 영향 파트
- 파트 1~8 전체 (버튼 명칭), 파트 공통 UI (파이프라인 상황판, 헤더 컨트롤 박스)
### 수정 파일
- app_v15_9_1.py (신규 생성)
- RUN_APP.bat (버전 포인터 업데이트)

---
"""

try:
    existing = ""
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            existing = f.read()
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(new_entry + existing)
    print("CHANGELOG 업데이트 완료!")
except Exception as e:
    print(f"CHANGELOG 오류: {e}")

# 옵시디언 세션 저장
session_dir = r'C:\SageMirror_Production\00_Obsidian\sessions'
os.makedirs(session_dir, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M")
session_file = os.path.join(session_dir, f"session_{ts}_v15.9.1.md")
session_content = f"""# 세션 로그 — v15.9.1 (2026-05-22)

## 변경 사항 요약
1. **버튼 명칭 변경**: "🤖 Sage Pop-up" → "🤖 젬마 어시스턴트" (파트 1~8 전체, 9개 버튼)
2. **CSS 개선**: 실시간 데이터 연동 상황판 파이프 라벨 폰트 크기 확대 (0.70em → 0.82em)
3. **CSS 추가**: 파트 헤더 우측 컨트롤 박스 글래스모피즘 스타일 (.glass-control-box) 적용

## 수정된 함수 목록
- `render_top_panel()` (CSS 수정)
- `render_part1()` ~ `render_part8()` (버튼 텍스트 수정)

## 다음 작업 예정
- 파트 1~8 헤더에 .glass-control-box div 래핑 적용 (Python HTML 코드 수정)
- 연동 상태 카드 팝오버 기능 구현 (OBS_RAG_CLICK, GIT_CLICK → 팝오버)
- 미연동 시 빨간 동그라미 표시 로직 강화

*생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

try:
    with open(session_file, 'w', encoding='utf-8') as f:
        f.write(session_content)
    print(f"옵시디언 세션 저장 완료: {session_file}")
except Exception as e:
    print(f"세션 저장 오류: {e}")
