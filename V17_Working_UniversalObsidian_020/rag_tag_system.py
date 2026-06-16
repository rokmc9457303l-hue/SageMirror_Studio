import re

# ══════════════════════════════════════════════════════════════
# 🗂️ 현자의 거울 — RAG 검색 카테고리 분류 시스템 v1.0
# ══════════════════════════════════════════════════════════════

RAG_CATEGORY_MAP = {
    "🔴 핵심 감정": [
        "고독", "외로움", "고립", "소외", "단절", "혼자됨", "쓸쓸함",
        "후회", "회한", "자책", "죄책감", "미련", "아쉬움", "돌아봄",
        "상실", "죽음", "이별", "떠나보냄", "비어있음", "그리움",
        "공허", "허무", "무의미", "허탈", "무력감", "탈진",
        "슬픔", "우울", "절망", "무기력", "침묵", "체념",
        "분노", "억울함", "배신감", "상처", "원망", "서운함",
        "두려움", "불안", "걱정", "공포", "망설임", "회피",
        "수치심", "열등감", "자존감 붕괴", "부끄러움", "위축됨",
    ],
    "🟡 관계 심리": [
        "관계 단절", "가족 갈등", "부모 자식", "부부 갈등", "형제 단절",
        "친구 배신", "직장 인간관계", "오래된 관계", "관계 피로",
        "외면", "무시", "냉대", "거절", "버려짐", "선택받지 못함",
        "의존", "집착", "떠나지 못함", "관계 중독", "감정 소진",
        "혼자 남겨짐", "은퇴 후 고독", "빈둥지 증후군",
        "노년 고독", "황혼 이혼", "세대 갈등", "소통 단절",
    ],
    "🌑 다크심리학": [
        "가스라이팅", "현실 왜곡", "자존감 파괴", "심리 조종",
        "나르시시즘", "자기애적 학대", "지배 착취", "감정 착취",
        "정서적 방치", "냉담", "무관심 폭력", "감정 노예",
        "죄책감 유발", "수치심 주입", "조종자", "피해자화",
        "의존성 심화", "분리 불안", "심리적 학대",
        "공감 결여", "경계선 붕괴",
        "트라우마 결합", "복합 PTSD", "학습된 무기력",
        "독성 관계", "학대 사이클", "생존자 증후군",
    ],
    "🟣 쇼펜하우어": [
        "쇼펜하우어", "의지와 표상으로서의 세계", "맹목적 의지",
        "욕망의 허무", "고통의 근원", "의지 부정", "금욕주의",
        "권태와 고통", "염세주의", "비관주의", "고독의 철학",
        "천재와 고독", "동정심", "죽음과 의지",
        "미적 관조", "구원으로서의 예술", "쾌락의 환상",
        "마야의 베일", "세계 의지", "자아의 환상",
    ],
    "🟠 칼 융": [
        "칼 융", "분석심리학", "무의식", "집단 무의식",
        "그림자", "페르소나", "아니마", "아니무스",
        "자기실현", "개성화", "원형", "콤플렉스",
        "심리 유형", "내향", "외향", "공시성",
        "노년기 심리", "인생 후반", "중년 위기",
        "투사", "내면 아이", "억압된 감정",
        "상징과 꿈", "종교와 심리", "신화와 무의식",
    ],
    "🟤 빅터 프랭클": [
        "빅터 프랭클", "로고테라피", "의미치료", "죽음의 수용소에서",
        "삶의 의미", "의미 상실", "실존적 공허", "실존 분석",
        "비극적 낙관주의", "고통의 의미", "선택의 자유",
        "자기 초월", "자기 거리두기", "탈반성",
        "책임과 의미", "삶이 묻는 질문", "소명",
        "집단 신경증", "의미 없는 성공",
    ],
    "🌿 스토아 철학": [
        "스토아", "마르쿠스 아우렐리우스", "명상록", "에픽테토스",
        "세네카", "통제 이분법", "현재 집중",
        "감정 조절", "이성과 자연", "덕의 윤리",
        "죽음 명상", "메멘토 모리", "아모르 파티",
        "내면의 요새", "자연과의 조화", "판단 중지",
    ],
    "🍃 몽테뉴·에세이": [
        "몽테뉴", "수상록", "자기 탐구", "인간 본성",
        "불완전함의 수용", "자기 자신으로 살기",
        "경험의 철학", "회의주의", "관용", "자기 관찰",
        "일상의 철학", "죽음과 친해지기", "우정",
        "인간의 다양성", "솔직함", "자유로운 정신",
    ],
    "📖 성경": [
        "시편", "시편 23편", "시편 46편", "시편 91편", "시편 139편",
        "잠언", "잠언 3장", "잠언 31장",
        "전도서", "전도서 3장", "헛되고 헛되다", " 때의 철학",
        "욥기", "고통과 신앙", "욥의 인내", "시련의 의미",
        "이사야", "이사야 40장", "위로의 신학", "새 힘",
        "로마서", "로마서 8장", "고통과 영광", "연단",
        "고린도전서", "사랑장", "고린도후서", "약함의 은혜",
        "마태복음", "산상수훈", "걱정 말라", "용서",
        "누가복음", "돌아온 탕자", "자비", "화해",
        "히브리서", "믿음의 정의",
        "야고보서", "시험과 인내", "지혜 구하기",
    ],
    "🧠 심리학 일반": [
        "자존감", "자아 정체성", "정체성 혼란",
        "트라우마", "애착", "불안 애착", "회피 애착", "안정 애착",
        "번아웃", "소진", "정서 조절", "감정 표현",
        "방어기제", "억압", "투사", "합리화", "부정",
        "인지왜곡", "흑백논리", "과잉일반화", "재앙화",
        "자기효능감", "레질리언스", "회복탄력성",
        "노화 심리", "죽음 불안", "생의 의미",
    ],
    "🎭 인생 단계 (4070)": [
        "은퇴", "은퇴 후 정체성", "역할 상실", "직업 정체성",
        "노년기", "중년 위기", "인생 후반",
        "빈둥지", "자녀 독립", "부모 역할 종료",
        "건강 쇠퇴", "질병", "몸의 변화", "죽음 준비",
        "재정 불안", "노후 걱정", "경제적 불안",
        "인생 회고", "과거 정리", "남은 삶", "유산",
    ],
    "🌍 영적·실존": [
        "실존주의", "하이데거", "키르케고르",
        "죽음을 향한 존재", "본래성",
        "신앙", "영성", "기도", "묵상", "침묵",
        "용서와 화해", "회개", "은혜", "구원",
        "인생의 목적", "소명", "사명",
        "영원성", "내세", "부활", "희망",
    ],
}

PART_DEFAULT_CATEGORIES = {
    "part1": [
        "🔴 핵심 감정", "🟡 관계 심리", "🌑 다크심리학",
        "🟣 쇼펜하우어", "🟠 칼 융", "🟤 빅터 프랭클",
        "📖 성경", "🎭 인생 단계 (4070)",
    ],
    "part2": [
        "🌑 다크심리학", "🟣 쇼펜하우어", "🟠 칼 융",
        "🟤 빅터 프랭클", "🌿 스토아 철학", "🍃 몽테뉴·에세이",
        "📖 성경", "🔴 핵심 감정", "🌍 영적·실존",
    ],
    "part3": [
        "🔴 핵심 감정", "🌑 다크심리학", "📖 성경",
        "🟣 쇼펜하우어", "🍃 몽테뉴·에세이", "🌍 영적·실존",
    ],
    "part4": [
        "🔴 핵심 감정", "📖 성경", "🌍 영적·실존",
        "🟣 쇼펜하우어", "🌿 스토아 철학",
    ],
    "part5": [
        "🔴 핵심 감정", "🟡 관계 심리", "🌑 다크심리학",
        "📖 성경", "🎭 인생 단계 (4070)",
    ],
    "part6": [
        "🔴 핵심 감정", "📖 성경", "🌍 영적·실존",
        "🟤 빅터 프랭클", "🌿 스토아 철학",
    ],
    "part7": [
        "🔴 핵심 감정", "🌑 다크심리학", "📖 성경",
        "🎭 인생 단계 (4070)", "🟡 관계 심리",
    ],
    "part8": [
        "🔴 핵심 감정", "🌑 다크심리학", "📖 성경",
        "🟣 쇼펜하우어", "🟠 칼 융", "🟤 빅터 프랭클",
        "🌍 영적·실존", "🎭 인생 단계 (4070)",
    ],
}

PART_RAG_TAG_MAP = {
    "part1": ["Part1", "Librarian", "Benchmark", "TopicMemory", "자료조사"],
    "part2": ["Part2", "Alchemist", "Planning", "ResearchMemory", "총괄기획"],
    "part3": ["Part3", "Script", "Narration", "ScriptDrafts", "대본작성"],
    "part4": ["Part4", "ImagePrompt", "Visual", "Assets", "이미지생성"],
    "part5": ["Part5", "VideoPrompt", "Veo3", "Assets", "영상생성"],
    "part6": ["Part6", "Narration", "BGM", "Audio", "나레이션"],
    "part7": ["Part7", "Shorts", "Hooking", "ScriptDrafts", "숏폼생성"],
    "part8": ["Part8", "CapCut", "FinalAssembly", "Logs", "최종조립"],
}

PART_RAG_FOLDER_MAP = {
    "part1": "TopicMemory",
    "part2": "ResearchMemory",
    "part3": "ScriptDrafts",
    "part4": "Assets",
    "part5": "Assets",
    "part6": "ResearchMemory",
    "part7": "ScriptDrafts",
    "part8": "Logs",
}

def _unique_keep_order(items, limit=None):
    seen = set()
    out = []
    for item in items:
        if item is None:
            continue
        s = str(item).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
        if limit and len(out) >= limit:
            break
    return out

def get_default_tags_for_part(part_key: str) -> str:
    """파트별 기본 카테고리에서 태그 문자열 생성"""
    categories = PART_DEFAULT_CATEGORIES.get(part_key, list(RAG_CATEGORY_MAP.keys()))
    all_tags = []
    for cat in categories:
        all_tags.extend(RAG_CATEGORY_MAP.get(cat, []))
    # 중복 제거 후 최대 80개
    seen = set()
    unique = []
    for t in all_tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return ", ".join(unique[:80])

def detect_rag_categories(text: str, part_key: str = "part1", max_keywords: int = 80) -> dict:
    """RAG_CATEGORY_MAP 기준 자동 카테고리/키워드 감지 + 파트별 태그 부여."""
    text = text or ""
    text_lower = text.lower()
    matched_categories = []
    matched_keywords = []
    category_scores = {}

    for category, keywords in RAG_CATEGORY_MAP.items():
        found = []
        for kw in keywords:
            kw_s = str(kw).strip()
            if kw_s and kw_s.lower() in text_lower:
                found.append(kw_s)
        if found:
            matched_categories.append(category)
            matched_keywords.extend(found)
            category_scores[category] = len(found)

    if not matched_categories:
        matched_categories = PART_DEFAULT_CATEGORIES.get(part_key, [])[:3]
        for cat in matched_categories:
            matched_keywords.extend(RAG_CATEGORY_MAP.get(cat, [])[:5])
            category_scores[cat] = 0

    part_tags = PART_RAG_TAG_MAP.get(part_key, [part_key])
    keywords = _unique_keep_order(part_tags + matched_keywords, max_keywords)
    return {
        "part_key": part_key,
        "part_tags": part_tags,
        "categories": matched_categories,
        "category_scores": category_scores,
        "keywords": keywords,
        "wiki_links": [f"[[{k}]]" for k in keywords],
        "hash_tags": ["#" + re.sub(r"\s+", "_", k) for k in keywords],
    }

def build_rag_classification_markdown(detection: dict) -> str:
    """자동 분류 결과를 저장용 마크다운 섹션으로 변환."""
    cats = detection.get("categories", [])
    scores = detection.get("category_scores", {})
    part_tags = detection.get("part_tags", [])
    wiki_links = detection.get("wiki_links", [])
    hash_tags = detection.get("hash_tags", [])
    md = "## 🧠 자동 RAG 카테고리 분류\n"
    if cats:
        for cat in cats:
            md += f"- **{cat}** — 매칭 점수: {scores.get(cat, 0)}\n"
    else:
        md += "- 자동 감지된 카테고리 없음\n"
    md += "\n## 🏷️ 파트별 태그\n"
    md += ", ".join([f"#{t}" for t in part_tags]) if part_tags else "- 없음"
    md += "\n\n## 🔗 자동 연결 개념\n"
    md += "\n".join([f"- {w}" for w in wiki_links[:30]]) if wiki_links else "- 없음"
    md += "\n\n## #️⃣ 해시태그\n"
    md += " ".join(hash_tags[:40]) if hash_tags else "- 없음"
    md += "\n"
    return md
