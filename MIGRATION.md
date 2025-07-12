# Repository Reorganization Migration Guide

## Overview

The gpt-parser repository has been reorganized to improve code organization and make it more LLM-friendly. This guide helps you navigate the changes.

## Import Changes

### Parser Imports
- **Old**: `from scripts.assistants_api_runner import parse_task`
- **New**: `from parsers.openai_assistant import parse_task`

- **Old**: `from scripts.unified_parser import UnifiedParser`
- **New**: `from parsers.unified import UnifiedParser`

### Integration Imports
- **Old**: `from scripts.telegram_bot import run_bot`
- **New**: `from integrations.telegram.bot import run_bot`

### Convenience Import
You can now use the root-level convenience module:
```python
from gpt_parser import UnifiedParser, parse_with_assistant, run_bot
```

## Running Scripts

### Telegram Bot
- **Old**: `python scripts/telegram_bot.py`
- **New**: `python -m integrations.telegram.bot`

### Bot with Monitoring
- **Old**: `python scripts/run_bot_with_monitoring.py`
- **New**: `python -m cli.run_bot`

### Evaluation
- **Old**: `python scripts/evaluate_output.py`
- **New**: `python -m cli.evaluate`

## File Locations

### Moved Files
| Old Location | New Location |
|--------------|--------------|
| `scripts/assistants_api_runner.py` | `parsers/openai_assistant.py` |
| `scripts/unified_parser.py` | `parsers/unified.py` |
| `scripts/telegram_bot.py` | `integrations/telegram/bot.py` |
| `scripts/code.gs` | `integrations/google_sheets/code.gs` |
| `scripts/run_bot_with_monitoring.py` | `cli/run_bot.py` |
| `scripts/evaluate_output.py` | `cli/evaluate.py` |
| `scripts/monitor.py` | `operations/monitoring.py` |
| `prompts/` | `config/prompts/` |
| `github-issues/` | `development-phases/` (files moved directly, no subdirectory) |

### New Directories
- `parsers/` - Core parsing implementations
- `integrations/` - External service connections
- `cli/` - Command-line entry points
- `operations/` - Operational and monitoring tools
- `common/` - Shared utilities (future use)
- `.claude/` - Claude Code configuration
- `scratch/` - Temporary development area

## Updating Your Code

If you have local changes or scripts that import from the old structure:

1. Update all imports as shown above
2. Update any file paths that reference the old structure
3. Run tests to ensure everything works:
   ```bash
   python -m pytest tests/
   ruff check .
   ```

## Benefits

1. **Clear separation of concerns** - Easy to find code by function
2. **LLM-friendly** - Prevents dumping everything in scripts/
3. **Better organization** - Logical grouping of related code
4. **Cleaner imports** - More intuitive import paths

## Rollback

If you need to revert to the old structure:
```bash
git checkout pre-reorg-backup
```

The backup branch contains the code before reorganization.