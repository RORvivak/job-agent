# Python Agent

The AI workflow engine for the job agent. It listens on a Redis queue, processes tasks using a LangGraph state machine, and reports results back to the Rails API.

---

## How it works

```
Redis queue (BRPOP)
      │
      ▼
   main.py
      │
      ├── run_automation  → build_graph()
      └── retry_application → build_retry_graph()
            │
            ▼
      LangGraph nodes (see graph/)
            │
            ▼
      Rails API (HTTP callbacks)
```

---

## Folder Structure

```
python-agent/
├── main.py                  # entry point — Redis worker loop
├── login.py                 # one-time LinkedIn login helper
│
├── graph/
│   ├── state.py             # JobAgentState — shared data between nodes
│   ├── workflow.py          # builds the LangGraph, connects nodes
│   └── nodes/
│       ├── collect_preferences.py    # fetch user prefs from Rails
│       ├── parse_resume.py           # PDF/DOCX → structured JSON
│       ├── search_jobs.py            # scrape LinkedIn job listings
│       ├── rank_jobs.py              # LLM scores jobs by relevance
│       ├── customize_resume.py       # LLM tailors resume to job
│       ├── generate_cover_letter.py  # LLM writes cover letter
│       ├── apply_job.py              # Playwright submits application
│       ├── external_portal_handler.py# handles external job portals
│       ├── save_application.py       # saves result to Rails
│       ├── retry_failed_application.py # loads failed app for retry
│       └── error_handler.py          # saves error to Rails
│
├── portals/
│   ├── base_portal.py        # ApplyResult dataclass + base interface
│   └── linkedin/
│       ├── session.py        # browser launch + login + session save
│       ├── scraper.py        # search LinkedIn, extract job cards
│       └── applier.py        # click Easy Apply, fill form, submit
│
├── resume_engine/
│   ├── parser.py             # extract structured data from resume file
│   ├── customizer.py         # rewrite resume sections for a job
│   └── generator.py          # export resume to PDF/DOCX
│
├── services/
│   ├── llm_limiter.py        # daily LLM quota guard
│   ├── rails_client.py       # all HTTP calls to Rails API
│   └── redis_client.py       # BRPOP helper
│
├── automation/
│   ├── form_filler.py        # fill any web form field
│   └── captcha_handler.py    # detect captcha, save screenshot
│
├── prompts/
│   ├── resume_prompt.py      # parse + customize resume prompts
│   ├── cover_letter_prompt.py
│   ├── job_ranker_prompt.py
│   └── form_filler_prompt.py
│
└── .sessions/
    └── linkedin/
        └── 1.json            # saved LinkedIn session (auto-created)
```

---

## Workflow Diagrams

### Main Graph (daily run)

```
START
  │
  ▼
collect_preferences          fetch job prefs + resume path from Rails
  │
  ▼
parse_resume ──── quota exceeded? ──────────────────────────────► END
  │ ok
  ▼
search_jobs                  scrape LinkedIn job listings
  │
  ▼
rank_jobs ────── quota exceeded? ──────────────────────────────► END
  │ ok
  │
  │◄─────────────────────────────────────────────────────────────┐
  ▼                                                              │ more jobs?
customize_resume             tailor resume to current job        │
  │                                                              │
  ▼                                                              │
generate_cover_letter ──── quota exceeded? ───────────────────► END
  │ ok                                                           │
  ▼                                                              │
apply_job                                                        │
  │          │           │                                       │
success   external     error                                     │
  │          │           │                                       │
  │   external_portal    │                                       │
  │   _handler           │                                       │
  │    │      │          │                                       │
  │  save   error        │                                       │
  ▼    ▼      ▼          ▼                                       │
save_application      error_handler                              │
  └──────────────────────┘                                       │
            │ more jobs? ────────────────────────────────────────┘
            │ done
            ▼
           END
```

### Retry Graph (single failed application)

```
START
  │
  ▼
retry_failed_application     load failed app + job from Rails
  │
  ▼
customize_resume
  │
  ▼
generate_cover_letter
  │
  ▼
apply_job
  │          │           │
success   external     error
  │          │           │
  │   external_portal    │
  │   _handler           │
  │    │      │          │
  │  save   error        │
  ▼    ▼      ▼          ▼
save_application      error_handler
  │                       │
  ▼                       ▼
 END                     END
```

---

## Setup

```bash
cd python-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

---

## First-time LinkedIn Login

Run this once to log in and save the session:

```bash
.venv/bin/python login.py
```

A browser opens → log in manually → press Enter → session saved to `.sessions/linkedin/1.json`. The agent reuses this session on every run.

---

## Running

```bash
cd python-agent
.venv/bin/python main.py
```

The agent blocks and waits for tasks from Redis. Trigger a run from Rails:

```bash
curl -X POST http://localhost:3000/api/v1/automation/start
```

Or push directly to Redis:

```bash
redis-cli LPUSH job_queue '{"type":"run_automation","user_id":1,"correlation_id":"test-1"}'
```

---

## State

Every node receives and returns `JobAgentState` (a dict). State grows as nodes add to it:

| Field | Set by | Used by |
|-------|--------|---------|
| `user_id` | main.py | all nodes |
| `preferences` | collect_preferences | search_jobs, rank_jobs |
| `resume_path` | collect_preferences | parse_resume |
| `parsed_resume` | parse_resume | customize_resume |
| `jobs` | search_jobs | rank_jobs |
| `ranked_jobs` | rank_jobs | workflow loop |
| `current_job` | workflow loop | customize_resume, apply_job |
| `customized_resume_path` | customize_resume | apply_job |
| `cover_letter_path` | generate_cover_letter | apply_job |
| `apply_result` | apply_job | routing, save_application |
| `errors` | any node | error_handler, routing |

---

## Adding a New Job Portal

1. Create `portals/<name>/session.py`, `scraper.py`, `applier.py` following the LinkedIn files as reference
2. `applier.py` must return an `ApplyResult` from `portals/base_portal.py`
3. Register in `graph/nodes/search_jobs.py` and `graph/nodes/apply_job.py` — branch on `job["portal"]`
4. Add credentials to `.env`
