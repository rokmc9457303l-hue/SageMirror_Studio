import subprocess
import sys

print("========================================================")
print("현자의 거울 - 새로운 깃허브 저장소로 연결 변경")
print("========================================================\n")

repo_url = input("깃허브에서 새로 만드신 [비어있는 새 저장소]의 URL을 붙여넣고 엔터를 치세요:\n> ").strip()

if repo_url:
    try:
        # 기존 주소(AI-)를 지우고 새 주소로 덮어쓰기
        subprocess.run("git remote set-url origin " + repo_url, shell=True, check=True)
        print("\n✅ 성공! 새로운 저장소로 주소가 완벽하게 변경되었습니다.")
        print("이제 기존처럼 '깃허브_자동백업.bat'를 실행하시면 안전하게 새 저장소로 백업됩니다!")
    except Exception as e:
        print(f"\n❌ 주소 변경 중 오류가 발생했습니다: {e}")
else:
    print("\n아무 주소도 입력되지 않았습니다.")

print("\n========================================================")
input("종료하려면 엔터 키를 누르세요...")
