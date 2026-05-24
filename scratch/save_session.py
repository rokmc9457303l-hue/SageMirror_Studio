import os
from pathlib import Path
from datetime import datetime

def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    ver = "v15.9.34.8"
    session_dir = Path(r"C:\SageMirror_Production\00_Obsidian\sessions")
    session_dir.mkdir(parents=True, exist_ok=True)
    filepath = session_dir / f"session_{ts}_{ver}.md"

    content = f"""# 작업 세션 보고서 ({datetime.now().strftime('%Y-%m-%d %H:%M')})

## 📌 버전 정보
- **버전**: {ver}

## 📋 변경 요약
- **실행 연결 스크립트 수정**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs`가 최신 안정본인 `app_v15_9_34_8.py`를 실행하도록 타겟 변경
- **디버그 빌드 스크립트 고도화**: `RUN_DEBUG.bat`에서 `app_v15_9_34_8.py`와 `sage_popups.py` 두 파일의 문법적 무결성(`py_compile`)을 모두 검증한 후 Streamlit을 구동하도록 개선

## 🔍 최종 기능 점검 완료 목록
1. **감정기반 RAG 검색**: `RAG_CATEGORY_MAP` 분류, 1차 옵시디언 검색 및 2차 웹 검색(Gemini/Tavily) 보완 연동, `TagIndex` 연결 및 파일 잠금 흐름 정상 확인.
2. **젬마 어시스턴트**: `popup_assistant()` 내 현재 파트 인식 및 컨텍스트/규칙서 주입, 대화 결과 옵시디언 자동 저장 흐름 정상 확인.
3. **파일 업로드 저장 기능**: 📎 `파일 업로드 저장` 탭을 통한 다중 포맷 텍스트 추출, Gemma 활용 분석, 전체 8개 파트 공용 `References` 기억 저장 및 `TagIndex` 연결 및 잠금 흐름 정상 확인.

## 🚀 다음 작업 예정
- 파트 5~8 세부 기능 운영 및 고도화 테스트
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"Session saved to {filepath}")

if __name__ == "__main__":
    main()
