from pathlib import Path
import difflib

old_path = Path(r"C:\SageMirror_Production\V17_Working_RightChat_005\app_v17_2_3.py")
new_path = Path(r"C:\SageMirror_Production\V17_Working_RightChat_007\app_v17_2_3.py")
report_path = Path(r"C:\SageMirror_Production\rightchat_005_vs_007_diff.txt")

old_lines = old_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
new_lines = new_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

diff = list(difflib.unified_diff(
    old_lines, new_lines,
    fromfile=str(old_path),
    tofile=str(new_path),
    n=2
))

report_path.write_text("".join(diff), encoding="utf-8")

added   = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
print(f"총 diff 줄: {len(diff)}")
print(f"추가: {len(added)}, 삭제: {len(removed)}")
print(f"저장: {report_path}")
