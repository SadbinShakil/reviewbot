import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json
import asyncio

from models.database import get_db, SessionLocal
from models.pr import PullRequest
from models.comment import BotComment
from services import github_client, diff_parser, review_engine, feedback_tracker

router = APIRouter(prefix="/demo", tags=["demo"])

PR_URL_PATTERN = re.compile(
    r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)


class DemoReviewRequest(BaseModel):
    pr_url: str


def _parse_pr_url(url: str) -> tuple[str, int]:
    m = PR_URL_PATTERN.search(url)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid GitHub PR URL. Expected: https://github.com/owner/repo/pull/123")
    return f"{m.group('owner')}/{m.group('repo')}", int(m.group("number"))


async def _stream_review(repo_full_name: str, pr_number: int):
    """Generator that streams review progress as SSE events."""

    def event(kind: str, data: dict) -> str:
        return f"data: {json.dumps({'type': kind, **data})}\n\n"

    db = SessionLocal()
    try:
        yield event("status", {"message": f"Fetching PR #{pr_number} from {repo_full_name}..."})
        await asyncio.sleep(0.1)

        pr_meta = await github_client.get_pull_request(repo_full_name, pr_number)
        if not pr_meta:
            yield event("error", {"message": "Could not fetch PR. Make sure it's a public repo or your GITHUB_TOKEN is set."})
            return

        head_sha = pr_meta["head"]["sha"]
        pr_title = pr_meta["title"]
        pr_author = pr_meta["user"]["login"]
        pr_url = pr_meta["html_url"]

        # Upsert PR in DB
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

        yield event("pr_found", {
            "message": f"Found: \"{pr_title}\" by {pr_author}",
            "pr_id": pr.id,
        })

        yield event("status", {"message": "Downloading diff..."})
        raw_diff = await github_client.get_pull_request_diff(repo_full_name, pr_number)
        if not raw_diff:
            yield event("error", {"message": "Could not fetch diff."})
            pr.status = "error"
            db.commit()
            return

        file_diffs = diff_parser.parse_diff(raw_diff)
        chunks = diff_parser.get_reviewable_chunks(file_diffs)

        files_changed = len(file_diffs)
        yield event("status", {"message": f"Parsed {files_changed} changed file(s), {len(chunks)} review chunk(s)"})

        if not chunks:
            yield event("done", {"message": "No reviewable code changes found.", "pr_id": pr.id, "comments": []})
            pr.status = "reviewed"
            pr.reviewed_at = datetime.utcnow()
            db.commit()
            return

        yield event("status", {"message": f"Sending {min(len(chunks), 10)} chunk(s) for review..."})

        prompt_modifier = await feedback_tracker.generate_prompt_modifier(db)
        review_comments = await review_engine.review_pull_request(chunks, prompt_modifier)

        yield event("status", {"message": f"Found {len(review_comments)} issue(s). Saving..."})

        saved_comments = []
        for comment_data in review_comments:
            import os
            github_comment_id = None
            if os.getenv("GITHUB_TOKEN") and not os.getenv("GITHUB_TOKEN", "").startswith("ghp_your"):
                body = github_client.format_comment_body(
                    comment_data["severity"],
                    comment_data["category"],
                    comment_data["comment"],
                    comment_data.get("suggestion", ""),
                )
                posted = await github_client.post_inline_comment(
                    repo_full_name, pr_number, head_sha,
                    comment_data["file_path"], comment_data["absolute_line"], body,
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
            saved_comments.append({
                "file_path": comment_data["file_path"],
                "line": comment_data["absolute_line"],
                "severity": comment_data["severity"],
                "category": comment_data["category"],
                "comment": comment_data["comment"],
                "suggestion": comment_data.get("suggestion", ""),
                "posted_to_github": github_comment_id is not None,
            })

            # Stream each comment as it's saved
            yield event("comment", saved_comments[-1])

        pr.status = "reviewed"
        pr.reviewed_at = datetime.utcnow()
        db.commit()

        yield event("done", {
            "message": f"Review complete! {len(saved_comments)} comment(s) found.",
            "pr_id": pr.id,
            "total": len(saved_comments),
        })

    except Exception as e:
        yield event("error", {"message": str(e)})
        try:
            pr.status = "error"
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/review")
async def demo_review(req: DemoReviewRequest):
    repo_full_name, pr_number = _parse_pr_url(req.pr_url)
    return StreamingResponse(
        _stream_review(repo_full_name, pr_number),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
