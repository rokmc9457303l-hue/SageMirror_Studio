## v16.1.18 - 2026-05-26 20:15
### 변경 내용
- **중복 위젯 키 대응 및 로컬 상태 동기화 강화 (DuplicateWidgetID Response & Session State Sync)**:
  - **위젯 식별자(Key) 고유화**: `render_part2()` 내부의 썸네일 기획안 텍스트 영역(`p2_thumb_area_widget`) 및 젬마 프로토콜 텍스트 영역(`p2_gemma_protocol_display`)의 key를 에피소드 식별자가 동적으로 포함된 `f"thumb_area_{st.session_state.get('episode_name', 'EP')}"` 및 `f"gemma_proto_{st.session_state.get('episode_name', 'EP')}"`로 각각 재설계하여 에피소드 전환 시 발생하는 Streamlit의 `DuplicateWidgetID` 중복 위젯 키 오류를 근본적으로 차단했습니다.
  - **세션 상태 동기화 재설계**: `init_session_state()` 함수 내부에서 파일 로딩 전 강제 정화(`sanitize_workspace_prompt_values_once()`)를 수행하고, 로드된 설정 데이터를 세션 상태에 덮어쓸 수 있도록 로직을 수정하여 상태 데이터가 휘발되거나 유실되는 문제를 해결했습니다.
  - **배포 스크립트 3종 갱신**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 타겟을 `app_v16_1_18.py`로 갱신 완료했습니다.
### 영향 파트
- Part 2 Alchemist 기획 단계(Step 1) UI 위젯 상태 엔진, 에피소드 전환 상태 동기화 파이프라인
### 수정 파일
- `app_v16_1_18.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.15 - 2026-05-26 18:40
### 변경 내용
- **Part 2 Step 1 데이터 저장 버그 수정 (Thumbnail Save Integration)**:
  - **썸네일 기획안 직접 수정 저장 연동**: 썸네일 기획안 `text_area` 위젯을 고유 위젯 key `p2_thumb_area_widget`으로 지정하고, 사용자가 기획안 텍스트를 직접 편집하여 변경했을 시에만 `st.session_state.p2_thumbnail_plan`을 갱신하고 `save_workspace_state()`를 유기적으로 자동 호출하도록 수정하여 저장 유실 문제를 최종 보완하였습니다.
  - **배포 스크립트 3종 갱신**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 타겟을 `app_v16_1_15.py`로 갱신 완료했습니다.
### 영향 파트
- Part 2 Alchemist 기획 단계(Step 1) 썸네일 기획안 사용자 편집 레이어 및 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_15.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.11 - 2026-05-26 15:31
### 변경 내용
- **Part 2 Step 1 긴급 복구 및 롤백 (Emergency Recovery from v16.1.9 Baseline)**:
  - **안정 버전 복구**: v16.1.10에서 추가된 Part 2 UI 직접 편집 기능, 위젯 키 변경, `on_change` 저장 루프 등을 전면 폐기하고, 검증 완료된 v16.1.9 안정본을 기준으로 `app_v16_1_11.py` 신규 버전을 생성했습니다.
  - **UI 구조 원복**: 젬마 프로토콜 표시창의 `disabled=True` 속성 및 원래의 썸네일 텍스트 영역 구조를 온전히 복구하여 UI 오작동 가능성을 제거했습니다.
  - **배포 스크립트 3종 갱신**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 타겟을 `app_v16_1_11.py`로 갱신 완료했습니다.
### 영향 파트
- Part 2 Alchemist 기획 단계(Step 1) UI 인터페이스 및 사용자 편집 레이어, 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_11.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.10 - 2026-05-26 15:11
### 변경 내용
- **Part 2 Step 1 UI 상태 관리 패치 (UI State Management Patch)**:
  - **프롬프트 덮어쓰기 조건 수정**: `render_part2()` 최상단에서 프롬프트를 무조건 덮어쓰던 코드를 `if not st.session_state.get(_k):` 조건문으로 감싸, 사용자가 저장한 커스텀 프롬프트가 유지되도록 복구했습니다.
  - **젬마 프로토콜 직접 편집 저장 연동**: 프로토콜 `text_area` 위젯을 editable하게 변경하고 고유 위젯 key `p2_gemma_protocol_widget`을 지정하여, 텍스트 직접 편집 시 세션에 양방향 동기화 및 `save_workspace_state()` 자동 호출이 유기적으로 일어나도록 고도화했습니다.
  - **썸네일 기획 편집 결과 저장 연동**: 썸네일 기획 `text_area` 위젯을 고유 위젯 key `p2_thumb_area_widget`으로 갱신하여, 직접 편집 결과가 `p2_thumbnail_plan` 세션 및 워크스페이스 상태에 안전하게 자동 저장되도록 복구했습니다.
  - **배포 스크립트 3종 갱신**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 타겟을 `app_v16_1_10.py`로 갱신 완료했습니다.
### 영향 파트
- Part 2 Alchemist 기획 단계(Step 1) UI 인터페이스 및 사용자 편집 저장 연동 레이어, 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_10.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.9 - 2026-05-26 14:53
### 변경 내용
- **Part 2 Step 1 영속성 복구 패치 (Persistent Memory Recovery Patch)**:
  - **영속성 누락 키 추가**: `memory_state_manager.py` 내 `keys_to_save` 리스트에 `"p2_gemma_protocol"`, `"p2_thumbnail_sets"`, `"p2_selected_thumbnail"` 키들이 누락되어 있었던 현상을 발견하고 이를 추가했습니다. 이를 통해 젬마 프로토콜, 썸네일 카드, 선택값 등이 `workspace_state.json` 파일에 정상 저장되도록 복구했습니다.
  - **세션 초기화 기본값 세팅 보완**: `app_v16_1_9.py`를 신규 생성하여 버전 명을 `v16.1.9`로 업데이트하고, `init_session_state()`의 `defaults` 사전에 누락 키들의 기본값을 선언하여 초기화 시 덮어쓰기를 방지하고 로드된 데이터가 안전하게 유지되도록 조치했습니다.
  - **배포 스크립트 3종 갱신**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 타겟을 `app_v16_1_9.py`로 갱신 완료했습니다.
### 영향 파트
- Part 2 Alchemist 기획 단계(Step 1), 영속성 관리 및 설정 저장 장치, 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_9.py`
- `memory_state_manager.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.8 - 2026-05-26 12:26
### 변경 내용
- **Gemma Assistant 안정화 및 견고화 (Stabilization Phase)**:
  - **Recent Activity 디듀플리케이션 및 품질 개선**: `rag_memory_utils.py` 내의 `update_recent_activity_memory()` 함수에 중복 제거 로직을 구현하여, 동일한 type과 content를 가진 활동이 계속 추가되더라도 최신 정보만 남기도록 개선하였습니다. 또한 `build_recent_activity_memory()`의 마크다운 정리와 최신순 정렬 방식을 최적화했습니다.
  - **도구 레지스트리 메타데이터 보강**: `agent_registry.py` 내의 각 도구 명세에 `"experimental": False`, `"safe_mode": True` 속성을 수록하여 도구의 안전 등급 관리를 시작하였습니다.
  - **검색 RAG 폴백 강화**: `research_router.py` 내 `build_tavily_rag_context_core()`에서 임시 검색 실패 상황(API 차단 또는 에러 키 감지) 시에도 전체 시스템이 먹통이 되지 않고 RAG 규격의 폴백 응답을 안정적으로 반환하도록 보완하였습니다.
  - **에이전트 런타임 차단 및 복구력(Recovery) 강화**: `sage_popups.py` 내 `_detect_tools()`에서 `enabled=False` 상태의 도구를 원천적으로 탐색 대상에서 배제하고, `_execute_tool()` 진입부에서 미등록 혹은 비활성화 도구를 차단하며, `run_agent_loop()` 내부에서 툴 호출부를 `try-except`로 묶어 예외 상황이 발생해도 시스템이 중단되지 않고 RAG에 에러를 반영하여 복구할 수 있도록 개선하였습니다.
  - **배포 스크립트 3종 갱신**: `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 타겟을 `app_v16_1_8.py` 및 포트 `8505`로 갱신 완료했습니다.
### 영향 파트
- 젬마 어시스턴트 자율 에이전트 엔진, RAG 메모리 시스템, 검색 폴백 파이프라인, 도구 권한 필터 및 런타임 에러 처리기
### 수정 파일
- `app_v16_1_8.py`
- `sage_popups.py`
- `agent_registry.py`
- `agent_toolkit.py`
- `rag_memory_utils.py`
- `research_router.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.7 — 2026-05-26 08:53
### 변경 내용
- **Agent Registry System 도입**:
  - Gemma Assistant가 사용할 수 있는 에이전트 도구들의 메타데이터(설명, 별칭, 패턴, 카테고리, 활성화 여부 등)를 통합 관리하는 중앙 레지스트리 모듈 `agent_registry.py`를 신규 설계하여 추가했습니다.
  - `agent_registry.py` 내에 구현한 핵심 함수군: `get_agent_tool_registry()`, `normalize_registry_tool_name()`, `get_enabled_tools()`, `get_tool_metadata()`, `get_tool_description()`, `get_tool_category()`.
  - `agent_registry.py`는 순수 Python 모듈로서 Streamlit UI 및 플랫폼 의존성을 원천 배제했습니다.
  - `agent_toolkit.py`를 수정하여 기존에 하드코딩되어 있던 툴 목록 사전을 걷어내고, `agent_registry`를 import하여 연동 및 정규식 패턴을 동적 빌드하도록 리팩토링했습니다.
  - `sage_popups.py`에서 `agent_toolkit`을 통해 정규화 및 탐색할 때 Registry 사전에 등록되어 비활성화(`enabled=False`) 처리된 도구들은 자동으로 감지 대상에서 배제되도록 정합성을 고도화했습니다.
  - `app_v16_1_7.py`를 신규 생성하여 버전 명을 `v16.1.7`로 갱신하고, 기존 에이전트 구동에 지장이 없도록 안정성을 유지했습니다.
  - 구동 스크립트 3종(`RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs`)의 Streamlit 실행 대상을 `app_v16_1_7.py` 및 `8505` 포트로 갱신하여 릴리즈를 일원화했습니다.
### 영향 파트
- 젬마 어시스턴트 자율 에이전트 엔진, 도구 Registry 탐색 및 정규화 레이어, 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_7.py`
- `sage_popups.py`
- `agent_toolkit.py`
- `agent_registry.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.6 — 2026-05-26 08:38
### 변경 내용
- **Agent Toolkit 모듈 분리**:
  - `sage_popups.py` 및 `app_v16_1_5.py` 내부에 혼재되어 있던 에이전트 도구 실행 전후의 결과 문자열 포맷팅, 도구 이름 정규화, 명령 파싱, 지원 도구 목록 등의 비-UI 헬퍼 로직을 신규 순수 Python 모듈 `agent_toolkit.py`로 격리하여 분리했습니다.
  - `agent_toolkit.py` 내에 분리 및 추가한 함수군: `get_supported_agent_tools()`, `normalize_tool_name()`, `parse_tool_command()`, `format_tool_result()`, `format_check_source_result()`, `format_search_web_result()`, `format_search_youtube_result()`, `format_save_obsidian_result()`, `format_save_reference_result()`, `format_build_packet_result()`.
  - `agent_toolkit.py`는 순수 Python 모듈로서 Streamlit UI 및 세션 상태 접근을 배제하여 플랫폼 독립적으로 설계했습니다.
  - `app_v16_1_6.py`를 신규 생성하여 버전 명을 `v16.1.6`으로 갱신하고, 기존 동작 안정성을 그대로 유지했습니다.
  - `sage_popups.py`에서 `agent_toolkit` 모듈을 연동하여 `_detect_tools`, `_execute_tool`이 도구 이름 정규화 및 포맷터를 사용하도록 리팩토링했습니다.
  - 구동 스크립트 3종(`RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs`)의 Streamlit 실행 대상을 `app_v16_1_6.py` 및 `8505` 포트로 갱신하여 릴리즈를 일원화했습니다.
### 영향 파트
- 젬마 어시스턴트 자율 에이전트 엔진, RAG 웹/옵시디언 리서치 도구 레이어, 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_6.py`
- `sage_popups.py`
- `agent_toolkit.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.5 — 2026-05-26 08:20
### 변경 내용
- **Research Router 모듈 분리**:
  - `app_v16_1_4.py` 및 `sage_popups.py` 내부에 섞여 있던 Tavily 검색, `NEED_RESEARCH` 태그 분석, 검색 결과 마크다운 가공, RAG 컨텍스트 구축 등 비-UI 검색 흐름을 신규 순수 Python 모듈 `research_router.py`로 분리하여 격리했습니다.
  - `research_router.py` 내에 분리한 함수군: `should_trigger_research()`, `run_tavily_research()`, `clean_search_query()`, `format_search_results_markdown()`, `build_tavily_rag_context_core()`, `build_gemini_search_context_core()`, `build_youtube_search_context_core()`, `build_research_markdown_document()`, `format_source_citation()`.
  - `research_router.py`는 순수 Python 모듈로서 Streamlit UI 및 세션 상태 접근을 원천 배제하여 플랫폼 독립적인 코어로 설계했습니다.
  - `app_v16_1_5.py`를 신규 생성하여 분리된 기능들을 import 하여 연결하고, `call_gemma` 핵심 웹 검색 루프 및 어시스턴트 팝업의 실행 흐름을 안정적으로 연동했습니다.
  - 구동 스크립트 3종(`RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs`)의 Streamlit 실행 타겟을 `app_v16_1_5.py` 및 `8505` 포트로 갱신하여 릴리즈를 일원화했습니다.
### 영향 파트
- RAG 웹 검색 엔진, 어시스턴트 백그라운드 리서치 라우터, 파트 1~8 지식 검색 파이프라인
### 수정 파일
- `app_v16_1_5.py`
- `sage_popups.py`
- `research_router.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.4 — 2026-05-26 07:45
### 변경 내용
- **Memory Layer 안정화 및 분리**:
  - `app_v16_1_3.py` 내의 비-UI 메모리 관리 기능(오염 방지 필터 `clean_prompt_contamination`, 워크스페이스 상태 일괄 정화 `sanitize_workspace_prompt_values_once_core`, 워크스페이스 저장 `save_workspace_state_core`, 워크스페이스 설정값 로드 `load_workspace_state_core`, 업로드 파일 텍스트 추출 `extract_text_from_uploaded_file`, 텍스트 마크다운 구조화 `convert_text_to_markdown_structure`, 공용 태그 빌더 `build_all_parts_common_tags_preview`, References 저장 `save_reference_markdown_file`, References 파싱 `parse_markdown_reference`)을 순수 Python 모듈인 `memory_state_manager.py`로 격리/분리했습니다.
  - `memory_state_manager.py` 모듈 내에서 Streamlit 임포트 및 세션 상태 접근을 최소화/배제하여 UI 및 플랫폼 의존성 없는 독립 코어 구조를 보장했습니다.
  - `app_v16_1_4.py`를 신규 생성하여 분리된 메모리 코어 기능들을 `from memory_state_manager import ...`로 import하여 연결하고, 기존 동작(UI 토스트 알림, 에러 메시지 처리, 세션 스테이트 갱신 및 Recent Activity Sync)에 문제가 없도록 안전한 래퍼 함수 구조를 설계했습니다.
  - 구동 스크립트 3종(`RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs`)의 Streamlit 실행 대상을 `app_v16_1_4.py`로 갱신하여 릴리즈를 일원화했습니다.
### 영향 파트
- 메모리 관리 레이어(RAG, References, Workspace, Session) 독립화, 전체 앱의 상태 보존 및 로드 시스템, 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_4.py`
- `memory_state_manager.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.3 — 2026-05-26 07:30
### 변경 내용
- **RAG Tag System 모듈 분리**:
  - `app_v16_1_2.py`에 혼재되어 있던 RAG 태그, 카테고리, 폴더 맵 및 RAG 자동 분류 핵심 로직 함수들(`RAG_CATEGORY_MAP`, `PART_DEFAULT_CATEGORIES`, `PART_RAG_TAG_MAP`, `PART_RAG_FOLDER_MAP`, `get_default_tags_for_part()`, `detect_rag_categories()`, `build_rag_classification_markdown()`, `_unique_keep_order()`)을 순수 Python 모듈인 `rag_tag_system.py`로 분리 추출하였습니다.
  - `rag_tag_system.py` 모듈 내에서 Streamlit 임포트 및 세션 상태 접근을 배제하여 의존성 없는 구조를 구축했습니다.
  - `app_v16_1_3.py`를 신규 생성하여 분리된 RAG 자산들을 `from rag_tag_system import ...` 형식으로 불러와 연결되도록 리팩토링을 마쳤습니다.
  - 구동 스크립트 3종(`RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs`)의 Streamlit 실행 타겟을 `app_v16_1_3.py`로 갱신하여 릴리즈를 일원화했습니다.
### 영향 파트
- RAG 자동 분류 및 태그 인덱싱 엔진, 파트별 RAG 검색 컴포넌트(Librarian, Alchemist 등), 실행 배포 파이프라인
### 수정 파일
- `app_v16_1_3.py`
- `rag_tag_system.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.2 — 2026-05-26 07:15
### 변경 내용
- **Gemma Assistant Completion Phase 2 (Recent Activity Dynamic Sync)**:
  - `rag_memory_utils.py` 내에 `update_recent_activity_memory()` 함수를 신규 개발하고, `build_recent_activity_memory()`를 리스트 필터링 구조로 고도화하여 정적 요약을 보완한 실시간 갱신 시스템을 구현했습니다.
  - 리스트 용량을 최대 15개로 규정하여 오래된 기록은 자동으로 FIFO 방식으로 배출되도록 안전 한도를 적용했습니다.
  - `sage_popups.py` 내의 이벤트 감지 시점(사용자 질문 전송 `_on_popup_send()`, 에이전트 및 수동 Tavily 검색 완료, References 파일 주입 로드 시, `_save_to_obsidian_with_tags` 옵시디언 저장 완료 시)에 자동으로 최근 활동 기록을 실시간 누적 갱신하게 연동했습니다.
  - `app_v16_1_2.py` 내의 상태 보존 시점(`save_workspace_state()`, `save_obsidian_memory()`, 파트별 `lock_and_push_final_version()` 잠금 및 `create_revision_version()` 수정본 생성 시)에도 자동으로 활동 기억이 실시간 누적 갱신되도록 연동했습니다.
  - `st.caption("🧠 Recent Activity Synced")` 코드를 적용하여 주입 시 인지 상태를 시각화했습니다.
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 및 내부 임포트 버전을 `app_v16_1_2.py`로 갱신하여 릴리즈를 일원화했습니다.
### 영향 파트
- 젬마 어시스턴트 대화 팝업(`popup_assistant()`), 세션 및 설정 보존부, 파트 최종 잠금/수정 파이프라인
### 수정 파일
- `app_v16_1_2.py`
- `sage_popups.py`
- `rag_memory_utils.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.1.1 — 2026-05-26 06:58
### 변경 내용
- **Gemma Assistant Completion Phase 1 (Recent Activity Memory 연동)**:
  - `rag_memory_utils.py` 내부에 `build_recent_activity_memory()` 유틸리티 함수를 신규 구현하여 최근 작업 흐름을 6000자 제한 내로 자동 요약하는 엔진을 구축했습니다.
  - `sage_popups.py` 내의 `popup_assistant()` 스트리밍 대화 블록에서 `[현재 파트 컨텍스트] -> [RECENT_ACTIVITY_MEMORY] -> [REFERENCES_MEMORY]` 순으로 시스템 컨텍스트가 결합되도록 통합 연동했습니다.
  - UI 상에 Recent Activity Memory가 성공적으로 적재되었음을 알리는 `🧠 Recent Activity Memory Loaded` 캡션 노출 코드를 적용했습니다.
  - `sage_popups.py` 내의 `save_workspace_state` 임포트 버전을 `app_v16_1_1`로 업데이트하여 버전 미스매치를 방지했습니다.
  - `app_v16_1_1.py` 버전을 정식 개발 기준본으로 승격하고, 배치 및 VBS 실행 파일 3종의 실행 타겟을 `app_v16_1_1.py`로 갱신했습니다.
### 영향 파트
- 젬마 어시스턴트 대화 팝업(`popup_assistant()`), RAG 최적화 레이어, 실행 배포 스크립트 3종
### 수정 파일
- `app_v16_1_1.py`
- `sage_popups.py`
- `rag_memory_utils.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.0.3 — 2026-05-25 20:30 (오늘 최종 작업 종료 및 안정 상태 고정)
### 변경 내용
- **v16.0.3 안정 상태 고정 및 환경 정리**:
  - 오늘 작업의 성과인 젬마 어시스턴트 RAG 기능 고도화 및 `rag_memory_utils.py` 모듈 독립 분리가 검증된 안정 기준본을 최종 고정했습니다.
  - `app_v16_0_3.py`를 최종 구동 타깃으로 결정하고 배치 및 VBS 실행 스크립트 3종의 대상을 `app_v16_0_3.py`로 롤백 및 연결 고정 완료했습니다.
  - `sage_popups.py` 내의 `save_workspace_state` 임포트 버전을 `app_v16_0_3`으로 일괄 동기화했습니다.
- **RAG Utility 독립 검증 및 예외망 확보**:
  - References 4개 테스트 파일을 이용해 RAG 오염 필터 및 RAG 인용 출처 노출 동작을 이상 없이 검증했습니다.
  - 예외 안전망을 확보하여 어시스턴트 로드 실패 시에도 대화 흐름이 멈추지 않는 "실전 사용 가능한 Gemma Assistant 베타" 상태를 완료했습니다.
### 영향 파트
- 앱 배포 파이프라인, 세션 동기화 및 젬마 어시스턴트 대화 팝업
### 수정 파일
- `app_v16_0_3.py`
- `sage_popups.py`
- `rag_memory_utils.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_Obsidian/sessions/session_20260525_final_status_v16_0_3.md`
- `00_History\CHANGELOG.md`

---

## v16.0.3 — 2026-05-25 20:15
### 변경 내용
- **v16.0.2 검증 성공본을 Stable Checkpoint로 고정**:
  - `app_v16_0_2.py`를 기반으로 신규 `app_v16_0_3.py` 버전을 생성했습니다.
  - 새 기능 추가나 UI 구조 변경 없이 안정 버전 고정을 위한 상단 주석 설명만 갱신 완료했습니다.
- **실행 배치 및 스크립트 파일 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 구동 및 검사 대상을 `app_v16_0_3.py`로 일괄 업데이트 완료했습니다 (포트 8505 유지).
- **안정본 세션 기록 문서 작성**:
  - `00_Obsidian/sessions/session_20260525_v16_0_3_stable_checkpoint.md` 문서를 생성하여 RAG Utility 모듈 분리 성과 및 References 테스트 파일 4종의 필터링 세부 결과(1개 로드 성공, 3개 안전 제외)를 명확히 기록해 두었습니다.
### 영향 파트
- 앱 배포 파이프라인 및 안정본 세션 관리
### 수정 파일
- `app_v16_0_3.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_Obsidian/sessions/session_20260525_v16_0_3_stable_checkpoint.md`
- `00_History\CHANGELOG.md`

---

## v16.0.2 — 2026-05-25 19:55
### 변경 내용
- **RAG Utility Module 분리 및 Streamlit 의존성 제거**:
  - RAG Memory와 관련된 핵심 함수 5종(`load_recent_reference_files`, `build_gemma_memory_prompt_preview`, `build_manual_gemma_memory_buffer`, `build_manual_memory_injected_prompt`, `build_condensed_reference_context`)을 `rag_memory_utils.py` 유틸 모듈로 완전히 분리 추출했습니다.
  - `rag_memory_utils.py` 내부에서는 Streamlit 임포트(`import streamlit`) 및 `st.*` API 호출을 완전히 제거하여 순수 Python 환경에서 실행 가능하도록 정제했습니다.
- **오염/비정상 파일 제외 로그 제어권 이관**:
  - `build_condensed_reference_context()`가 직접 화면에 출력하지 않고, 제외된 오염/비정상 파일 목록을 튜플 `(prompt, excluded_files)`로 반환하도록 개선했습니다.
  - `sage_popups.py` 내의 `popup_assistant()`에서 반환된 제외 파일 목록을 수신하여 팝업 렌더링 시점에 직접 `st.caption`으로 제외 로그를 출력하도록 이관했습니다.
- **임포트 및 배포 스크립트 갱신**:
  - `app_v16_0_2.py` 및 `sage_popups.py` 내부의 RAG 중복 정의 및 `app_v16_0_1` 임포트를 제거하고 `from rag_memory_utils import ...` 구조로 갱신하여 안정화했습니다.
  - `sage_popups.py` 내 `save_workspace_state` 임포트 버전을 `app_v16_0_2`로 갱신했습니다.
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 배치 및 스크립트 파일들의 구동 대상을 `app_v16_0_2.py`로 변경 완료했습니다.
### 영향 파트
- 젬마 어시스턴트 대화 탭(`popup_assistant()`) 및 배포 파이프라인
### 수정 파일
- `app_v16_0_2.py`
- `sage_popups.py`
- `rag_memory_utils.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.0.1 — 2026-05-25 19:30
### 변경 내용
- **References Memory 주입 품질 최적화**:
  - `app_v16_0_1.py` 에 최신 References 기억을 압축 및 최적화하여 젬마 프롬프트 형태로 변환해 주는 `build_condensed_reference_context()` 함수를 추가했습니다.
  - 최신 8개 파일은 본문 일부(최대 800자) 및 요약/키워드/위키링크/SOURCE를 유지하며, 9번째 이후 파일(오래된 파일)은 본문을 생략하고 메타데이터 및 핵심 키워드/요약만 고압축하여 제공하도록 개선했습니다.
  - 파일 간의 중복된 위키링크와 해시태그를 전역적으로 머지 및 정리하여 최상단에 제공하는 전역 위키링크 모음 기능을 포함했습니다.
- **RAG 파일 안전 필터링 규칙 도입 (추가 안전 조건)**:
  - 본문 길이 300자 미만 파일 제외
  - 특정 HTML/오염 문자열(span, display, background-color, 자동저장:, [EP001]) 포함 파일 제외
  - SOURCE / 키워드 / 위키링크가 모두 비어있는 파일 제외
  - 동일 파일명 중복 시 수정시간(mtime) 기준 최신 파일만 사용
  - 필터링에 의해 제외된 오염/비정상 파일 발생 시 `st.caption` 제외 로그 출력 적용
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내의 `save_workspace_state` 및 RAG 임포트 경로를 `app_v16_0_1`로 갱신했습니다.
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 배치 및 스크립트 파일들의 구동 대상을 `app_v16_0_1.py`로 변경 완료했습니다.
  - RAG 로딩 상태 표시를 `"🧠 References Memory Loaded: X files"` 형태로 변경하고, 에러가 발생해도 대화 흐름이 무너지지 않도록 예외 처리 안전망을 유지했습니다.
### 영향 파트
- 젬마 어시스턴트 대화 탭(`popup_assistant()`) 및 배포 파이프라인
### 수정 파일
- `app_v16_0_1.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v16.0.0 — 2026-05-25 19:25
### 변경 내용
- **젬마 어시스턴트 팝업 내 References RAG 메모리 주입 연동**:
  - `sage_popups.py`의 `popup_assistant()` Gemma 대화 스트리밍 처리부(`pending_stream` 처리 블록)에 `load_recent_reference_files()` 및 `build_gemma_memory_prompt_preview()`와 `build_manual_gemma_memory_buffer()`를 결합하여 최근 References 및 파일 RAG 데이터를 주입 완료했습니다.
  - RAG 데이터 주입은 `max_chars=30000`자로 안전 절사 처리를 동반하며, `try-except` 예외 처리 및 폴백(`st.caption` 우회 알림)을 적용하여 로드 실패 시에도 대화 흐름이 절대 중단되지 않도록 완벽하게 안전망을 구축했습니다.
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v16_0_0`으로 업데이트했습니다.
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 배치 및 스크립트 파일들의 구동 대상을 `app_v16_0_0.py`로 통합 완료했습니다. (포트 8505)
- **컴파일 무오류 검증 완료**:
  - `app_v16_0_0.py` 및 `sage_popups.py` 두 자산의 `py_compile` 무오류 통과를 완료했습니다.
### 영향 파트
- 젬마 어시스턴트 대화 탭(`popup_assistant()`) 및 배포 파이프라인
### 수정 파일
- `app_v16_0_0.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.34.26 — 2026-05-25 18:55
### 변경 내용
- **하단 임시 개발자 테스트 UI 비활성화 처리**:
  - `st.markdown("### 🛠️ 개발자 테스트 영역: 파일 텍스트 추출기")` 하위의 모든 임시 개발자 테스트 위젯 블록을 물리적 삭제 없이 `if False:` 조건문으로 래핑하여 비활성화/숨김 처리했습니다.
  - 이로써, 사용자 실서빙 모드에서 불필요한 개발용 콘솔 UI 노출을 완벽하게 숨기면서도 기존 구조를 안전하게 보존했습니다.
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_26`으로 업데이트했습니다.
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 배치 및 스크립트 파일들의 구동 대상을 `app_v15_9_34_26.py`로 변경 완료했습니다. (포트 8505)
- **컴파일 무오류 검증 완료**:
  - `app_v15_9_34_26.py` 및 `sage_popups.py` 두 자산의 `py_compile` 무오류 통과를 완료했습니다.
### 영향 파트
- 앱 배포 파이프라인 및 메인 페이지 최하단 렌더링 레이어
### 수정 파일
- `app_v15_9_34_26.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.34.24 — 2026-05-25 17:30
### 변경 내용
- **어플리케이션 시작 시 RAG 설정 파일 정화 프로세스 자동화**:
  - `workspace_state.json` 설정 파일 내부의 HTML 오염 문구(span 태그 등)를 앱 로딩 시 선제적으로 탐지 및 정거하는 `sanitize_workspace_prompt_values_once()` 함수를 `init_session_state()` 세션 초기화 바로 직전에 1회 강제 호출하도록 수정했습니다.
  - 이로써, 부팅 과정에서 오염 데이터가 메모리에 직접 탑재되는 것을 사전 차단하여 브라우저 화면 툴팁/팝업 오작동 현상을 완벽하게 해소했습니다.
- **실행 포트 통합 및 구동 스크립트 정비**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일의 구동 타깃을 모두 최신 버전인 `app_v15_9_34_24.py` 파일로 갱신 완료했습니다.
  - `RUN_DEBUG.bat` 스크립트에 누락된 `--server.port 8505` 옵션을 추가 적용하여 포트 8505로 실행이 통일되도록 조치했습니다.
### 영향 파트
- 앱 구동 시 초기화 레이어 및 부팅/배포 파이프라인
### 수정 파일
- `app_v15_9_34_24.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.34.22 — 2026-05-25 13:20
### 변경 내용
- **Gemma RAG 주입용 최종 프롬프트 조립 엔진 구현**:
  - 9차의 `memory_buffer`와 사용자 임시 입력을 결합하여 젬마 어시스턴트 입력 규격을 생성하는 `build_manual_memory_injected_prompt()` 함수를 구현했습니다.
  - 최종 조립된 프롬프트 크기가 `max_chars=40000`자를 초과하는 경우, 사용자 질문 훼손 방지를 위해 memory_buffer 우선 절사 처리를 적용하고 `[프롬프트 일부 생략됨 — max_chars 제한]` 생략 문구를 자동 결합하도록 예외 방지 패턴을 적용했습니다.
- **수동 실제 주입 테스트 UI 연동 및 1회성 call_gemma() 호출**:
  - 최하단 테스트 영역에 "✏️ 테스트 질문 입력" 필드 및 "🚀 Gemma Memory 실제 주입 테스트" 컴포넌트를 추가하고, 사용자가 수동 버튼을 클릭했을 때에만 1회성 `call_gemma()` API 호출을 유발하여 응답 결과를 출력하도록 구성했습니다.
  - 디버그 및 미리보기 용도인 `st.session_state["debug_memory_preview"]` 및 `st.session_state["debug_memory_response"]` 에만 기록 및 출력을 격리했습니다. (기존 popup_assistant() 및 chat_history의 데이터 오염 방지)
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_22`로 교체했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 배치 파일들의 구동 대상을 `app_v15_9_34_22.py`로 변경 완료했습니다.
### 영향 파트
- 파일 업로드 및 RAG 어시스턴트 1회성 테스트 호출 영역
### 수정 파일
- `app_v15_9_34_22.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.21 — 2026-05-25 13:10
### 변경 내용
- **임시 Gemma RAG 메모리 버퍼 빌더 구현**:
  - 8차 결과물(`prompt_preview`)을 받아 실제 Assistant 프롬프트 앞부분에 삽입할 수 있는 ACTIVE 구조화 버퍼(`[ACTIVE_REFERENCE_MEMORY]`)를 조립하는 `build_manual_gemma_memory_buffer()` 함수를 구현했습니다.
  - 버퍼의 최종 크기가 `max_chars=32000`자를 초과하는 경우, 내부 프리뷰 문자열을 자르고 `[메모리 일부 생략됨 — max_chars 제한]` 생략 구문을 자동 추가하도록 설계했습니다.
- **수동 버퍼 주입 테스트 UI 연동**:
  - 최하단 테스트 영역에 "🧠 Gemma Memory Inject 테스트" 컴포넌트를 추가하고, 사용자가 수동 버튼을 클릭했을 때에만 메모리 로드 및 가공, 버퍼 생성을 실행하여 생성된 버퍼를 `st.text_area` 상에 출력하도록 구성했습니다.
  - 생성된 버퍼를 디버그 미리보기 용도인 `st.session_state["debug_memory_preview"]`에만 저장하도록 격리하였습니다. (메시지, 채팅 히스토리, RAG Index 등 다른 상태의 보존성 유지)
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_21`로 교체했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 배치 파일들의 구동 대상을 `app_v15_9_34_21.py`로 변경 완료했습니다.
### 영향 파트
- 파일 업로드 및 RAG 어시스턴트 프롬프트 주입 영역
### 수정 파일
- `app_v15_9_34_21.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.20 — 2026-05-25 13:00
### 변경 내용
- **Gemma 어시스턴트용 RAG 메모리 블록 빌더 구현**:
  - References 로더 결과 리스트를 가공하여 젬마 프롬프트 컨텍스트에 삽입 가능한 통합 RAG 기억 장치 블록을 조립하는 `build_gemma_memory_prompt_preview()` 함수를 구현했습니다.
  - 마크다운 파싱 헬퍼 `parse_markdown_reference()`를 도입하여 원문, 키워드 목록, 요약 정보를 완벽하게 발췌하도록 설계했습니다.
  - 프롬프트 블록의 최종 크기가 `max_chars=30000`자를 초과할 수 없도록 설계했으며, 초과 시 본문을 안전하게 절삭하고 `[메모리 일부 생략됨 — max_chars 제한]` 안내 문구를 자동 결합하는 에러 방지 패턴을 확립했습니다.
- **수동 프롬프트 미리보기 UI 연동**:
  - 최하단 테스트 영역에 "🧠 Gemma Memory Prompt 미리보기" 컴포넌트를 추가하고, 사용자가 직접 버튼을 클릭했을 때에만 실시간으로 메모리를 가공해 생성된 프롬프트 문자열 전문을 대용량 `st.text_area` 컴포넌트(높이 500px)에 출력하도록 연동했습니다.
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_20`로 교체했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 배치 파일들의 구동 대상을 `app_v15_9_34_20.py`로 변경 완료했습니다.
### 영향 파트
- 파일 업로드 및 RAG 어시스턴트 프롬프트 빌더 영역
### 수정 파일
- `app_v15_9_34_20.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.19 — 2026-05-25 12:45
### 변경 내용
- **References 최신 파일 안전 로더 구현**:
  - `00_Obsidian/References/` 고정 경로에 저장된 최신 마크다운 파일들을 수정 시간(`mtime`) 내림차순(최신순)으로 정렬하여 메모리에 읽기 전용으로 안전하게 로드하는 `load_recent_reference_files()` 함수를 구현했습니다.
  - 최대 파일 수 `max_files=20` 제한 및 총 누적 글자 수 `max_chars=120000` 상한 제한(초과 시 문자열 절삭 및 truncated 플래그 설정)을 통해 메모리 오버헤드를 원천 차단했습니다.
- **수동 로드 버튼 UI 연동**:
  - 최하단 테스트 영역에 "📖 References 로드 테스트" 컴포넌트를 추가하고, 자동 로드가 아닌 사용자가 수동 버튼을 클릭했을 때만 파일 로드를 실행하여 읽어온 파일 목록과 용량 상태, 3000자 이내의 본문 내용을 `st.expander`를 통해 실시간으로 렌더링합니다.
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_19`로 교체했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 배치 파일들의 구동 대상을 `app_v15_9_34_19.py`로 변경 완료했습니다.
### 영향 파트
- 파일 업로드 및 References 아카이브 로더 영역
### 수정 파일
- `app_v15_9_34_19.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.18 — 2026-05-25 12:15
### 변경 내용
- **References 수동 저장 엔진 구현**:
  - 4차 RAG 공용 태그 및 감지된 메타데이터를 포함한 마크다운을 `C:\SageMirror_Production\00_Obsidian\References\` 고정 폴더에 UTF-8 인코딩으로 영구 저장하는 `save_reference_markdown_file()` 함수를 구현했습니다.
  - 파일명 생성 시 원본 파일의 stem 이름에 대해 Windows 금지 문자(`< > : " / \ | ? *`)를 제거하고 공백을 `_`로 변환한 후, 타임스탬프(`_YYYYMMDD_HHMM.md`)를 접미사로 자동 결합하여 안전성을 높였습니다.
  - 파일 내부 구조는 지정된 템플릿(메타데이터, 전체 공용 태그, 위키링크, 핵심 키워드 목록, 2차 Markdown 원문 정리) 형식을 철저히 준수하도록 구성했습니다.
- **수동 저장 버튼 UI 연동**:
  - 최하단 테스트 영역에 "📥 References 저장 테스트" 컴포넌트를 추가하고, 자동 저장이 아닌 사용자가 수동 버튼을 클릭했을 때만 파일이 저장되도록 이벤트를 결합했습니다.
  - 저장 완료 시 생성된 마크다운 문서의 절대 경로만 `st.success` 화면에 깔끔하게 표시해 줍니다.
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_18`로 교체했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 배치 파일들의 구동 대상을 `app_v15_9_34_18.py`로 변경 완료했습니다.
### 영향 파트
- 파일 업로드 및 References 아카이브 저장 영역
### 수정 파일
- `app_v15_9_34_18.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.17 — 2026-05-25 12:05
### 변경 내용
- **RAG 공용 태그 빌더 구현**:
  - `PART_RAG_TAG_MAP`의 `part1`부터 `part8`까지의 모든 기본 태그를 순서대로 병합 및 `_unique_keep_order`를 통한 중복 제거(최대 80개 이하)를 수행하는 `build_all_parts_common_tags_preview()` 함수를 구현했습니다.
  - 이 빌더는 `detection`에서 넘겨받은 `keywords`, `wiki_links`, `hash_tags`와 공용 태그를 순서 유지하며 병합 및 중복 제거(각각 최대 120개 이하)를 수행하며, 공백을 `_`로 치환하고 `#` 접두사를 보장하는 해시태그 정리 규칙을 적용해 딕셔너리로 반환합니다.
- **개발자 테스트 UI 연동**:
  - 최하단 테스트 영역에 "🌐 전체 8파트 공용 태그 미리보기" 섹션을 추가하여 실시간 병합 데이터(전체 파트 태그, 통합 키워드, 통합 위키링크, 통합 해시태그)를 출력합니다.
- **임포트 및 배포 스크립트 갱신**:
  - `sage_popups.py` 내 `save_workspace_state` 임포트 참조를 `app_v15_9_34_17`로 교체했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 배치 파일들의 구동 대상을 `app_v15_9_34_17.py`로 변경 완료했습니다.
### 영향 파트
- 파일 업로드 및 RAG 공용 분석 미리보기 영역
### 수정 파일
- `app_v15_9_34_17.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.16 — 2026-05-25 12:05
### 변경 내용
- **기존 detect_rag_categories() 분석 시스템 연결**:
  - 파일 업로드 -> 텍스트 추출 -> 마크다운 구조화 결과에 대해 기존에 완성되어 있던 RAG 카테고리/키워드/위키링크/해시태그 감지 함수인 `detect_rag_categories()`를 연동했습니다. (임시 part_key="part1" 고정 참조)
- **임시 개발자 테스트 UI 확장**:
  - 메인 페이지 최하단 개발자 테스트 UI에 "자동 RAG 카테고리 분석 미리보기" 컴포넌트를 탑재하여 감지된 카테고리, 점수, 키워드, 위키링크, 해시태그(각각 상위 30개)를 실시간 `st.write`로 시각화해 줍니다.
- **sage_popups.py, 구동 및 디버그 스크립트 실행 타겟 버전 상향**:
  - `sage_popups.py` 내의 `save_workspace_state` 임포트 버전을 `app_v15_9_34_16`으로 상향했습니다.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 Streamlit 실행/컴파일 타겟을 `app_v15_9_34_16.py`로 갱신 완료했습니다.
### 영향 파트
- **App Core (RAG Category Connection)**: 파일에서 구조화된 마크다운을 분석해 RAG 인덱싱할 카테고리/태그 정보를 추출하는 시스템 연동.
- **Developer Test Area**: 분석된 RAG 카테고리 및 해시태그 메타데이터를 즉각 검증할 수 있는 디버깅 뷰 구성.
### 수정 파일
- `app_v15_9_34_16.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.15 — 2026-05-25 11:55
### 변경 내용
- **Markdown 구조화 엔진 추가**:
  - `convert_text_to_markdown_structure(raw_text, source_name)` 유틸 함수를 추가하여 업로드 텍스트를 마크다운 양식으로 자동 구조화하는 기능을 개발했습니다.
  - HTML 잔여 태그 제거, 연속 공백 및 3줄 이상 빈줄 제거, 특수문자 반복 제거 등 텍스트 자동 정리 규칙을 적용했습니다.
  - 텍스트 앞부분을 기준으로 핵심 문장들을 발췌하여 '핵심 요약' 블록을 자동 생성하도록 설계했습니다.
  - 메모리 폭주 방지를 위해 5만 자 초과 시 생략 처리 문구(`[문서 일부 생략됨]`)를 추가하는 안전장치를 적용했습니다.
- **임시 개발자 테스트 UI 확장**:
  - 메인 최하단의 1차 테스트 UI 하단에 구조화된 마크다운 결과를 실시간으로 프리뷰할 수 있는 마크다운 텍스트 영역 컴포넌트를 추가했습니다.
- **sage_popups.py 및 구동 스크립트 실행 타겟 버전 상향**:
  - `sage_popups.py` 내의 `save_workspace_state` 임포트 버전을 `app_v15_9_34_15`로 상향했습니다.
  - `RUN_APP.bat` 파일의 Streamlit 실행 타겟을 `app_v15_9_34_15.py`로 갱신 완료했습니다.
### 영향 파트
- **App Core (Markdown Converter)**: 파일 텍스트를 정리하여 정형화된 마크다운 구조로 변환하는 유틸 모듈 탑재.
- **Developer Test Area**: 마크다운 변환 결과의 실시간 확인을 위한 프리뷰 컴포넌트 연동.
### 수정 파일
- `app_v15_9_34_15.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.14 — 2026-05-25 11:45
### 변경 내용
- **업로드 파일 텍스트 추출 안전 유틸 함수 추가**:
  - `extract_text_from_uploaded_file(uploaded_file)` 함수를 추가하여 TXT, MD, HTML, PDF 파일에서 텍스트를 안전하게 추출할 수 있는 기능을 구현했습니다.
  - HTML 파일의 경우 BeautifulSoup 라이브러리를 이용하여 script, style 태그를 분해(decompose)한 뒤 순수 텍스트만 추출하며, 라이브러리 부재 시 정규식 폴백 처리를 적용했습니다.
  - PDF 파일의 경우 pypdf / PyPDF2 라이브러리를 사용하여 안전하게 텍스트를 추출하며, 실패하거나 라이브러리가 없을 시 None을 반환하도록 예외 처리를 구성했습니다.
- **임시 개발자 테스트 UI 추가**:
  - 메인 라우팅 블록의 최하단에 파일 업로더와 텍스트 프리뷰 영역을 렌더링하는 임시 테스트 UI를 안전하게 추가했습니다. (사이드바 수정금지 룰을 회피하기 위해 메인 하단에 배치함)
- **sage_popups.py 및 구동 스크립트 실행 타겟 버전 상향**:
  - `sage_popups.py` 내의 `save_workspace_state` 임포트 버전을 `app_v15_9_34_14`로 상향했습니다.
  - `RUN_APP.bat` 파일의 Streamlit 실행 타겟을 `app_v15_9_34_14.py`로 갱신 완료했습니다.
### 영향 파트
- **App Core (File Utility)**: 파일 형식별 텍스트 추출 안전 모듈 추가.
- **Developer Test Area**: 텍스트 추출 기능 검증을 위한 메인 하단 임시 UI 컴포넌트 추가.
### 수정 파일
- `app_v15_9_34_14.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.13 — 2026-05-25 11:30
### 변경 내용
- **상단 공통 프롬프트 HTML 오염 정화 필터 강화**:
  - `clean_prompt_contamination(text)` 함수를 보강하여 span 태그, CSS 속성, LED UI 잔재 문자열 등 14개 이상의 오염 패턴을 정규식 및 개별 치환으로 완벽 제거하도록 구현했습니다.
- **상태 로드 및 초기화 정화 자동화**:
  - `load_workspace_state()` 내부에서 14개 주요 키(`obsidian_rules`, `base_prompt_rules`, `p1_gemma_protocol` 등) 로드 시 정화 함수를 일괄 적용하도록 했습니다.
  - 앱 시작 직후 `init_session_state()`에서 로드된 세션 상태에 대해서도 1회 정화 처리를 수행하고, 변경 사항이 있을 시 `save_workspace_state()`를 통해 `workspace_state.json`에 영속화하도록 자동화했습니다.
- **상단 공통 패널 저장 시 강제 정화 적용**:
  - 옵시디언 규칙서 및 마스터 프롬프트 저장 버튼 핸들러 내부에서 저장 직전 `clean_prompt_contamination()`을 호출하여 오염을 원천 차단했습니다.
- **sage_popups.py 및 구동 스크립트의 실행 타겟 버전 상향**:
  - `sage_popups.py` 내의 `save_workspace_state` 임포트 버전을 `app_v15_9_34_13`으로 갱신하여 버전 불일치 오류를 막았습니다.
  - `RUN_APP.bat` 파일의 Streamlit 실행 타겟을 `app_v15_9_34_13.py`로 갱신 완료했습니다.
### 영향 파트
- **App Core (Contamination Cleaning)**: 상태 로드/세션 초기화/저장 시점의 HTML 오염 완전 제거.
- **sage_popups & RUN_APP.bat**: 최신 앱 구동 버전(`v15.9.34.13`) 연동 완료.
### 수정 파일
- `app_v15_9_34_13.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.34.10 — 2026-05-24 22:45
### 변경 내용
- **떡상채널 발굴기 큐레이션 프롬프트 보강**:
  - `kw_prompt` 및 `filter_prompt` 내의 `[공통 조건]` 및 `[공통 평가 기준]` 블록에 다크심리학(가스라이팅, 나르시시즘, 독성관계 등), 4070 공명 및 인생 체험담(댓글 공명 지수) 관련 분석 기준을 고도화하여 타겟 채널 발굴기의 매칭 성능을 극대화했습니다.
- **실행 스크립트 3종의 구동 버전 상향**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 타겟 버전을 `app_v15_9_34_10.py`로 갱신 완료했습니다.
### 영향 파트
- **Part 1 (벤치마킹)**: 떡상채널 발굴기 제미나이 큐레이션 알고리즘 프롬프트 보강.
- **App Core & Launch Scripts**: 실행 스크립트 3종 타겟 갱신.
### 수정 파일
- `app_v15_9_34_10.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.34.9 — 2026-05-24 22:25
### 변경 내용
- **[A] popup_edit_text_value() 내 sync_flag_key 버그 수정**:
  - `session_key`가 `obsidian_rules`가 아닐 때 sync flag 세션 변수명이 `top_pr_view_{session_key}_widget`과 매칭되도록 `_widget_key = f"top_pr_view_{session_key}_widget"` 및 `_sync_key = f"_sync_{_widget_key}_next_run"` 패턴으로 동기화 로직을 정확하게 매치하여 저장 후 팝업 미차단 버그를 해결했습니다.
- **[C] P2_MASTER_PROMPT_DEFAULT 연금술 변환 공식 v2.0 완성본 교체**:
  - 기-승-전-결 연금술 공식 및 다크심리학, 철학(쇼펜하우어, 융, 프랭클, 스토아), 에세이(몽테뉴), 성경의 융합 구조가 상세히 탑재된 마스터 프롬프트 완성본 v2.0으로 교체 완료했습니다.
- **[D] 실행 스크립트 3종의 구동 버전 상향**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 타겟 버전을 `app_v15_9_34_9.py`로 갱신 완료했습니다.
### 영향 파트
- **Part 2 (총괄기획)**: 연금술 융합 설계 프롬프트 v2.0 탑재.
- **App Core & Dialogs**: 팝업창 텍스트 에디터 저장/동기화 락 해제 버그 수정 및 실행 파일 타겟 갱신.
### 수정 파일
- `app_v15_9_34_9.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.34.8 — 2026-05-24 22:10
### 변경 내용
- **최종 안정본 연결 및 실행 스크립트 3개 업데이트**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 실행 연결 대상을 최신 안정본인 `app_v15_9_34_8.py`로 일괄 연결 완료했습니다.
  - `RUN_DEBUG.bat` 검사 대상에 `sage_popups.py`를 추가하여 두 핵심 파일(`app_v15_9_34_8.py`, `sage_popups.py`)의 컴파일 적합성을 엄격히 자동 체크하도록 개선했습니다.
### 영향 파트
- **App Core / Launch Scripts**: 실행 스크립트 3종의 타겟 갱신 및 컴파일 안정성 강화.
### 수정 파일
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.34.1 — 2026-05-24 17:22
### 변경 내용
- **Part 2 Alchemist 마스터 프롬프트 4종 양방향 바인딩 세션 꼬임 수정**:
  - `p2_gemma_protocol`, `p2_bench_prompt`, `p2_research_prompt`, `p2_plan_prompt` 4개 프롬프트의 위젯 key와 실제 세션 데이터 key를 분리(`_widget` 접미사 추가)하여 팝업창 편집 저장본이 메인 구버전 위젯 버퍼에 덮어써지는 현상을 완전히 해결했습니다.
- **직접 수정 방지 및 팝업 편집 가이드 안내**:
  - 메인 화면에 표시되는 `p2_gemma_protocol` 텍스트 영역을 직접 타이핑할 수 없도록 `disabled=True` 처리하고, 하단에 `"직접 수정은 아래 [프로토콜 팝업 편집] 버튼을 사용하십시오."` 캡션 안내 문구를 추가했습니다.
- **PIN 잠금 상태에 따른 프롬프트 편집 비활성화 정책 적용**:
  - 보안 및 편집 안전을 위해 `p2_edit_proto`, `p2_edit_bench_prompt_btn`, `p2_edit_res_prompt_btn` (자료조사), `p2_edit_plan_prompt_btn` (총괄기획) 4개 편집 버튼에 `disabled=is_locked`를 추가하여 마스터 PIN이 풀린 상태에서만 팝업 수정이 가능하도록 제한했습니다.
- **popup_edit_gemma_protocol_p2() 및 popup_edit_text_value() 저장 방식 개선**:
  - 저장 시 `save_workspace_state()`를 명시적으로 실행하여 세션 데이터를 로컬 디스크 파일에 확실히 영속 저장한 뒤 토스트 메시지를 출력하고 `st.rerun()`을 호출하도록 저장 처리 흐름을 표준화했습니다.
  - `popup_edit_gemma_protocol_p2()` 내부의 text_area와 버튼들에 고유 key(`p2_gemma_protocol_popup_textarea`, `p2_gemma_protocol_popup_save`, `p2_gemma_protocol_popup_cancel`)를 부여해 중복 충돌을 방지했습니다.
### 영향 파트
- **Part 2 (총괄기획)**: 마스터 프롬프트 4종 편집 및 저장 기능 보강, 보안 잠금 상태 편집 연동.
### 수정 파일
- `app_v15_9_34_1.py`
- `00_History\CHANGELOG.md`

---

## v15.9.33 — 2026-05-24 16:00
### 변경 내용
- **RAG 검색 카테고리 분류 시스템 도입**:
  - `RAG_CATEGORY_MAP`, `PART_DEFAULT_CATEGORIES` 상수 2개 및 `get_default_tags_for_part()` 헬퍼 함수를 추가하여 파트별 고유 기본 카테고리 세트를 매핑했습니다.
  - `render_obsidian_rag_search()` 함수 내부에 카테고리 멀티 체크박스 선택 UI를 결합하고, 체크박스 토글 시 세션 상태(`partN_selected_categories`, `partN_rag_query_val`)가 동적으로 즉각 갱신 및 rerunning되어 검색 쿼리에 적용되도록 구현했습니다.
  - 파트 1~8의 `render_obsidian_rag_search` 호출부 총 8개의 기본 태그 값을 `get_default_tags_for_part("partN")` 호출로 일괄 교체했습니다.
- **RAG_TAG_SYSTEM 및 call_gemma / sage_popups.py 연동**:
  - `sage_config.py` 로부터 `RAG_TAG_SYSTEM`을 `app_v15_9_33.py` 에 임포트하고 `call_gemma()` 함수 시작 부분에 시스템 프롬프트용 태그 목록을 자동 주입하는 로직을 통합했습니다.
  - `sage_popups.py` 내의 `popup_assistant` 대화 시스템 프롬프트(sys_ctx) 구성 시에도 `RAG_TAG_SYSTEM` 목록이 누락되지 않고 자동 주입되도록 시스템을 강화했습니다.
- **세션 상태 및 저장 영속성 연동**:
  - `init_session_state()`의 `defaults` 딕셔너리에 Part 5~8의 RAG 검색 결과, 쿼리, 모델 선택자 및 파트 1~4의 카테고리 상태 키 20개를 초기값으로 탑재했습니다.
  - `save_workspace_state()`의 `keys_to_save` 리스트에도 해당 20개 키를 전부 등록하여 영속 저장되도록 설정했습니다.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일의 Streamlit 실행 대상을 신버전 `app_v15_9_33.py`로 일괄 업데이트했습니다.
### 영향 파트
- **RAG Engine (render_obsidian_rag_search)**: 카테고리 뷰 및 태그 동적 세팅 기능 추가.
- **App Core & Assistant (call_gemma / sage_popups)**: RAG_TAG_SYSTEM 전역 주입에 의한 에이전트 태그 추적 최적화.
- **전체 파트 (Part 1~8)**: RAG 검색 컴포넌트의 파트별 카테고리 탑재 및 호출.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_33.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.32 — 2026-05-24 11:00
### 변경 내용
- **글로벌 모델 스위칭 시스템 도입**:
  - 좌측 사이드바에 글로벌 모델 선택기(`gemma4:e2b`, `gemma4:e4b`)를 추가하여 기본적으로 전체 파트에 일괄 자동 적용되도록 구현.
  - 동시에 각 파트 화면의 최상단 우측에 있는 개별 모델 선택기는 필요에 따라 개별적으로 변경해 사용할 수 있도록 세션 독립화(프록시 모델 바인딩 구조).
  - 전체 파트 렌더링 전후에 selectbox 세션 값을 동적으로 가로채어 개별 파트 키(`p1_selected_model` ~ `p8_selected_model`)에 자동 갱신 및 저장되도록 하여 [절대 수정 금지] 구역인 `render_part1()`, `render_part2()`, `render_part34()` 내부 수정을 우회하고 무결성 유지.
- **Ollama 실시간 모델 상태 표시 동적화**:
  - `sage_engine.py` 내 `check_ollama_status` 함수가 `target_model` 파라미터를 받아 동적 검사를 진행할 수 있도록 변경.
  - 사이드바 내의 Ollama 연결 상태 표시 컴포넌트(`[OK] Ollama | ...`)가 하드코딩되었던 부분(`OLLAMA_MODEL` 고정)을 제거하고, 현재 선택된 글로벌 모델을 동적으로 검사하여 화면에 실시간 표시하도록 수정.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일의 Streamlit 실행 대상을 신버전 `app_v15_9_32.py`로 일괄 업데이트.
### 영향 파트
- **App Core (Ollama Engine & Sidebar)**: 글로벌/개별 파트 연동 모델 선택 시스템 및 Ollama 실시간 모델 상태 모듈.
- **전체 파트 (Part 1~8)**: 개별 모델 선택기의 전역 덮어쓰기 및 독립적 오버라이드.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_32.py`
- `sage_engine.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.31 — 2026-05-24 10:40
### 변경 내용
- **call_gemma 에이전트 강화 ([A], [B], [C])**:
  - `[READ_OBSIDIAN:]` 태그 감지 시 옵시디언 RAG 자동 검색 및 RAG 컨텍스트 재주입 로직 구현.
  - YouTube API와 연동하여 유튜브/채널/영상 관련 키워드가 포함될 경우 실시간 YouTube API 검색 결과 주입.
  - AI 생성물 반환 직전 Gemma Critic 에이전트를 이용한 2단계 자체 데이터 무결성 검수(1차 FAIL 시 자동 재생성, 2차 FAIL 시 경고 제공) 구축.
- **sage_popups.py 동기화 및 2단계 검수 적용 ([D])**:
  - `_execute_tool` 함수에 `SEARCH_YOUTUBE` 툴 실행 분기 추가 및 `AGENT_TOOL_PATTERNS` 딕셔너리에 추가 등록.
  - `run_agent_loop` 팝업 에이전트 루프에도 동일한 2단계 자가 데이터 무결성 검수 프로세스 이식 완료.
- **구동/실행 스크립트 실행 타겟 일괄 갱신 ([E])**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일의 Streamlit 실행 대상을 신버전 `app_v15_9_31.py`로 일괄 업데이트.
### 영향 파트
- **App Core (Gemma Engine)**: call_gemma 에이전트 자동 검색 및 2단계 검수 파이프라인.
- **Popup Assistant (sage_popups)**: 자율 팝업 에이전트의 YouTube 연동 및 검수 기능.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_31.py`
- `sage_popups.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.29 — 2026-05-24 09:56
### 변경 내용
- **결과물 표시 전용 st.text_area 일괄 리팩토링**:
  - 결과물을 표시만 하던 `st.text_area` (자료 조사 결과, 총괄 기획안, 나레이션/이미지 대본 등)를 4줄 요약 프리뷰 및 `[👁 전체 보기 & 편집]`, `[🧠]` 옵시디언 즉시 저장 기능이 결합된 `render_result_preview()` 컴포넌트로 전면 통합 교체했습니다.
  - 적용 대상: Part 1(자료조사, 전달패킷), Part 2(벤치마킹, 자료조사, 총괄기획), Part 3·4(나레이션, 이미지대본), Part 5(A-MASTER, B-MASTER, C-1결과), Part 6(Veo3결과) 전체 적용.
  - 옵시디언 규칙서 v4.0 저장 폴더 표준화 및 `p1_` ~ `p6_` 22개 저장 상태 변수 세션 영속성 연동을 마쳤습니다.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat` 파일의 Streamlit 실행 대상을 `app_v15_9_29.py`로 갱신 완료했습니다.
### 영향 파트
- **전체 파트 (Part 1~6)**: 결과물 표시 컴포넌트 프리뷰 통합 및 옵시디언 저장 자동화.
- **App Core**: 실행 환경 및 구동 배치 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_29.py`
- `RUN_APP.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.27 — 2026-05-23 23:22
### 변경 내용
- **이중 마스터 PIN 해제 경고 창(노란색 warning 박스) 제거**:
  - 각 파트(Part 1 ~ Part 8) 최상단 근처에서 중복으로 크게 자리를 차지하던 `[WARN] 분석 실행 및 편집을 위해 상단 우측에 마스터 PIN(7777)을 입력해 주세요.` 노란색 경고 창을 안전하게 일괄 삭제했습니다.
  - 이를 통해 상단 우측에 위치한 '마스터 PIN 입력 박스'만으로도 충분히 잠금 상태를 시각적으로 확인하고 입력할 수 있게 되어, 전체 화면의 미적인 불필요함을 해소하고 렘브란트 다크 테마 고유의 차분하고 깊은 레이아웃 균형을 되찾았습니다.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_27.py`로 갱신 완료했습니다.
### 영향 파트
- **전체 파트 (Part 1~8)**: 중복 경고창 제거를 통한 UI 뷰 개선 및 렘브란트 다크 테마 일관성 회복.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_27.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.26 — 2026-05-23 23:08
### 변경 내용
- **좌측 Sidebar 최상단 🎬 Episode Control Center 안전 추가**:
  - 회차별(Episode) 독립 관리 시스템을 사이드바 최상단에 은은한 버건디-골드 앰비언트 카드 스타일(컨테이너)로 구현했습니다.
  - 회차 선택(`st.selectbox`) 시 현재 회차의 결과물을 세션에 자동 저장하고, 해당 회차의 데이터를 복원 로드합니다.
  - **🆕 새 Episode 시작**: 기존 세션을 갱신 저장한 후, 현재 에피소드 중 최대 번호를 탐색해 자동으로 다음 회차(예: EP002)를 생성하고 작업 결과물 세션 키만 깔끔하게 초기화하여 시작합니다.
  - **💾 현재 Episode 전체 저장**: `C:\SageMirror_Outputs\EPXXX\` 및 옵시디언 `Studio\Episodes\EPXXX\` 경로 하위에 파트별로 세분화된 8개 하위 폴더(01_Librarian ~ 08_Dashboard)를 자동 생성하고 포맷팅된 결과물 파일들을 이중 분할 저장 및 GitHub Push를 자동으로 수행합니다.
- **에피소드 세션 상태 파일 격리 저장소 (`00_Session_States`)**:
  - 프로젝트 루트가 번잡해지지 않도록 에피소드별 실시간 세션 데이터 파일은 `C:\SageMirror_Outputs\00_Session_States\workspace_state_[EPISODE_NAME].json` 경로에 분리하여 저장/로드되도록 래핑 구현했습니다.
- **각 파트 타이틀 좌측 에피소드 번호 동적 출력**:
  - 렌더링 영역의 모든 `h3` 헤더 앞에 `[EPXXX]` 접두사가 자동으로 달라붙는 전역 CSS 스타일을 동적으로 주입하여, 파트 1~8의 화면 최상단 타이틀 좌측에 현재 작업 회차 정보가 무결하게 표시되도록 구현했습니다.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_26.py`로 갱신 완료했습니다.
### 영향 파트
- **App Core / Sidebar**: Episode Control Center 및 에피소드 격리 세션 저장/로드 기능 추가.
- **전체 파트 (Part 1~8)**: 최상단 타이틀에 현재 진행 에피소드 번호(`[EPXXX]`) 동적 접두사 표시.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_26.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.25 — 2026-05-23 22:38
### 변경 내용
- **최종본 Lock & 수정본 생성 버튼 2열 앰비언트 글로우 스타일 박스 디자인 적용**:
  - Part 1~8 전체 파트 최하단의 Lock/Revision 버튼 묶음을 은은한 골드-버건디 그라데이션 광원 배경과 골드 아웃라인 테두리, 그리고 글로우 섀도우가 적용된 앰비언트 스타일 박스(`st.container`)로 감싸 시각적 완성도를 극대화했습니다.
  - 마크다운 CSS `:has()` 선택자 기법을 사용하여 Streamlit의 레이아웃 구조를 해치지 않고 고도로 정밀한 앰비언트 레이아웃 스타일링을 전역 적용했습니다.
- **Part 1 Lock 버튼 최하단 위치 이동**:
  - 다른 파트와 달리 Step 2 중간에 끼어있던 Part 1의 Lock 버튼 위치를 Step 2의 3단 분석 엔진 렌더링이 완전히 마무리된 Part 1 최하단으로 깔끔하게 이동 배치하여 통일감을 맞추었습니다.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_25.py`로 갱신 완료했습니다.
### 영향 파트
- **전체 파트 (Part 1~8)**: Lock & Revision 버튼 영역의 앰비언트 글로우 스타일링 적용.
- **Part 1 (벤치마킹)**: 락 버튼을 파트 화면 최하단으로 위치 이동 및 2열 통일.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_25.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.24 — 2026-05-23 22:05
### 변경 내용
- **8개 파트 전체에 최종본 Lock 및 수정본 생성 시스템 통합 규격화**:
  - 기존 파트 2, 3-4, 5, 6, 7, 8 등 여러 파트 하단에 중복 배치되어 화면을 복잡하게 하던 구식 `st.button("💾 파트 X 옵시디언 자동 백업", ...)` 버튼 코드를 완전히 삭제 정리했습니다.
  - Part 1~8 전 파트 하단에 통일된 가로 2열 구성의 **`[🔒 최종본 Lock & GitHub Push]`** 및 **`[🔓 수정본 생성]`** 버튼으로 일원화하고, 각 파트별 백업 세션 변수 타겟을 정확히 매핑하여 데이터 영속성 안전 구조를 확립했습니다.
- **Git Push 대기 및 무한 로딩(락) 방지 환경설정 추가**:
  - `auto_git_push` 호출 시, 깃허브 토큰 만료 또는 네트워크 입력 대기 상태로 인해 프로세스가 무한 블로킹되는 현상을 방지하도록 `GIT_TERMINAL_PROMPT = 0` 및 `GIT_SSH_COMMAND` 환경 변수를 강제 구성하여 락 현상을 예방했습니다.
- **실행 및 구동 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_24.py`로 갱신 완료했습니다.
### 영향 파트
- **전체 파트 (Part 1~8)**: 구식 백업 버튼 제거, Lock & Push 버튼 매핑 통일 및 대칭성 최적화.
- **App Core (Git Backup)**: Git push 시 대화식 터미널 락 방지 안전 장치 적용.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_24.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.23 — 2026-05-23 21:46
### 변경 내용
- **파트 1 Step 2 '현자의 거울 3단 분석 엔진'의 탭 라벨과 탭 내 제목 100% 일치화**:
  - 파트 1의 Step 2 탭 버튼 라벨 `"[TARGET] 1️⃣ 채널 벤치마킹"`, `"📚 2️⃣ 자료 조사"`, `"[PACKAGE] 3️⃣ Part 2 전달 패킷"`을 탭 본문 내부 콘텐츠의 제목 및 탭 이모지와 통일되도록 각각 `"[TARGET] 1️⃣ 벤치마킹 분석"`, `"🔍 2️⃣ 자료 조사 결과"`, `"[PACKAGE] 3️⃣ 총괄 기획안"`으로 일치시켜 명칭 불일치를 완벽히 해결했습니다.
- **실행 및 구동 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_23.py`로 갱신 완료했습니다.
### 영향 파트
- **Part 1 (벤치마킹)**: Step 2 3단 분석 엔진 탭 라벨 명칭 통일.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_23.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.18 — 2026-05-23 18:50
### 변경 내용
- **최종본 Lock & GitHub Push 및 수정본 생성 버튼 시스템 구축**:
  - 각 파트(Part 1 ~ Part 8) 하단에 `[🔒 최종본 Lock & GitHub Push]` 및 `[🔓 수정본 생성]` 버튼 2개를 가로 2열 나란히 배치했습니다.
  - **최종본 LOCK**: 클릭 시 현재 세션 데이터를 마크다운 문서로 포맷팅하고 하단 주석에 원시 세션 데이터를 JSON으로 인코딩 주입하여 `00_Obsidian/Studio/Final_Locks/Part[X]_Final_LOCK.md` 경로에 저장하고 `lock_file_readonly()`로 잠근 뒤 깃허브로 백업 Push합니다. (기존 작업 영역 파일은 잠그지 않음)
  - **수정본 생성**: LOCK 파일을 읽어와 `Part[X]_REV[N].md` 파일로 복사(잠금 해제 상태)하고, JSON 메타 주석에서 데이터를 파싱하여 작업 영역(`st.session_state`)에 완벽 복구 로드합니다.
  - **Rembrandt Dark 커스텀 CSS 스타일링**: Lock 버튼은 다크 레드 계열(`#9B1C1C`), 수정본 버튼은 차분한 그레이/앰버 오렌지 계열로 고급스럽게 커스텀 렌더링했습니다.
- **구동/실행 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_18.py`로 갱신 완료했습니다.
### 영향 파트
- **전 파트 (Part 1~8)**: 하단 최종본 Lock & 수정본 생성 통합 관리 기능 추가 및 UI 스타일링 완료.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_18.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.17 — 2026-05-23 16:30
### 변경 내용
- **파트 2 Step 2 '현자의 거울 3단 분석 엔진'의 탭 라벨과 탭 내 제목 100% 일치화**:
  - 파트 2의 Step 2 탭 버튼 라벨 `"[TARGET] 1️⃣ 채널 벤치마킹"`, `"📚 2️⃣ 자료 조사"`, `"[ALCHEMY] 3️⃣ 총괄 기획안"`을 탭 본문 내부 콘텐츠의 제목과 동일하게 각각 `"[TARGET] 1️⃣ 채널 벤치마킹 및 주제 도출"`, `"📚 2️⃣ 옵시디언 융합 리서치"`, `"[ALCHEMY] 3️⃣ 총괄 기획안 생성"`으로 일치시켜 사용자 경험상의 혼선을 해결했습니다.
- **실행 및 구동 스크립트 실행 타겟 일괄 갱신**:
  - `RUN_APP.bat`, `RUN_DEBUG.bat`, `RUN_APP.vbs` 파일들의 Streamlit 실행 대상을 `app_v15_9_17.py`로 갱신 완료했습니다.
### 영향 파트
- **Part 2 (총괄기획)**: Step 2 3단 분석 엔진 탭 라벨 명칭 통일.
- **App Core**: 실행 환경 및 구동 배치/VBS 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_17.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `RUN_APP.vbs`
- `00_History\CHANGELOG.md`

---

## v15.9.16 — 2026-05-23 11:15
### 변경 내용
- **보안 위협 원천 차단 및 소스 코드 정제**:
  - `app_v15_9_15.py` 소스 코드의 `init_session_state` 및 설정창 텍스트 입력창 기본값에 포함되어 있던 제미나이 API Key 하드코딩(`AIzaSyAhLl...`)을 완벽하게 제거하여 공란(`""`)으로 교체했습니다.
- **보안 중요 정보 로컬 격리 시스템 구축 (`local_secrets.json`)**:
  - 민감한 보안 키 목록(`gemini_api_key`, `tavily_api_key`, `youtube_api_key`, `github_token`, `github_pat`)을 기존 `workspace_state.json` 저장 목록에서 완전히 제외 처리했습니다.
  - 중요 키들은 Git 추적 목록에서 배제된 별도의 `local_secrets.json` 파일에 로컬 전용으로 따로 안전하게 격리 저장 및 업데이트되도록 `save_workspace_state()` 함수를 개조했습니다.
  - 앱 구동 시 `workspace_state.json`과 로컬의 `local_secrets.json` 정보를 자동 병합하여 로딩하도록 `load_workspace_state()` 로직을 개선하여 UX 편의성을 100% 유지했습니다.
- **Git 유출 차단 필터 추가**:
  - `.gitignore` 파일에 `local_secrets.json` 필터를 추가하여, 사용자의 수동 작업이나 자동화 프로세스 중 실수가 있더라도 깃허브 원격 저장소에 노출되지 않도록 이중 안전 장치를 걸었습니다.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 Streamlit 실행 대상을 `app_v15_9_16.py`로 갱신 완료했습니다.
### 영향 파트
- **App Core (보안 시스템)**: 로컬 보안 설정 이중화 및 유출 방지 조치 완료.
- **App Core**: 실행 환경 및 구동 배치 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_16.py`
- `workspace_state.json` (기존 API Key 삭제 완료)
- `local_secrets.json` (신규 분리 저장 완료)
- `.gitignore`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.15 — 2026-05-23 10:50
### 변경 내용
- **Part 1 Obsidian 감정 기반 RAG 검색 UI 통합**:
  - Part 1의 기존 낡은 단순 검색 인터페이스를 공통 `render_obsidian_rag_search()` 검색 UI로 전면 교체하여 1~8 전 파트 통일성을 완료했습니다.
  - 이와 동시에 Part 1 `tab_research` 내부에 중복으로 들어있던 검색 UI를 삭제하여 화면을 단일화하고 데이터 흐름 무결성을 확보했습니다.
- **RAG 기본 태그/키워드 전 파트 공통 통일**:
  - 모든 파트(Part 1~8)에 대한 기본 RAG 검색 태그(`DEFAULT_P1_TAGS` ~ `DEFAULT_P8_TAGS`)를 Part 1 기준인 `"고독, 후회, 상실, 관계, 용서, 쇼펜하우어, 성경"`으로 일괄 통일화했습니다.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 Streamlit 실행 대상을 `app_v15_9_15.py`로 갱신 완료했습니다.
### 영향 파트
- **전 파트 (Part 1~8)**: RAG 기본 검색 키워드/태그 통일화 완료.
- **Part 1 (Librarian)**: RAG 검색 UI 통합 및 중복 위젯 정리로 UI 직관성 개선.
- **App Core**: 실행 환경 및 구동 배치 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_15.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

## v15.9.14 — 2026-05-23 10:45
### 변경 내용
- **8개 파트 전체에 공통 Obsidian 감정 기반 RAG 검색 UI 적용 완료**:
  - 기존 Part 1에 탑재되어 있던 `render_obsidian_rag_search()` 공통 검색 UI 및 기능을 Part 2~8 전체에 통일된 접힘 expander (`🔍 RAG 보완 검색 설정 (접기/펼치기)`) 레이아웃으로 확대 적용.
  - 1차 옵시디언 simple_keyword_search 검색과 2차 웹 검색(Gemini/Tavily) 보완 연동을 통해 부족한 철학/심리학/성경 지식을 자동으로 추가 수집.
  - 검색 결과는 양식화된 마크다운으로 생성되어 옵시디언 Studio Vault 경로에 자동 저장 및 읽기 전용 잠금 처리.
- **Part 2~8 AI 생성기에 RAG Context 주입**:
  - Part 2 융합 리서치, Part 3 나레이션 대본 집필, Part 4 C-1 이미지 프롬프트 생성, Part 5 비디오 4단 매핑 조립에 RAG Context를 결합하여 프롬프트 품질 극대화.
- **Part 7 숏폼 후킹 생성 및 Part 8 검수 가이드라인 AI 생성 신규 기능 도입**:
  - Part 7 숏폼 생성 화면에 나레이션 대본 기반 후킹 멘트 및 CTA 자동 도출 AI 블록 신설.
  - Part 8 대시보드 화면에 최종 연출/편집/믹싱 가이드라인 도출 AI 블록 신설.
  - 생성 결과는 옵시디언 백업 마크다운 내용에 포함되어 단일 트랜잭션으로 백업 연동.
- **구동 및 디버그 스크립트 실행 타겟 갱신**:
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 파일의 Streamlit 실행 타겟을 `app_v15_9_14.py`로 갱신 완료.
### 영향 파트
- **전 파트 (Part 1~8)**: RAG 보완 검색 UI 적용 및 AI 생성 루틴 내부 RAG Context 주입 활성화.
- **Part 7, 8**: 후킹 멘트 및 최종 검수 가이드라인 AI 생성 블록 탑재, 마크다운 백업 내용 보강.
- **App Core**: 실행 환경 및 구동 배치 파일 타겟 업데이트.
### 수정 파일
- `app_v15_9_14.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---


## v15.9.11 — 2026-05-23 00:10
### 변경 내용
- **옵시디언 규칙서 옆 수동 실시간 구글 리서치 검색 & 저장 UI 추가**:
  - 최상단 공통 옵시디언 규칙서 텍스트 영역 하단에 직접 검색 키워드를 입력하고 즉시 검색 및 저장을 실행할 수 있는 `🔍 즉석 실시간 구글 리서치 & 저장` 입력 칸 및 `💾 리서치 & 저장` 버튼 UI 탑재.
  - 검색 성공 시 Gemini 2.5 Flash가 실시간 리서치한 자료 요약본 및 출처 링크 목록을 `00_Obsidian/Studio/ResearchMemory/` 하위에 `Manual_Research_[검색어]` 파일명으로 즉각 저장하고 Git Push 연동.
  - `RUN_APP.bat` 및 `RUN_DEBUG.bat` 의 실행 대상 파일을 `app_v15_9_11.py`로 일괄 업데이트.
### 영향 파트
- **App Core**: 상단 공통 옵시디언 규칙서 영역 내 수동 리서치 검색 & 저장 UI 고도화, 구동 배치 스크립트 실행 타겟 변경.
### 수정 파일
- `app_v15_9_11.py`
- `RUN_APP.bat`
- `RUN_DEBUG.bat`
- `00_History\CHANGELOG.md`

---

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
