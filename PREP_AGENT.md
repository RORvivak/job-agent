# Prep-Only Agent + Human-Apply Dashboard

## Overview

The agent runs daily, fetches and ranks jobs, customizes the resume and generates a cover letter for each one, then saves everything as `ready_to_apply`. The user reviews the dashboard, opens the job link, downloads their documents, applies manually, and checks the checkbox to mark it done.

---

## Python Agent

### Deleted nodes (automated apply — removed entirely)
- `graph/nodes/apply_job.py`
- `graph/nodes/external_portal_handler.py`
- `graph/nodes/capture_job_page.py`
- `graph/nodes/plan_application.py`
- `graph/nodes/execute_application.py`
- `graph/nodes/retry_failed_application.py`
- `automation/page_capturer.py`
- `automation/plan_executor.py`
- `automation/form_planner.py`

### Graph (`graph/workflow.py`)

```
collect_preferences → parse_resume → fetch_jobs → rank_jobs
→ select_next_job → customize_resume → generate_cover_letter → save_application
→ [loop back to select_next_job if more jobs, else END]
```

- `error_handler` wired in for LLM quota failures on `customize_resume` and `generate_cover_letter`
- `build_prep_graph(use_remotive=True)` — primary, uses Remotive REST API
- `build_graph()` — fallback, uses LinkedIn scraper
- `main.py` routes `run_prep` / `run_automation` → `build_prep_graph()`

### `graph/nodes/save_application.py`
- Always sets status `ready_to_apply`
- Saves `resume_path` and `cover_letter_path`
- Resets `application_id` to `None` so the next loop iteration creates a fresh record

### `graph/state.py`
Removed fields: `job_screenshots`, `form_plan`, `apply_url`, `apply_result`

---

## Rails Dashboard

### Model (`app/models/application.rb`)
Added `ready_to_apply` to `STATUSES`.

### Routes (`config/routes.rb`)
```ruby
resources :applications, only: [:index, :show] do
  post :retry,                on: :member
  post :mark_applied,         on: :member
  get  :download_resume,      on: :member
  get  :download_cover_letter, on: :member
end
```

### Controller (`app/controllers/applications_controller.rb`)
- `mark_applied` — sets status `applied` + `applied_at: Time.current`, redirects to dashboard
- `download_resume` — serves the customized resume PDF via `send_file`
- `download_cover_letter` — serves the cover letter PDF via `send_file`

### Agent callback (`app/controllers/api/v1/agent_callback_controller.rb`)
`create_application` event now sets `status: "ready_to_apply"` instead of `"running"`.

### Dashboard table (`app/views/dashboard/index.html.erb`)

| # | Title | Company | Apply | Resume | Cover Letter | Status | Applied? | Applied At |
|---|---|---|---|---|---|---|---|---|
| id | title | company | `Apply →` (opens job URL) | `Resume ↓` (download) | `Cover Letter ↓` (download) | badge | checkbox | timestamp |

- **Applied?** — checkbox form POSTing to `mark_applied_application_path` when status is `ready_to_apply`; checked + disabled when status is `applied`

---

## Queue payload

```json
{ "type": "run_prep", "user_id": 1 }
```

Push to Redis:
```
docker exec job-agent-redis-1 redis-cli LPUSH job_queue '{"type":"run_prep","user_id":1}'
```
