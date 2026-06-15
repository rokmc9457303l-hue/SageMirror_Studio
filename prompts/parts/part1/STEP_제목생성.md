# prompts/parts/part1/STEP_제목생성.md
> Part 1 Step 4 — 떡상 제목 생성
> 시청자를 멈추게 하는 제목 만들기

---

## 이 스텝의 정체

제목은 **CTR(클릭률)**을 결정한다.
아무리 좋은 영상도 제목이 약하면 클릭이 안 된다.

YouTube 알고리즘은 CTR을 보고 추천 여부를 결정한다.
→ **제목이 약하면 떡상은 없다.**

---

## 입력

```yaml
topic_candidates: {STEP_주제발굴.md의 10개 이상 주제}
channel_profile: {channel_profile_yaml}
```

---

## 떡상 제목의 7대 공식

각 제목은 다음 7개 공식 중 하나 이상을 사용:

### 공식 1: 수사 의문문

```
✅ "왜 착한 사람이 갑자기 차가워질까?"
✅ "당신은 왜 그날 그 말을 못 했을까요?"

원리: 시청자 머릿속에 답을 찾고 싶은 욕구 생성
```

### 공식 2: 구체적 숫자

```
✅ "20년을 참았던 그 사람"
✅ "65세에야 알게 된 한 가지"
✅ "엄마 돌아가신 후 3년"

원리: 구체성이 사실감을 만든다
```

### 공식 3: 반전 / 의외성

```
✅ "마음이 떠난 사람은 더 이상 다투지 않는다"
✅ "당신을 가장 사랑한 사람이 가장 먼저 떠난 이유"
✅ "착한 사람의 마지막 선택"

원리: 통념과 다른 진실 → 호기심 폭발
```

### 공식 4: 강렬한 감정 단어

```
✅ "끝내", "결국", "마침내", "여전히"
✅ "한 번도", "다시는", "절대"
✅ "조용히", "아무 말 없이"

원리: 감정 단어가 자기 동일시 유발
```

### 공식 5: 구체적 상황

```
✅ "엄마 마지막 전화의 진짜 의미"
✅ "결혼 30년 만에 알게 된 한 가지"
✅ "퇴직 첫날 거울 앞에서"

원리: 시청자가 즉시 자기 경험 떠올림
```

### 공식 6: 자기 동일시 트리거

```
✅ "당신이 ___할 때"
✅ "혹시 당신도..."
✅ "이런 순간 있었나요"

원리: "당신"으로 직접 호명 → 클릭 욕구
```

### 공식 7: 통찰 약속

```
✅ "___의 진짜 이유"
✅ "이제야 알게 된 ___"
✅ "그동안 몰랐던 ___"

원리: 시청 후 깨달음 약속 → 시간 투자 정당화
```

---

## 제목 작성 절대 금지

```
❌ "외로움에 대하여" (추상적, 클릭 욕구 없음)
❌ "오늘은 ___에 대해 알아보겠습니다" (자기소개형)
❌ "충격! 놀라운! 대박!" (저속한 어그로)
❌ "##세대를 위한 ___" (대상 한정)
❌ "행복해지는 법" (식상한 자기계발)
❌ "꿀팁 모음" (가벼움)
❌ 모든 영상이 비슷한 패턴 (천편일률)
```

---

## Profile 톤에 맞춘 제목

채널 톤에 따라 제목 스타일 달라야 함:

### Profile.tone = "차분하고 깊은 감정 해부형"

```
✅ "오래 참은 사람이 어느 날 조용히 떠나는 이유"
✅ "마음이 떠난 순간, 그 사람이 보낸 침묵의 신호"
✅ "당신이 그토록 외로웠던 진짜 이유"

❌ 자극적 단어 ("충격!", "대박!")
❌ 가벼운 어조
```

### Profile.tone = "따뜻하고 친근한 부엌 수다"

```
✅ "엄마가 끓여주던 김치찌개, 그 비밀의 한 가지"
✅ "20년 만에 다시 찾아낸 외할머니 손맛"
✅ "오늘 저녁, 그리운 그 맛을 다시 만났다"

❌ 무거운 분위기
❌ 추상적 표현
```

---

## 제목 길이 기준

```
한국어:
  - 최적: 15~25자 (썸네일과 함께 잘 보임)
  - 최대: 35자 (모바일에서 잘림 위험)
  
영어:
  - 최적: 30~50자
  - 최대: 70자
```

---

## 각 주제당 제목 3개

주제 1개당 다음 3가지 제목:

```
제목 1 (메인): 가장 강력한 떡상 제목 — A/B 테스트의 A
제목 2 (대안): 다른 각도의 제목 — A/B 테스트의 B
제목 3 (보수): 안전한 제목 — 떡상 실패 시 백업
```

---

## 작업 흐름

### 1단계: 각 주제 분석

```python
for topic in topic_candidates:
    # 핵심 감정 추출
    core_emotion = extract_core_emotion(topic)
    
    # 자기 동일시 키워드 추출
    self_id_keywords = extract_keywords(topic)
    
    # 구체적 상황 식별
    specific_situations = identify_situations(topic)
```

### 2단계: 7대 공식 적용

```python
for topic in topic_candidates:
    title_drafts = []
    
    # 공식 1: 수사 의문문
    title_drafts.append(generate_rhetorical_question(topic))
    
    # 공식 2: 구체적 숫자
    title_drafts.append(generate_with_number(topic))
    
    # 공식 3: 반전
    title_drafts.append(generate_with_twist(topic))
    
    # 공식 4: 감정 단어
    title_drafts.append(add_emotional_words(topic))
    
    # 공식 5: 구체적 상황
    title_drafts.append(add_specific_situation(topic))
    
    # 공식 6: 자기 동일시
    title_drafts.append(add_self_identification(topic))
    
    # 공식 7: 통찰 약속
    title_drafts.append(promise_insight(topic))
```

### 3단계: Profile 톤 필터

```python
for drafts in all_title_drafts:
    filtered = [t for t in drafts if matches_tone(t, profile.tone)]
```

### 4단계: 점수 매기기

```python
def score_title(title):
    score = 0.0
    
    # 길이 적정성 (15%)
    score += length_score(title) * 0.15
    
    # 자기 동일시 가능성 (25%)
    score += self_id_potential(title) * 0.25
    
    # 구체성 (20%)
    score += specificity(title) * 0.2
    
    # 호기심 유발 (20%)
    score += curiosity_score(title) * 0.2
    
    # Profile 톤 부합 (10%)
    score += tone_match(title) * 0.1
    
    # 클리셰 회피 (10%)
    score += anti_cliche_score(title) * 0.1
    
    return score
```

### 5단계: 각 주제당 상위 3개 선정

---

## 출력 형식

```json
{
  "step": "title_generation",
  "completed": true,
  
  "topic_titles": [
    {
      "topic_id": "T001",
      "topic": "오래 참은 사람이 어느 날 조용히 떠나는 이유",
      
      "titles": [
        {
          "title": "착한 사람이 갑자기 차가워지는 진짜 이유",
          "rank": 1,
          "type": "main",
          "formulas_used": ["수사_의문문", "반전", "통찰_약속"],
          "length": 21,
          "scores": {
            "length": 0.95,
            "self_identification": 0.92,
            "specificity": 0.85,
            "curiosity": 0.93,
            "tone_match": 0.97,
            "anti_cliche": 0.88,
            "total": 0.91
          },
          "rationale": "수사 의문 + '진짜 이유' 통찰 약속 + '갑자기' 반전. 시청자 즉시 '내 얘기' 느낌."
        },
        {
          "title": "20년을 참았던 그 사람, 왜 아무 말 없이 떠났을까",
          "rank": 2,
          "type": "alternative",
          "formulas_used": ["구체적_숫자", "수사_의문문", "강렬한_감정_단어"],
          "length": 27,
          "scores": {
            "total": 0.87
          },
          "rationale": "구체적 숫자(20년) + '아무 말 없이' 감정 단어 + 미스터리"
        },
        {
          "title": "마음이 떠난 사람은 더 이상 다투지 않는다",
          "rank": 3,
          "type": "conservative",
          "formulas_used": ["반전", "통찰"],
          "length": 21,
          "scores": {
            "total": 0.82
          },
          "rationale": "통념 반전. 차분한 톤. 안전한 선택지."
        }
      ]
    }
    // ... 10개 이상
  ]
}
```

---

## 자가 검증

```
□ 각 주제에 제목 3개 모두 있는가?
□ 제목 길이 15~35자 범위?
□ 7대 공식 중 1개 이상 사용?
□ Profile.tone에 맞는가?
□ 클리셰 사용 0건?
□ {forbidden_expressions} 미포함?
□ 자기 동일시 유발하는가?
□ A/B/보수 3종 다양성 있는가?
```

---

## 절대 금지

```
❌ 어그로 ("충격!", "대박!", "꼭 보세요!")
❌ Profile.tone과 다른 어조
❌ 추상적 제목 ("외로움에 대해")
❌ 자기계발류 ("___하는 5가지 방법")
❌ 모든 주제에 같은 패턴 (다양성 필요)
❌ {forbidden_expressions} 사용
❌ 사실 왜곡 (주제와 다른 약속)
```

---

## 다음 단계

제목 생성 완료 → Comment Topic Packet 최종 완성 → Critic 자동 검수 → Part 2로 전달

---

**스텝 끝 — Part 1 작업 완료. 사용자가 주제 1개 선택하면 Part 2 자동 시작.**
