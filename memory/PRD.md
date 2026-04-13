# PM Research Lab - Cognitive Offloading Research Tool

## Original Problem Statement
Build a computational proof-of-concept tool to simulate and analyze the impact of automated digital notifications on prospective memory (PM) and cognitive offloading. The tool investigates how notification frequency, timing, and visual structure influence users' reliance on digital systems for remembering future intentions (multi-dose vaccination context).

## User Personas
1. **Study Participants** - Experience simulated medication reminders, make offloading choices, respond to recall probes
2. **Cognitive Science Researchers** - Configure experiments, analyze offloading behavior, export thesis data
3. **Thesis Advisors/Reviewers** - Review weekly reports and progress documentation

## Architecture

### Two Interfaces
1. **Participant Interface** (Public - `/`, `/participate/*`, `/study/:shareCode`)
   - Landing page with study overview
   - Direct study join via shareable links (`/study/JIT2026A`)
   - Informed consent form
   - Demographics collection (validated, saved to DB)
   - Simulation with offloading choice mechanism

2. **Researcher Interface** (Protected - `/researcher/*`)
   - Password: `pmresearch2026`
   - Dashboard with offloading comparison charts
   - Experiment configuration (4 strategies) with shareable links
   - Analytics with thesis data export (CSV, JSON, Validated JSON, PDF)
   - Progress tracker & weekly reports

### Backend (FastAPI + MongoDB)
- Full CRUD for experiments, sessions, participants
- Offloading event tracking
- Response time measurement
- Analytics endpoints for thesis analysis
- PDF report generation (ReportLab)
- Validated data export with cross-references

## Core Features Implemented (v2.2)

### Thesis-Critical Features
- [x] **Offloading Choice Mechanism** - "I'll Remember" vs "Set Reminder"
- [x] **Decision Time Tracking** - Milliseconds to make offloading choice
- [x] **Response Time Tracking** - Exact timing for recall probe answers
- [x] **Scaffolded Strategy** - Interval increases by factor (1.5x default)
- [x] **Faded Strategy** - Notification opacity decreases over time
- [x] **Demographics Saved to MongoDB** - Age, education, tech familiarity, memory self-rating
- [x] **Informed Consent** - IRB-style consent form

### New Features (v2.2)
- [x] **Shareable Participant Links** - Each experiment has a unique share code; direct join via `/study/:shareCode`
- [x] **PDF Report Generation** - Thesis-quality PDF with strategy comparisons, demographics, session data
- [x] **Data Export Validation** - Cross-referenced export with data integrity checks, strategy summaries, demographics cross-tabs

## Notification Strategies

| Strategy | Behavior |
|----------|----------|
| **Just-in-Time** | Constant notification interval |
| **Scaffolded** | Interval increases when user chooses "Remember" |
| **Faded** | Notification opacity decreases over time |
| **Control** | No notifications (baseline) |

## API Endpoints
```
# Experiments
POST /api/experiments - Create with auto-generated share_code
GET /api/experiments - List all (includes share_code)
GET /api/experiments/{id} - Get single
GET /api/experiments/join/{share_code} - Join by share code (participant link)

# Participants
POST /api/participants - Create with demographics
PUT /api/participants/{id}/demographics - Update demographics

# Sessions
POST /api/sessions - Create session
POST /api/sessions/{id}/start - Start simulation
POST /api/sessions/{id}/notification - Record notification
POST /api/sessions/{id}/offloading-event - Record choice (KEY)
POST /api/sessions/{id}/recall-probe - Record probe with timing
POST /api/sessions/{id}/start-blackout - Enter blackout phase
POST /api/sessions/{id}/complete - End session
PUT /api/sessions/{id}/strategy-metrics - Save final metrics

# Analytics
GET /api/analytics/overview - Dashboard stats
GET /api/analytics/offloading-comparison - Thesis data
GET /api/analytics/experiments/{id} - Per-experiment stats

# Export
GET /api/export/full-research-data - Complete JSON export
GET /api/export/validated-research-data - Enhanced cross-referenced export with integrity checks
GET /api/export/sessions?format=csv - Sessions CSV
GET /api/export/tasks - Tasks export
GET /api/export/pdf-report - Thesis-quality PDF report
```

## Researcher Access
- **URL**: `/researcher/login`
- **Password**: `pmresearch2026`

## Data Integrity
- All participant demographics saved immediately on creation
- Each offloading event logged with timestamp
- Response times captured with millisecond precision
- Session metrics auto-calculated and stored
- Validated export includes cross-referenced data with integrity checks

## Prioritized Backlog

### P0 - Completed
- [x] Shareable participant links with unique codes
- [x] PDF report generation
- [x] Data export validation

### P1 - High (Future)
- [ ] Real-time participant session monitoring
- [ ] Email export delivery
- [ ] Multi-researcher accounts
- [ ] Session replay viewer

### P2 - Medium (Future)
- [ ] Refactor App.js into smaller components (~2000 lines monolith)
- [ ] Dark mode
- [ ] Mobile participant interface optimization
- [ ] Calendar integration

## Test Results
- Backend: 100% pass rate (22/22 - iteration 4)
- Frontend: 100% pass rate (12/12 - iteration 4)
- All thesis-critical features working

## Version History
- **v1.0.0** (2026-03-10): Initial MVP
- **v2.0.0** (2026-03-10): Complete redesign with two interfaces
- **v2.1.0** (2026-03-10): Thesis-critical features (offloading choice, strategies, response time tracking)
- **v2.2.0** (2026-04-04): Shareable participant links, PDF report generation, validated data export
- **v2.2.1** (2026-04-04): QR code generator for shareable study links
