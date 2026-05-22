# -*- coding: utf-8 -*-
import os

changelog_path = r"C:\SageMirror_Production\00_History\CHANGELOG.md"

new_content = """## v15.9.12 — 2026-05-23 00:20
### 변경 내용
- **리서치 자동저장 상태 실시간 확인 LED 인디케이터 UI 추가**:
  - 최상단 공통 옵시디언 규칙서 수동 리서치 검색란 우측에 14px 크기의 조그마한 LED 동그라미 인디케이터 배치.
  - 평상시(대기 상태)에는 하얀색/회색(`#e2e8f0`)으로 대기 중 상태를 표기하고, 구글/Tavily 자동 또는 수동 리서치 결과가 옵시디언에 자동으로 성공적으로 저장 완료 시 파란색(`#60a5fa`) LED 및 글로우(Glow) 박스 섀도우 효과로 즉시 시각적 피드백 제공.
  - 세션 상태 (`st.session_state.research_auto_save_success`) 및 `workspace_state.json` 영속화를 통하여 새로고침 시에도 가장 최근 저장 완료 상태가 일관되게 동기화되도록 연동.
  - 신규 리서치 개시 시에는 인디케이터 상태가 즉각 대기(하얀색)로 리셋 처리되어 신뢰성 제고.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 의 실행 타겟 파일을 `app_v15_9_12.py`로 총괄 업데이트.
### 영향 파트
- **App Core / UI**: 최상단 공통 옵시디언 패널 내부 실시간 리서치 UI, 리서치 자동저장 연동 상태 확인 인디케이터, 배치 파일 실행 타겟 갱신.
### 수정 파일
- `app_v15_9_12.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\\CHANGELOG.md`

---

"""

if os.path.exists(changelog_path):
    with open(changelog_path, "r", encoding="utf-8") as f:
        old_content = f.read()
else:
    old_content = ""

final_content = new_content + old_content

with open(changelog_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print("SUCCESS")
