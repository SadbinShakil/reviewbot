from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from models.database import get_db
from models.pr import PullRequest
from models.comment import BotComment
from models.feedback import Feedback
from services import github_client

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("")
def list_pull_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(PullRequest).order_by(desc(PullRequest.created_at))
    if status:
        query = query.filter(PullRequest.status == status)

    total = query.count()
    prs = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": pr.id,
                "repo_full_name": pr.repo_full_name,
                "pr_number": pr.pr_number,
                "title": pr.title,
                "author": pr.author,
                "status": pr.status,
                "pr_url": pr.pr_url,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "reviewed_at": pr.reviewed_at.isoformat() if pr.reviewed_at else None,
                "comment_count": len(pr.comments),
            }
            for pr in prs
        ],
    }


@router.get("/{pr_id}")
def get_pull_request_detail(pr_id: int, db: Session = Depends(get_db)):
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")

    comments = []
    for c in pr.comments:
        feedback = db.query(Feedback).filter(Feedback.comment_id == c.id).first()
        comments.append({
            "id": c.id,
            "github_comment_id": c.github_comment_id,
            "file_path": c.file_path,
            "line_number": c.line_number,
            "severity": c.severity,
            "category": c.category,
            "comment_text": c.comment_text,
            "suggestion": c.suggestion,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "feedback": {"outcome": feedback.outcome, "logged_at": feedback.logged_at.isoformat()} if feedback else None,
        })

    return {
        "id": pr.id,
        "repo_full_name": pr.repo_full_name,
        "pr_number": pr.pr_number,
        "title": pr.title,
        "author": pr.author,
        "status": pr.status,
        "pr_url": pr.pr_url,
        "head_sha": pr.head_sha,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "reviewed_at": pr.reviewed_at.isoformat() if pr.reviewed_at else None,
        "comments": comments,
    }


@router.post("/{pr_id}/rerun")
async def rerun_review(pr_id: int, db: Session = Depends(get_db)):
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")

    from routers.webhook import _process_pull_request

    pr.status = "reviewing"
    db.commit()

    # _process_pull_request manages its own session
    await _process_pull_request(
        repo_full_name=pr.repo_full_name,
        pr_number=pr.pr_number,
        pr_title=pr.title,
        pr_author=pr.author,
        head_sha=pr.head_sha,
        pr_url=pr.pr_url,
    )

    return {"status": "rerun_complete"}


@router.post("/register-webhook")
async def register_webhook(repo_full_name: str, webhook_url: str, db: Session = Depends(get_db)):
    import os
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    result = await github_client.register_webhook(repo_full_name, webhook_url, secret)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to register webhook")
    return {"status": "registered", "webhook": result}
