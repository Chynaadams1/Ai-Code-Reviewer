from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, Optional
from worker.tasks import run_review_job

router = APIRouter()

class WebhookPayload(BaseModel):
    action: Optional[str] = None
    repository: Dict[str, Any] = {}
    pull_request: Dict[str, Any] = {}

@router.post("/webhook/github")
async def github_webhook(payload: WebhookPayload):
    results = run_review_job(payload.repository.get("full_name"), payload.pull_request.get("number"))
    print(f"Processing PR #{payload.pull_request.get('number')} from {payload.repository.get('full_name')}")

    return {
    "message": "Webhook received and review completed",
    "action": payload.action,
    "repo": payload.repository.get("full_name"),
    "pr_number": payload.pull_request.get("number"),
    "results": results
}

