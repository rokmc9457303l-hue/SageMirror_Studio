import os
import subprocess
from datetime import datetime

print("========================================================")
print("현자의 거울 (Tubie Studio) 깃허브 자동 백업 시스템")
print("========================================================\n")

# 작업 폴더 고정
REPO_DIR = r"C:\SageMirror_Production"
os.chdir(REPO_DIR)

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

# 1. 깃 초기화 확인
if not os.path.exists(".git"):
    print("[안내] 이 폴더는 아직 깃허브와 연결되지 않았습니다. 초기화를 진행합니다.")
    run_cmd("git init")
    run_cmd("git branch -M main")
    
    repo_url = input("깃허브에서 새로 만든 빈 저장소(Repository)의 URL을 붙여넣기 해주세요:\n(예: https://github.com/계정명/저장소명.git) > ").strip()
    
    if repo_url:
        success, msg = run_cmd(f"git remote add origin {repo_url}")
        if not success:
            print(f"오류: 리모트 저장소 추가 실패\n{msg}")
            exit(1)
    else:
        print("URL이 입력되지 않아 종료합니다.")
        exit(1)

print("[작업 중] 변경된 모든 파일을 수집하고 있습니다 (git add .)")
run_cmd("git add .")

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
commit_msg = f"자동 백업: {current_time}"

print(f"[작업 중] 백업 기록을 남깁니다 (git commit -m '{commit_msg}')")
success, msg = run_cmd(f'git commit -m "{commit_msg}"')

# 변경사항이 없을 때 에러가 발생하므로 체크
if "nothing to commit" in msg or not success:
    print("-> 💡 변경된(새로운) 파일이 없습니다. 백업할 내용이 최신 상태입니다.")
else:
    print("[작업 중] 깃허브로 안전하게 전송합니다 (git push)...")
    success, push_msg = run_cmd("git push -u origin main")
    if not success and ("rejected" in push_msg or "non-fast-forward" in push_msg or "fetch first" in push_msg):
        print("-> 기존 저장소의 자료가 발견되었습니다. 병합(Merge)을 시도합니다...")
        run_cmd("git pull origin main --allow-unrelated-histories --no-rebase -m '자동 병합'")
        success, push_msg = run_cmd("git push -u origin main")

    if success:
        print("-> ✅ 성공적으로 깃허브 서버에 전송(백업)되었습니다!")
    else:
        print(f"-> ❌ 전송 중 오류가 발생했습니다. (계정 인증 창이 떴다면 로그인해주세요)\n{push_msg}")

print("\n========================================================")
print("자동 백업 루틴이 완료되었습니다.")
print("========================================================")
input("종료하려면 엔터 키를 누르세요...")
