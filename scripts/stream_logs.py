#!/usr/bin/env python3
"""
Stream logs in real-time with color coding
"""
import subprocess
import sys
import os

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "telegram_bot.log")

def colorize_line(line):
    """Add colors to log lines based on content"""
    if 'ERROR' in line:
        return f"{RED}{line}{RESET}"
    elif 'SUCCESS' in line or '✅' in line:
        return f"{GREEN}{line}{RESET}"
    elif 'INFO' in line:
        return f"{CYAN}{line}{RESET}"
    elif 'WARNING' in line:
        return f"{YELLOW}{line}{RESET}"
    elif 'Received message' in line:
        return f"{BLUE}{line}{RESET}"
    else:
        return line

def main():
    print(f"{GREEN}=== Streaming Telegram Bot Logs ==={RESET}")
    print(f"Watching: {LOG_FILE}")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Use tail -f to follow the log file
        proc = subprocess.Popen(['tail', '-f', LOG_FILE], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
        
        for line in iter(proc.stdout.readline, ''):
            print(colorize_line(line.rstrip()))
            sys.stdout.flush()
            
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopped streaming logs{RESET}")
        proc.terminate()
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")

if __name__ == "__main__":
    main()