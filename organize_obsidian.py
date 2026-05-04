import os
import shutil

print("========================================================")
print("Sage Mirror Obsidian Vault Consolidation")
print("========================================================\n")

NEW_DIR = r"C:\SageMirror_Production\00_Obsidian"
OLD_DIR1 = r"C:\SageMirror_Production\00_Production_Vault"
OLD_DIR2 = r"C:\Tubie_Master\00_Production_Vault"

print("[Task 1] Preparing new '00_Obsidian' directory...")
os.makedirs(NEW_DIR, exist_ok=True)

print("[Task 2] Moving current '00_Production_Vault' data...")
if os.path.exists(OLD_DIR1):
    try:
        for item in os.listdir(OLD_DIR1):
            s = os.path.join(OLD_DIR1, item)
            d = os.path.join(NEW_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print("-> Move complete. Deleting old folder.")
        shutil.rmtree(OLD_DIR1)
    except Exception as e:
        print(f"Error occurred: {e}")
else:
    print("-> Old folder (SageMirror) not found. Skipping.")

print("\n[Task 3] Moving old version (Tubie_Master) 'Production_Vault' data...")
if os.path.exists(OLD_DIR2):
    try:
        for item in os.listdir(OLD_DIR2):
            s = os.path.join(OLD_DIR2, item)
            d = os.path.join(NEW_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print("-> Old version folder data merged.")
    except Exception as e:
        print(f"Error occurred: {e}")
else:
    print("-> Old version folder (Tubie_Master) not found. Skipping.")

print("\n========================================================")
print("Obsidian Vault Consolidation Complete!")
print(f"Please use the {NEW_DIR} directory from now on.")
print("========================================================")
