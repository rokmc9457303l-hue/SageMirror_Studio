# Part 8 — STEP: 최종 검수 리포트

## 목적

Part 1~7 결과물 전체를 종합 검수하고
업로드 패키지 완성 여부를 판정한다.

## 입력

- p1_packet ~ p7_packet (모든 패킷)
- assembly_order.csv
- capcut_project.json

## 검수 항목

### 1. 콘텐츠 품질 (Part 1~3)

| 항목 | 기준 | 결과 |
|------|------|------|
| 주제 명확성 | core_emotion 1개 확정 | ✅/❌ |
| 제목 후보 | 5개 이상 | ✅/❌ |
| 대본 씬 수 | 정확히 112씬 | ✅/❌ |
| 금지 표현 포함 | 0건 | ✅/❌ |
| 지식 인용 출처 | 전부 [SOURCE:] 태그 | ✅/❌ |
| 감정 곡선 구현 | 7단계 완성 | ✅/❌ |

### 2. 자료 품질 (Part 1 RAG)

| 항목 | 기준 |
|------|------|
| knowledge_score 합계 | 15점 이상 (18점 만점) |
| 외부 출처 인용 | 최소 3건 |
| 댓글 반영 | comment_insights ⭐⭐⭐ 1건 이상 |

### 3. 제작물 완성도 (Part 4~7)

| 항목 | 기준 |
|------|------|
| 이미지 | 112개 |
| 영상 클립 | 112개 |
| 오디오 | 112개 |
| 자막 | 112개 |
| 숏폼 | 5편 |

### 4. 업로드 자료

| 항목 | 확인 |
|------|------|
| 제목 (최종 1개) | |
| 설명란 초안 | |
| 해시태그 (10~15개) | |
| 출처 정리 | |
| AI 사용 표시 | |

## 설명란 초안 구조 (CLAUDE.md 기준)

```
[제작자 노트]
이 영상을 만들게 된 계기:
나도 비슷한 경험:
시청자에게 전하고 싶은 것:

[오늘의 묵상]
{성경 또는 철학 인용 1줄}
{현자의 해석 1~2줄}
"오늘 하루, 이 한 줄과 함께하세요."

[출처]
{research_sources 목록}

[해시태그]
```

## 최종 판정

```
PASS 기준:
- 검수 항목 전체 ✅
- knowledge_score ≥ 15
- missing_items = 0
- 금지 표현 0건

FAIL 시: 해당 Part 재실행 지시 + 이유 명시
```

## final_packet 구조

```json
{
  "part": 8,
  "episode_id": "",
  "channel": "{{CHANNEL_NAME}}",
  "title_final": "",
  "description_draft": "",
  "hashtags": [],
  "sources": [],
  "ai_disclosure": true,
  "all_scenes_complete": true,
  "shorts_complete": true,
  "capcut_json": "capcut_project.json",
  "assembly_csv": "assembly_order.csv",
  "quality_score": 0,
  "review_passed": false,
  "completed_at": ""
}
```

## 다음 단계

→ final_packet.json 저장
→ 옵시디언 Schema 저장
→ 제작 완료
