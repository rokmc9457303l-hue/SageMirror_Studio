import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path

target = Path(r"C:\SageMirror_Production\V17_Working_RightChat_007\app_v17_2_3.py")
lines = target.read_text(encoding="utf-8", errors="replace").splitlines()

patterns = [
    "def sync_global_model_to_parts",
    "sync_global_model_to_parts(",
    "global_model",
    "global_model_select",
    "selected_model",
    "Ollama |",
    "right_research_engine",
    "right_gemma_model_select",
    "right_research_engine_id",
    "gemma4:e2b",
    "gemma4:e4b",
]

report_path = Path(r"C:\SageMirror_Production\search_report.txt")
out = []

for pat in patterns:
    hits = [(i+1, l.rstrip()) for i, l in enumerate(lines) if pat in l]
    out.append(f"\n=== [{pat}] --- {len(hits)}\n")
    for lineno, content in hits:
        out.append(f"  L{lineno}: {content}\n")

report_path.write_text("".join(out), encoding="utf-8")
print("Done. See search_report.txt")
