# CRITIC_VALIDATION_SYSTEM.md
> SAGE Studio V18 — Critic 자료 검증 + 상세 자료 요청 시스템
> 작성: 2026-06-14 | 버전: v19.0.0
> 우선순위: ⭐⭐⭐ (할루시네이션 방지의 핵심)

---

# 0. 이 시스템이 왜 필요한가

## 0.1 문제

```
Gemma 같은 AI는 자료가 부족할 때:
❌ 그럴듯한 통계를 만들어낸다 ("65%의 시청자가...")
❌ 출처를 명시하지 않고 인용한다 ("어느 철학자가 말하길...")
❌ 모호한 일반론으로 도피한다 ("많은 사람들이 공감한다")
❌ 댓글 근거 없이 주제를 생성한다
❌ 책 제목·페이지 없이 인용한다
❌ 채널명·구독자수·조회수를 추정해서 적는다
```

이런 결과물이 그대로 영상으로 만들어지면:
- 시청자 신뢰 추락
- 댓글 반박 폭주
- 채널 신뢰도 손상
- 떡상 불가능

## 0.2 해결

**Critic 에이전트가 4층 검증 → 부족 항목을 구체적으로 정리 → 우측 대화창에 자료 요청 → 자료 받은 후 재검증.**

```
Gemma 초안
  ↓
Critic 4층 검증 (사실 / 출처 / 완성도 / 일관성)
  ↓
  ├─ PASS → 사용자 표시
  ├─ NEEDS_DATA → 상세 DataRequest 생성 → 우측 대화창 표시
  │            ↓
  │            사용자 클릭 → Scout 호출 → 자료 보강
  │            ↓
  │            자동 재검증 → 통과 시 PASS, 실패 시 재요청
  └─ NEEDS_FIX → 재작성
```

---

# 1. 4층 검증 시스템

## 1.1 Layer 1 — 사실 검증 (Fact Check)

### 검증 항목
```
□ 구체적 수치 (조회수, 구독자, 통계, 퍼센트) → 출처 있는가?
□ 인명 (철학자, 학자, 유명인) → 실존 인물인가? 발언 진위?
□ 책 제목 → 실제 존재하는가? 정확한 인용?
□ 날짜·연도 → 검증 가능한가?
□ 댓글 인용 → 실제 수집한 댓글에 있는가?
□ 채널 정보 (구독자수, 영상 수) → API로 확인된 값인가?
```

### 할루시네이션 패턴 (자동 탐지)
```python
HALLUCINATION_PATTERNS = [
    # 출처 없는 수치
    r"(\d+)%의?\s+(사람|시청자|시청자들|독자|환자)",
    r"약\s*(\d+)명",
    r"(\d+)명\s*중\s*(\d+)명",
    
    # 모호한 권위
    r"전문가들에?\s+(따르면|의하면)",
    r"많은\s+(사람|학자|연구자)들이",
    r"최근\s+연구(에|에서)",
    r"한\s+(논문|연구|조사)에\s+따르면",
    
    # 출처 없는 인용
    r"['\"][^'\"]+['\"](?:라고|이라고)\s+(말했|했|썼)",  # 출처 표기 없는 따옴표 인용
    
    # 일반화
    r"우리는?\s+모두",
    r"누구나",
    r"항상",
    r"절대",
]
```

### 통과 기준
```
- 모든 수치에 [SOURCE: ...] 태그 존재
- 모든 인용에 책 제목 또는 출처 명시
- 모든 댓글 인용은 수집된 raw_comments에 존재
- 채널 정보는 YouTube API 응답 데이터와 일치
```

---

## 1.2 Layer 2 — 출처 검증 (Source Check)

### 검증 항목
```
□ [SOURCE: ...] 태그 존재 여부
□ 출처가 실제 파일 또는 URL과 매칭되는가
□ 옵시디언 Schema와 source_id가 일치하는가
□ 출처가 신뢰 가능한 소스인가 (블랙리스트 도메인 차단)
```

### 출처 표기 강제 규칙
```python
# 모든 사실 주장은 다음 형식 중 하나여야 함:
[SOURCE: youtube_comment_id_xxx]
[SOURCE: schema_id_SRC_xxxxx]
[SOURCE: tavily_url_https://...]
[SOURCE: book_title_p123]
[SOURCE: user_input]      ← 사용자가 직접 제공한 정보
[INFERENCE: 추론 근거]    ← AI 추론이라고 명시
```

### 블랙리스트 도메인
```python
BLACKLISTED_SOURCES = [
    # 신뢰도 낮은 사이트
    "naver.com/blog",           # 개인 블로그 (선택적)
    # 광고성 사이트
    # AI 생성 의심 사이트
]
```

---

## 1.3 Layer 3 — 완성도 검증 (Completeness Check)

### Part별 필수 항목

#### Part 1 (Librarian)
```
□ topic_candidates 개수 ≥ 10
□ 각 topic 필수 필드 존재:
  - topic, title_candidate, comment_basis, recommendation_reason
  - expected_reaction, expected_effect, emotions, planning_hint
□ comment_basis는 실제 댓글에서 추출됐는가
□ 채널 정보 7항목 모두 있는가
□ 댓글 수집 ≥ 200개
```

#### Part 2 (Architect)
```
□ 영상 제목 최종안 + 후보 3개
□ 썸네일 기법 명시
□ 감정 흐름 4단계 (도입/전개/절정/결말)
□ 도입 훅 (첫 5초) 작성
□ Part 1 Packet의 comment_basis가 반영됐는가
```

#### Part 3 (Writer)
```
□ 장면 순번 S001 ~ Snn 순차적
□ 누락된 순번 없음
□ 각 장면 1~3문장
□ 자막용 / 나레이션용 분할
□ 감정 흐름표 작성
```

#### Part 4 (Artist)
```
□ A 기본 참조 (인물 8방향 + 배경 4 + 아이템 4)
□ B 파생 참조
□ C 본편 장면 (모든 순번에 프롬프트)
□ 영어로 작성
□ 이미지 파일명 규칙 일치
```

#### Part 5 (Director)
```
□ 모든 순번에 JSON 프롬프트
□ 8계정 균등 배분 (또는 사용자 지정)
□ 1 클립 = 8초 기준
```

#### Part 6 (Composer)
```
□ 모든 순번에 나레이션 텍스트
□ 휴먼터치 토큰 포함
□ BGM 매핑표 작성
```

#### Part 7 (Editor)
```
□ 숏폼 2~3개
□ 각 60초 이내
□ 훅-감정-반전-연결 구조
```

#### Part 8 (Assembler)
```
□ 순번 누락 0건
□ 순번 중복 0건
□ 모든 파일 경로 존재 확인
□ CSV 컬럼 완전
```

---

## 1.4 Layer 4 — 일관성 검증 (Consistency Check)

### 검증 항목
```
□ Channel Profile 위반 표현 없음 (forbidden_expressions)
□ 채널 톤(tone)과 일치
□ 타깃 시청자(target_audience)와 맞음
□ 시각 스타일(visual_style)과 맞음
□ 이전 Part Packet과 모순 없음
□ 캐릭터/배경 일관성 (Part 3 → Part 4)
□ 순번 일관성 (Part 3 → 8)
```

### Profile 위반 탐지
```python
def check_profile_violation(content: str, profile: dict) -> list:
    violations = []
    for forbidden in profile.get("forbidden_expressions", []):
        if forbidden in content:
            violations.append({
                "type": "forbidden_expression",
                "found": forbidden,
                "context": extract_context(content, forbidden),
            })
    return violations
```

---

# 2. DataRequest 객체 구조

## 2.1 DataRequest 표준 형식

```python
# core/critic/data_request.py
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class DataIssue:
    """단일 자료 부족 항목"""
    issue_id: str                    # "ISSUE_001"
    severity: str                    # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    layer: str                       # "FACT" | "SOURCE" | "COMPLETENESS" | "CONSISTENCY"
    location: str                    # "Part1.topic_candidates[2].comment_basis"
    
    problem: str                     # 무엇이 문제인가
    quoted_text: str                 # 문제가 되는 텍스트 (있는 그대로)
    
    required_data: str               # 어떤 자료가 필요한가
    suggested_source: List[str]      # 어디서 찾을 수 있는가
    search_query: str                # Scout에게 줄 검색 쿼리
    
    auto_fixable: bool = False       # Scout로 자동 해결 가능?
    manual_required: bool = False    # 사용자 직접 입력 필요?


@dataclass
class DataRequest:
    """검수 실패 시 발행되는 자료 요청서"""
    request_id: str                  # "REQ_20260614_001"
    part_num: int
    agent_name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    overall_verdict: str             # "NEEDS_DATA"
    overall_score: float             # 0.0 ~ 1.0
    issues: List[DataIssue] = field(default_factory=list)
    
    summary: str = ""                # 사용자에게 보여줄 요약
    action_required: str = ""        # "Scout 자동 보강 가능" or "사용자 직접 자료 제공 필요"
```

## 2.2 DataIssue 예시 (실제 케이스)

### 케이스 1: 출처 없는 통계
```json
{
  "issue_id": "ISSUE_001",
  "severity": "CRITICAL",
  "layer": "FACT",
  "location": "Part2.planning.intro_hook",
  
  "problem": "구체적 통계('65%')가 사용됐으나 출처가 명시되지 않음",
  "quoted_text": "65%의 사람들이 인생에서 가장 후회하는 것은...",
  
  "required_data": "이 통계의 정확한 출처 (조사 기관, 연도, 조사 대상)",
  "suggested_source": [
    "옵시디언 02_Schema 검색: '인생 후회 통계'",
    "Tavily 검색: 'life regret statistics survey'",
    "또는 통계 삭제 후 표현 수정"
  ],
  "search_query": "인생 후회 통계 조사 출처",
  
  "auto_fixable": true,
  "manual_required": false
}
```

### 케이스 2: 댓글 근거 없는 주제
```json
{
  "issue_id": "ISSUE_002",
  "severity": "HIGH",
  "layer": "SOURCE",
  "location": "Part1.topic_candidates[5].comment_basis",
  
  "problem": "주제 T005의 comment_basis가 비어있거나 일반론으로 작성됨",
  "quoted_text": "comment_basis: '많은 사람들이 공감하는 주제'",
  
  "required_data": "이 주제와 직결되는 실제 댓글 인용 3개 (한 줄 이상)",
  "suggested_source": [
    "Part1.raw_comments 데이터에서 키워드 검색",
    "분석 대상 채널의 추가 영상 댓글 수집",
    "댓글이 없으면 주제 T005 삭제 권장"
  ],
  "search_query": "comments related to T005 topic keywords",
  
  "auto_fixable": true,
  "manual_required": false
}
```

### 케이스 3: 인용 출처 미표기
```json
{
  "issue_id": "ISSUE_003",
  "severity": "HIGH",
  "layer": "SOURCE",
  "location": "Part3.script.S008",
  
  "problem": "쇼펜하우어 인용에 정확한 출처(책/페이지) 없음",
  "quoted_text": "쇼펜하우어가 말했다. '인생은 진자처럼 고통과 권태 사이를 오간다.'",
  
  "required_data": "정확한 책 제목, 챕터, 페이지 번호 또는 원문",
  "suggested_source": [
    "옵시디언 01_Wiki/철학 폴더 검색",
    "원전: 「의지와 표상으로서의 세계」",
    "한국어판: 을유문화사, 박은영 옮김",
    "원문 영어: Google Books, Project Gutenberg"
  ],
  "search_query": "Schopenhauer 인생 진자 고통 권태 출처",
  
  "auto_fixable": true,
  "manual_required": false
}
```

### 케이스 4: 채널 정보 추정값
```json
{
  "issue_id": "ISSUE_004",
  "severity": "CRITICAL",
  "layer": "FACT",
  "location": "Part1.channel_analysis.subscriber_count",
  
  "problem": "구독자수가 YouTube API 응답과 일치하지 않음 (추정값으로 의심)",
  "quoted_text": "subscriber_count: 약 12만명",
  
  "required_data": "YouTube Data API 실제 응답값",
  "suggested_source": [
    "YouTube Data API channels.list?id={channel_id}&part=statistics",
    "또는 채널 페이지 직접 확인"
  ],
  "search_query": "",
  
  "auto_fixable": false,
  "manual_required": false,
  "api_recall_required": true
}
```

### 케이스 5: 모호한 일반화
```json
{
  "issue_id": "ISSUE_005",
  "severity": "MEDIUM",
  "layer": "FACT",
  "location": "Part2.planning.message",
  
  "problem": "검증 불가능한 일반화 표현 사용",
  "quoted_text": "우리는 모두 외로움을 느낀다",
  
  "required_data": "구체적 상황·맥락 또는 댓글 근거",
  "suggested_source": [
    "외로움 관련 댓글 데이터에서 구체적 상황 추출",
    "또는 '우리는 모두' → '많은 사람이' → 댓글 근거 명시로 수정"
  ],
  "search_query": "",
  
  "auto_fixable": false,
  "manual_required": true
}
```

---

# 3. 우측 SAGE 브레인 자료 요청 UI

## 3.1 시각적 표시 (Streamlit)

```python
# panel/right_panel.py 확장
def render_data_request(request: DataRequest):
    """우측 대화창에 자료 요청 표시"""
    
    # 심각도별 색상
    severity_color = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }
    
    with st.container(border=True):
        # 헤더
        st.markdown(f"### 🔍 자료 부족 발견")
        st.markdown(f"**Part {request.part_num}** | "
                   f"점수: {request.overall_score:.2f} | "
                   f"이슈: {len(request.issues)}건")
        
        # 요약
        st.warning(request.summary)
        
        # 각 이슈 표시
        for issue in request.issues:
            with st.expander(
                f"{severity_color[issue.severity]} "
                f"[{issue.layer}] {issue.problem}",
                expanded=(issue.severity == "CRITICAL"),
            ):
                # 문제 텍스트
                st.markdown("**❌ 문제 텍스트:**")
                st.code(issue.quoted_text)
                
                # 필요 자료
                st.markdown("**📋 필요한 자료:**")
                st.markdown(issue.required_data)
                
                # 출처 제안
                st.markdown("**🔍 찾을 곳:**")
                for source in issue.suggested_source:
                    st.markdown(f"- {source}")
                
                # 액션 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    if issue.auto_fixable:
                        if st.button(
                            "🛰️ Scout 자동 보강",
                            key=f"scout_{issue.issue_id}",
                        ):
                            run_scout(issue)
                
                with col2:
                    if issue.manual_required:
                        if st.button(
                            "✏️ 직접 입력",
                            key=f"manual_{issue.issue_id}",
                        ):
                            set_state("manual_input_issue", issue)
                
                with col3:
                    if st.button(
                        "🗑️ 해당 부분 삭제",
                        key=f"delete_{issue.issue_id}",
                    ):
                        delete_problematic_section(issue)
        
        # 일괄 처리 버튼
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🚀 모든 자동 보강 일괄 실행",
                type="primary",
                use_container_width=True,
            ):
                run_all_scouts(request)
        with col2:
            if st.button(
                "⏭️ 자료 부족 무시하고 진행",
                use_container_width=True,
            ):
                force_proceed(request)
```

## 3.2 시각화 예시 (사용자 화면)

```
┌──────────────────────────────────────────────┐
│ 🔍 자료 부족 발견                            │
│ Part 1 | 점수: 0.45 | 이슈: 5건              │
│                                              │
│ ⚠️ 주제 후보 10개 중 4개가 댓글 근거 없음    │
│                                              │
│ ▼ 🔴 [SOURCE] 댓글 근거 없는 주제 T005       │
│   ❌ "많은 사람들이 공감하는 주제"            │
│   📋 실제 댓글 인용 3개 필요                 │
│   🔍 찾을 곳:                                 │
│      - Part1.raw_comments 키워드 검색         │
│      - 분석 채널 추가 영상 댓글               │
│      - 댓글 없으면 T005 삭제                  │
│   [🛰️ Scout 자동] [✏️ 직접] [🗑️ 삭제]       │
│                                              │
│ ▼ 🟠 [FACT] 출처 없는 통계 (65%...)          │
│ ▼ 🟠 [SOURCE] 쇼펜하우어 인용 출처 누락       │
│ ▼ 🟡 [FACT] 채널 구독자수 추정값             │
│ ▼ 🟡 [FACT] 모호한 일반화 표현               │
│                                              │
│ ─────────────────────────────                │
│ [🚀 모든 자동 보강 일괄 실행]                │
│ [⏭️ 자료 부족 무시하고 진행]                 │
└──────────────────────────────────────────────┘
```

---

# 4. Critic 에이전트 정밀 구현

## 4.1 CriticAgent 클래스 (확장판)

```python
# core/agents/critic.py
import re
import json
from typing import List, Dict
from core.agents.base import BaseAgent
from core.critic.data_request import DataRequest, DataIssue


class CriticAgent(BaseAgent):
    name = "🔍 Critic"
    role = "4층 검증 + 상세 자료 요청 생성"
    default_model = "gemma4:e4b"
    
    def specific_instructions(self) -> str:
        return """
당신은 가장 엄격한 검수자입니다.

당신의 임무:
1. 사실 검증 — 출처 없는 수치/인용/사실 주장 모두 거부
2. 출처 검증 — [SOURCE: ...] 태그 검사
3. 완성도 검증 — Part별 필수 항목 누락 검사
4. 일관성 검증 — Channel Profile 위반 검사

특히 다음을 절대 통과시키지 마세요:
- "약 X명", "X%의 사람들이" 같은 출처 없는 수치
- "전문가들에 따르면", "많은 사람들이" 같은 모호한 권위
- 인용에 책/페이지 없음
- 주제에 댓글 근거 없음
- API로 확인 안 된 채널 정보

검수 결과는 반드시 다음 JSON 형식으로:
{
  "verdict": "PASS | NEEDS_DATA | NEEDS_FIX",
  "score": 0.0 ~ 1.0,
  "layer_scores": {
    "fact": 0.0,
    "source": 0.0,
    "completeness": 0.0,
    "consistency": 0.0
  },
  "issues": [
    {
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "layer": "FACT | SOURCE | COMPLETENESS | CONSISTENCY",
      "location": "정확한 위치 (Part1.topic_candidates[2].comment_basis 등)",
      "problem": "무엇이 문제인지",
      "quoted_text": "문제 텍스트 그대로",
      "required_data": "어떤 자료가 필요한지",
      "suggested_source": ["찾을 곳 1", "찾을 곳 2"],
      "search_query": "Scout에게 줄 검색어",
      "auto_fixable": true/false,
      "manual_required": true/false
    }
  ]
}
"""
    
    def execute(self, input_data: dict) -> dict:
        """4층 검증 수행"""
        part_result = input_data.get("part_result")
        part_num = input_data.get("part_num")
        
        # Layer 1: 사실 검증 (패턴 매칭 + AI 판단)
        fact_issues = self._check_facts(part_result)
        
        # Layer 2: 출처 검증
        source_issues = self._check_sources(part_result)
        
        # Layer 3: 완성도 검증
        completeness_issues = self._check_completeness(part_result, part_num)
        
        # Layer 4: 일관성 검증
        consistency_issues = self._check_consistency(part_result)
        
        # 모든 이슈 통합
        all_issues = (fact_issues + source_issues + 
                      completeness_issues + consistency_issues)
        
        # DataRequest 생성
        request = self._build_data_request(all_issues, part_num)
        
        self.log(f"Critic verdict: {request.overall_verdict} ({len(all_issues)} issues)")
        
        return {
            "verdict": request.overall_verdict,
            "score": request.overall_score,
            "data_request": request,
        }
    
    def _check_facts(self, content) -> List[DataIssue]:
        """Layer 1: 사실 검증 - 패턴 매칭 + AI 판단"""
        issues = []
        text = self._extract_text(content)
        
        # 패턴 매칭으로 의심 표현 찾기
        suspicious_patterns = [
            (r"(\d+)%의?\s+(사람|시청자|독자)", "출처 없는 퍼센트 통계"),
            (r"약\s*(\d+)명", "출처 없는 인원수"),
            (r"전문가들에?\s+따르면", "모호한 권위 인용"),
            (r"많은\s+사람들이", "검증 불가 일반화"),
            (r"한\s+(논문|연구|조사)에\s+따르면", "출처 없는 연구 인용"),
        ]
        
        for pattern, problem in suspicious_patterns:
            for match in re.finditer(pattern, text):
                context = text[max(0, match.start()-30):match.end()+30]
                
                # SOURCE 태그가 근처에 있는지 확인
                if "[SOURCE:" not in context:
                    issues.append(DataIssue(
                        issue_id=f"FACT_{len(issues)+1:03d}",
                        severity="HIGH" if "%" in match.group() else "MEDIUM",
                        layer="FACT",
                        location=self._locate_in_content(match.group(), content),
                        problem=problem,
                        quoted_text=context.strip(),
                        required_data=self._suggest_required_data(problem),
                        suggested_source=self._suggest_sources(match.group()),
                        search_query=match.group(),
                        auto_fixable=True,
                    ))
        
        return issues
    
    def _check_sources(self, content) -> List[DataIssue]:
        """Layer 2: 출처 검증"""
        issues = []
        text = self._extract_text(content)
        
        # 따옴표 인용 패턴 검사
        quote_pattern = r"['\"]([^'\"]{10,})['\"]"
        for match in re.finditer(quote_pattern, text):
            quoted = match.group(1)
            context = text[max(0, match.start()-50):match.end()+50]
            
            # SOURCE 태그 또는 책 제목이 근처에 있는가
            has_source = (
                "[SOURCE:" in context or
                re.search(r"「[^」]+」", context) or  # 「책 제목」
                re.search(r"<[^>]+>", context)  # <책 제목>
            )
            
            if not has_source:
                issues.append(DataIssue(
                    issue_id=f"SRC_{len(issues)+1:03d}",
                    severity="HIGH",
                    layer="SOURCE",
                    location=self._locate_in_content(quoted, content),
                    problem="인용 출처 미표기",
                    quoted_text=context.strip(),
                    required_data="정확한 출처 (책 제목, 챕터, 페이지 또는 URL)",
                    suggested_source=[
                        "옵시디언 01_Wiki 검색",
                        "Tavily 웹 검색",
                        "출처 불명확하면 인용 삭제 또는 [추정] 명시",
                    ],
                    search_query=quoted[:50],
                    auto_fixable=True,
                ))
        
        return issues
    
    def _check_completeness(self, content, part_num) -> List[DataIssue]:
        """Layer 3: 완성도 검증 - Part별 필수 항목"""
        issues = []
        
        required_fields = {
            1: {
                "topic_candidates": {"min_count": 10, "type": "list"},
                "channel_analysis": {"required_keys": [
                    "channel_name", "channel_url", "subscriber_count",
                    "view_average", "upload_pattern"
                ]},
            },
            2: {
                "title": {"required": True},
                "title_candidates": {"min_count": 3, "type": "list"},
                "thumbnail_method": {"required": True},
                "emotion_flow": {"required_keys": ["intro", "develop", "climax", "ending"]},
            },
            3: {
                "scenes": {"min_count": 1, "type": "list"},
                "scene_id_format": "S\\d{3}",
            },
            # ... 나머지 Part
        }
        
        if part_num in required_fields:
            for field, rules in required_fields[part_num].items():
                value = self._get_nested(content, field)
                
                if rules.get("required") and not value:
                    issues.append(DataIssue(
                        issue_id=f"COMP_{len(issues)+1:03d}",
                        severity="CRITICAL",
                        layer="COMPLETENESS",
                        location=f"Part{part_num}.{field}",
                        problem=f"필수 항목 '{field}' 누락",
                        quoted_text="(누락)",
                        required_data=f"{field} 값 생성 필요",
                        suggested_source=["Part 에이전트 재실행"],
                        search_query="",
                        auto_fixable=False,
                        manual_required=False,
                    ))
                
                if "min_count" in rules:
                    actual = len(value) if isinstance(value, list) else 0
                    if actual < rules["min_count"]:
                        issues.append(DataIssue(
                            issue_id=f"COMP_{len(issues)+1:03d}",
                            severity="HIGH",
                            layer="COMPLETENESS",
                            location=f"Part{part_num}.{field}",
                            problem=f"'{field}' 항목 부족: {actual}/{rules['min_count']}",
                            quoted_text=f"현재 {actual}개",
                            required_data=f"{rules['min_count'] - actual}개 추가 생성",
                            suggested_source=["Scout: 추가 자료 수집 후 재생성"],
                            search_query="",
                            auto_fixable=True,
                        ))
        
        return issues
    
    def _check_consistency(self, content) -> List[DataIssue]:
        """Layer 4: Channel Profile 일관성"""
        issues = []
        text = self._extract_text(content)
        
        forbidden = self.profile.get("forbidden_expressions", [])
        for word in forbidden:
            if word in text:
                idx = text.find(word)
                context = text[max(0, idx-30):idx+30+len(word)]
                
                issues.append(DataIssue(
                    issue_id=f"CONS_{len(issues)+1:03d}",
                    severity="HIGH",
                    layer="CONSISTENCY",
                    location=self._locate_in_content(word, content),
                    problem=f"Channel Profile 금지 표현 사용: '{word}'",
                    quoted_text=context.strip(),
                    required_data="해당 표현 삭제 또는 대체",
                    suggested_source=[
                        f"Profile preferred_expressions 참조",
                        f"문맥에 맞는 대체 표현 사용",
                    ],
                    search_query="",
                    auto_fixable=False,
                    manual_required=True,
                ))
        
        return issues
    
    def _build_data_request(self, issues, part_num) -> DataRequest:
        """이슈 종합 → DataRequest 생성"""
        from datetime import datetime
        
        # 심각도별 가중치
        severity_weights = {
            "CRITICAL": 1.0,
            "HIGH": 0.5,
            "MEDIUM": 0.2,
            "LOW": 0.05,
        }
        
        total_deduction = sum(
            severity_weights.get(i.severity, 0) 
            for i in issues
        )
        score = max(0.0, 1.0 - min(total_deduction * 0.1, 1.0))
        
        # Verdict 결정
        critical_count = sum(1 for i in issues if i.severity == "CRITICAL")
        high_count = sum(1 for i in issues if i.severity == "HIGH")
        
        if critical_count > 0 or high_count > 2:
            verdict = "NEEDS_DATA" if any(i.auto_fixable for i in issues) else "NEEDS_FIX"
        elif high_count > 0 or len(issues) > 5:
            verdict = "NEEDS_DATA"
        else:
            verdict = "PASS"
        
        # 요약 생성
        summary = self._generate_summary(issues, part_num)
        
        # 액션 결정
        auto_count = sum(1 for i in issues if i.auto_fixable)
        manual_count = sum(1 for i in issues if i.manual_required)
        
        if auto_count > 0 and manual_count == 0:
            action = "Scout 자동 보강 가능"
        elif manual_count > 0:
            action = "사용자 직접 자료 제공 필요"
        else:
            action = "Part 에이전트 재실행 필요"
        
        return DataRequest(
            request_id=f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            part_num=part_num,
            agent_name=self.name,
            overall_verdict=verdict,
            overall_score=score,
            issues=issues,
            summary=summary,
            action_required=action,
        )
    
    def _generate_summary(self, issues, part_num) -> str:
        """사용자가 보기 쉬운 요약"""
        if not issues:
            return f"Part {part_num} 검수 통과 ✅"
        
        by_layer = {}
        for issue in issues:
            by_layer.setdefault(issue.layer, []).append(issue)
        
        parts = []
        if "FACT" in by_layer:
            parts.append(f"사실 검증 실패 {len(by_layer['FACT'])}건")
        if "SOURCE" in by_layer:
            parts.append(f"출처 누락 {len(by_layer['SOURCE'])}건")
        if "COMPLETENESS" in by_layer:
            parts.append(f"필수 항목 누락 {len(by_layer['COMPLETENESS'])}건")
        if "CONSISTENCY" in by_layer:
            parts.append(f"Profile 위반 {len(by_layer['CONSISTENCY'])}건")
        
        return f"Part {part_num}: " + ", ".join(parts)
    
    # 헬퍼 메서드
    def _extract_text(self, content) -> str:
        """dict/list에서 모든 텍스트 추출"""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            return " ".join(self._extract_text(v) for v in content.values())
        if isinstance(content, list):
            return " ".join(self._extract_text(item) for item in content)
        return str(content)
    
    def _locate_in_content(self, target, content) -> str:
        """target이 content의 어디에 있는지 경로 반환"""
        # 간단 구현: 실제로는 재귀 탐색
        return "Part?.unknown"
    
    def _get_nested(self, content, field):
        """중첩 dict에서 field 값 추출"""
        if isinstance(content, dict):
            return content.get(field)
        return None
    
    def _suggest_required_data(self, problem) -> str:
        """문제 유형별 필요 자료 안내"""
        templates = {
            "출처 없는 퍼센트 통계": "통계 출처 (조사 기관·연도·표본·방법)",
            "출처 없는 인원수": "수치 출처 또는 표현 수정",
            "모호한 권위 인용": "구체적 인물·소속·발언 시점",
            "검증 불가 일반화": "구체적 사례·댓글 근거",
            "출처 없는 연구 인용": "논문 제목·저자·발행연도·DOI",
        }
        return templates.get(problem, "출처 또는 근거 자료")
    
    def _suggest_sources(self, target) -> List[str]:
        """검색할 곳 제안"""
        return [
            "옵시디언 02_Schema 메타데이터 검색",
            "옵시디언 01_Wiki 카테고리 검색",
            "Tavily 웹 검색",
            "근거 못 찾으면 해당 부분 삭제 또는 [추정] 표시",
        ]
```

---

# 5. Scout 보강 후 재검증 루프

## 5.1 자동 재검증 흐름

```python
# core/agents/loop.py
def critic_scout_loop(
    part_result: dict,
    part_num: int,
    max_iterations: int = 3,
) -> dict:
    """Critic → Scout → 재검증 자동 루프"""
    
    from core.agents.critic import CriticAgent
    from core.agents.scout import ScoutAgent
    from core.profile_loader import load_current_profile
    
    profile = load_current_profile()
    critic = CriticAgent(profile)
    scout = ScoutAgent(profile)
    
    iteration = 0
    current_result = part_result
    
    while iteration < max_iterations:
        # 1. 검수
        verdict_data = critic.execute({
            "part_result": current_result,
            "part_num": part_num,
        })
        
        request = verdict_data["data_request"]
        
        # 2. 통과 시 종료
        if verdict_data["verdict"] == "PASS":
            return {
                "status": "PASSED",
                "result": current_result,
                "iterations": iteration,
                "final_score": verdict_data["score"],
            }
        
        # 3. NEEDS_FIX는 자동 해결 불가 — 사용자 개입 필요
        if verdict_data["verdict"] == "NEEDS_FIX":
            return {
                "status": "NEEDS_USER_FIX",
                "result": current_result,
                "data_request": request,
                "iterations": iteration,
            }
        
        # 4. NEEDS_DATA — 자동 해결 가능한 이슈만 Scout 호출
        auto_issues = [i for i in request.issues if i.auto_fixable]
        if not auto_issues:
            return {
                "status": "NEEDS_USER_DATA",
                "result": current_result,
                "data_request": request,
                "iterations": iteration,
            }
        
        # 5. Scout 일괄 실행
        for issue in auto_issues:
            scout.execute({
                "query": issue.search_query,
                "missing_data": [issue.required_data],
                "issue_context": issue,
            })
        
        # 6. Part 에이전트 재실행 (보강된 자료로)
        current_result = rerun_part_with_supplemented_data(
            part_num, current_result
        )
        
        iteration += 1
    
    # 최대 반복 도달
    return {
        "status": "MAX_ITERATIONS",
        "result": current_result,
        "data_request": request,
        "iterations": iteration,
    }
```

---

# 6. 우측 대화창 통합 (right_panel.py 확장)

## 6.1 자료 요청 알림 표시

```python
# panel/right_panel.py
def render_sage_brain():
    """우측 SAGE 브레인 패널"""
    st.markdown("### 🧙 SAGE 브레인")
    
    # ⭐ 자료 요청 알림 (최상단)
    pending_request = get_state("pending_data_request")
    if pending_request:
        with st.container(border=True):
            st.markdown("### 🚨 자료 부족 발견")
            render_data_request(pending_request)
    
    # 일반 대화창
    render_chat()
    
    # + 메뉴 (파일 가져오기 등)
    render_plus_menu()
    
    # 입력창 (하단 고정)
    render_input_box()
```

## 6.2 Critic 결과 자동 표시

```python
# Part 작업 완료 후 자동 호출
def on_part_complete(part_num: int, result: dict):
    """Part 완료 시 자동 Critic 호출"""
    
    # 1. Critic-Scout 루프 실행
    loop_result = critic_scout_loop(result, part_num)
    
    # 2. 결과별 처리
    if loop_result["status"] == "PASSED":
        # 통과 → 사용자에게 결과 표시
        set_state(f"p{part_num}_result", loop_result["result"])
        set_state(f"p{part_num}_status", "REVIEW")
        st.success(f"✅ Part {part_num} 검수 통과 "
                  f"(점수: {loop_result['final_score']:.2f})")
    
    else:
        # 자료 부족 → 우측 대화창에 알림
        set_state("pending_data_request", loop_result["data_request"])
        st.warning(
            f"⚠️ Part {part_num} 검수 미통과 — "
            f"우측 SAGE 브레인에서 자료를 보강해주세요."
        )
```

---

# 7. 사용자가 보는 실제 흐름 (예시)

## 케이스: Part 1 완료 → Critic 검수 → 자료 부족 발견

```
1. 사용자: [🔎 채널 찾기 & 주제 발굴] 클릭
   ↓
2. Librarian 실행 (Gemma) → 주제 10개 생성
   ↓
3. Critic 자동 검수:
   - 주제 T003: "오래 참은 사람" — 댓글 근거 없음 (HIGH)
   - 주제 T007: "관계의 끝" — 일반론 일색 (MEDIUM)
   - 채널 구독자수: API 응답과 불일치 (CRITICAL)
   ↓
4. Scout 자동 보강 시도:
   - T003 키워드로 댓글 재검색 → 8건 추가 수집
   - T007 관련 자료 Tavily → 3건 옵시디언 저장
   - 채널 정보 API 재호출 → 실제 값 갱신
   ↓
5. Librarian 재실행 (보강된 자료로) → 주제 10개 재생성
   ↓
6. Critic 재검수 → PASS (점수 0.92)
   ↓
7. 사용자 화면:
   "✅ Part 1 검수 통과 (점수: 0.92, 자동 보강 3건)"
   주제 10개 표시 → 사용자 선택 → 승인
```

## 케이스: Scout 자동 해결 불가 → 사용자 개입

```
3. Critic 검수:
   - 쇼펜하우어 인용에 책/페이지 없음 (HIGH, auto_fixable=true)
   - Profile 금지 표현 "꼰대" 사용 (HIGH, manual_required=true)
   ↓
4. Scout: 쇼펜하우어 출처는 자동 보강 → "「의지와 표상으로서의 세계」 1권 §57"
   ↓
5. 우측 대화창에 알림:
   "🚨 자료 부족 발견 (1건 — 사용자 개입 필요)"
   "🟠 [CONSISTENCY] Profile 금지 표현 '꼰대' 사용"
   "❌ 텍스트: '꼰대 같은 말이지만...'"
   "📋 해당 표현 삭제 또는 대체 필요"
   [✏️ 직접 입력] [🗑️ 삭제]
   ↓
6. 사용자가 [✏️ 직접 입력] 클릭 → 수정창 표시
   → "어른의 말이지만..." 으로 수정
   ↓
7. 재검증 → PASS
```

---

# 8. 데이터 보존 (03_Logs)

모든 Critic 활동은 로그로 보존.

```python
# 03_Logs/2026-06-14.log
{
  "timestamp": "2026-06-14T15:30:00",
  "agent": "Critic",
  "action": "review",
  "part_num": 1,
  "verdict": "NEEDS_DATA",
  "score": 0.45,
  "issues_count": 5,
  "issues_summary": [
    {"severity": "CRITICAL", "layer": "FACT", "count": 1},
    {"severity": "HIGH", "layer": "SOURCE", "count": 2},
    {"severity": "MEDIUM", "layer": "FACT", "count": 2}
  ],
  "auto_fixable": 4,
  "manual_required": 1,
  "request_id": "REQ_20260614_153000"
}
```

이걸로 채널마다 어느 패턴이 자주 검수 실패하는지 분석 가능 → 향후 Profile 강화에 활용.

---

# 9. 구축 순서

## 1단계 (즉시)
```
1. core/critic/ 폴더 생성
2. core/critic/data_request.py — DataRequest, DataIssue 클래스
3. core/critic/patterns.py — 할루시네이션 패턴 사전
4. core/agents/critic.py — 4층 검증 구현
```

## 2단계
```
5. core/agents/scout.py 확장 — DataIssue 기반 정밀 검색
6. core/agents/loop.py — critic_scout_loop()
7. panel/right_panel.py 확장 — DataRequest UI
```

## 3단계
```
8. Part 1 통합 — on_part_complete() 자동 호출
9. Part 2~8 순차 통합
10. 03_Logs 자동 기록
```

---

# 10. 통합 체크리스트

```
□ Critic이 4층 검증 모두 수행하는가
□ 출처 없는 통계/인용 자동 탐지하는가
□ DataIssue가 구체적인가 (어디서 무엇이 필요한지)
□ 우측 대화창에 시각적으로 표시되는가
□ Scout 자동 보강 가능한 이슈는 자동 처리되는가
□ 사용자 개입 필요 이슈는 명확히 구분되는가
□ 재검증 루프가 최대 3회 작동하는가
□ 모든 활동이 03_Logs에 기록되는가
□ Channel Profile 금지 표현 검사하는가
□ 댓글 근거 검증 작동하는가
```

---

**문서 끝 — 이 시스템이 완성되면 SAGE Studio의 결과물 신뢰도가 결정된다.**
