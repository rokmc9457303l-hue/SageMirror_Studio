# 📘 TubeMaster Studio 시스템 통합 매뉴얼 (v1.0)

이 문서는 '현자의 거울' 채널의 자동화 생산 라인 운영을 위한 표준 지침서입니다.

## 1. 하드웨어 구성 (실행 도구)
- **지휘소(v3.8.1)**: `YouTube_Analyzer.html` (기획 및 데이터 추출)
- **배달부(v1.0)**: `CapCut_Auto_Assembler.py` (자동 조립 엔진)
- **공장(Factory)**: `99_Output_Factory` (데이터 보관소)

## 2. 생산 공정 5단계
### 1단계: 기획 (Planning)
- 지휘소 앱에서 벤치마킹 데이터 분석 및 주제 확정.
- AI를 통해 대본(Script)과 이미지 프롬프트(Prompts) 생성.

### 2단계: 재료 생성 (Asset Creation)
- TTS 도구를 사용하여 대본을 음성 파일로 변환.
- 나노 바나나를 사용하여 프롬프트를 이미지 파일로 변환.

### 3단계: 입고 (In-take)
- `1_Narration`: 음성 파일 입고.
- `2_Images`: 이미지 파일들 입고.
- `3_Data`: `draft_content.json` 파일 입고 (지휘소에서 Download).

### 4단계: 조립 (Assembly)
- 배달부 앱 실행 -> 스캔 -> 조립 시작.
- `COMPLETED_PROJECT` 폴더 생성 확인.

### 5단계: 출고 (Export)
- 캡컷에서 프로젝트 로드 후 최종 감성 마감 및 렌더링.

---
## 💡 유지보수 가이드
- 대본의 스타일 수정이 필요할 경우 `10_Wiki/🚀 Skills/Knowledge_Usage_Skill.md`를 수정하십시오.
- 새로운 벤치마킹 채널은 `20_Meta/Master_Context.md`에 업데이트하십시오.
