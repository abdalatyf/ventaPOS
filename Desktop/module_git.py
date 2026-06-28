import subprocess
from config import BASE_DIR

def commit_and_tag(version):
    print("\n🌐 Documenting release in Git...")
    subprocess.run(["git", "add", "."], cwd=BASE_DIR)
    subprocess.run(["git", "commit", "-m", f"Release version {version}"], cwd=BASE_DIR)
    subprocess.run(["git", "tag", "-a", f"v{version}", "-m", f"Release version {version}"], cwd=BASE_DIR)
    print(f"✅ Successfully committed and tagged as v{version} in Git.")