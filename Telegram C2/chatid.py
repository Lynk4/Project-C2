import requests

BOT_TOKEN = "9843982793:XXXXXXXXXXXXXXXXXXXXXXX"  # Replace with your BotFather token

resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates")
if resp.status_code == 200:
    data = resp.json()["result"]
    if data:
        chat_id = data[-1]["message"]["chat"]["id"]
        print(f"Your Chat ID: {chat_id}")
        print(f"Use this in script: CHAT_ID = '{chat_id}'")
    else:
        print("No messages found — send 'test' to bot and re-run.")
else:
    print(f"Error: {resp.status_code} — check your BOT_TOKEN.")