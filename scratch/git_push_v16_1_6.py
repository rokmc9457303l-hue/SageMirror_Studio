import sys
from git import Repo

def run_push():
    try:
        repo = Repo(r"C:\SageMirror_Production")
        print("Adding all files to staging...")
        repo.git.add("--all")
        
        commit_msg = "v16.1.6: Agent Toolkit Separation - 20260526_0838"
        print(f"Committing with message: {commit_msg}")
        repo.index.commit(commit_msg)
        
        print("Pushing to origin remote...")
        origin = repo.remote("origin")
        origin.push()
        print("Git Push Completed Successfully!")
    except Exception as e:
        print(f"Error during git push: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_push()
