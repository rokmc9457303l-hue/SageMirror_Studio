# [[오팔 롱폼 영상 제작 시스템 (Opal Longform Video System v5.0)]]

## 📌 Brief Summary
40-70대 타겟의 철학/심리 롱폼 콘텐츠를 위해 설계된 12단계 노드 기반의 자율 영상 제작 시스템입니다.

## 📖 Core Content
### 시스템 아키텍처 (12단계 노드)
1. **분석 및 기획**: 벤치마킹 노드를 통해 후킹 전략을 추출하고, 8챕터 구조의 감정 아크(Emotion Arc)를 설계합니다.
2. **지식 추출 (NotebookLM)**: '고통-치료-안식'으로 이어지는 철학적/성경적 지식의 정수를 추출하여 대본의 뼈대를 만듭니다.
3. **스토리보딩 및 샷 설계**: 총 96샷(8챕터 x 12샷)을 배분하며, 각 장면의 구도(Wide/Medium/Close-up)와 카메라 무브먼트 5종을 정의합니다.
4. **이미지 및 영상 생성**: Nano Banana Pro와 Veo 3.1을 활용하여 주인공 'Professor Lee'의 비주얼 일관성을 유지하며 8초 단위의 고퀄리티 영상을 생성합니다.
5. **통합 및 후반 작업**: TTS 음성과 자막(SRT)을 병합하여 최종 12~20분 분량의 완성본을 출력합니다.

### 제작 가이드 및 주의사항
- **비주얼 일관성**: Professor_Lee_Reference 시트를 활용하여 전 챕터에 걸쳐 캐릭터의 외형을 유지합니다.
- **검열 우회 전략**: AI 검열을 피하기 위해 철학자 이름이나 성경과 같은 직접적인 명칭 대신, 이를 은유적으로 묘사하는 프롬프트 엔지니어링을 적용합니다.
- **감정 전이**: 조명 온도를 3200K(고뇌)에서 6500K(각성)로 점진적으로 변화시켜 시청자의 심리적 변화를 유도합니다.

## 🔗 Knowledge Connections
- **Related Topics:** [[Sage_Mirror_Master_Workflow]], [[Nano_Banana_Expert]], [[YouTube_Thumbnail_Expert]]
- **Projects/Contexts:** [[Sage's Mirror (현자의 거울)]], [[Opal Project]]
- **Contradictions/Notes:** 본 시스템은 '공장형 제작'이 아닌 '작품형 제작'을 지향하며, 각 노드 간의 유기적 데이터 흐름이 품질을 결정합니다.


---
*Last updated: 2026-05-03*


---
🔙 [[00_현자의_지도(Master_Map)]]
