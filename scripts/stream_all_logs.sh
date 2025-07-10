#!/bin/bash
# Stream all FLRTS logs in real-time and start bot with monitoring

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/../logs"
PROJECT_DIR="$SCRIPT_DIR/.."

# Function to cleanup on exit
cleanup() {
    echo -e "\n\033[93mStopping bot monitor...\033[0m"
    if [ ! -z "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null
    fi
    exit 0
}

trap cleanup EXIT INT TERM

echo "=== FLRTS Bot Runner & Log Streamer ==="
echo "Starting bot with monitoring..."
echo ""

# Check if bot is already running
if pgrep -f "telegram_bot.py" > /dev/null; then
    echo -e "\033[93mWarning: Bot appears to be already running\033[0m"
    echo "Showing logs only (not starting new bot instance)"
else
    # Start the bot with monitoring in background
    cd "$PROJECT_DIR"
    python scripts/run_bot_with_monitoring.py &
    BOT_PID=$!
    echo -e "\033[92mBot monitor started (PID: $BOT_PID)\033[0m"
    sleep 2  # Give it time to start
fi

echo ""
echo "Streaming logs... Press Ctrl+C to stop"
echo ""

# Use tail -f to follow multiple log files
tail -f "$LOG_DIR/telegram_bot.log" "$LOG_DIR/api_log.txt" | while read line; do
    # Color code based on content
    if [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"💀"* ]] || [[ "$line" == *"❌"* ]]; then
        echo -e "\033[91m$line\033[0m"  # Red
    elif [[ "$line" == *"SUCCESS"* ]] || [[ "$line" == *"✅"* ]]; then
        echo -e "\033[92m$line\033[0m"  # Green
    elif [[ "$line" == *"INFO"* ]]; then
        echo -e "\033[96m$line\033[0m"  # Cyan
    elif [[ "$line" == *"WARNING"* ]] || [[ "$line" == *"🔄"* ]]; then
        echo -e "\033[93m$line\033[0m"  # Yellow
    elif [[ "$line" == *"Received message"* ]] || [[ "$line" == *"🚀"* ]]; then
        echo -e "\033[94m$line\033[0m"  # Blue
    elif [[ "$line" == "==> "* ]]; then
        echo -e "\033[95m$line\033[0m"  # Magenta for file headers
    else
        echo "$line"
    fi
done