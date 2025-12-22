# Telegram as a c2..........

---

```
┌─────────────────┐    HTTPS    ┌─────────────────┐    HTTPS    ┌─────────────────┐
│                 │─────────────▶│   Telegram      │─────────────▶│                 │
│  Target System  │             │    Bot API      │             │  Operator's     │
│    (Agent)      │◀─────────────│                 │◀─────────────│  Telegram App   │
│                 │             │                 │             │                 │
└─────────────────┘             └─────────────────┘             └─────────────────┘
        │                                                               │
        │ Subprocess Execution                                          │ Command Input
        ▼                                                               ▼
┌─────────────────┐                                             ┌─────────────────┐
│  Local Commands │                                             │  Encrypted Chat │
│  (Shell/PS/etc) │                                             │  with Bot       │
└─────────────────┘                                             └─────────────────┘
```
---


### Data Flow:

    - Operator sends command via Telegram to bot

    - Bot forwards to Telegram API

    - Agent polls API for new commands

    - Agent executes command locally

    - Results sent back via Telegram API

    - Operator receives results in Telegram


---

### 📋 Prerequisites Software Requirements

- Python 3.8+ (tested on 3.8-3.12)

- pip package manager

- Git (for cloning repository)

- Telegram account (mobile or desktop)

```python
# Core dependencies
pip install requests

# Optional (for enhanced features)
pip install cryptography      # For encrypted config
pip install pillow           # For screenshots (Windows)
pip install netifaces        # For network interface detection
```

---



### Telegram Requirements

- Active Telegram account

- Bot token from @BotFather

- Your Chat ID from @userinfobot

---


### 🔧 Setup Guide (Step by Step)
### Step 1: Create Telegram Bot

- Open Telegram on any device

- Search for @BotFather (official bot creator)

- Start chat and send: /newbot

- Choose a name for your bot (e.g., "SystemMonitor")

- Choose a username ending with 'bot' (e.g., "system_monitor_bot")

- SAVE THE TOKEN provided (looks like: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ)

---


### Step 2: Get Your Chat ID

- use chatid.py to get it........

- Save the number (e.g., 123456789)

---

### Step 3: Configure the Agent

```python3
# In the script, edit these lines:
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"      # From @BotFather
CHAT_ID = "YOUR_CHAT_ID_HERE"          # From @userinfobot
```

---

### 🎮 Usage Starting the Agent

```
python3 telegram_c2.py
```

### On telegram bot

Will get a notification on telegram bot.


----


### 📖 Commands Reference

<img width="788" height="341" alt="Screenshot 2025-12-22 at 1 57 06 PM" src="https://github.com/user-attachments/assets/47c54633-1c8d-4262-87a7-4287099c43ae" />


---

