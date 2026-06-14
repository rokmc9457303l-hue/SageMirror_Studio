from pathlib import Path
import difflib

old_path = Path(r"C:\SageMirror_Production\V17_Working_RightChat_005\app_v17_2_3.py")
new_path = Path(r"C:\SageMirror_Production\V17_Working_RightChat_006\app_v17_2_3.py")
report_path = Path(r"C:\SageMirror_Production\rightchat_005_vs_006_diff_utf8.txt")

old_lines = old_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
new_lines = new_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

print(f"_005 줄수: {len(old_lines)}")
print(f"_006 줄수: {len(new_lines)}")
print(f"_005 바이트: {old_path.stat().st_size}")
print(f"_006 바이트: {new_path.stat().st_size}")

diff = list(difflib.unified_diff(
    old_lines,
    new_lines,
    fromfile=str(old_path),
    tofile=str(new_path),
    n=3,
))

report_path.write_text("".join(diff), encoding="utf-8")
print(f"총 diff 줄수: {len(diff)}")
print(f"저장 완료: {report_path}")

# 변경 라인만 추출
added = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
print(f"추가 라인: {len(added)}")
print(f"삭제 라인: {len(removed)}")
