# Autonomous Engineering System

A production-ready autonomous engineering system where a **Telegram bot** acts as the command console and tasks are executed by **Devin AI**. The system exposes an integration API so that **Hermes** (or any external orchestrator) can connect and dispatch tasks through the Devin API.

## Architecture

```
Telegram Bot
     ↓
Webhook API Server (FastAPI)
     ↓
Task API
     ↓
Task Queue (Redis + RQ)
     ↓
Devin Client
     ↓
GitHub Repository Automation
```

Hermes connects to the **Task API** directly.

---

## Project Structure

```
/autonomous-devin-system
│
├── app/
│   ├── agents/
│   │   ├── planner_agent.py        # Breaks requests into task plans
│   │   ├── dispatcher_agent.py     # Routes tasks to backends
│   │   ├── execution_agent.py      # Sends work to Devin, monitors progress
│   │   ├── memory_agent.py         # Persists and retrieves task history
│   │   └── result_agent.py         # Formats and delivers results
│   │
│   ├── integrations/
│   │   ├── telegram_bot.py         # Telegram command console
│   │   ├── devin_client.py         # Devin AI API client
│   │   └── github_client.py        # GitHub repository management
│   │
│   ├── core/
│   │   ├── config.py               # Centralised configuration
│   │   ├── message_bus.py          # In-process pub/sub bus
│   │   ├── task_dispatcher.py      # Task routing logic
│   │   └── logging_setup.py        # Logging configuration
│   │
│   ├── database/
│   │   ├── db.py                   # Database access layer
│   │   └── models.py              # SQLAlchemy ORM models
│   │
│   ├── server/
│   │   └── api.py                  # FastAPI REST server
│   │
│   └── workers/
│       └── worker.py               # Background task worker
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── logs/                           # Log files (auto-created)
├── run_api.py                      # API entry-point
├── run_bot.py                      # Telegram bot entry-point
├── run_worker.py                   # Worker entry-point
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/maliot123/autonomous-devin-system.git
cd autonomous-devin-system
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Token from [@BotFather](https://t.me/BotFather) |
| `DEVIN_API_KEY` | Yes | Your Devin API key |
| `DEVIN_ORG_ID` | No | Devin organisation ID |
| `DEVIN_API_URL` | No | Defaults to `https://api.devin.ai/v1` |
| `GITHUB_TOKEN` | No | GitHub personal access token |
| `REDIS_URL` | No | Defaults to `redis://redis:6379/0` |
| `DATABASE_URL` | No | Defaults to SQLite |

### 3. Run with Docker (recommended)

```bash
cd docker
docker compose up -d --build
```

This starts four services:

| Service | Description |
|---|---|
| `task_api` | FastAPI server on port 8000 |
| `telegram_bot` | Telegram polling bot |
| `worker` | Background task processor |
| `redis` | Message queue backend |

### 4. Run locally (development)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1 — API server
python run_api.py

# Terminal 2 — Telegram bot
python run_bot.py

# Terminal 3 — Worker
python run_worker.py
```

---

## Telegram Commands

| Command | Description | Example |
|---|---|---|
| `/start` | Show help | `/start` |
| `/status` | System status | `/status` |
| `/agents` | List agents | `/agents` |
| `/build <desc>` | Generate code | `/build create SaaS landing page` |
| `/task <desc>` | Generic task | `/task fix authentication bug` |
| `/repo <url>` | Analyse repo | `/repo https://github.com/user/project` |
| `/deploy <desc>` | Setup deploy | `/deploy deploy project to production` |
| `/logs [task_id]` | View logs | `/logs` or `/logs abc123` |

---

## API Endpoints

### Create a task

```bash
curl -X POST http://localhost:8000/task/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "CODE_GENERATION",
    "description": "Create a SaaS landing page using Next.js and Tailwind",
    "repository": "https://github.com/user/project",
    "priority": "normal"
  }'
```

**Response:**

```json
{
  "task_id": "a1b2c3d4e5f6...",
  "status": "queued",
  "message": "Task queued for execution via CODE_GENERATION"
}
```

### Get task status

```bash
curl http://localhost:8000/task/status/{task_id}
```

### Get task result

```bash
curl http://localhost:8000/task/result/{task_id}
```

### System status

```bash
curl http://localhost:8000/system/status
```

### View logs

```bash
curl http://localhost:8000/logs
curl http://localhost:8000/logs?task_id=abc123&limit=50
```

### Health check

```bash
curl http://localhost:8000/health
```

---

## Task Types

| Type | Description |
|---|---|
| `CODE_GENERATION` | Generate new code / projects |
| `REPO_ANALYSIS` | Analyse repository structure |
| `BUG_FIX` | Fix bugs in existing code |
| `REFACTORING` | Refactor / clean up code |
| `AUTOMATION_SCRIPT` | Create automation scripts |
| `DEPLOYMENT_SETUP` | Set up deployment pipelines |
| `AI_AGENT_CREATION` | Build AI agents |

---

## Sample Devin Task Payload

When the system sends a task to Devin, it constructs a prompt like:

```
Task: Create a SaaS landing page using Next.js and Tailwind
Repository: https://github.com/user/project
Task type: CODE_GENERATION
```

The Devin client creates a session via `POST /v1/sessions` with:

```json
{
  "prompt": "Task: Create a SaaS landing page using Next.js and Tailwind\nRepository: https://github.com/user/project\nTask type: CODE_GENERATION",
  "idempotency_key": "<task_id>"
}
```

---

## Hermes Integration

Hermes connects directly to the Task API. No code changes are required.

### Endpoint

```
POST http://<your-server>:8000/task/create
```

### Example payload

```json
{
  "task_type": "CODE_GENERATION",
  "description": "Create a SaaS landing page using Next.js and Tailwind",
  "repository": "https://github.com/user/project",
  "priority": "normal"
}
```

### Integration flow

```
Hermes
  ↓  POST /task/create
Task API
  ↓
Task Queue
  ↓
Worker → Devin API → Devin executes → Result stored
  ↓
Hermes polls GET /task/status/{task_id}
  ↓
Hermes retrieves GET /task/result/{task_id}
```

### Authentication (future)

The API currently accepts unauthenticated requests. To secure the endpoint for Hermes, add an API key middleware or OAuth2 bearer token validation to the FastAPI app.

---

## Workflow Example

1. User sends `/build create SaaS landing page` in Telegram
2. Telegram bot sends `POST /task/create` to the API
3. API creates a task record and enqueues it
4. Worker picks up the task from the queue
5. Planner agent infers task type (`CODE_GENERATION`)
6. Dispatcher agent routes to the Devin backend
7. Execution agent creates a Devin session with the prompt
8. System polls Devin until the session completes
9. Result is stored in the database
10. Telegram bot can retrieve and display the result

---

## Environment Variables

All secrets are stored in environment variables via `.env`. **Never hardcode secrets.**

See `.env.example` for the full list.

---

## License

MIT
