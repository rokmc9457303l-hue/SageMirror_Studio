import os
import subprocess
import shutil

print("========================================================")
print("과거 저장소(AI-) 자료 복원 및 통합 시스템")
print("========================================================\n")

target_dir = r"C:\SageMirror_Production\99_Old_AI_Backup"
# .git이 빠져있을 수 있으므로 안전하게 붙여줍니다. (이미 있으면 제외하는 로직이 필요하지만 clone시엔 보통 자동처리됨)
old_repo_url = "https://github.com/rokmc9457303l-hue/AI-.git"

print(f"1. 기존 깃허브({old_repo_url})에서 모든 과거 파일들을 다운로드합니다...")
if not os.path.exists(target_dir):
    try:
        # 깃허브에서 클론(다운로드) 수행
        result = subprocess.run(f"git clone {old_repo_url} {target_dir}", shell=True, capture_output=True, text=True)
        if result.returncode == 0 or "Cloning into" in result.stderr:
            print("-> 📥 다운로드 완료!")
            
            # .git 폴더 삭제 (새 저장소에 파일 자체로 포함시키기 위함, 안 지우면 충돌남)
            git_sub_dir = os.path.join(target_dir, ".git")
            if os.path.exists(git_sub_dir):
                def remove_readonly(func, path, _):
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(git_sub_dir, onerror=remove_readonly)
                print("-> 🔗 기존 연결선 제거 완료 (새 저장소에 완벽히 소속되도록 처리함)")
                
        else:
            print(f"❌ 클론 오류: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 예기치 못한 오류가 발생했습니다: {e}")
else:
    print("-> ⚠️ 이미 다운로드된 폴더(99_Old_AI_Backup)가 존재합니다. 그대로 두셔도 됩니다.")

print("\n========================================================")
print("작업이 완료되었습니다!")
print("이제 컴퓨터의 [99_Old_AI_Backup] 폴더에서 옛날 자료들을 열어볼 수 있습니다.")
print("========================================================")
input("종료하려면 엔터 키를 누르세요...")
