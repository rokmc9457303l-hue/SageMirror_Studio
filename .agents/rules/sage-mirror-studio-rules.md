---
trigger: always_on
---

# V17 최상단 절대 검증 원칙

앞으로 V17의 모든 작업은 “보이는 것”이 아니라 “실제로 작동하는 것”을 기준으로 완료 판정한다

코드 작성 완료, 화면 표시, 버튼 생성, UI 배치만으로는 완료가 아니다.

모든 기능과 Part 1~8 작업은 반드시 아래 검증을 통과해야 한다.

1. 기준 작업본과 새 작업본 확인
2. 지정된 최신 폴더에서만 수정
3. `py_compile` 통과
4. Streamlit 공식 주소 `http://localhost:8518`# Sage Mirror Studio / 현자의 거울 V17 전체 작업 기준서

## 0. 현재 최우선 지시

이 문서는 Antigravity가 V17 앱의 전체 목적, 구조, 작업 순서, 금지사항, 연결 방식을 정확히 이해하고 작업하기 위한 기준서다.

앞으로 모든 작업은 이 문서를 우선 기준으로 삼는다.

현재 작업 기준은 다음과 같다.

* 공식 프로젝트 루트: `C:\SageMirror_Production`
* 현재 V17 기준 흐름: `V17_Working_UniversalObsidian`
* 공식 실행 주소: `http://localhost:8518`
* V18 접근 금지
* GitHub Push 금지
* API Key / Token / PAT 노출 금지
* 기존 안정본 직접 수정 금지
* 새 작업은 반드시 새 번호 작업본을 만들어 진행
* `Remove-Item` 사용 금지
* 기존 작업본 덮어쓰기 금지
* 작업 완료 후 반드시 백업 버전업 저장
* 앱 파일도 `00_History`에 버전업 저장

현재 화면이나 IDE에서 `V17_Working_RightGemma_001`, `app_v17_2_3.py` 같은 구버전 폴더/파일을 보고 있다면 즉시 중단하고, 현재 기준 작업본이 맞는지 확인한다.

---

# 1. 프로젝트 정체성

이 앱은 단순한 버튼 모음이 아니다.

이 앱은 유튜브 롱폼/숏폼 콘텐츠 제작을 자동화하는 AI 제작 운영체제다.

기본 채널은 다음 정체성을 가진다.

* 채널명: 현자의 거울
* 핵심 상징: 거울, 내면 응시, 감정 해부
* 타깃: 한국 40~70대
* 시청자 호칭: `@Protagonist`
* 콘텐츠 융합:

  * 성경
  * 철학
  * 심리학
  * 에세이
  * 다크 심리학
* 주요 철학/심리 축:

  * 쇼펜하우어
  * 빅터 프랭클
  * 융
  * 몽테뉴
  * 성경 구약/신약/시편/잠언
* 영상 분위기:

  * 낮고 묵직함
  * 감정 해부형
  * 강의식 금지
  * 쉬운 위로 금지
  * “힘내세요”식 표현 금지
  * 시청자의 내면을 직면하게 하는 문체
* 비주얼 기준:

  * 17세기 서재
  * 촛불
  * 렘브란트 명암
  * 바로크 거울
  * 거울 속 감정 실루엣
  * 늙은 현자 내레이터

단, 이 정체성은 Core 코드에 하드코딩하면 안 된다.

현자의 거울 정체성은 다음 위치에서 관리해야 한다.

* Profile 설정
* Prompt MD 파일
* Channel Identity MD 파일
* 사용자가 수정 가능한 설정값

Core는 범용 시스템이어야 한다.

---

# 2. 절대 설계 원칙

## 2.1 Core에 넣을 것

Core에는 시스템 구조만 둔다.

Core에 들어갈 수 있는 것:

* Agent Registry
* School Registry
* Packet Router
* Command Router
* Task Queue
* 상태 관리
* 자동 저장
* 실패 재시도
* Obsidian 저장 연결
* RAG 요청 연결
* Provider 선택 구조
* 보안 저장 구조
* 설정값 로딩
* UI 상태 관리

## 2.2 Core에 넣으면 안 되는 것

Core에 특정 채널의 내용이나 세계관을 하드코딩하지 않는다.

Core에 넣으면 안 되는 것:

* “현자의 거울” 고정 문구
* 특정 채널명
* 특정 세계관
* 특정 타깃
* 특정 문체
* 특정 성경/철학 조합
* 특정 이미지 스타일
* 특정 프롬프트 본문
* 특정 유튜브 채널명
* 특정 GitHub 저장소명
* 특정 Obsidian 경로
* API Key
* Token
* PAT

---

# 3. 앱 전체 구조

앱은 다음 구조로 동작한다.

```text
사용자
↓
좌측바 조종석
↓
설정창 / Profile / Channel Identity
↓
Gemma 공장장
↓
Agent School / Agent Campus
↓
Part별 Agent
↓
Prompt MD
↓
작업 결과
↓
Packet
↓
검수 / 보강
↓
Obsidian Raw / Wiki / Schema / Logs 저장
↓
다음 Part 전달
↓
최종 영상 제작
```

---

# 4. 좌측바 역할

좌측바는 앱의 조종석이다.

좌측바는 복잡하면 안 된다.
기본 화면은 작고 명확해야 한다.

좌측바 기본 표시 항목:

* 현재 프로젝트
* 채널명
* 선택 Profile
* 현재 Part
* Agent School 상태
* 등록 Agent 수
* 현재 Part Agent 수
* Packet Queue 상태
* 최근 명령
* Part 1~8 이동
* 설정 열기
* 고급 정보 보기

좌측바 기본 화면에서 숨겨야 할 항목:

* Episode Control Center
* EP001 고정 표기
* 현재 Episode 전체 저장
* 새 Episode 시작
* 고정 채널명
* 고정 앱명
* 고정 Obsidian 경로
* 고정 GitHub 저장소명
* API Key 입력창
* Token 입력창
* 긴 디버그 로그
* 백업 버튼 상시 노출

고급 정보 보기 안에만 넣을 수 있는 항목:

* Obsidian 경로
* GitHub Repo
* 내부 상태
* 백업 상태
* 디버그 정보
* 로그 확인
* 수동 저장

---

# 5. 우측 대화창 역할

우측 대화창은 사용자가 Gemma 공장장에게 명령을 내리는 곳이다.

우측 대화창은 직접 중앙 결과를 덮어쓰면 안 된다.

우측 대화창의 역할:

* 사용자 명령 수신
* “시작해” 명령 감지
* Gemma 공장장 호출
* Agent School에 작업 요청
* Agent 실행 요청 생성
* 검수 요청
* 보강 요청
* Obsidian 저장 요청
* 다음 Part Packet 준비
* 사용자 승인 기록

우측 대화창이 하면 안 되는 것:

* 중앙 Part 결과 직접 덮어쓰기
* Obsidian 직접 무한 검색
* RAG 직접 무한 로딩
* API Key 노출
* 사용자 승인 없이 다음 Part 반영
* 사용자 승인 없이 GitHub Push

---

# 6. Agent School / 학교 구조

우측 대화창에서 “시작해”를 받아도, 내부에 학교가 없으면 연결할 수 없다.

따라서 Agent School이 먼저 있어야 한다.

Agent School은 다음 역할을 한다.

* Part 1~8을 학과처럼 등록
* 각 Part의 Agent 등록
* Agent별 역할 관리
* Agent별 Prompt MD 경로 관리
* Agent별 입력 Packet 타입 관리
* Agent별 출력 Packet 타입 관리
* Agent 실행 상태 관리
* Packet Queue 관리
* 다음 Agent 또는 다음 Part로 전달 규칙 관리
* Gemma 공장장이 호출할 순서 관리

현재 `_023`에서 1차로 생성된 구조:

* `core/agent_school.py`
* 8개 학과
* 38명 Agent
* Packet Queue 기초
* Command Router 기초
* 좌측바 Agent School 상태 연결

이 구조를 앞으로 확장한다.

---

# 7. Gemma의 역할

Gemma는 단순 생성 모델이 아니다.

Gemma는 공장장이다.

Gemma의 역할:

* 사용자 명령 해석
* 현재 Part 판단
* 필요한 Agent 순서 결정
* Prompt MD 읽기
* Agent 작업 요청 생성
* 결과 Packet 검토
* 부족한 부분 판정
* 보강 요청
* Obsidian 저장 요청
* 다음 Part 전달 준비
* 사용자 승인 요청

Gemma가 직접 모든 작업을 한 번에 처리하면 안 된다.

Gemma는 각 Agent에게 작업을 나누고, 결과를 모아 다음 단계로 넘긴다.

---

# 8. Prompt MD 원칙

이 앱의 품질은 Prompt MD의 품질로 결정된다.

프롬프트는 코드에 하드코딩하지 않는다.

모든 주요 작업 프롬프트는 `.md` 파일로 저장한다.

Prompt MD는 앱에서 열고 수정할 수 있어야 한다.

사용자가 결과물이 부족하다고 느끼면:

```text
해당 Part Prompt MD 열기
↓
프롬프트 보강
↓
저장
↓
다시 생성
↓
새 프롬프트 기준으로 결과 재생성
```

Prompt MD에는 다음 항목이 반드시 들어가야 한다.

* Agent 역할
* 입력값
* 작업 순서
* 분석 기준
* 생성 기준
* 금지사항
* 출력 형식
* 품질 기준
* 검수 기준
* 보강 기준
* 다음 Part 전달 Packet 규격

---

# 9. Prompt MD 기본 폴더 구조

앞으로 프롬프트는 다음 구조로 관리한다.

```text
prompts/
├─ gemma/
│  ├─ gemma_factory_master_protocol.md
│  ├─ gemma_agent_orchestration.md
│  └─ gemma_quality_review_protocol.md
│
├─ profiles/
│  └─ default_channel_identity.md
│
├─ part1/
│  ├─ 01_떡상_채널_발굴기.md
│  ├─ 02_유튜브_채널_조사.md
│  ├─ 03_성공영상_벤치마킹.md
│  ├─ 04_댓글_감정_분석.md
│  ├─ 05_주제_제목_후보_생성.md
│  ├─ 06_part1_packet_생성.md
│  └─ 07_part1_품질_검수.md
│
├─ part2/
│  ├─ 01_총괄기획_생성.md
│  ├─ 02_감정선_구조화.md
│  ├─ 03_자료_정합성_검수.md
│  ├─ 04_part2_packet_생성.md
│  └─ 05_part2_품질_검수.md
│
├─ part3/
│  ├─ 01_롱폼_대본_작성.md
│  ├─ 02_오프닝_훅_생성.md
│  ├─ 03_서사_깊이_강화.md
│  ├─ 04_문체_검수.md
│  └─ 05_part3_packet_생성.md
│
├─ part4/
│  ├─ 01_이미지_프롬프트_생성.md
│  ├─ 02_레퍼런스_에셋_선정.md
│  ├─ 03_씬_비주얼_구성.md
│  ├─ 04_이미지_품질_검수.md
│  └─ 05_part4_packet_생성.md
│
├─ part5/
│  ├─ 01_Opal_JSON_생성.md
│  ├─ 02_씬_타이밍_계산.md
│  ├─ 03_영상_시퀀스_검수.md
│  └─ 04_part5_packet_생성.md
│
├─ part6/
│  ├─ 01_TTS_SSML_생성.md
│  ├─ 02_BGM_프롬프트_생성.md
│  ├─ 03_오디오_무드_검수.md
│  └─ 04_part6_packet_생성.md
│
├─ part7/
│  ├─ 01_숏폼_훅_생성.md
│  ├─ 02_숏폼_대본_생성.md
│  ├─ 03_숏폼_자막_구성.md
│  └─ 04_part7_packet_생성.md
│
└─ part8/
   ├─ 01_최종_품질_검수.md
   ├─ 02_CapCut_배치_설계.md
   ├─ 03_업로드_체크리스트.md
   └─ 04_최종_packet_생성.md
```

---

# 10. Part 1 첫 시작 구조

Part 1은 “떡상 채널 발굴기”로 시작한다.

사용자가 다음 명령을 입력하면 Part 1 시작 준비가 되어야 한다.

* 시작해
* 시작
* Part 1 시작
* 떡상 채널 발굴 시작
* 유튜브 조사 시작
* 채널 조사 시작

동작 흐름:

```text
사용자: 시작해
↓
Command Router 명령 인식
↓
Gemma 공장장 호출 준비
↓
Part 1 Agent School 호출
↓
떡상 채널 발굴 Agent 준비
↓
Prompt MD 읽기
↓
채널명 / Profile / Channel Identity 반영
↓
유튜브 채널 조사
↓
성공 영상 벤치마킹
↓
댓글 감정 분석
↓
주제 / 제목 후보 생성
↓
Part 1 Packet 생성
↓
검수
↓
Obsidian 저장
↓
Part 2로 전달 준비
```

---

# 11. Part 1 Agent 구성

Part 1은 다음 Agent가 담당한다.

## 11.1 rising_channel_discovery_agent

역할:

* 떡상 채널 후보 발굴
* 채널 성장 가능성 분석
* 경쟁 채널 후보 추출

## 11.2 youtube_channel_research_agent

역할:

* 유튜브 채널 구조 분석
* 인기 영상 구조 분석
* 반복 주제 추출
* 제목/썸네일 패턴 파악

## 11.3 benchmark_video_analysis_agent

역할:

* 성공 영상 벤치마킹
* 제목 구조
* 썸네일 구조
* 초반 훅
* 감정 흐름
* 댓글 반응
* 조회수 대비 반응성 분석

## 11.4 comment_emotion_analysis_agent

역할:

* 댓글 감정 분석
* 시청자의 상처/분노/외로움/후회/공감 추출
* 주제화 가능한 감정 패턴 추출

## 11.5 topic_title_candidate_agent

역할:

* 주제 후보 생성
* 제목 후보 생성
* 썸네일 방향 생성
* 채널 정체성과의 일치도 평가

## 11.6 part1_packet_builder_agent

역할:

* Part 2로 넘길 Packet 구성
* 벤치마킹 결과 정리
* 주제 후보 정리
* 제목 후보 정리
* 댓글 인사이트 정리

## 11.7 part1_quality_review_agent

역할:

* Part 1 결과 검수
* 채널 정체성 일치 여부 판정
* 자료 부족 여부 판정
* 보강 필요 항목 표시

---

# 12. Packet 원칙

각 Agent는 결과를 그냥 화면에 쓰는 것이 아니라 Packet으로 넘긴다.

Packet은 다음 Part가 바로 읽을 수 있는 구조화된 결과물이다.

Packet 기본 필드:

```json
{
  "packet_id": "",
  "source_part": "",
  "target_part": "",
  "source_agent": "",
  "target_agent": "",
  "project_name": "",
  "channel_name": "",
  "profile_name": "",
  "status": "",
  "created_at": "",
  "prompt_files": [],
  "input_summary": "",
  "output_summary": "",
  "payload": {},
  "quality_review": {},
  "obsidian_paths": {
    "raw": "",
    "wiki": "",
    "schema": "",
    "logs": ""
  }
}
```

Packet 상태:

* pending
* running
* needs_review
* needs_supplement
* approved
* failed
* delivered

---

# 13. Obsidian 저장 구조

Obsidian은 단순 저장소가 아니다.

Obsidian은 앱의 기억 시스템이다.

기본 경로:

```text
C:\SageMirror_Production\00_Obsidian
```

저장 계층:

```text
00_Raw
01_Wiki
02_Schema
03_Logs
```

저장 원칙:

* Raw: 원본 입력/대화/자료
* Wiki: 사람이 읽는 요약/지식 노트
* Schema: JSON 구조 데이터
* Logs: 작업 로그/중복/오류/실행 기록

API Key / Token / PAT는 절대 Obsidian에 저장하지 않는다.

---

# 14. RAG 연결 구조

RAG는 앱 내부에서 자료 보강을 위한 검색/기억 계층이다.

RAG는 우측 대화창에서 무한 검색하면 안 된다.

정상 흐름:

```text
Agent 결과 부족
↓
Gemma가 자료 부족 판단
↓
RAG 요청 Packet 생성
↓
RAG Queue 등록
↓
자료 보강
↓
Obsidian 저장
↓
보강 결과 Packet 생성
↓
해당 Part 또는 Agent로 반환
```

RAG 요청 상태:

* queued
* searching
* saved
* ready_for_review
* failed
* retrying

---

# 15. 설정창 역할

설정창은 범용 Provider 설정 센터다.

좌측바의 작은 Expander가 아니라, 가능하면 큰 설정창으로 구성한다.

설정창 섹션:

1. 기본 프로젝트
2. 채널 / Profile
3. 저장소 경로
4. AI Provider
5. 리서치 Provider
6. 제작 도구
7. 테마 / 화면 스타일
8. 보안 / API Key
9. Agent 설정
10. Prompt MD 편집

설정창에서 수정 가능해야 할 것:

* 프로젝트명
* 채널명
* Profile명
* Channel Identity MD
* Obsidian Vault
* GitHub Repo
* Google Drive / Docs
* NotebookLM 폴더
* CapCut Drafts
* CapCut Materials
* Ollama 모델
* Gemini 모델
* OpenAI 모델
* Claude 모델
* Tavily 사용 여부
* YouTube API 사용 여부
* TTS 도구
* BGM 도구
* 이미지 생성 도구
* 영상 생성 도구
* 테마 색상
* 배경 이미지
* Agent ON/OFF
* Agent별 Provider
* Agent별 Prompt MD

---

# 16. 채널명 전역 적용

채널명은 사용자가 직접 수정할 수 있어야 한다.

채널명은 다음에 자동 반영되어야 한다.

* 좌측바
* 중앙 상단
* Part 1~8
* Prompt 변수
* Packet
* Obsidian Raw 메타데이터
* Obsidian Wiki 메타데이터
* Obsidian Schema
* 결과물 파일명
* 최종 출력물 메타데이터

채널명 저장 기준:

```python
app_settings["channel_name"]
```

fallback은 가능하지만, 코드 곳곳에 “현자의 거울”을 반복 삽입하면 안 된다.

---

# 17. 테마 / 바탕화면 변경 구조

사용자는 앱의 바탕화면과 색상을 바꿀 수 있어야 한다.

설정값:

* theme_mode
* background_color
* sidebar_color
* accent_color
* text_color
* background_image_path

기본값:

* background_color: `#FFFFFF`
* sidebar_color: `#F7F7F7`
* accent_color: `#B8860B`
* text_color: `#111111`

색상은 코드에 하드코딩하지 않고 설정값에서 읽어 CSS 변수로 주입한다.

---

# 18. API Key 보안 원칙

API Key, Token, PAT는 절대 평문으로 공개 파일에 저장하지 않는다.

저장 금지 위치:

* workspace_state.json
* Obsidian
* History
* GitHub
* Log
* Terminal 출력
* 화면 표시

보안 대상:

* tavily_api_key
* youtube_api_key
* gemini_api_key
* github_token
* openai_api_key
* anthropic_api_key
* google_drive_token
* any secret / token / password

허용 구조:

* `.env`
* `.streamlit/secrets.toml`
* `local_secrets.json`

단, 이 파일들은 반드시 `.gitignore` 대상이어야 한다.

화면에는 항상 마스킹한다.

---

# 19. 작업 순서 원칙

모든 작업은 다음 순서를 따른다.

```text
1. 기준 작업본 확인
2. 새 번호 작업본 생성
3. 기존 작업본 직접 수정 금지
4. 작은 범위만 수정
5. py_compile 검사
6. Streamlit 8518 실행
7. 브라우저 화면 확인
8. 사용자 확인
9. 백업 버전업 저장
10. app 파일 History 저장
11. CHANGELOG 기록
12. 다음 작업으로 이동
```

---

# 20. 현재 완료된 주요 단계

현재까지 완료된 것으로 보고된 단계:

## _021

* 중앙 상단 UI 정리
* 우측 패널 정리
* 우측 대화창 높이 조정
* 공식 포트 8518 확인

## _022

* _021 기준 다음 작업본 생성
* 좌측바 + 설정창 범용화 사전 진단
* 오늘 종료 백업 완료

## _023

* Agent School 기초 생성
* 8개 학과 등록
* 38명 Agent 등록
* Prompt MD 폴더 구조 생성
* 좌측바 Agent School 상태 연결
* 좌측바 기본 노출 정리
* API Key 입력창 기본 화면에서 제거
* py_compile 통과
* Streamlit 8518 실행 확인
* 백업 저장
* app 파일 History 저장

---

# 21. 현재 발견된 문제

## 21.1 설정 열기 버튼 문제

좌측바에서 “설정 열기” 버튼을 눌러도 설정창이 열리지 않는 문제가 있다.

가능한 원인:

* 버튼이 `st.session_state.show_settings_modal = True`만 설정하고 실제 설정창 렌더링 함수가 없음
* `render_settings_modal()` 또는 `st.dialog` 연결이 없음
* 현재 Antigravity가 다른 구버전 폴더를 보고 있음
* 현재 실행 중인 앱이 `_024`가 아니라 이전 폴더일 가능성

이 문제는 다음 작업에서 반드시 수정한다.

## 21.2 현재 IDE 폴더 불일치 위험

화면상 Antigravity IDE가 `V17_Working_RightGemma_001` 같은 구버전 폴더를 보고 있다면 즉시 중단한다.

현재 작업은 반드시 다음 흐름이어야 한다.

```text
V17_Working_UniversalObsidian_023
↓
V17_Working_UniversalObsidian_024
```

잘못된 폴더에서 작업하지 않는다.

---

# 22. 다음 작업 우선순위

다음 작업은 `_023`을 기준으로 `_024`를 생성하여 진행한다.

다음 작업명:

```text
V17 _024 설정창 범용화 + API Key 보안 분리 + 설정 열기 버튼 실제 연결
```

다음 작업 목표:

1. `_024` 생성
2. 설정 열기 버튼 실제 작동
3. 설정창을 큰 설정 UI로 정리
4. 프로젝트명 수정
5. 채널명 수정
6. Profile명 수정
7. 채널명 좌측바/중앙 상단 반영
8. 테마 색상 변경
9. 바탕화면 변경 준비
10. API Key workspace_state.json 저장 차단
11. local_secrets 구조 준비
12. py_compile
13. Streamlit 8518 실행
14. 브라우저 확인
15. _024 백업
16. app 파일 History 저장

---

# 23. 완료 보고서 필수 항목

모든 작업 완료 보고서에는 다음을 포함한다.

* 기준 작업본
* 새 작업본
* 직접 수정 금지 준수 여부
* 새로 만든 파일
* 수정한 파일
* 삭제한 파일 여부
* py_compile 결과
* Streamlit 8518 실행 결과
* 브라우저 확인 결과
* 백업 경로
* app 파일 History 저장 경로
* CHANGELOG 기록 여부
* Git Push 여부
* API Key 노출 여부
* 다음 작업 제안

---

# 24. 마지막 원칙

이 앱은 특정 버튼 앱이 아니다.

이 앱은 다음 구조의 범용 AI 제작 공장이다.

```text
Profile이 정체성을 정한다.
Prompt MD가 작업 기준을 정한다.
Gemma가 공장장 역할을 한다.
Agent School이 작업자를 관리한다.
Part가 공정을 나눈다.
Packet이 결과물을 이동시킨다.
Obsidian이 기억을 축적한다.
RAG가 부족한 자료를 보강한다.
좌측바는 조종석이다.
우측 대화창은 명령실이다.
설정창은 운영센터다.
```

이 원칙을 어기지 말고, 작은 단위로 안정적으로 작업한다.