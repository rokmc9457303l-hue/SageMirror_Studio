import os
import shutil

print("========================================================")
print("현자의 거울 (Tubie Studio) 옵시디언 금고 통합 자동화 스크립트")
print("========================================================\n")

NEW_DIR = r"C:\SageMirror_Production\00_Obsidian"
OLD_DIR1 = r"C:\SageMirror_Production\00_Production_Vault"
OLD_DIR2 = r"C:\Tubie_Master\00_Production_Vault"

print("[작업 1] 새로운 '00_Obsidian' 폴더를 준비합니다...")
os.makedirs(NEW_DIR, exist_ok=True)

print("[작업 2] 현재 폴더의 00_Production_Vault 자료를 이동합니다...")
if os.path.exists(OLD_DIR1):
    try:
        for item in os.listdir(OLD_DIR1):
            s = os.path.join(OLD_DIR1, item)
            d = os.path.join(NEW_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print("-> 이동 완료. 기존 폴더를 삭제합니다.")
        shutil.rmtree(OLD_DIR1)
    except Exception as e:
        print(f"오류 발생: {e}")
else:
    print("-> 기존 폴더(SageMirror)가 없습니다. 패스합니다.")

print("\n[작업 3] 구 버전(Tubie_Master)의 Production_Vault 자료를 백업/이동합니다...")
if os.path.exists(OLD_DIR2):
    try:
        for item in os.listdir(OLD_DIR2):
            s = os.path.join(OLD_DIR2, item)
            d = os.path.join(NEW_DIR, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        print("-> 구 버전 폴더 자료 통합 완료. (원본은 유지됩니다)")
    except Exception as e:
        print(f"오류 발생: {e}")
else:
    print("-> 구 버전 폴더(Tubie_Master)가 없습니다. 패스합니다.")

print("\n========================================================")
print("옵시디언 통합이 완료되었습니다!")
print(f"이제 {NEW_DIR} 폴더를 사용하세요.")
print("========================================================")
input("종료하려면 엔터 키를 누르세요...")
