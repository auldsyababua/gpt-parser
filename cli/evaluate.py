import json
from dateutil.parser import parse

# === Load test inputs from file ===
# Each input is prefixed with "### INPUT" and separated by that tag.
with open("tests/inputs.txt", "r") as f:
    test_inputs = f.read().split("### INPUT")[1:]
    test_inputs = ["### INPUT" + i.strip() for i in test_inputs if i.strip()]

# === Load expected outputs from the few-shot examples file ===
# Each output follows an "### OUTPUT" tag inside a single example block.
with open("prompts/few_shot_examples.txt", "r") as f:
    expected_outputs = f.read().split("### INPUT")[1:]
    expected_outputs = [
        i.split("### OUTPUT")[1].strip() for i in expected_outputs if "### OUTPUT" in i
    ]

# === Sanity check ===
assert len(test_inputs) == len(
    expected_outputs
), "Mismatch between test inputs and expected outputs."


# === Function: validate_fields ===
# Compares actual and expected task objects on a fixed set of fields.
# Returns False and a reason if any field is missing or mismatched.
def validate_fields(expected, actual, fields):
    for field in fields:
        if field in expected:
            if field not in actual:
                return False, f"Missing field: {field}"
            if expected[field] != actual[field]:
                return (
                    False,
                    f"Field mismatch for '{field}': expected {expected[field]} but got {actual[field]}",
                )
    return True, ""


# === Function: normalize_datetime ===
# Ensures date-like fields (due_date, reminder_date) are in YYYY-MM-DD format.
# Leaves created_at untouched, assumes it's already ISO 8601.
def normalize_datetime(obj):
    for key in ["due_date", "reminder_date", "created_at"]:
        if key in obj:
            try:
                obj[key] = str(parse(obj[key]).date()) if "date" in key else obj[key]
            except Exception:
                pass  # Fallback: leave it unchanged if it can't parse
    return obj


# === Main Evaluation Loop ===
# For each input:
#  - Load the actual output (from tests/generated_output_N.json)
#  - Normalize dates
#  - Apply default logic (e.g., reminder = due if missing)
#  - Validate the fields
results = []
for i, (input_text, expected_json) in enumerate(zip(test_inputs, expected_outputs)):
    print(f"\nTest {i+1}: {input_text.splitlines()[0].replace('Text:', '').strip()}")
    try:
        expected = json.loads(expected_json)
        with open(f"tests/generated_output_{i+1}.json", "r") as f:
            actual = json.load(f)

        expected = normalize_datetime(expected)
        actual = normalize_datetime(actual)

        # === Fallback logic if reminder fields are missing ===
        if "due_time" in actual and "reminder_time" not in actual:
            actual["reminder_time"] = actual["due_time"]
        if "due_date" in actual and "reminder_date" not in actual:
            actual["reminder_date"] = actual["due_date"]

        # === Validate all fields including new reminder fields ===
        fields_to_check = [
            "assignee",
            "assigner",
            "task",
            "due_date",
            "due_time",
            "reminder_date",
            "reminder_time",
            "status",
            "created_at",
        ]
        ok, message = validate_fields(expected, actual, fields_to_check)

        if not ok:
            print(f"❌ {message}")
        else:
            print("✅ Pass")

    except Exception as e:
        print(f"❌ Error: {e}")
