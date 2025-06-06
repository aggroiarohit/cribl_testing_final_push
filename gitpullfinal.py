import os
import time
import subprocess
import requests
import git
from datetime import datetime

# --- Configuration ---
CRIBL_CONFIG_PATH = "/opt/cribl/local/"
GITHUB_REPO_URL = 'git@github.com:aggroiarohit/cribl_on_prem_new.git'
CRIBL_CLOUD_TOKEN = "rohitrohitrohit"
CRIBL_API_URL = "https://main-laughing-ardinghelli-3fusyyj.cribl.cloud/api/deploy"
GIT_COMMIT_MESSAGE = f"Automated commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
# ----------------------

def has_changes():
    repo = git.Repo(CRIBL_CONFIG_PATH)
    return repo.is_dirty(untracked_files=True)

def commit_to_github():
    os.chdir(CRIBL_CONFIG_PATH)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", GIT_COMMIT_MESSAGE], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✅ Changes committed and pushed to GitHub.")

def deploy_to_cloud():
    headers = {
        "Authorization": f"Bearer {CRIBL_CLOUD_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "path": "/path/to/github",  # Replace with correct Git path if required
        "source": "github",
        "repo": "aggroiarohit/cribl_on_prem_new"  # Make sure this matches Cribl's expected format
    }

    response = requests.post(CRIBL_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        print("🚀 Successfully deployed to Cribl.Cloud.")
    else:
        print(f"❌ Deployment failed: {response.status_code} > {response.text}")

def main():
    os.chdir(CRIBL_CONFIG_PATH)

    if has_changes():
        print("🔄 Changes detected in Cribl config.")
        try:
            commit_to_github()
            deploy_to_cloud()
        except subprocess.CalledProcessError as e:
            print(f"❌ Git error: {e}")
        except Exception as e:
            print(f"❌ Deployment error: {e}")
    else:
        print("✅ No changes detected in Cribl config.")

if __name__ == "__main__":
    main()

