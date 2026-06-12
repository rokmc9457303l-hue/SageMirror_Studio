import os
import shutil
from pathlib import Path
import hashlib
import json

root_dir = Path(r"C:\SageMirror_Production")

# 1. Find all V17_Completed folders
completed_folders = []
for p in root_dir.iterdir():
    if p.is_dir() and p.name.startswith("V17_Completed"):
        completed_folders.append({
            "Name": p.name,
            "FullName": str(p),
            "LastWriteTime": p.stat().st_mtime
        })

# Sort descending by LastWriteTime
completed_folders.sort(key=lambda x: x["LastWriteTime"], reverse=True)

report = {}
report["found_completed_folders"] = [{"Name": f["Name"], "Time": f["LastWriteTime"]} for f in completed_folders]

latest_folder_path = Path(completed_folders[0]["FullName"]) if completed_folders else None
report["latest_folder"] = str(latest_folder_path) if latest_folder_path else None
report["latest_folder_time"] = completed_folders[0]["LastWriteTime"] if completed_folders else None

# Check if there is any backup newer than V17_Completed_RightResearchPanel_UICheckpoint_001_20260610
report["has_newer_than_target"] = False
if completed_folders and completed_folders[0]["Name"] != "V17_Completed_RightResearchPanel_UICheckpoint_001_20260610":
    report["has_newer_than_target"] = True

# 2. Check core files in latest backup
core_files = [
    "app_v17_2_3.py", "sage_popups_v17_2_3.py", "sage_config.py", "sage_engine.py",
    "research_router.py", "agent_toolkit.py", "agent_registry.py", "memory_state_manager.py",
    "rag_memory_utils.py", "rag_tag_system.py", "obsidian_search.py"
]
core_files_exist = {}
if latest_folder_path:
    for f in core_files:
        core_files_exist[f] = (latest_folder_path / f).exists()
report["core_files_exist"] = core_files_exist

# 3. Check specific contents in app_v17_2_3.py
app_content = ""
if latest_folder_path and (latest_folder_path / "app_v17_2_3.py").exists():
    app_content = (latest_folder_path / "app_v17_2_3.py").read_text(encoding="utf-8-sig", errors="ignore")

report["has_render_right_gemma_panel"] = "render_right_gemma_panel" in app_content
report["has_right_research_history"] = "right_research_history" in app_content
report["has_render_part0_assistant"] = "render_part0_assistant" in app_content
report["has_popup_assistant"] = "popup_assistant()" in app_content
report["has_running_version"] = "RUNNING VERSION" in app_content
report["has_master_pin"] = "마스터 PIN" in app_content
report["has_gemma_assistant"] = "젬마 어시스턴트" in app_content
report["has_text_input"] = "st.text_input" in app_content
report["has_text_area"] = "st.text_area" in app_content

# 4. Hash records
def get_sha256(filepath):
    if not filepath.exists(): return None
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as afile:
        buf = afile.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(65536)
    return hasher.hexdigest()

if latest_folder_path:
    report["hash_app"] = get_sha256(latest_folder_path / "app_v17_2_3.py")
    report["hash_popups"] = get_sha256(latest_folder_path / "sage_popups_v17_2_3.py")

# 5. Create new working copy
new_work_base = r"C:\SageMirror_Production\V17_Working_Part1Benchmark_{:03d}"
idx = 1
while True:
    new_work_dir = Path(new_work_base.format(idx))
    if not new_work_dir.exists():
        break
    idx += 1

report["new_work_dir"] = str(new_work_dir)

def ignore_forbidden(dir, contents):
    forbidden = {
        '.env', 'local_secrets.json', 'google_token.json', 
        'credentials.json', 'client_secret.json', '__pycache__'
    }
    ignore_list = [c for c in contents if c in forbidden or c.endswith('.env') or c.endswith('.token') or c.endswith('.key') or c.endswith('.pem') or c.endswith('.pyc')]
    return ignore_list

if latest_folder_path:
    shutil.copytree(latest_folder_path, new_work_dir, ignore=ignore_forbidden)
    
    # 6. Clear caches
    for r, dirs, files in os.walk(new_work_dir, topdown=False):
        for name in files:
            if name.endswith('.pyc') or name.endswith('.token') or name.endswith('.key') or name.endswith('.pem') or name.endswith('.env'):
                os.remove(os.path.join(r, name))
        for name in dirs:
            if name == '__pycache__':
                shutil.rmtree(os.path.join(r, name))

with open('checkout_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("Checkout script completed.")
