# prompts/parts/part1/STEP_댓글분석.md
> Part 1 Step 2 — 댓글 감정 분석
> 떡상 채널의 댓글에서 시청자의 진짜 고통을 발굴

---

## 이 스텝의 정체

이 스텝은 **시스템 전체의 핵심**이다.

여기서 추출한 시청자의 진짜 고통이 → 다음 영상의 주제가 된다.
여기서 실수하면 → 만들어지는 영상이 떡상하지 못한다.

**댓글은 거짓말하지 않는다. 다만 듣는 사람이 못 들을 뿐이다.**

---

## 입력

```yaml
discovered_channels: {STEP_채널검색.md 결과 5개 채널}
channel_profile: {channel_profile_yaml}
```

---

## 작업 흐름

```
각 채널의 대표 영상에서 댓글 200개 수집
    ↓
1단계: 노이즈 제거 (단순 칭찬 / 짧은 반응)
    ↓
2단계: 의미 있는 댓글 50개 이상 선별
    ↓
3단계: 감정 카테고리 분류
    ↓
4단계: 반복 패턴 추출
    ↓
5단계: "시청자 고통 지도" 작성
```

---

## 1단계 — 노이즈 제거

다음 댓글은 **제외**한다:

```
❌ 단순 칭찬 ("좋은 영상이네요", "감사합니다")
❌ 짧은 반응 ("ㅋㅋ", "ㅠㅠ", "👍")
❌ 광고 / 스팸
❌ 욕설 / 비방
❌ 영상과 무관한 댓글
❌ 봇 댓글 (반복 패턴)
```

---

## 2단계 — 의미 있는 댓글 선별

다음 특징이 있는 댓글을 **선별**한다:

### 실제 경험 댓글

```
✅ "저도 그랬어요..." 
✅ "제 이야기 같아요"
✅ "지금 제 상황이에요"
✅ "그때 그 순간이 떠올라요"
```

### 해결되지 않은 고통

```
✅ "아직도 잊지 못해요"
✅ "그때 알았더라면"
✅ "지금도 가끔..."
✅ "여전히 마음이..."
```

### 구체적 디테일

```
✅ "그 사람 마지막 말이..."
✅ "20년 전 그날..."
✅ "엄마가 돌아가시기 전에..."
```

### 자기 인식

```
✅ "이제야 알겠어요"
✅ "이 영상 보고 깨달았어요"
✅ "왜 그랬는지 이제 이해돼요"
```

### 시청 지속 신호

```
✅ "끝까지 봤어요"
✅ "여러 번 봤어요"
✅ "댓글 보러 다시 왔어요"
```

---

## 3단계 — 감정 카테고리 분류

선별된 댓글을 다음 감정으로 분류:

```yaml
관계_상처:
  - 배신감, 서운함, 분노, 체념
  
가족_갈등:
  - 부모와의 거리, 자녀에 대한 죄책감, 형제 갈등
  
노년_외로움:
  - 고립감, 무력감, 상실감, 두려움
  
인생_후회:
  - 못 한 일, 잘못한 일, 놓친 기회
  
자기_직면:
  - 자기 부정, 자기 연민, 자기 수용
  
사회적_고립:
  - 직장 소외, 친구 단절, 시대 격차
  
사랑과_이별:
  - 미련, 그리움, 회한, 잊지 못함
  
실존_불안:
  - 의미 상실, 죽음, 종교적 의문
```

이 카테고리는 `{channel_profile.typical_categories}`에 맞게 조정.

---

## 4단계 — 반복 패턴 추출

분류된 댓글에서 **50회 이상 반복되는 패턴** 찾기:

### 패턴 예시

```
패턴 #1: "참다가 떠나는 사람"
  발견 횟수: 67회
  대표 댓글 3개:
    - "20년을 참다가 결국 아무 말 없이 떠났습니다"
    - "착한 사람이 갑자기 차가워지는 이유를 이제 알겠어요"
    - "더는 안 되겠다는 순간 마음이 떠나더라"
  공통 감정: [서운함, 분노, 체념, 외로움]
  공통 상황: [관계, 가족, 직장]

패턴 #2: "엄마에게 못 한 말"
  발견 횟수: 52회
  대표 댓글 3개:
    - "엄마 살아계실 때 한 번도 못 한 말..."
    - "돌아가시고 나서야 알았어요"
    - "그날 전화를 했더라면..."
  공통 감정: [후회, 죄책감, 그리움]
  공통 상황: [가족, 부모, 이별]
```

이런 패턴 5~10개 추출 → 다음 스텝에서 주제로 변환.

---

## 5단계 — 시청자 고통 지도

추출된 패턴을 종합하여 **시청자 고통 지도** 작성:

```json
{
  "channel_audience_pain_map": {
    "primary_pain": "관계에서 참다가 떠나는 경험",
    "secondary_pains": [
      "가족에 대한 미해결 감정",
      "노년의 고립과 무력감",
      "인생 후반의 자기 직면"
    ],
    "emotion_clusters": [
      {
        "cluster_name": "참음과 떠남",
        "frequency": 67,
        "emotions": ["서운함", "분노", "체념"],
        "common_situations": ["관계", "가족", "직장"],
        "comment_count": 67,
        "representative_quotes": [
          "20년을 참다가 결국 아무 말 없이 떠났습니다",
          "더는 안 되겠다는 순간 마음이 떠나더라"
        ]
      }
      // ... 더 많은 클러스터
    ],
    "viewer_demographic_estimation": {
      "age_range": "추정 50~70대",
      "life_stage": "후반기 자기 직면 시기",
      "relationship_status": "장기 관계 후 변화 시기"
    }
  }
}
```

---

## 출력 형식

```json
{
  "step": "comment_analysis",
  "completed": true,
  
  "raw_comments_collected": {
    "channel_1": {"url": "", "count": 200},
    "channel_2": {"url": "", "count": 200},
    "channel_3": {"url": "", "count": 200},
    "channel_4": {"url": "", "count": 200},
    "channel_5": {"url": "", "count": 200}
  },
  
  "meaningful_comments_selected": 287,
  
  "emotion_distribution": {
    "관계_상처": 89,
    "가족_갈등": 67,
    "노년_외로움": 54,
    "인생_후회": 43,
    "자기_직면": 34
  },
  
  "extracted_patterns": [
    {
      "pattern_id": "P001",
      "pattern_name": "참다가 떠나는 사람",
      "frequency": 67,
      "emotions": ["서운함", "분노", "체념"],
      "situations": ["관계", "가족", "직장"],
      "representative_comments": [
        {
          "text": "20년을 참다가 결국 아무 말 없이 떠났습니다",
          "source": "[SOURCE: youtube_comment_id_xyz123]",
          "channel": "채널명"
        }
        // ... 3개 이상
      ],
      "potential_topic_seed": "오래 참은 사람이 어느 날 조용히 떠나는 이유"
    }
    // ... 5~10개 패턴
  ],
  
  "audience_pain_map": {
    "primary_pain": "",
    "secondary_pains": [],
    "viewer_demographic_estimation": {}
  },
  
  "obsidian_saved": {
    "raw_path": "01_Raw_Data/채널_{channel}/Part1_자료수집/comments_{timestamp}.md",
    "wiki_path": "01_Wiki/감정/audience_pain_map_{timestamp}.md",
    "schema_path": "02_Schema/SRC_{timestamp}.json"
  }
}
```

---

## 실패 처리

### 의미 있는 댓글 < 50개

```python
# 추가 영상에서 댓글 수집
additional_videos = get_more_videos_from_channels()
collect_comments(additional_videos, additional=100)

# 여전히 부족하면
if meaningful_comments < 50:
    return {
        "status": "NEEDS_DATA",
        "message": "댓글 수집 부족. Scout 호출 또는 비슷한 채널 추가 검색 필요."
    }
```

### 패턴이 5개 미만

```python
# 분류 기준 완화하지 말 것
# 대신 검색 범위 확대

# 추가 채널에서 댓글 수집
additional_channels = expand_channel_search()
re_analyze_with_additional_data()
```

---

## 절대 금지

```
❌ 댓글 임의 창작 ("이런 댓글이 있을 것이다")
❌ 패턴 추정 (50회 미만인데 50회로 보고)
❌ 감정 카테고리 임의 추가 (Profile 외)
❌ 시청자 demographic 임의 추정 (댓글 근거 없이)
❌ 다른 영상의 댓글을 이 채널 댓글로 표기
```

---

## 다음 스텝

분석 완료 → 자동으로 `STEP_주제발굴.md` 호출
추출된 패턴을 → 실제 영상 주제로 변환.

---

**스텝 끝 — 진짜 고통을 발견하지 못하면 떡상은 없다.**
