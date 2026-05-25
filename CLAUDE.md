# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Local-first AI job application agent. Rails 8 API handles scheduling, persistence, and the web dashboard. A Python LangGraph agent handles the AI workflow (resume parsing, job ranking, resume customization, cover letter generation, browser-driven application). Redis is the only coupling between them — Rails pushes a JSON task to a Redis list; Python BRPOP-blocks on that list.

## Commands

### Rails API (`rails-api/`)
```bash
bundle install
bin/rails db:setup        # create DB, run migrations, seed default user
bin/rails s -p 3000       # start server
bundle exec sidekiq -C config/sidekiq.yml  # start background jobs
bin/rubocop               # lint
bin/rails test            # run tests
bin/rails test test/models/application_test.rb  # single test file
```

### Python Agent (`python-agent/`)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
.venv/bin/python main.py  # start agent (blocks on Redis)
.venv/bin/python login.py # one-time LinkedIn session capture
```

### Full stack (from repo root)
```bash
docker compose up -d redis         # Redis only
foreman start -f Procfile.dev      # rails + sidekiq + python agent
```

## Architecture

### Communication pattern
Rails dispatches work by calling `AgentDispatcher.dispatch_run(user_id)`, which `LPUSH`es a JSON payload onto `job_queue` (Redis). The Python agent `BRPOP`s from that queue in `main.py`, deserializes the payload into an initial `JobAgentState`, and invokes the compiled LangGraph.

The Python agent never writes to the database directly — it reports back via HTTP to `POST /api/v1/agent/callback` (authenticated by a shared HS256 JWT via `AGENT_SHARED_SECRET`). The callback controller (`AgentCallbackController`) dispatches on `event`: `log`, `status_update`, `llm_usage`, `upsert_job`, `create_application`.

### LangGraph workflow (`python-agent/graph/`)
`workflow.py` defines two compiled graphs. `main.py` selects based on the Redis payload's `type` field:
- `run_prep` or `run_automation` → `build_prep_graph(use_remotive=True)` — fetches jobs from Remotive's public REST API (no auth)
- any other type → `build_graph()` which calls `build_prep_graph(use_remotive=False)` — uses the LinkedIn Playwright scraper (requires saved session)

Node execution order: `collect_preferences → parse_resume → fetch_jobs/search_jobs → rank_jobs → [loop: select_next_job → customize_resume → generate_cover_letter → save_application]`

Conditional edges check `state["errors"]` for `llm_quota_exceeded` to short-circuit to `END`. The per-job loop continues while `state["ranked_jobs"]` is non-empty (each iteration pops the next job via `select_next_job`).

`JobAgentState` is a `TypedDict` — nodes receive and return the full state dict; fields accumulate across nodes.

### LLM quota guard
`@llm_guarded(est_calls=N)` decorator (in `services/llm_limiter.py`) wraps any node that calls an LLM. It checks `GET /api/v1/llm_usage` before invoking and calls `POST /api/v1/agent/callback` with `event=llm_usage` after. `get_llm()` in the same file returns either a `ChatOpenAI` or `ChatAnthropic` instance based on `LLM_PROVIDER` env var, cached per provider.

### Rails background jobs (`rails-api/app/sidekiq/`)
- `DailyAutomationJob` — triggers a full run for each active user (queues Redis task via `AgentDispatcher`)
- `RetryFailedApplicationsJob` — retries `Application` records where `status=failed` and `retry_count < 3`
- `LlmQuotaInitJob` — resets the daily LLM usage counter

Sidekiq queues: `automation` and `default`. Cron schedule is managed via the Sidekiq cron configuration. Sidekiq web UI is mounted at `http://localhost:3000/sidekiq`.

### Data model (SQLite via Active Storage)
Key models: `User`, `Resume` (has Active Storage attachments), `UserPreference`, `Job` (unique on `portal+job_url`), `Application` (status machine), `AutomationLog`, `LlmApiUsage`.

Application statuses: `pending`, `running`, `ready_to_apply`, `applied`, `failed`, `paused_quota`, `paused_captcha`, `skipped`.

Resumes and cover letters are stored both as local files (referenced by path in `python-agent/storage/`) and uploaded to Rails via `POST /api/v1/applications/:id/upload_resume` / `upload_cover_letter`.

### Adding a new job portal
1. Create `python-agent/portals/<name>/` with `session.py`, `scraper.py`, `applier.py`
2. `applier.py` must return `ApplyResult` from `portals/base_portal.py`
3. Register in `graph/nodes/search_jobs.py` and `graph/nodes/apply_job.py` — branch on `job["portal"]`
4. Add credentials to `.env`

## Key environment variables
| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `openai` (default) or `anthropic` |
| `AGENT_SHARED_SECRET` | JWT secret for Rails↔Python auth |
| `PLAYWRIGHT_HEADLESS` | Set `false` for first LinkedIn login |
| `MAX_LLM_API_CALLS_PER_DAY` | Daily LLM call budget (checked via Rails) |
| `RAILS_API_BASE` | Python agent uses this to call back to Rails (default `http://localhost:3000`) |
| `JOB_QUEUE_NAME` | Redis list name (default `job_queue`) |
| `AGENT_MAX_WORKERS` | Python agent ThreadPoolExecutor concurrency (default `2`) |
