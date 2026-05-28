from git import Repo
try:
    repo = Repo(r"C:\SageMirror_Production")
    repo.git.add("--all")
    repo.index.commit("v17.1.3: 젬마 어시스턴트 A시스템 안정화 2차 (속도계측 + 역할분리 + 동적임포트) — 20260529_0230")
    origin = repo.remote("origin")
    origin.push()
    print("[OK] Git commit and push completed successfully.")
except Exception as e:
    print(f"[FAIL] Git push failed: {e}")
