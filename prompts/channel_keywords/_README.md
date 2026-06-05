# channel_keywords/ 폴더 사용 안내

이 폴더는 v18의 다채널 분류 시스템 키워드 사전입니다.

## 파일 종류

- `_universal.json` : 모든 채널 공통 범용 카테고리 (감정/인생주제/세대 등 7개)
- `_production.json` : 모든 채널 공통 제작 메타 카테고리
- `_template.json` : 새 채널 만들 때 복사용 빈 템플릿
- `현자의거울.json` : 채널 1 (활성)
- `_slot_02_예약.json` : 비어있는 채널 슬롯 (사용 시 enabled: true로)
- `_slot_03_예약.json` : 비어있는 채널 슬롯

## 새 채널 추가 방법 (코드 수정 없음)

1. `_template.json`을 복사해서 `(채널이름).json`으로 저장
2. channel_id, concept, drive_folder, domains 값을 채우기
3. enabled를 true로 변경
4. Google Drive에 `(채널이름)_자료` 폴더 생성
5. 끝 — 시스템이 자동 인식

## 비활성 슬롯 깨우기

`_slot_02_예약.json` 파일명을 `(채널이름).json`으로 바꾸고
내부 값들을 채운 뒤 enabled: true로 변경.
