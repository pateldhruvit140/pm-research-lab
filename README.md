# PM Research Lab

A computational proof-of-concept tool designed for a master's thesis investigating how automated digital notifications influence **prospective memory** and **cognitive offloading** behavior. The tool simulates a multi-dose medication reminder scenario where participants choose between relying on their own memory or offloading to digital reminders.

---

## What This Tool Does

This application serves as a complete research platform with two distinct interfaces:

### For Participants
- Join a study via a **share code** or **QR code** provided by the researcher
- Complete an **informed consent** form and **demographics** questionnaire
- Experience a **simulated medication reminder** scenario with time-compressed notifications
- At each notification, choose: **"I'll Remember"** (internal memory) or **"Set Reminder"** (cognitive offloading)
- Complete **recall probes** (memory tests) during a blackout period when reminders stop
- View personal results including recall accuracy, offloading rate, and decision times

### For Researchers
- Create and configure experiments with **4 notification strategies**:
  - **Just-in-Time** — constant notification intervals
  - **Scaffolded** — intervals increase when participant chooses "Remember"
  - **Faded** — notification prominence decreases over time
  - **Control** — no notifications (baseline group)
- Generate **shareable links and QR codes** to distribute studies to participants
- View **analytics dashboard** with offloading rate comparisons across strategies
- Export data in multiple formats: **CSV**, **JSON**, **Validated JSON** (cross-referenced with integrity checks), and **PDF reports**
- Track weekly **progress and milestones** for thesis documentation

---

## Research Concepts

| Concept | Definition |
|---------|-----------|
| **Prospective Memory (PM)** | Remembering to perform an intended action at the right time in the future |
| **Cognitive Offloading** | Using external tools (e.g., phone reminders) to reduce mental demand |
| **Scaffolded Reminders** | Gradually reducing reminder support as the user demonstrates recall ability |
| **Faded Reminders** | Gradually reducing the visual prominence of reminders over time |

---

## Data Collected

The tool captures the following data points for thesis analysis:

- **Demographics** — age group, education, tech familiarity, memory self-rating
- **Offloading choices** — "Remember" vs "Set Reminder" for each notification, with decision time (ms)
- **Recall probes** — question, answer, correctness, response time (ms)
- **Notification metadata** — dose number, prominence level, interval timing
- **Session aggregates** — offloading rate, recall accuracy, average decision/response times
- **Strategy-specific metrics** — final scaffolded interval, final faded prominence

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Tailwind CSS, Recharts, React Router, qrcode.react |
| Backend | FastAPI, Pydantic, Motor (async MongoDB driver) |
| Database | MongoDB 7 |
| PDF Generation | ReportLab |
| Containerization | Docker, Docker Compose |

---

## Local Development (Docker)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed

### Quick Start

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd pm-research-lab

# 2. Start all services (MongoDB + Backend + Frontend)
docker compose up --build

# 3. Seed sample data (in a new terminal)
curl -X POST http://localhost:8001/api/seed

# 4. Open the app
open http://localhost:3000
```

### Services

| Service  | Port  | URL                              |
|----------|-------|----------------------------------|
| Frontend | 3000  | http://localhost:3000             |
| Backend  | 8001  | http://localhost:8001/api         |
| MongoDB  | 27018 | mongodb://localhost:27018/pm-lab  |

### Useful Commands

```bash
# Start in background
docker compose up -d --build

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Stop and wipe all data (fresh start)
docker compose down -v

# Rebuild after code changes
docker compose up --build
```

### Verify Data in MongoDB

```bash
# Connect via container
docker exec -it pm-research-mongo mongosh

# Or from your Mac directly
mongosh "mongodb://localhost:27018/pm-lab"

# Inside mongosh:
use pm-lab
db.experiments.find().pretty()
db.participants.find().pretty()
db.sessions.find().pretty()
```

---

## Cloud Deployment

For hosting on the cloud with a public URL for real participants, see [CLOUD_SETUP.md](./CLOUD_SETUP.md) — step-by-step guide using **Render** (free) + **MongoDB Atlas** (free).

---

## Access

### Researcher Dashboard
- **URL**: http://localhost:3000/researcher/login
- **Password**: `pmresearch2026`

### Participant Flow
No credentials needed. Enter a share code on the landing page or use a direct link.

### Share Codes (after seeding sample data)

| Code     | Strategy   | Experiment                   | Direct Link |
|----------|-----------|------------------------------|-------------|
| JIT2026A | Just-in-Time | JIT Notification Study     | http://localhost:3000/study/JIT2026A |
| SCF2026B | Scaffolded   | Scaffolded Reminder Study  | http://localhost:3000/study/SCF2026B |
| FAD2026C | Faded        | Faded Reminder Study       | http://localhost:3000/study/FAD2026C |
| CTL2026D | Control      | Control Group              | http://localhost:3000/study/CTL2026D |

---

## API Endpoints

### Experiments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/experiments` | Create experiment (auto-generates share code) |
| GET | `/api/experiments` | List all experiments |
| GET | `/api/experiments/{id}` | Get single experiment |
| GET | `/api/experiments/join/{share_code}` | Join by share code |
| DELETE | `/api/experiments/{id}` | Delete experiment |

### Participants & Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/participants` | Create participant with demographics |
| POST | `/api/sessions` | Create session |
| POST | `/api/sessions/{id}/start` | Start simulation |
| POST | `/api/sessions/{id}/offloading-event` | Record offloading choice |
| POST | `/api/sessions/{id}/recall-probe` | Record recall probe |
| POST | `/api/sessions/{id}/complete` | Complete session |

### Analytics & Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/overview` | Dashboard summary |
| GET | `/api/analytics/offloading-comparison` | Strategy comparison (thesis data) |
| GET | `/api/export/sessions?format=csv` | Sessions as CSV |
| GET | `/api/export/full-research-data` | Complete JSON export |
| GET | `/api/export/validated-research-data` | Cross-referenced export with integrity checks |
| GET | `/api/export/pdf-report` | Thesis-quality PDF report |

---

## Project Structure

```
pm-research-lab/
├── backend/
│   ├── server.py          # FastAPI server (routes, models, DB logic)
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React application
│   │   ├── App.css
│   │   └── index.css      # Tailwind + custom styles
│   ├── package.json
│   ├── Dockerfile
│   └── tailwind.config.js
├── docker-compose.yml     # Local Docker orchestration
├── DOCKER_SETUP.md        # Detailed Docker instructions
├── CLOUD_SETUP.md         # Render + MongoDB Atlas deployment guide
└── README.md
```

---

## License

For academic research use only.
