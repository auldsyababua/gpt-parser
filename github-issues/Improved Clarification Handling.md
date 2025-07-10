### 🔄 Enhancement: Improved Task Clarification Handling

**Goal:**
Improve how the system handles user clarifications when they reject or want to modify a parsed task.

---

### 🐛 Current Issue

When users provide clarification, the system simply appends:
```python
combined_message = f"{original}. User clarification: {update.message.text}"
```

This can confuse the LLM, especially when the clarification contradicts the original parsing.

**Example Problem:**
- Original: "at 4pm CST tomorrow, remind Joel to check the oil cans"
- Bot parses: Due at 00:00 (incorrect)
- User clarifies: "4pm CST would be 16:00 Joel's time"
- Combined: "at 4pm CST tomorrow, remind Joel to check the oil cans. User clarification: 4pm CST would be 16:00 Joel's time"
- LLM gets confused about what to fix

---

### ✅ Proposed Solution

1. **Structured Clarification Prompt**
   ```python
   clarification_prompt = f"""
   Original request: {original}
   
   Previous parsing result:
   - Task: {parsed_json.get('task')}
   - Due time: {parsed_json.get('due_time')} 
   - Reminder time: {parsed_json.get('reminder_time')}
   
   User correction: {update.message.text}
   
   Please re-parse the task incorporating the user's correction.
   """
   ```

2. **Add Clarification Examples to Few-Shot**
   ```
   ### INPUT
   Original request: at 4pm CST tomorrow, remind Joel to check oil
   Previous parsing result:
   - Due time: 00:00
   User correction: I said 4pm CST, not midnight
   
   ### OUTPUT
   {
     "assignee": "Joel",
     "task": "Check oil",
     "due_time": "16:00",
     ...
   }
   ```

3. **Common Clarification Patterns**
   - Time corrections: "I said X time, not Y time"
   - Date corrections: "tomorrow, not today"
   - Assignee corrections: "Joel, not Bryan"
   - Task detail additions: "at Site A"

---

### 🔧 Implementation

1. Update `handle_confirmation()` to structure clarifications better
2. Add few-shot examples for common clarification patterns
3. Consider showing what the bot understood vs what user meant
4. Track clarification success rate for continuous improvement

---

### 📊 Benefits

- More accurate re-parsing after clarifications
- Less user frustration with multiple rounds
- Better learning data for future improvements
- Clearer communication of what went wrong