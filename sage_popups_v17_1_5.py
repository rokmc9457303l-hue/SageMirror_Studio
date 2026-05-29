# -*- coding: utf-8 -*-
"""
sage_popups.py — 팝업 다이얼로그 v3.1
[v3.1 업그레이드: 2026-05-26]
- Agent Layer Separation Phase 1 (Research Router) 연동
- Tavily 검색 및 태그 디텍션 동작 위임
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from sage_config import (
    DEFAULT_OBSIDIAN_RULES, DEFAULT_BASE_PROMPT,
    SAGE_PERSONA, OLLAMA_MODEL,
)
from sage_engine import call_gemma, call_gemma_stream, tavily_search, check_ollama_status
from research_router import (
    should_trigger_research,
    run_tavily_research,
    clean_search_query,
    format_search_results_markdown,
    build_tavily_rag_context_core,
    format_source_citation,
)
from agent_toolkit import (
    normalize_tool_name,
    format_tool_result,
    get_supported_agent_tools,
    format_check_source_result,
    format_search_web_result,
    format_save_obsidian_result,
)
from agent_registry import get_tool_metadata

# ─── 상수 ───
AVAILABLE_MODELS = ["gemma4:e2b", "gemma4:e4b"]

# 범용 12개 카테고리 태그 분류 시스템 (다채널 운영용)
UNIVERSAL_CATEGORY_TAGS = {
    "감정": ["고독", "후회", "불안", "기쁨", "분노", "소망", "외로움",
             "상실", "슬픔", "공허", "두려움", "희망", "용기", "감사",
             "loneliness", "anxiety", "grief", "fear", "hope"],
    "철학": ["쇼펜하우어", "스토아", "실존주의", "니체", "칸트", "소크라테스",
             "동양철학", "노자", "장자", "불교", "하이데거", "몽테뉴",
             "프랭클", "융", "philosophy", "stoic"],
    "성경·신앙": ["시편", "잠언", "전도서", "욥기", "이사야", "신약",
                  "기도", "회복", "은혜", "성경", "bible", "psalm"],
    "심리학": ["자존감", "관계", "트라우마", "애착", "번아웃", "나르시시즘",
               "가스라이팅", "회복탄력성", "마음챙김", "인지행동",
               "psychology", "trauma", "resilience"],
    "역사": ["인물", "사건", "시대", "문명", "전쟁", "문화", "역사",
             "history", "civilization"],
    "경제·비즈니스": ["돈", "은퇴", "부업", "투자", "시장", "직업",
                      "재테크", "창업", "경제", "economy", "business"],
    "건강·생활": ["수면", "운동", "식습관", "노년", "건강", "라이프",
                  "wellness", "health", "lifestyle"],
    "유튜브전략": ["제목", "썸네일", "후킹", "알고리즘", "시청지속",
                   "youtube", "thumbnail", "hook", "retention"],
    "채널운영": ["채널", "타겟", "페르소나", "콘텐츠", "포맷", "구독",
                 "channel", "content", "persona"],
    "제작자료": ["이미지", "영상", "나레이션", "BGM", "캡컷", "대본",
                 "script", "narration", "video", "image"],
    "출처자료": ["책", "논문", "기사", "PDF", "웹", "연구", "출처",
                 "book", "research", "article", "source"],
    "에피소드": ["EP001", "EP002", "EP003", "에피소드", "episode",
                 "롱폼", "숏폼", "shorts"],
}

# 파트별 컨텍스트 맵
PART_CONTEXT_MAP = {
    "part1": {
        "name": "Part 1 — Librarian (벤치마킹 & 타겟 분석)",
        "keys": ["p1_topic_selection", "p1_bench_result", "p1_research_result", "p1_planning_result"],
        "desc": "유튜브 채널 벤치마킹, 타겟 분석, 주제 선정, 기획안 작성 파트",
        "obsidian_folder": "Part1_Librarian",
    },
    "part2": {
        "name": "Part 2 — Alchemist (철학·감정 융합)",
        "keys": ["p2_topic_selection", "p2_research_result", "p2_planning_result"],
        "desc": "성경-철학-에세이 3원 융합 자료조사 및 총괄 기획안 작성 파트",
        "obsidian_folder": "Part2_Alchemist",
    },
    "part34": {
        "name": "Part 3-4 — Architect & Writer (대본 설계)",
        "keys": ["p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data"],
        "desc": "112씬 구조 설계, 나레이션/이미지/캡컷 대본 집필 파트",
        "obsidian_folder": "Part34_Writer",
    },
    "part5": {
        "name": "Part 5 — Image Consistency (구글 플로우 연동)",
        "keys": ["p5_a_result", "p5_b_result", "p5_c_results"],
        "desc": "@Protagonist 일관성 확보 및 이미지 프롬프트 최종 검증 파트",
        "obsidian_folder": "Part5_Image",
    },
    "part5img": {
        "name": "Part 5 — Image Generation (이미지 생성)",
        "keys": ["p5_a_result", "p5_c_results"],
        "desc": "이미지 생성 및 검증 파트",
        "obsidian_folder": "Part5_Image",
    },
    "part6": {
        "name": "Part 6 — Narration & BGM",
        "keys": ["p34_narration_script"],
        "desc": "CosyVoice 나레이션 생성 및 BGM 배분 파트",
        "obsidian_folder": "Part6_Narration",
    },
    "part7": {
        "name": "Part 7 — CapCut Bridge (캡컷 자동 조립)",
        "keys": ["p34_capcut_data", "p34_image_script"],
        "desc": "캡컷 에셋 자동 조립 및 타임라인 배분 파트",
        "obsidian_folder": "Part7_CapCut",
    },
    "part8": {
        "name": "Part 8 — Final Assembly (최종 완성)",
        "keys": [],
        "desc": "전체 파이프라인 결과물 최종 검토 및 업로드 준비 파트",
        "obsidian_folder": "Part8_Final",
    },
}


# ══════════════════════════════════════════════════════════════════════
# 핵심 유틸리티 함수들
# ══════════════════════════════════════════════════════════════════════

def _get_current_part() -> str:
    """현재 선택된 파트를 세션 스테이트에서 읽어옴"""
    return st.session_state.get("sidebar_part", "part1")


def _build_part_context(part_key: str) -> str:
    """현재 파트의 데이터를 컨텍스트 문자열로 변환"""
    info = PART_CONTEXT_MAP.get(part_key, PART_CONTEXT_MAP["part1"])
    ctx = f"[현재 작업 파트: {info['name']}]\n{info['desc']}\n\n"
    ctx += "[현재 파트 세션 데이터 (작업 참조용)]\n"
    for k in info["keys"]:
        val = st.session_state.get(k, "")
        if val:
            val_str = str(val)[:600] + ("..." if len(str(val)) > 600 else "")
            ctx += f"- {k}:\n{val_str}\n\n"
    return ctx


def _build_obsidian_rag_context() -> str:
    """옵시디언 저장 자료 중 최근 세션 데이터를 컨텍스트로 읽어옴"""
    ctx = "[옵시디언 RAG 최근 자료 요약]\n"
    vault_root = Path(r"C:\SageMirror_Production\00_Obsidian")
    if not vault_root.exists():
        return ctx + "(옵시디언 자료 없음)\n"
    try:
        md_files = sorted(vault_root.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        loaded = 0
        for mf in md_files[:8]:
            try:
                content = mf.read_text(encoding="utf-8", errors="ignore")
                ctx += f"\n### [{mf.parent.name}/{mf.stem}]\n{content[:400]}...\n"
                loaded += 1
            except Exception:
                continue
        if loaded == 0:
            ctx += "(최근 저장된 옵시디언 파일 없음)\n"
    except Exception as e:
        ctx += f"(옵시디언 파일 읽기 오류: {e})\n"
    return ctx


def call_gemini_search(keyword: str, api_key: str, model_name: str = "gemini-2.5-flash") -> dict:
    try:
        import google.generativeai as genai
        import re as _re
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            tools="google_search"
        )
        prompt = f"""
[지시]
입력된 키워드 '{keyword}'에 대해 구글 검색을 수행하고, 그 결과를 바탕으로 사실 위주의 풍부한 리서치 조사 정보를 작성하라.
특히, 각 구체적인 사실 또는 문장 근처에 정보 출처 웹사이트의 URL을 매치하여 자세히 명시하라.

[검색 키워드]
{keyword}
"""
        response = model.generate_content(prompt)
        text_content = response.text if hasattr(response, "text") else ""
        
        results = []
        try:
            metadata = response.grounding_metadata
            chunks = getattr(metadata, "grounding_chunks", [])
            for chunk in chunks:
                web = getattr(chunk, "web", None)
                if web:
                    uri = getattr(web, "uri", "")
                    title = getattr(web, "title", "웹 검색 출처")
                    if uri and not any(r.get("url") == uri for r in results):
                        results.append({
                            "title": title,
                            "url": uri,
                            "content": f"구글 검색 출처: {title}"
                        })
        except Exception:
            pass
            
        if not results:
            urls = _re.findall(r'https?://[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/))', text_content)
            for idx, url in enumerate(list(set(urls))[:5], 1):
                results.append({
                    "title": f"구글 검색 결과 {idx}",
                    "url": url,
                    "content": "구글 검색을 통해 참조된 웹 페이지입니다."
                })
                
        return {
            "summary": text_content,
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def _build_tavily_rag_context() -> str:
    """저장된 Tavily 검색 결과를 젬마 컨텍스트로 반환"""
    history = st.session_state.get("popup_search_history", [])
    return build_tavily_rag_context_core(history)


def _classify_universal_tags(text: str) -> dict:
    """텍스트에서 범용 카테고리 태그를 자동 분류"""
    text_lower = text.lower()
    matched = {}
    for category, keywords in UNIVERSAL_CATEGORY_TAGS.items():
        found = [kw for kw in keywords if kw.lower() in text_lower]
        if found:
            matched[category] = found
    return matched


def _save_to_obsidian_with_tags(
    content: str,
    title: str,
    source_type: str,
    part_key: str,
    model_name: str,
    extra_tags: list = None,
    folder_override: str = None
) -> str | None:
    """
    옵시디언에 심리학 태그 세분화하여 자동 저장.
    - 감정 태그 자동 분류
    - 채널 전용 태그 + 범용 태그 동시 생성
    - 각 파트 옵시디언 규칙서 참조
    """
    try:
        part_info = PART_CONTEXT_MAP.get(part_key, PART_CONTEXT_MAP["part1"])
        obsidian_folder = folder_override or part_info.get("obsidian_folder", "General")

        # 범용 카테고리 태그 자동 분류
        emotion_tags = _classify_universal_tags(content + " " + title)

        # 젬마로 키워드 추출
        kw_prompt = f"""아래 내용에서 옵시디언 RAG 태그로 사용할 핵심 키워드 6~8개를 쉼표로만 출력하라.
다양한 채널에서 활용 가능한 범용 태그로 주제, 감정, 분야, 인물, 개념을 포함할 것.
예시: 고독, 쇼펜하우어, 자아성찰, 심리치유, 은퇴준비, 역사인물, 유튜브전략, 건강생활

[내용]
{content[:600]}

[KEYWORDS]:"""
        try:
            kw_raw = call_gemma(kw_prompt, model=model_name)
            tag_list = [t.strip() for t in kw_raw.replace("#", "").split(",") if t.strip()][:8]
        except Exception:
            tag_list = ["세이지대화", "자료조사", "옵시디언저장", "범용자료"]

        if extra_tags:
            tag_list = list(set(tag_list + extra_tags))

        # 태그 포맷 생성
        tag_links = " ".join([f"[[{t}]]" for t in tag_list])
        tag_hashes = " ".join([f"#{t.replace(' ', '_')}" for t in tag_list])

        # 감정 분류 섹션 생성
        emotion_section = ""
        if emotion_tags:
            emotion_section = "\n## 🎭 감정 태그 분류 (자동)\n"
            for cat, found_kws in emotion_tags.items():
                cat_tag = cat.replace("·", "_").replace(" ", "_")
                emotion_section += f"- **{cat}**: {', '.join(found_kws)} → #{cat_tag}\n"
                tag_hashes += f" #{cat_tag}"

        # 파트 옵시디언 규칙서 참조 정보
        obs_rules_ref = st.session_state.get("obsidian_rules", "")
        obs_rules_summary = obs_rules_ref[:200] + "..." if len(obs_rules_ref) > 200 else obs_rules_ref

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content_md = f"""# [[{title}]]

## 📌 핵심 요약
- 

## 🗂️ 분류 정보
- 대분류: {list(emotion_tags.keys())[0] if emotion_tags else "미분류"}
- 채널:
- 에피소드:
- 활용 파트: {part_info['name']}

## 메타데이터
- **소스 유형**: {source_type}
- **파트**: {part_info['name']}
- **모델**: {model_name}
- **저장 시각**: {today_str}
- **옵시디언 폴더**: {obsidian_folder}

## 🎯 핵심 키워드 / RAG 태그
- **개념 링크**: {tag_links}
- **해시 태그**: {tag_hashes}
{emotion_section}

## 📋 옵시디언 규칙서 참조 (파트 기준)
> {obs_rules_summary}

## 📖 내용

{content}

## 🔗 파이프라인 연결
- **출처 파트**: {part_info['name']}
- **소스 유형**: {source_type}
- **저장 모델**: {model_name}
- **활용 가능 파트**: 전체 (RAG 태그 기반 자동 검색)

---
*[SOURCE: {source_type} — {model_name} 처리, {today_str}]*
*저장 경로: {obsidian_folder}/{title[:30]}_{ts}.md*
"""

        # 저장 경로 결정
        save_dir = Path(r"C:\SageMirror_Production\00_Obsidian") / obsidian_folder
        save_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c for c in title[:40] if c.isalnum() or c in " -_[]()").strip()
        save_path = save_dir / f"{safe_title}_{ts}.md"
        save_path.write_text(content_md, encoding="utf-8")

        # 전체 태그 인덱스에도 추가 (범용 검색용)
        tag_index_dir = Path(r"C:\SageMirror_Production\00_Obsidian\TagIndex")
        tag_index_dir.mkdir(parents=True, exist_ok=True)
        for tag in tag_list[:5]:
            safe_tag = "".join(c for c in tag if c.isalnum() or c in "-_").strip()
            if safe_tag:
                tag_file = tag_index_dir / f"tag_{safe_tag}.md"
                existing = tag_file.read_text(encoding="utf-8", errors="ignore") if tag_file.exists() else f"# 태그: {tag}\n\n## 연결 문서\n"
                existing += f"- [[{obsidian_folder}/{save_path.stem}]] — {today_str}\n"
                tag_file.write_text(existing, encoding="utf-8")

        # ── Recent Activity Dynamic Sync ──
        try:
            from rag_memory_utils import update_recent_activity_memory
            state_dict = dict(st.session_state)
            updated_mem = update_recent_activity_memory(state_dict, "obsidian", f"Obsidian 저장: {save_path.name}")
            st.session_state.recent_activity_memory = updated_mem
        except Exception:
            pass

        return str(save_path)

    except Exception as e:
        return None



# ══════════════════════════════════════════════════════════════════════
# 📎 파일 업로드 → RAG 카테고리/태그 자동 분류 → 옵시디언 저장 헬퍼
# ══════════════════════════════════════════════════════════════════════

FILE_RAG_CATEGORY_KEYWORDS = {
    "🔴 핵심 감정": ["고독", "외로움", "상실", "후회", "공허", "허무", "불안", "분노", "수치", "자존감"],
    "🟡 관계 심리": ["관계", "가족", "부부", "친구", "직장", "갈등", "소통", "단절", "의존", "집착"],
    "🌑 다크심리학": ["가스라이팅", "나르시시즘", "조종", "정서적 방치", "착취", "트라우마", "학습된 무기력"],
    "🟣 쇼펜하우어": ["쇼펜하우어", "의지", "표상", "욕망", "권태", "염세", "고통"],
    "🟠 칼 융": ["칼 융", "융", "그림자", "페르소나", "무의식", "개성화", "원형"],
    "🟤 빅터 프랭클": ["빅터 프랭클", "프랭클", "로고테라피", "의미치료", "삶의 의미", "실존적 공허"],
    "🌿 스토아 철학": ["스토아", "마르쿠스", "에픽테토스", "세네카", "통제", "메멘토 모리", "아모르 파티"],
    "🍃 몽테뉴·에세이": ["몽테뉴", "수상록", "에세이", "자기 탐구", "불완전함", "자기 관찰"],
    "📖 성경": ["시편", "잠언", "전도서", "욥기", "이사야", "로마서", "마태복음", "누가복음", "야고보서", "성경"],
    "🧠 심리학 일반": ["심리", "자존감", "트라우마", "애착", "번아웃", "인지왜곡", "회복탄력성"],
    "🎭 인생 단계 (4070)": ["은퇴", "노년", "중년", "빈둥지", "자녀 독립", "건강", "죽음 준비", "노후"],
    "🌍 영적·실존": ["실존", "신앙", "영성", "기도", "묵상", "용서", "회개", "은혜", "구원", "소명"],
}

PART_UPLOAD_TAGS = {
    "part1": ["Part1", "Librarian", "Benchmark", "TopicMemory"],
    "part2": ["Part2", "Alchemist", "Research", "PlanningMemory"],
    "part34": ["Part3", "Part4", "Script", "Narration", "ScriptDrafts"],
    "part5": ["Part5", "Image", "Visual", "Assets"],
    "part5img": ["Part5", "Image", "Visual", "Assets"],
    "part6": ["Part6", "Narration", "BGM", "Audio"],
    "part7": ["Part7", "Shorts", "CapCut", "ScriptDrafts"],
    "part8": ["Part8", "FinalAssembly", "Logs"],
}

def _detect_file_rag_categories(text: str) -> dict:
    """업로드 파일 내용에서 RAG 카테고리와 키워드를 자동 감지한다."""
    if not text:
        return {}
    t = text.lower()
    detected = {}
    for category, keywords in FILE_RAG_CATEGORY_KEYWORDS.items():
        hits = []
        for kw in keywords:
            if kw.lower() in t:
                hits.append(kw)
        if hits:
            detected[category] = hits[:12]
    return detected

def _read_uploaded_file_text(uploaded_file) -> tuple[str, str]:
    """Streamlit uploaded_file에서 텍스트를 안전하게 추출한다."""
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    raw = uploaded_file.getvalue()
    if suffix in [".txt", ".md", ".csv", ".json", ".py", ".srt", ".vtt", ".html", ".xml"]:
        for enc in ["utf-8", "cp949", "euc-kr"]:
            try:
                return raw.decode(enc, errors="ignore"), suffix
            except Exception:
                continue
        return raw.decode("utf-8", errors="ignore"), suffix
    if suffix == ".pdf":
        try:
            import io
            try:
                from pypdf import PdfReader
            except Exception:
                from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            pages = []
            for page in reader.pages[:80]:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pass
            return "\n\n".join(pages), suffix
        except Exception as e:
            return f"[PDF 텍스트 추출 실패: {e}]", suffix
    return f"[지원하지 않는 파일 형식: {suffix}]", suffix

def _build_uploaded_file_memory_markdown(
    filename: str,
    file_text: str,
    gemma_analysis: str,
    detected_categories: dict,
    part_key: str,
    model_name: str,
    destination_folder: str,
) -> tuple[str, list]:
    """업로드 파일 저장용 마크다운과 태그 목록 생성."""
    part_info = PART_CONTEXT_MAP.get(part_key, PART_CONTEXT_MAP["part1"])
    part_tags = PART_UPLOAD_TAGS.get(part_key, [part_key])
    detected_tags = []
    for cat, hits in detected_categories.items():
        detected_tags.append(cat.replace(" ", "_"))
        detected_tags.extend(hits)
    final_tags = []
    seen = set()
    for tag in part_tags + detected_tags + ["파일업로드", "RAG분류", "현자의거울"]:
        clean = str(tag).strip()
        if clean and clean not in seen:
            seen.add(clean)
            final_tags.append(clean)

    cat_md = ""
    if detected_categories:
        for cat, hits in detected_categories.items():
            cat_md += f"- **{cat}**: {', '.join(hits)}\n"
    else:
        cat_md = "- 자동 감지된 카테고리 없음. 젬마 분석 결과를 참고하십시오.\n"

    excerpt = file_text[:3500] + ("\n..." if len(file_text) > 3500 else "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = f"""# [[업로드 자료 — {filename}]]

## 📌 메타데이터
- **파일명**: {filename}
- **저장 위치**: {destination_folder}
- **현재 파트**: {part_info['name']}
- **사용 모델**: {model_name}
- **생성일**: {now}

## 🏷️ 파트별 태그
{' '.join([f'[[{t}]]' for t in part_tags])}

## 🗂️ 자동 감지 RAG 카테고리
{cat_md}
## 🔗 자동 태그
{' '.join([f'[[{t}]]' for t in final_tags])}

## 🤖 Gemma 분석 요약
{gemma_analysis}

## 📖 원문 발췌
```text
{excerpt}
```

## 다음 파트 전달 메모
이 자료는 {part_info['name']}에서 업로드되어 RAG 기억으로 저장되었으며, 향후 TopicMemory / ResearchMemory / References 검색에 재사용할 수 있습니다.

## 📚 출처
[SOURCE: 사용자 업로드 파일 — {filename} — {now}]
"""
    return md, final_tags

def _apply_part_action(part_key: str, instruction: str, response: str) -> str | None:
    """젬마 지시에 따라 해당 파트 세션 데이터를 직접 수정"""
    inst_lower = instruction.lower()
    info = PART_CONTEXT_MAP.get(part_key, {})
    keys = info.get("keys", [])

    if any(k in inst_lower for k in ["나레이션", "narration", "나레"]):
        if "p34_narration_script" in keys and len(response) > 50:
            st.session_state.p34_narration_script = response
            return "✅ 나레이션 대본이 업데이트되었습니다."

    if any(k in inst_lower for k in ["기획안", "planning", "기획"]):
        if "p2_planning_result" in keys and len(response) > 50:
            st.session_state.p2_planning_result = response
            return "✅ 총괄 기획안이 업데이트되었습니다."
        elif "p1_planning_result" in keys and len(response) > 50:
            st.session_state.p1_planning_result = response
            return "✅ 기획안이 업데이트되었습니다."

    if any(k in inst_lower for k in ["이미지", "image script", "c-1"]):
        if "p34_image_script" in keys and len(response) > 50:
            st.session_state.p34_image_script = response
            return "✅ 이미지 대본이 업데이트되었습니다."

    if any(k in inst_lower for k in ["씬구조", "씬 구조", "scene structure", "112씬"]):
        if "p34_scene_structure" in keys and len(response) > 50:
            st.session_state.p34_scene_structure = response
            return "✅ 씬 구조가 업데이트되었습니다."

    return None


def _on_popup_send():
    q = st.session_state.get("popup_chat_input_ta", "")
    if q.strip():
        st.session_state.popup_history.append({"role": "user", "content": q})
        st.session_state.pending_stream = q
        st.session_state.popup_chat_input_ta = ""
        # ── Recent Activity Dynamic Sync ──
        try:
            from rag_memory_utils import update_recent_activity_memory
            state_dict = dict(st.session_state)
            updated_mem = update_recent_activity_memory(state_dict, "question", q)
            st.session_state.recent_activity_memory = updated_mem
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════
# 옵시디언 규칙서 편집 팝업
# ══════════════════════════════════════════════════════════════════════
@st.dialog("📚 옵시디언 규칙서 — 상세 편집", width="large")
def popup_edit_obsidian():
    st.caption("성경·철학·에세이 참조 원칙 (모든 파트의 Gemma 호출 시스템 컨텍스트로 주입)")
    with st.container(height=350, border=True):
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;"
            f"padding:8px;font-family:Pretendard,Noto Sans KR,sans-serif;'>"
            f"{st.session_state.obsidian_rules}</div>",
            unsafe_allow_html=True,
        )
    new_val = st.text_area(
        "옵시디언 규칙서 본문", value=st.session_state.obsidian_rules,
        height=280, key="popup_obsidian_edit_ta", label_visibility="collapsed",
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💾 저장", use_container_width=True, type="primary", key="ob_save"):
            st.session_state.obsidian_history.append(st.session_state.obsidian_rules)
            st.session_state.obsidian_rules = new_val
            st.session_state.top_ob_view_widget = new_val
            try:
                import sys
                import importlib
                app_module = None
                for mod_name in list(sys.modules.keys()):
                    if mod_name.startswith('app_v') and hasattr(sys.modules[mod_name], 'save_workspace_state'):
                        app_module = sys.modules[mod_name]
                        break
                if app_module is None:
                    app_module = importlib.import_module("app_v17_1_4C")
                app_module.save_workspace_state()
            except Exception:
                pass
            try:
                from rag_memory_utils import update_recent_activity_memory
                st.session_state.recent_activity_memory = update_recent_activity_memory(dict(st.session_state), "system", "옵시디언 규칙서 수정")
            except: pass
            st.toast("✅ 옵시디언 규칙서 저장 완료", icon="✅")
            st.rerun()
    with c2:
        if st.button(f"⬅️ 뒤로 ({len(st.session_state.obsidian_history)})",
                     use_container_width=True, key="ob_back",
                     disabled=len(st.session_state.obsidian_history) == 0):
            st.session_state.obsidian_rules = st.session_state.obsidian_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 기본값", use_container_width=True, key="ob_reset"):
            st.session_state.obsidian_history.append(st.session_state.obsidian_rules)
            st.session_state.obsidian_rules = DEFAULT_OBSIDIAN_RULES
            st.rerun()
    with c4:
        st.download_button(
            "📥 .md", data=st.session_state.obsidian_rules,
            file_name=f"obsidian_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            use_container_width=True, key="ob_dl",
        )


# ══════════════════════════════════════════════════════════════════════
# 기본 프롬프트 편집 팝업
# ══════════════════════════════════════════════════════════════════════
@st.dialog("🎯 기본 프롬프트 편집", width="large")
def popup_edit_prompt():
    st.caption("Part 1 Librarian의 채널 선정 원칙.")
    with st.container(height=350, border=True):
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.7;color:#f5e9d3;"
            f"padding:8px;'>{st.session_state.base_prompt_rules}</div>",
            unsafe_allow_html=True,
        )
    new_val = st.text_area(
        "기본 프롬프트 본문", value=st.session_state.base_prompt_rules,
        height=280, key="popup_prompt_edit_ta", label_visibility="collapsed",
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💾 저장", use_container_width=True, type="primary", key="pr_save"):
            st.session_state.prompt_history.append(st.session_state.base_prompt_rules)
            st.session_state.base_prompt_rules = new_val
            st.session_state["top_pr_view_base_prompt_rules_widget"] = new_val
            try:
                import sys
                import importlib
                app_module = None
                for mod_name in list(sys.modules.keys()):
                    if mod_name.startswith('app_v') and hasattr(sys.modules[mod_name], 'save_workspace_state'):
                        app_module = sys.modules[mod_name]
                        break
                if app_module is None:
                    app_module = importlib.import_module("app_v17_1_4C")
                app_module.save_workspace_state()
            except Exception:
                pass
            try:
                from rag_memory_utils import update_recent_activity_memory
                st.session_state.recent_activity_memory = update_recent_activity_memory(dict(st.session_state), "system", "기본 프롬프트 수정")
            except: pass
            st.toast("✅ 기본 프롬프트 저장 완료", icon="✅")
            st.rerun()
    with c2:
        if st.button(f"⬅️ 뒤로 ({len(st.session_state.prompt_history)})",
                     use_container_width=True, key="pr_back",
                     disabled=len(st.session_state.prompt_history) == 0):
            st.session_state.base_prompt_rules = st.session_state.prompt_history.pop()
            st.rerun()
    with c3:
        if st.button("🔄 기본값", use_container_width=True, key="pr_reset"):
            st.session_state.prompt_history.append(st.session_state.base_prompt_rules)
            st.session_state.base_prompt_rules = DEFAULT_BASE_PROMPT
            st.rerun()
    with c4:
        st.download_button(
            "📥 .txt", data=st.session_state.base_prompt_rules,
            file_name=f"base_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            use_container_width=True, key="pr_dl",
        )


# ══════════════════════════════════════════════════════════════════════
# ⚙️ 파트 작업 지시 — 대형 팝업 다이얼로그 (NEW v3.0)
# ══════════════════════════════════════════════════════════════════════
@st.dialog("⚙️ 파트 직접 작업 지시 — Gemma AI 작업 실행", width="large")
def popup_part_action_dialog():
    """파트 작업 지시 전용 대형 팝업 — 젬마 직접 작업, 세션 자동 적용"""

    current_part_key = _get_current_part()
    current_part_info = PART_CONTEXT_MAP.get(current_part_key, PART_CONTEXT_MAP["part1"])
    current_part_name = current_part_info["name"]
    current_model = st.session_state.get("popup_selected_model", OLLAMA_MODEL)

    # 파트 배지
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#1a3a5c,#0d2240);border-left:4px solid #d4af6a;"
        f"padding:10px 16px;border-radius:0 8px 8px 0;margin-bottom:12px;'>"
        f"<b style='color:#d4af6a;font-size:1.1rem;'>📍 {current_part_name}</b><br>"
        f"<span style='color:#aaa;font-size:0.85rem;'>{current_part_info['desc']}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # 현재 파트 데이터 현황 (확장 가능)
    with st.expander("📋 현재 파트 데이터 현황 (클릭해서 열기)", expanded=False):
        part_ctx = _build_part_context(current_part_key)
        with st.container(height=250, border=True):
            st.markdown(part_ctx)
        st.download_button(
            "📥 파트 데이터 다운로드",
            data=part_ctx,
            file_name=f"part_context_{current_part_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            key="part_action_dl_ctx",
            use_container_width=True,
        )

    st.divider()

    # 기능 탭
    tab_a, tab_b, tab_c, tab_d = st.tabs([
        "🚀 AI 작업 실행",
        "✏️ 직접 수정 / 주입",
        "🧩 파트 간 연결",
        "📊 작업 이력"
    ])

    # ─── 탭 A: AI 작업 실행 ───
    with tab_a:
        st.markdown("##### 🎯 젬마에게 작업 지시")
        st.caption("자유롭게 작업을 지시하세요. 젬마가 현재 파트 데이터 + 옵시디언 + 인터넷 자료를 모두 참조하여 실행합니다.")

        # 빠른 지시 템플릿
        st.markdown("**⚡ 빠른 지시 템플릿 (클릭 → 자동 입력)**")
        quick_cmds = {
            "나레이션 개선": "현재 나레이션 대본의 감성을 더 따뜻하고 묵직하게 개선해줘. 60대 현자의 목소리로.",
            "기획안 보완": "현재 기획안에 성경 구절과 철학자 인용구를 각 1개씩 추가해줘. 출처 명기 필수.",
            "씬 구조 점검": "현재 112씬 구조에서 감정 흐름(기-승-전-결)이 자연스러운지 분석하고 개선안을 제시해줘.",
            "옵시디언 태그 생성": "현재 파트의 모든 내용을 분석하여 옵시디언 RAG 태그 10개를 생성해줘.",
            "이미지 대본 점검": "이미지 대본의 C-1 형식이 올바른지 검수하고 문제있는 씬을 수정해줘.",
        }
        cols = st.columns(3)
        for i, (label, cmd) in enumerate(quick_cmds.items()):
            with cols[i % 3]:
                if st.button(f"⚡ {label}", key=f"quick_cmd_{i}", use_container_width=True):
                    st.session_state.part_action_quick_input = cmd

        # 작업 지시 입력창
        default_input = st.session_state.get("part_action_quick_input", "")
        action_instruction = st.text_area(
            "🎯 작업 지시 (자유 입력)",
            value=default_input,
            placeholder=(
                "예: Part 3-4 나레이션 대본의 첫 번째 씬을 더 따뜻한 톤으로 다시 작성해줘\n"
                "예: 총괄 기획안에 시편 23편 구절을 추가해줘\n"
                "예: 이미지 대본의 씬 001 한글 묘사를 수정해줘\n"
                "예: 현재 주제로 유튜브 제목 5개를 추천해줘"
            ),
            height=120,
            key="part_action_main_input",
            label_visibility="collapsed",
        )
        # 빠른 입력 상태 초기화
        if st.session_state.get("part_action_quick_input"):
            st.session_state.part_action_quick_input = ""

        # 옵션 설정
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        with col_opt1:
            use_obs_rag = st.checkbox("🧠 옵시디언 RAG 참조", value=True, key="paw_use_obs")
        with col_opt2:
            use_tavily_rag = st.checkbox("🌐 인터넷 자료 참조", value=True, key="paw_use_tavily")
        with col_opt3:
            auto_apply = st.checkbox("⚙️ 결과 자동 적용", value=False, key="paw_auto_apply")

        col_run1, col_run2 = st.columns(2)
        with col_run1:
            run_action = st.button(
                "🚀 작업 실행 (AI)",
                type="primary", use_container_width=True, key="part_action_run_main"
            )
        with col_run2:
            run_stream = st.button(
                "⚡ 스트리밍 실행 (긴 작업)",
                use_container_width=True, key="part_action_run_stream"
            )

        if (run_action or run_stream) and action_instruction.strip():
            # 시스템 컨텍스트 구성 (모든 자료 통합)
            sys_ctx = SAGE_PERSONA + "\n\n"
            sys_ctx += "[작업 원칙]\n"
            sys_ctx += "1. 지시된 작업을 정확하게 수행하라. 완성된 결과물만 출력하라.\n"
            sys_ctx += "2. 모르는 것은 솔직하게 말하고 절대 추측하지 마라.\n"
            sys_ctx += "3. 마크다운 형식([[링크]], **강조**, ## 제목, > 인용)을 적극 활용하라.\n"
            sys_ctx += "4. 출처는 [SOURCE: 출처명]으로 반드시 명기하라.\n\n"
            sys_ctx += "[현재 파트 컨텍스트]\n" + _build_part_context(current_part_key) + "\n"
            sys_ctx += "[옵시디언 규칙서]\n" + st.session_state.get("obsidian_rules", "") + "\n"

            if use_obs_rag:
                sys_ctx += "\n" + _build_obsidian_rag_context()
            if use_tavily_rag:
                tavily_ctx = _build_tavily_rag_context()
                if tavily_ctx:
                    sys_ctx += tavily_ctx

            action_prompt = f"""[파트 작업 지시]
파트: {current_part_name}

[지시 내용]
{action_instruction}

위 지시를 정확히 수행하여 즉시 사용 가능한 완성된 결과물을 출력하라.
설명, 서론, 결론, 사족 불필요. 결과물만 출력."""

            if run_stream:
                # 스트리밍 실행
                st.markdown("##### 🎯 작업 결과 (스트리밍)")
                result_container = st.empty()
                full_result = ""
                with st.spinner(f"🔮 {current_model}이 작업 중..."):
                    try:
                        for token in call_gemma_stream(action_prompt, system=sys_ctx, model=current_model):
                            full_result += token
                            result_container.markdown(full_result + "▌")
                        result_container.markdown(full_result)
                        action_result = full_result
                    except Exception as e:
                        action_result = f"[오류] 스트리밍 실패: {e}"
                        result_container.error(action_result)
            else:
                # 일반 실행
                with st.spinner(f"🔮 {current_model}이 작업 중..."):
                    try:
                        action_result = call_gemma(action_prompt, system=sys_ctx, model=current_model)
                    except Exception as e:
                        action_result = f"[오류] 작업 실패: {e}"

                st.markdown("##### 🎯 작업 결과")
                with st.container(height=300, border=True):
                    st.markdown(action_result)

            # 복사용 텍스트
            with st.expander("📋 복사용 텍스트 (드래그 선택)", expanded=False):
                st.code(action_result, language="markdown")
            st.download_button(
                "📥 결과 다운로드 (.md)",
                data=action_result,
                file_name=f"part_action_{current_part_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                key="part_action_dl_result",
                use_container_width=True,
            )

            # 세션 데이터 자동 적용
            if auto_apply:
                apply_msg = _apply_part_action(current_part_key, action_instruction, action_result)
                if apply_msg:
                    st.success(apply_msg)
                else:
                    st.info("💡 자동 적용 조건 미충족. 수동으로 복사하여 해당 파트에 붙여넣으세요.")

            # 옵시디언 자동 저장
            try:
                saved = _save_to_obsidian_with_tags(
                    content=f"[지시]\n{action_instruction}\n\n[결과]\n{action_result}",
                    title=f"[파트작업] {action_instruction[:30]}",
                    source_type=f"파트 작업 지시 — {current_part_name}",
                    part_key=current_part_key,
                    model_name=current_model,
                )
                if saved:
                    st.toast("🧠 옵시디언 자동 저장 완료!", icon="💾")
            except Exception:
                pass

            # 대화 이력에도 추가
            st.session_state.popup_history.append({"role": "user", "content": f"[파트 작업 지시] {action_instruction}"})
            st.session_state.popup_history.append({
                "role": "assistant", "content": action_result,
                "model": current_model, "part": current_part_name,
                "source": f"파트 작업 지시 — {current_part_name}"
            })

    # ─── 탭 B: 직접 수정 / 주입 ───
    with tab_b:
        st.markdown("##### ✏️ 파트 세션 데이터 직접 수정")
        st.caption("젬마 없이 텍스트를 직접 수정하거나, 외부 자료를 붙여넣어 파트 데이터를 업데이트합니다.")

        info = PART_CONTEXT_MAP.get(current_part_key, {})
        keys = info.get("keys", [])

        if not keys:
            st.info(f"'{current_part_name}'에는 직접 수정 가능한 데이터 키가 없습니다.")
        else:
            selected_key = st.selectbox(
                "수정할 데이터 키",
                options=keys,
                key="part_action_key_select",
                format_func=lambda x: f"📝 {x}"
            )
            current_val = st.session_state.get(selected_key, "")
            new_val = st.text_area(
                f"✏️ {selected_key} 수정",
                value=current_val,
                height=350,
                key=f"part_action_direct_edit_{selected_key}",
                label_visibility="collapsed",
            )
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                if st.button("💾 저장 및 적용", type="primary", use_container_width=True, key="part_action_direct_save"):
                    st.session_state[selected_key] = new_val
                    st.toast(f"✅ {selected_key} 업데이트 완료!", icon="✅")
                    # 옵시디언에도 저장
                    _save_to_obsidian_with_tags(
                        content=new_val,
                        title=f"[직접수정] {selected_key}",
                        source_type="직접 수정",
                        part_key=current_part_key,
                        model_name=current_model,
                    )
            with col_s2:
                if st.button("🔄 원래 값으로", use_container_width=True, key="part_action_direct_reset"):
                    st.rerun()
            with col_s3:
                st.download_button(
                    "📥 현재 값 다운로드",
                    data=new_val,
                    file_name=f"{selected_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    key="part_action_direct_dl",
                    use_container_width=True,
                )

    # ─── 탭 C: 파트 간 연결 ───
    with tab_c:
        st.markdown("##### 🧩 파트 간 데이터 연결 현황")
        pipeline_data = [
            ("Part 1", "p1_topic_selection", "Part 2", "선택된 주제"),
            ("Part 2", "p2_research_result", "Part 3-4", "자료조사 결과"),
            ("Part 2", "p2_planning_result", "Part 3-4", "총괄 기획안"),
            ("Part 3-4", "p34_narration_script", "Part 6", "나레이션 대본"),
            ("Part 3-4", "p34_image_script", "Part 5", "이미지 대본 (C-1)"),
            ("Part 3-4", "p34_capcut_data", "Part 7", "캡컷 JSON"),
        ]
        for from_part, key, to_part, label in pipeline_data:
            val = st.session_state.get(key, "")
            status = "✅ 데이터 있음" if val else "⏳ 미완성"
            color = "#10B981" if val else "#888"
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;padding:6px 10px;"
                f"background:#1a1a1a;border-radius:6px;margin:4px 0;'>"
                f"<span style='color:#d4af6a;font-weight:700;'>{from_part}</span>"
                f"<span style='color:#555;'>→</span>"
                f"<span style='color:#aaa;'>{label}</span>"
                f"<span style='color:#555;'>→</span>"
                f"<span style='color:#d4af6a;font-weight:700;'>{to_part}</span>"
                f"<span style='color:{color};margin-left:auto;font-size:0.8rem;'>{status}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.divider()
        st.markdown("##### 🔄 데이터 전달 (파트 간 수동 복사)")
        col_from, col_to = st.columns(2)
        with col_from:
            from_key = st.selectbox("원본 키", options=list(st.session_state.keys()),
                                    key="pipe_from_key",
                                    format_func=lambda x: x if len(x) < 40 else x[:37] + "...")
        with col_to:
            to_key = st.selectbox("대상 키", options=[k for info in PART_CONTEXT_MAP.values() for k in info.get("keys", [])],
                                  key="pipe_to_key")
        if st.button("🔄 데이터 전달", use_container_width=True, key="pipe_transfer_btn"):
            src_val = st.session_state.get(from_key, "")
            if src_val:
                st.session_state[to_key] = src_val
                st.success(f"✅ {from_key} → {to_key} 전달 완료!")
            else:
                st.warning(f"'{from_key}' 에 데이터가 없습니다.")

    # ─── 탭 D: 작업 이력 ───
    with tab_d:
        st.markdown("##### 📊 파트 작업 이력")
        action_history = [
            m for m in st.session_state.get("popup_history", [])
            if "파트 작업 지시" in m.get("content", "")
        ]
        if not action_history:
            st.info("아직 파트 작업 이력이 없습니다.")
        else:
            for msg in action_history:
                role_icon = "🧑" if msg["role"] == "user" else "🤖"
                bg = "#1a3a5c" if msg["role"] == "user" else "#2d1b00"
                st.markdown(
                    f"<div style='background:{bg};padding:8px 12px;margin:4px 0;border-radius:6px;'>"
                    f"<b>{role_icon}</b> {msg['content'][:100]}...</div>",
                    unsafe_allow_html=True,
                )
            if st.button("🗑️ 이력 초기화", key="part_action_history_clear"):
                st.session_state.popup_history = []
                st.rerun()



# ══════════════════════════════════════════════════════════════════════
# 🤖 SAGE AGENT SYSTEM v1.0 — 젬마 자율 에이전트 엔진
# ══════════════════════════════════════════════════════════════════════

import re as _re_agent

# ── 툴 태그 패턴 정의 ──────────────────────────────────────────────
AGENT_TOOL_PATTERNS = get_supported_agent_tools()

def _detect_tools(response: str) -> list:
    """젬마 응답에서 툴 태그 전체 감지 (Stabilized v16.1.8)"""
    detected = []
    for tool_name, pattern in AGENT_TOOL_PATTERNS.items():
        # 레지스트리 비활성화 도구 사전 차단
        meta = get_tool_metadata(tool_name)
        if meta and not meta.get("enabled", True):
            continue
            
        matches = _re_agent.findall(pattern, response)
        for m in matches:
            detected.append({"tool": normalize_tool_name(tool_name), "param": m.strip()})
    # 자료부족 키워드도 감지 (기존 방식)
    unsure_kws = ["자료가 부족", "확실하지 않", "모르겠습니다", "알 수 없", "정보가 없"]
    if any(kw in response for kw in unsure_kws) and not detected:
        # SEARCH_WEB이 레지스트리 상 활성화된 상태인지 확인
        web_meta = get_tool_metadata("SEARCH_WEB")
        if web_meta and web_meta.get("enabled", True):
            detected.append({"tool": "SEARCH_WEB", "param": "자동감지"})
    return detected

def _execute_tool(tool: str, param: str, question: str, model: str, part_key: str) -> str:
    """툴 태그 실행 → 결과 반환"""
    result = ""
    norm_tool = normalize_tool_name(tool)

    # ── 레지스트리 기반 도구 검증 및 조기 차단 (Stabilized v16.1.8) ──
    meta = get_tool_metadata(norm_tool)
    if not meta:
        return f"[도구 거부: {tool} — 레지스트리에 등록되지 않은 알 수 없는 도구입니다.]"
    if not meta.get("enabled", True):
        return f"[도구 거부: {norm_tool} — 현재 비활성화 상태인 도구입니다.]"

    if norm_tool == "SEARCH_WEB" or tool == "NEED_RESEARCH":
        # Tavily 웹 검색
        query = question if param == "자동감지" else param
        api_key = st.session_state.get("tavily_api_key")
        if api_key:
            sr = run_tavily_research(query, api_key, max_results=4)
            if "error" not in sr:
                # 결과 포맷팅 위임
                result = format_search_web_result(query, sr.get("results", []), format_search_results_markdown)
                # 검색 기록 저장
                if "popup_search_history" not in st.session_state:
                    st.session_state.popup_search_history = []
                st.session_state.popup_search_history.append({"q": query, "res": sr})
                # ── Recent Activity Dynamic Sync ──
                try:
                    from rag_memory_utils import update_recent_activity_memory
                    state_dict = dict(st.session_state)
                    updated_mem = update_recent_activity_memory(state_dict, "tavily", f"에이전트 검색: {query}")
                    st.session_state.recent_activity_memory = updated_mem
                except Exception:
                    pass
            else:
                result = format_tool_result(norm_tool, False, "", sr['error'])
        else:
            result = format_tool_result(norm_tool, False, "", "Tavily API Key 미설정")

    elif norm_tool == "READ_OBSIDIAN" or tool == "READ_OBSIDIAN":
        # 옵시디언 RAG 검색
        try:
            from obsidian_search import simple_keyword_search
            obs_results = simple_keyword_search(
                st.session_state.get("path_obsidian", ""), param, top_k=5
            )
            if obs_results:
                result = f"\n[🧠 옵시디언 검색 결과 — {param}]\n"
                result += "\n".join([
                    f"- [[{r['title']}]]: {r['preview'][:300]} [SOURCE: 옵시디언 — {r['title']}]"
                    for r in obs_results[:5]
                ])
            else:
                result = f"[옵시디언 검색 결과 없음: {param}]"
        except Exception as e:
            result = f"[옵시디언 검색 실패: {e}]"

    elif norm_tool == "SAVE_OBSIDIAN" or tool == "SAVE_MEMORY":
        # 옵시디언 자동 저장
        try:
            _save_to_obsidian_with_tags(
                content=f"[주제] {param}\n\n[저장 요청 시각] {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                title=param[:50],
                source_type="젬마 자동 저장 요청",
                part_key=part_key,
                model_name=model,
            )
            result = format_save_obsidian_result(param, True)
        except Exception as e:
            result = format_save_obsidian_result(param, False, str(e))

    elif norm_tool == "VERIFY" or tool == "VERIFY":
        # 자체 검증 (젬마가 비평가로 재검토)
        verify_prompt = f"""[자가 검증 요청]
아래 내용이 다음 기준을 충족하는지 검증하라:
1. 출처 [SOURCE:] 태그 포함 여부
2. 가짜 성경 구절 또는 존재하지 않는 철학 인용 여부
3. @Protagonist 표기 통일 여부
4. AI 냄새 나는 문장 여부

[검증 대상]: {param[:300]}

[검증 결과]: PASS / FAIL + 이유"""
        try:
            verify_result = call_gemma(verify_prompt, model=model)
            result = f"\n[🔍 자체 검증 결과 — {param[:30]}]\n{verify_result}"
        except Exception as e:
            result = f"[검증 실패: {e}]"

    elif norm_tool == "ANALYZE" or tool == "ANALYZE":
        # 심층 분석 (별도 젬마 호출)
        analyze_prompt = f"""[심층 분석 요청]
주제: {param}
현자의 거울 기준으로 아래를 분석하라:
1. 핵심 감정 키워드 3개
2. 관련 철학자 및 성경 구절
3. 4070 시청자 공명 포인트
[출력]: 분석 결과만 간결하게"""
        try:
            analyze_result = call_gemma(analyze_prompt, model=model)
            result = f"\n[🔬 심층 분석 — {param}]\n{analyze_result}"
        except Exception as e:
            result = f"[분석 실패: {e}]"

    elif norm_tool == "CHECK_SOURCE" or tool == "CHECK_SOURCE":
        # 출처 검증 (Tavily로 실제 존재 여부 확인)
        api_key = st.session_state.get("tavily_api_key")
        if api_key:
            sr = run_tavily_research(param, api_key, max_results=3)
            if "error" not in sr:
                # 결과 포맷팅 위임
                result = format_check_source_result(param, sr.get("results", []), format_source_citation)
            else:
                result = format_tool_result(norm_tool, False, "", sr['error'])
        else:
            result = format_tool_result(norm_tool, False, "", "Tavily API Key 미설정")

    return result


def run_agent_loop(
    question: str,
    sys_ctx: str,
    model: str,
    part_key: str,
    max_iterations: int = 4,
    stream_placeholder=None,
    status_widget=None,
) -> str:
    """
    🤖 SAGE AGENT LOOP v1.0
    젬마 자율 에이전트 — 툴 감지 → 실행 → 재주입 → 반복
    
    흐름:
    1. 젬마 응답 생성
    2. 툴 태그 감지
    3. 툴 실행 → 결과 수집
    4. 결과를 컨텍스트에 주입
    5. 최대 max_iterations 반복
    6. 최종 응답 반환
    """
    accumulated_context = ""
    final_response = ""
    tools_log = []

    for iteration in range(max_iterations):
        # 컨텍스트 포함 프롬프트 구성
        if accumulated_context:
            enriched_prompt = (
                f"{question}\n\n"
                f"[수집된 자료 (툴 실행 결과)]\n{accumulated_context}\n\n"
                f"위 자료를 바탕으로 최종 답변을 완성하라. "
                f"모든 인용에 [SOURCE:] 태그 필수."
            )
        else:
            enriched_prompt = question

        # 젬마 응답 생성 (모든 반복에 실시간 스트리밍 적용)
        if stream_placeholder:
            full_response = ""
            try:
                for token in call_gemma_stream(enriched_prompt, system=sys_ctx, model=model):
                    full_response += token
                    stream_placeholder.markdown(full_response + "▌")
                stream_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"[오류] {e}"
                stream_placeholder.error(full_response)
        else:
            try:
                full_response = call_gemma(enriched_prompt, sys_ctx, model=model)
            except Exception as e:
                full_response = f"[오류] {e}"

        final_response = full_response

        # 툴 태그 감지
        detected_tools = _detect_tools(full_response)

        if not detected_tools:
            # 툴 없음 = 완성
            if status_widget:
                status_widget.update(
                    label=f"✅ 완료 ({iteration+1}회 반복{'·'+', '.join(tools_log) if tools_log else ''})",
                    state="complete", expanded=False
                )
            break

        # 툴 실행
        tool_results = []
        for tool_info in detected_tools:
            tool_name = tool_info["tool"]
            tool_param = tool_info["param"]

            if status_widget:
                status_widget.update(
                    label=f"🔧 [{tool_name}] 실행 중: {tool_param[:30]}...",
                    state="running", expanded=True
                )

            try:
                result = _execute_tool(tool_name, tool_param, question, model, part_key)
            except Exception as e:
                from agent_toolkit import format_tool_error
                result = format_tool_error(tool_name, f"도구 실행 중 치명적 오류 발생: {e}")

            if result:
                tool_results.append(result)
                tools_log.append(tool_name)

        if tool_results:
            accumulated_context += "\n".join(tool_results)
            # 스트리밍 플레이스홀더에 진행 상황 표시
            if stream_placeholder:
                stream_placeholder.markdown(
                    f"{full_response}\n\n---\n"
                    f"*🔧 {', '.join([t['tool'] for t in detected_tools])} 실행 완료 → 재생성 중...*"
                )
        else:
            # 툴 결과 없음 = 종료
            break

    return final_response


# ══════════════════════════════════════════════════════════════════════
# 🤖 세이지 팝업 v3.0 — 메인 팝업
# ══════════════════════════════════════════════════════════════════════
def _call_gemma_fast_a_mode(prompt: str, system: str = "", model: str = "gemma4:e2b") -> str:
    """
    [A모드 전용 v17.1.4-E] 동기 방식 단일 호출.
    @st.dialog 팝업 내부에서 스트리밍 placeholder 실시간 업데이트가
    작동하지 않아 응답이 화면에 표시되지 않는 문제 해결.
    sage_engine.call_gemma() 동기 호출 후 popup_assistant에서
    st.rerun()으로 화면 갱신 → 대화창 닫지 않아도 응답 즉시 표시.
    """
    try:
        from sage_engine import call_gemma as _cg
        result = _cg(prompt, system=system, model=model)
        if not result or not result.strip():
            return "응답을 생성하지 못했습니다. 다시 시도해 주세요."
        return result
    except Exception as e:
        return f"[A모드 호출 오류] {e}"


# ─── A모드 스트리밍 제너레이터 (v17.1.5) ─────────────────────────
def _stream_gemma_a_mode(prompt: str, system: str = "", model: str = "gemma4:e2b"):
    """
    [A모드 전용 v17.1.5] Ollama /api/generate 스트리밍 제너레이터.
    st.write_stream()에 전달하여 토큰을 한 글자씩 실시간 출력.
    - 초경량 system prompt(50자 내외)와 함께 사용
    - HTTP 연결 유지 방식으로 타임아웃 원천 차단
    - thinking 태그 필터링 포함
    """
    import requests as _req
    import json as _json

    ka_val = st.session_state.get("popup_keep_alive", "10m")
    np_val = st.session_state.get("popup_num_predict", 300)
    temp_val = st.session_state.get("popup_temperature", 0.2)
    tp_val = st.session_state.get("popup_top_p", 0.8)

    full_prompt = ""
    if system and system.strip():
        full_prompt = system.strip() + "\n\n"
    full_prompt += prompt

    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,
        "keep_alive": ka_val,
        "options": {
            "num_predict": np_val,
            "temperature": temp_val,
            "top_p": tp_val,
        }
    }

    try:
        in_thinking = False
        with _req.post(ollama_url, json=payload, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    chunk = _json.loads(raw_line.decode("utf-8"))
                except Exception:
                    continue
                token = chunk.get("response", "")
                if token:
                    # <think> 태그 필터링 (thinking 모드 출력 제거)
                    if "<think>" in token:
                        in_thinking = True
                    if in_thinking:
                        if "</think>" in token:
                            in_thinking = False
                        continue
                    yield token
                if chunk.get("done", False):
                    break
    except Exception as e:
        yield f"\n[스트리밍 오류] {e}"


# ─── 대화 영속성 헬퍼 ─────────────────────────────────────────────
CHAT_JSON_PATH = Path(r"C:\SageMirror_Outputs\00_Session_States\popup_chat_EP001.json")

def _save_chat_history(history: list) -> None:
    """popup_history를 JSON 파일로 영속 저장"""
    try:
        CHAT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHAT_JSON_PATH.write_text(
            __import__('json').dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass

def _load_chat_history() -> list:
    """JSON 파일에서 popup_history 복원"""
    try:
        if CHAT_JSON_PATH.exists():
            raw = CHAT_JSON_PATH.read_text(encoding="utf-8", errors="ignore")
            data = __import__('json').loads(raw)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def _compress_chat_history_stub(history: list) -> list:
    """대화 압축 구조 뼈대 (50턴 초과 시 앞 30턴 요약 — 추후 구현)"""
    # TODO: 50턴 초과 시 앞 30턴 요약 압축, 최근 20턴 원문 유지
    return history


@st.dialog("🤖 세이지 팝업 — Gemma × Tavily × Obsidian RAG", width="large")
def popup_assistant():
    # ── 상태 초기화 ──
    defaults = {
        "popup_selected_model": OLLAMA_MODEL,
        "popup_history": [],
        "popup_search_history": [],
        "pending_stream": None,
        "popup_chat_input_ta": "",
        "popup_auto_search": False,
        "popup_use_rag": False,
        "popup_gemma_mode": "A",
        "tavily_rag_context": "",
        "part_action_quick_input": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── 대화 영속성 복원 (첫 진입 시 JSON에서 로드) ──
    if not st.session_state.popup_history:
        import time
        t_restore_start = time.perf_counter()
        loaded = _load_chat_history()
        t_restore_end = time.perf_counter()
        st.session_state["popup_history_restore_time"] = t_restore_end - t_restore_start
        if loaded:
            st.session_state.popup_history = loaded
    else:
        if "popup_history_restore_time" not in st.session_state:
            st.session_state["popup_history_restore_time"] = 0.0

    current_part_key = _get_current_part()
    current_part_info = PART_CONTEXT_MAP.get(current_part_key, PART_CONTEXT_MAP["part1"])
    current_part_name = current_part_info["name"]

    # ── 연결 상태 ──
    status_obj = check_ollama_status()
    c_stat1, c_stat2 = st.columns(2)
    with c_stat1:
        sel_model = st.session_state.popup_selected_model
        if status_obj.get("server") and status_obj.get("model"):
            st.success(f"🟢 연결 정상: {sel_model}")
        else:
            st.error(f"🔴 연결 에러: {sel_model}")
    with c_stat2:
        if st.session_state.get("tavily_api_key"):
            st.success("🟢 Tavily API 연결 정상")
        else:
            st.warning("🟡 Tavily API Key 미입력")

    # ── 파트 배지 + 모델 선택 ──
    col_badge, col_model, col_save = st.columns([3, 3, 2])
    with col_badge:
        st.markdown(
            f"<div style='background:#1a3a5c;color:#d4af6a;padding:4px 12px;"
            f"border-radius:20px;font-size:0.82rem;font-weight:700;margin-top:6px;'>"
            f"📍 {current_part_name}</div>",
            unsafe_allow_html=True,
        )
    with col_model:
        selected_model = st.selectbox(
            "모델", AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(st.session_state.popup_selected_model)
            if st.session_state.popup_selected_model in AVAILABLE_MODELS else 0,
            key="popup_model_selector", label_visibility="collapsed",
        )
        st.session_state.popup_selected_model = selected_model
    with col_save:
        if st.button("💾 대화 옵시디언 저장", use_container_width=True, key="popup_obs_save_btn",
                     disabled=not st.session_state.popup_history):
            saved = _save_to_obsidian_with_tags(
                content="\n".join([f"[{m['role'].upper()}] {m['content']}" for m in st.session_state.popup_history]),
                title=f"[Sage Chat] {current_part_name}",
                source_type="Sage 팝업 대화",
                part_key=current_part_key,
                model_name=st.session_state.popup_selected_model,
            )
            if saved:
                st.toast("🧠 대화 옵시디언 저장 완료!", icon="💾")

    # Tavily 자료가 있으면 표시
    if st.session_state.get("popup_search_history"):
        search_count = len(st.session_state.popup_search_history)
        st.markdown(
            f"<div style='background:#0d2a0d;border:1px solid #10B981;padding:4px 10px;"
            f"border-radius:6px;font-size:0.8rem;color:#10B981;margin:4px 0;'>"
            f"🌐 인터넷 자료 {search_count}건 수집됨 — 젬마가 자동으로 참조합니다</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── 탭 구성 ──
    tab_chat, tab_tavily, tab_upload, tab_part_action = st.tabs([
        "💬 빠른 대화",
        "🔎 자료 조사",
        "📂 젬마 자료 업로드",
        "🧠 옵시디언 저장소"
    ])

    # ══════════════════════════════════════════════════════
    # 탭 1: 빠른 대화 (A 시스템 — 경량 1회 호출)
    # ══════════════════════════════════════════════════════
    with tab_chat:
        # 모드 선택 칩(Pills) 형태 UI
        mode_cols = st.columns([1, 1])
        with mode_cols[0]:
            st.session_state.popup_gemma_mode = st.radio(
                "⚡ 대화 모드 선택",
                options=["A", "B"],
                format_func=lambda x: "⚡ 빠른 대화 (A모드)" if x == "A" else "🧠 심층 에이전트 (B모드)",
                horizontal=True,
                label_visibility="collapsed"
            )

        # A모드 매개변수 세션 초기화
        if "popup_keep_alive" not in st.session_state:
            st.session_state["popup_keep_alive"] = "10m"
        if "popup_num_predict" not in st.session_state:
            st.session_state["popup_num_predict"] = 300
        if "popup_temperature" not in st.session_state:
            st.session_state["popup_temperature"] = 0.2
        if "popup_top_p" not in st.session_state:
            st.session_state["popup_top_p"] = 0.8

        with st.expander("⚙️ 속도 최적화 매개변수 설정", expanded=False):
            c_opt1, c_opt2 = st.columns(2)
            with c_opt1:
                ka_val = st.text_input("keep_alive (메모리 유지 시간)", value=st.session_state.popup_keep_alive, key="p_opt_ka_input")
                np_opts = [150, 300, 500, 1000]
                cur_np = st.session_state.popup_num_predict
                np_idx = np_opts.index(cur_np) if cur_np in np_opts else 1
                np_val = st.selectbox("num_predict (최대 토큰)", np_opts, index=np_idx, key="p_opt_np_select")
            with c_opt2:
                temp_val = st.slider("temperature (창의성)", 0.0, 1.0, value=st.session_state.popup_temperature, step=0.1, key="p_opt_temp_slider")
                tp_val = st.slider("top_p (다양성)", 0.0, 1.0, value=st.session_state.popup_top_p, step=0.1, key="p_opt_tp_slider")
            
            st.session_state.popup_keep_alive = ka_val
            st.session_state.popup_num_predict = np_val
            st.session_state.popup_temperature = temp_val
            st.session_state.popup_top_p = tp_val

        # ── 채팅 UI 컨테이너 ──
        st.markdown("##### 💬 대화 기록")
        chat_container = st.container(height=450, border=True)

        with chat_container:
            if not st.session_state.popup_history and not st.session_state.get("pending_stream"):
                st.markdown(
                    "<div style='color:#888;padding:20px;text-align:center;'>"
                    "💭 아직 대화가 없습니다.<br><br>"
                    "<small style='color:#d4af6a;'>"
                    "• 아래 입력창에 질문을 입력하세요<br>"
                    "• 대화 내용은 자동으로 영속성 저장됩니다"
                    "</small></div>",
                    unsafe_allow_html=True,
                )

            # 이전 대화 렌더링
            for msg in st.session_state.popup_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant":
                        source_info = msg.get("source", "")
                        model_used = msg.get("model", sel_model)
                        st.caption(f"🤖 {model_used} | {source_info}")

            # 스트리밍 및 응답 생성 대기 영역
            if st.session_state.get("pending_stream"):
                q_stream = st.session_state.pending_stream
                current_model = st.session_state.popup_selected_model
                current_mode = st.session_state.get("popup_gemma_mode", "A")

                # 사용자 질문 바로 표시 (pending)
                with st.chat_message("user"):
                    st.markdown(q_stream)

                with st.chat_message("assistant"):
                    if current_mode == "A":
                        # A 모드: 초경량 프롬프트 & 실시간 스트리밍
                        sys_ctx = (
                            "너는 현자의 거울 스튜디오의 친절한 대화 파트너 젬마다. "
                            "짧고 명쾌하게 대답하라."
                        )
                        # 스트리밍 제너레이터 호출 (requests.iter_lines)
                        stream_gen = _stream_gemma_a_mode(
                            q_stream,
                            system=sys_ctx,
                            model=current_model
                        )
                        # st.write_stream()으로 타다다닥 실시간 렌더링
                        full_response = st.write_stream(stream_gen)
                        source_label = "A모드 스트리밍"
                    else:
                        # B 모드: 기존 복합 RAG 에이전트 시스템 활용
                        sys_ctx = SAGE_PERSONA + "\n\n"
                        sys_ctx += "[현재 파트]\n" + current_part_name + "\n"
                        sys_ctx += "[옵시디언 규칙서]\n" + st.session_state.get("obsidian_rules", "")[:500] + "\n"
                        
                        with st.status("🔮 젬마 에이전트 작동 중...", expanded=True) as status_widget:
                            ans_placeholder = st.empty()
                            try:
                                full_response = run_agent_loop(
                                    question=q_stream,
                                    sys_ctx=sys_ctx,
                                    model=current_model,
                                    part_key=current_part_key,
                                    max_iterations=4,
                                    stream_placeholder=ans_placeholder,
                                    status_widget=status_widget,
                                )
                            except Exception as e:
                                full_response = f"[오류] {e}"
                                ans_placeholder.error(full_response)
                        st.markdown(full_response)
                        source_label = "에이전트 루프 v1.0"

                # 공통: 대화 기록 저장
                st.session_state.popup_history.append({
                    "role": "user",
                    "content": q_stream
                })
                st.session_state.popup_history.append({
                    "role": "assistant",
                    "content": full_response,
                    "model": current_model,
                    "part": current_part_name,
                    "source": source_label,
                })
                
                st.session_state.pending_stream = None
                
                # 영속성 JSON 파일 실시간 저장
                try:
                    _save_chat_history(st.session_state.popup_history)
                except Exception:
                    pass
                
                # 대화 완료 후 화면 상태 갱신
                st.rerun()

        # ── 하단 채팅 입력 (st.chat_input) ──
        if user_input := st.chat_input("안녕 / 간단한 질문을 입력하세요..."):
            st.session_state.pending_stream = user_input
            st.rerun()

        # 도구 모음
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ 대화 초기화", use_container_width=True, key="popup_clear"):
                st.session_state.popup_history = []
                st.session_state.pending_stream = None
                _save_chat_history([])
                st.toast("🗑️ 대화 기록 초기화 완료", icon="🗑️")
                st.rerun()
        with c2:
            if st.session_state.popup_history:
                all_chat = "\n\n".join(
                    f"### [{m['role'].upper()}]\n{m['content']}"
                    for m in st.session_state.popup_history
                )
                st.download_button("💾 대화 다운로드", data=all_chat,
                                   file_name=f"sage_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                   use_container_width=True, key="popup_dl")
            else:
                st.button("💾 대화 다운로드", use_container_width=True, key="popup_dl_disabled", disabled=True)

    # ══════════════════════════════════════════════════════
    # 탭 2: 🔎 자료 조사
    # ══════════════════════════════════════════════════════
    with tab_tavily:
        st.markdown("##### 🔎 자료 조사 (Gemini / Tavily)")
        st.markdown(
            "<div style='background:rgba(214,175,106,0.05);border:1px solid rgba(214,175,106,0.15);"
            "padding:10px 14px;border-radius:6px;font-size:0.88rem;margin-bottom:12px;color:#f5e9d3;'>"
            "💡 <b>역할 분리 시스템 안내</b><br>"
            "- <b>Gemini / Tavily</b>: 실시간 웹 및 전문 데이터베이스로부터 외부 자료를 강력하게 수집합니다.<br>"
            "- <b>Gemma (Local)</b>: 수집된 날것의 자료를 심도 있게 분석·요약하고 범용 카테고리와 RAG 태그를 추출하여 옵시디언 <code>ResearchMemory</code>에 체계적으로 구조화하여 저장합니다."
            "</div>",
            unsafe_allow_html=True,
        )

        search_tool = st.radio(
            "검색 도구 선택",
            ["Gemini 자료조사", "Tavily Research"],
            horizontal=True,
            key="p_research_tool"
        )

        sq = st.text_area(
            "검색어 입력",
            placeholder=(
                "예: 쇼펜하우어 의지와 표상으로서의 세계의 현대 심리학적 의미\n"
                "예: 빅터 프랭클의 의미치료(로고테라피) 실제 상담 사례\n"
                "예: 60대 은퇴 후 노년층이 겪는 상실감과 우울증 극복 방안"
            ),
            height=100,
            key="p_research_q",
            label_visibility="collapsed"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            do_search = st.button("🚀 검색 및 젬마 분석", key="p_research_btn", use_container_width=True, type="primary")
        with c2:
            sback = st.button(f"⬅️ 이전 ({len(st.session_state.popup_search_history)})",
                              key="p_research_back", use_container_width=True,
                              disabled=len(st.session_state.popup_search_history) == 0)
        with c3:
            sclear = st.button("🗑️ 기록 초기화", key="p_research_clear", use_container_width=True)

        if sback and st.session_state.popup_search_history:
            st.session_state.popup_search_history.pop()
            st.rerun()
        if sclear:
            st.session_state.popup_search_history = []
            st.rerun()

        if do_search and sq.strip():
            # API Key 체크
            gemini_key = st.session_state.get("gemini_api_key", "").strip()
            tavily_key = st.session_state.get("tavily_api_key", "").strip()

            error_msg = None
            if search_tool == "Gemini 자료조사" and not gemini_key:
                error_msg = "⚠️ Gemini API Key가 없습니다. 사이드바 설정에서 입력해 주세요."
            elif search_tool == "Tavily Research" and not tavily_key:
                error_msg = "⚠️ Tavily API Key가 없습니다. 사이드바 설정에서 입력해 주세요."

            if error_msg:
                st.error(error_msg)
            else:
                with st.spinner(f"🌐 {search_tool} 자료 수집 중..."):
                    try:
                        res = {}
                        raw_results = ""
                        source_info = ""

                        if search_tool == "Gemini 자료조사":
                            # 구글 검색 Grounding
                            g_res = call_gemini_search(sq, gemini_key)
                            if "error" in g_res:
                                st.error(f"❌ Gemini 검색 중 오류 발생: {g_res['error']}")
                                st.stop()
                            
                            res["results"] = g_res.get("results", [])
                            res["answer"] = g_res.get("summary", "")
                            raw_results = f"[Gemini 구글 검색 요약]\n{res['answer']}\n\n"
                            raw_results += "\n".join([
                                f"[{r.get('title','')}] {r.get('content','')} (URL: {r.get('url','')})"
                                for r in res.get("results", [])
                            ])
                            source_info = "Gemini 구글 검색"
                        else:
                            # Tavily 웹 리서치
                            t_res = run_tavily_research(sq, tavily_key)
                            if "error" in t_res:
                                st.error(f"❌ Tavily 검색 중 오류 발생: {t_res['error']}")
                                st.stop()
                            
                            res["results"] = t_res.get("results", [])
                            res["answer"] = t_res.get("answer", "")
                            raw_results = "\n".join([
                                f"[{r.get('title','')}] {r.get('content','')[:400]} (URL: {r.get('url','')})"
                                for r in res.get("results", [])[:5]
                            ])
                            source_info = "Tavily 웹 검색"

                        # Gemma 가공 및 분석
                        st.info("🔮 수집된 날것의 자료를 Gemma 모델이 정제 및 구조화 분석 중...")
                        analysis_prompt = f"""[지시] 수집된 리서치 자료를 현자의 거울 스튜디오 형식으로 면밀히 가공 및 요약하라.
인위적인 환각(허구 인용)을 배제하고 사실에 근거하여 작성하라.

[검색 주제]
{sq}

[수집 자료]
{raw_results[:4000]}

[출력 형식 — 반드시 준수]
## 🔎 핵심 요약 (3줄)
- (핵심 요점 1)
- (핵심 요점 2)
- (핵심 요점 3)

## 📖 심층 분석
(내용 분석 + 현자의 거울 주제와의 깊이 있는 학술적/감성적 연관성)

## 💡 파트별 활용 방안
({current_part_name}에서 이 리서치 정보를 어떻게 대본이나 기획에 접목할 수 있는지 상세히 기술)

## 🎭 범용 카테고리 & 시청자 감정 매핑
(이 자료와 연결되는 시청자 상태 또는 분류: 외로움/불안/상실/죽음/용서 등 기술)

## 📚 자료 출처 정보
(참조한 URL들을 [SOURCE: URL] 형식으로 명시할 것)"""

                        gemma_analysis = call_gemma(
                            analysis_prompt,
                            model=st.session_state.popup_selected_model
                        )
                        res["gemma_analysis"] = gemma_analysis

                        st.session_state.popup_search_history.append({"q": sq, "res": res, "tool": search_tool})

                        # ── Recent Activity Dynamic Sync ──
                        try:
                            from rag_memory_utils import update_recent_activity_memory
                            state_dict = dict(st.session_state)
                            updated_mem = update_recent_activity_memory(state_dict, "tavily", f"자료조사 ({search_tool}): {sq}")
                            st.session_state.recent_activity_memory = updated_mem
                        except Exception:
                            pass

                        # 범용 감정/RAG 카테고리 추출 및 태그화
                        all_content = sq + " " + gemma_analysis + " " + " ".join([r.get("content", "") for r in res.get("results", [])[:5]])
                        auto_emotion_tags = list(_classify_universal_tags(all_content).keys())

                        # 옵시디언 자동 저장 (ResearchMemory로 강제고정)
                        save_content = f"[검색 도구]: {search_tool}\n"
                        save_content += f"[검색 키워드]: {sq}\n\n"
                        if gemma_analysis:
                            save_content += f"## 🤖 Gemma 구조화 요약 및 정제 보고서\n\n{gemma_analysis}\n\n"
                        
                        save_content += "## 🌐 수집 원문 데이터 레퍼런스\n"
                        if res.get("answer"):
                            save_content += f"\n*검색 엔진 직속 요약 답변:*\n{res['answer']}\n"
                        for r in res.get("results", []):
                            save_content += f"\n### [{r.get('title','')}]({r.get('url','')})\n{r.get('content','')}\n[SOURCE: {r.get('url','')}]\n"

                        saved_path = _save_to_obsidian_with_tags(
                            content=save_content,
                            title=f"Research_{sq[:40]}",
                            source_type=f"{search_tool} 수집 및 Gemma 정제",
                            part_key=current_part_key,
                            model_name=st.session_state.popup_selected_model,
                            extra_tags=auto_emotion_tags,
                            folder_override="ResearchMemory",
                        )

                        if saved_path:
                            st.success(f"💾 옵시디언 ResearchMemory 저장 완료!\n경로: `{saved_path}`")
                            st.toast("🧠 옵시디언 저장 및 RAG 인덱싱 완료!", icon="💾")

                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ 리서치 작업 중 에러 발생: {e}")

        # 검색 결과 표시
        st.markdown("##### 📊 검색 결과")
        with st.container(height=380, border=True):
            if not st.session_state.popup_search_history:
                st.markdown(
                    "<div style='color:#888;padding:20px;text-align:center;'>"
                    "🔍 아직 검색 기록이 없습니다.</div>",
                    unsafe_allow_html=True,
                )
            else:
                latest = st.session_state.popup_search_history[-1]
                st.markdown(f"**🔎 검색어:** `{latest['q']}` (도구: {latest.get('tool', 'Tavily Research')})")
                res = latest["res"]
                if "error" in res:
                    st.error(res["error"])
                else:
                    if res.get("gemma_analysis"):
                        st.markdown("### 🤖 Gemma 정제 보고서")
                        st.markdown(res["gemma_analysis"])
                        with st.expander("📋 복사용", expanded=False):
                            st.code(res["gemma_analysis"], language="markdown")
                        st.divider()
                    if res.get("answer"):
                        st.info(f"💡 **직속 요약:** {res['answer']}")
                        st.divider()
                    for idx, r in enumerate(res.get("results", []), 1):
                        st.markdown(f"**{idx}. [{r.get('title','')}]({r.get('url','')})**")
                        st.write(r.get("content", ""))
                        st.caption(f"[SOURCE: {r.get('url','')}]")
                        st.divider()

    # ══════════════════════════════════════════════════════
    # 탭 3: 파일 업로드 → 키워드/파트 태그 분류 → 옵시디언 저장
    # ══════════════════════════════════════════════════════
    with tab_upload:
        st.markdown("##### 📎 파일 업로드 → RAG 카테고리/태그 자동 저장")
        st.caption("파일을 읽고, 젬마가 옵시디언 규칙서 기준으로 분석한 뒤 카테고리·파트 태그와 함께 저장합니다.")

        up_col1, up_col2 = st.columns([3, 2])
        with up_col1:
            uploaded_files = st.file_uploader(
                "파일 선택",
                type=["txt", "md", "csv", "json", "py", "srt", "vtt", "pdf"],
                accept_multiple_files=True,
                key="sage_file_memory_uploader",
                label_visibility="collapsed",
            )
        with up_col2:
            destination_folder = st.selectbox(
                "옵시디언 저장 폴더",
                ["References", "TopicMemory", "ResearchMemory", "ScriptDrafts", "Assets", "Logs"],
                index=0,
                key="sage_file_memory_dest_folder",
            )

        st.markdown("**저장 방식**")
        opt_col1, opt_col2 = st.columns(2)
        with opt_col1:
            use_gemma_analysis = st.checkbox("🤖 Gemma 분석 포함", value=True, key="sage_file_use_gemma")
        with opt_col2:
            save_each_file = st.checkbox("💾 파일별 개별 저장", value=True, key="sage_file_save_each")

        if uploaded_files:
            st.info(f"선택된 파일: {len(uploaded_files)}개")
            for uf in uploaded_files:
                st.caption(f"- {uf.name} ({len(uf.getvalue()):,} bytes)")

        if st.button(
            "📎 업로드 파일 분석 및 옵시디언 저장",
            type="primary",
            use_container_width=True,
            key="sage_file_analyze_save_btn",
            disabled=not uploaded_files,
        ):
            saved_paths = []
            for uf in uploaded_files:
                with st.spinner(f"📖 {uf.name} 읽는 중..."):
                    file_text, suffix = _read_uploaded_file_text(uf)

                if not file_text or file_text.startswith("[지원하지 않는"):
                    st.warning(f"{uf.name}: 읽을 수 없는 파일입니다.")
                    continue

                detected_categories = _detect_file_rag_categories(file_text)
                current_model = st.session_state.get("popup_selected_model", OLLAMA_MODEL)

                gemma_analysis = "Gemma 분석 생략됨."
                if use_gemma_analysis:
                    analysis_prompt = f"""[작업 지시]
아래 업로드 파일을 현자의 거울 옵시디언 규칙서 기준으로 분석하라.

[현재 파트]
{current_part_name}

[파일명]
{uf.name}

[자동 감지 카테고리]
{detected_categories}

[출력 형식]
## 핵심 요약
## 감정/철학/성경/심리 키워드
## RAG 저장 분류 제안
## 유튜브 제작 활용 포인트
## 출처 표기
[SOURCE: 사용자 업로드 파일 — {uf.name}]

[파일 내용]
{file_text[:6000]}
"""
                    try:
                        gemma_analysis = call_gemma(
                            analysis_prompt,
                            system=SAGE_PERSONA + "\n\n[옵시디언 규칙서]\n" + st.session_state.get("obsidian_rules", ""),
                            model=current_model,
                        )
                    except Exception as e:
                        gemma_analysis = f"[Gemma 분석 실패: {e}]"

                md_content, tags = _build_uploaded_file_memory_markdown(
                    filename=uf.name,
                    file_text=file_text,
                    gemma_analysis=gemma_analysis,
                    detected_categories=detected_categories,
                    part_key=current_part_key,
                    model_name=current_model,
                    destination_folder=destination_folder,
                )

                if save_each_file:
                    saved = _save_to_obsidian_with_tags(
                        content=md_content,
                        title=f"[업로드자료] {Path(uf.name).stem[:35]}",
                        source_type=f"파일 업로드 — {uf.name}",
                        part_key=current_part_key,
                        model_name=current_model,
                        extra_tags=tags,
                        folder_override=destination_folder,
                    )
                    if saved:
                        saved_paths.append(saved)

                st.session_state.popup_history.append({
                    "role": "assistant",
                    "content": md_content,
                    "model": current_model,
                    "part": current_part_name,
                    "source": f"파일 업로드 분석 — {uf.name}",
                })

                with st.expander(f"📄 분석 결과 보기 — {uf.name}", expanded=False):
                    st.markdown(md_content)
                    st.download_button(
                        "📥 분석 결과 다운로드",
                        data=md_content,
                        file_name=f"upload_memory_{Path(uf.name).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        key=f"upload_memory_dl_{uf.name}",
                    )

            if saved_paths:
                st.success(f"✅ 옵시디언 저장 완료: {len(saved_paths)}개")
                with st.expander("📂 저장 경로 확인", expanded=True):
                    for sp in saved_paths:
                        st.code(sp)
            else:
                st.info("분석 결과는 대화 기록에 추가되었지만, 파일 저장은 수행되지 않았습니다.")

    # ══════════════════════════════════════════════════════
    # 탭 4: 파트 작업 지시 (팝업 전환 버튼)
    # ══════════════════════════════════════════════════════
    with tab_part_action:
        st.markdown(f"##### ⚙️ 현재 파트 직접 작업 지시")
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#1a3a5c,#0d2240);border-left:4px solid #d4af6a;"
            f"padding:10px 16px;border-radius:0 8px 8px 0;margin-bottom:12px;'>"
            f"<b style='color:#d4af6a;'>📍 {current_part_name}</b><br>"
            f"<span style='color:#aaa;font-size:0.85rem;'>{current_part_info['desc']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # 현재 파트 데이터 미리보기
        with st.container(height=130, border=True):
            part_ctx = _build_part_context(current_part_key)
            st.code(part_ctx[:700], language="markdown")

        st.divider()

        st.markdown(
            "<div style='background:linear-gradient(135deg,#1a2a00,#0d1a00);border:1px solid #d4af6a;"
            "padding:16px;border-radius:8px;text-align:center;margin:8px 0;'>"
            "<h3 style='color:#d4af6a;margin:0 0 8px 0;'>⚙️ 전체 작업 기능</h3>"
            "<p style='color:#aaa;margin:0 0 12px 0;font-size:0.9rem;'>"
            "AI 작업 실행, 직접 수정, 파트 간 연결, 작업 이력<br>"
            "4가지 전문 기능이 대형 팝업창에서 제공됩니다</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        if st.button(
            "⚙️ 파트 작업 지시 전용 팝업창 열기",
            type="primary",
            use_container_width=True,
            key="open_part_action_popup_btn"
        ):
            popup_part_action_dialog()

        st.divider()
        st.markdown("**⚡ 빠른 실행 (팝업 없이)**")
        quick_input = st.text_area(
            "빠른 지시",
            placeholder="간단한 작업은 여기서 바로 실행하세요...",
            height=80,
            key="quick_part_action_input",
            label_visibility="collapsed",
        )
        if st.button("🚀 빠른 실행", use_container_width=True, key="quick_part_action_btn",
                     disabled=not quick_input.strip()):
            sys_ctx = SAGE_PERSONA + "\n\n[현재 파트]\n" + _build_part_context(current_part_key)
            sys_ctx += "\n[옵시디언 규칙서]\n" + st.session_state.get("obsidian_rules", "")
            sys_ctx += "\n" + _build_tavily_rag_context()
            with st.spinner("🔮 실행 중..."):
                try:
                    quick_result = call_gemma(quick_input, system=sys_ctx,
                                              model=st.session_state.popup_selected_model)
                    st.markdown("**결과:**")
                    st.markdown(quick_result)
                    with st.expander("📋 복사용"):
                        st.code(quick_result, language="markdown")
                    # 옵시디언 저장
                    _save_to_obsidian_with_tags(
                        content=f"[빠른 지시]\n{quick_input}\n\n[결과]\n{quick_result}",
                        title=f"[빠른작업] {quick_input[:30]}",
                        source_type="빠른 작업 지시",
                        part_key=current_part_key,
                        model_name=st.session_state.popup_selected_model,
                    )
                    st.toast("🧠 결과 옵시디언 저장 완료!", icon="💾")
                except Exception as e:
                    st.error(f"실행 실패: {e}")
