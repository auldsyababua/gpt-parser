"""
Temporal expression pre-processor using dateparser library.
Handles common temporal expressions to reduce LLM processing time.
"""

import re
import dateparser
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any
import pytz
import logging

logger = logging.getLogger(__name__)


class TemporalProcessor:
    """Pre-processes temporal expressions using dateparser for faster parsing."""

    def __init__(self, default_timezone: str = "America/Los_Angeles"):
        """
        Initialize the temporal processor.

        Args:
            default_timezone: Default timezone for parsing (Colin's PDT)
        """
        self.default_timezone = default_timezone
        self.tz = pytz.timezone(default_timezone)

        # Common patterns that dateparser might miss
        self.custom_patterns = {
            r"end of (?:the )?hour": self._handle_end_of_hour,
            r"top of (?:the )?hour": self._handle_top_of_hour,
            r"end of (?:the )?day": self._handle_end_of_day,
            r"end of tonight": self._handle_end_of_tonight,
            r"(?:this )?weekend": self._handle_weekend,
        }

        # Timezone mapping for city names
        self.city_to_tz = {
            "houston": "CST",
            "chicago": "CST",
            "dallas": "CST",
            "austin": "CST",
            "la": "PST",
            "los angeles": "PST",
            "san francisco": "PST",
            "seattle": "PST",
            "new york": "EST",
            "nyc": "EST",
            "boston": "EST",
            "miami": "EST",
        }

    def preprocess(
        self, text: str, reference_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Pre-process temporal expressions in the text.

        Args:
            text: Input text containing temporal expressions
            reference_time: Reference time for relative expressions (default: now)

        Returns:
            Dict containing:
                - original_text: The original input
                - processed_text: Text with temporal expressions replaced
                - temporal_data: Extracted temporal information
                - confidence: Confidence score (0-1)
        """
        if reference_time is None:
            reference_time = datetime.now(self.tz)

        result = {
            "original_text": text,
            "processed_text": text,
            "temporal_data": {},
            "confidence": 0.0,
        }

        # Extract timezone if specified
        timezone_info = self._extract_timezone(text)
        if timezone_info:
            result["temporal_data"]["timezone"] = timezone_info["timezone"]
            text = timezone_info["cleaned_text"]

        # Try custom patterns first
        for pattern, handler in self.custom_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                custom_result = handler(text, reference_time)
                if custom_result:
                    result.update(custom_result)
                    result["confidence"] = 0.9
                    return result

        # Extract time-related parts
        time_parts = self._extract_time_parts(text)

        if time_parts["date_part"] or time_parts["time_part"]:
            # Try parsing with dateparser
            parsed_result = self._parse_with_dateparser(
                time_parts,
                reference_time,
                timezone_info.get("timezone") if timezone_info else None,
            )

            if parsed_result:
                result["processed_text"] = self._build_processed_text(
                    text, time_parts, parsed_result
                )
                result["temporal_data"] = parsed_result
                result["confidence"] = (
                    0.8 if parsed_result.get("reminder_time") else 0.7
                )

        return result

    def _extract_timezone(self, text: str) -> Optional[Dict[str, str]]:
        """Extract timezone information from text."""
        # Direct timezone mentions (CST, PST, EST, etc.)
        tz_pattern = r"\b(CST|CDT|PST|PDT|EST|EDT|MST|MDT)\b"
        tz_match = re.search(tz_pattern, text, re.IGNORECASE)

        if tz_match:
            return {
                "timezone": tz_match.group(1).upper(),
                "cleaned_text": re.sub(
                    tz_pattern, "", text, flags=re.IGNORECASE
                ).strip(),
            }

        # City-based timezone
        for city, tz in self.city_to_tz.items():
            city_pattern = rf"\b{city}\s+time\b"
            if re.search(city_pattern, text, re.IGNORECASE):
                return {
                    "timezone": tz,
                    "cleaned_text": re.sub(
                        city_pattern, "", text, flags=re.IGNORECASE
                    ).strip(),
                }

        return None

    def _extract_time_parts(self, text: str) -> Dict[str, Optional[str]]:
        """Extract date and time parts from text."""
        # Common patterns for dates and times
        date_patterns = [
            r"tomorrow",
            r"today",
            r"yesterday",
            r"next \w+",
            r"this \w+",
            r"on \w+",
            r"\d{1,2}/\d{1,2}",
            r"\w+ \d{1,2}(?:st|nd|rd|th)?",
        ]

        time_patterns = [
            r"at \d{1,2}(?::\d{2})?\s*(?:am|pm)?",
            r"\d{1,2}(?::\d{2})?\s*(?:am|pm)",
            r"(?:before|after) \w+",
            r"\d{1,2}\s*(?:hours?|minutes?)\s*(?:before|after|from now)",
        ]

        # Reminder patterns
        reminder_patterns = [
            r"remind\s+\w+\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+reminder",
            r"remind.*?(\d+)\s*minutes?\s*before",
        ]

        result = {
            "date_part": None,
            "time_part": None,
            "reminder_part": None,
            "task_part": text,
        }

        # Extract date
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["date_part"] = match.group(0)
                break

        # Extract time
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["time_part"] = match.group(0)
                break

        # Extract reminder time if different
        for pattern in reminder_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["reminder_part"] = (
                    match.group(1) if match.groups() else match.group(0)
                )
                break

        return result

    def _parse_with_dateparser(
        self,
        time_parts: Dict[str, Optional[str]],
        reference_time: datetime,
        timezone: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Parse extracted time parts using dateparser."""
        settings = {
            "TIMEZONE": self.default_timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": reference_time,
        }

        result = {}

        # Parse main date/time
        datetime_str = " ".join(
            filter(None, [time_parts["date_part"], time_parts["time_part"]])
        )
        if datetime_str:
            parsed_dt = dateparser.parse(datetime_str, settings=settings)
            if parsed_dt:
                result["due_date"] = parsed_dt.strftime("%Y-%m-%d")
                if time_parts["time_part"]:
                    result["due_time"] = parsed_dt.strftime("%H:%M")

        # Parse reminder if present
        if time_parts["reminder_part"]:
            # Check if it's a "X minutes before" pattern
            before_match = re.search(
                r"(\d+)\s*minutes?\s*before", time_parts["reminder_part"]
            )
            if before_match and "due_time" in result:
                minutes = int(before_match.group(1))
                reminder_dt = parsed_dt - timedelta(minutes=minutes)
                result["reminder_date"] = reminder_dt.strftime("%Y-%m-%d")
                result["reminder_time"] = reminder_dt.strftime("%H:%M")
            else:
                # Parse as absolute time
                reminder_dt = dateparser.parse(
                    time_parts["reminder_part"], settings=settings
                )
                if reminder_dt:
                    result["reminder_time"] = reminder_dt.strftime("%H:%M")
                    result["reminder_date"] = result.get(
                        "due_date", reminder_dt.strftime("%Y-%m-%d")
                    )

        # If no separate reminder, copy due time
        if "due_time" in result and "reminder_time" not in result:
            result["reminder_time"] = result["due_time"]
            result["reminder_date"] = result["due_date"]

        if timezone:
            result["timezone_context"] = timezone

        return result if result else None

    def _build_processed_text(
        self,
        original: str,
        time_parts: Dict[str, Optional[str]],
        temporal_data: Dict[str, Any],
    ) -> str:
        """Build processed text with temporal expressions replaced."""
        processed = original

        # Build replacement string
        replacements = []
        if "due_date" in temporal_data:
            replacements.append(f"on {temporal_data['due_date']}")
        if "due_time" in temporal_data:
            replacements.append(f"at {temporal_data['due_time']}")

        if replacements:
            # Remove original temporal expressions
            for part in [time_parts["date_part"], time_parts["time_part"]]:
                if part:
                    processed = processed.replace(part, "").strip()

            # Add structured temporal data
            processed += f" [{' '.join(replacements)}]"

        return processed

    # Custom handlers for specific patterns
    def _handle_end_of_hour(
        self, text: str, reference_time: datetime
    ) -> Dict[str, Any]:
        """Handle 'end of the hour' expressions."""
        next_hour = reference_time.replace(minute=59, second=0, microsecond=0)
        if next_hour <= reference_time:
            next_hour += timedelta(hours=1)

        return {
            "processed_text": re.sub(
                r"end of (?:the )?hour",
                f"at {next_hour.strftime('%H:59')}",
                text,
                flags=re.IGNORECASE,
            ),
            "temporal_data": {
                "due_date": next_hour.strftime("%Y-%m-%d"),
                "due_time": next_hour.strftime("%H:%M"),
                "reminder_date": next_hour.strftime("%Y-%m-%d"),
                "reminder_time": next_hour.strftime("%H:%M"),
            },
        }

    def _handle_top_of_hour(
        self, text: str, reference_time: datetime
    ) -> Dict[str, Any]:
        """Handle 'top of the hour' expressions."""
        next_hour = reference_time.replace(minute=0, second=0, microsecond=0)
        if next_hour <= reference_time:
            next_hour += timedelta(hours=1)

        return {
            "processed_text": re.sub(
                r"top of (?:the )?hour",
                f"at {next_hour.strftime('%H:00')}",
                text,
                flags=re.IGNORECASE,
            ),
            "temporal_data": {
                "due_date": next_hour.strftime("%Y-%m-%d"),
                "due_time": next_hour.strftime("%H:%M"),
                "reminder_date": next_hour.strftime("%Y-%m-%d"),
                "reminder_time": next_hour.strftime("%H:%M"),
            },
        }

    def _handle_end_of_day(self, text: str, reference_time: datetime) -> Dict[str, Any]:
        """Handle 'end of day' expressions."""
        end_of_day = reference_time.replace(hour=23, minute=59, second=0, microsecond=0)

        return {
            "processed_text": re.sub(
                r"end of (?:the )?day", "at 23:59", text, flags=re.IGNORECASE
            ),
            "temporal_data": {
                "due_date": end_of_day.strftime("%Y-%m-%d"),
                "due_time": "23:59",
                "reminder_date": end_of_day.strftime("%Y-%m-%d"),
                "reminder_time": "23:59",
            },
        }

    def _handle_end_of_tonight(
        self, text: str, reference_time: datetime
    ) -> Dict[str, Any]:
        """Handle 'end of tonight' expressions."""
        # Same as end of day
        return self._handle_end_of_day(text.replace("tonight", "day"), reference_time)

    def _handle_weekend(self, text: str, reference_time: datetime) -> Dict[str, Any]:
        """Handle 'weekend' expressions."""
        # Find next Saturday
        days_until_saturday = (5 - reference_time.weekday()) % 7
        if days_until_saturday == 0:  # Today is Saturday
            if reference_time.hour >= 12:  # After noon, use Sunday
                next_weekend = reference_time + timedelta(days=1)
            else:
                next_weekend = reference_time
        else:
            next_weekend = reference_time + timedelta(days=days_until_saturday)

        next_weekend = next_weekend.replace(hour=9, minute=0, second=0, microsecond=0)

        return {
            "processed_text": re.sub(
                r"(?:this )?weekend",
                f"on {next_weekend.strftime('%Y-%m-%d')}",
                text,
                flags=re.IGNORECASE,
            ),
            "temporal_data": {
                "due_date": next_weekend.strftime("%Y-%m-%d"),
                "reminder_date": next_weekend.strftime("%Y-%m-%d"),
            },
        }
