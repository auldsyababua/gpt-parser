# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Testing Protocol

When fixing bugs or implementing features, NEVER claim something is "fixed" or "working correctly" before the user has personally tested it. Instead, always end with:

"To verify this fix, here's what we should test:"

1. List specific steps the user should take
2. Include expected outcomes for each step
3. Provide clear rationale for why these tests verify the fix
4. Include edge cases or potential failure modes to check

Example format:
```
To verify this fix, here's what we should test:

1. Start the bot: `python -m integrations.telegram.bot`
   - Expected: Bot starts without errors, shows "Assistant initialized successfully"
   
2. Send a test message in Telegram: "Remind Joel at 3pm to check oil"
   - Expected: Bot responds with "Processing your request..." followed by parsed task confirmation
   
3. Test with timezone: "Tell Bryan at 2pm CST to restart servers"
   - Expected: Bot correctly identifies CST timezone in the parsed output
   
4. Test timeout handling: Send a message and wait
   - Expected: If API is slow, should see timeout message after 30 seconds

This verifies: async execution, assistant initialization, timezone parsing, and error handling.
```

## Project Overview

gpt-parser is a natural language task parsing system for off-grid bitcoin mining operations. It converts informal task descriptions (e.g., "Remind Joel at 7pm tomorrow to restart the node at Site A") into structured JSON data that can be stored in Google Sheets or other task management systems.

## Architecture

The system flow:
1. User sends task via Telegram bot (`integrations/telegram/bot.py`)
2. Bot forwards to parser (`parsers/unified.py` or `parsers/openai_assistant.py`)
3. Parser converts text into JSON following `schema/task_schema.json`
4. Valid tasks are sent to Google Sheets via Apps Script webhook

Key components:
- **Parsers**: `parsers/` - Core parsing implementations
  - `unified.py` - Fast GPT-4o-mini implementation
  - `openai_assistant.py` - OpenAI Assistant API implementation
- **Integrations**: `integrations/` - External services
  - `telegram/bot.py` - Telegram bot interface
  - `google_sheets/code.gs` - Sheet integration
- **CLI Tools**: `cli/` - Command-line utilities
  - `run_bot.py` - Bot runner with monitoring
  - `evaluate.py` - Test evaluation
- **Operations**: `operations/monitoring.py` - Process monitoring

## Development Commands

### Running the Bot
```bash
# Start bot with monitoring
python3 -m cli.run_bot

# Run bot directly
python3 -m integrations.telegram.bot

# Stream logs
./scripts/stream_telegram_logs.sh
```

### Testing
```bash
# Run evaluation against test inputs
python3 -m cli.evaluate

# Test inputs are in tests/inputs.txt
# Expected outputs are in tests/expected_outputs.jsonl
```

### Dependencies
```bash
# Install requirements
pip3 install -r requirements.txt
```

Required environment variables:
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`

## Domain Context

The system is designed for three operators: Colin (default assigner), Bryan, and Joel. Tasks relate to:
- Generator maintenance (oil checks, coolant, etc.)
- Site management (Sites A, B, C, D)
- Equipment monitoring (flare skids, nodes, telemetry)
- Contractor coordination
- Recurring maintenance schedules

All timestamps are stored in UTC. The schema enforces specific assignees and a "pending" status for new tasks.

## Code Style

- Python 3.10+ required
- Use existing logging patterns (see `integrations/telegram/bot.py`)
- Follow the JSON schema strictly (`schema/task_schema.json`)
- Error handling should preserve original user input for debugging

## Directory Structure Rules

### NEVER put in scripts/:
- The `scripts/` directory has been removed to prevent code dumping
- Use the appropriate directory based on code function

### File Placement:
- **Parsers**: Put parsing logic in `parsers/`
- **External Services**: Put integrations in `integrations/<service>/`
- **CLI Tools**: Put command-line utilities in `cli/`
- **Utilities**: Keep shared utilities in `utils/`
- **Configuration**: Put config files in `config/`
- **Tests**: Put all tests in `tests/`

### Temporary Files:
- ALWAYS use `scratch/` for experiments and temporary scripts
- ALWAYS clean up after tasks
- NEVER commit files from `scratch/`
- Files in `scratch/` are gitignored

### When Adding Features:
1. Identify the correct directory based on function
2. Use descriptive filenames
3. Update relevant `__init__.py` files
4. Add tests in `tests/`
5. Update imports to use new paths

### Import Best Practices:
- Use absolute imports from project root
- Consider using the convenience module: `from gpt_parser import ...`
- Keep imports organized and grouped