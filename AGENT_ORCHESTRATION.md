# AGENT_ORCHESTRATION.md
> 13개 에이전트가 떡상 영상을 만드는 협업 흐름
> Conductor + 8개 Part 에이전트 + 4개 보조 에이전트

---

# 0. 이 문서의 정체

각 에이전트의 MD는 자기 일만 안다.
이 문서는 **모두가 어떻게 협업하는지** 보여준다.

이 문서가 없으면 에이전트들은 따로 논다.

---

# 1. 13개 에이전트 전체 지도

```
                  🎼 Conductor (지휘자)
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   [메인 8개]      [보조 3개]      [품질 1개]
        │               │               │
        ▼               ▼               ▼
   📚 Librarian    🔍 Critic       🏆 QA Master
   🏗️ Architect   📦 Curator
   ✍️ Writer      🛰️ Scout
   🎨 Artist
   🎬 Director
   🎙️ Composer
   ✂️ Editor
   🚀 Assembler
```

---

# 2. 사용자 입장에서 본 흐름

```
사용자: 채널 선택 → "시작" 입력
            ↓
[자동 실행 - 사용자 개입 X]
            ↓
Conductor가 모든 에이전트 호출 시작
            ↓
약 5~10분 후
            ↓
사용자에게: 주제 10개 후보 표시
            ↓
사용자: 1개 선택 (방향 결정)
            ↓
[자동 실행 - 사용자 개입 X]
            ↓
Architect → Writer → Artist → Director → Composer → Editor → Assembler
            ↓
QA Master 최종 점검
            ↓
사용자에게: 영상 패키지 + 떡상 점수 표시
            ↓
사용자: 최종 승인 → 출시
```

**사용자 액션은 단 2번:**
1. 주제 선택 (방향)
2. 최종 승인 (출시)

---

# 3. 시간순 상세 흐름

## 0초 — 사용자 "시작"

```python
# panel/right_panel.py
if user_input == "시작":
    conductor.initiate(current_channel)
```

## 0초 — Conductor 호출

```python
# core/agents/conductor.py
class ConductorAgent:
    def initiate(self, channel):
        # 1. Channel Profile 로드
        profile = load_current_profile()
        
        # 2. 이전 영상 RAG (옵시디언)
        previous = rag_search_previous_videos(channel, limit=5)
        
        # 3. Part 1 실행 명령
        self.execute_part1(profile, previous)
```

## 1초 — Part 1 자동 실행

```python
def execute_part1(self, profile, previous):
    # 모든 MD 로드
    rules = load_md("prompts/parts/part1/AGENT_PROTOCOL.md")
    main = load_md("prompts/parts/part1/MAIN_PROMPT.md")
    
    # Librarian 호출
    librarian = LibrarianAgent(profile)
    librarian.set_context(rules, main, previous)
    
    # 자동 실행
    result = librarian.execute_with_steps([
        "STEP_채널검색.md",
        "STEP_댓글분석.md",
        "STEP_주제발굴.md",
        "STEP_제목생성.md",
    ])
    
    # 자동 검증
    self.auto_verify_and_save(result, part_num=1)
```

## 30초~3분 — Librarian 작업

```python
# core/agents/librarian.py
class LibrarianAgent:
    def execute_with_steps(self, step_files):
        intermediate_results = {}
        
        for step_file in step_files:
            step_prompt = load_md(f"prompts/parts/part1/{step_file}")
            
            # 이전 스텝 결과 + 새 스텝 프롬프트
            context = build_context(intermediate_results)
            
            # Gemma 호출 (3중 보호)
            result = self.safe_gemma_call(
                system=self.system_prompt + step_prompt,
                user=context,
                anti_hallucination=True,
                source_citation_required=True,
                profile_strict=True,
            )
            
            # 단계마다 Pre-Critic 검증
            if not pre_critic.verify(result):
                # Scout 자동 보강
                supplement = scout.execute({...})
                result = self.retry_with_supplement(result, supplement)
            
            intermediate_results[step_file] = result
        
        # 최종 결과 통합
        return self.compose_packet(intermediate_results)
```

## 3~5분 — Critic 4층 검증

```python
# 자동 호출됨
def auto_verify_and_save(self, result, part_num):
    # 1. Critic 4층 검증
    verdict = critic.execute({
        "part_result": result,
        "part_num": part_num,
    })
    
    if verdict.status == "NEEDS_DATA":
        # Scout 자동 호출
        for issue in verdict.issues:
            if issue.auto_fixable:
                scout.execute({
                    "query": issue.search_query,
                    "missing_data": issue.required_data,
                })
        
        # 재실행 (최대 3회)
        return self.retry_part(part_num, max_iterations=3)
    
    if verdict.status == "NEEDS_FIX":
        # 사용자에게 알림 (우측 SAGE 브레인)
        return self.notify_user(verdict.data_request)
    
    # PASS → 다음 단계
    self.save_and_push(result, part_num)
```

## 5분 — Curator 자동 저장

```python
# core/agents/curator.py
def save_and_push(self, result, part_num):
    # Curator 호출
    paths = curator.execute({
        "raw_content": result.raw_data,
        "wiki_content": result.refined_data,
        "schema_content": result.metadata,
        "channel": current_channel,
        "part_num": part_num,
    })
    
    # 옵시디언 자동 저장 완료
    # 다음 Part로 Packet 푸시 (자동)
    self.push_to_next_part(part_num + 1, result, paths)
```

## 5분 — 사용자에게 결과 표시

```python
# 화면 표시
display_topic_candidates(result.topic_candidates)
show_message("주제 10개 발굴 완료. 하나를 선택해주세요.")

# 사용자 입력 대기
selected_topic = wait_for_user_selection()
```

## ~ — 사용자 주제 선택

```python
# 사용자가 T003 선택
on_topic_selected(topic_id="T003"):
    set_state("selected_topic", topic_id)
    # Part 2 자동 시작
    conductor.execute_part2()
```

## 5~30분 — Part 2~8 자동 연쇄

```python
def execute_part2(self):
    architect = ArchitectAgent(profile)
    result = architect.execute_with_steps(["STEP_기획.md", ...])
    self.auto_verify_and_save(result, part_num=2)
    self.execute_part3()  # 자동 연쇄

def execute_part3(self):
    writer = WriterAgent(profile)
    # ... 같은 패턴
    self.execute_part4()

# Part 8까지 자동 연쇄
```

## 30분 — QA Master 최종 점검

```python
# core/agents/qa_master.py
class QAMasterAgent:
    def final_check(self, all_packets):
        return {
            "총점": 0.91,
            "체크리스트": {
                "주제_명확성": "PASS",
                "제목_클릭유도": "PASS",
                "썸네일_시선유도": "PASS",
                "도입_5초_훅": "PASS",
                "감정_곡선": "PASS",
                "대본_일관성": "PASS",
                "이미지_캐릭터_일관성": "PASS",
                "나레이션_휴먼터치": "PASS",
                "BGM_감정매칭": "PASS",
                "숏폼_파생점": "PASS",
                "출처_표기_완전성": "PASS",
                "Profile_부합도": "PASS",
                "트렌드_부합도": "PASS",
            },
            "떡상_확률": 0.87,
            "개선_제안": [],
        }
```

## 31분 — 사용자에게 최종 결과

```python
display_final_package({
    "video_title": "착한 사람이 갑자기 차가워지는 진짜 이유",
    "qa_score": 0.91,
    "explosive_probability": 0.87,
    "capcut_package_path": "...",
    "shortform_count": 3,
    "all_assets_ready": True,
})

show_button("[승인 → 출시]")
```

---

# 4. 에이전트 간 통신 규칙

## Packet으로 통신

에이전트는 직접 변수를 주고받지 않는다. **Packet으로만**.

```python
# ✅ 올바른 통신
packet = {
    "from_agent": "Librarian",
    "to_agent": "Architect",
    "version": "v001",
    "status": "APPROVED",
    "payload": {...},
    "raw_path": "...",
    "wiki_path": "...",
    "schema_path": "...",
    "timestamp": "...",
}

architect.receive_packet(packet)
```

## 상태 머신 강제

```
DRAFT → REVIEW → (PASS / NEEDS_DATA / NEEDS_FIX)
NEEDS_DATA → RESEARCHED → REWRITTEN → REVIEW
APPROVED → LOCKED → PUSHED
```

APPROVED 되지 않은 Packet은 다음 Part로 못 간다. **시스템이 강제**.

---

# 5. 보조 에이전트 호출 규칙

## Critic — 자동 호출

```python
# 모든 메인 에이전트는 작업 완료 시 Critic 자동 호출
def complete_work(self, result):
    verdict = critic.verify(result)
    if not verdict.passed:
        return self.handle_critic_failure(verdict)
    return result
```

## Curator — 자동 호출

```python
# Critic PASS 후 자동 호출
def save_result(self, result):
    paths = curator.execute({...})
    return paths
```

## Scout — Critic 실패 시 자동

```python
# Critic이 NEEDS_DATA 판정 시 자동
if verdict.status == "NEEDS_DATA":
    scout.execute({
        "query": verdict.search_query,
        "missing_data": verdict.missing_items,
    })
```

## Researcher — 작업 시작 시 자동

```python
# 모든 메인 에이전트는 작업 시작 시 자동 RAG
def start_work(self):
    rag_results = researcher.deep_search(
        query=self.current_topic,
        folders=["01_Raw_Data", "01_Wiki"],
        limit=10,
    )
    self.context.add(rag_results)
```

---

# 6. 실패 처리 정책

## 1회 실패: 자동 보강 후 재실행

```python
if verdict.failed:
    supplement = scout.execute(...)
    result = retry(supplement=supplement)
```

## 2회 실패: 사용자 알림

```python
if second_failure:
    show_user_notification(
        title="Part {N} 검수 미통과",
        details=verdict.data_request,
        actions=["자동 보강 재시도", "사용자 직접 입력", "해당 부분 삭제"],
    )
```

## 3회 실패: 작업 중단

```python
if third_failure:
    pause_workflow()
    notify_user(
        message="자동 진행 불가. 사용자 개입 필요.",
        details=full_log,
    )
```

---

# 7. Gemma 호출 통합 함수

모든 에이전트가 동일 함수 사용:

```python
# core/brain.py
def call_gemma_with_full_context(
    agent_name: str,
    part_num: int,
    step_name: str = None,
    user_input: str = None,
):
    """
    완전한 컨텍스트로 Gemma 호출
    - MD 파일 자동 로드
    - Channel Profile 자동 적용
    - 옵시디언 RAG 자동 포함
    - 할루시네이션 방지 강제
    """
    
    # 1. MD 로드 (계층별)
    master = load_md("MASTER_VIDEO_STRATEGY.md")
    anti_hall = load_md("prompts/shared/ANTI_HALLUCINATION.md")
    citation = load_md("prompts/shared/SOURCE_CITATION.md")
    agent_md = load_md(f"prompts/agents/{agent_name}.md")
    part_md = load_md(f"prompts/parts/part{part_num}/MAIN_PROMPT.md")
    
    if step_name:
        step_md = load_md(f"prompts/parts/part{part_num}/STEP_{step_name}.md")
    else:
        step_md = ""
    
    # 2. Channel Profile
    profile = load_current_profile()
    profile_section = format_profile_for_prompt(profile)
    
    # 3. 옵시디언 RAG
    rag = rag_search_for_agent(agent_name, user_input)
    
    # 4. 시스템 프롬프트 조립
    system = "\n\n---\n\n".join([
        master,
        anti_hall,
        citation,
        agent_md,
        part_md,
        step_md,
        f"## Channel Profile\n{profile_section}",
        f"## RAG Results\n{rag}",
    ])
    
    # 5. Gemma 호출
    result = ollama_call(
        model="gemma4:e4b",
        system=system,
        user=user_input,
        timeout=300,
        num_predict=4000,
    )
    
    # 6. 자동 검증
    if has_hallucination_pattern(result):
        return retry_with_warning(result)
    
    if not has_source_tags(result):
        return retry_with_warning(result)
    
    return result
```

---

# 8. 검수 4중 방어선

이 시스템에 거짓 자료가 들어갈 4번의 차단:

```
1차 방어: Gemma 시스템 프롬프트 (MD가 강제)
   → ANTI_HALLUCINATION.md, SOURCE_CITATION.md

2차 방어: Pre-Critic (Gemma 출력 직후)
   → 패턴 매칭으로 의심 표현 즉시 거부

3차 방어: Critic (Part 완료 시)
   → 4층 검증으로 정밀 검사

4차 방어: QA Master (전체 완료 시)
   → 떡상 가능성 종합 평가
```

이 4중 방어선을 통과한 자료만 영상에 들어간다.

---

# 9. 자동 학습 루프

매 영상이 완성될 때마다:

```python
def post_video_learning():
    # 1. 옵시디언 저장
    save_to_obsidian(full_video_data)
    
    # 2. 다음 영상에 활용 가능한 패턴 추출
    patterns = extract_reusable_patterns(full_video_data)
    save_patterns_to_obsidian(patterns)
    
    # 3. Channel Profile 보강 제안
    profile_suggestions = analyze_what_worked(full_video_data)
    notify_user_for_profile_update(profile_suggestions)
    
    # 4. 댓글 피드백 누적 (영상 출시 후)
    # → 다음 영상 주제 발굴 시 자동 RAG
```

채널이 진화한다. 10편째는 1편보다 훨씬 강력해진다.

---

# 10. 핵심 한 문장

```
13개 에이전트는 따로 일하지 않는다.
하나의 두뇌처럼 협업한다.
사용자는 방향과 승인만 한다.
시스템이 나머지를 자동으로 한다.
이것이 V100이다.
```

---

**문서 끝 — 모든 에이전트는 이 문서에 따라 협업한다.**
