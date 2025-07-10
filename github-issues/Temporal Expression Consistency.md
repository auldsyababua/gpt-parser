### 🕐 Bug: Inconsistent Temporal Expression Parsing

**Priority:** High

**Issue:**
LLM inconsistently parses similar temporal expressions, leading to unpredictable time interpretations.

---

### 🐛 Observed Behavior

**Case 1:** ✅ Successful parsing
```
Input: "have claude fix the bot by the end of tonight so it stops crashing"
Time: 6:35 PM
Parsed: 23:59 (correct - end of day)
```

**Case 2:** ❌ Failed parsing
```
Input: "have claude fix the bot by the end of the hour so it stops crashing"
Time: 6:18 PM
Parsed: xx:xx (failed - should be 18:59)
```

---

### 🔍 Root Cause Analysis

1. **Training Data Frequency**
   - "end of tonight/day" → Common phrase, well-represented
   - "end of the hour" → Rare phrase, poorly represented

2. **Context Requirements**
   - Hour-based expressions need current time context
   - Day-based expressions are more absolute

3. **LLM Non-determinism**
   - Same input can yield different outputs
   - No guaranteed consistency without constraints

---

### 💡 Proposed Fix

**Short-term (Immediate):**

1. **Add Pre-processing Rules**
   ```python
   temporal_mappings = {
       r"end of (?:the )?hour": lambda t: f"{t.hour}:59",
       r"end of (?:the )?day": "23:59",
       r"end of tonight": "23:59",
       r"top of (?:the )?hour": lambda t: f"{(t.hour + 1) % 24}:00"
   }
   ```

2. **Include Current Time in Prompt**
   ```
   System: Current time is 18:35 PDT.
   When user says "end of the hour", interpret as 18:59.
   ```

**Long-term (Robust):**

1. **Two-Stage Processing**
   - Stage 1: LLM extracts temporal intent
   - Stage 2: Rule engine applies consistent mappings

2. **Confidence-Based Routing**
   ```json
   {
     "temporal_expression": "end of the hour",
     "confidence": 0.4,
     "action": "apply_rule_engine"
   }
   ```

3. **Test Suite for Edge Cases**
   - "in 5" → 5 minutes? 5 hours?
   - "later" → How much later?
   - "soon" → Define threshold

---

### 📝 Implementation Checklist

- [ ] Create temporal expression test cases
- [ ] Implement pre-processing rule engine
- [ ] Add current time to all LLM prompts
- [ ] Build confidence scoring for time parsing
- [ ] Add fallback prompts for ambiguous times
- [ ] Create user preference settings (e.g., "morning" = 8am vs 9am)

---

### 🎯 Success Criteria

- 95% consistent parsing for common expressions
- Clear handling of ambiguous cases
- User-configurable defaults for subjective times
- Comprehensive test coverage for edge cases