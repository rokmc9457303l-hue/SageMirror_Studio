---
type: 인용DB
fields: [인용문, 출처, 페이지, 저자, 검증여부, 카테고리, 키워드]
-
channel_id: UNCLASSIFIED
category: 사유/성찰
status: "#Raw_Data"
migrated_date: 2026-06-12
---
# 인용 데이터베이스

검증된 인용문 모음. YAML frontmatter로 구조화됨.

## 신규 인용 추가 형식

```yaml
- 인용문: "이것은 인용문입니다"
  출처: 책제목
  페이지: 123
  저자: 저자이름
  검증여부: true
  카테고리: 철학
  키워드: [고독, 의지]
```

## 자동 추가
앱이 외부 자료에서 인용문 발견 시 자동 추가.
검증 통과한 것만 등재.
