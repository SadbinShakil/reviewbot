import json
import re
import asyncio
import hashlib
import os
import anthropic
from services.diff_parser import DiffChunk
from prompts.review_prompt import build_system_prompt, build_user_prompt

_MODEL = "claude-sonnet-4-20250514"
_MAX_CHUNKS = 10
_MAX_TOKENS = 1024

_review_cache: dict[str, list[dict]] = {}


def _get_client() -> anthropic.AsyncAnthropic:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return anthropic.AsyncAnthropic(api_key=key)


def _chunk_cache_key(chunk: DiffChunk) -> str:
    return hashlib.sha256(f"{chunk.filename}:{chunk.content}".encode()).hexdigest()


def _parse_response(text: str) -> list[dict]:
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    json_match = re.search(r'\{[\s\S]*"comments"[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)
    try:
        data = json.loads(text)
        valid = []
        for c in data.get("comments", []):
            if all(k in c for k in ("line", "severity", "category", "comment")):
                valid.append({
                    "line": int(c["line"]),
                    "severity": c["severity"] if c["severity"] in ("critical", "warning", "suggestion") else "suggestion",
                    "category": c["category"] if c["category"] in ("bug", "security", "performance", "style", "testing") else "style",
                    "comment": c["comment"],
                    "suggestion": c.get("suggestion", ""),
                })
        return valid
    except (json.JSONDecodeError, ValueError):
        return []


async def review_chunk(chunk: DiffChunk, client: anthropic.AsyncAnthropic, modifier: str = "") -> list[dict]:
    cache_key = _chunk_cache_key(chunk)
    if cache_key in _review_cache:
        return _review_cache[cache_key]

    try:
        response = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=build_system_prompt(modifier),
            messages=[{"role": "user", "content": build_user_prompt(
                chunk.filename, chunk.language, chunk.content, chunk.start_line
            )}],
        )
        text = response.content[0].text if response.content else ""
        results = _parse_response(text)
        _review_cache[cache_key] = results
        return results
    except anthropic.APIError as e:
        print(f"Review engine error ({chunk.filename}:{chunk.start_line}): {e}")
        return []


async def review_pull_request(chunks: list[DiffChunk], modifier: str = "") -> list[dict]:
    client = _get_client()
    selected = sorted(chunks, key=lambda c: c.added_lines + c.removed_lines, reverse=True)[:_MAX_CHUNKS]
    semaphore = asyncio.Semaphore(3)

    async def bounded(chunk: DiffChunk) -> tuple[DiffChunk, list[dict]]:
        async with semaphore:
            return chunk, await review_chunk(chunk, client, modifier)

    results = await asyncio.gather(*[bounded(c) for c in selected], return_exceptions=True)

    all_comments = []
    for result in results:
        if isinstance(result, Exception):
            continue
        chunk, comments = result
        for c in comments:
            c["file_path"] = chunk.filename
            c["absolute_line"] = chunk.start_line + max(0, c["line"] - 1)
        all_comments.extend(comments)

    return all_comments
