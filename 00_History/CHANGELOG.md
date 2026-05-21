# 🪞 현자의 거울 스튜디오 — CHANGELOG

## v13.33 — 2026-05-21 [마이너/기능완성]
### 변경 내용
- **Part 2 Step 2 (채널 벤치마킹) 3단 버튼 구조 및 백업 시스템 개편**:
  - 채널 벤치마킹(`tab_bench`), 자료 조사(`tab_research`), 총괄 기획안(`tab_plan`) 전 영역에 3단 버튼 레이아웃(AI 실행 / 로컬 자동저장 완료 / 옵시디언 백업 완료) 적용
  - 결과물 생성 완료 시 RAG 키워드 자동 추출 후 옵시디언 아카이브 이중화 저장 및 GitHub Auto-Push 연동 완료
- **프롬프트 팝업 편집 기능 연동**:
  - 각 탭의 젬마 프롬프트 박스 하단에 `📝 프롬프트 팝업 편집` 버튼 추가 및 범용 팝업 에디터 `popup_edit_text_value` 연동 완료
- **데이터 흐름 및 파이프라인 연동 강화**:
  - Part 2 진입 시 `p2_channel_url`이 비어 있는 경우 Part 1의 `p1_channel_url`을 자동 상속받아 연동되도록 데이터 흐름 개선
  - `generate_research_draft()` 함수에 `custom_prompt` 파라미터를 추가하여 사용자가 편집한 커스텀 자료조사 프롬프트가 실제 Gemma AI에 주입되어 호출되도록 버그 수정
- **엔트리포인트 동기화**:
  - `RUN_APP.bat` 실행 타겟 및 앱 실행 버전을 `app_v13_33.py`로 갱신 완료

### 영향 파트
- **Part 2 (Alchemist)**: 채널 벤치마킹, 자료 조사, 총괄 기획안 전 단계의 UI 개편 및 프롬프트 편집 팝업 연동

### 수정 파일
- `app_v13_33.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

## v13.28 — 2026-05-21 [마이너/기능완성]
### 변경 내용
- **Part 3-4 Architect & Writer 하단부 3단 버튼 구조 통일**:
  - Step 2 구조 설계(🏗️) 및 Step 3 Writer의 나레이션(🎙️), 이미지(🖼️), 캡컷([CINEMA]) 전 영역에 Part 1과 동일한 3단 버튼 레이아웃(시작 / 로컬 자동저장 완료 / 옵시디언 자동백업 완료) 완성
  - 각 영역 시작 시 결과물 초기화 → 생성 완료 즉시 젬마 키워드 자동 세분화 → 옵시디언 RAG 폴더(ScriptDrafts) 저장 → Git Push 파이프라인 적용
  - 예비용 수동 백업 버튼 추가(각 결과물 존재 시 표시)
  - Part 2 → Part 3-4 데이터 수신 상태 패널을 통해 선행 데이터 의존성 검증 유지
- **세션 스테이트 영속화 강화**:
  - p34 인디케이터 키 8종(p34_arch_saved/obsidian, p34_narr_saved/obsidian, p34_img_saved/obsidian, p34_cap_saved/obsidian)을 기본값 초기화 블록 및 `keys_to_save` 리스트에 추가하여 탭 전환/새로고침 후에도 상태 유지
- **엔트리포인트 동기화**: `RUN_APP.bat` 및 앱 내부 실행 버전을 `app_v13_28.py`로 갱신

### 영향 파트
- **Part 3-4: Architect & Writer**: Step 2 구조 설계 + Step 3 나레이션/이미지/캡컷 전 영역 UI 고도화

### 수정 파일
- `app_v13_28.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

## v13.27 — 2026-05-21 [마이너/기능완성]
### 변경 내용
- **Part 1 Librarian 3단 분석 엔진 UI 활성화 및 RAG 자동 백업 완전 이식**:
  - `tab_bench` (1️⃣ 벤치마킹 분석) 및 `tab_research` (2️⃣ 자료 조사 결과) 탭에 3단 버튼 구조 (시작 / 로컬 자동저장 / 옵시디언 자동백업) 및 RAG 기반 키워드 세분화 백업 시스템 완성
  - 텍스트 입력창 양방향 세션 스테이트 연동 및 수정 기능 활성화 (NameError 제거를 위한 Streamlit 바인딩 로직 적용)
  - 수동 백업 시 Git Push 연계 로직 탑재 및 예외 처리 견고화
- **엔트리포인트 동기화**: `RUN_APP.bat` 및 앱 내부 실행 버전을 `app_v13_27.py`로 갱신

### 영향 파트
- **Part 1: Librarian**: 3단 분석 엔진 1, 2단계 UI 고도화, 자동 백업 상태 유지, Git Push

### 수정 파일
- `app_v13_27.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

## v13.26 — 2026-05-21 [패치/안정화]
### 변경 내용
- **Part 1 Librarian 3단 분석 엔진 영속성 보존 및 상태 무결성 확보**:
  - `app_v13_25.py`에서 발생할 수 있는 텍스트 영역 내 미보존 및 상태 소실 버그를 완전히 수정하여 `app_v13_26.py`로 버전 업
  - 각 스텝의 입력 텍스트 영역에 `on_change` 콜백을 적용하여 탭 전환 및 앱 Rerun 시에도 입력값이 안정적으로 보존되도록 구현
  - 벤치마킹, 자료조사, 최종 기획안 단계의 시작 버튼 클릭 시 기존 결과 및 인디케이터 상태가 올바르게 초기화되도록 세션 관리 적용
  - 시작/로컬저장/옵시디언 백업의 3단 동적 상태 표시(인디케이터) 레이아웃을 Streamlit 정렬에 맞게 개선하여 시각적 직관성 확보
- **엔트리포인트 동기화**: `RUN_APP.bat` 및 앱 내부 실행 버전을 `app_v13_26.py`로 갱신

### 영향 파트
- **Part 1: Librarian**: 상태 보존, 3단 인디케이터 UI, 갱신 및 백업 로직

### 수정 파일
- `app_v13_26.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

## v13.25 — 2026-05-21 [마이너/기능추가]
### 변경 내용
- **Part 1 Librarian 3단 분석 엔진 활성화 및 UI 고도화**:
  - 마스터 PIN 잠금 해제 시, 3단 엔진의 각 프롬프트 텍스트 영역(`st.text_area`)을 활성화하여 직접 편집 및 복사/붙여넣기가 가능하도록 변경
  - 분석 결과 출력 화면에 대해 직접 수정이 가능한 넉넉한 크기(`height=350`)의 수정용 텍스트 영역을 메인 화면에 기본 제공
  - 벤치마킹 분석 완료 후 결과 원본 텍스트를 직접 수정하고, 이를 기반으로 주제 20개를 다시 파싱할 수 있는 `🔄 수정 텍스트 기반 주제 재파싱` 기능 탑재
- **옵시디언 자동 저장 파이프라인 연동 및 이중화**:
  - 각 스텝(벤치마킹, 자료조사, 최종 기획안) 하단에 동적 태깅 키워드 입력란 추가
  - `💾 [스텝명] 저장 및 옵시디언 자동 백업` 단일 버튼을 통해, 입력된 태그를 옵시디언 규칙서 포맷(`[[개념]]` 링크 및 `#태그`)에 맞춰 포맷팅 후 `00_Obsidian_Archive` 하위 지정 디렉토리에 이중화 저장
  - 저장 시 `lock_file_readonly`를 통한 읽기전용 잠금 처리와 `auto_git_push`를 활용한 GitHub 백업 자동 실행 및 toast 알림 연동 완료
- **Part 1 전용 Gemma 분석 API 함수 신규 정의**:
  - Part 2와의 의존성을 완벽히 격리하기 위해 `analyze_channel_to_topics_p1`, `generate_research_draft_p1`, `generate_final_planning_p1` 함수를 신규 생성하여 동적 프롬프트가 안전하게 전달 및 실행되도록 격리
- **엔트리포인트 동기화**: `RUN_APP.bat` 및 앱 내부 실행 버전을 `app_v13_25.py`로 갱신

### 영향 파트
- **Part 1: Librarian**: 3단 분석 엔진 UI 활성화, 옵시디언 자동 저장 및 Git 백업, 분석 API 격리 적용

### 수정 파일
- `app_v13_25.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

## v13.17 — 2026-05-19 [마이너/패치]
### 변경 내용
- **Part 3-4 탭 기반 UI 개편**: 3분할(Columns) 구조를 Part 1, 2와 동일한 가로 탭(Tabs) 구조로 리팩토링 (나레이션 / 이미지 프롬프트 / 캡컷 JSON)
- **프롬프트 뷰어 추가**: 각 탭 상단에 현재 단계의 Gemma 프롬프트 직관적 표시
- **팝업창(Dialog) 신설**:
  - `popup_edit_narration_p34()`, `popup_edit_image_p34()`, `popup_edit_capcut_p34()` 신설: 좁은 Column에서 벗어나 넓은 팝업창에서 결과물을 검토, 수정 및 다운로드(`.txt`, `.json`) 가능하도록 기능 업그레이드
- **버전업**: 안전을 위해 원본을 `app_v13_17.py`로 분리 및 `RUN_APP.bat` 업데이트

### 영향 파트
- **Part 3-4 (Architect & Writer)**: 탭 렌더링, 신규 팝업창 연동, 데이터 저장 및 다운로드 로직

### 수정 파일
- `app_v13_17.py`
- `RUN_APP.bat`

## v13.16 — 2026-05-19 [마이너/패치]
### 변경 내용
- **Part 2 탭 기반 UI 개편**: 3분할(Columns) 구조를 Part 1과 동일한 가로 탭(Tabs) 구조로 리팩토링
- **프롬프트 뷰어 추가**: 각 분석 단계(벤치마킹, 자료조사, 기획안) 탭 상단에 현재 단계의 Gemma 프롬프트 직관적 표시
- **팝업창(Dialog) 고도화**:
  - `popup_edit_benchmarking_p2()` 신설: 20개 주제 추출 결과를 넓은 팝업창에서 스크롤 및 다운로드 가능하도록 개선 (기존 Expander 제거)
  - `popup_edit_research_p2()`, `popup_edit_planning_p2()`: 넓은 텍스트 영역 및 `.txt` 다운로드 버튼 추가
- **버전업**: 안전을 위해 원본을 `app_v13_16.py`로 분리 및 `RUN_APP.bat` 업데이트

### 영향 파트
- **Part 2 (Alchemist)**: 탭 렌더링, 팝업창 교체, 자동저장 로직 보완

### 수정 파일
- `app_v13_16.py`
- `RUN_APP.bat`## v13.15 — 2026-05-19 [마이너/패치]
### 변경 내용
- **Part 1 UI/UX 고도화**: 각 분석 단계(벤치마킹, 자료조사, 기획안) 탭 상단에 현재 단계의 Gemma 프롬프트를 직관적으로 보여주는 가로형 텍스트 박스 추가
- **결과물 팝업 인터페이스 완벽 연동**: 기존 팝업 함수(`popup_edit_research`, `popup_edit_planning`, `popup_edit_benchmarking`)를 개선하여, 넓은 화면에서 스크롤 및 복사/수정이 원활하도록 UI 개선 및 txt 다운로드 버튼 추가
- **버전업**: 안전을 위해 원본을 `app_v13_15.py`로 분리 및 `RUN_APP.bat` 업데이트

### 영향 파트
- **Part 1 (Librarian)**: 프롬프트 표시 및 팝업창 렌더링

### 수정 파일
- `app_v13_15.py`
- `RUN_APP.bat`

## v13.14 — 2026-05-19 [마이너/패치]
### 변경 내용
- **Part 1 UI 리팩토링**: `render_part1()` 하단의 3분할 Column 구조를 Part 4와 동일한 탭(Tabs) 구조로 개편
- **자동 저장 고도화**: Part 1 각 단계별 결과물 생성 후 `save_workspace_state()` 자동 호출 추가
- **벤치마킹 팝업 신설**: 20개 채널 추천 주제 결과를 팝업창에서 스크롤 및 복사할 수 있는 `popup_edit_benchmarking()` 추가
- **옵시디언/GitHub 알림 강화**: 백업 완료 시 `st.success`와 `st.toast`를 통해 저장 경로 및 성공 여부 명시
- **버전 패치**: `app_v13_14.py` 기반으로 메인 파일 갱신 (`RUN_APP.bat` 업데이트 완료)

### 영향 파트
- **Part 1 (Librarian)**: UI/UX 구조 변경 및 데이터 보존성 확보

### 수정 파일
- `app_v13_14.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

---
## v14.0 — 2026-05-15 20:55 [메이저 릴리즈]
### 변경 내용
- **영상 파트(Part 5) 로직 복구**: `app_v13_2.py`의 완성된 로직을 `app_v14_0.py`에 완전 이식
- **나레이션 모듈(Part 6) 통합**: 신규 오디오 파이프라인 구축
- **UI/UX 복원**: 이모지 및 테마 일관성 확보

### 변경 내용
- **Part 6 나레이션 & BGM 완전 구현**: `render_part7_narration()` 및 4탭 UI 구축 (대본 정제 / BGM 설계 / CosyVoice 연동 / 오디오 검수)
- **CosyVoice 연동 엔진**: Gradio URL 기반 연결 테스트 및 나레이션 씬별 TXT 일괄 생성 로직 탑재
- **BGM 큐시트 자동 설계**: 젬마(Gemma)를 활용한 기-승-전-결 구간별 악기(첼로/피아노) 및 감정 톤 자동 배정 기능 추가
- **팝업 시스템 확장**: 나레이션 마스터 가이드, 프로토콜, 정제본, BGM 큐시트용 전용 팝업 4종 신설
- **상태 관리 고도화**: p7 계열 세션 스테이트 10개 추가 및 `workspace_state.json` 자동 동기화 지원
- **버전 업그레이드**: v13.3 → v14.0 상향 조정 및 `app_v14_0.py` 프로덕션 배포

### 영향 파트
- **Part 6 (Narration & BGM)**: 핵심 기능 활성화 및 데이터 연동 완료
- **CapCut Bridge**: 나레이션/BGM 에셋 연동 준비 완료

### 수정 파일
- `app_v14_0.py` (v13.3 기반 신규 생성)
- `RUN_APP.bat` (엔트리 포인트 변경)
- `CHANGELOG.md` (업데이트 로그 추가)

---

## v13.3 — 2026-05-15 19:45 [메이저]
### 변경 내용
- **UI 이모지 일괄 복원**: `[MIRROR]`, `[BOT]`, `[SAVE]` 등의 텍스트 라벨을 `🪞`, `🤖`, `💾` 등 시각적 이모지로 일괄 복원하여 UI 직관성 강화
- **디자인 가독성 개선**: 사이드바 라디오 버튼 및 각 파트 헤더의 시각적 요소를 정비
- **ASCII 안전 프로토콜**: 젬마 프로토콜(Part 4, 5) 내 핵심 시스템 지시는 ASCII 형식을 유지하여 로컬 Ollama 파서의 SyntaxError 재발 방지
- **환경 동기화**: `RUN_APP.bat` 및 앱 내부 버전 정보를 `v13.3`으로 일괄 동기화 및 프로덕션 오케스트레이터 교체

### 영향 파트
- **UI 시스템**: 전 파트(Part 1~8) 시각적 요소
- **오케스트레이터**: `app_v13_3.py` 시스템 코어

### 수정 파일
- `app_v13_3.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

---

## v13.2.4 — 2026-05-15 19:05 [패치]
### 변경 내용
- **최종 구문 정제 (Final Syntax Sanitization)**: Part 3-4 (Writer) 모듈 내에서 잔존하던 잘못 이스케이프된 트리플 따옴표(`f\"\"\"`, `\"\"\"`)를 모두 제거하고 정상적인 따옴표로 복구
- **코드 무결성 복구**: 이전 작업 중 발생한 Part 5(Video) 내의 의도치 않은 코드 주입 사고를 발견하고 원본 로직으로 완전 복구
- **버전 패치**: v13.2.3 → v13.2.4 상향 조정 및 프로덕션 안정화 완료

### 영향 파트
- **Part 3-4 (Architect & Writer)**: 112씬 구조 설계 및 대본 집필 시의 SyntaxError 해결
- **Part 5 (Video Production)**: 손상되었던 C-1 프롬프트 생성 루프 및 검증 엔진 복구 완료

### 수정 파일
- `app_v13_2.py`
- `CHANGELOG.md`

---

## v13.2.3 — 2026-05-15 18:55 [패치]
### 변경 내용
- **구문 오류 수정 (SyntaxError Fix)**: `st.markdown` 호출 시 잘못 이스케이프된 트리플 따옴표(`\"\"\"`)를 정상적인 따옴표(`"""`)로 복구
- **추가 산성화**: UI 가이드 내의 유니코드 화살표(`→`)를 ASCII 하이픈(`->`)으로 교체
- **버전 패치**: v13.2.2 → v13.2.3 상향 조정

### 영향 파트
- **App Execution**: 비정상적인 이스케이프로 인한 실행 불가 현상 해결
- **Part 4 & 5**: 작업 가이드(expander) 내의 구문 오류 수정

---

## v13.2.2 — 2026-05-15 18:50 [패치]
### 변경 내용
- **프로토콜 ASCII 산성화**: `P5_PROTO_DEFAULT` 및 `P6_PROTO_DEFAULT` 초기값을 특수 기호가 없는 안전한 ASCII/영문 기반 텍스트로 교체
- **버전 패치**: v13.2.1 → v13.2.2 상향 조정

---

## v13.2.1 — 2026-05-15 18:30 [패치]
### 변경 내용
- **전역 이모지 산성화 (Emoji Sanitization)**: Python `SyntaxError` 유발 요인인 비ASCII 이모지 캐릭터를 전역적으로 제거하고 텍스트 태그(`[OK]`, `[WARN]`, `[BOT]` 등)로 교체
- **구문 안정화**: `P5_PROTO_DEFAULT`, `P6_GEMMA_PROTOCOL_V2` 등 핵심 상수 내 유니코드 캐릭터 정리
- **버전 패치**: v13.2 → v13.2.1 상향 조정

### 영향 파트
- **App Core**: 파싱 에러 해결 및 실행 안정성 확보
- **UI/UX**: 모든 파트의 이모지 아이콘이 텍스트 태그로 변경됨

### 수정 파일
- `app_v13_2.py`
- `sage_config.py`
- `CHANGELOG.md`

---

## v13.2 — 2026-05-15 18:00
### 변경 내용
- **Veo3 & Gemma Protocol v2.0 완전 통합**: Part 5 영상 제작 모듈에 YouTube Creative Director Edition 마스터 프롬프트 및 비디오 오케스트레이션 프로토콜 전문 주입
- **데이터 영속성 강화**: `init_session_state`의 기본값에 신규 프로토콜 텍스트를 상수로 정의하여 앱 초기 실행 시 자동 로딩되도록 개선
- **UI/UX 고도화**: 영상 파트 내 '젬마 프로토콜' 및 'Veo3 마스터' 섹션의 기본값을 신규 규격으로 동기화
- **버전 업그레이드**: v13.1 → v13.2 상향 조정 및 안정화

### 영향 파트
- **Part 5 (Video Production)**: 프로토콜 및 마스터 프롬프트 완전 탑재

### 수정 파일
- `app_v13_2.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

---

## v13.1 — 2026-05-15 13:10
### 변경 내용
- **Part 5 (Video Production) 내용 교체**: 이미지 파트 placeholders를 실제 영상 제작(Veo3/Opal) 규격으로 전환
- **Veo3 마스터 프롬프트 및 영상 프로토콜 섹션 고도화**: YouTube Creative Director 페르소나 및 영상 지시 규격(P6_PROTO_DEFAULT) 적용
- **작업 순서(Workflow) 업데이트**: Google Opal 기반의 112씬 8계정 병렬 렌더링 루틴 명세화
- **세션 스테이트 동기화**: `p6_veo3_master_prompt`, `p6_gemma_protocol`, `p6_protocol_loaded` 키를 통한 데이터 영속성 확보
- **버전 패치**: v13.0 → v13.1 상향 조정

### 영향 파트
- **Part 5 (Video Production)**: 영상 제작 파이프라인 데이터 및 UI 명세화 완료

### 수정 파일
- `app_v13.py`
- `CHANGELOG.md`

---

## v13.0 — 2026-05-15 11:30
### 변경 내용
- **Part 5 (Video Production) 뼈대 구현**: `render_part6_video()` 및 4개 탭 헬퍼 함수(`_p6_tab_veo3/gemma/opal/check`) 신규 생성
- **UI/UX 복제 및 전환**: Part 4(Image)의 4탭 UI 구조를 그대로 계층 복사하여 영상 공정용 레이아웃으로 전환
- **헤더 및 제목 갱신**: "Part 5 — Video Production (Veo3 × Google Opal × CapCut)" 명칭 적용
- **보안 및 권한**: `p6_vid_pin_input`, `unlock_part6_vid` 키를 통한 파트 잠금 해제 로직 적용 (PIN: 7777)
- **라우팅 블록 연결**: `Part 5` 선택 시 `render_part6_video()` 함수가 호출되도록 라우팅 블록 교체
- **세션 스테이트 초기화**: `init_session_state()`에 영상 파트 전용 핀 및 잠금 키 추가
- **버전 업그레이드**: 전역 버전을 v12.0.1에서 v13.0으로 상향 조정

### 영향 파트
- **Part 5 (Video Production)**: 신규 기능 뼈대 완성
- **Routing**: `Part 5` 라우팅 활성화
- **Initialization**: 영상 파트 전용 세션 키 등록

### 수정 파일
- `app_v13.py`
- `RUN_APP.bat`
- `CHANGELOG.md`

---

## v12.0.1 — 2026-05-15 09:23 [패치]

### 변경 내용
- `C-1 단독 생성 프롬프트`: `[A-MASTER]→[@배경]` → `[인물1]→[배경]` 교체
- `C-1 전체 일괄 프롬프트`: `[A-MASTER]+[@배경]` → `[인물1]+[배경]` 교체
- `정규식 검증 로직`: `"[A-MASTER]" not in eng` → `"[인물1]" not in eng` 교체, 경고 메시지 "FlowRun [인물1] 태그 누락"으로 변경

### 변경 이유
FlowRun 크롬 확장은 `[인물1]`, `[배경]` 태그로 레퍼런스 이미지를 자동 첨부함.
`[A-MASTER]` 태그는 FlowRun이 인식하지 못하므로 전면 교체.

### 영향 파트
- Part 4 → `_p5_tab_c()` 내부 (C-1 생성 프롬프트 2곳 + 검증 1곳)

### 수정 파일
- `app_v11.py`

---

## v12.0 — 2026-05-15 09:04

### 변경 내용
- `render_part5_image()` 완전 구현: 헬퍼 분할 전략(_p5_tab_a/b/c/v)으로 4탭 구성
- `popup_edit_image_master()` 신규 추가 (이미지 마스터 규정서 편집 팝업)
- `popup_edit_a_result()` / `popup_edit_b_result()` / `popup_edit_c_result()` 추가 (history 뒤로가기 방식)
- 저장 경로 통일: `.md` → `path_obsidian` / CSV → `path_assets` / 하드코딩 제거
- A파트/B파트 저장 시 `lock_file_readonly` + `auto_git_push` 자동 적용
- C파트 최종 저장 시 `.md`(path_obsidian) + `.csv`(path_assets) 동시 저장
- `세션 스테이트 p5 계열 키 14개` 추가 (p5_gemma_protocol, p5_a/b/c_result 등)
- Part 4 라우팅 블록 → `render_part5_image()` 단일 호출로 교체
- 파일 상단 docstring v11.1 → v12.0 갱신

### 영향 파트
- Part 4 (Image Consistency) — 완전 구현
- `init_session_state()` — p5 계열 키 추가
- 파트 라우팅 블록 — Part 4 placeholder 제거

### 수정 파일
- `app_v11.py`

---

## v11.1 — 2026-05-15 08:31

### 변경 내용
- `세션 스테이트 누락 키 추가`: `pending_stream`, `p6_opal_df`, `p6_save_done`, `p7_capcut_df`, `p8_check_result`, `p8_save_done` 6개 키를 `init_session_state()` defaults 딕셔너리에 추가 (기존 `obsidian_history` 등 5개 키는 이미 존재 확인)
- `라우팅 블록 재구성`: Part 4~8 각각 독립 `elif` 분기로 분리. 각 파트에 플레이스홀더 UI + 옵시디언 백업 버튼 포함. 향후 `render_part5_image()` / `render_part6_opal()` / `render_part7_capcut()` / `render_part8_dashboard()` 연결 예약
- `버전 주석 업데이트`: 파일 상단 docstring v11.0 → v11.1 갱신

### 영향 파트
- `init_session_state()` — 세션 키 추가
- 파트 라우팅 블록 (`if part.startswith(...)`) — Part 4~8 분기 독립화
- 파일 최상단 docstring — 버전 정보

### 수정 파일
- `app_v11.py`

---

## v11.0 — 2026-05-13

### 변경 내용
- Part 2 ↔ Part 3-4 역할 분리 및 데이터 연동 강화

### 수정 파일
- `app_v11.py`

---
