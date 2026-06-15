# prompts/parts/part1/STEP_주제발굴.md
> Part 1 Step 3 — 떡상 주제 발굴
> 시청자 고통 → 영상 주제로 변환

---

## 이 스텝의 정체

여기가 영상의 **DNA**가 결정되는 순간이다.
좋은 주제 = 떡상의 시작
나쁜 주제 = 아무리 잘 만들어도 묻힘

---

## 입력

```yaml
extracted_patterns: {STEP_댓글분석.md의 5~10개 패턴}
channel_profile: {channel_profile_yaml}
previous_videos: {최근 5편 RAG 결과}
```

---

## 출력 목표

```
✅ 주제 후보 10개 이상 (절대 미만 금지)
✅ 각 주제에 댓글 근거 1~3개
✅ Channel Profile 100% 부합
✅ 이전 영상과 중복 0건
```

---

## 떡상 주제의 5대 조건

각 주제는 다음 5가지를 충족해야 한다:

### 1. 시청자가 "내 얘기"라고 느낄 것

```
✅ 좋은 예: "오래 참은 사람이 어느 날 조용히 떠나는 이유"
  → 시청자가 즉시 자기 상황을 떠올림

❌ 나쁜 예: "관계의 심리학"
  → 추상적, 자기 동일시 어려움
```

### 2. 구체적 상황이 떠오를 것

```
✅ 좋은 예: "엄마에게 끝내 못 한 그 한마디"
  → 구체적 상황: 부모, 못 한 말, 후회

❌ 나쁜 예: "후회에 대하여"
  → 추상적
```

### 3. 댓글 근거가 강할 것

```
✅ 댓글 50회 이상 반복된 패턴
✅ 실제 경험 댓글 3개 이상

❌ 1~2개 댓글에서 끌어낸 주제 (대표성 부족)
```

### 4. 채널 Profile 부합

```
✅ {target_audience}이 공감 가능
✅ {typical_categories} 영역
✅ {forbidden_expressions} 미포함
✅ {tone}으로 다룰 수 있음
```

### 5. 영상으로 만들 수 있을 것

```
✅ 8~15분 영상 분량 확보 가능
✅ 감정 곡선 그릴 수 있음
✅ 첫 5초 훅 만들 수 있음
✅ 시각화 가능 (Part 4)
```

---

## 주제 생성 6단계

### 1단계: 패턴 → 주제 원형

각 패턴(`extracted_patterns`)을 주제 원형으로 변환:

```
패턴: "참다가 떠나는 사람" (67회)
   ↓
주제 원형:
  - "오래 참은 사람이 어느 날 조용히 떠나는 이유"
  - "착한 사람이 갑자기 차가워지는 진짜 이유"
  - "마음이 떠난 순간 — 더 이상 노력하지 않는 사람"
  - "관계에서 가장 무서운 말은 침묵이다"
```

한 패턴에서 3~5개 주제 원형 생성.

### 2단계: Channel Profile 필터링

각 주제 원형을 Profile에 맞게 필터:

```python
def filter_by_profile(topic, profile):
    # 금지 표현 검사
    for forbidden in profile.forbidden_expressions:
        if forbidden in topic:
            return False
    
    # 톤 적합성
    if not matches_tone(topic, profile.tone):
        return False
    
    # 타깃 적합성
    if not appeals_to(topic, profile.target_audience):
        return False
    
    return True
```

### 3단계: 이전 영상 중복 제거

```python
def is_duplicate(topic, previous_videos):
    for prev in previous_videos:
        similarity = calculate_semantic_similarity(topic, prev.topic)
        if similarity > 0.7:
            return True
    return False
```

중복 시 → 변형 (각도 바꾸기) 또는 제외.

### 4단계: 떡상 점수 매기기

각 주제에 점수:

```python
def calculate_topic_score(topic, pattern, profile):
    score = 0.0
    
    # 댓글 근거 강도 (40%)
    score += min(pattern.frequency / 100, 1.0) * 0.4
    
    # 자기 동일시 가능성 (20%)
    score += calculate_self_identification(topic) * 0.2
    
    # 구체성 (15%)
    score += measure_specificity(topic) * 0.15
    
    # Profile 부합도 (15%)
    score += profile_match(topic, profile) * 0.15
    
    # 첫 5초 훅 가능성 (10%)
    score += hook_potential(topic) * 0.1
    
    return score
```

상위 10~15개 선정.

### 5단계: 제목 후보 생성

각 주제에 제목 후보 3개:

```
주제: "오래 참은 사람이 어느 날 조용히 떠나는 이유"

제목 후보 1: "착한 사람이 갑자기 차가워지는 진짜 이유"
  → 수사 의문문, 호기심 유발
  
제목 후보 2: "20년을 참았던 그 사람, 왜 아무 말 없이 떠났을까"
  → 구체적 숫자, 미스터리
  
제목 후보 3: "마음이 떠난 사람은 더 이상 다투지 않는다"
  → 반전, 통찰
```

### 6단계: 추가 정보 작성

각 주제마다:
- recommendation_reason (왜 추천)
- expected_reaction (시청자 예상 반응)
- expected_effect (조회수/댓글/체류)
- emotions (관련 감정)
- risk_notes (위험 요소)
- planning_hint (Part 2를 위한 감정 흐름 제안)

---

## 출력 형식

```json
{
  "step": "topic_generation",
  "completed": true,
  
  "topic_candidates": [
    {
      "topic_id": "T001",
      "topic": "오래 참은 사람이 어느 날 조용히 떠나는 이유",
      
      "title_candidate": "착한 사람이 갑자기 차가워지는 진짜 이유",
      "title_alternatives": [
        "20년을 참았던 그 사람, 왜 아무 말 없이 떠났을까",
        "마음이 떠난 사람은 더 이상 다투지 않는다"
      ],
      
      "comment_basis": {
        "pattern_id": "P001",
        "frequency": 67,
        "representative_quotes": [
          {
            "text": "20년을 참다가 결국 아무 말 없이 떠났습니다",
            "source": "[SOURCE: youtube_comment_id_abc123]"
          },
          {
            "text": "착한 사람이 갑자기 차가워지는 이유를 이제 알겠어요",
            "source": "[SOURCE: youtube_comment_id_def456]"
          },
          {
            "text": "더는 안 되겠다는 순간 마음이 떠나더라",
            "source": "[SOURCE: youtube_comment_id_ghi789]"
          }
        ]
      },
      
      "recommendation_reason": "67회 반복된 패턴. {target_audience}이 관계·가족·직장에서 반복적으로 겪는 감정. 자기 동일시 강함.",
      
      "expected_reaction": "'내 이야기 같다' '나도 저랬다' 자기 고백형 댓글 다수 예상. '이제야 이유를 알겠다' 깨달음 댓글 예상.",
      
      "expected_effect": {
        "view_potential": "high",
        "comment_potential": "very_high",
        "retention_potential": "high",
        "share_potential": "medium"
      },
      
      "emotions": ["서운함", "분노", "체념", "외로움"],
      
      "channel_profile_match": {
        "category": "관계·심리",
        "tone_match": 0.95,
        "audience_match": 0.92,
        "category_match": 0.98,
        "total_match": 0.95
      },
      
      "risk_notes": "관계 갈등 자극 가능 — 톤을 깊은 성찰로 유지 필요",
      
      "planning_hint": "Part 2 감정 흐름 제안: 참음(공감) → 무시당함(분노) → 침묵(체념) → 이별(슬픔) → 자기 회복(통찰)",
      
      "explosive_score": 0.87,
      "rank": 1
    }
    // ... 10개 이상
  ],
  
  "generation_metadata": {
    "patterns_used": 7,
    "raw_topics_generated": 23,
    "filtered_by_profile": 18,
    "after_duplicate_removal": 14,
    "final_selection": 12,
    "minimum_required": 10
  },
  
  "obsidian_saved": {
    "raw_path": "01_Raw_Data/채널_{channel}/Part1_자료수집/topics_{timestamp}.md",
    "wiki_path": "01_Wiki/주제발굴/{primary_emotion}_{timestamp}.md",
    "schema_path": "02_Schema/SRC_{timestamp}.json"
  }
}
```

---

## 자가 검증 (출력 전)

```
□ topic_candidates 개수 ≥ 10?
□ 각 주제에 comment_basis 있는가?
□ 각 주제에 실제 댓글 인용 3개 이상?
□ [SOURCE: ...] 태그 모두 있는가?
□ Channel Profile 부합도 모두 0.7 이상?
□ 이전 영상과 중복 0건?
□ title_candidate 모두 있는가?
□ planning_hint 모두 있는가? (Part 2 위해)
```

---

## 실패 처리

### 주제 10개 미만

```python
# 패턴 더 추출
patterns = re_extract_patterns(comments, threshold=30)  # 50→30 완화

# 같은 패턴에서 더 많은 각도
for pattern in patterns:
    additional = generate_more_angles(pattern, count=5)

# 그래도 10개 안 되면
if len(topics) < 10:
    return {
        "status": "NEEDS_DATA",
        "message": "주제 발굴 부족. Scout 호출 또는 추가 채널 검색 필요.",
        "current_count": len(topics),
        "minimum_required": 10
    }
```

---

## 절대 금지

```
❌ 댓글 근거 없는 주제 ("AI가 생각하기에 좋은 주제")
❌ 일반론 ("외로움이란 무엇인가")
❌ 교과서적 주제 ("후회의 심리학")
❌ Profile 외 카테고리
❌ 이전 영상 직접 복제
❌ 1~2개 댓글에서 끌어낸 주제 (대표성 부족)
```

---

## 다음 스텝

주제 발굴 완료 → 자동으로 `STEP_제목생성.md` 호출
각 주제의 제목을 더 정교하게 다듬는다.

---

**스텝 끝 — 주제가 약하면 다음 모든 단계가 무의미해진다.**
