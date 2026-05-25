# -*- coding: utf-8 -*-

"""
🪞 현자의 거울 스튜디오 — RAG Memory Utility Module (v16.0.2)
- Streamlit 의존성(st.sidebar, st.caption, st.toast 등)이 완전히 제거된 순수 Python 유틸리티 파일입니다.
- RAG 로드, 파싱, 필터링 및 프롬프트 조립을 담당합니다.
"""

import os
import re
import glob
import sys
from pathlib import Path

def load_recent_reference_files(max_files: int = 20, max_chars: int = 120000) -> list:
    """Obsidian References 폴더의 최신 md 파일들을 안전하게 읽어와 메모리에 로드합니다."""
    loaded_files = []
    try:
        ref_dir = r"C:\SageMirror_Production\00_Obsidian\References"
        if not os.path.exists(ref_dir):
            return []
            
        # *.md 파일 검색
        files = glob.glob(os.path.join(ref_dir, "*.md"))
        # 수정 시간 기준 내림차순 정렬
        files_with_time = []
        for f in files:
            try:
                files_with_time.append((f, os.path.getmtime(f)))
            except Exception:
                continue
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        total_chars = 0
        for fpath, mtime in files_with_time[:max_files]:
            try:
                content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
                content_len = len(content)
                
                # 글자 수 상한 제한 (누적 max_chars)
                if total_chars + content_len > max_chars:
                    allowed_len = max_chars - total_chars
                    if allowed_len <= 0:
                        break
                    content = content[:allowed_len] + "\n\n[글자 수 초과로 인해 본문 일부 생략됨]"
                    loaded_files.append({
                        "filename": os.path.basename(fpath),
                        "content": content,
                        "mtime": mtime,
                        "truncated": True
                    })
                    total_chars = max_chars
                    break
                else:
                    loaded_files.append({
                        "filename": os.path.basename(fpath),
                        "content": content,
                        "mtime": mtime,
                        "truncated": False
                    })
                    total_chars += content_len
            except Exception:
                continue
    except Exception as e:
        sys.stderr.write(f"[References 로드 오류] {e}\n")
        
    return loaded_files


def build_gemma_memory_prompt_preview(memory_items: list, max_chars: int = 30000) -> str:
    """References 로드 결과를 바탕으로 젬마 주입용 메모리 프롬프트 블록을 구성합니다."""
    header = """[OBSIDIAN_REFERENCE_MEMORY]

역할:
이 자료는 사용자가 직접 업로드하여 References에 저장한 공용 기억이다.
Gemma는 아래 자료를 추측보다 우선한다.

사용 규칙:
1. 이 자료를 1차 근거로 삼는다.
2. 출처 없는 내용은 단정하지 않는다.
3. 핵심 개념은 [[위키링크]]로 연결한다.
4. 부족하면 [NEED_RESEARCH: 검색어]를 요청한다.
5. 답변에는 필요한 경우 [SOURCE: References — 파일명]을 붙인다.

[REFERENCE_FILES]
"""
    footer = "\n[/OBSIDIAN_REFERENCE_MEMORY]"
    
    def parse_markdown_reference(content_str: str) -> dict:
        summary = ""
        keywords = ""
        body_text = ""
        
        # 1. 원문 정리 파싱
        body_match = re.search(r"##\s*원문\s*정리\s*\n(.*)", content_str, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_text = body_match.group(1).strip()
        else:
            body_text = content_str.strip()
            
        # 2. 핵심 키워드 파싱
        kw_match = re.search(r"##\s*핵심\s*키워드\s*\n(.*?)(?=\n---|\n##)", content_str, re.DOTALL | re.IGNORECASE)
        if kw_match:
            keywords = kw_match.group(1).strip()
            
        # 3. 핵심 요약 파싱
        summary_match = re.search(r"##\s*핵심\s*요약\s*\n(.*?)(?=\n---|\n##)", content_str, re.DOTALL | re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()
        else:
            summary = body_text[:200].replace("\n", " ") + "..."
            
        return {
            "summary": summary or "None",
            "keywords": keywords or "None",
            "body": body_text
        }
        
    file_blocks = []
    for idx, item in enumerate(memory_items, 1):
        filename = item.get("filename", f"file_{idx}.md")
        content = item.get("content", "")
        
        parsed = parse_markdown_reference(content)
        
        body_preview = parsed["body"][:1200]
        if len(parsed["body"]) > 1200:
            body_preview += "\n...(이하 생략)..."
            
        block = f"""{idx}. 파일명: {filename}
요약: {parsed['summary']}
핵심 키워드: {parsed['keywords']}
본문 일부:
{body_preview}
"""
        file_blocks.append(block)
        
    files_content = "\n".join(file_blocks)
    prompt = header + files_content + footer
    
    if len(prompt) > max_chars:
        truncation_msg = "\n[메모리 일부 생략됨 — max_chars 제한]"
        allowed_len = max_chars - len(footer) - len(truncation_msg)
        if allowed_len > 0:
            prompt = prompt[:allowed_len] + truncation_msg + footer
        else:
            prompt = prompt[:max_chars]
            
    return prompt


def build_manual_gemma_memory_buffer(prompt_preview: str, max_chars: int = 32000) -> str:
    """Gemma Prompt Preview를 받아 실제 Assistant Prompt에 삽입 가능한 메모리 버퍼 문자열을 생성합니다."""
    header = """[ACTIVE_REFERENCE_MEMORY]

주의:
아래 메모리는 사용자가 직접 업로드하고 검토한 자료다.
Gemma는 아래 기억을 우선 참조한다.

규칙:
1. 추측보다 References 우선
2. 출처 없는 내용 단정 금지
3. 핵심 개념은 [[위키링크]] 유지
4. 필요 시 [SOURCE: References — 파일명] 표기
5. 기억 충돌 시 최신 자료 우선

[MEMORY_BLOCK]
"""
    footer = "\n[/MEMORY_BLOCK]\n\n[/ACTIVE_REFERENCE_MEMORY]"
    
    total_len = len(header) + len(prompt_preview) + len(footer)
    
    if total_len > max_chars:
        truncation_msg = "\n[메모리 일부 생략됨 — max_chars 제한]"
        allowed_len = max_chars - len(header) - len(footer) - len(truncation_msg)
        if allowed_len > 0:
            prompt_preview = prompt_preview[:allowed_len] + truncation_msg
        else:
            return (header + prompt_preview + footer)[:max_chars]
            
    return header + prompt_preview + footer


def build_manual_memory_injected_prompt(
    user_prompt: str,
    memory_buffer: str,
    max_chars: int = 40000
) -> str:
    """사용자 질문에 References 기억 버퍼를 결합하여 최종 Gemma 주입용 프롬프트를 빌드합니다."""
    middle_header = "\n\n[USER_REQUEST]\n\n"
    middle_footer = "\n\n[/USER_REQUEST]\n\n[ASSISTANT_RULE]\n\n위 메모리를 우선 참조하여 답변하라.\n출처 없는 내용은 추측하지 마라.\n필요 시 [SOURCE:] 표시를 유지하라.\n\n[/ASSISTANT_RULE]"
    
    # 기본 골격 크기
    base_len = len(middle_header) + len(middle_footer)
    
    # 만약 전체 결합 길이가 max_chars를 초과하면
    if len(memory_buffer) + len(user_prompt) + base_len > max_chars:
        truncation_msg = "\n[프롬프트 일부 생략됨 — max_chars 제한]"
        allowed_memory_len = max_chars - len(user_prompt) - base_len - len(truncation_msg)
        
        if allowed_memory_len > 0:
            memory_buffer = memory_buffer[:allowed_memory_len] + truncation_msg
        else:
            memory_buffer = ""
            allowed_user_len = max_chars - base_len - len(truncation_msg)
            user_prompt = user_prompt[:allowed_user_len] + truncation_msg
            
    return memory_buffer + middle_header + user_prompt + middle_footer


def build_condensed_reference_context(memory_items: list, max_chars: int = 30000) -> tuple:
    """
    RAG Memory Optimization Layer (v16.0.2)
    - 중복 제거, 너무 긴 본문 축약, 핵심 키워드 우선, SOURCE 유지, 위키링크 유지
    - 최근 저장 파일(최대 5~8개)은 상세 본문 포함, 오래된 자료는 본문 생략/자동 축약
    - 추가 안전 조건:
      1. 본문 300자 미만 제외
      2. span title, display: inline-block, background-color, 자동저장:, [EP001] 포함 제외
      3. SOURCE / 키워드 / 위키링크 모두 비어있는 파일 제외
      4. 동일 파일명 중복 시 mtime 기준 최신만 사용
    - 반환값: (prompt_preview: str, excluded_files: list)
    """
    header = """[OBSIDIAN_REFERENCE_MEMORY]

역할:
이 자료는 사용자가 직접 업로드하여 References에 저장한 공용 기억이다.
Gemma는 아래 자료를 추측보다 우선한다.

사용 규칙:
1. 이 자료를 1차 근거로 삼는다.
2. 출처 없는 내용은 단정하지 않는다.
3. 핵심 개념은 [[위키링크]]로 연결한다.
4. 부족하면 [NEED_RESEARCH: 검색어]를 요청한다.
5. 답변에는 필요한 경우 [SOURCE: References — 파일명]을 붙인다.

[REFERENCE_FILES]
"""
    footer = "\n[/OBSIDIAN_REFERENCE_MEMORY]"
    
    excluded_files = []
    
    try:
        if not memory_items:
            return "", []
            
        def parse_markdown_reference_v2(content_str: str) -> dict:
            source_match = re.search(r"-\s*SOURCE_FILE:\s*(.*)", content_str, re.IGNORECASE)
            source = source_match.group(1).strip() if source_match else ""
            
            cat_match = re.search(r"-\s*RAG_CATEGORIES:\s*(.*)", content_str, re.IGNORECASE)
            categories = cat_match.group(1).strip() if cat_match else ""
            
            wiki_match = re.search(r"##\s*위키링크\s*\n(.*?)(?=\n---|\n##)", content_str, re.DOTALL | re.IGNORECASE)
            wiki_links = wiki_match.group(1).strip() if wiki_match else ""
            
            kw_match = re.search(r"##\s*핵심\s*키워드\s*\n(.*?)(?=\n---|\n##)", content_str, re.DOTALL | re.IGNORECASE)
            keywords = kw_match.group(1).strip() if kw_match else ""
            
            summary_match = re.search(r"##\s*핵심\s*요약\s*\n(.*?)(?=\n---|\n##)", content_str, re.DOTALL | re.IGNORECASE)
            summary = summary_match.group(1).strip() if summary_match else ""
            
            body_match = re.search(r"##\s*원문\s*정리\s*\n(.*)", content_str, re.DOTALL | re.IGNORECASE)
            body_text = body_match.group(1).strip() if body_match else content_str.strip()
            
            if not summary:
                summary = body_text[:200].replace("\n", " ").strip() + "..."
                
            return {
                "source": source,
                "categories": categories,
                "wiki_links": wiki_links,
                "keywords": keywords,
                "summary": summary,
                "body": body_text
            }

        # 중복 파일명 필터링 (최신 파일만 사용)
        seen_filenames = set()
        unique_memory_items = []
        for item in memory_items:
            fname = item.get("filename", "")
            if not fname:
                continue
            if fname in seen_filenames:
                continue
            seen_filenames.add(fname)
            unique_memory_items.append(item)

        parsed_items = []
        global_wikilinks = set()
        
        # 오염/비정상 필터링
        for idx, item in enumerate(unique_memory_items):
            content = item.get("content", "")
            filename = item.get("filename", f"file_{idx+1}.md")
            
            polluted_keywords = ["<span title=", "display: inline-block", "background-color:", "자동저장:", "[EP001]"]
            if any(pw in content for pw in polluted_keywords):
                excluded_files.append((filename, "오염 단어 포함"))
                continue
                
            parsed = parse_markdown_reference_v2(content)
            
            if len(parsed["body"]) < 300:
                excluded_files.append((filename, "본문 300자 미만"))
                continue
                
            src_empty = not parsed["source"].strip()
            kw_clean = parsed["keywords"].replace("None", "").replace("-", "").strip()
            kw_empty = not kw_clean
            wiki_clean = parsed["wiki_links"].replace("None", "").strip()
            wiki_empty = not wiki_clean
            
            if src_empty and kw_empty and wiki_empty:
                excluded_files.append((filename, "메타데이터 부재"))
                continue

            parsed["filename"] = filename
            parsed_items.append(parsed)
            
            links = re.findall(r"\[\[(.*?)\]\]", parsed["wiki_links"])
            for link in links:
                global_wikilinks.add(link.strip())
                
        file_blocks = []
        for idx, parsed in enumerate(parsed_items, 1):
            filename = parsed["filename"]
            source = parsed["source"] or filename
            keywords = parsed["keywords"].replace("- ", "").replace("\n", ", ")
            keywords_list = [k.strip() for k in keywords.split(",") if k.strip() and k.lower() != "none"]
            unique_keywords = []
            for k in keywords_list:
                if k not in unique_keywords:
                    unique_keywords.append(k)
            keywords_str = ", ".join(unique_keywords) if unique_keywords else "None"
            
            summary = parsed["summary"]
            
            w_links = re.findall(r"\[\[(.*?)\]\]", parsed["wiki_links"])
            w_links_unique = []
            for wl in w_links:
                wl_strip = wl.strip()
                if wl_strip and wl_strip.lower() != "none" and wl_strip not in w_links_unique:
                    w_links_unique.append(wl_strip)
            w_links_str = " ".join([f"[[{wl}]]" for wl in w_links_unique]) if w_links_unique else "None"

            # 최근 8개만 상세 표시
            is_recent = (idx <= 8)
            
            block = []
            block.append(f"{idx}. [SOURCE: References — {filename}]")
            if parsed["source"] and parsed["source"] != filename:
                block.append(f"   원본 출처: {parsed['source']}")
            block.append(f"   핵심 키워드: {keywords_str}")
            block.append(f"   요약: {summary}")
            block.append(f"   위키링크: {w_links_str}")
            
            if is_recent:
                body_preview = parsed["body"][:800]
                if len(parsed["body"]) > 800:
                    body_preview += "\n   ...(이하 생략)..."
                block.append(f"   본문 일부:\n   {body_preview}")
            else:
                block.append("   (오래된 자료: 세부 본문 생략됨)")
                
            file_blocks.append("\n".join(block))
            
        global_wiki_str = " ".join([f"[[{wl}]]" for wl in sorted(list(global_wikilinks))]) if global_wikilinks else "None"
        global_header = f"전역 RAG 위키링크 모음: {global_wiki_str}\n\n"
        
        files_content = "\n\n".join(file_blocks)
        prompt = header + global_header + files_content + footer
        
        if len(prompt) > max_chars:
            truncation_msg = "\n[메모리 일부 생략됨 — max_chars 제한]"
            allowed_len = max_chars - len(footer) - len(truncation_msg)
            if allowed_len > 0:
                prompt = prompt[:allowed_len] + truncation_msg + footer
            else:
                prompt = prompt[:max_chars]
                
        return prompt, excluded_files
        
    except Exception as e:
        return f"[References Memory 최적화 중 오류 발생: {e}]", excluded_files
