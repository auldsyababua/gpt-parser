#!/usr/bin/env python3
"""
Tests for the temporal processor module.
"""

import unittest
from datetime import datetime
import pytz
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.temporal_processor import TemporalProcessor


class TestTemporalProcessor(unittest.TestCase):
    """Test cases for temporal expression preprocessing."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = TemporalProcessor(default_timezone="America/Los_Angeles")
        # Fixed reference time for consistent testing
        self.reference_time = datetime(
            2025, 7, 10, 14, 30, 0, tzinfo=pytz.timezone("America/Los_Angeles")
        )

    def test_simple_tomorrow(self):
        """Test parsing 'tomorrow' expressions."""
        result = self.processor.preprocess(
            "Remind Joel tomorrow at 3pm to check batteries", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertEqual(result["temporal_data"]["due_date"], "2025-07-11")
        self.assertEqual(result["temporal_data"]["due_time"], "15:00")
        self.assertEqual(result["temporal_data"]["reminder_time"], "15:00")

    def test_explicit_timezone(self):
        """Test parsing with explicit timezone."""
        result = self.processor.preprocess(
            "Tell Bryan at 2PM CST tomorrow to restart servers", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertEqual(result["temporal_data"]["timezone_context"], "CST")
        self.assertEqual(result["temporal_data"]["due_time"], "14:00")

    def test_city_timezone(self):
        """Test parsing with city-based timezone."""
        result = self.processor.preprocess(
            "at 2pm Houston time, remind Joel to check the generators",
            self.reference_time,
        )

        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertEqual(result["temporal_data"]["timezone_context"], "CST")

    def test_end_of_hour(self):
        """Test 'end of the hour' expression."""
        result = self.processor.preprocess(
            "Check telemetry at end of the hour", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.9)
        self.assertEqual(
            result["temporal_data"]["due_time"], "14:59"
        )  # Next hour minus 1 minute

    def test_top_of_hour(self):
        """Test 'top of the hour' expression."""
        result = self.processor.preprocess(
            "Meeting at top of the hour", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.9)
        self.assertEqual(result["temporal_data"]["due_time"], "15:00")  # Next hour

    def test_end_of_day(self):
        """Test 'end of day' expression."""
        result = self.processor.preprocess(
            "Submit report by end of day", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.9)
        self.assertEqual(result["temporal_data"]["due_time"], "23:59")

    def test_weekend(self):
        """Test 'weekend' expression."""
        # Reference time is Thursday
        result = self.processor.preprocess(
            "Do maintenance this weekend", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.9)
        self.assertEqual(result["temporal_data"]["due_date"], "2025-07-12")  # Saturday

    def test_reminder_before(self):
        """Test 'X minutes before' pattern."""
        result = self.processor.preprocess(
            "Remind Joel 30 minutes before the 4pm meeting", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertEqual(result["temporal_data"]["due_time"], "16:00")
        self.assertEqual(result["temporal_data"]["reminder_time"], "15:30")

    def test_no_temporal_expression(self):
        """Test input without temporal expressions."""
        result = self.processor.preprocess(
            "Check the generator oil levels", self.reference_time
        )

        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["temporal_data"], {})

    def test_complex_expression(self):
        """Test complex temporal expression."""
        result = self.processor.preprocess(
            "Next Monday at 9am EST, remind Bryan to call the contractor",
            self.reference_time,
        )

        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertEqual(result["temporal_data"]["timezone_context"], "EST")
        self.assertEqual(result["temporal_data"]["due_time"], "09:00")
        # Next Monday from Thursday
        self.assertEqual(result["temporal_data"]["due_date"], "2025-07-14")

    def test_today_expression(self):
        """Test 'today' expression."""
        result = self.processor.preprocess(
            "Finish the task today at 5pm", self.reference_time
        )

        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertEqual(result["temporal_data"]["due_date"], "2025-07-10")
        self.assertEqual(result["temporal_data"]["due_time"], "17:00")

    def test_relative_hours(self):
        """Test 'in X hours' expression."""
        result = self.processor.preprocess("Call Joel in 2 hours", self.reference_time)

        self.assertGreaterEqual(result["confidence"], 0.7)
        # 14:30 + 2 hours = 16:30
        self.assertEqual(result["temporal_data"]["due_time"], "16:30")

    def test_processed_text_format(self):
        """Test that processed text is properly formatted."""
        result = self.processor.preprocess(
            "Remind Joel tomorrow at 3pm to check batteries", self.reference_time
        )

        # Should contain the task with temporal parts replaced
        self.assertIn("check batteries", result["processed_text"])
        self.assertIn("[on 2025-07-11 at 15:00]", result["processed_text"])


class TestPerformance(unittest.TestCase):
    """Test performance improvements."""

    def setUp(self):
        """Set up performance tests."""
        self.processor = TemporalProcessor()

    def test_preprocessing_speed(self):
        """Test that preprocessing is fast."""
        import time

        test_cases = [
            "Remind Joel tomorrow at 3pm to check batteries",
            "Tell Bryan at 2PM CST to restart servers",
            "Check telemetry at end of the hour",
            "Submit report by end of day",
        ]

        for text in test_cases:
            start = time.time()
            result = self.processor.preprocess(text)
            elapsed = time.time() - start

            # Should be very fast (under 50ms)
            self.assertLess(
                elapsed, 0.05, f"Preprocessing '{text}' took {elapsed:.3f}s"
            )


if __name__ == "__main__":
    unittest.main()
