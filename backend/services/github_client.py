import httpx
import hashlib
import hmac
import os
from typing import Optional

GITHUB_API_BASE = "https://api.github.com"


def _token() -> str:
    t = os.getenv("GITHUB_TOKEN", "")
    # Treat placeholder as missing
    if t.startswith("ghp_your") or not t:
        return ""
    return t


def _webhook_secret() -> str:
    s = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if s.startswith("your_random") or not s:
        return ""
    return s


def _headers(accept: str = "application/vnd.github.v3+json") -> dict:
    h = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _token()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def verify_webhook_signature(payload_bytes: bytes, signature_header: str) -> bool:
    secret = _webhook_secret()
    if not secret:
        return True  # dev mode — no secret set
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(key=secret.encode(), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()
    received = signature_header[7:]
    return hmac.compare_digest(expected, received)


def has_github_token() -> bool:
    return bool(_token())


async def get_pull_request_diff(repo_full_name: str, pr_number: int) -> Optional[str]:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/pulls/{pr_number}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=_headers("application/vnd.github.v3.diff"))
        if response.status_code == 200:
            return response.text
        return None


async def get_pull_request(repo_full_name: str, pr_number: int) -> Optional[dict]:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/pulls/{pr_number}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=_headers())
        if response.status_code == 200:
            return response.json()
        return None


async def post_inline_comment(
    repo_full_name: str,
    pr_number: int,
    commit_sha: str,
    file_path: str,
    line: int,
    body: str,
) -> Optional[dict]:
    if not has_github_token():
        return None
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/pulls/{pr_number}/comments"
    payload = {
        "body": body,
        "commit_id": commit_sha,
        "path": file_path,
        "line": line,
        "side": "RIGHT",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=_headers(), json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 422:
            return await post_pr_comment(repo_full_name, pr_number, f"**`{file_path}` line {line}**\n\n{body}")
        return None


async def post_pr_comment(repo_full_name: str, pr_number: int, body: str) -> Optional[dict]:
    if not has_github_token():
        return None
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/issues/{pr_number}/comments"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=_headers(), json={"body": body})
        if response.status_code == 201:
            return response.json()
        return None


async def get_repo_webhooks(repo_full_name: str) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/hooks"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=_headers())
        if response.status_code == 200:
            return response.json()
        return []


async def register_webhook(repo_full_name: str, webhook_url: str, secret: str) -> Optional[dict]:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/hooks"
    payload = {
        "name": "web",
        "active": True,
        "events": ["pull_request", "pull_request_review_comment", "pull_request_review"],
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0",
        },
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=_headers(), json=payload)
        if response.status_code == 201:
            return response.json()
        return None


def format_comment_body(severity: str, category: str, comment: str, suggestion: str) -> str:
    severity_emoji = {"critical": "🔴", "warning": "🟡", "suggestion": "🔵"}.get(severity, "⚪")
    body = f"{severity_emoji} **ReviewBot [{category.upper()}]**: {comment}"
    if suggestion:
        body += f"\n\n**Suggestion:**\n```\n{suggestion}\n```"
    body += "\n\n---\n*Posted by [ReviewBot](http://localhost:3000)*"
    return body
