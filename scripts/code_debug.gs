function doPost(e) {
  var sheetId = '1MRsFeMM513pG0r-HZy6lzpsVzoqQaiukqH5YqkyaJtA';
  var sheetName = 'tasks';

  var sheet = SpreadsheetApp.openById(sheetId).getSheetByName(sheetName);

  if (!sheet) {
    return ContentService.createTextOutput(JSON.stringify({ error: "Sheet not found" }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  var data = JSON.parse(e.postData.contents);
  
  // DEBUG: Log the received data
  console.log('Received data:', JSON.stringify(data, null, 2));

  // Define the order of columns in your Google Sheet
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
  
  // DEBUG: Build row with logging
  headers.forEach(function(header) {
    var value = data[header] || "";
    console.log('Header:', header, 'Value:', value);
    row.push(value);
  });
  
  // DEBUG: Log the complete row
  console.log('Complete row:', JSON.stringify(row));

  // Add a debug row first to see column alignment
  var debugRow = [];
  for (var i = 0; i < headers.length; i++) {
    debugRow.push('COL' + (i+1) + ':' + headers[i]);
  }
  sheet.appendRow(debugRow);
  
  // Then add the actual data
  sheet.appendRow(row);

  return ContentService.createTextOutput(JSON.stringify({ 
    message: "Task added successfully",
    debug: {
      receivedData: data,
      rowData: row
    }
  }))
    .setMimeType(ContentService.MimeType.JSON);
}