"""Convenience imports for gpt-parser."""

from parsers.unified import (
    parse_task as parse_with_unified,
    format_task_for_confirmation,
    send_to_google_sheets,
)
from parsers.openai_assistant import (
    parse_task as parse_with_assistant,
    get_or_create_assistant,
)

# Note: Telegram bot is run as a module, not imported

__version__ = "1.0.0"
__all__ = [
    "parse_with_unified",
    "parse_with_assistant",
    "get_or_create_assistant",
    "format_task_for_confirmation",
    "send_to_google_sheets",
]
