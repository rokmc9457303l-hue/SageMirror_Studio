from git import Repo
import os

try:
    repo_path = r"C:\SageMirror_Production"
    repo = Repo(repo_path)
    repo.git.add("--all")
    commit_msg = "v13.2: Veo3 & Gemma Protocol v2.0 Integration — 20260515_1802"
    repo.index.commit(commit_msg)
    origin = repo.remote("origin")
    origin.push()
    print("✅ GitHub Push Success")
except Exception as e:
    print(f"❌ GitHub Push Failed: {e}")
