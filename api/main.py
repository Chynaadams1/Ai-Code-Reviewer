"""
api/main.py
FastAPI server that receives GitHub webhook events and queues PR reviews.
"""
import hashlib
import hmac
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from worker.reviewer import review_pull_request

load_dotenv()

GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

app = FastAPI(
    title="AI Code Reviewer",
    description="GitHub webhook receiver that auto-reviews pull requests with AI.",
    version="1.0.0",
)


# ── Signature verification ────────────────────────────────────────────────────

def verify_signature(payload: bytes, sig_header: str) -> bool:
    """Verify the GitHub HMAC-SHA256 webhook signature."""
    if not GITHUB_WEBHOOK_SECRET:
        return True  # skip in dev if secret not set
    if not sig_header or not sig_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "AI Code Reviewer is live"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    payload_bytes = await request.body()

    if not verify_signature(payload_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    event = x_github_event
    payload = json.loads(payload_bytes)

    # Only act on pull_request opened / synchronize (new commits pushed)
    if event != "pull_request":
        return JSONResponse({"ignored": True, "reason": f"Event '{event}' not handled."})

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return JSONResponse({"ignored": True, "reason": f"Action '{action}' not handled."})

    pr = payload["pull_request"]
    repo = payload["repository"]

    context = {
        "repo_full_name": repo["full_name"],
        "pr_number": pr["number"],
        "pr_title": pr["title"],
        "pr_head_sha": pr["head"]["sha"],
        "pr_base_branch": pr["base"]["ref"],
        "pr_head_branch": pr["head"]["ref"],
        "pr_url": pr["html_url"],
        "diff_url": pr["diff_url"],
        "patch_url": pr["patch_url"],
    }

    # Run review (async — in production wire this to Celery/ARQ/RQ)
    result = await review_pull_request(context)

    return JSONResponse({"reviewed": True, "pr": pr["number"], "summary": result.get("summary")})
