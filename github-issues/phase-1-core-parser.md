# Phase 1: Core Parser Foundation

## Overview
This phase focuses on building a reliable natural language task parser that can handle common use cases with high accuracy.

## Status: IN PROGRESS

### ✅ Completed Features
1. **Basic Task Parsing**
   - Natural language input → structured JSON output
   - Extracts: assignee, task description, due date/time
   - Status: COMPLETE

2. **Telegram Bot Integration**
   - Bot receives messages and sends to parser
   - Returns confirmation to user
   - Status: COMPLETE

3. **Google Sheets Storage**
   - Parsed tasks sent to Google Sheets via Apps Script
   - Status: COMPLETE

4. **User Confirmation Flow**
   - Shows human-readable task summary
   - Allows confirmation, cancellation, or clarification
   - Status: COMPLETE

5. **Virtual Environment Setup**
   - Fixed bot crashes due to missing dependencies
   - Proper venv configuration
   - Status: COMPLETE

### 🚧 In Progress Features

1. **Temporal Expression Normalization** (Critical Bug)
   - Issue: Inconsistent parsing of time expressions
   - Examples that fail: "end of the hour", "top of the hour"
   - Examples that work: "end of tonight", "tomorrow at 3pm"
   - Solution: Build pre-processor to normalize expressions before LLM
   - Files: Create `temporal_processor.py`
   - Reference: [Temporal Expression Consistency.md](./Temporal%20Expression%20Consistency.md)

### 📋 Remaining Features

1. **Task Perspective Normalization**
   - Issue: Tasks written from assigner perspective ("Tell Bryan to...")
   - Goal: Transform to assignee perspective ("Check generator oil")
   - Approach: Post-processing layer for pronoun replacement
   - Files: Create `perspective_normalizer.py`

2. **Improved Clarification Handling**
   - Issue: Current approach appends clarifications which confuses LLM
   - Solution: Structured prompt showing original parsing and correction separately
   - Example: "Original: {task}, User correction: {clarification}"
   - Files: Update `telegram_bot.py` clarification flow

3. **Better Parsing Options**
   - Replace free-form text with structured options
   - Implement enums for: repeat_interval, priority, status
   - Pre-validate LLM outputs against allowed values
   - Files: Update `task_schema.json` and prompts

4. **Comprehensive Test Suite**
   - Expand from current test inputs to 50+ cases
   - Cover edge cases for temporal expressions
   - Test perspective normalization
   - Add automated test runner
   - Files: Enhance `tests/` directory

5. **Error Handling & Retry Logic**
   - Graceful handling of API failures
   - Retry with exponential backoff
   - Better error messages for users
   - Files: Update `assistants_api_runner.py`

6. **Schema Validation**
   - Ensure all parsed tasks match schema
   - Reject invalid outputs before confirmation
   - Files: Enhance `task_schema.json` usage

## Technical Debt
- [ ] Add logging to all components
- [ ] Create development vs production configs
- [ ] Document API error codes
- [ ] Add rate limiting for API calls

## Success Metrics
- [ ] 90% accuracy on 50-test suite
- [ ] All temporal expressions from test set parse correctly
- [ ] Tasks consistently written from assignee perspective
- [ ] Zero crashes in 24-hour operation
- [ ] Average parsing time < 3 seconds

## Next Steps
1. Fix temporal expression parsing (highest priority)
2. Implement perspective normalization
3. Expand test suite
4. Add comprehensive error handling

## Dependencies for Phase 2
Before moving to Phase 2, we must have:
- Reliable temporal parsing
- Consistent perspective normalization
- 90%+ test accuracy
- Stable error handling