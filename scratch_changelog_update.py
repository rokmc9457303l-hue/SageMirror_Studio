import codecs

log = '''
## V17 Agent School + Left Sidebar 023

* 기준 작업본: V17_Working_UniversalObsidian_022
* 새 작업본: V17_Working_UniversalObsidian_023
* 작업 범위:
  * Agent Campus / School Registry 기초 생성
  * Part 1~8 Agent 자리 등록
  * Prompt MD 경로 구조 준비
  * Packet Queue / Command Router 기초 생성
  * 좌측바 학교 상태 연결
  * 좌측바 기본 노출 정리
* 공식 실행 주소: http://localhost:8518
* GitHub Push: 하지 않음
* 다음 예정 작업:
  * 설정창 범용화
  * 채널명 직접 수정 기능 강화
  * Part 1~8 프롬프트 MD 본문 작성
  * Gemma 공장장 프로토콜 본문 작성
  * 우측 대화창 “시작해” 명령 실제 연결
'''

with codecs.open(r'C:\SageMirror_Production\00_History\CHANGELOG.md', 'a', 'utf-8-sig') as f:
    f.write(log)
