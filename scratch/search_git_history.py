import subprocess
import os

try:
    result = subprocess.run(["git", "log", "--oneline"], capture_output=True, encoding="utf-8", errors="ignore", check=True)
    commits = [line.split()[0] for line in result.stdout.strip().split("\n")]
    print(f"Total commits: {len(commits)}")
    
    keywords = ["chat_history", "chat_sessions"]
    for commit in commits:
        res = subprocess.run(["git", "show", commit], capture_output=True, encoding="utf-8", errors="ignore")
        for kw in keywords:
            if kw in res.stdout:
                title_res = subprocess.run(["git", "log", "-n", "1", "--format=%s", commit], capture_output=True, encoding="utf-8", errors="ignore")
                print(f"Match found in commit {commit} ({title_res.stdout.strip()}): contains keyword '{kw}'")
                
except Exception as e:
    print("Error:", e)
