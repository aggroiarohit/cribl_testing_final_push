import os
import time
import subprocess
import requests
import git
from datetime import datetime

# --- Configuration ---
CRIBL_CONFIG_PATH = "/opt/cribl/local/"
GITHUB_REPO_URL = 'git@github.com:aggroiarohit/cribl_on_prem_new.git'
CRIBL_CLOUD_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1BLUJhY294M3RGbk5XekVLYmxxMyJ9.eyJodHRwczovL2NyaWJsLmNsb3VkL3JvbGUiOlsib3JnX2FkbWluIl0sImh0dHBzOi8vY3JpYmwuY2xvdWQvb3JnYW5pemF0aW9uSWQiOiJsYXVnaGluZy1hcmRpbmdoZWxsaS0zZnVzeXlqIiwiaHR0cHM6Ly9jcmlibC5jbG91ZC9vcmdhbml6YXRpb24iOnsibmFtZSI6ImxhdWdoaW5nLWFyZGluZ2hlbGxpLTNmdXN5eWoifSwiaHR0cHM6Ly9jcmlibC5jbG91ZC9lbWFpbCI6ImFnZ3JvaWFyb2hpdEBnbWFpbC5jb20iLCJodHRwczovL2NyaWJsLmNsb3VkL25hbWUiOiJhZ2dyb2lhcm9oaXRAZ21haWwuY29tIiwiaHR0cHM6Ly9jcmlibC5jbG91ZC9jbGllbnRSZXF1ZXN0Ijp0cnVlLCJpc3MiOiJodHRwczovL2xvZ2luLmNyaWJsLmNsb3VkLyIsInN1YiI6IllRQTMyc3U2cEkxeG43dlY4T0F1cFE1eExCOGVDR0ROQGNsaWVudHMiLCJhdWQiOiJodHRwczovL2FwaS5jcmlibC5jbG91ZCIsImlhdCI6MTc0OTA0NTc5MSwiZXhwIjoxNzQ5MTMyMTkxLCJzY29wZSI6InVzZXI6cmVhZDpjbGllbnRzIHVzZXI6Y3JlYXRlOmNsaWVudHMgdXNlcjp1cGRhdGU6Y2xpZW50cyB1c2VyOnJlYWQ6d29ya2VyZ3JvdXBzIHVzZXI6dXBkYXRlOndvcmtlcmdyb3VwcyB1c2VyOnJlYWQ6Y29ubmVjdGlvbnMgdXNlcjpjcmVhdGU6Y29ubmVjdGlvbnMgdXNlcjp1cGRhdGU6Y29ubmVjdGlvbnMgdXNlcjpkZWxldGU6Y29ubmVjdGlvbnMgdXNlcjp1cGRhdGU6d29ya3NwYWNlcyB1c2VyOnJlYWQ6d29ya3NwYWNlcyB1c2VyOmRlbGV0ZTp3b3Jrc3BhY2VzIHVzZXI6Y3JlYXRlOndvcmtzcGFjZXMiLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJhenAiOiJZUUEzMnN1NnBJMXhuN3ZWOE9BdXBRNXhMQjhlQ0dETiIsInBlcm1pc3Npb25zIjpbInVzZXI6cmVhZDpjbGllbnRzIiwidXNlcjpjcmVhdGU6Y2xpZW50cyIsInVzZXI6dXBkYXRlOmNsaWVudHMiLCJ1c2VyOnJlYWQ6d29ya2VyZ3JvdXBzIiwidXNlcjp1cGRhdGU6d29ya2VyZ3JvdXBzIiwidXNlcjpyZWFkOmNvbm5lY3Rpb25zIiwidXNlcjpjcmVhdGU6Y29ubmVjdGlvbnMiLCJ1c2VyOnVwZGF0ZTpjb25uZWN0aW9ucyIsInVzZXI6ZGVsZXRlOmNvbm5lY3Rpb25zIiwidXNlcjp1cGRhdGU6d29ya3NwYWNlcyIsInVzZXI6cmVhZDp3b3Jrc3BhY2VzIiwidXNlcjpkZWxldGU6d29ya3NwYWNlcyIsInVzZXI6Y3JlYXRlOndvcmtzcGFjZXMiXX0.CyyOuqe3EZMZ_bj-qlE7GK7LwNOwbYPnrZuHasIMEA55p9wYx7alw0grRfQA-tQFE3qcRRORsSwWcsHo2jdIwYJ7_fxq3NL4678G6-P79ownGvr5OyABLRCP6FsK9W0_FwqAByg0KjBfvnrdKS_O46gk8qFmjR2tkjN1jFqlCfGKtJLv9-9cahl5Sa5jFDBeOqRtI29tiD150_3E9R8e_ng-2CVU6O802oTvHaVmgRoy5J6-Z9t1_JnCvi8jwlhlv36brNeXVDrAK0suunGGKurl9WC_OuUp5E-1JL-MacoCA-wDxxIlNMCTbCl9kzVMWR2Lyk7J2RZsqzWstIGSnQ"
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

