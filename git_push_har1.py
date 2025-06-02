import subprocess
import os
import time
from datetime import datetime
REPOSITORIES = [
    r"/opt/cribl/"
]
 
PUSH_INTERVAL_SECONDS = 120
 
def run_command(command, cwd):

    """Runs a shell command and returns its output, error, and return code."""
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,

            shell=False
        )
        return process.stdout.strip(), process.stderr.strip(), process.returncode
    except FileNotFoundError:
        return "", f"Error: Command '{command[0]}' not found. Is Git installed and in PATH?", -1

    except Exception as e:
        return "", f"An unexpected error occurred: {e}", -2
def get_current_branch(repo_path):
    """Gets the current git branch."""

    stdout, _, returncode = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if returncode == 0:
        return stdout
    print(f"Error getting current branch: {stdout}")
    return None
def get_upstream_branch(repo_path, local_branch_name):
    """
    Gets the full name of the upstream branch for the given local branch.
    Example: refs/remotes/origin/main
    """
    if not local_branch_name:
        return None
    stdout, _, returncode = run_command(
        ["git", "rev-parse", "--symbolic-full-name", f"{local_branch_name}@{{upstream}}"],
        cwd=repo_path
    )
    if returncode == 0 and stdout:
        return stdout
    return None
def push_repository_if_pending(repo_path):
    """
    Checks if the local branch has commits not yet pushed to its remote
    counterpart, and pushes them if so.
    """
    print(f"--- Processing repository: {repo_path} ---")
    if not os.path.isdir(repo_path):
        print(f"ERROR: Directory {repo_path} does not exist. Skipping.")
        return False
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        print(f"ERROR: {repo_path} is not a Git repository (missing .git folder). Skipping.")
        return False
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path) # Change context for git commands
        current_branch = get_current_branch(repo_path)
        if not current_branch:
            print("ERROR: Could not determine current branch. Skipping.")
            return False
        print(f"Current local branch: {current_branch}")
        print("Fetching from remote(s) to update remote tracking branches...")
        _, stderr_fetch, returncode_fetch = run_command(["git", "fetch", "--all"], cwd=repo_path)
        if returncode_fetch != 0:
            print(f"WARNING: 'git fetch --all' failed (exit code: {returncode_fetch}).")
            if stderr_fetch: print(f"Stderr:\n{stderr_fetch}")
            print("         Proceeding with local info, but it might be stale.")
        else:
            print("Fetch successful.")
        upstream_branch = get_upstream_branch(repo_path, current_branch)
        if not upstream_branch:
            print(f"WARNING: No upstream branch is set for local branch '{current_branch}'.")
            print(f"         Cannot determine if there are pending commits to push.")
            print(f"         Please set an upstream branch, e.g., with:")
            print(f"           git branch --set-upstream-to=origin/{current_branch} {current_branch}")
            print(f"         (Replace 'origin/{current_branch}' with the correct remote branch name if different)")
            return True
        print(f"Comparing local '{current_branch}' with upstream '{upstream_branch}'.")
        commits_ahead_stdout, stderr_count, returncode_count = run_command(
            ["git", "rev-list", "--count", f"{upstream_branch}..{current_branch}"],
            cwd=repo_path
        )
        if returncode_count != 0:
            print(f"ERROR: Could not count commits ahead of upstream (exit code: {returncode_count}).")
            if commits_ahead_stdout: print(f"Stdout: {commits_ahead_stdout}")
            if stderr_count: print(f"Stderr:\n{stderr_count}")
            print(f"         This might happen if '{upstream_branch}' is not a valid reference after fetching.")
            return False
        try:
            num_commits_ahead = int(commits_ahead_stdout)
        except ValueError:
            print(f"ERROR: Could not parse number of commits ahead. Output: '{commits_ahead_stdout}'")
            return False
        if num_commits_ahead > 0:
            print(f"Local branch '{current_branch}' is {num_commits_ahead} commit(s) ahead of '{upstream_branch}'.")
            print("Attempting to push...")
            stdout_push, stderr_push, returncode_push = run_command(["git", "push"], cwd=repo_path)
            if returncode_push == 0:
                print("Push successful.")
                if stdout_push: print(f"Stdout:\n{stdout_push}")
            else:
                print(f"WARNING: 'git push' encountered issues (exit code: {returncode_push}).")
                if stdout_push: print(f"Stdout:\n{stdout_push}")
                if stderr_push: print(f"Stderr:\n{stderr_push}")
                print("         Common issues: remote has diverged (pull needed), no permission, network issue.")
            return returncode_push == 0 # Returns True if push was successful, False otherwise
        else:
            print(f"Local branch '{current_branch}' is not ahead of '{upstream_branch}' (or is 0 commits ahead). No push needed.")
            return True
    finally:
        os.chdir(original_dir) # Always change back
def main_loop():
    print(f"Starting scheduled Git push operation for pending local commits.")
    print(f"Will check every {PUSH_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")
    print("==========================================")
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running push check cycle for all repositories...")
        all_repo_checks_ok = True
        for repo in REPOSITORIES:
            success = push_repository_if_pending(repo)
            if not success:
                all_repo_checks_ok = False
            print("-" * 40)
        if all_repo_checks_ok:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Push check cycle finished. Waiting for {PUSH_INTERVAL_SECONDS} seconds...")
        else:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Push check cycle finished with some issues. Waiting for {PUSH_INTERVAL_SECONDS} seconds...")
        try:
            time.sleep(PUSH_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting scheduler.")
            break
        print("==========================================")
if __name__ == "__main__":
    main_loop()

