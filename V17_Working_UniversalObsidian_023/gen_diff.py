import difflib
from pathlib import Path

old_p = Path(r"C:\SageMirror_Production\V17_Working_RightChat_009\app_v17_2_3.py")
new_p = Path(r"C:\SageMirror_Production\V17_Working_RightChat_012\app_v17_2_3.py")
diff_p = Path(r"C:\SageMirror_Production\rightchat_009_vs_012_mcp_scroll_fix.txt")

with open(old_p, "r", encoding="utf-8") as f:
    old_lines = f.readlines()
with open(new_p, "r", encoding="utf-8") as f:
    new_lines = f.readlines()

diff = list(difflib.unified_diff(old_lines, new_lines, fromfile="_009", tofile="_012", n=3))
diff_p.write_text("".join(diff), encoding="utf-8")
print(f"Diff lines: {len(diff)}")
print(f"Changed lines: {sum(1 for l in diff if l.startswith('+') or l.startswith('-'))}")
print(f"Saved to: {diff_p}")
