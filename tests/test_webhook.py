"""
tests/test_webhook.py
Run with: pytest tests/ -v
"""
import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from api.main import app

FAKE_SECRET = "test_secret"
FAKE_REVIEW = {
    "summary": "Looks good overall.",
    "score": 8,
    "verdict": "approve",
    "issues": [],
    "positives": ["Clean logic"],
}


def _sign(payload: bytes, secret: str = FAKE_SECRET) -> str:
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _pr_payload(action="opened") -> dict:
    return {
        "action": action,
        "repository": {"full_name": "testuser/testrepo"},
        "pull_request": {
            "number": 42,
            "title": "Test PR",
            "diff_url": "https://github.com/testuser/testrepo/pull/42.diff",
            "head": {"sha": "abc123"},
        },
    }


@pytest.mark.asyncio
async def test_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/status")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_ignored_non_pr_event():
    body = json.dumps({"action": "created"}).encode()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/webhook/github",
            content=body,
            headers={"x-github-event": "push", "x-hub-signature-256": _sign(body)},
        )
    assert resp.status_code == 200
    assert resp.json()["ignored"] is True


@pytest.mark.asyncio
async def test_webhook_ignored_closed_action():
    body = json.dumps(_pr_payload("closed")).encode()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/webhook/github",
            content=body,
            headers={"x-github-event": "pull_request", "x-hub-signature-256": _sign(body)},
        )
    assert resp.status_code == 200
    assert resp.json()["ignored"] is True


@pytest.mark.asyncio
async def test_webhook_triggers_review():
    body = json.dumps(_pr_payload("opened")).encode()
    with patch("api.routes_github.run_review_job", new=AsyncMock(return_value=FAKE_REVIEW)):
        with patch("api.routes_github.get_settings") as mock_cfg:
            mock_cfg.return_value.github_webhook_secret = ""  # skip sig check
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/webhook/github",
                    content=body,
                    headers={"x-github-event": "pull_request", "x-hub-signature-256": _sign(body)},
                )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pr_number"] == 42
    assert data["results"]["score"] == 8


@pytest.mark.asyncio
async def test_webhook_bad_signature():
    body = json.dumps(_pr_payload()).encode()
    with patch("api.routes_github.get_settings") as mock_cfg:
        mock_cfg.return_value.github_webhook_secret = FAKE_SECRET
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/webhook/github",
                content=body,
                headers={"x-github-event": "pull_request", "x-hub-signature-256": "sha256=bad"},
            )
    assert resp.status_code == 401
