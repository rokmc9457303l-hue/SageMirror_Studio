import os

VAULT_DIR = r"C:\SageMirror_Production\00_Obsidian"
MASTER_MAP_FILE = "00_현자의_지도(Master_Map).md"
MASTER_MAP_PATH = os.path.join(VAULT_DIR, MASTER_MAP_FILE)
BACK_LINK = f"\n\n---\n🔙 [[{MASTER_MAP_FILE.replace('.md', '')}]]\n"

print("========================================================")
print("Sage Mirror Obsidian Network Builder")
print("========================================================\n")

print("1. Scanning all markdown files and building index...")

categories = {}

for root, dirs, files in os.walk(VAULT_DIR):
    # Ignore internal obsidian folders
    if ".obsidian" in root or "Templates" in root:
        continue
        
    folder_name = os.path.basename(root)
    if folder_name == "00_Obsidian":
        folder_name = "Root (최상위)"
        
    for file in files:
        if file.endswith(".md") and file != MASTER_MAP_FILE and file != "00_지식_구조화_마스터_템플릿.md":
            if folder_name not in categories:
                categories[folder_name] = []
            
            file_path = os.path.join(root, file)
            file_name_no_ext = file.replace(".md", "")
            categories[folder_name].append(file_name_no_ext)
            
            # Inject backlink if not present
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "🔙 [[" not in content:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(BACK_LINK)

print("2. Generating Master Map...")

map_content = f"# 🗺️ 현자의 지도 (Master Map)\n\n"
map_content += f"**Sage Mirror Studio**의 모든 지식이 이곳으로 모이고 연결됩니다.\n"
map_content += f"이 지도를 통해 언제든 자료를 찾고, 탐색하세요.\n\n---\n"

for category, items in categories.items():
    map_content += f"## 📂 {category}\n"
    for item in items:
        map_content += f"- [[{item}]]\n"
    map_content += "\n"

with open(MASTER_MAP_PATH, "w", encoding="utf-8") as f:
    f.write(map_content)

print("-> Master Map created successfully.")
print("\n========================================================")
print("Network build complete! Open Obsidian and check '00_현자의_지도(Master_Map)'.")
print("========================================================")
