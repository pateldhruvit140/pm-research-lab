# PM Research Lab — Local Docker Setup

## Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) installed

## Quick Start

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd pm-research-lab

# 2. Start everything (MongoDB + Backend + Frontend)
docker compose up --build

# 3. Open in browser
#    Frontend:  http://localhost:3000
#    Backend:   http://localhost:8001/api/health
```

## What Runs Where

| Service  | Port  | URL                            | Description            |
|----------|-------|--------------------------------|------------------------|
| Frontend | 3000  | http://localhost:3000           | React app              |
| Backend  | 8001  | http://localhost:8001/api       | FastAPI server         |
| MongoDB  | 27018 | mongodb://localhost:27018/pm-lab | Database (mapped to 27018 to avoid conflicts) |

## Seed Sample Data

After starting, load sample experiments:

```bash
curl -X POST http://localhost:8001/api/seed
```

This creates 4 experiments with share codes: `JIT2026A`, `SCF2026B`, `FAD2026C`, `CTL2026D`

## Researcher Login
- URL: http://localhost:3000/researcher/login
- Password: `pmresearch2026`

## Participant Testing
- Enter a share code on http://localhost:3000 (e.g., `JIT2026A`)
- Or use direct link: http://localhost:3000/study/JIT2026A

## Verify Data in MongoDB

```bash
# Option 1: Connect via the container
docker exec -it pm-research-mongo mongosh

# Option 2: Connect from your Mac directly (port 27018)
mongosh "mongodb://localhost:27018/pm-lab"

# Inside mongosh:
use pm-lab
db.experiments.find().pretty()
db.participants.find().pretty()
db.sessions.find().pretty()
```

## Useful Commands

```bash
# Start in background
docker compose up -d --build

# View logs
docker compose logs -f

# View only backend logs
docker compose logs -f backend

# View only frontend logs
docker compose logs -f frontend

# Stop everything
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v

# Rebuild after code changes
docker compose up --build
```

## Port Summary

| Port  | Service  | Notes                                      |
|-------|----------|--------------------------------------------|
| 3000  | Frontend | React dev server                           |
| 8001  | Backend  | FastAPI (all API routes under /api)         |
| 27018 | MongoDB  | Host port 27018 → container port 27017     |

## Data Persistence
MongoDB data is stored in a Docker volume (`mongo_data`). Your data persists across restarts. To wipe the database, run `docker compose down -v`.

## Database
- **Name**: `pm-lab`
- **Connection string (from Mac)**: `mongodb://localhost:27018/pm-lab`
- **Connection string (between containers)**: `mongodb://mongodb:27017/pm-lab`

## Frontend Environment
When running locally, the frontend connects to the backend at `http://localhost:8001`. This is configured via the `REACT_APP_BACKEND_URL` build arg in `docker-compose.yml`. The `.env` file in `frontend/` is only used for the cloud preview environment.
