# Job Agent

A local-first AI job application agent. It searches LinkedIn for relevant jobs, customizes your resume for each role, generates cover letters, and applies automatically — all running on your own machine.

---

## How it works

```
Rails API (scheduler + DB + tracking)
    │
    └── Sidekiq cron job (09:00 daily)
            │
            └── LPUSH → Redis queue → BRPOP
                                          │
                                    Python Agent (LangGraph)
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                   Resume Engine    LinkedIn Bot    LLM Limiter
                   (parse/customize) (Playwright)  (quota guard)
```

**Rails** handles scheduling, the database, file management, and API endpoints.
**Python** handles the AI workflow: parsing resumes, ranking jobs, customizing documents, and driving the browser.
**Redis** is the queue between them. One `LPUSH` from Sidekiq starts a full agent run.

---

## Prerequisites

- Ruby 3.3+
- Python 3.12+ (3.14 works)
- Node.js 18+ (for Playwright)
- Redis 7 (via Docker or local install)
- Docker (for Redis, optional)

---

## Local Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd job-agent
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```bash
OPENAI_API_KEY=sk-...          # or use ANTHROPIC_API_KEY + set LLM_PROVIDER=anthropic
LINKEDIN_EMAIL=you@example.com
LINKEDIN_PASSWORD=yourpassword

MAX_LLM_API_CALLS_PER_DAY=50   # adjust to your budget
MAX_JOBS_TO_APPLY_PER_DAY=10
```

### 3. Start Redis

```bash
docker compose up -d redis
```

Or if you have Redis installed locally:

```bash
redis-server
```

### 4. Set up the Rails API

```bash
cd rails-api
bundle install
bin/rails db:setup        # creates DB, runs migrations, seeds default user
```

The seed creates a user with your email (`vk2853@gmail.com`) and default job preferences. Edit `db/seeds.rb` to change preferences before seeding.

### 5. Set up the Python agent

```bash
cd python-agent
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m playwright install chromium
```

### 6. Upload your resume

Start the Rails server first (see Running below), then:

```bash
curl -X POST http://localhost:3000/api/v1/resumes \
  -F "file=@/path/to/your/resume.pdf"
```

Or `resume.docx` — both are supported.

---

## Running

Open three terminal tabs.

**Tab 1 — Rails API:**
```bash
cd rails-api
bin/rails s -p 3000
```

**Tab 2 — Sidekiq:**
```bash
cd rails-api
bundle exec sidekiq -C config/sidekiq.yml
```

**Tab 3 — Python Agent:**
```bash
cd python-agent
.venv/bin/python main.py
```

Or use the Procfile (single command):
```bash
# Install foreman: gem install foreman
cd job-agent
foreman start -f Procfile.dev
```

---

## Dashboard

Open `http://localhost:3000` in your browser to see:
- Application stats (applied, failed, pending, etc.)
- LLM usage for today
- Recent applications with status
- Start Automation button

---

## Trigger a run manually

**Via the dashboard:** click "Start Automation Now" at `http://localhost:3000`

**Via curl:**
```bash
curl -X POST http://localhost:3000/api/v1/automation/start
```

Or push directly to the Redis queue:

```bash
redis-cli LPUSH job_queue '{"type":"run_automation","user_id":1,"correlation_id":"test-1"}'
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/resumes` | Upload resume (multipart `file`) |
| `GET` | `/api/v1/resumes/:id/download` | Download customized resume |
| `POST` | `/api/v1/automation/start` | Trigger a run immediately |
| `GET` | `/api/v1/applications` | List all applications |
| `GET` | `/api/v1/applications/:id` | Get single application with job details |
| `POST` | `/api/v1/applications/:id/retry` | Retry a failed application |
| `GET` | `/api/v1/logs` | Recent automation logs |
| `GET` | `/api/v1/llm_usage` | Today's LLM usage vs limit |
| `GET` | `/api/v1/users/:id/preferences` | Get job preferences |
| `PUT` | `/api/v1/preferences` | Update job preferences |

---

## Job Preferences

Update what roles and locations to target:

```bash
curl -X PUT http://localhost:3000/api/v1/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "desired_roles": ["Senior Backend Engineer", "AI Engineer"],
    "preferred_stack": ["Ruby on Rails", "Python", "LangGraph"],
    "locations": ["Remote", "San Francisco"],
    "remote_preference": "remote",
    "salary_min": 150000,
    "salary_max": 250000,
    "years_experience": 8
  }'
```

---

## LLM Usage Limit

The agent tracks every LLM call and stops when the daily limit is hit.

```bash
# Check current usage
curl http://localhost:3000/api/v1/llm_usage
# {"date":"2026-05-10","limit":50,"used":12,"remaining":38,"quota_exceeded":false}
```

Change the limit without restarting:

```bash
# Edit .env
MAX_LLM_API_CALLS_PER_DAY=100
# Then restart the Rails server and Python agent
```

When the limit is hit, pending applications get status `paused_quota` and will be retried the next day.

---

## LinkedIn First Login

The first time you run, LinkedIn will require you to log in manually (and possibly solve a CAPTCHA or complete MFA). Set `PLAYWRIGHT_HEADLESS=false` in `.env` so the browser window is visible:

```bash
PLAYWRIGHT_HEADLESS=false
```

After a successful login the session is saved to `python-agent/.sessions/linkedin/<user_id>.json` and reused on all subsequent runs. Once the session is stable you can set `PLAYWRIGHT_HEADLESS=true`.

---

## Retrying Failed Applications

Applications fail for common reasons: captcha, timeout, unsupported form. They are retried automatically every 30 minutes (up to 3 attempts). To retry one immediately:

```bash
curl -X POST http://localhost:3000/api/v1/applications/42/retry
```

Check why an application failed:

```bash
curl http://localhost:3000/api/v1/applications/42
# Shows: status, error_message, failed_step, screenshot_path
```

Screenshots are saved to `rails-api/storage/screenshots/`.

---

## Monitoring

```bash
# Tail automation logs
curl http://localhost:3000/api/v1/logs | python3 -m json.tool

# Watch the SQLite DB directly
sqlite3 rails-api/storage/development.sqlite3 \
  "SELECT a.id, j.title, j.company, a.status, a.error_message
   FROM applications a JOIN jobs j ON a.job_id = j.id
   ORDER BY a.created_at DESC LIMIT 20;"
```

Sidekiq web UI (add to Gemfile or access via Rails routes if configured):

```bash
# Sidekiq stats via CLI
bundle exec sidekiq-client stats
```

---

## Project Structure

```
job-agent/
├── .env                        # your secrets (gitignored)
├── .env.example                # template
├── docker-compose.yml          # Redis only
├── Procfile.dev                # rails + sidekiq + python agent
│
├── rails-api/
│   ├── app/
│   │   ├── controllers/api/v1/ # all API endpoints
│   │   ├── controllers/        # dashboard + applications (web UI)
│   │   ├── views/              # HTML frontend (dashboard, applications)
│   │   ├── models/             # User, Resume, Job, Application, LlmApiUsage, AutomationLog
│   │   ├── services/           # AgentDispatcher, AgentJwt
│   │   └── sidekiq/            # DailyAutomationJob, RetryFailedApplicationsJob, LlmQuotaInitJob
│   ├── config/
│   │   ├── initializers/       # redis.rb, sidekiq.rb, cors.rb, sqlite_wal.rb
│   │   └── sidekiq.yml
│   └── db/
│       ├── migrate/            # 7 migrations
│       └── seeds.rb
│
└── python-agent/
    ├── main.py                 # Redis BRPOP worker loop
    ├── graph/
    │   ├── state.py            # JobAgentState TypedDict
    │   ├── workflow.py         # LangGraph StateGraph (11 nodes)
    │   └── nodes/              # one file per node
    ├── portals/
    │   └── linkedin/           # session.py, scraper.py, applier.py
    ├── services/
    │   ├── llm_limiter.py      # @llm_guarded decorator + get_llm()
    │   ├── rails_client.py     # HTTP calls back to Rails
    │   └── redis_client.py     # BRPOP helper
    ├── resume_engine/
    │   ├── parser.py           # PDF/DOCX → structured JSON via LLM
    │   ├── customizer.py       # tailor resume to job description
    │   └── generator.py        # export to PDF (ReportLab) and DOCX
    ├── automation/
    │   ├── form_filler.py      # fill any web form; LLM fallback for unknown fields
    │   └── captcha_handler.py  # detect captcha, save screenshot, pause
    └── prompts/                # all LLM prompt templates
```

---

## Adding a New Job Portal

1. Create `python-agent/portals/<portal_name>/` with `session.py`, `scraper.py`, `applier.py` following the `BasePortal` interface in `portals/base_portal.py`.
2. Register in `graph/nodes/search_jobs.py` and `graph/nodes/apply_job.py` — add a branch on `job["portal"]`.
3. Add credentials to `.env` (e.g. `NAUKRI_EMAIL`, `NAUKRI_PASSWORD`).

No changes to core graph logic needed.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required if `LLM_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | — | Required if `LLM_PROVIDER=anthropic` |
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `LINKEDIN_EMAIL` | — | Your LinkedIn login email |
| `LINKEDIN_PASSWORD` | — | Your LinkedIn login password |
| `MAX_LLM_API_CALLS_PER_DAY` | `50` | Daily LLM call budget |
| `MAX_JOBS_TO_APPLY_PER_DAY` | `10` | Max applications per daily run |
| `PLAYWRIGHT_HEADLESS` | `false` | Set `true` after first login |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `RAILS_API_BASE` | `http://localhost:3000` | Rails server URL (used by Python) |
| `AGENT_SHARED_SECRET` | `change_me` | JWT secret for Rails↔Python auth |
| `JOB_QUEUE_NAME` | `job_queue` | Redis list name for task queue |
| `STORAGE_DIR` | `storage` | Root dir for resumes, cover letters, screenshots |

---

## Troubleshooting

**Python agent can't connect to Rails:**
Make sure the Rails server is running on port 3000. The agent will log errors but keep retrying from the queue.

**LinkedIn login fails or MFA required:**
Run with `PLAYWRIGHT_HEADLESS=false`, complete the login manually in the browser window. The session will be saved automatically.

**`No module named 'X'` in Python:**
The venv was built with `--no-deps` for some packages. Install the missing module:
```bash
python-agent/.venv/bin/pip install <module>
```

**`Redis::CannotConnectError`:**
Start Redis: `docker compose up -d redis`

**Applications stuck at `pending`:**
Check the Python agent is running and connected to Redis. Push a test payload:
```bash
redis-cli LPUSH job_queue '{"type":"run_automation","user_id":1,"correlation_id":"debug-1"}'
```
Then tail Python agent stdout.
