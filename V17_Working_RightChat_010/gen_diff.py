import difflib
from pathlib import Path

old_p = Path(r"C:\SageMirror_Production\V17_Working_RightChat_009\app_v17_2_3.py")
new_p = Path(r"C:\SageMirror_Production\V17_Working_RightChat_010\app_v17_2_3.py")
diff_p = Path(r"C:\SageMirror_Production\rightchat_009_vs_010_diff.txt")

with open(old_p, "r", encoding="utf-8") as f:
    old_lines = f.readlines()
with open(new_p, "r", encoding="utf-8") as f:
    new_lines = f.readlines()

diff = difflib.unified_diff(old_lines, new_lines, fromfile=str(old_p), tofile=str(new_p), n=3)
diff_p.write_text("".join(diff), encoding="utf-8")
print(f"Diff saved to {diff_p}")
