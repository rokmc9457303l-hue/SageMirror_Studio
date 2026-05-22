
## v15.9.10 — 2026-05-22 23:59
### 변경 내용
- **리서치 자동저장 제어 및 모니터링 강화**:
  - 최상단 공통 옵시디언 규칙서 하단 영역을 3열 분할 레이아웃으로 재구성하여 `[SEARCH] 편집`, `💾 자동저장: ON/OFF`, `📂 저장 확인` 버튼 배치.
  - `📂 저장 확인` 팝오버를 통해 최근 저장된 리서치 기록을 최대 8개까지 실시간 확인 가능하도록 UI 개선.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 의 실행 대상 파일을 `app_v15_9_10.py`로 일괄 업데이트.
### 영향 파트
- **App Core**: 상단 공통 규칙서 패널 하단 UI 고도화, 배치 파일 실행 파일 포인터 갱신.
### 수정 파일
- `app_v15_9_10.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.9 — 2026-05-22 23:40
### 변경 내용
- **전역 자동 웹 리서치 루프(Self-Research Loop) 도입 (최대 4회)**:
  - 로컬 Gemma 모델의 지식 한계를 보완하고 RAG 자료 부족 시 발생하는 가짜 정보(환각)를 방지하기 위해 자동 웹 검색 보완 루프 구현.
  - 젬마 호출 래퍼(`call_gemma`)에 Tavily API를 연동하여 `[NEED_RESEARCH: 검색어]` 태그 감지 시 백그라운드에서 최대 4회까지 자동으로 인터넷 검색을 수행하고 지식을 스스로 보강하는 RAG 체인 탑재.
  - 검색된 결과는 `[SOURCE: 웹 — URL — 검색일: YYYY-MM-DD]` 형식의 출처와 함께 최종 결과물에 깔끔하게 병합되도록 설계.
- **배치 파일 실행 대상 및 버전 메타정보 업데이트**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat`의 Streamlit 실행 타겟을 `app_v15_9_9.py`로 변경 완료.
  - 메인 앱 파일 상단 주석 및 page_title 버전을 `v15.9.9`로 상향 동기화.
### 영향 파트
- **App Core**: `call_gemma` 래핑 함수 고도화, 버전 업데이트 및 구동 배치 파일 타겟 포인터 갱신.
- **전체 파트 (Part 1~8)**: 별도의 UI 코드 수정 없이 모든 AI 호출 시 자동 웹 리서치 루프 작동.
### 수정 파일
- `app_v15_9_9.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.8 — 2026-05-22 23:05
### 변경 내용
- **파트 2 (Alchemist) 3단 분석 프롬프트 고도화**:
  - 기존 프롬프트 내용을 대대적으로 개편하여 40~70대 시청자의 인생 경험 및 감정 고통(고독, 후회, 상실, 관계, 용서 등)에 맞춘 구체적인 벤치마킹 및 주제 추출 가이드를 구현.
  - 철학(쇼펜하우어, 칼 융, 빅터 프랭클), 성경(시편, 잠언, 전도서 등), 에세이(몽테뉴 등), 다크심리학 지식을 3원 융합하는 단계별 지식 융합 상세 프로세스를 명시.
  - Part 3-4 (Architect & Writer)에 완결된 대본 작업 패킷(기승전결 구조, @Protagonist 내레이터 지침)을 성공적으로 인계하기 위한 전달 패킷 설계 지침 도입.
  - 프롬프트 기본값에 맞게 `Librarian` (수석 조사관) 명칭을 `Alchemist` (수석 연금술사) 페르소나 명칭으로 올바르게 수정 반영.
- **배치 파일 실행 대상 업데이트**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat`의 Streamlit 실행 타겟을 `app_v15_9_8.py`로 변경 완료.
- **Python 3.14 호환성 검증**:
  - Python 3.14 환경에서의 구문 오류 방지를 위해 `py_compile`을 통한 정적 컴파일 검증 성공.
### 영향 파트
- **Part 2 (Alchemist)**: 벤치마킹, 지식 융합, 전달 패킷 프롬프트 교체 및 페르소나 명칭 정정.
- **App Core**: 버전 업데이트(v15.9.8) 및 구동 배치 파일 타겟 포인터 갱신.
### 수정 파일
- `app_v15_9_8.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.2 — 2026-05-22 13:12
### 변경 내용
- **파트 1 채널 탐색기 전면 개편**:
  - 기존 Tavily 단독 검색 5개 채널 표출 구조를 제미나이(Gemini) + Tavily 큐레이션 통합 구조로 격상.
  - "채널 탐색 시작" 버튼 클릭 시, [제미나이 7종 검색어 자동 설계 -> Tavily 후보 30개 수집 -> 제미나이 AI 복제/표절 배제 및 필터링 -> 최종 10개 큐레이션 및 1순위 자동 확정]의 일괄 자동화 프로세스 구축.
  - 탐색된 10개 채널은 전용 팝오버 카드로 깔끔하게 표시하며, 링크 클릭 시 즉시 새 창으로 해당 유튜브 채널이 열리도록 UI 개선.
  - API 할당량 초과 대비 및 유연성을 위해 헤더 내 Gemini 모델 선택기(gemini-2.0-flash-exp, gemini-1.5-flash 등) 동적 전환 UI 지원.
  - 사이드바 설정 변경 섹션 내 `🤖 Gemini API Key` 입력 필드 연동.
- **세션 상태 및 영속화 연동**:
  - `gemini_api_key`, `p1_gemini_model`, `p1_channel_top10`, `p1_benchmark_channel`, `p1_search_keywords`를 세션 초기화(`init_session_state`) defaults 및 `save_workspace_state` 저장 키 리스트에 추가하여 영구 백업 보장.
### 영향 파트
- **Part 1 (Librarian)**: 채널 탐색기 UI 및 검색 자동화 엔진 교체
- **App Core**: 사이드바 설정 필드 추가, 세션 상태 및 자동 저장 파이프라인 연동
### 수정 파일
- `app_v15_9_2.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.1 — 2026-05-22 08:51
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
# 🪞 현자의 거울 스튜디오 — CHANGELOG

## v15.9 — 2026-05-22 00:20 [패치/영상생성/통합저장파이프라인]
### 변경 내용
- **파트 5 (영상 생성) 통합 저장 및 백업 시스템 구축**:
  - `save_video_production_all` 통합 저장 함수와 개별 저장 버튼의 핸들러 연동 완료.
  - "오팔 배분 외부 저장 및 백업" 버튼(`p6_step3_outputs_save_btn`) 클릭 시, `save_video_production_all` 함수를 호출하여 외부 출력 저장소(`C:\SageMirror_Outputs`)에 CSV 백업을 기록함과 동시에 옵시디언 자동 저장 및 GitHub 자동 push가 단일 트랜잭션으로 연동되도록 구현.
  - "옵시디언 자동 백업" 버튼(`p6_video_obsidian_backup_btn`) 역시 `save_video_production_all` 단일 통합 함수를 호출하도록 단일화하여 데이터 정합성 보장 및 중복 저장 코드를 완전 제거함.
  - 세션 데이터 호출 시 `.get()` 안전 패턴을 적용하여 Streamlit NameError 및 KeyError 사태를 원천 차단.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 실행 타겟을 `app_v15_9.py`로 변경.

### 영향 파트
- **Part 5 (Video Production)**: 오팔 배분 데이터 백업 및 옵시디언 백업 간의 파이프라인 통합.
- **App Core / Batch Scripts**: 실행 환경을 `app_v15_9.py`로 업데이트.

### 수정 파일
- `app_v15_9.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.8 — 2026-05-22 00:15 [마이너/영상생성개편/저장파이프라인]
### 변경 내용
- **파트 5 (영상 생성) 3단 스텝 가로 배치 레이아웃 구현**:
  - 기존 4탭 구조를 전면 폐지하고 `col1, col2, col3` 가로 3단 레이아웃으로 전면 개편.
  - **스텝 1 (좌측)**: 이미지 파트(Part 4)에서 수신한 대본/프롬프트 데이터 파싱 및 실시간 편집.
  - **스텝 2 (중간)**: Gemma AI 연동을 통해 장면 생성용 JSON 구조가 결합된 4단 매핑 데이터(`씬번호 | 대본 | 이미지프롬프트 | @장면을 만드는 JSON프롬프트@`) 생성 및 정규식 검증 기능 제공.
  - **스텝 3 (우측)**: 4단 매핑 데이터를 계정당 최대 12개 이하의 씬으로 자동 분배(112씬 기준 10개 계정 동적 확장)하여 Opal 작업용 CSV 생성 및 저장.
- **외부 격리 회차별 자동 저장 파이프라인 (`C:\\SageMirror_Outputs`) 구축**:
  - 소스코드 디렉토리와 제작 에셋 간의 혼선을 방지하기 위해 외부 저장 폴더 생성.
  - 회차별(에피소드명 기반) 하위 폴더 구조 생성: 대본(`01_Script`), 이미지(`02_Image`), 영상(`03_Video`), 나레이션(`04_Narration`), BGM(`05_BGM`).
  - 파트 3~6 저장 완료 시 해당 외부 디렉토리로 완성본 에셋 자동 격리 복사.
- **대본 파트(Part 3-4) 감지식 자동 백업 적용**:
  - 접근 금지 구역인 `render_part34()`를 수정하지 않고, 하단 라우팅 단에서 세션 플래그(`p34_arch_obsidian_saved` 등) 변화를 감지하여 외부 `01_Script\script_final.md`에 최종본을 복사하는 트리거링 시스템 구축.
- **Python 3.12+ 이스케이프 경고 해결**:
  - 주석 내 정규식 및 경로(`\S`) 등으로 인한 이스케이프 경고(SyntaxWarning) 현상을 `\\S` 등으로 이중 이스케이프 처리하여 Python 3.14 구동 안정성 확보.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 실행 타겟을 `app_v15_8.py`로 변경.

### 영향 파트
- **Part 5 (Video Production)**: 3단 가로형 스텝 UI 구축 및 Opal 씬 자동 분배 최적화.
- **Part 3~6 (Script, Image, Video, Narration, BGM)**: 외부 격리 폴더 (`C:\\SageMirror_Outputs`)로의 에셋 자동 복사 파이프라인 적용.
- **App Core**: 백업 감지 트리거 구현 및 파이썬 3.14 구동 호환성 패치.

### 수정 파일
- `app_v15_8.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.7 — 2026-05-22 00:05 [마이너/중간백업]
### 변경 내용
- **영상 파트 개편 및 저장 파이프라인 개발용 중간 징검다리 백업**:
  - 파트 5 UI 가로 3단 재구성 시범 적용 및 `C:\\SageMirror_Outputs` 입출력 인터페이스 프로토타이핑.
- **수정 파일**: `app_v15_7.py`

---

## v15.6.1 — 2026-05-21 23:10 [패치/UI보완/모델연동]
### 변경 내용
- **상단 '시스템 연동 및 동기화 상태' 패널 4개 카드 디자인 대칭성 확보**:
  - 카드 배치 비율을 `[1, 1, 1, 1]`로 균등화하고, 로컬 DB 카드와 동일한 배경색, 둥근 모서리, 그라데이션 테두리 래핑 스타일 통일.
  - 투명 absolute overlay 테크닉(:has 가상 클래스 선택자 활용)을 도입하여 RAG, Git, 동기화 카드의 내부 HTML 스타일이 로컬 DB 연결 카드와 100% 시각적으로 일치하도록 개선.
- **파트 1~8 전체 상단 헤더 내 모델 선택기 탑재 및 디자인 통합**:
  - 모든 파트의 최상단 타이틀 폰트 크기를 `font-size: 1.85em`로 확대하고, 우측 컨트롤 박스 레이아웃을 모델 선택기, 마스터 PIN, Sage Pop-up 버튼 3분할(`st.columns([3.8, 3.8, 2.4])`)로 재편.
  - 올라마(Ollama) 연동 모델 선택기(GEMMA4:E2B / GEMMA4:E4B)를 탑재하여 사용자가 세션 내에서 모델을 동적으로 전환 및 연동해 사용할 수 있도록 함.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 실행 대상을 신버전 `app_v15_6_1.py`로 갱신함.

### 영향 파트
- **App Core / Top Panel**: 시스템 연동 상태 카드의 디자인 대칭성 및 스타일 통일.
- **전 파트 (Part 1~8)**: 모델 선택기 연동 및 헤더 디자인 리팩토링 완료.

### 수정 파일
- `app_v15_6_1.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.6 — 2026-05-21 23:00 [마이너/UI개편/기능보완]
### 변경 내용
- **상단 '시스템 연동 및 동기화 상태' 패널 4개 카드 디자인 및 레이아웃 통일**:
  - 카드 배치 비율을 `[1, 1, 1, 1]`로 완벽히 균등화함.
  - 클릭 가능한 "옵시디언 RAG", "GitHub 연동", "전체 즉시 동기화" 카드를 클릭할 수 없는 "로컬 DB 연결" 카드(`sage-stat-card`)와 동일한 배경색, 둥근 모서리, 그라데이션 테두리 스타일로 래핑하여 디자인적 완결성 확보.
  - "전체 즉시 동기화" 카드에 골드 테두리 그라데이션(`.sage-stat-card.sync`)을 적용하여 렘브란트 다크 테마에 부합하는 고급스러운 시각 효과 구현.
- **파트 1~8 전체 상단 헤더 개편 및 모델 선택기 탑재**:
  - 모든 파트의 최상단 타이틀 폰트 크기를 `font-size: 1.85em`로 확대하고, 우측 컨트롤 박스 레이아웃을 모델 선택기, 마스터 PIN, Sage Pop-up 버튼 3분할(`st.columns([3.8, 3.8, 2.4])`)로 재편.
  - 올라마(Ollama) 연동 모델 선택기(GEMMA4:E2B / GEMMA4:E4B)를 탑재하여 사용자가 세션 내에서 모델을 동적으로 전환 및 연동해 사용할 수 있도록 함.
  - 파트 3, 파트 6, 파트 7, 파트 8의 남은 헤더 영역 개편을 일괄 마무리하여 전 파트 UI 일관성 달성.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 실행 대상을 신버전 `app_v15_6.py`로 갱신함.

### 영향 파트
- **App Core / Top Panel**: 시스템 연동 상태 카드의 디자인 대칭성 및 스타일 통일.
- **전 파트 (Part 1~8)**: 모델 선택기 연동 및 헤더 디자인 리팩토링 완료.

### 수정 파일
- `app_v15_6.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.4 — 2026-05-21 22:30 [패치/UI헤더개편]
### 변경 내용
- **파트 1~8 전체 상단 헤더 레이아웃 개편 및 디자인 통합**:
  - 파트 1부터 파트 8까지 전체 화면의 최상단 헤더에 있는 [마스터 PIN 입력부 + Sage Pop-up 버튼] 영역을 하나의 '우측 컨트롤 박스'로 통합함
  - 이 컨트롤 박스의 배경색(`linear-gradient(135deg, #131b2e 0%, #0c1220 100%)`)과 골드 테두리(`border: 1.5px solid #d4af6a44`)를 하단의 **실시간 데이터 연동 상황판**과 완전히 동일하게 통일하여 시각적 일관성과 정합성을 극대화함
  - PIN 입력창과 Pop-up 버튼 위젯의 세로 크기를 `38px`로 통일하고 수평 정렬을 엄격하게 맞춤
- **상하 공간 여백 최소화 및 초박형 구분선 교체**:
  - 상하 간격을 과도하게 늘리던 기존의 `st.divider()`를 두께 1px의 초박형 커스텀 골드 라인으로 교체하여 밀착형 레이아웃 구성
- **RAG Expander 기본 접힘 처리**:
  - 상단 RAG Vault 규칙서의 기본 상태를 접힘(`expanded=False`)으로 설정하여 스크롤 없이 핵심 작업 화면을 먼저 볼 수 있도록 공간 활용도를 개선함
- **구동 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 파일의 실행 대상을 `app_v15_4.py`로 갱신하여 신규 버전이 자동으로 구동되도록 정비함

### 영향 파트
- **전 파트 (Part 1~8)**: 최상단 헤더 UI 레이아웃, 정렬 및 테마 디자인 통합

### 수정 파일
- `app_v15_4.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.3 — 2026-05-21 22:05 [패치/UI단일화]
### 변경 내용
- **파트 6, 7, 8 중복 상단 expander 제거 및 UI 단일화**:
  - 파트 6(`render_part6_opal()`), 파트 7(`render_part7_capcut()`), 파트 8(`render_part8_dashboard()`) 함수 내부에 개별적으로 들어가 있던 중복 `with st.expander("📋 상단 공통: ...")` 구문 및 관련 RAG 뷰어 위젯들을 완전히 삭제함
  - 이로써 모든 파트가 상단 공통 패널(`render_top_panel()`)로 RAG 규칙 및 마스터 프롬프트를 일원화하여 표시하도록 UI를 단순화하고 중복 렌더링에 의한 시각적/기능적 이중화를 완벽하게 해결함
- **버전 및 구동 스크립트 갱신**:
  - `RUN_APP.bat` 실행 타겟을 `app_v15_3.py`로 갱신하여 신버전 안전 연동 확인
  - Python 3.14 컴파일 검사(`py_compile`)를 통해 에러 없음을 사전 검증함

### 영향 파트
- **Part 6 (Opal Dispatch)**: 중복 RAG expander 제거 및 UI 간소화
- **Part 7 (CapCut Bridge)**: 중복 RAG expander 제거 및 UI 간소화
- **Part 8 (Dashboard)**: 중복 RAG expander 제거 및 UI 간소화

### 수정 파일
- `app_v15_3.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.2 — 2026-05-21 21:58 [패치/UI통일]
### 변경 내용
- **상단 동기화 및 연동 패널 디자인 통일화**: 상단에 위치한 로컬 DB 연결 상태, 옵시디언 RAG, GitHub 연동 및 동기화 버튼 패널을 하단의 "실시간 데이터 연동 상황판"과 동일한 배경 그라데이션 및 골드 테두리(`border-radius: 14px`) 박스 모델로 감싸 디자인 일관성 대폭 향상 (사용자 요청 반영)
  - CSS 인접 형제 선택자를 활용해 Streamlit 렌더링 손상 없이 안전한 마크다운 HTML 래핑 구현
  - 개별 연동 카드의 배경과 코너 반경을 큰 래퍼에 어울리도록 정밀 튜닝하여 이중 보더 및 시각적 충돌 완화
- **구동 스크립트 연동**: `RUN_APP.bat` 실행 대상을 `app_v15_2.py`로 갱신

### 영향 파트
- **App Core / Top Panel**: 공통 상단 데이터 연동 패널의 디자인 스타일 통일

### 수정 파일
- `app_v15_2.py`
- `RUN_APP.bat`

---

## v15.1 — 2026-05-21 21:45 [패치/UI개선]
### 변경 내용
- **파트 6, 7, 8 PIN 경고 메시지 제거**: 파트 6(나레이션 & 배경음악), 파트 7(Shorts Creator / CapCut Bridge), 파트 8(캡컷 최종 조립 Dashboard)에서 마스터 PIN이 잠겨 있을 때 최상단에 노출되던 경고 메시지(`st.warning`)를 제거하여 UI의 시각적 복잡성 완화 (사용자 요청 반영)

### 영향 파트
- **Part 6 (Opal Dispatch)**: PIN 미입력 시 상단 경고 메시지 제거
- **Part 7 (CapCut Bridge)**: PIN 미입력 시 상단 경고 메시지 제거
- **Part 8 (Dashboard)**: PIN 미입력 시 상단 경고 메시지 제거

### 수정 파일
- `app_v15_1.py`
- `RUN_APP.bat`

---

## v14.0.1 — 2026-05-21 17:48 [패치/버그수정]
### 변경 내용
- **파트 6 변수 스코프 버그 수정**: `Opal 8계정 씬 자동 배분` 버튼 내부에서 `selected_bgm`/`mix_ratio` 를 외부 위젯 변수로 직접 참조하던 것을 `st.session_state.get()` 안전 접근으로 교체
  - 수정 전: `selected_bgm`, `mix_ratio` (위젯 로컬 변수 → 버튼 클릭 시 값 유실 가능성)
  - 수정 후: `_selected_bgm = st.session_state.get("p6_bgm_selection", ...)`, `_mix_ratio = st.session_state.get("p6_mixing_ratio", ...)` (세션 스테이트 경유 안전 참조)
- **파트 8 통계 변수 스코프 버그 수정**: `💾 파트 8 최종 생산 세션 백업` 버튼 내부에서 `total_scenes`, `total_duration`, `avg_duration`, `completion_rate`, `exist_count`, `missing_scenes` 변수를 참조할 때 `UnboundLocalError` 발생 가능성 제거
  - 수정 전: 버튼 외부 try 블록에서만 변수가 정의됨 → 버튼 클릭 시 해당 변수가 미정의 상태일 수 있음
  - 수정 후: 버튼 선언 위에서 기본값으로 초기화 (`total_scenes=0`, `completion_rate=0.0` 등) 후 try 블록에서 재계산 → 항상 안전하게 참조 가능
- **파트 8 Git Push 변수명 충돌 수정**: `auto_git_push` 반환값을 `success_push`, `msg_push`로 교체하여 내부 `st.success` 변수명과 충돌 방지

### 영향 파트
- **Part 6 (Opal Dispatch)**: 배분 버튼 내 BGM/믹싱 설정값 참조 안정화
- **Part 8 (Dashboard)**: 저장 버튼 내 통계 변수 스코프 안정화

### 수정 파일
- `app_v14.py` (5969줄 → 5985줄)

---

## v14.0 — 2026-05-21 17:41 [메이저 릴리즈]
### 변경 내용
- **파트 6 (나레이션 & 배경음악) 완전 구현**: `render_part6_opal()` 함수 완성
  - 파트 3-4 나레이션 대본(`p34_narration_script`) 또는 이미지 대본(`p34_image_script`)에서 씬 번호 + 나레이션 텍스트 자동 파싱
  - 112개 씬을 8개 계정(1번~8번)에 14씬씩 균등 자동 배분하는 Opal 배분 테이블 생성
  - Gemma AI 배분 지시 + 정규식 검증(`re.compile`) + 배분 실패 줄 리스트업 기능 구현
  - `p6_opal_data` (dict list) 직렬화 세션 저장 및 `st.dataframe` 시각화
  - CSV 다운로드(utf-8-sig, Excel 한글 깨짐 방지) 기능 탑재
  - 옵시디언 자동 백업 + Git Push 파이프라인 연동
- **파트 7 (숏폼 생성 CapCut Bridge) 완전 구현**: `render_part7_capcut()` 함수 완성
  - `p6_opal_data`에서 씬 정보 복원 → 자막 지속시간 자동 연산 (글자당 0.25초, 최소 4.0초)
  - 이미지파일명(`scene_001.png`), 비디오파일명(`video_001.mp4`), 나레이션파일명(`narration_001.mp3`) 자동 생성
  - CapCut Bridge DataFrame(`p7_capcut_data_v2`) 구축 및 `st.dataframe` 시각화
  - CSV 다운로드(utf-8-sig) 기능 탑재
  - 옵시디언 자동 백업 + Git Push 파이프라인 연동
- **파트 8 (캡컷 최종 조립 Dashboard) 완전 구현**: `render_part8_dashboard()` 함수 완성
  - `06_Video_Clips` 로컬 폴더 실시간 스캔 → `video_001.mp4`~`video_112.mp4` 파일 매칭률(%) 계산
  - 매칭 완료/누락 비디오 파일 리스트업 및 `st.progress` 시각화
  - 총 씬 수 / 총 예상 재생시간 / 총 자막 글자 수 등 통계 카드 제공
  - 옵시디언 자동 백업 + Git Push 파이프라인 연동
- **신규 세션 스테이트 키 11개 추가**:
  - `p6_opal_data`, `p6_opal_raw_text`, `p6_opal_saved`, `p6_opal_obsidian_saved`
  - `p7_capcut_data_v2`, `p7_capcut_saved`, `p7_capcut_obsidian_saved`
  - `p8_video_match_result`, `p8_dashboard_saved`, `unlock_part6`, `unlock_part7`, `unlock_part8`
- **DataFrame 직렬화 우회**: JSON 직렬화 불가 pandas DataFrame을 `to_dict("records")` 리스트로 변환하여 `workspace_state.json` 영속화 안전 보장
- **등장인물 규칙 준수**: 모든 나레이션 템플릿 및 프롬프트에 `@Protagonist` 표기 강제

### 영향 파트
- **Part 6 (Opal Dispatch)**: 나레이션 파싱 + 8계정 배분 + CSV 다운로드 완전 구현
- **Part 7 (Shorts Creator / CapCut Bridge)**: 자막 지속시간 연산 + CapCut 데이터 조립 완전 구현
- **Part 8 (Dashboard)**: 비디오 파일 매칭률 체크 + 통계 카드 완전 구현
- **App Core**: 세션 스테이트 초기화 및 영속화(`workspace_state.json`) 강화

### 수정 파일
- `app_v14.py` (v13.42 기반 메이저 버전 업, 5937줄)
- `RUN_APP.bat` (실행 타겟 → `app_v14.py`)
- `RUN_DEBUG.bat` (실행 타겟 → `app_v14.py`)
- `00_History\CHANGELOG.md`

---


## v13.41 — 2026-05-21 [마이너/기능완성]
### 변경 내용
- **파트 3 대본 화면 중복 Expander 제거**:
  - `render_part34()` 내부의 중복 렌더링되던 `st.expander` 블록을 완벽히 제거하여 화면 표시 오류 해결 및 상단 공통 패널과 디자인 정합성 유지
- **파트 6~8 화면 파트 명칭 및 고유 마스터 프롬프트 동적 연동**:
  - `p6_master_prompt`, `p7_master_prompt`, `p8_master_prompt` 전용 프롬프트 키를 신설하고 동기화하여 파트별 고유의 마스터 프롬프트가 동적으로 연동되도록 기능 구현
  - `init_session_state()`의 기본값과 `save_workspace_state()`의 `keys_to_save` 목록에 추가하여 영구 백업 연동 완료
- **상단 클릭형 RAG / GitHub 통합 카드 연동**:
  - 옵시디언 RAG 상태 카드와 GitHub 연동 카드를 Streamlit 버튼 형태의 클릭형 카드로 변경하여, 클릭 시 즉시 팝업(`st.dialog`)이 뜨도록 UI 개선
- **엔트리포인트 동기화**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 실행 타겟 및 버전을 `app_v13_41.py`로 갱신 완료

### 영향 파트
- **Part 3-4 (Architect & Writer)**: 대본 화면 중복 패널 제거 및 UI 정리
- **Part 6 (Opal Dispatch)**: 파트 명칭 및 고유 마스터 프롬프트 연동
- **Part 7 (Shorts Creator)**: 파트 명칭 및 고유 마스터 프롬프트 연동
- **Part 8 (Dashboard)**: 파트 명칭 및 고유 마스터 프롬프트 연동
- **App Core**: 상단 패널 클릭형 카드 도입 및 구동 스크립트 갱신

### 수정 파일
- `app_v13_41.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

## v13.40 — 2026-05-21 [마이너/기능보완]
### 변경 내용
- **상단 RAG 패널 동적 연동 정렬**:
  - 사이드바 라디오 버튼으로 파트 전환 시 상단 RAG 패널의 마스터 프롬프트와 파트 명칭이 실시간으로 동적 연동되도록 정렬
- **세션 상태 및 라디오 파트 번호 정합성 확보**:
  - 각 파트별 Sage Pop-up 클릭 시에 지정되는 sidebar_part 세션 상태를 라디오 파트 번호와 정확히 일치시켜 일관된 UI 연동 보장

### 영향 파트
- **App Core**: 상단 RAG 패널 및 세션 상태 동기화

### 수정 파일
- `app_v13_40.py`

## v13.38 — 2026-05-21 [마이너/기능보완]
### 변경 내용
- **Part 4 (Image Consistency) 및 Part 5 (Video Production) 최상단 상태바 및 구분선 일관 적용**:
  - `render_part5_image()`와 `render_part6_video()` 최상단에 `render_top_panel()` 및 `st.divider()`를 추가하여 로컬 DB, 옵시디언, 깃허브 연동 상태 표시의 일관성 확보
- **Gemma 공통 운영 헌법(COMMON_GEMMA_PROTOCOL) 구문 오류 수정**:
  - `app_v13_37.py`에서 잘못 닫혀 있던 트리플 따옴표(`"""`)를 제거하여, 로컬 실행 시 발생하던 파이썬 구문 에러(SyntaxError)를 해결
- **엔트리포인트 동기화**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 실행 대상을 신규 릴리즈 버전인 `app_v13_38.py`로 변경 완료

### 영향 파트
- **Part 4 (Image Consistency)**: 상단 상태바 및 구분선 적용
- **Part 5 (Video Production)**: 상단 상태바 및 구분선 적용
- **App Core**: 공통 젬마 프로토콜 구문 오류 해결 및 기동 스크립트 갱신

### 수정 파일
- `app_v13_38.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

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
