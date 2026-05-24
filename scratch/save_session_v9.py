import os
from pathlib import Path
from datetime import datetime

def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    ver = "v15.9.34.9"
    session_dir = Path(r"C:\SageMirror_Production\00_Obsidian\sessions")
    session_dir.mkdir(parents=True, exist_ok=True)
    filepath = session_dir / f"session_{ts}_{ver}.md"

    content = f"""# 작업 세션 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M')})

## 📌 버전 정보
- **버전**: {ver}

## 📋 변경 요약
1. **[A] popup_edit_text_value() 저장 후 팝업 안 닫히는 버그 및 sync_flag_key 불일치 수정**:
   - `session_key`가 `obsidian_rules`가 아닐 때 sync flag 세션 변수명이 `top_pr_view_#session_key#_widget`과 매칭되도록 `_widget_key = f"top_pr_view_{{session_key}}_widget"` 및 `_sync_key = f"_sync_{{_widget_key}}_next_run"` 패턴으로 동기화 로직을 정확하게 수정했습니다.
2. **[C] P2_MASTER_PROMPT_DEFAULT 연금술 변환 공식 v2.0 완성본 교체**:
   - 기-승-전-결 연금술 공식 및 다크심리학, 철학(쇼펜하우어, 융, 프랭클, 스토아), 에세이(몽테뉴), 성경의 융합 구조가 상세히 탑재된 마스터 프롬프트 완성본 v2.0으로 2721번 줄의 기본값을 전면 교체했습니다.
3. **[D] 실행 스크립트 3종의 구동 버전 상향**:
   - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 타겟 버전을 `app_v15_9_34_9.py`로 갱신 완료했습니다.

## 🚀 다음 작업 예정
- 수정된 팝업 텍스트 편집기 연동 정상 작동 테스트
- 파트 2 젬마 프롬프트 연금술 변환 동작 테스트
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"Session saved to {filepath}")

if __name__ == "__main__":
    main()
