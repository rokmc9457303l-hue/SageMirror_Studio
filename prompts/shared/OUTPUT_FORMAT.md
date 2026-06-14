# 출력 표준 형식

## Packet JSON 구조

모든 Part 결과는 다음 Packet JSON으로 출력:

```json
{
  "packet_type": "P{N}_PACKET",
  "source_part": "Part{N}",
  "target_part": "Part{N+1}",
  "version": "v001",
  "status": "DRAFT",
  "payload": {},
  "sources": [],
  "raw_path": "",
  "wiki_path": "",
  "schema_path": ""
}
```

## status 값

- `DRAFT`: 초안 (Critic 미통과)
- `CRITIC_PASS`: Critic 통과
- `READY`: 다음 Part 전달 가능
- `FINAL`: 확정

## 필수 필드

- `packet_type`, `source_part`, `target_part`: 항상 포함
- `sources`: 출처 목록 (비어있으면 Critic FAIL)
- `payload`: Part별 핵심 데이터

## 금지

- payload 없는 Packet 전달
- sources 없는 Packet 전달
- status=DRAFT 상태로 자동 push 금지
