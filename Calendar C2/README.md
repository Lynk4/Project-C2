# Calender C2

---

### 📋 Prerequisites

- Python 3.8+

- Google Account (for Calendar)

- Discord Account (for webhooks)

- Basic terminal knowledge

---

### 🚀 Quick Start
1. Install Dependencies

```python
pip install requests icalendar
```


### 2. Create Google Calendar

Go to calendar.google.com

Click "+" next to "Other calendars" → "Create new calendar"

Configure:

Name: Project Schedule (or any name)

Timezone: Your timezone

```Make calendar public (CRITICAL)```

Get Calendar URL:

Calendar Settings → "Integrate calendar"

Copy "Public address in iCal format"

URL looks like: https://calendar.google.com/calendar/ical/.../public/basic.ics


### 3. Create Discord Webhook

Create Discord Server (or use existing)

Create Text Channel: #c2-output

Get Webhook URL: Channel Settings → Integrations → Webhooks → New Webhook

- Name: C2 Bot

- Copy Webhook URL

- URL looks like: https://discord.com/api/webhooks/123456/abc123...

### 4. Configure Agent


edit mark1.py

```
# ===== CONFIGURATION =====
CALENDAR_ICAL_URL = "PASTE_YOUR_iCal_URL_HERE"
DISCORD_WEBHOOK_URL = "PASTE_YOUR_DISCORD_WEBHOOK_HERE"
```

### 5. Run Agent

### 📝 How It Works
Sending Commands

Create Calendar Event in your public calendar

Title Format: CMD: [base64_encoded_command]

Save Event → Agent detects within 3 seconds

### Encoding Commands

```
# Linux/macOS
echo -n "whoami" | base64
# Output: d2hvYW1p

# Windows PowerShell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("whoami"))
```

---

### 🖥️ Agent Output

#### Terminal Output

<img width="885" height="534" alt="Screenshot 2025-12-24 at 4 53 13 PM" src="https://github.com/user-attachments/assets/94682012-6e0a-435c-a816-e2a10645befd" />

---


#### Discord output

<img width="585" height="426" alt="Screenshot 2025-12-24 at 4 23 37 PM" src="https://github.com/user-attachments/assets/2aad3ab4-11a2-4d82-859a-475606e0209b" />


---

### 🔄 Workflow Diagram

<img width="5287" height="700" alt="worflow" src="https://github.com/user-attachments/assets/30160885-4aa2-417f-9ff3-75a48e2d7194" />

---
