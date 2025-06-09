import subprocess
import os
import time
from datetime import datetime

# --- Configuration ---
REPOSITORIES = [
    r"/opt/cribl/"
    ]

# Interval in seconds (e.g., 3600 for 1 hour, 600 for 10 minutes)
PULL_INTERVAL_SECONDS = 60
# --- End Configuration ---

def run_command(command, cwd):
    """Runs a shell command and returns its output and error code."""
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False # Don't raise exception for non-zero exit codes
        )
        return process.stdout, process.stderr, process.returncode
    except FileNotFoundError:
        return "", f"Error: Command '{command[0]}' not found. Is Git installed and in PATH?", -1
    except Exception as e:
        return "", f"An unexpected error occurred: {e}", -2


def pull_repository(repo_path):
    """Performs git pull in the specified repository."""
    print(f"--- Processing repository: {repo_path} ---")

    if not os.path.isdir(repo_path):
        print(f"ERROR: Directory {repo_path} does not exist. Skipping.")
        return False

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(f"ERROR: {repo_path} is not a Git repository (missing .git folder). Skipping.")
        return False

    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)
        current_branch_stdout, _, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
        print(f"Current branch: {current_branch_stdout.strip()}")
        print("Fetching and resetting to latest Cribl code...")

        run_command(["git", "fetch"], cwd=repo_path)
        stdout, stderr, returncode = run_command(["git", "reset", "--hard", "origin/main"], cwd=repo_path)

        if returncode == 0:
            print("Pull successful.")
            if stdout.strip() and stdout.strip() != "Already up to date.":
                print(f"Output:\n{stdout.strip()}")
        else:
            print(f"WARNING: 'git pull' encountered issues (exit code: {returncode}).")
            if stdout: print(f"Stdout:\n{stdout.strip()}")
            if stderr: print(f"Stderr:\n{stderr.strip()}")
            print("         You may need to resolve conflicts or other issues manually.")
        return returncode == 0
    finally:
        os.chdir(original_dir) # Go back to the original directory

def main_pull_loop():
    print(f"Starting scheduled Git pull operation. Interval: {PULL_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")
    print("==========================================")

    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running pull for all repositories...")
        for repo in REPOSITORIES:
            pull_repository(repo)
            print("-" * 40)

        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pull cycle finished. Waiting for {PULL_INTERVAL_SECONDS} seconds...")
        try:
            time.sleep(PULL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting pull scheduler.")
            break
        print("==========================================")

if __name__ == "__main__":
    main_pull_loop()
