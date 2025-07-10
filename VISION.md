# FLRTS Vision: Field Reports, Lists, Reminders, Tasks & Subtasks

## The Dream

FLRTS is an integrated operational management system designed specifically for distributed teams managing off-grid bitcoin mining and sustainable energy operations. It transforms how field technicians and managers coordinate work through natural language interfaces and intelligent automation.

## Current State: gpt-parser

The `gpt-parser` project is the foundational building block - a natural language task parser that converts conversational input into structured data. This MVP proves the core concept: field workers can create tasks using natural language, and the system intelligently extracts structured information.

## The Full Vision

### Core Philosophy
- **Low-friction data entry**: Field technicians should spend time doing work, not filling out forms
- **Natural language first**: Speak or type naturally, let the system handle structure
- **Single source of truth**: All operational data lives in one place
- **Intelligent automation**: The system should understand context and reduce manual work

### Key Capabilities

1. **Natural Language Task Management**
   - Create tasks via voice or text: "Tell Bryan to check generator oil tomorrow at 3pm"
   - Multi-step task parsing with dependencies
   - Automatic assignment based on expertise and availability
   - Context-aware reminders and follow-ups

2. **Field Reporting**
   - Voice-to-text field reports from technicians
   - Automatic categorization and tagging
   - Photo/video attachment with AI-powered descriptions
   - Incident tracking and resolution workflows

3. **Intelligent Lists & Inventory**
   - Dynamic equipment checklists
   - Parts inventory tracking across sites
   - Automated reorder triggers
   - Maintenance schedule generation

4. **Financial Integration**
   - Automated markup calculations on vendor invoices
   - Partner reporting and profit sharing
   - Expense tracking by site and project
   - Real-time financial dashboards

5. **Multi-Channel Interface**
   - Telegram bot for field workers (voice + text)
   - Web dashboard for managers
   - API for external integrations
   - Email/SMS notifications

### Target Users

1. **Field Technicians** (Bryan, Joel)
   - Need quick, hands-free task logging
   - Work in remote locations with limited connectivity
   - Focus on doing work, not documentation

2. **Operations Managers** (Colin)
   - Need real-time visibility into field operations
   - Coordinate multiple technicians and sites
   - Require financial and operational reporting

3. **Partners & Stakeholders**
   - Need automated reporting
   - Require financial transparency
   - Want operational metrics

## Evolution Path

### Phase 1: Core Parser (Current)
- Natural language → structured JSON
- Basic task parsing with assignee, dates, reminders
- Telegram bot interface
- Google Sheets storage

### Phase 2: Enhanced Parsing & Data
- Temporal expression normalization
- Timezone-aware processing
- Database backend (PostgreSQL)
- Task perspective normalization

### Phase 3: Field Operations
- Voice input support
- Field report parsing
- Photo/video attachments
- Offline capability with sync

### Phase 4: Web Interface
- Manager dashboard
- Task querying and filtering
- Report generation
- User management

### Phase 5: Intelligence & Integration
- Predictive task assignment
- Automated scheduling optimization
- External API integrations (Todoist, Google Drive)
- Advanced NLP with context awareness

### Phase 6: Financial & Analytics
- Invoice processing and markup
- Financial reporting
- Predictive maintenance
- Performance analytics

## Success Metrics

1. **Efficiency**: 80% reduction in time spent on data entry
2. **Adoption**: 95% of tasks created via natural language
3. **Accuracy**: <5% task parsing errors
4. **Visibility**: Real-time operational dashboard
5. **Financial**: Automated calculation of all markups and profit sharing

## Technical Principles

1. **Start simple, iterate fast**: Each phase must deliver working value
2. **Parser first**: Natural language processing is the core differentiator
3. **API-driven**: Every feature should be accessible via API
4. **Mobile-first**: Field workers are the primary users
5. **Offline-capable**: Must work in remote locations

## Why This Matters

Managing distributed field operations is inherently complex. Current solutions require extensive manual data entry, leading to incomplete records, delayed reporting, and operational blind spots. FLRTS changes this by meeting workers where they are - allowing natural communication that's automatically transformed into structured, actionable data.

The end result: operators spend more time operating and less time reporting, while managers get better visibility than ever before.