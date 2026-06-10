# Claude Code 작업 프롬프트 (6pm 리셋 후 사용)

> 아래 명령어를 순서대로 Claude Code 창에 입력합니다.

---

## 1단계: CLAUDE.md 교체

```
C:\SageMirror_Studio_v18\CLAUDE.md 파일을 새로 만든 통합 버전으로 교체해줘.
파일 첨부 자료(/mnt/user-data/uploads/CLAUDE.md)의 내용을 그대로 복사해서
기존 파일을 덮어쓰기.

작업 순서:
1. git tag backup-20260607-claude-md
2. git checkout -b v18.0.25-claude-md-v2
3. 첨부된 CLAUDE.md 내용으로 교체
4. py_compile 불필요 (md 파일)
5. 커밋 메시지: "v18.0.24: CLAUDE.md v2 통합 - 8파트 전체 기획"
6. push
```

---

## 2단계: API 키 영구 저장 기능 구현

```
사이드바에서 API 키 입력 시 secrets.toml에 자동 저장하는 기능 구현:

목표: 사용자가 사이드바에서 API 키를 입력하면
      .streamlit/secrets.toml에 즉시 영구 저장되어
      앱 재시작 후에도 키가 유지되도록 한다.

구현 위치: app.py 사이드바 API 키 입력 부분

핵심 함수 추가 (core/secrets_manager.py 새 파일):
- def save_api_key_to_secrets(key_name, value):
    .streamlit/secrets.toml 파일 읽기
    api_keys 섹션의 해당 키 업데이트
    파일 다시 쓰기

사이드바 API 입력 변경 시 자동 호출
   on_change 콜백으로 저장

기존 코드와 충돌 없도록 백업 후 작업.
py_compile 후 현자 확인.
```

---

## 3단계: 벤치마킹 6개 항목 구현

```
parts/part1_자료수집.py의 run_benchmark() 함수 확장:

현재: 단일 분석 결과만 출력
목표: 6개 항목으로 구조화된 분석

6개 항목:
1. 채널 구조 (업로드주기/시리즈/영상길이)
2. 후킹 기법 (첫5초/30초/오프닝/감정자극)
3. 썸네일 기법 (색상/폰트/클릭유도)
4. 스크립트 구조 (기승전결/철학인용/감정곡선)
5. 태그/키워드 분석
6. 댓글 분석 (⭐⭐⭐ 체험/공감/해결 댓글 추출)

각 항목 결과는 별도 expander로 표시.
6번 댓글 분석 결과는 session_state["p1_comment_insights"]에 저장.

수정: 백업 → 새 브랜치 → py_compile → 확인 → push
```

---

## 4단계: 채널 발굴 시스템 구현

```
우측 SAGE 브레인 패널에 [🔍 채널 발굴] 버튼 추가:

흐름:
1. [🔍 채널 발굴 시작] 버튼 클릭
2. Gemini Flash에 웹 검색 요청:
   "유튜브 심리학/철학 채널 중
    구독자 1만명 이하 + 단일 영상 조회수 10만 이상
    바이럴 지수 상위 TOP 10 찾기"
3. YouTube Data API로 각 채널 검증:
   - 구독자수 확인 (1만 이하)
   - 최근 영상 조회수 (10만 이상)
   - 바이럴 지수 = 조회수/구독자
4. TOP 5 표시 (채널명, 구독자, 최고조회수, 바이럴지수)
5. Gemini에게 분석 요청:
   "이 5개 중 현재 트렌드/키워드/알고리즘에
    가장 적합한 1개 채널 추천 및 사유"
6. [✅ 이 채널로 벤치마킹] 버튼
7. 클릭 시 좌측 벤치마킹 탭 URL에 자동 입력

새 파일: core/channel_finder.py
수정 파일: panel/right_panel.py, parts/part1_자료수집.py

수정 규칙 100% 준수.
```

---

## 5단계: 주제 추천 3대 소스 연동

```
parts/part1_자료수집.py의 generate_topics() 확장:

3대 소스 통합:
소스 1: 댓글 (session_state["p1_comment_insights"])
소스 2: 옵시디언 RAG (기존 연동 유지)
소스 3: Tavily 트렌드 (새로 추가)

Tavily 연동:
- core/tavily_client.py 새 파일
- API 키: secrets.toml의 tavily
- 검색 쿼리: 채널 주제 + 최신 트렌드
- 결과: 인기 키워드 TOP 10

주제 20개 출력 형식 (주제당 6개 항목):
1. 제목
2. 핵심 주제
3. 추천 사유 (어느 소스에서 왔는지 명시)
4. 핵심 키워드 (해시태그 형식)
5. 시청자 예상 반응
6. 시청자 예상 효과

수정 규칙 100% 준수.
```

---

## 6단계: 자료조사 점수화 시스템

```
parts/part1_자료수집.py의 자료조사 탭에 점수화 추가:

18점 만점 평가:
1. 관련성 (0~3점)
2. 출처성 (0~3점)
3. 깊이 (0~3점)
4. 균형 (성경+철학+심리+감정, 0~3점)
5. 제작 활용성 (0~3점)
6. 최신성 (0~3점)

총점 판정:
15~18점: 충분 (Part 2 진행 가능)
10~14점: 보완 필요 (외부 리서치 권장)
0~9점: 부족 (필수 보완)

부족 시:
- Gemini 리서치 질문 자동 생성
- Tavily 검색 키워드 자동 생성
- 수동 리서치 입력창 표시

새 파일: core/knowledge_router.py
수정 규칙 100% 준수.
```

---

## 진행 순서 (총 6단계)

```
Day 1 (오늘):
  1. CLAUDE.md 교체
  2. API 키 영구 저장

Day 2:
  3. 벤치마킹 6개 항목
  4. 채널 발굴 시스템

Day 3:
  5. 주제 추천 3대 소스
  6. 자료조사 점수화

이후:
  Part 2 ~ Part 8 구현 (각 단계별 진행)
```

---

## 작업 원칙 (모든 단계 공통)

```
1. git tag backup-날짜
2. git checkout -b v18.x.xx-작업명
3. 복사본 브랜치에서만 작업
4. py_compile 검증
5. 현자 확인 대기
6. merge + push
7. 덮어쓰기 절대 금지
```
