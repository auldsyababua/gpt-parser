# Enhanced CLAUDE.md Template

This is the enhanced CLAUDE.md file that incorporates LLM-friendly practices:

```markdown
# CLAUDE.md - GPT Parser Project Guidelines

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

gpt-parser is a natural language task parsing system for off-grid bitcoin mining operations.

## Directory Structure & Rules

### Directory Map
```
gpt-parser/
├── parsers/         # Core parsing logic ONLY
├── integrations/    # External service connections ONLY  
├── cli/            # Command-line entry points ONLY
├── utils/          # Shared utilities
├── config/         # Configuration files
├── tests/          # All test code
├── scratch/        # TEMPORARY work area (auto-cleanup required)
└── logs/           # Application logs (git-ignored)
```

### 🚫 NEVER Put These in Wrong Directories:

**scripts/ directory NO LONGER EXISTS - DO NOT CREATE IT**

- ❌ Test scripts → use `tests/`
- ❌ Temporary code → use `scratch/`
- ❌ Parser implementations → use `parsers/`
- ❌ Bot code → use `integrations/telegram/`
- ❌ CLI tools → use `cli/`

### ✅ Correct File Placement:

1. **Adding a new parser?**
   - Location: `parsers/new_parser.py`
   - Update: `parsers/__init__.py`
   - Tests: `tests/unit/test_new_parser.py`

2. **Creating a temporary test?**
   - Location: `scratch/test_something.py`
   - Cleanup: DELETE after use
   - Never commit files from scratch/

3. **Adding a CLI command?**
   - Location: `cli/command_name.py`
   - Pattern: Single entry point per file
   - Import core logic from parsers/utils

## File Management Rules

### Temporary Files

1. **ALWAYS use scratch/ for temporary work**
2. **ALWAYS clean up temporary files after tasks**
3. **NEVER commit files from scratch/**
4. **Add this to end of tasks**: "Cleaning up temporary files from scratch/"

### When Creating Files

```python
# Good: Clear purpose and location
parsers/openai_assistant.py
integrations/telegram/bot.py
tests/unit/test_temporal_processor.py

# Bad: Vague names or wrong location  
scripts/test.py
script_v2.py
temp_parser.py
```

## Development Workflow

### Before Starting a Task

1. Identify which directory the work belongs in
2. Check if temporary files will be needed → use scratch/
3. Plan file locations before creating them

### After Completing a Task

1. Remove any files from scratch/
2. Ensure all files are in correct directories
3. Update this file if you found new patterns
4. Run relevant tests

## Testing

### Running Tests
```bash
# All tests
python -m pytest tests/

# Specific module
python -m pytest tests/unit/test_temporal_processor.py

# With coverage
python -m pytest tests/ --cov=parsers --cov=integrations
```

### Test File Organization
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Performance tests: `tests/performance/`
- Test fixtures: `tests/fixtures/`
- Temporary test files: `tests/temp/` (auto-cleaned)

## Common Commands

### Parser Testing
```bash
python -m cli.parse_task "Remind Joel at 3pm to check oil"
```

### Bot Operations
```bash
# Start bot
python -m cli.run_bot

# View logs
tail -f logs/telegram_bot.log
```

### Model Comparison
```bash
python -m cli.compare_models
```

## Import Patterns

### Correct Imports After Reorganization
```python
# Parsers
from parsers.openai_assistant import parse_task
from parsers.groq_chat import GroqParser

# Integrations
from integrations.telegram.bot import start_bot
from integrations.google_sheets.webhook import send_to_sheets

# Utilities
from utils.temporal_processor import preprocess_time
from utils.timezone_converter import convert_timezone
```

## Git Commit Guidelines

### Before Committing

1. Check for files in scratch/ (should not be committed)
2. Ensure imports are updated if files moved
3. Run tests to verify nothing broke
4. Use descriptive commit messages

### Commit Message Format
```
type: brief description

- Detail 1
- Detail 2

Closes #issue
```

Types: feat, fix, docs, refactor, test, chore

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...

# Optional
GROQ_API_KEY=...
GOOGLE_APPS_SCRIPT_URL=...
```

## Troubleshooting

### Import Errors After Reorganization

1. Check if using old path (scripts/ instead of new location)
2. Verify __init__.py exists in parent directories
3. Use proper module imports: `python -m cli.parse_task`

### Temporary Files Accumulating

1. Check scratch/ directory
2. Delete all contents except README.md
3. Check tests/temp/ directory
4. Add cleanup to your workflow

## Performance Benchmarks

- GPT-4o-mini: ~12s per request
- Groq Llama3: ~1.1s per request  
- Target: <2s for user response

## Remember

1. **scratch/ is for temporary work only**
2. **No more scripts/ directory**
3. **Clean up after yourself**
4. **Place files by function, not by type**
5. **Update docs when adding features**
```