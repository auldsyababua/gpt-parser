#!/usr/bin/env python3
"""Restart bot with forced module reloading"""

import subprocess
import time
import os
import signal


def kill_bot_processes():
    """Kill all bot-related processes"""
    print("🛑 Killing existing bot processes...")

    # Try to kill by name patterns
    patterns = ["python.*telegram.*bot", "python.*run_bot"]

    for pattern in patterns:
        try:
            result = subprocess.run(["pkill", "-f", pattern], capture_output=True)
            if result.returncode == 0:
                print(f"  ✅ Killed processes matching: {pattern}")
        except:
            pass

    # Also try specific PIDs if we know them
    pids_to_check = []
    try:
        ps_result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for line in ps_result.stdout.split("\n"):
            if "telegram" in line and "bot" in line and "grep" not in line:
                parts = line.split()
                if len(parts) > 1:
                    pids_to_check.append(parts[1])
    except:
        pass

    for pid in pids_to_check:
        try:
            os.kill(int(pid), signal.SIGTERM)
            print(f"  ✅ Killed PID: {pid}")
        except:
            pass

    # Wait for processes to die
    time.sleep(2)


def clear_all_caches():
    """Clear all Python caches"""
    print("\n🧹 Clearing all caches...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Clear .pyc files
    subprocess.run(
        ["find", project_root, "-name", "*.pyc", "-type", "f", "-delete"], check=False
    )

    # Clear __pycache__ directories
    subprocess.run(
        [
            "find",
            project_root,
            "-name",
            "__pycache__",
            "-type",
            "d",
            "-exec",
            "rm",
            "-rf",
            "{}",
            "+",
        ],
        check=False,
    )

    print("  ✅ Caches cleared")


def start_bot_fresh():
    """Start bot with fresh Python interpreter"""
    print("\n🚀 Starting bot with fresh modules...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(project_root, "venv", "bin", "python3")

    # Set environment to disable Python bytecode
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    # Start the bot directly (not through run_bot.py to avoid extra layers)
    cmd = [venv_python, "-B", "-m", "integrations.telegram.bot"]

    print(f"  Command: {' '.join(cmd)}")
    print("  Note: Using -B flag to prevent bytecode generation")
    print("\n📱 Bot starting... Watch for module loading messages above...")

    # Run the bot
    subprocess.run(cmd, env=env)


if __name__ == "__main__":
    print("=== Bot Clean Restart Tool ===")

    # Step 1: Kill existing processes
    kill_bot_processes()

    # Step 2: Clear all caches
    clear_all_caches()

    # Step 3: Start fresh
    start_bot_fresh()
