# prompts/parts/part1/STEP_채널검색.md
> Part 1 Step 1 — 떡상 채널 검색
> Librarian이 호출하는 첫 번째 스텝

---

## 이 스텝의 목적

작은 채널인데 영상 하나가 폭발한 **떡상 채널**을 찾는다.
이런 채널이 갖고 있는 **시청자 모임**과 **댓글 데이터**가 다음 단계의 원료가 된다.

---

## 검색 대상

```yaml
target_categories: {channel_profile.typical_categories}
target_audience: {channel_profile.target_audience}
language: {language}
exclude_keywords: {channel_profile.forbidden_expressions}
```

---

## 4중 필터 알고리즘

### 1차 필터 — 떡상 지수

```python
def is_explosive(channel):
    ratio = channel.recent_video_views / max(channel.subscribers, 1)
    return ratio >= 5
```

**의미:** 구독자 1명당 5회 이상 본 영상이 있는 채널
**해석:** 알고리즘이 추천한 = 잠재력 있는 채널

### 2차 필터 — 댓글 밀도

```python
def has_high_engagement(video):
    density = video.comment_count / max(video.view_count, 1)
    return density >= 0.005  # 0.5%
```

**의미:** 100명 보면 0.5명 이상 댓글 단 영상
**해석:** 보고 말하고 싶게 만든 영상

### 3차 필터 — 시청 지속 신호

대표 영상의 댓글에서 다음 키워드 검색:

```
한국어:
  "끝까지 봤다"
  "여러 번 봤다"
  "또 보게 된다"
  "정주행"
  "시간 가는 줄 몰랐다"
  "다 보고 나니"

영어:
  "watched the whole thing"
  "kept watching"
  "binged"
  "couldn't stop"
```

이런 댓글이 5개 이상이면 → 시청 지속 시간 긴 영상으로 판정

### 4차 필터 — Profile 부합

```python
def matches_profile(channel, profile):
    # 카테고리 부합
    if not any(cat in channel.tags for cat in profile.typical_categories):
        return False
    
    # 금지 표현 검사
    if any(word in channel.description for word in profile.forbidden_expressions):
        return False
    
    # 타깃 추정 부합
    estimated_target = estimate_audience(channel)
    if not audience_match(estimated_target, profile.target_audience):
        return False
    
    return True
```

---

## 검색 도구

### YouTube Data API (한국어 채널)

```python
# 1단계: 카테고리 키워드 검색
search_params = {
    "q": " OR ".join(profile.typical_categories[:3]),
    "type": "channel",
    "maxResults": 50,
    "regionCode": "KR",
    "relevanceLanguage": "ko",
}

# 2단계: 각 채널의 통계 조회
channels = youtube.channels.list(
    part="statistics,snippet",
    id=",".join(channel_ids)
)

# 3단계: 최근 영상 조회
videos = youtube.search.list(
    channelId=ch_id,
    order="viewCount",
    maxResults=10
)

# 4단계: 4중 필터 적용
explosive = [v for v in videos if all_filters_pass(v)]
```

### Tavily (국외 채널)

```python
tavily.search(
    query=f"small youtube channel viral {category} {language}",
    search_depth="advanced",
    max_results=10
)
```

---

## 종합 점수 계산

각 채널의 떡상 점수:

```python
def calculate_explosive_score(channel):
    score = 0.0
    
    # 1차: 떡상 지수 (40%)
    explosive_ratio = channel.views / max(channel.subs, 1)
    score += min(explosive_ratio / 10, 1.0) * 0.4
    
    # 2차: 댓글 밀도 (30%)
    density = channel.comments / max(channel.views, 1)
    score += min(density / 0.01, 1.0) * 0.3
    
    # 3차: 시청 지속 신호 (20%)
    retention = count_retention_signals(channel.top_comments)
    score += min(retention / 10, 1.0) * 0.2
    
    # 4차: Profile 부합도 (10%)
    profile_match = calculate_profile_match(channel, profile)
    score += profile_match * 0.1
    
    return score
```

상위 5개 채널 선정.

---

## 출력 형식

```json
{
  "step": "channel_search",
  "completed": true,
  "discovered_channels": [
    {
      "channel_name": "실제 채널명",
      "channel_url": "https://youtube.com/@channel_handle",
      "channel_id": "UCxxxxxx",
      "subscriber_count": 7234,
      "total_video_count": 47,
      "representative_video": {
        "title": "실제 영상 제목",
        "url": "https://youtube.com/watch?v=...",
        "video_id": "abc123",
        "view_count": 342847,
        "comment_count": 2156,
        "like_count": 12453,
        "published_at": "2026-03-15"
      },
      "scores": {
        "explosive_ratio": 47.4,
        "comment_density": 0.0063,
        "retention_signals": 12,
        "profile_match": 0.87,
        "total_score": 0.84
      },
      "selection_reason": "구독자 7천명인데 30만 조회. 댓글에서 '여러 번 봤다' 12회 발견. 채널 Profile의 '감정/관계' 카테고리 완전 부합.",
      "source": "[SOURCE: youtube_api_search_query_{timestamp}]"
    }
    // ... 5개
  ],
  "search_metadata": {
    "tool_used": ["youtube_api", "tavily"],
    "queries_executed": 8,
    "total_candidates_examined": 247,
    "passed_all_filters": 5,
    "timestamp": "2026-06-14T15:30:00"
  }
}
```

---

## 실패 처리

### 검색 결과 0건

```python
# 1차: 키워드 재구성
new_query = expand_with_synonyms(original_query)

# 2차: 카테고리 확대
extended_categories = profile.typical_categories + related_categories

# 3차: 검색 범위 확대 (지역/언어)
extend_search_region()

# 4차: 그래도 0건이면
return {
    "status": "NEEDS_USER_INPUT",
    "message": "검색 키워드 조정이 필요합니다. 우측 SAGE 브레인에 다른 키워드를 입력해주세요."
}
```

### 필터 통과 채널 < 5개

```python
# 필터 완화하지 말 것 (품질 떨어짐)
# 대신 → Scout 호출하여 추가 검색

scout.execute({
    "query": f"more {category} channels viral small",
    "missing_data": ["explosive channels < 5"]
})
```

---

## 절대 금지

```
❌ 검색 결과 없는데 채널 만들어내기
❌ 구독자수/조회수 임의 기재
❌ "추정" "약" 등으로 얼버무리기
❌ 4중 필터 완화 (품질 우선)
❌ Profile 무시 (다른 채널이 떡상 점수 높아도)
```

---

## 다음 스텝

검색 완료 → 자동으로 `STEP_댓글분석.md` 호출
각 채널의 대표 영상에서 댓글 200개씩 수집 시작.

---

**스텝 끝 — 떡상 채널이 발견되어야 다음 스텝으로 진입.**
