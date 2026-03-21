"""
api/routes_github.py
Receives GitHub webhook events, verifies the HMAC signature,
and dispatches PR reviews to the worker.
"""
import hashlib
import hmac
import json

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from api.config import get_settings
from worker.tasks import run_review_job

router = APIRouter()


def _verify_signature(payload_bytes: bytes, sig_header: str) -> bool:
    """Verify GitHub's HMAC-SHA256 webhook signature."""
    settings = get_settings()
    secret = settings.github_webhook_secret

    # Skip verification in dev if secret not configured
    if not secret:
        return True

    if not sig_header or not sig_header.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
):
    """
    Entry point for all GitHub webhook events.
    Only pull_request events with action opened/synchronize/reopened trigger a review.
    """
    payload_bytes = await request.body()

    # ── Security: verify signature ───────────────────────────────────────────
    if not _verify_signature(payload_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    # ── Parse payload ────────────────────────────────────────────────────────
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    # ── Filter events ────────────────────────────────────────────────────────
    if x_github_event != "pull_request":
        return JSONResponse({
            "ignored": True,
            "reason": f"Event type '{x_github_event}' is not handled.",
        })

    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return JSONResponse({
            "ignored": True,
            "reason": f"PR action '{action}' does not trigger a review.",
        })

    pr   = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    repo_full_name = repo.get("full_name", "")
    pr_number      = pr.get("number")
    diff_url       = pr.get("diff_url", "")
    pr_title       = pr.get("title", "")
    head_sha       = pr.get("head", {}).get("sha", "")

    if not repo_full_name or not pr_number:
        raise HTTPException(status_code=422, detail="Missing repo or PR number in payload.")

    print(f"[webhook] PR #{pr_number} '{pr_title}' in {repo_full_name} — action: {action}")

    # ── Dispatch to worker ───────────────────────────────────────────────────
    results = await run_review_job(
        repo_full_name=repo_full_name,
        pr_number=pr_number,
        diff_url=diff_url,
        head_sha=head_sha,
    )

    return JSONResponse({
        "message": "Webhook received and review completed.",
        "action": action,
        "repo": repo_full_name,
        "pr_number": pr_number,
        "results": results,
    })
