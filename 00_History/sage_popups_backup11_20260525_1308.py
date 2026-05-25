# -*- coding: utf-8 -*-
"""
sage_popups.py — 팝업 다이얼로그 v3.0
[v3.0 업그레이드]
- 파트 작업 지시 → 별도 대형 팝업창 (popup_part_action_dialog)
- 리서치 결과 → 젬마 자동 컨텍스트 주입 (session_state.tavily_rag_context)
- 심리학 채널 전용 감정/태그 세분화 자동저장 시스템
- 각 파트 상단 옵시디언 규칙서 참조 → 저장 시 자동 반영
- 모든 데이터 소스(Tavily+옵시디언+파트데이터) 통합 RAG 컨텍스트
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
from sage_config import (
    DEFAULT_OBSIDIAN_RULES, DEFAULT_BASE_PROMPT,
    SAGE_PERSONA, OLLAMA_MODEL,
)
from sage_engine import call_gemma, call_gemma_stream, tavily_search, check_ollama_status

# ─── 상수 ───
AVAILABLE_MODELS = ["gemma4:e2b", "gemma4:e4b"]

# 심리학 채널 전용 감정 태그 분류 시스템
PSYCHOLOGY_EMOTION_TAGS = {
    "외로움·고독": ["외로움", "고독", "고립", "loneliness", "isolation", "solitude"],
    "불안·두려움": ["불안", "두려움", "공포", "anxiety", "fear", "worry", "걱정"],
    "상실·슬픔": ["상실", "슬픔", "비통", "grief", "loss", "sadness", "애도"],
    "무기력·공허": ["무기력", "공허", "허무", "emptiness", "helplessness", "burnout", "번아웃"],
    "분노·억울함": ["분노", "억울", "원망", "anger", "resentment", "frustration", "배신"],
    "자기혐오·수치": ["자기혐오", "수치", "죄책감", "shame", "guilt", "self-hatred", "후회"],
    "성장·회복": ["성장", "회복", "치유", "healing", "growth", "resilience", "회복력"],
    "관계·갈등": ["관계", "갈등", "부부", "가족", "conflict", "relationship", "소통"],
    "인생의미·목적": ["의미", "목적", "삶", "meaning", "purpose", "존재", "실존"],
    "철학·성경": ["철학", "성경", "지혜", "philosophy", "bible", "wisdom", "현자"],
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


def _build_tavily_rag_context() -> str:
    """저장된 Tavily 검색 결과를 젬마 컨텍스트로 반환"""
    history = st.session_state.get("popup_search_history", [])
    if not history:
        return ""
    ctx = "\n[인터넷 리서치 자료 (Tavily — 자동 수집)]\n"
    for item in history[-5:]:  # 최근 5개 검색
        q = item.get("q", "")
        res = item.get("res", {})
        ctx += f"\n🔎 검색어: {q}\n"
        if res.get("answer"):
            ctx += f"  즉시답변: {res['answer'][:200]}\n"
        for r in res.get("results", [])[:3]:
            ctx += f"  - [{r.get('title','')}]: {r.get('content','')[:200]}\n"
            ctx += f"    [SOURCE: {r.get('url','')}]\n"
        if res.get("gemma_analysis"):
            ctx += f"  젬마 분석: {res['gemma_analysis'][:300]}\n"
    return ctx


def _classify_emotion_tags(text: str) -> dict:
    """텍스트에서 심리학 감정 태그를 자동 분류"""
    text_lower = text.lower()
    matched = {}
    for category, keywords in PSYCHOLOGY_EMOTION_TAGS.items():
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

        # 감정 태그 자동 분류
        emotion_tags = _classify_emotion_tags(content + " " + title)

        # 젬마로 키워드 추출
        kw_prompt = f"""아래 내용에서 옵시디언 RAG 태그로 사용할 핵심 키워드 6~8개를 쉼표로만 출력하라.
심리학 채널 특성상 감정, 인물(철학자/성경 인물), 개념, 주제를 포함할 것.
예시: 외로움, 쇼펜하우어, 자아성찰, 심리치유, 시편23편, 실존주의, 4070세대, 관계갈등

[내용]
{content[:600]}

[KEYWORDS]:"""
        try:
            kw_raw = call_gemma(kw_prompt, model=model_name)
            tag_list = [t.strip() for t in kw_raw.replace("#", "").split(",") if t.strip()][:8]
        except Exception:
            tag_list = ["세이지대화", "현자의거울", "심리치유", "자아성찰"]

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

        content_md = f"""# {title}

## 📌 메타데이터
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
            from app_v15_9_34_22 import save_workspace_state
            save_workspace_state()
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
            from app_v15_9_34_22 import save_workspace_state
            save_workspace_state()
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
AGENT_TOOL_PATTERNS = {
    "NEED_RESEARCH":  r"\[NEED_RESEARCH:\s*(.+?)\]",
    "READ_OBSIDIAN":  r"\[READ_OBSIDIAN:\s*(.+?)\]",
    "SAVE_MEMORY":    r"\[SAVE_MEMORY:\s*(.+?)\]",
    "VERIFY":         r"\[VERIFY:\s*(.+?)\]",
    "ANALYZE":        r"\[ANALYZE:\s*(.+?)\]",
    "CHECK_SOURCE":   r"\[CHECK_SOURCE:\s*(.+?)\]",
}

def _detect_tools(response: str) -> list:
    """젬마 응답에서 툴 태그 전체 감지"""
    detected = []
    for tool_name, pattern in AGENT_TOOL_PATTERNS.items():
        matches = _re_agent.findall(pattern, response)
        for m in matches:
            detected.append({"tool": tool_name, "param": m.strip()})
    # 자료부족 키워드도 감지 (기존 방식)
    unsure_kws = ["자료가 부족", "확실하지 않", "모르겠습니다", "알 수 없", "정보가 없"]
    if any(kw in response for kw in unsure_kws) and not detected:
        detected.append({"tool": "NEED_RESEARCH", "param": "자동감지"})
    return detected

def _execute_tool(tool: str, param: str, question: str, model: str, part_key: str) -> str:
    """툴 태그 실행 → 결과 반환"""
    result = ""

    if tool == "NEED_RESEARCH":
        # Tavily 웹 검색
        query = question if param == "자동감지" else param
        if st.session_state.get("tavily_api_key"):
            try:
                sr = tavily_search(query, st.session_state.tavily_api_key, max_results=4)
                if sr.get("results"):
                    result = f"\n[🌐 웹 검색 결과 — {query}]\n"
                    result += "\n".join([
                        f"- {r.get('title','')}: {r.get('content','')[:300]} [SOURCE: {r.get('url','')}]"
                        for r in sr["results"][:4]
                    ])
                    # 검색 기록 저장
                    if "popup_search_history" not in st.session_state:
                        st.session_state.popup_search_history = []
                    st.session_state.popup_search_history.append({"q": query, "res": sr})
            except Exception as e:
                result = f"[검색 실패: {e}]"
        else:
            result = "[Tavily API Key 미설정]"

    elif tool == "READ_OBSIDIAN":
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

    elif tool == "SAVE_MEMORY":
        # 옵시디언 자동 저장
        try:
            _save_to_obsidian_with_tags(
                content=f"[주제] {param}\n\n[저장 요청 시각] {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                title=param[:50],
                source_type="젬마 자동 저장 요청",
                part_key=part_key,
                model_name=model,
            )
            result = f"[✅ 옵시디언 저장 완료: {param}]"
        except Exception as e:
            result = f"[저장 실패: {e}]"

    elif tool == "VERIFY":
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

    elif tool == "ANALYZE":
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

    elif tool == "CHECK_SOURCE":
        # 출처 검증 (Tavily로 실제 존재 여부 확인)
        if st.session_state.get("tavily_api_key"):
            try:
                sr = tavily_search(param, st.session_state.tavily_api_key, max_results=3)
                if sr.get("results"):
                    result = f"\n[✅ 출처 검증 — {param}]\n"
                    result += "\n".join([
                        f"- {r.get('title','')}: {r.get('url','')} [SOURCE: {r.get('url','')}]"
                        for r in sr["results"][:3]
                    ])
                else:
                    result = f"[⚠️ 출처 미확인: {param} — Gemma 추론으로 표기 필요]"
            except Exception as e:
                result = f"[출처 검증 실패: {e}]"

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

        # 젬마 응답 생성
        if stream_placeholder and iteration == 0:
            # 첫 번째 반복만 스트리밍
            full_response = ""
            try:
                for token in call_gemma_stream(enriched_prompt, system=sys_ctx, model=model):
                    full_response += token
                    stream_placeholder.markdown(full_response + "▌")
                stream_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"[오류] {e}"
                if stream_placeholder:
                    stream_placeholder.error(full_response)
        else:
            # 이후 반복은 일반 호출
            try:
                full_response = call_gemma(enriched_prompt, sys_ctx, model=model)
                if stream_placeholder:
                    stream_placeholder.markdown(full_response)
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

            result = _execute_tool(tool_name, tool_param, question, model, part_key)
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
@st.dialog("🤖 세이지 팝업 — Gemma × Tavily × Obsidian RAG", width="large")
def popup_assistant():
    # ── 상태 초기화 ──
    defaults = {
        "popup_selected_model": OLLAMA_MODEL,
        "popup_history": [],
        "popup_search_history": [],
        "pending_stream": None,
        "popup_chat_input_ta": "",
        "popup_auto_search": True,
        "popup_use_rag": True,
        "tavily_rag_context": "",
        "part_action_quick_input": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

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
        "💬 Gemma 대화",
        "🌐 Tavily 인터넷 리서치",
        "📎 파일 업로드 저장",
        "⚙️ 파트 작업 지시"
    ])

    # ══════════════════════════════════════════════════════
    # 탭 1: Gemma 대화
    # ══════════════════════════════════════════════════════
    with tab_chat:
        st.markdown("##### 💬 대화 기록 (스크롤 / 드래그 복사)")
        chat_container = st.container(height=340, border=True)

        st.markdown("##### ✏️ 질문 입력")
        st.text_area(
            "질문 입력", key="popup_chat_input_ta",
            placeholder=(
                "현자에게 물어보세요...\n\n"
                "예: '이 파트의 나레이션을 더 감성적으로 수정해줘'\n"
                "예: '빅터 프랭클의 의미치료에 대해 설명해줘'\n"
                "예: '지금 수집된 인터넷 자료를 요약해줘'"
            ),
            height=110, label_visibility="collapsed",
        )

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            auto_search = st.checkbox("🌐 모를 때 Tavily 자동 검색",
                                      value=st.session_state.get("popup_auto_search", True),
                                      key="popup_auto_search_cb")
            st.session_state.popup_auto_search = auto_search
        with col_opt2:
            use_rag = st.checkbox("🧠 옵시디언 + 인터넷 자료 주입",
                                   value=st.session_state.get("popup_use_rag", True),
                                   key="popup_use_rag_cb")
            st.session_state.popup_use_rag = use_rag

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.button("📤 전송", use_container_width=True, key="popup_send",
                      type="primary", on_click=_on_popup_send)
        with c2:
            back = st.button(f"⬅️ 뒤로 ({len(st.session_state.popup_history) // 2})",
                             use_container_width=True, key="popup_back",
                             disabled=len(st.session_state.popup_history) < 2)
        with c3:
            clear = st.button("🗑️ 초기화", use_container_width=True, key="popup_clear")
        with c4:
            if st.session_state.popup_history:
                all_chat = "\n\n".join(
                    f"### [{m['role'].upper()}]\n{m['content']}"
                    for m in st.session_state.popup_history
                )
                st.download_button("📥 .md", data=all_chat,
                                   file_name=f"sage_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                   use_container_width=True, key="popup_dl")

        if back and len(st.session_state.popup_history) >= 2:
            st.session_state.popup_history = st.session_state.popup_history[:-2]
            st.rerun()
        if clear:
            st.session_state.popup_history = []
            st.session_state.pending_stream = None
            st.rerun()

        # 대화 기록 렌더링
        with chat_container:
            if not st.session_state.popup_history and not st.session_state.get("pending_stream"):
                st.markdown(
                    "<div style='color:#888;padding:20px;text-align:center;'>"
                    "💭 아직 대화가 없습니다.<br><br>"
                    "<small style='color:#d4af6a;'>"
                    "• 수집된 인터넷 자료를 젬마가 자동 참조합니다<br>"
                    "• 모를 때는 자동으로 Tavily 검색 후 보완합니다<br>"
                    "• 모든 대화는 옵시디언에 태그 분류 후 자동 저장됩니다"
                    "</small></div>",
                    unsafe_allow_html=True,
                )
            for msg in st.session_state.popup_history:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,#1a3a5c,#0d2440);"
                        f"border-left:3px solid #d4af6a;padding:10px 14px;margin:6px 0;"
                        f"border-radius:0 8px 8px 0;'>"
                        f"<b style='color:#d4af6a;'>🧑 사용자</b><br>"
                        f"<span style='color:#f5e9d3;white-space:pre-wrap;'>{msg['content']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    model_used = msg.get("model", sel_model)
                    source_info = msg.get("source", "")
                    st.markdown(
                        f"<div style='background:linear-gradient(135deg,#2d1b00,#1a1000);"
                        f"border-left:3px solid #10B981;padding:8px 14px;margin:6px 0;"
                        f"border-radius:0 8px 8px 0;'>"
                        f"<b style='color:#10B981;'>🤖 Sage ({model_used})</b>"
                        f"{(' <small style=\"color:#555;\">| ' + source_info + '</small>') if source_info else ''}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg['content'])
                    with st.expander("📋 복사용 텍스트", expanded=False):
                        st.code(msg["content"], language="markdown")

            # 스트리밍 처리
            if st.session_state.get("pending_stream"):
                q_stream = st.session_state.pending_stream
                current_model = st.session_state.popup_selected_model

                # ── 통합 시스템 컨텍스트 구성 ─────────────────────
                try:
                    from sage_config import RAG_TAG_SYSTEM as _rts
                except Exception:
                    _rts = ""
                sys_ctx = SAGE_PERSONA + "\n\n" + (_rts if _rts else "")

                # 젬마 프로토콜 v9.0 주입
                gemma_protocol = st.session_state.get("p1_gemma_protocol", "")
                if gemma_protocol:
                    sys_ctx += "[젬마 프로토콜]\n" + gemma_protocol + "\n\n"

                sys_ctx += "[핵심 3원칙]\n"
                sys_ctx += "HOW (어떻게 말하는가) → 자유 (창의·표현·서사)\n"
                sys_ctx += "WHAT (무엇을 말하는가) → 통제 (사실 기반·출처 필수)\n"
                sys_ctx += "WHO (누구로서 말하는가) → 고정 (@Protagonist·기승전결)\n\n"
                sys_ctx += "[응답 원칙]\n"
                sys_ctx += "1. 모르면 [NEED_RESEARCH: 키워드] 태그 출력. 절대 추측 금지.\n"
                sys_ctx += "2. 옵시디언 자료 필요시 [READ_OBSIDIAN: 키워드] 출력.\n"
                sys_ctx += "3. 자동 저장 요청시 [SAVE_MEMORY: 제목] 출력.\n"
                sys_ctx += "4. 자체 검증 필요시 [VERIFY: 내용] 출력.\n"
                sys_ctx += "5. 심층 분석 필요시 [ANALYZE: 주제] 출력.\n"
                sys_ctx += "6. 출처 확인 필요시 [CHECK_SOURCE: 인용구] 출력.\n"
                sys_ctx += "7. [SOURCE: 출처] 반드시 명기. 가짜 성경 구절·철학 인용 절대 금지.\n\n"
                sys_ctx += "[현재 파트 컨텍스트]\n" + _build_part_context(current_part_key) + "\n"
                sys_ctx += "[옵시디언 규칙서]\n" + st.session_state.get("obsidian_rules", "") + "\n"
                if st.session_state.get("popup_use_rag", True):
                    sys_ctx += "\n" + _build_obsidian_rag_context()
                    tavily_ctx = _build_tavily_rag_context()
                    if tavily_ctx:
                        sys_ctx += "\n" + tavily_ctx

                # ── 에이전트 루프 실행 ────────────────────────────
                with st.status("🔮 젬마 에이전트 작동 중...", expanded=True) as status_widget:
                    st.write(f"모델: {current_model} | 파트: {current_part_name}")
                    ans_placeholder = st.empty()
                    full_response = ""

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
                        full_response = f"[오류] {e}\n→ Ollama 서버 실행 여부 확인"
                        ans_placeholder.error(full_response)
                        status_widget.update(label="❌ 오류", state="error", expanded=False)

                st.session_state.popup_history.append({
                    "role": "assistant", "content": full_response,
                    "model": current_model, "part": current_part_name,
                    "source": f"에이전트 루프 v1.0",
                })
                st.session_state.pending_stream = None

                # 대화 옵시디언 자동 저장
                try:
                    _save_to_obsidian_with_tags(
                        content=f"[Q] {q_stream}\n\n[A] {full_response}",
                        title=f"[Chat] {q_stream[:30]}",
                        source_type="Sage 팝업 대화",
                        part_key=current_part_key,
                        model_name=current_model,
                    )
                    st.toast("🧠 대화 옵시디언 자동 저장!", icon="💾")
                except Exception:
                    pass

                st.rerun()

    # ══════════════════════════════════════════════════════
    # 탭 2: Tavily 인터넷 리서치
    # ══════════════════════════════════════════════════════
    with tab_tavily:
        st.markdown("##### 🌐 인터넷 리서치 (Tavily)")
        st.info(
            "🔍 **검색한 모든 자료는:**\n"
            "① 젬마 대화 탭에서 자동으로 컨텍스트로 활용됩니다\n"
            "② 심리학 감정 태그로 세분화되어 옵시디언에 자동 저장됩니다\n"
            "③ 저장된 자료는 다음 검색 때도 젬마가 참조합니다",
            icon="💡"
        )

        sq = st.text_area(
            "검색어", key="tavily_q_ta",
            placeholder=(
                "예: 빅터 프랭클 의미치료 사례\n"
                "예: 쇼펜하우어 의지와 표상으로서의 세계\n"
                "예: 4070 세대 유튜브 심리학 채널 트렌드\n"
                "예: 시편 23편 목자 의미 해석"
            ),
            height=100, label_visibility="collapsed",
        )

        # 심리학 감정 태그 선택 (수동 추가)
        with st.expander("🎭 감정 태그 수동 추가 (선택)", expanded=False):
            st.caption("검색 주제와 관련된 감정 태그를 선택하면 옵시디언 분류에 활용됩니다.")
            selected_emotion_cats = []
            cols = st.columns(2)
            for i, cat in enumerate(PSYCHOLOGY_EMOTION_TAGS.keys()):
                with cols[i % 2]:
                    if st.checkbox(cat, key=f"emotion_tag_{i}"):
                        selected_emotion_cats.append(cat)

        # 검색 옵션
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            analyze_with_gemma = st.checkbox("🤖 젬마로 자동 분석 후 정리", value=True, key="tavily_gemma_analyze")
        with col_o2:
            auto_obs_save = st.checkbox("💾 옵시디언 자동 저장", value=True, key="tavily_auto_obs")

        c1, c2, c3 = st.columns(3)
        with c1:
            do_search = st.button("🔍 인터넷 검색", key="tavily_search_btn",
                                  use_container_width=True, type="primary")
        with c2:
            sback = st.button(f"⬅️ 이전 ({len(st.session_state.popup_search_history)})",
                              key="tavily_back", use_container_width=True,
                              disabled=len(st.session_state.popup_search_history) == 0)
        with c3:
            sclear = st.button("🗑️ 초기화", key="tavily_clear", use_container_width=True)

        if sback and st.session_state.popup_search_history:
            st.session_state.popup_search_history.pop()
            st.rerun()
        if sclear:
            st.session_state.popup_search_history = []
            st.rerun()

        if do_search and sq.strip():
            if not st.session_state.get("tavily_api_key"):
                st.error("⚠️ Tavily API Key가 없습니다. 사이드바 설정에서 입력해 주세요.")
            else:
                with st.spinner("🌐 Tavily 검색 중..."):
                    try:
                        res = tavily_search(sq, st.session_state.tavily_api_key)

                        # 젬마 자동 분석
                        if analyze_with_gemma and res.get("results"):
                            raw_results = "\n".join([
                                f"[{r.get('title','')}] {r.get('content','')[:300]} (URL: {r.get('url','')})"
                                for r in res.get("results", [])[:5]
                            ])
                            analysis_prompt = f"""[지시] 아래 인터넷 검색 결과를 현자의 거울 스튜디오 옵시디언 형식으로 분석하라.

[검색어]
{sq}

[현재 파트]
{current_part_name}

[검색 결과 원문]
{raw_results}

[출력 형식 — 반드시 준수]
## 🔎 핵심 요약 (3줄)
(핵심 내용 3줄 요약)

## 📖 심층 분석
(내용 분석 + 현자의 거울 주제 연관성)

## 💡 파트 활용 방안
({current_part_name}에서 이 자료를 어떻게 활용할 수 있는가)

## 🎭 심리학 감정 연결
(이 자료와 연결되는 시청자 감정 상태: 외로움/불안/상실/무기력 등)

## 📚 참고 문헌 / 출처
(URL 목록 — [SOURCE: URL] 형식)

[SOURCE: Tavily 검색 — {datetime.now().strftime('%Y-%m-%d')}]"""
                            gemma_analysis = call_gemma(
                                analysis_prompt,
                                model=st.session_state.popup_selected_model
                            )
                            res["gemma_analysis"] = gemma_analysis
                        else:
                            gemma_analysis = ""

                        st.session_state.popup_search_history.append({"q": sq, "res": res})

                        # 감정 태그 자동 분류
                        all_content = sq + " " + " ".join([r.get("content", "") for r in res.get("results", [])[:5]])
                        auto_emotion_tags = list(_classify_emotion_tags(all_content).keys())
                        all_extra_tags = selected_emotion_cats + auto_emotion_tags

                        # 옵시디언 자동 저장 (심리학 태그 세분화)
                        if auto_obs_save:
                            save_content = f"[검색어]\n{sq}\n\n"
                            if gemma_analysis:
                                save_content += f"[젬마 분석]\n{gemma_analysis}\n\n"
                            save_content += "[원문 결과]\n"
                            for r in res.get("results", [])[:5]:
                                save_content += f"\n### [{r.get('title','')}]({r.get('url','')})\n{r.get('content','')[:500]}\n[SOURCE: {r.get('url','')}]\n"

                            saved_path = _save_to_obsidian_with_tags(
                                content=save_content,
                                title=f"[리서치] {sq[:40]}",
                                source_type="Tavily 인터넷 검색",
                                part_key=current_part_key,
                                model_name=st.session_state.popup_selected_model,
                                extra_tags=all_extra_tags,
                                folder_override="WebResearch",
                            )
                            if saved_path:
                                st.toast(f"🧠 옵시디언 자동 저장 완료! (감정 태그 {len(auto_emotion_tags)}개)", icon="💾")

                        st.rerun()

                    except Exception as e:
                        st.error(f"검색 실패: {e}")

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
                st.markdown(f"**🔎 검색어:** `{latest['q']}`")
                res = latest["res"]
                if "error" in res:
                    st.error(res["error"])
                else:
                    if res.get("gemma_analysis"):
                        st.markdown("### 🤖 젬마 분석 결과")
                        st.markdown(res["gemma_analysis"])
                        with st.expander("📋 복사용", expanded=False):
                            st.code(res["gemma_analysis"], language="markdown")
                        st.divider()
                    if res.get("answer"):
                        st.info(f"💡 **즉시 답변:** {res['answer']}")
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
