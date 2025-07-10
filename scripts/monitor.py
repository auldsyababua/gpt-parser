#!/usr/bin/env python3
"""
Simple monitoring script to check if the telegram bot is running
and display recent logs.
"""
import os
import subprocess
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "telegram_bot.log")
API_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "api_log.txt")


def check_process(process_name):
    """Check if a process is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", process_name], capture_output=True, text=True
        )
        return len(result.stdout.strip()) > 0
    except Exception:
        return False


def tail_log(file_path, lines=10):
    """Get the last N lines from a log file"""
    if not os.path.exists(file_path):
        return f"Log file not found: {file_path}"

    try:
        with open(file_path, "r") as f:
            all_lines = f.readlines()
            return "".join(all_lines[-lines:])
    except Exception as e:
        return f"Error reading log: {e}"


def main():
    print(
        f"=== Telegram Bot Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
    )

    # Check if bot is running
    bot_running = check_process("telegram_bot.py")
    print(f"Bot Status: {'🟢 RUNNING' if bot_running else '🔴 NOT RUNNING'}")

    # Show recent telegram bot logs
    print("\n--- Recent Telegram Bot Logs ---")
    print(tail_log(LOG_FILE, 15))

    # Show recent API logs
    print("\n--- Recent API Logs ---")
    print(tail_log(API_LOG_FILE, 10))


if __name__ == "__main__":
    main()
