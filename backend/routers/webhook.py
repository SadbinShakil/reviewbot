from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

from models.database import get_db, SessionLocal
from models.pr import PullRequest
from models.comment import BotComment
from services import github_client, diff_parser, review_engine, feedback_tracker

router = APIRouter(prefix="/webhook", tags=["webhook"])


async def _process_pull_request(
    repo_full_name: str,
    pr_number: int,
    pr_title: str,
    pr_author: str,
    head_sha: str,
    pr_url: str,
):
    # Background tasks must own their own DB session
    db = SessionLocal()
    try:
        pr = db.query(PullRequest).filter(
            PullRequest.repo_full_name == repo_full_name,
            PullRequest.pr_number == pr_number,
        ).first()

        if not pr:
            pr = PullRequest(
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                title=pr_title,
                author=pr_author,
                head_sha=head_sha,
                pr_url=pr_url,
                status="reviewing",
            )
            db.add(pr)
        else:
            pr.status = "reviewing"
            pr.head_sha = head_sha

        db.commit()
        db.refresh(pr)

        raw_diff = await github_client.get_pull_request_diff(repo_full_name, pr_number)
        if not raw_diff:
            pr.status = "error"
            db.commit()
            return

        file_diffs = diff_parser.parse_diff(raw_diff)
        chunks = diff_parser.get_reviewable_chunks(file_diffs)

        if not chunks:
            pr.status = "reviewed"
            pr.reviewed_at = datetime.utcnow()
            db.commit()
            return

        prompt_modifier = await feedback_tracker.generate_prompt_modifier(db)
        review_comments = await review_engine.review_pull_request(chunks, prompt_modifier)

        for comment_data in review_comments:
            body = github_client.format_comment_body(
                comment_data["severity"],
                comment_data["category"],
                comment_data["comment"],
                comment_data.get("suggestion", ""),
            )
            posted = await github_client.post_inline_comment(
                repo_full_name,
                pr_number,
                head_sha,
                comment_data["file_path"],
                comment_data["absolute_line"],
                body,
            )

            github_comment_id = posted.get("id") if posted else None
            bot_comment = BotComment(
                pr_id=pr.id,
                github_comment_id=github_comment_id,
                file_path=comment_data["file_path"],
                line_number=comment_data["absolute_line"],
                severity=comment_data["severity"],
                category=comment_data["category"],
                comment_text=comment_data["comment"],
                suggestion=comment_data.get("suggestion", ""),
            )
            db.add(bot_comment)

        pr.status = "reviewed"
        pr.reviewed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"Error processing PR {repo_full_name}#{pr_number}: {e}")
        try:
            pr.status = "error"
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not github_client.verify_webhook_signature(payload_bytes, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = request.headers.get("X-GitHub-Event", "")

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if event_type == "pull_request":
        action = payload.get("action", "")
        if action in ("opened", "synchronize", "reopened"):
            pr_data = payload["pull_request"]
            repo = payload["repository"]["full_name"]
            background_tasks.add_task(
                _process_pull_request,
                repo_full_name=repo,
                pr_number=pr_data["number"],
                pr_title=pr_data["title"],
                pr_author=pr_data["user"]["login"],
                head_sha=pr_data["head"]["sha"],
                pr_url=pr_data["html_url"],
            )
            return {"status": "queued", "pr": pr_data["number"]}

    elif event_type == "pull_request_review_comment":
        action = payload.get("action", "")
        if action == "deleted":
            comment_id = payload["comment"]["id"]
            feedback_tracker.log_feedback(db, comment_id, "accepted")
            return {"status": "feedback_logged", "outcome": "accepted"}

    elif event_type == "pull_request_review":
        action = payload.get("action", "")
        if action == "submitted":
            review_state = payload.get("review", {}).get("state", "")
            if review_state == "dismissed":
                return {"status": "review_dismissed"}

    return {"status": "ignored", "event": event_type}
