import os
import time
import json
import requests
import subprocess
from datetime import datetime
 
# --- Cribl.Cloud Configuration ---
# !!! IMPORTANT: Replace these placeholders with your actual values !!!
CRIBL_BASE_URL = "https://main-laughing-ardinghelli-3fusyyj.cribl.cloud"  # e.g., "https://myorg.cribl.cloud"
API_TOKEN = "Bearer UYXlS3KmOH3PXhG14k7QRDjifMEWAX_d8aZ5Cw8zutD0o5g21s9Z5ZSYtHNt7Mfy"          # e.g., "Bearer CFE...YOUR_TOKEN...XYZ"
# Optional: Specify a default worker group if pipelines are not global
# CRIBL_WORKER_GROUP = "default" # or your specific worker group name
 
# --- Git Configuration ---
# List of local paths to your Git repositories (root of the clone)
REPOSITORIES = [
    r"/opt/cribl/"
]
# Subdirectory within each repository where .json pipeline config files are located.
# Based on typical Cribl Pack structure and your screenshot, this might be "data/default/pipelines".
# Adjust if your pipeline JSONs are elsewhere (e.g., directly in the root, or another path).
CONFIG_SUBDIR = "/opt/cribl/default/"
 
# Interval in seconds for checking Git and potentially pushing to Cribl
PULL_INTERVAL_SECONDS = 60  # 1 minute
 
# --- Cribl API Push Function ---
def push_config_to_cribl(file_path, pipeline_name_override=None):
    """Pushes a single pipeline configuration file to Cribl.Cloud."""
    if pipeline_name_override:
        pipeline_name = pipeline_name_override
    else:
        # Derives pipeline name from the filename (e.g., "my_pipeline.json" -> "my_pipeline")
        pipeline_name = os.path.splitext(os.path.basename(file_path))[0]
 
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Config file not found {file_path}")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from {file_path}")
        return
 
    # Construct the URL. Adjust if using worker groups.
    # If using worker groups, the URL might be:
    # url = f"{CRIBL_BASE_URL}/api/v1/m/{CRIBL_WORKER_GROUP}/p/pipelines/{pipeline_name}"
    # For global/default scope pipelines:
    url = f"{CRIBL_BASE_URL}/api/v1/pipelines/{pipeline_name}"
 
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }
 
    print(f"Attempting to push pipeline '{pipeline_name}' from {file_path} to {url}")
    try:
        # Using PUT to create or update.
        response = requests.put(url, headers=headers, json=config_data, timeout=30) # 30-second timeout
        if response.status_code in [200, 201]:  # 200 OK (updated), 201 Created (new)
            print(f"✅ Successfully pushed '{pipeline_name}'. Status: {response.status_code}")
        else:
            print(f"❌ Failed to push '{pipeline_name}'. Status: {response.status_code}, URL: {url}, Msg: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for '{pipeline_name}': {e}")
 
# --- Git Helper Function ---
def run_command(command, cwd):
    """Runs a shell command and returns its output, error, and return code."""
    try:
        # Using shell=True can be a security risk if command components are from untrusted input.
        # Here, command is constructed internally, so it's generally safer.
        # On Windows, shell=True can sometimes help with finding `git` if not perfectly in PATH for subprocess.
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False, # Do not raise exception for non-zero exit codes
            shell=True # Consider if this is needed in your environment
        )
        return process.stdout, process.stderr, process.returncode
    except FileNotFoundError:
        return "", f"Error: Command '{command[0]}' not found. Is Git installed and in your system's PATH?", -1
    except Exception as e:
        return "", f"An unexpected error occurred while running command: {e}", -2
 
# --- Git Pull and Trigger Function ---
def pull_repository_and_trigger_push(repo_path, config_relative_path):
    """
    Performs git operations in the specified repository.
    If changes are pulled, it scans for .json files in the config_relative_path
    and pushes them to Cribl.Cloud.
    """
    print(f"\n--- Processing repository: {repo_path} ---")
 
    if not os.path.isdir(repo_path):
        print(f"ERROR: Repository directory {repo_path} does not exist. Skipping.")
        return
 
    dot_git_path = os.path.join(repo_path, ".git")
    if not os.path.isdir(dot_git_path):
        print(f"ERROR: {repo_path} is not a Git repository (missing .git folder). Skipping.")
        return
 
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] Checking for remote changes in {repo_path}...")
 
 
    # 2. Get current local commit (HEAD)
    local_commit_stdout, _, _ = run_command(["git", "rev-parse", "HEAD"], cwd=repo_path)
    local_commit = local_commit_stdout.strip()
 
    # 3. Get remote commit for main/master branch (try common names)
    remote_branch_name_to_check = ""
    remote_commit = ""
    # Determine the default remote branch (e.g. origin/main or origin/master)
    # This could be made more robust by parsing `git remote show origin`
    for branch_ref in ["origin/main", "origin/master"]: # Common default branch names
        rev_parse_stdout, _, rev_parse_retcode = run_command(["git", "rev-parse", branch_ref], cwd=repo_path)
        if rev_parse_retcode == 0 and rev_parse_stdout.strip():
            remote_branch_name_to_check = branch_ref
            remote_commit = rev_parse_stdout.strip()
            break
   
    if not remote_branch_name_to_check:
        print(f"ERROR: Could not determine remote commit hash for origin/main or origin/master in {repo_path}. Skipping pull.")
        # You might need to explicitly configure the branch name if it's different
        return
 
    print(f"Local HEAD: {local_commit}, Remote {remote_branch_name_to_check}: {remote_commit}")
 
    if local_commit == remote_commit:
        print(f"Repository {repo_path} is already up to date with {remote_branch_name_to_check}. No pull needed.")
        return # No changes, so no push to Cribl needed
 
    print(f"Changes detected in {repo_path} ({remote_branch_name_to_check} is different or ahead).")
    print(f"Running: git reset --hard {remote_branch_name_to_check}")
   
    # 4. Reset local to remote branch state (overwrite local changes)
    reset_stdout, reset_stderr, reset_returncode = run_command(["git", "reset", "--hard", remote_branch_name_to_check], cwd=repo_path)
 
    if reset_returncode == 0:
        print(f"Git reset to {remote_branch_name_to_check} successful for {repo_path}.")
        if "Already up to date." not in reset_stdout: # Check if reset actually changed anything
             print(f"Output:\n{reset_stdout.strip()}")
        # --- Trigger Cribl Push for updated files ---
        actual_config_dir_to_scan = os.path.join(repo_path, config_relative_path)
       
        if not os.path.isdir(actual_config_dir_to_scan):
            print(f"WARNING: Config directory '{actual_config_dir_to_scan}' not found. No configs to push from this path.")
            return
 
        print(f"Scanning '{actual_config_dir_to_scan}' for .json files to push to Cribl...")
        pushed_any_config_successfully = False
        for filename in os.listdir(actual_config_dir_to_scan):
            if filename.endswith('.json'):
                file_path_to_push = os.path.join(actual_config_dir_to_scan, filename)
                push_config_to_cribl(file_path_to_push) # Filename implies pipeline name
                pushed_any_config_successfully = True # Mark that we attempted a push
 
        if not pushed_any_config_successfully:
            print(f"No .json files found in '{actual_config_dir_to_scan}' to push, or directory was empty.")
    else:
        print(f"ERROR: 'git reset --hard {remote_branch_name_to_check}' failed for {repo_path} (Code: {reset_returncode}).")
        if reset_stdout: print(f"Stdout:\n{reset_stdout.strip()}")
        if reset_stderr: print(f"Stderr:\n{reset_stderr.strip()}")
        print("         Manual intervention may be needed in the repository. Configs will not be pushed.")
 
# --- Main Loop ---
def main_loop():
    # Validate Cribl Configuration early
    if "<your-org>" in CRIBL_BASE_URL or "<your-api-token>" in API_TOKEN:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR: CRIBL_BASE_URL or API_TOKEN still has placeholder values. !!!")
        print("!!! Please replace <your-org> and <your-api-token> in the script.    !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return
    if not API_TOKEN.startswith("Bearer "):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! WARNING: API_TOKEN does not start with 'Bearer '. This might be incorrect. !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
 
 
    print(f"Starting Git pull and Cribl push scheduler.")
    print(f"Checking repositories: {REPOSITORIES}")
    print(f"Pushing .json configs found in subdirectory: '{CONFIG_SUBDIR}' within each repo.")
    print(f"Check interval: {PULL_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")
    print("==========================================")
 
    try:
        while True:
            current_cycle_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{current_cycle_time}] Running scheduled tasks for all repositories...")
            for repo_root_path in REPOSITORIES:
                pull_repository_and_trigger_push(repo_root_path, CONFIG_SUBDIR)
                print("-" * 40) # Separator between repositories
 
            current_cycle_done_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{current_cycle_done_time}] Task cycle finished for all repositories.")
            print(f"Waiting for {PULL_INTERVAL_SECONDS} seconds until the next cycle...")
            time.sleep(PULL_INTERVAL_SECONDS)
            print("==========================================")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting scheduler.")
    except Exception as e:
        print(f"\nAn unexpected error occurred in the main loop: {e}")
    finally:
        print("Scheduler stopped.")
 
if __name__ == "__main__":
    main_loop()
 
