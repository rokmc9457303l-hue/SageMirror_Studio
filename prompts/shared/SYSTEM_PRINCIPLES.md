# V100 시스템 절대 원칙 (SYSTEM_PRINCIPLES)

> 이 원칙은 모든 에이전트와 모든 Part에 적용된다.  
> Profile과 충돌 시 → Profile 우선. 이 원칙과 충돌 시 → 이 원칙 우선.

---

## 1. 범용성 보장

- 시스템은 어떤 주제·채널도 처리 가능해야 한다
- 채널 종속 코드 절대 금지 (코드에 채널명/인물명 하드코딩 금지)
- 모든 채널별 설정은 `profiles/{key}.yaml`로 분리
- 새 채널 추가 = YAML 파일 1개 추가로 충분

## 2. 자료 진실성

- 출처 없는 사실 주장 금지
- 인용구는 반드시 원전 명시 (`[SOURCE: ...]`)
- 할루시네이션 감지 시 즉시 `[NEED_VERIFY]` 태그 + Critic 차단
- Gemma/Gemini는 검증된 자료로만 대본 작업

## 3. 자동 연결 (Auto-Flow)

- Part간 수동 전달 금지
- `packet_router.auto_push_to_next_part()` 가 자동 처리:
  - Critic 검증 → Obsidian 저장 → Packet 빌드 → 다음 Part 전달
- 사용자는 방향 입력 + 최종 승인만 결정
- 실패 시 우측 SAGE 브레인이 자료 요청

## 4. 채널 정체성

- 매 영상 일관된 정체성 (`CHANNEL_IDENTITY.md` 적용)
- Profile + 이전 영상 자동 RAG
- 채널 진화는 데이터 누적 기반 (감에 의존하지 않음)

## 5. 떡상 지향 (Viral Targeting)

- 저구독·고조회 채널 벤치마킹 (구독자 1만↓, 조회 10만↑)
- 바이럴 지수 = `조회수 / 구독자` ≥ 5 기준
- 댓글 밀도 = `댓글수 / 조회수` 높은 채널 우선
- 정주행 신호 댓글: "끝까지", "여러 번", "또 봤", "정주행", "다시"
- 트렌드·알고리즘·키워드는 `TrendAnalyzer`가 자동 분석

---

## 에이전트 역할 분담

| 에이전트 | 역할 |
|---|---|
| Conductor | 파이프라인 지휘 + 상태 관리 |
| Librarian | 자료수집 + 댓글분석 + 주제발굴 |
| HitChannelFinder | 떡상 채널 발굴 + 벤치마킹 |
| TrendAnalyzer | 트렌드·알고리즘·키워드 분석 |
| Curator | RAG 검색 + 지식 정제 + 저장 |
| Scout | 자료 자동 보강 (Tavily/Gemini) |
| Critic | 4층 품질 검증 |
| QualityAssurance | 최종 출시 전 종합 점검 |

---

## 최종 완성 기준

```
✅ 어떤 채널에도 적용 가능
✅ Part간 자동 푸시 작동
✅ 결과물 옵시디언 자동 저장
✅ 다음 작업 시 이전 자료 자동 RAG
✅ 떡상 채널 자동 발굴
✅ 채널 정체성 일관 유지
✅ 3중 검증 (Critic + FactCheck + QA) 작동
✅ 며느리 시나리오 — 처음 켜도 막힘 없이 제작 가능
```
