# AI Code Reviewer

An AI-powered code review assistant that integrates with GitHub pull requests to provide intelligent feedback on code quality, architecture, and security.

## How It Works

1. You open or push to a Pull Request on GitHub
2. GitHub sends a webhook event to this server
3. The server fetches the PR's unified diff
4. OpenAI GPT-4o analyzes the diff and generates a structured review
5. The review is automatically posted as a comment on your PR 

---

## Project Structure

```
Ai-Code-Reviewer/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── routes_github.py     # Webhook receiver + signature verification
│   └── config.py            # Environment variable management
├── worker/
│   ├── __init__.py
│   └── tasks.py             # Diff fetching, OpenAI call, GitHub comment posting
├── tests/
│   └── test_webhook.py      # pytest test suite
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Chynaadams1/Ai-Code-Reviewer.git
cd Ai-Code-Reviewer
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|---|---|
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens (need `repo` or `public_repo` scope) |
| `GITHUB_WEBHOOK_SECRET` | You choose this string when registering the webhook on GitHub |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |

### 3. Run the server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Exposing to GitHub (local dev)

GitHub needs a public URL to send webhooks. Use [ngrok](https://ngrok.com):

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok.io` URL for the next step.

---

## Registering the GitHub Webhook

1. Go to your repo → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL:** `https://your-cloudflare-url.trycloudflare.com/webhook/github`
3. **Content type:** `application/json`
4. **Secret:** same value as `GITHUB_WEBHOOK_SECRET` in your `.env`
5. **Events:** Select "Let me select individual events" → check **Pull requests** only
6. Click **Add webhook**

> 💡 To get a free public URL, run: `npx cloudflared tunnel --url http://localhost:8001`
> Copy the `https://...trycloudflare.com` URL it generates.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests mock OpenAI and GitHub — no API keys needed.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/status` | Health check |
| `POST` | `/webhook/github` | GitHub webhook receiver |

---

## Example PR Review Output

```
## 🤖 AI Code Review  (Score: 7/10)

### Summary
The changes introduce a new auth module with JWT support. Logic is mostly sound
but there are some security and error-handling concerns worth addressing.

### ✅ Positives
- Good separation of concerns between token creation and validation
- Consistent use of type hints throughout

### ⚠️ Issues
| Severity | File | Line | Issue |
|---|---|---|---|
| 🔴 Critical | auth/jwt.py | 42 | Secret key is hardcoded — use an environment variable |
| 🟡 Warning | auth/middleware.py | 18 | Missing exception handling on token decode |
| 🔵 Suggestion | auth/jwt.py | 10 | Consider adding token expiry validation |

### 💡 Recommendations
Move the JWT secret to an environment variable immediately. Add try/except
around `jwt.decode()` to handle expired/invalid tokens gracefully.
```
