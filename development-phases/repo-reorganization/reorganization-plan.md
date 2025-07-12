# Repository Reorganization Plan

## Overview

Reorganize the gpt-parser repository to be more LLM-friendly and prevent common Claude Code mistakes like dumping everything in scripts/ or creating temporary files everywhere.

## Current Problems

1. **Scripts folder becomes a dumping ground** - LLMs put ANY script there
2. **No clear separation of concerns** - Parsers mixed with CLI tools
3. **Temporary files scattered everywhere** - No designated cleanup area
4. **Unclear naming** - "scripts" doesn't tell you what's inside
5. **Path confusion** - "github-issues" folder doesn't contain GitHub issues

## New LLM-Friendly Structure

```
gpt-parser/
├── parsers/                    # Core parsing implementations only
│   ├── openai_assistant.py     # (from assistants_api_runner.py)
│   ├── groq_chat.py           # (from groq_parser.py)
│   ├── local_llama.py         # Future local implementation
│   └── __init__.py
│
├── integrations/              # External service connections
│   ├── telegram/
│   │   ├── bot.py            # (from telegram_bot.py)
│   │   ├── handlers.py       # Message/button handlers
│   │   └── auth.py           # User authentication
│   ├── google_sheets/
│   │   ├── webhook.py        # Sheets integration
│   │   └── code.gs          # Apps Script code
│   └── __init__.py
│
├── cli/                       # Command-line entry points only
│   ├── parse_task.py         # Single task parser
│   ├── run_bot.py           # (from run_bot_with_monitoring.py)
│   ├── evaluate.py          # (from evaluate_output.py)
│   └── compare_models.py    # Model comparison tool
│
├── utils/                     # Shared utilities (keep as is)
│   ├── temporal_processor.py
│   ├── timezone_converter.py
│   └── __init__.py
│
├── config/                    # All configuration
│   ├── timezone_config.py
│   ├── users.json           # User authorization
│   └── prompts/             # System prompts
│
├── tests/                     # All test code
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   ├── fixtures/            # Test data
│   └── temp/                # Temporary test files (auto-cleaned)
│
├── development-phases/        # Project planning docs
│   ├── completed-features.md # Links to implemented features
│   ├── future-phases.md     # Upcoming work
│   └── temporal-fix.md      # Specific bug documentation
│
├── docs/                      # User documentation
│   ├── setup.md
│   ├── usage.md
│   └── api.md
│
├── scratch/                   # Temporary work area
│   ├── README.md             # "Files here are temporary!"
│   └── .gitignore            # Ignore everything except README
│
├── logs/                      # Application logs
│   └── .gitignore            # Ignore all logs
│
├── .claude/                   # Claude Code configuration
│   └── commands/             # Slash command templates
│       ├── cleanup.md        # Cleanup reminder
│       ├── test.md          # Test execution
│       └── commit.md        # Safe commit practices
│
├── CLAUDE.md                 # Enhanced with new rules
├── .env.example              # Environment template
└── requirements.txt          # Python dependencies
```

## Key Improvements

### 1. Clear Purpose Directories
- `parsers/` - ONLY parsing logic
- `integrations/` - ONLY external service code
- `cli/` - ONLY command-line entry points
- `scratch/` - ONLY temporary work

### 2. Descriptive Names
- `telegram_bot.py` → `integrations/telegram/bot.py`
- `assistants_api_runner.py` → `parsers/openai_assistant.py`
- `run_bot_with_monitoring.py` → `cli/run_bot.py`

### 3. Designated Temporary Area
- `scratch/` for development work
- `tests/temp/` for test artifacts
- Both have .gitignore to prevent commits

### 4. Claude Code Helpers
- `.claude/commands/` for consistent prompts
- Enhanced CLAUDE.md with explicit rules

## Migration Steps

### Phase 1: Create New Branch
```bash
git checkout -b reorganize-for-llm-navigation
```

### Phase 2: Create Directory Structure
```bash
# Create all new directories
mkdir -p parsers integrations/telegram integrations/google_sheets
mkdir -p cli development-phases .claude/commands
mkdir -p tests/temp scratch
```

### Phase 3: Move Files (with git mv)
```bash
# Parsers
git mv scripts/assistants_api_runner.py parsers/openai_assistant.py
git mv scripts/groq_parser.py parsers/groq_chat.py

# Integrations
git mv scripts/telegram_bot.py integrations/telegram/bot.py
git mv scripts/code.gs integrations/google_sheets/

# CLI tools
git mv scripts/run_bot_with_monitoring.py cli/run_bot.py
git mv scripts/evaluate_output.py cli/evaluate.py

# Development docs
git mv github-issues development-phases
```

### Phase 4: Update Imports

1. **Update all Python imports**:
   ```python
   # Old
   from assistants_api_runner import parse_task
   
   # New
   from parsers.openai_assistant import parse_task
   ```

2. **Update relative imports in moved files**

3. **Update any hardcoded paths**

### Phase 5: Create Helper Files

1. **scratch/README.md**:
   ```markdown
   # Scratch Directory
   
   ⚠️ **TEMPORARY FILES ONLY** ⚠️
   
   Files in this directory are:
   - Not tracked by git
   - Subject to deletion at any time
   - For development experiments only
   
   Use this for:
   - Testing new features
   - Temporary scripts
   - Work-in-progress code
   ```

2. **.claude/commands/cleanup.md**:
   ```markdown
   After completing this task:
   1. Remove any temporary files from scratch/
   2. Ensure all new files are in proper directories
   3. Update CLAUDE.md if you discovered new patterns
   4. Run tests to verify nothing broke
   ```

### Phase 6: Update CLAUDE.md

Add these sections:

```markdown
## Directory Structure Rules

### NEVER put in scripts/:
- Test files (use tests/)
- Temporary scripts (use scratch/)
- External integrations (use integrations/)
- Core logic (use parsers/)

### Temporary Files:
- ALWAYS use scratch/ for experiments
- ALWAYS clean up after tasks
- NEVER commit files from scratch/

### When Adding Features:
1. Identify the correct directory
2. Use descriptive filenames
3. Update relevant __init__.py
4. Add tests in tests/
```

### Phase 7: Testing

1. Run all existing tests
2. Test each entry point:
   ```bash
   python -m cli.parse_task "Test task"
   python -m cli.run_bot
   python -m cli.evaluate
   ```
3. Verify imports work correctly

## Benefits

1. **Claude won't dump everything in scripts/**
2. **Clear where temporary work goes**
3. **Obvious where each type of code belongs**
4. **Easier to find files by function**
5. **Prevents accidental commits of temp files**

## Rollback Plan

If issues arise:
```bash
git checkout main
git branch -D reorganize-for-llm-navigation
```

All moves use `git mv` so history is preserved.

**Recommended Extension: Python Refactor**

What it does: Lets you move/rename Python files and will attempt to update all import statements in your workspace accordingly.
How to use:
Install the extension from the VSCode marketplace.
Right-click the Python file you want to move/rename in the VSCode explorer.
Choose “Refactor: Move” or “Refactor: Rename”.
The extension will update import paths in your project.
Limitations:
It may not catch every edge case, especially with dynamic imports or non-standard project structures.
Always review the changes (use version control to see the diff).

**Other Notes**

Manual Search & Replace
- Double check by using global search (Cmd+Shift+F on Mac) to search for the old path to make sure there are no more calls to it.
- Always check your codebase for broken imports after moving files, especially in Python.
- Use relative imports where possible for easier refactoring.
- Keep your project structure modular (which you already do).
- Use version control (git) to review and revert any unwanted changes after a move/refactor.
- After moving files, run your test suite (tests/ directory) to catch any broken imports.
- Use a linter to catch unresolved imports.
- do 