from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models.database import get_db
from models.pr import PullRequest
from models.comment import BotComment
from models.feedback import Feedback
from services.feedback_tracker import get_acceptance_rates, get_feedback_stats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total_prs = db.query(func.count(PullRequest.id)).scalar() or 0
    reviewed_prs = db.query(func.count(PullRequest.id)).filter(PullRequest.status == "reviewed").scalar() or 0
    total_comments = db.query(func.count(BotComment.id)).scalar() or 0
    total_feedback = db.query(func.count(Feedback.id)).scalar() or 0

    accepted = db.query(func.count(Feedback.id)).filter(Feedback.outcome == "accepted").scalar() or 0
    overall_rate = round(accepted / total_feedback, 2) if total_feedback > 0 else 0.0

    return {
        "total_prs": total_prs,
        "reviewed_prs": reviewed_prs,
        "total_comments": total_comments,
        "total_feedback": total_feedback,
        "overall_acceptance_rate": overall_rate,
    }


@router.get("/by-category")
def comments_by_category(db: Session = Depends(get_db)):
    results = (
        db.query(BotComment.category, func.count(BotComment.id).label("count"))
        .group_by(BotComment.category)
        .order_by(desc("count"))
        .all()
    )
    return [{"category": cat, "count": cnt} for cat, cnt in results]


@router.get("/by-severity")
def comments_by_severity(db: Session = Depends(get_db)):
    results = (
        db.query(BotComment.severity, func.count(BotComment.id).label("count"))
        .group_by(BotComment.severity)
        .order_by(desc("count"))
        .all()
    )
    return [{"severity": sev, "count": cnt} for sev, cnt in results]


@router.get("/acceptance-rates")
def acceptance_rates(db: Session = Depends(get_db)):
    rates = get_acceptance_rates(db)
    return [{"category": cat, "acceptance_rate": rate} for cat, rate in rates.items()]


@router.get("/feedback-stats")
def feedback_stats(db: Session = Depends(get_db)):
    return get_feedback_stats(db)


@router.get("/top-issues")
def top_issues(limit: int = 10, db: Session = Depends(get_db)):
    results = (
        db.query(
            BotComment.category,
            BotComment.severity,
            BotComment.file_path,
            func.count(BotComment.id).label("count"),
        )
        .group_by(BotComment.category, BotComment.severity, BotComment.file_path)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return [
        {"category": cat, "severity": sev, "file_path": fp, "count": cnt}
        for cat, sev, fp, cnt in results
    ]


@router.get("/pr-timeline")
def pr_timeline(days: int = 30, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    results = (
        db.query(
            func.date_trunc("day", PullRequest.created_at).label("day"),
            func.count(PullRequest.id).label("count"),
        )
        .filter(PullRequest.created_at >= cutoff)
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [{"day": str(day.date()), "count": cnt} for day, cnt in results]
