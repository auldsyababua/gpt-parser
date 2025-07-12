function doPost(e) {
  var sheetId = '1MRsFeMM513pG0r-HZy6lzpsVzoqQaiukqH5YqkyaJtA';
  var sheetName = 'tasks';

  var sheet = SpreadsheetApp.openById(sheetId).getSheetByName(sheetName);

  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({ error: "Sheet not found" }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  var data = JSON.parse(e.postData.contents);

  // Define the order of columns in your Google Sheet, matching the exact text of your headers
  // The values in the 'data' object will be mapped to these columns.
  var headers = [
    "original_prompt",     // Maps to "Original Prompt"
    "corrections_history", // Maps to "Corrections and responses (if applicable)"
    "task",                // Maps to "Task Title"
    "assignee",            // Maps to "Assignee"
    "assigner",            // Maps to "Assigner"
    "due_date",            // Maps to "Due Date (UTC, format: YYYY-MM-DD)"
    "due_time",            // Maps to "Due Time (UTC, format: HH:MM)"
    "reminder_date",       // Maps to "Reminder Date (UTC, format: YYYY-MM-DD)"
    "reminder_time",       // Maps to "Reminder Time (UTC, format: HH:MM)"
    "status",              // Maps to "Status"
    "site",                // Maps to "Site (optional)"
    "created_at",          // Maps to "Created At (UTC, format: YYYY-MM-DDTHH:MM)"
    "repeat_interval",     // Maps to "Repeat Interval"
    "timezone_context",    // Maps to "Timezone Context"
    "reasoning"            // Maps to "Reasoning"
  ];

  var row = [];
  headers.forEach(function(header) {
    row.push(data[header] || ""); // Add value from JSON or empty string if not present
  });

  sheet.appendRow(row);

  return ContentService.createTextOutput(JSON.stringify({ message: "Task added successfully" }))
    .setMimeType(ContentService.MimeType.JSON);
}