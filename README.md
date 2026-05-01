# ReviewBot

A GitHub Pull Request review bot that analyzes code diffs and posts inline comments on bugs, security issues, performance problems, and style violations. Tracks which comments get accepted or dismissed to improve review quality over time.

---

## Features

- Triggers on PR open/update via GitHub webhook
- Reviews code across: bugs, security, performance, style, test coverage
- Posts inline comments directly on diff lines in GitHub
- Tracks accepted/dismissed comment outcomes per category
- Dashboard showing reviewed PRs, per-PR comment breakdown, and analytics
- Adjusts review focus based on historical feedback after enough data is collected

---

## Architecture

```
GitHub PR → Webhook → FastAPI Backend → Diff Parser → LLM Review Engine
                                      ↓
                               SQLite / PostgreSQL
                                      ↓
                              Next.js Dashboard
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- GitHub personal access token (repo + webhook scopes)
- LLM API key
- ngrok (for local webhook testing)

### 1. Clone and configure

```bash
git clone <your-repo>
cd reviewbot
cp .env.example .env
# Fill in your credentials
```

### 2. Start services

```bash
docker compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### 3. Expose local backend for GitHub webhooks

```bash
ngrok http 8000
```

### 4. Register webhook on your GitHub repo

Option A — via the API:
```bash
curl -X POST http://localhost:8000/reviews/register-webhook \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "your-user/your-repo", "webhook_url": "https://abc123.ngrok.io/webhook"}'
```

Option B — GitHub Settings → Webhooks → Add webhook:
- Payload URL: `https://abc123.ngrok.io/webhook`
- Content type: `application/json`
- Secret: value from `GITHUB_WEBHOOK_SECRET` in `.env`
- Events: Pull requests, Pull request review comments

### 5. Open a PR and watch ReviewBot post comments

---

## Local Development (no Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./reviewbot.db uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub PAT with `repo` and `admin:repo_hook` scopes |
| `GITHUB_WEBHOOK_SECRET` | Random string shared with GitHub webhook config |
| `LLM_API_KEY` | API key for the review engine |
| `DATABASE_URL` | PostgreSQL or SQLite connection string |
| `FRONTEND_URL` | Frontend origin for CORS (default: http://localhost:3000) |
| `NEXT_PUBLIC_API_URL` | Backend URL visible to browser (default: http://localhost:8000) |

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | GitHub webhook receiver |
| `/reviews` | GET | List all reviewed PRs |
| `/reviews/{id}` | GET | PR detail with comments |
| `/reviews/{id}/rerun` | POST | Re-run review on a PR |
| `/demo/review` | POST | Review any public PR by URL (SSE stream) |
| `/analytics/summary` | GET | High-level stats |
| `/analytics/by-category` | GET | Comment counts per category |
| `/analytics/by-severity` | GET | Comment counts per severity |
| `/analytics/acceptance-rates` | GET | Feedback acceptance rate per category |
| `/analytics/pr-timeline` | GET | PRs reviewed per day |

Interactive docs: http://localhost:8000/docs

---

## How the Feedback Loop Works

1. ReviewBot posts inline comments on GitHub PRs
2. When a developer deletes a bot comment after fixing the issue, it's logged as `accepted`
3. When a reviewer resolves a comment without acting on it, it's logged as `dismissed`
4. After enough feedback accumulates, acceptance rates per category are computed
5. A prompt modifier is generated and prepended to future reviews to adjust focus
6. e.g. "Prioritise security findings (82% accepted). Reduce style comments (9% accepted)."

---

## Deployment on AWS EC2

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
git clone <your-repo> && cd reviewbot
cp .env.example .env
docker compose up -d
```

Point your GitHub webhook at `http://<EC2-public-ip>:8000/webhook`, or put nginx in front for SSL.

---

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

1. Fork this repo
2. Connect to Railway
3. Add PostgreSQL plugin
4. Set environment variables
5. Deploy

---

## Project Structure

```
reviewbot/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── webhook.py        # GitHub webhook handler
│   │   ├── reviews.py        # PR CRUD endpoints
│   │   ├── analytics.py      # Dashboard data
│   │   └── demo.py           # Try-any-PR endpoint (SSE)
│   ├── services/
│   │   ├── github_client.py  # GitHub API wrapper
│   │   ├── review_engine.py  # LLM integration + prompt logic
│   │   ├── diff_parser.py    # Unified diff parser
│   │   └── feedback_tracker.py
│   ├── models/               # SQLAlchemy models
│   ├── prompts/              # Prompt templates
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/
│   └── lib/api.ts
├── docker-compose.yml
└── .env.example
```
