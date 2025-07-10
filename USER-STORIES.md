# FLRTS User Stories

## Field Technician Stories (Bryan, Joel)

### Task Management
- [x] **As Bryan**, I want to create tasks using text commands in Telegram, so I can quickly log work that needs to be done.
- [x] **As a field tech**, I want to see a confirmation of my task before it's saved, so I can correct any parsing errors.
- [ ] **As Bryan**, I want to create tasks using voice commands while my hands are dirty, so I don't have to stop working to document what needs to be done.
- [ ] **As Joel**, I want to report task completion by saying "done with the generator service at Site A", so I can quickly move to the next job.
- [ ] **As a field tech**, I want to get reminders on my phone about upcoming tasks, so I don't forget time-sensitive maintenance.
- [ ] **As a field tech**, I want to query my tasks for the day by asking "what do I need to do today?", so I can plan my route efficiently.

### Field Reporting
- **As Bryan**, I want to dictate field reports while walking through a site, so I can capture observations in real-time.
- **As Joel**, I want to attach photos to my reports by taking a picture and saying what it shows, so I can document issues visually.
- **As a field tech**, I want to report equipment issues in natural language like "Generator 2 is making a weird knocking sound", so problems get logged immediately.
- **As a field tech**, I want to access previous reports about a site before I arrive, so I know what issues to look for.

### Lists & Inventory
- **As Bryan**, I want to check off maintenance items by voice as I complete them, so I can track progress hands-free.
- **As Joel**, I want to add items to the parts order list when I notice we're running low, so we never run out of critical supplies.
- **As a field tech**, I want to know what tools and parts are at each site before I drive there, so I can bring what's missing.

### Communication
- [x] **As a field tech**, I want to send task requests via Telegram, so I can communicate without phone calls.
- [x] **As Bryan**, I want to clarify task details if the parsing is wrong, so tasks are accurate.
- [ ] **As a field tech**, I want to send updates to Colin without calling him, so I can communicate efficiently while working.
- [ ] **As Bryan**, I want to get clarification on tasks by asking follow-up questions in the chat, so I understand exactly what needs to be done.

## Operations Manager Stories (Colin)

### Task Assignment & Monitoring
- [x] **As Colin**, I want to create tasks in natural language like "Tell Bryan to check the generator tomorrow at 3pm", so I can quickly delegate work.
- [x] **As Colin**, I want tasks to be automatically parsed into structured data, so they're stored consistently.
- [x] **As Colin**, I want to confirm task details before they're saved, so I can ensure accuracy.
- [ ] **As Colin**, I want to assign tasks to technicians based on their location and skills, so work gets done efficiently.
- [ ] **As Colin**, I want to see all open tasks across all sites on a dashboard, so I can track operational status.
- [ ] **As Colin**, I want to get alerts when high-priority tasks are overdue, so I can follow up immediately.
- [ ] **As Colin**, I want to reassign tasks between technicians easily, so I can handle scheduling changes.

### Reporting & Analytics
- **As Colin**, I want to generate weekly reports showing completed tasks by technician and site, so I can track productivity.
- **As Colin**, I want to see patterns in equipment failures, so I can plan preventive maintenance.
- **As Colin**, I want to track time between task creation and completion, so I can identify bottlenecks.
- **As Colin**, I want to export task data for specific date ranges, so I can analyze trends.

### Financial Management
- [x] **As Colin**, I want tasks stored in Google Sheets, so I can access them from anywhere.
- [ ] **As Colin**, I want to see costs associated with each task (parts, labor, travel), so I can track profitability by site.
- [ ] **As Colin**, I want to automatically calculate markup on vendor invoices, so billing is consistent.
- [ ] **As Colin**, I want to generate partner reports showing revenue and costs by site, so profit sharing is transparent.

### Team Coordination
- **As Colin**, I want to broadcast announcements to all technicians, so everyone gets important updates.
- **As Colin**, I want to see which technician is at which site in real-time, so I can coordinate responses to urgent issues.
- **As Colin**, I want to create recurring tasks that automatically assign to available technicians, so routine maintenance doesn't get missed.

## Partner & Stakeholder Stories

### Visibility & Reporting
- **As a partner**, I want to receive monthly automated reports about my sites' performance, so I can track my investment.
- **As a stakeholder**, I want to access a web portal showing real-time operational metrics, so I can monitor performance.
- **As a partner**, I want to see financial breakdowns including revenue, costs, and profit share, so I understand my returns.

### Notifications
- **As a site owner**, I want to get alerts about critical issues at my sites, so I can be informed of problems.
- **As a partner**, I want to receive summaries of completed maintenance, so I know my equipment is being cared for.

## System Administrator Stories

### Configuration & Setup
- **As an admin**, I want to easily add new sites and equipment to the system, so we can scale operations.
- **As an admin**, I want to configure which technicians can access which sites, so security is maintained.
- **As an admin**, I want to set up automated task templates for routine maintenance, so nothing gets forgotten.

### Integration & API
- **As an admin**, I want to connect FLRTS to our existing tools (Google Workspace, Todoist), so data flows seamlessly.
- **As an admin**, I want to set up webhook notifications for external systems, so other tools can react to FLRTS events.
- **As an admin**, I want to backup and restore system data, so we're protected against data loss.

## Future User Stories

### Advanced AI Features
- **As a field tech**, I want the system to predict what parts I'll need based on the task description, so I can prepare better.
- **As Colin**, I want AI to suggest optimal task scheduling based on technician location and skills, so routing is efficient.
- **As a field tech**, I want to ask the system questions like "when was the last oil change on Generator 2?", so I have context for my work.

### Offline Capabilities
- **As a field tech**, I want to create tasks and reports while offline that sync when I get connection, so remote sites don't stop my workflow.
- **As Joel**, I want to access site documentation offline, so I can reference manuals and procedures without internet.

### Voice Assistant Integration
- **As Bryan**, I want to use voice commands through my truck's Bluetooth to create tasks while driving between sites.
- **As a field tech**, I want to get task reminders through my smartwatch, so I'm notified even when my phone is away.