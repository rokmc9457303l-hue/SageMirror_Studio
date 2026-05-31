import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("sage_popups_v17_1_19.py", "r", encoding="utf-8") as f:
    code = f.read()

# 새 함수 정의 (Raw/Wiki 이중 저장)
new_func = '''
def _save_raw_wiki(content, title, source_type, part_key, model_name):
    """Raw/Wiki 이중 저장 — 00_Raw(원본) + 01_Wiki(개념추출)"""
    try:
        vault = st.session_state.get("path_obsidian", "")
        if not vault:
            return "[경로 미설정]"
        from pathlib import Path as _P
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe = "".join(c for c in title if c.isalnum() or c in " _-")[:40].strip()
        if not safe:
            safe = "untitled"

        # Raw 저장 (원본 그대로)
        raw_dir = _P(vault) / "00_Raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"{safe}_{ts}.md"
        raw_md = f"# [RAW] {title}\\n\\n## 메타\\n- 소스: {source_type}\\n- 모델: {model_name}\\n- 저장: {today}\\n\\n## 원본 내용\\n\\n{content}\\n\\n---\\n*[RAW DATA - 원본 보존]*\\n"
        raw_path.write_text(raw_md, encoding="utf-8")

        # Wiki 저장 (개념 추출)
        wiki_dir = _P(vault) / "01_Wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        wiki_path = wiki_dir / f"{safe}_{ts}.md"
        try:
            cp = f"아래 내용에서 한줄 요약과 핵심 개념 5개를 추출하라.\\n형식:\\n요약: (한줄)\\n개념: 개념1, 개념2, 개념3, 개념4, 개념5\\n\\n[내용]\\n{content[:800]}"
            concept = call_gemma(cp, model=model_name)
        except Exception:
            concept = "요약: 자동 추출 실패\\n개념: 미분류"
        try:
            tags = _classify_universal_tags(content + " " + title)
            tag_links = " ".join([f"[[{t}]]" for cat in tags.values() for t in cat])
        except Exception:
            tag_links = ""
        wiki_md = f"# [[{title}]]\\n\\n## 핵심 개념 (Wiki Node)\\n{concept}\\n\\n## 연결 개념\\n{tag_links}\\n\\n## 메타\\n- 소스: {source_type}\\n- 모델: {model_name}\\n- 저장: {today}\\n- Raw 원본: [[00_Raw/{safe}_{ts}]]\\n\\n---\\n*[WIKI NODE - 개념 신경망]*\\n"
        wiki_path.write_text(wiki_md, encoding="utf-8")

        return f"Raw+Wiki 저장 완료: {safe}_{ts}.md"
    except Exception as e:
        return f"[Raw/Wiki 저장 오류] {e}"


'''

# _save_to_obsidian_with_tags 함수 정의 앞에 새 함수 삽입
marker = "def _save_to_obsidian_with_tags("
if marker in code and "_save_raw_wiki" not in code:
    code = code.replace(marker, new_func + marker, 1)
    with open("sage_popups_v17_1_19.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: _save_raw_wiki 함수 추가 완료")
elif "_save_raw_wiki" in code:
    print("SKIP: 이미 함수 있음")
else:
    print("ERROR: 마커 못찾음 — def _save_to_obsidian_with_tags( 없음")
