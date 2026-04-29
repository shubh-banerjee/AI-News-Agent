# AI News Agent

Daily AI news digest bot that fetches the latest Google News AI headlines, summarizes them with NVIDIA's OpenAI-compatible API, and posts the digest to Slack.

## Repo Structure

- `agent.py` — fetches news, summarizes articles, sends Slack message
- `requirements.txt` — Python dependencies
- `.env.example` — local environment variable template
- `.github/workflows/daily.yml` — GitHub Actions daily automation

## Local Run

1. Copy `.env.example` to `.env`
2. Fill in:
   - `OPENAI_API_KEY`
   - `SLACK_WEBHOOK_URL`
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run:

```bash
python3 agent.py
```

## GitHub Actions Setup

### 1. Push this project to GitHub

Create a new GitHub repository, then push this folder.

### 2. Add GitHub Actions secrets

In your GitHub repository:

1. Open `Settings`
2. Open `Secrets and variables` → `Actions`
3. Click `New repository secret`
4. Add:
   - `OPENAI_API_KEY`
   - `SLACK_WEBHOOK_URL`

### 3. Workflow schedule

The workflow in `.github/workflows/daily.yml` runs:

- Every day at `03:30 UTC`, which is `09:00 AM IST`
- Manually via `Actions` → `Daily AI News` → `Run workflow`

## Workflow Behavior

GitHub Actions will:

1. Check out the repository
2. Set up Python 3.10
3. Install dependencies
4. Run `agent.py`
5. Send the Slack digest using repository secrets

## Security Notes

- Do not commit your real `.env`
- Store production secrets only in GitHub Actions secrets
- `.env.example` is safe to commit because it contains placeholders only
# AI-News-Agent
