#!/usr/bin/env python3
"""
Repository reorganization migration script.
Creates new structure and moves files safely.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def create_directories():
    """Create new directory structure."""
    print("\n=== Creating new directories ===")

    directories = [
        "parsers",
        "integrations/telegram",
        "integrations/google_sheets",
        "cli",
        "development-phases",
        ".claude/commands",
        "tests/temp",
        "scratch",
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")


def create_init_files():
    """Create __init__.py files for Python packages."""
    print("\n=== Creating __init__.py files ===")

    init_locations = [
        "parsers/__init__.py",
        "integrations/__init__.py",
        "integrations/telegram/__init__.py",
        "integrations/google_sheets/__init__.py",
        "cli/__init__.py",
    ]

    for init_file in init_locations:
        Path(init_file).touch()
        print(f"Created: {init_file}")


def move_files():
    """Move files to new locations using git mv."""
    print("\n=== Moving files ===")

    moves = [
        # Parsers
        ("scripts/assistants_api_runner.py", "parsers/openai_assistant.py"),
        ("scripts/groq_parser.py", "parsers/groq_chat.py"),
        # Integrations
        ("scripts/telegram_bot.py", "integrations/telegram/bot.py"),
        ("scripts/code.gs", "integrations/google_sheets/code.gs"),
        # CLI tools
        ("scripts/run_bot_with_monitoring.py", "cli/run_bot.py"),
        ("scripts/evaluate_output.py", "cli/evaluate.py"),
        ("scripts/monitor.py", "cli/monitor.py"),
        # Development docs
        ("github-issues", "development-phases"),
    ]

    for src, dst in moves:
        if os.path.exists(src):
            run_command(f"git mv {src} {dst}")
            print(f"Moved: {src} -> {dst}")
        else:
            print(f"Skipped (not found): {src}")


def create_helper_files():
    """Create helper files for LLM guidance."""
    print("\n=== Creating helper files ===")

    # scratch/README.md
    scratch_readme = """# Scratch Directory

⚠️ **TEMPORARY FILES ONLY** ⚠️

Files in this directory are:
- Not tracked by git
- Subject to deletion at any time
- For development experiments only

Use this for:
- Testing new features
- Temporary scripts
- Work-in-progress code
"""

    with open("scratch/README.md", "w") as f:
        f.write(scratch_readme)
    print("Created: scratch/README.md")

    # scratch/.gitignore
    with open("scratch/.gitignore", "w") as f:
        f.write("*\n!README.md\n!.gitignore\n")
    print("Created: scratch/.gitignore")

    # .claude/commands/cleanup.md
    cleanup_command = """After completing this task:
1. Remove any temporary files from scratch/
2. Ensure all new files are in proper directories
3. Update CLAUDE.md if you discovered new patterns
4. Run tests to verify nothing broke
"""

    with open(".claude/commands/cleanup.md", "w") as f:
        f.write(cleanup_command)
    print("Created: .claude/commands/cleanup.md")


def update_imports():
    """Update Python imports in moved files."""
    print("\n=== Updating imports ===")

    # This is a simplified version - in practice you'd want more sophisticated replacement
    import_updates = [
        # Update telegram bot imports
        (
            "integrations/telegram/bot.py",
            "from assistants_api_runner import",
            "from parsers.openai_assistant import",
        ),
        # Update CLI imports
        (
            "cli/run_bot.py",
            "from telegram_bot import",
            "from integrations.telegram.bot import",
        ),
    ]

    for file_path, old_import, new_import in import_updates:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()

            if old_import in content:
                content = content.replace(old_import, new_import)
                with open(file_path, "w") as f:
                    f.write(content)
                print(f"Updated imports in: {file_path}")


def create_consolidated_docs():
    """Consolidate development phase documents."""
    print("\n=== Creating consolidated documentation ===")

    completed_features = """# Completed Features

This document tracks features that have been implemented and need review/merge.

## Phase 1: Core Parser ✅
- **Status**: Implemented
- **Branch**: main
- **Description**: Basic OpenAI Assistant API integration

## Phase 2: Multi-User Timezone Support ✅
- **Status**: Implemented
- **Branch**: main
- **Description**: User timezone configuration and conversion

## Temporal Preprocessing 🔄
- **Status**: In Progress
- **Branch**: implement-temporal-preprocessor
- **PR**: [Link to PR when created]
- **Description**: Preprocessing common time expressions before LLM parsing

## Button UI Enhancement 🆕
- **Status**: Ready for implementation
- **Location**: scratch/telegram-buttons/
- **Description**: Inline keyboard buttons for better UX

## User Authentication 🆕
- **Status**: Ready for implementation
- **Location**: scratch/user-prefs/
- **Description**: User authorization and preferences system
"""

    with open("development-phases/completed-features.md", "w") as f:
        f.write(completed_features)
    print("Created: development-phases/completed-features.md")


def main():
    """Run the migration."""
    print("=== Repository Reorganization Migration ===")
    print("This script will reorganize the repository structure.")
    print("Make sure you're on a clean branch before proceeding.\n")

    response = input("Continue? (y/n): ")
    if response.lower() != "y":
        print("Aborted.")
        return

    # Check if we're in the right directory
    if not os.path.exists("scripts") or not os.path.exists("CLAUDE.md"):
        print("Error: Run this from the repository root directory.")
        sys.exit(1)

    # Create new branch
    print("\n=== Creating new branch ===")
    run_command("git checkout -b reorganize-for-llm-navigation")

    # Run migration steps
    create_directories()
    create_init_files()
    move_files()
    create_helper_files()
    update_imports()
    create_consolidated_docs()

    print("\n=== Migration complete! ===")
    print("\nNext steps:")
    print("1. Review the changes with: git status")
    print("2. Test the reorganized code")
    print("3. Update remaining imports manually")
    print("4. Copy enhanced CLAUDE.md from scratch/repo-reorganization/")
    print("5. Commit when ready")


if __name__ == "__main__":
    main()
