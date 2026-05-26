import sys
import os
from git import Repo

def main():
    try:
        repo = Repo(r"C:\SageMirror_Production")
        repo.git.add("--all")
        # EM DASH가 아닌 일반 하이픈(-)을 사용하여 인코딩 오류 방지
        commit_message = "v16.1.9: Part2 Persistent Memory Recovery Patch - 20260526_1453"
        repo.index.commit(commit_message)
        print("Commit successfully created.")
        
        origin = repo.remote("origin")
        push_info = origin.push()
        for info in push_info:
            print(f"Push info: {info.summary} - {info.flags}")
        print("Git Push completed successfully.")
    except Exception as e:
        print(f"Error during Git execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
