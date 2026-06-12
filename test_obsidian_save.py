import os
import sys
from pathlib import Path
import json

vault_dir = Path(r"C:\SageMirror_Production\00_Obsidian")
raw_dir = vault_dir / "00_Raw"
wiki_dir = vault_dir / "01_Wiki"
schema_dir = vault_dir / "02_Schema"

def count_files(d):
    if not d.exists(): return 0
    return len(list(d.glob("*.*")))

before_counts = {
    "raw": count_files(raw_dir),
    "wiki": count_files(wiki_dir),
    "schema": count_files(schema_dir)
}

# Add vault path to session_state mock
import streamlit as st
if "path_obsidian" not in st.session_state:
    st.session_state["path_obsidian"] = str(vault_dir)

sys.path.insert(0, r"C:\SageMirror_Production\V17_Working_Part1Benchmark_002")
from sage_popups_v17_2_3 import _save_raw_wiki

test_content = "우측 리서치 저장 기능 시험 — 2026-06-12\n\n이것은 기능 작동 여부를 확인하기 위한 테스트 텍스트입니다."
test_title = "테스트_리서치_결과"
source_type = "Right_Gemma_Test"
part_key = "part1"
model_name = "test-model"

result_msg = _save_raw_wiki(test_content, test_title, source_type, part_key, model_name)

after_counts = {
    "raw": count_files(raw_dir),
    "wiki": count_files(wiki_dir),
    "schema": count_files(schema_dir)
}

# Find newest files
def get_newest(d):
    if not d.exists(): return None
    files = list(d.glob("*.*"))
    if not files: return None
    newest = max(files, key=lambda f: f.stat().st_mtime)
    return {
        "path": str(newest),
        "size": newest.stat().st_size,
        "mtime": newest.stat().st_mtime
    }

report = {
    "before": before_counts,
    "after": after_counts,
    "result_msg": result_msg,
    "newest_raw": get_newest(raw_dir),
    "newest_wiki": get_newest(wiki_dir),
    "newest_schema": get_newest(schema_dir)
}

with open("obsidian_test_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("Obsidian save test completed")
