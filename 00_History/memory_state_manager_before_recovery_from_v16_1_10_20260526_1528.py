import json
import os
import re
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# 🗂️ 현자의 거울 — 메모리 레이어 관리 시스템 v1.0
# ══════════════════════════════════════════════════════════════

# 1. clean_prompt_contamination (오염 방지 필터)
def clean_prompt_contamination(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    import re as _re
    
    # span tag block 전체를 제거하는 정규식
    pattern1 = _re.compile(r'<span title=["\']리서치 자동저장 대기 중["\'].*?</span>', _re.DOTALL)
    text = pattern1.sub('', text)
    
    # style 속성이 있는 열린 span 태그 전체 제거를 대비한 정규식
    pattern2 = _re.compile(r'<span title=["\']리서치 자동저장 대기 중["\'][^>]*>', _re.DOTALL)
    text = pattern2.sub('', text)
    
    # 개별 조각 치환 (반드시 제거할 패턴 목록 반영)
    targets = [
        '<span title="리서치 자동저장 대기 중"',
        "<span title='리서치 자동저장 대기 중'",
        'display: inline-block;',
        'width: 14px;',
        'height: 14px;',
        'background-color:',
        'border-radius:',
        'box-shadow:',
        'transition:',
        '"></span>',
        '</span>',
        '즉석 실시간 구글 리서치 & 저장',
        '검색 키워드 입력',
        '💾 리서치 & 저장',
        '[SEARCH] 편집',
        '💾 자동저장: ON',
        '📂 저장 확인'
    ]
    for target in targets:
        text = text.replace(target, '')
        text = _re.sub(
            r'(?is)<span\s+title=["\']?리서치\s*자동저장\s*대기\s*중["\']?.*?</span>',
            '',
            text
        )
        text = _re.sub(r'(?im)^\s*display\s*:\s*inline-block\s*;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*width\s*:\s*14px\s*;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*height\s*:\s*14px\s*;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*background-color\s*:\s*#[0-9a-fA-F]{3,6}\s*;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*border-radius\s*:\s*50%\s*;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*box-shadow\s*:.*?;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*transition\s*:.*?;\s*$', '', text)
        text = _re.sub(r'(?im)^\s*["\']?\s*>\s*</span>\s*$', '', text)
        text = _re.sub(r'(?im)^\s*</span>\s*$', '', text)
        text = _re.sub(r'\n{3,}', '\n\n', text)    
    return text.strip()

# 2. sanitize_workspace_prompt_values_once_core (부팅 시 워크스페이스 상태 일괄 정화)
def sanitize_workspace_prompt_values_once_core(workspace_file_path: str) -> bool:
    try:
        workspace_path = Path(workspace_file_path)
        if not workspace_path.exists():
            return False

        with open(workspace_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        def recursive_clean(obj):
            nonlocal changed
            if isinstance(obj, dict):
                return {k: recursive_clean(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [recursive_clean(v) for v in obj]
            elif isinstance(obj, str):
                cleaned = clean_prompt_contamination(obj)
                if cleaned != obj:
                    changed = True
                return cleaned
            return obj

        cleaned_data = recursive_clean(data)
        if changed:
            with open(workspace_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            return True
    except Exception as e:
        print(f"[SANITIZE_ERROR] {e}")
    return False

# 3. save_workspace_state_core (st.session_state 딕셔너리를 받아서 파일 저장 및 정화)
def save_workspace_state_core(state_dict: dict, workspace_file: str, secrets_file: str) -> tuple[dict, dict, bool]:
    secrets_keys = ["github_token", "github_pat", "tavily_api_key", "youtube_api_key", "gemini_api_key"]
    keys_to_save = [
        "path_obsidian", "github_repo_url", "p1_gemini_model", "p1_channel_top10", "p1_benchmark_channel", "p1_search_keywords",
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        "p1_channel_url", "p1_region", "p1_topics", "p1_topic_selection",
        "p1_research_result", "p1_planning_result", "unlock_part1",
        "p1_bench_prompt", "p1_research_prompt", "p1_plan_prompt",
        "p1_bench_raw", "p1_bench_tags", "p1_research_tags", "p1_plan_tags",
        "p1_bench_saved", "p1_bench_obsidian_saved", "p1_research_saved", "p1_research_obsidian_saved", "p1_plan_saved", "p1_plan_obsidian_saved",
        "p2_topic_selection", "p2_research_result", "p2_planning_result", "p2_obsidian_search_results",
        "p2_gemma_protocol", "p2_thumbnail_sets", "p2_selected_thumbnail",
        "p2_thumbnail_plan", "unlock_part2",
        "p2_bench_prompt", "p2_bench_raw", "p2_bench_tags", "p2_bench_saved", "p2_bench_obsidian_saved",
        "p2_research_prompt", "p2_research_tags", "p2_research_saved", "p2_research_obsidian_saved",
        "p2_plan_prompt", "p2_plan_tags", "p2_plan_saved", "p2_plan_obsidian_saved",
        "p34_gemma_protocol", "p34_master_prompt", "unlock_part34",
        "p34_scene_structure", "p34_narration_script", "p34_image_script", "p34_capcut_data",
        "p34_narr_prompt", "p34_img_prompt", "p34_cap_prompt",
        "p34_arch_saved", "p34_arch_obsidian_saved", "p34_narr_saved", "p34_narr_obsidian_saved",
        "p34_img_saved", "p34_img_obsidian_saved", "p34_cap_saved", "p34_cap_obsidian_saved",
        "p5_image_master_prompt", "unlock_part5", 
        "p6_veo3_master_prompt", "p6_gemma_protocol", "p6_protocol_loaded", "p6_vid_pin_input", "unlock_part6_vid",
        "p6_master_prompt", "p7_master_prompt", "p8_master_prompt",
        "p1_verification", "p2_verification", "p2_plan_verification", "p34_narr_verification", "p34_img_verification",
        "p1_need_research_kw", "p2_need_research_kw", "p2_plan_need_research_kw", "p34_narr_need_research_kw", "p34_img_need_research_kw",
        "unlock_part6", "unlock_part7", "unlock_part8", "p6_opal_data", "p7_capcut_data_v2", "p7_capcut_data",
        "p7_script_input", "p7_scenes_input", "p7_video_style_input", "p7_bgm_style_input", "p7_subtitle_style_input",
        "p6_bgm_selection", "p6_mixing_ratio", "p6_narration_verified", "p6_opal_saved", "p6_opal_obsidian_saved",
        "p7_capcut_saved", "p7_capcut_obsidian_saved", "p8_dashboard_saved", "p8_dashboard_obsidian_saved",
        "selected_model",
        "global_model_select",
        "p1_selected_model", "p2_selected_model", "p34_selected_model", "p5img_selected_model", "p6vid_selected_model", "p6_selected_model", "p7_selected_model", "p8_selected_model",
        "episode_name", "p6_video_mapped_result", "p6_video_valid_rows", "p6_video_opal_data", "p6_video_opal_saved",
        "p34_outputs_saved", "p5_outputs_saved", "p6_outputs_saved", "p6_video_outputs_saved", "p7_outputs_saved",
        "research_auto_save", "research_auto_save_success",
        "p1_obsidian_search_results", "p2_obsidian_search_results", "p3_obsidian_search_results", "p4_obsidian_search_results",
        "p5_obsidian_search_results", "p6_obsidian_search_results", "p7_obsidian_search_results", "p8_obsidian_search_results",
        "p5_rag_query_val", "p5_selected_categories",
        "p6_rag_query_val", "p6_selected_categories",
        "p7_rag_query_val", "p7_selected_categories",
        "p8_rag_query_val", "p8_selected_categories",
        "part1_selected_categories", "part2_selected_categories",
        "part3_selected_categories", "part4_selected_categories",
        "p1_rag_model_selector", "p2_rag_model_selector", "p3_rag_model_selector", "p4_rag_model_selector",
        "p5_rag_model_selector", "p6_rag_model_selector", "p7_rag_model_selector", "p8_rag_model_selector",
        "p1_research_result_obsidian_saved", "p1_research_result_obsidian_path",
        "p1_planning_result_obsidian_saved", "p1_planning_result_obsidian_path",
        "p2_research_result_obsidian_saved", "p2_research_result_obsidian_path",
        "p2_planning_result_obsidian_saved", "p2_planning_result_obsidian_path",
        "p2_bench_raw_obsidian_saved", "p2_bench_raw_obsidian_path",
        "p34_narration_script_obsidian_saved", "p34_narration_script_obsidian_path",
        "p34_image_script_obsidian_saved", "p34_image_script_obsidian_path",
        "p5_a_result_obsidian_saved", "p5_a_result_obsidian_path",
        "p5_b_result_obsidian_saved", "p5_b_result_obsidian_path",
        "p5_c_results_obsidian_saved", "p5_c_results_obsidian_path",
        "p6_veo3_result_obsidian_saved", "p6_veo3_result_obsidian_path"
    ]

    contam_keys = [
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        "p2_gemma_protocol", "p2_bench_prompt", "p2_research_prompt",
        "p2_plan_prompt", "p34_master_prompt", "p5_image_master_prompt",
        "p6_veo3_master_prompt", "p6_master_prompt", "p7_master_prompt",
        "p8_master_prompt"
    ]

    data = {}
    cleaned_state_updates = {}
    for k in keys_to_save:
        if k in state_dict:
            val = state_dict[k]
            if k in contam_keys and isinstance(val, str):
                cleaned_val = clean_prompt_contamination(val)
                if cleaned_val != val:
                    cleaned_state_updates[k] = cleaned_val
                val = cleaned_val
            data[k] = val

    secrets_data = {}
    for k in secrets_keys:
        if k in state_dict:
            secrets_data[k] = state_dict[k]

    success = False
    try:
        with open(workspace_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if secrets_data:
            with open(secrets_file, "w", encoding="utf-8") as f:
                json.dump(secrets_data, f, ensure_ascii=False, indent=4)
        success = True
    except Exception as e:
        print(f"[SAVE_WORKSPACE_ERROR] {e}")

    return cleaned_state_updates, secrets_data, success

# 4. load_workspace_state_core (워크스페이스 설정값 로드 및 일괄 정화)
def load_workspace_state_core(workspace_file: str, secrets_file: str) -> dict:
    data = {}
    if os.path.exists(workspace_file):
        try:
            with open(workspace_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if os.path.exists(secrets_file):
        try:
            with open(secrets_file, "r", encoding="utf-8") as f:
                secrets = json.load(f)
                data.update(secrets)
        except Exception:
            pass

    contam_keys = [
        "obsidian_rules", "base_prompt_rules", "p1_gemma_protocol",
        "p2_gemma_protocol", "p2_bench_prompt", "p2_research_prompt",
        "p2_plan_prompt", "p34_master_prompt", "p5_image_master_prompt",
        "p6_veo3_master_prompt", "p6_master_prompt", "p7_master_prompt",
        "p8_master_prompt"
    ]
    for ck in contam_keys:
        if ck in data and isinstance(data[ck], str):
            data[ck] = clean_prompt_contamination(data[ck])

    try:
        with open(workspace_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    
    return data

# 5. extract_text_from_uploaded_file (업로드 파일 텍스트 추출 Core)
def extract_text_from_uploaded_file(uploaded_file) -> str | None:
    if not uploaded_file:
        return None
    try:
        filename = uploaded_file.name
        suffix = Path(filename).suffix.lower()
        
        if suffix in [".txt", ".md"]:
            try:
                raw_bytes = uploaded_file.read()
                for enc in ["utf-8", "cp949", "euc-kr"]:
                    try:
                        return raw_bytes.decode(enc)
                    except Exception:
                        continue
                return raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                return None
                
        elif suffix in [".html", ".htm"]:
            try:
                raw_bytes = uploaded_file.read()
                html_content = ""
                for enc in ["utf-8", "cp949", "euc-kr"]:
                    try:
                        html_content = raw_bytes.decode(enc)
                        break
                    except Exception:
                        continue
                if not html_content:
                    html_content = raw_bytes.decode("utf-8", errors="ignore")
                
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_content, "html.parser")
                    for script_or_style in soup(["script", "style"]):
                        script_or_style.decompose()
                    return soup.get_text()
                except Exception:
                    import re as _re
                    text = _re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=_re.DOTALL | _re.IGNORECASE)
                    text = _re.sub(r'<[^>]*>', '', text)
                    return text
            except Exception:
                return None
                
        elif suffix == ".pdf":
            try:
                import io
                try:
                    from pypdf import PdfReader
                except ImportError:
                    try:
                        from PyPDF2 import PdfReader
                    except ImportError:
                        return None
                
                raw_bytes = uploaded_file.read()
                reader = PdfReader(io.BytesIO(raw_bytes))
                pages = []
                for page in reader.pages:
                    try:
                        text = page.extract_text()
                        if text:
                            pages.append(text)
                    except Exception:
                        pass
                if pages:
                    return "\n\n".join(pages)
                else:
                    return None
            except Exception:
                return None
        else:
            return None
    except Exception:
        return None

# 6. convert_text_to_markdown_structure (텍스트 마크다운 구조화 Core)
def convert_text_to_markdown_structure(raw_text: str, source_name: str = "unknown") -> str:
    if not raw_text or not isinstance(raw_text, str):
        return ""
    
    import re as _re
    from datetime import datetime as _dt
    
    is_truncated = False
    if len(raw_text) > 50000:
        raw_text = raw_text[:50000]
        is_truncated = True
        
    text = _re.sub(r'<[^>]*>', '', raw_text)
    text = _re.sub(r'[ \t]+', ' ', text)
    text = _re.sub(r'([=\-*_#~])\1{2,}', r'\1\1\1', text)
    text = _re.sub(r'[ \t]+\n', '\n', text)
    text = _re.sub(r'\n{3,}', '\n\n', text)
    
    cleaned_text = text.strip()
    if is_truncated:
        cleaned_text += "\n\n[문서 일부 생략됨 (50,000자 초과)]"
        
    summary_sentences = []
    sentences = _re.split(r'(?<=[.!?])\s+', cleaned_text[:1000])
    for s in sentences:
        s_strip = s.strip()
        if s_strip and not s_strip.startswith(('#', '-', '*', '=')) and len(s_strip) > 5:
            summary_sentences.append(s_strip)
        if len(summary_sentences) >= 3:
            break
            
    if summary_sentences:
        summary = "\n".join([f"- {s}" for s in summary_sentences])
    else:
        summary = f"- {cleaned_text[:150].replace('\n', ' ')}..."
        
    created_time = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"""# {source_name}

## 문서 정보
- SOURCE: 업로드 파일 ({source_name})
- TYPE: raw_import
- CREATED: {created_time}

---

## 핵심 요약

{summary}

---

## 원문 정리

{cleaned_text}
"""
    return md_content

# 7. build_all_parts_common_tags_preview (공용 태그 빌더 Core)
def build_all_parts_common_tags_preview(detection: dict, part_rag_tag_map: dict, unique_keep_order_fn) -> dict:
    all_tags = []
    for i in range(1, 9):
        part_key = f"part{i}"
        all_tags.extend(part_rag_tag_map.get(part_key, []))
    all_part_tags = unique_keep_order_fn(all_tags, limit=80)
    
    detected_keywords = detection.get("keywords", [])
    combined_keywords = unique_keep_order_fn(all_part_tags + detected_keywords, limit=120)
    
    all_part_wiki = [f"[[{tag}]]" for tag in all_part_tags]
    detected_wiki = detection.get("wiki_links", [])
    wiki_links = unique_keep_order_fn(all_part_wiki + detected_wiki, limit=120)
    
    def clean_hashtag(tag_str):
        tag_str = str(tag_str).strip()
        if not tag_str:
            return ""
        cleaned = re.sub(r"\s+", "_", tag_str)
        if not cleaned.startswith("#"):
            cleaned = "#" + cleaned
        return cleaned

    all_part_hash = [clean_hashtag(tag) for tag in all_part_tags if tag]
    detected_hash = [clean_hashtag(ht) for ht in detection.get("hash_tags", []) if ht]
    
    all_part_hash = [h for h in all_part_hash if h]
    detected_hash = [h for h in detected_hash if h]
    
    hash_tags = unique_keep_order_fn(all_part_hash + detected_hash, limit=120)
    
    return {
        "all_part_tags": all_part_tags,
        "detected_keywords": detected_keywords,
        "combined_keywords": combined_keywords,
        "wiki_links": wiki_links,
        "hash_tags": hash_tags
    }

# 8. save_reference_markdown_file (References 저장 Core)
def save_reference_markdown_file(markdown_text: str, preview_data: dict, source_name: str, ref_dir: str) -> str:
    try:
        os.makedirs(ref_dir, exist_ok=True)
        stem_name = Path(source_name).stem
        safe_stem = re.sub(r'[<>:"/\\|?*]', '', stem_name)
        safe_stem = re.sub(r'\s+', '_', safe_stem)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{safe_stem}_{timestamp}.md"
        full_path = os.path.join(ref_dir, filename)
        
        categories = preview_data.get("categories", [])
        all_part_tags = preview_data.get("all_part_tags", [])
        hash_tags = preview_data.get("hash_tags", [])
        wiki_links = preview_data.get("wiki_links", [])
        combined_keywords = preview_data.get("combined_keywords", [])
        
        categories_str = ", ".join(categories) if categories else "None"
        total_tags_str = ", ".join(all_part_tags) if all_part_tags else "None"
        
        hash_tags_spaced = " ".join(hash_tags) if hash_tags else ""
        wiki_links_spaced = " ".join(wiki_links) if wiki_links else ""
        keywords_bulleted = "\n".join([f"- {k}" for k in combined_keywords]) if combined_keywords else ""
        
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"""# {safe_stem}

## 메타데이터
- SOURCE_FILE: {source_name}
- CREATED: {created_time}
- IMPORT_TYPE: uploaded_reference
- RAG_CATEGORIES: {categories_str}
- TOTAL_TAGS: {total_tags_str}

---

## 전체 공용 태그

{hash_tags_spaced}

---

## 위키링크

{wiki_links_spaced}

---

## 핵심 키워드

{keywords_bulleted}

---

## 원문 정리

{markdown_text}
"""
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return full_path
    except Exception as e:
        print(f"[References 저장 오류] {e}")
        return ""

# 9. parse_markdown_reference (References 파싱 Core)
def parse_markdown_reference(content: str) -> dict:
    meta = {}
    keywords = []
    source = "Unknown"
    
    kw_match = re.findall(r'-\s+\[\[(.*?)\]\]', content)
    if kw_match:
        keywords = list(set(kw_match))
        
    src_match = re.search(r'- SOURCE:\s*(.*?)(?:\n|$)', content)
    if src_match:
        source = src_match.group(1).strip()
        
    lines = content.split("\n")
    for line in lines:
        if line.startswith("- SOURCE_FILE:"):
            meta["source_file"] = line.split(":", 1)[1].strip()
        elif line.startswith("- IMPORT_TYPE:"):
            meta["import_type"] = line.split(":", 1)[1].strip()
        elif line.startswith("- RAG_CATEGORIES:"):
            meta["categories"] = [c.strip() for c in line.split(":", 1)[1].strip().split(",") if c.strip()]
        elif line.startswith("- TOTAL_TAGS:"):
            meta["tags"] = [t.strip() for t in line.split(":", 1)[1].strip().split(",") if t.strip()]
            
    return {
        "metadata": meta,
        "keywords": keywords,
        "source": source
    }
