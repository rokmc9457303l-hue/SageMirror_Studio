# Part 5 — STEP: 8계정 운영표

## 목적

112씬을 Google Opal 8개 계정에 균등 분배하고
2일 운영 일정을 확정한다.

## 계정 배분

| 계정 | 씬 범위 | 씬 수 | 운영일 |
|------|---------|-------|--------|
| Account 1 | 001~014 | 14씬 | Day 1 |
| Account 2 | 015~028 | 14씬 | Day 1 |
| Account 3 | 029~042 | 14씬 | Day 1 |
| Account 4 | 043~056 | 14씬 | Day 1 |
| Account 5 | 057~070 | 14씬 | Day 2 |
| Account 6 | 071~084 | 14씬 | Day 2 |
| Account 7 | 085~098 | 14씬 | Day 2 |
| Account 8 | 099~112 | 14씬 | Day 2 |

## 2일 운영 원칙

```
Day 1: Account 1~4 (scene 001~056)
       → Day 1 완료 후 실패 씬 목록 추출
Day 2: Account 5~8 (scene 057~112)
       + Day 1 실패분 재시도 (남은 계정 여유분 활용)
```

## 운영표 출력 형식

```json
{
  "account": 1,
  "day": 1,
  "scenes": ["001", "002", ..., "014"],
  "opal_json_file": "opal_prompts_day1.json",
  "status": "pending",
  "retry_scenes": []
}
```

## 실패 처리

```
실패 기준: Opal 생성 오류 or 품질 미달
재시도 횟수: 최대 2회
2회 실패 시: retry_image_list.md 에 기록 → 수동 처리
```

## 상태값

```
pending → working → done / failed
```

## p5_packet 구조

```json
{
  "part": 5,
  "day1_accounts": [1, 2, 3, 4],
  "day2_accounts": [5, 6, 7, 8],
  "total_scenes": 112,
  "done_scenes": 0,
  "failed_scenes": [],
  "opal_day1": "opal_prompts_day1.json",
  "opal_day2": "opal_prompts_day2.json",
  "account_plan": "account_operation_table.json",
  "next_part": 6
}
```

## 다음 단계

→ p5_packet → Part 6 나레이션
