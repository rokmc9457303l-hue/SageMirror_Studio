import sys
sys.stdout.reconfigure(encoding="utf-8")
filepath = r"C:\SageMirror_Production\sage_popups.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()
start_idx = end_idx = ra_idx = None
for i, line in enumerate(lines):
    if "통합 시스템 컨텍스트 구성" in line and start_idx is None:
        start_idx = i
    if start_idx and "obsidian_rules" in line and "규칙서" in line and end_idx is None:
        end_idx = i
    if start_idx and "Recent Activity Memory" in line and "주입" in line and ra_idx is None:
        ra_idx = i
print(f"start={start_idx+1} end={end_idx+1} recent={ra_idx+1 if ra_idx else None}")
for i in range(start_idx, min(start_idx+30, len(lines))):
    print(f"{i+1}: {repr(lines[i][:80])}")
