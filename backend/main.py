from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env", override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from models.database import init_db
from routers import webhook, reviews, analytics, demo

app = FastAPI(
    title="ReviewBot API",
    description="GitHub PR review bot",
    version="1.0.0",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(reviews.router)
app.include_router(analytics.router)
app.include_router(demo.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    from services.github_client import has_github_token
    return {
        "status": "ok",
        "service": "ReviewBot",
        "github_token": "set" if has_github_token() else "missing (public repos only)",
        "llm_key": "set" if os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-") else "missing",
    }


@app.get("/")
def root():
    return {"message": "ReviewBot API — see /docs for endpoints"}
