from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.comment import BotComment
from models.feedback import Feedback
from prompts.review_prompt import FEEDBACK_ANALYSIS_PROMPT
import os
import anthropic

MIN_FEEDBACK_FOR_MODIFIER = 50


def log_feedback(db: Session, github_comment_id: int, outcome: str) -> Optional[Feedback]:
    comment = db.query(BotComment).filter(BotComment.github_comment_id == github_comment_id).first()
    if not comment:
        return None

    existing = db.query(Feedback).filter(Feedback.comment_id == comment.id).first()
    if existing:
        existing.outcome = outcome
        db.commit()
        return existing

    feedback = Feedback(comment_id=comment.id, outcome=outcome)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_acceptance_rates(db: Session) -> dict[str, float]:
    results = (
        db.query(
            BotComment.category,
            Feedback.outcome,
            func.count(Feedback.id).label("count"),
        )
        .join(Feedback, Feedback.comment_id == BotComment.id)
        .group_by(BotComment.category, Feedback.outcome)
        .all()
    )

    category_counts: dict[str, dict[str, int]] = {}
    for category, outcome, count in results:
        if category not in category_counts:
            category_counts[category] = {}
        category_counts[category][outcome] = count

    rates = {}
    for category, outcomes in category_counts.items():
        accepted = outcomes.get("accepted", 0)
        total = sum(outcomes.values())
        rates[category] = round(accepted / total, 2) if total > 0 else 0.0

    return rates


def get_total_feedback_count(db: Session) -> int:
    return db.query(func.count(Feedback.id)).scalar() or 0


async def generate_prompt_modifier(db: Session) -> str:
    if get_total_feedback_count(db) < MIN_FEEDBACK_FOR_MODIFIER:
        return ""

    rates = get_acceptance_rates(db)
    if not rates:
        return ""

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""

    rates_summary = "\n".join(f"- {cat}: {rate * 100:.0f}% acceptance" for cat, rate in rates.items())
    prompt = FEEDBACK_ANALYSIS_PROMPT.format(rates_summary=rates_summary)

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip() if response.content else ""
    except anthropic.APIError:
        return ""


def get_feedback_stats(db: Session) -> dict:
    total = get_total_feedback_count(db)
    rates = get_acceptance_rates(db)
    by_outcome = (
        db.query(Feedback.outcome, func.count(Feedback.id).label("count"))
        .group_by(Feedback.outcome)
        .all()
    )
    return {
        "total_feedback": total,
        "acceptance_rates_by_category": rates,
        "outcomes": {outcome: count for outcome, count in by_outcome},
        "has_modifier": total >= MIN_FEEDBACK_FOR_MODIFIER,
    }
