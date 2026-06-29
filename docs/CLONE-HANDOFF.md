# Session Handoff

Last updated: 2026-06-30 KST

This file is tracked so a fresh clone on another Mac can continue the project without relying on local ignored notes.

## Project

- Local path used on the original Mac: `/Users/sungminkim/Desktop/nomad quiz`
- GitHub repo: `https://github.com/twsftrp-arch/life-coach-agent`
- Main branch: `main`
- Streamlit entrypoint: `app.py`
- Production app: `https://personal-agents.streamlit.app/`
- Share/OG page: `https://twsftrp-arch.github.io/life-coach-agent/`

## Current Product State

This repo now runs a Streamlit Personal Agent Hub with three modes:

- Life Coach: `https://personal-agents.streamlit.app/?agent=life_coach`
- Movie Agent: `https://personal-agents.streamlit.app/?agent=movie`
- Restaurant Bot: `https://personal-agents.streamlit.app/?agent=restaurant`

Root `/` opens the agent selection hub. The hub cards should show only the primary start action, not duplicate direct-link buttons.

## Feature Map

### Life Coach

- OpenAI Agents SDK `Agent` + `Runner`
- DeepSeek through OpenAI-compatible Chat Completions
- Streamlit chat UI using `st.chat_input` and `st.chat_message`
- `SQLiteSession` for SDK session memory
- Supabase-backed login, session persistence, chat restore, chat list, rename/delete, and read-only share links
- Google OAuth via Supabase Auth
- Persistent app auth cookie so refresh keeps the login state
- Private Supabase Storage bucket for goal files: `life-coach-goal-files`
- Goal file search tool implemented as a local `function_tool`
- Web search tool
- Image generation tool
- Life Coach-specific sidebar settings only in Life Coach mode

### Movie Agent

- Nomad Movies API tools:
  - `get_popular_movies`
  - `get_movie_details`
  - `get_movie_credits`
- Web-search fallback when the movie API fails
- Streaming responses and visible run evidence/logs

### Restaurant Bot

- Agents:
  - Triage Agent
  - Menu Agent
  - Order Agent
  - Reservation Agent
  - Complaints Agent
- Uses OpenAI Agents SDK handoffs.
- Input guardrail rejects:
  - off-topic, non-restaurant questions
  - inappropriate language
- Output guardrail checks:
  - professional and respectful response
  - no internal information leakage such as API keys, tokens, system prompts, or internal instructions
- Complaint examples should hand off to Complaints Agent.

Separate assignment repo for Restaurant Bot Guardrails + Complaints:

- Repo: `https://github.com/twsftrp-arch/restaurant-bot-handoffs`
- Submission commit: `28e50e1c05f381517ac70a9a3dc5aea2208e402b`
- Commit link: `https://github.com/twsftrp-arch/restaurant-bot-handoffs/commit/28e50e1c05f381517ac70a9a3dc5aea2208e402b`

## Latest Known Main Repo Commits

As of this handoff, recent commits include:

- `7fb8161` Force Streamlit full rebuild via requirements marker
- `6781e0c` Document movie web-search fallback and trigger redeploy
- `bb2518f` Fall back to web search when movie API fails
- `310ba07` Retry movie API calls and surface fetch errors
- `7acd7a3` Hide stale Google login error after auth restore
- `54bf57d` Show live run log and sources for Movie and Restaurant
- `3d5f8e0` Stream Movie and Restaurant responses like Life Coach
- `3f3bd75` Add restaurant guardrails and complaints agent

After cloning, run `git log --oneline -8` to verify the current remote state because this list may become stale.

## Required Local Secrets

Do not print secret values. Env var names are safe to mention.

The app can read secrets from environment variables or `.streamlit/secrets.toml`. The local secrets file is intentionally ignored by git.

Expected names:

```toml
DEEPSEEK_API_KEY = "..."
SUPABASE_URL = "..."
SUPABASE_ANON_KEY = "..."
SUPABASE_SERVICE_ROLE_KEY = "..."
APP_BASE_URL = "http://localhost:8501"
```

For deployed Streamlit Cloud, `APP_BASE_URL` should match the deployment URL:

```toml
APP_BASE_URL = "https://personal-agents.streamlit.app"
```

The app may also reuse `DEEPSEEK_API_KEY` from `~/Documents/movie-agent/.env` if present.

## GitHub Account Rule

Sungmin uses multiple GitHub accounts.

- Push/manage this repo with: `twsftrp-arch`
- Restore the usual account after push: `trinity-mathslab`
- Do not force push.
- Do not commit/push/deploy without explicit approval.

Useful checks:

```bash
gh auth status
git status --short --branch
git remote -v
```

If push is explicitly approved:

```bash
gh auth switch -u twsftrp-arch
git push origin main
gh auth switch -u trinity-mathslab
```

## Clone And Run On A New Mac

```bash
cd ~/Desktop
git clone https://github.com/twsftrp-arch/life-coach-agent.git "nomad quiz"
cd "nomad quiz"
git status --short --branch
git log --oneline -8
```

Run locally:

```bash
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
uv run --python 3.12 --with-requirements requirements.txt streamlit run app.py
```

Headless smoke:

```bash
uv run --python 3.12 --with-requirements requirements.txt streamlit run app.py \
  --server.headless true --server.port 8765
```

Health endpoint:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8765/_stcore/health
```

## Verification Checklist

Before changing code, check:

```bash
python3 -m py_compile app.py
git diff --check
git status --short --branch
```

Recommended app smoke paths:

- Hub root renders three cards.
- Life Coach can open with `?agent=life_coach`.
- Movie Agent can open with `?agent=movie`.
- Restaurant Bot can open with `?agent=restaurant`.
- Restaurant off-topic prompt such as `인생의 의미가 뭘까?` triggers input guardrail.
- Restaurant complaint prompt such as `음식이 차갑고 직원도 불친절했어` hands off to Complaints Agent.

External `https://personal-agents.streamlit.app/_stcore/health` can return Streamlit viewer-auth `303`. Do not treat that alone as an app crash.

## Security Notes

- Never print, summarize, commit, or log secret values.
- `.streamlit/secrets.toml`, `.env`, local DB files, and `__pycache__` are ignored.
- Earlier local debugging may have exposed sensitive values in tool output. Values were not intentionally committed, but rotating DeepSeek and Supabase service-role credentials after the assignment is still recommended.

## Current Handoff Status

- Main repo was clean and synced before adding this tracked handoff file.
- This file was added so a fresh clone can continue with project context.
- Next agent should read this file and `README.md` first, then report current `git status`, latest commits, active GitHub account, and whether local secrets are needed.

STATUS: done — tracked clone handoff created for continuing this repo on a clean Mac.
