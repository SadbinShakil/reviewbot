# ReviewBot

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat&logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

A GitHub Pull Request review bot that analyzes code diffs and posts inline comments on bugs, security issues, performance problems, and style violations. Tracks which comments get accepted or dismissed to improve review quality over time.

![Dashboard Preview](https://placehold.co/900x420/111827/3b82f6?text=ReviewBot+Dashboard)

---

## Features

- Triggers automatically on PR open/update via GitHub webhook
- Reviews code across bugs, security, performance, style, and test coverage
- Posts inline comments directly on diff lines in GitHub
- Tracks accepted/dismissed outcomes per category and adjusts future focus
- Live dashboard — paste any public PR URL and watch the review stream in real time
- Analytics showing comment trends, acceptance rates, and top issue types

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python, FastAPI, SQLAlchemy |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Recharts |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Review Engine | LLM API via `anthropic` SDK |
| Infra | Docker, Docker Compose |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- GitHub personal access token (`repo` + `admin:repo_hook` scopes)
- LLM API key
- [ngrok](https://ngrok.com) for local webhook testing

### 1. Clone and configure

```bash
git clone https://github.com/sadbinShakil/reviewbot.git
cd reviewbot
cp .env.example .env
# Fill in your credentials
```

### 2. Start

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 3. Connect a GitHub repo

Expose the backend with ngrok:

```bash
ngrok http 8000
```

Then register the webhook (replace the URL):

```bash
curl -X POST http://localhost:8000/reviews/register-webhook \
  -H "Content-Type: application/json" \
  -d '{"repo_full_name": "your-user/your-repo", "webhook_url": "https://abc123.ngrok.io/webhook"}'
```

Or go to **GitHub repo → Settings → Webhooks → Add webhook** manually.

### 4. Try without a webhook

Open http://localhost:3000, paste any public GitHub PR URL into the input, and hit **Review PR** — the review streams live in the dashboard.

---

## Local Development (no Docker)

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./reviewbot.db uvicorn main:app --reload
```

**Frontend**

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
| `GITHUB_WEBHOOK_SECRET` | Random string shared with your GitHub webhook config |
| `ANTHROPIC_API_KEY` | LLM API key |
| `DATABASE_URL` | SQLite or PostgreSQL connection string |
| `FRONTEND_URL` | Frontend origin for CORS (default: `http://localhost:3000`) |
| `NEXT_PUBLIC_API_URL` | Backend URL visible to the browser (default: `http://localhost:8000`) |

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /webhook` | POST | GitHub webhook receiver |
| `GET /reviews` | GET | List all reviewed PRs |
| `GET /reviews/{id}` | GET | PR detail with all comments |
| `POST /reviews/{id}/rerun` | POST | Re-run review on a PR |
| `POST /demo/review` | POST | Review any public PR by URL (SSE stream) |
| `GET /analytics/summary` | GET | High-level stats |
| `GET /analytics/by-category` | GET | Comment counts per category |
| `GET /analytics/by-severity` | GET | Comment counts per severity |
| `GET /analytics/acceptance-rates` | GET | Feedback acceptance rate per category |
| `GET /analytics/pr-timeline` | GET | PRs reviewed per day |

Interactive docs at http://localhost:8000/docs

---

## How the Feedback Loop Works

1. ReviewBot posts inline comments on GitHub PRs
2. When a developer deletes a bot comment after fixing the issue → logged as **accepted**
3. When a reviewer resolves a comment without acting → logged as **dismissed**
4. After enough data accumulates, acceptance rates per category are computed
5. A prompt modifier is generated to shift future review focus accordingly

---

## Deployment

**AWS EC2**

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
git clone https://github.com/sadbinShakil/reviewbot.git && cd reviewbot
cp .env.example .env  # fill in production values
docker compose up -d
```

Point your GitHub webhook at `http://<EC2-public-ip>:8000/webhook`.

**Railway**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

Fork → connect to Railway → add PostgreSQL plugin → set env vars → deploy.

---

## Project Structure

```
reviewbot/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── webhook.py          # GitHub webhook handler
│   │   ├── reviews.py          # PR CRUD endpoints
│   │   ├── analytics.py        # Dashboard data
│   │   └── demo.py             # Try-any-PR SSE endpoint
│   ├── services/
│   │   ├── github_client.py    # GitHub API wrapper
│   │   ├── review_engine.py    # LLM integration + prompt logic
│   │   ├── diff_parser.py      # Unified diff parser
│   │   └── feedback_tracker.py # Feedback logging + analysis
│   ├── models/                 # SQLAlchemy ORM models
│   ├── prompts/                # Prompt templates
│   └── requirements.txt
├── frontend/
│   ├── app/                    # Next.js App Router pages
│   ├── components/             # React components
│   └── lib/api.ts              # Typed API client
├── docker-compose.yml
└── .env.example
```

---

## License

MIT
