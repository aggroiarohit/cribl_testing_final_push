import os
import time
import json
import requests
import subprocess
from datetime import datetime

# --- CONFIGURATION ---

# Git repo path (local clone of your GitHub repo)
REPO_PATH = "/opt/cribl"

# Path to pipeline JSONs inside the repo (relative to repo root)
PIPELINE_CONFIG_DIR = "default"

# Cribl.Cloud config
CRIBL_BASE_URL = "https://main-laughing-ardinghelli-3fusyyj.cribl.cloud"
CRIBL_API_TOKEN = os.getenv("CRIBL_API_TOKEN")  # Set via env variable for safety

# Git commit message
COMMIT_MESSAGE = "Auto-sync pipeline updates"

# Time between checks (seconds)
SYNC_INTERVAL = 60

# --- HELPER FUNCTIONS ---

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_cmd(cmd, cwd):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=False)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def git_commit_and_push(repo_path):
    log("📝 Checking for local changes to commit...")
    run_cmd(["git", "add", "."], cwd=repo_path)
    out, err, code = run_cmd(["git", "diff", "--cached", "--quiet"], cwd=repo_path)

    if code == 0:
        log("✅ No local changes to commit.")
        return

    log("🔄 Committing changes...")
    run_cmd(["git", "commit", "-m", COMMIT_MESSAGE], cwd=repo_path)
    log("📤 Pushing changes to GitHub...")
    out, err, code = run_cmd(["git", "push"], cwd=repo_path)

    if code != 0:
        log(f"❌ Git push failed: {err}")
    else:
        log("✅ Git push successful.")

def git_pull(repo_path):
    log("📥 Pulling latest changes from GitHub...")
    out, err, code = run_cmd(["git", "pull"], cwd=repo_path)
    if code != 0:
        log(f"❌ Git pull failed: {err}")
    else:
        log("✅ Git pull successful.")

def push_pipeline_to_cribl(file_path):
    pipeline_name = os.path.splitext(os.path.basename(file_path))[0]
    url = f"{CRIBL_BASE_URL}/api/v1/pipelines/{pipeline_name}"
    headers = {
        "Authorization": CRIBL_API_TOKEN,
        "Content-Type": "application/json"
    }

    try:
        with open(file_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        log(f"❌ Failed to load JSON from {file_path}: {e}")
        return

    log(f"🚀 Pushing pipeline '{pipeline_name}' to Cribl.Cloud...")
    try:
        response = requests.put(url, headers=headers, json=config)
        if response.status_code in [200, 201]:
            log(f"✅ Pipeline '{pipeline_name}' pushed successfully.")
        else:
            log(f"❌ Cribl push failed ({response.status_code}): {response.text}")
    except requests.RequestException as e:
        log(f"❌ Cribl request error: {e}")

def sync():
    if not os.path.isdir(REPO_PATH):
        log(f"❌ Repo path not found: {REPO_PATH}")
        return

    git_commit_and_push(REPO_PATH)
    git_pull(REPO_PATH)

    config_dir = os.path.join(REPO_PATH, PIPELINE_CONFIG_DIR)
    if not os.path.isdir(config_dir):
        log(f"⚠️ Config directory not found: {config_dir}")
        return

    for filename in os.listdir(config_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(config_dir, filename)
            push_pipeline_to_cribl(file_path)

def main():
    if not CRIBL_API_TOKEN:
        log("❌ CRIBL_API_TOKEN environment variable is not set.")
        return

    log("🔁 Starting GitHub → Cribl.Cloud sync process.")
    while True:
        try:
            sync()
            log(f"⏱️ Waiting {SYNC_INTERVAL} seconds before next sync...\n")
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            log("🛑 Interrupted by user. Exiting.")
            break
        except Exception as e:
            log(f"❌ Unexpected error: {e}")
            time.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    main()

