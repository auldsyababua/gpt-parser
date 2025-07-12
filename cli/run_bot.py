#!/usr/bin/env python3
"""
Run the telegram bot with process monitoring and crash detection
"""
import subprocess
import time
import logging
import os
import sys
from datetime import datetime

# Setup logging
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "telegram_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger("BOT_MONITOR")


def monitor_process(proc, name):
    """Monitor a process and log when it dies"""
    while True:
        retcode = proc.poll()
        if retcode is not None:
            logger.error(f"💀 {name} DIED! Exit code: {retcode}")
            logger.error(
                f"❌ {name} crashed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Try to capture any error output
            if proc.stderr:
                stderr_output = proc.stderr.read()
                if stderr_output:
                    logger.error(
                        f"{name} stderr: {stderr_output.decode('utf-8', errors='ignore')}"
                    )

            logger.info(f"🔄 Attempting to restart {name} in 5 seconds...")
            time.sleep(5)
            return retcode
        time.sleep(1)


def run_bot():
    """Run the telegram bot with monitoring"""
    logger.info("🚀 Starting Telegram Bot with monitoring...")

    # Get the project root and venv python
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(project_root, "venv", "bin", "python3")

    # Use venv python if it exists, otherwise fall back to system python
    if os.path.exists(venv_python):
        python_executable = venv_python
        logger.info(f"Using venv Python: {python_executable}")
    else:
        python_executable = sys.executable
        logger.warning(f"Venv not found, using system Python: {python_executable}")

    while True:
        try:
            # Start the bot process
            proc = subprocess.Popen(
                [
                    python_executable,
                    "-m",
                    "integrations.telegram.bot",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )

            logger.info(f"✅ Bot started with PID: {proc.pid}")

            # Monitor the process
            exit_code = monitor_process(proc, "TELEGRAM BOT")

            if exit_code == 0:
                logger.info("Bot exited normally")
                break
            else:
                logger.warning(f"Bot crashed with exit code {exit_code}, restarting...")

        except KeyboardInterrupt:
            logger.info("⏹️  Received shutdown signal")
            if proc.poll() is None:
                proc.terminate()
            break
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            time.sleep(5)


if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("👋 Bot monitor stopped by user")
