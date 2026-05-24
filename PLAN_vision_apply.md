# Plan: Vision-Guided Job Application via Remotive + LLM

## Context

LinkedIn Easy Apply automation is unreliable — DOM selectors break, bot detection fires, and the scraper currently returns 0 jobs. The new approach:

1. **Fetch** jobs from Remotive REST API (no Playwright, no selectors to break)
2. **Capture** each job's application page as full-page screenshots (Playwright, with scrolling)
3. **Plan** with Claude Vision — analyze the form screenshots, return a structured JSON action plan
4. **Execute** the plan with Playwright (fill fields, upload resume, submit)

This is LLM-driven form automation: Claude sees what a human would see and generates the instructions. Handles any ATS (Greenhouse, Lever, Workable, etc.) without hardcoded selectors.

---

## New Graph Flow

```
fetch_jobs          (Remotive API, httpx — no Playwright)
    ↓
rank_jobs           (existing LLM ranker — unchanged)
    ↓
select_next_job     (existing — unchanged)
    ↓
customize_resume    (existing — unchanged)
    ↓
generate_cover_letter  (existing — unchanged)
    ↓
capture_job_page    (NEW: navigate Remotive page → follow apply link → full-page screenshots)
    ↓
plan_application    (NEW: Claude Vision → structured JSON action plan)
    ↓
execute_application (NEW: Playwright runs the plan step by step)
    ↓
save_application    (existing — unchanged)
    ↓ (loop if more jobs)
select_next_job
```

Added as `build_remotive_graph()` in `workflow.py`. Existing `build_graph()` (LinkedIn) untouched.
`main.py` routes `run_type == "run_remotive"` to the new graph.

---

## New Files

### `portals/remotive/scraper.py`
- `fetch_jobs(prefs: dict, limit: int) -> list[dict]`
- `GET https://remotive.com/api/remote-jobs?category=software-dev&limit=100`
- Filter jobs by preferred roles (keyword match on title)
- Returns: `[{title, company, job_url (remotive page URL), description (stripped HTML), portal: "remotive"}]`
- Pure httpx — no Playwright needed

### `automation/page_capturer.py`
- `capture_apply_page(page, job_url: str, app_id: int, screenshots_dir: str) -> dict`
- Navigate to `job_url` (Remotive page)
- Find "Apply for this job" / "Apply now" link → extract href (the real ATS URL)
- Navigate to the ATS apply URL
- Take `page.screenshot(full_page=True)` → saves as `form_full_{app_id}_{ts}.png`
- If page height > 3× viewport: also take 3 viewport-scroll screenshots (top / mid / bottom) for LLM clarity
- Returns `{screenshots: list[str], apply_url: str}`

### `automation/form_planner.py`
- `plan_form(llm, screenshots: list[str], candidate: dict, resume_path: str, cover_letter_path: str) -> dict`
- Reads each screenshot, base64-encodes it
- Calls Claude Vision via LangChain `HumanMessage` with image content blocks + candidate profile text
- System prompt: "You are an expert at analyzing job application forms. Return ONLY valid JSON."
- Returns structured plan:
```json
{
  "apply_url": "https://boards.greenhouse.io/...",
  "ats_type": "greenhouse",
  "actions": [
    {"action": "fill",   "label": "First Name",    "value": "Vivak",               "hints": ["first_name", "firstName"]},
    {"action": "fill",   "label": "Email",          "value": "vk2853@gmail.com",    "hints": ["email"]},
    {"action": "upload", "label": "Resume",         "value": "{resume_path}",       "hints": ["resume"]},
    {"action": "upload", "label": "Cover Letter",   "value": "{cover_letter_path}", "hints": ["cover"]},
    {"action": "select", "label": "Work Auth",      "value": "Yes",                 "hints": ["authorization"]},
    {"action": "submit", "label": "Submit Application"}
  ],
  "notes": "Has a LinkedIn URL field and optional cover letter upload"
}
```

### `automation/plan_executor.py`
- `execute_plan(page, plan: dict, resume_path: str, cover_letter_path: str, screenshots_dir: str, app_id: int) -> dict`
- Iterates plan `actions`:
  - `fill` → try each hint as `input[name*=hint]`, `input[placeholder*=hint]`, label-adjacent input
  - `select` → `page.select_option(...)` with matching hints
  - `upload` → `input[type='file']` matched by hint or first available; `set_input_files(path)`
  - `submit` → `button:has-text(label)` or `input[type='submit']`
- After submit: `page.screenshot(full_page=True)` → `submitted_{app_id}_{ts}.png`
- Returns `{success: bool, screenshot_path: str, error: str}`

### `graph/nodes/fetch_jobs.py`
- `run(state) -> state`
- Calls `portals.remotive.scraper.fetch_jobs(prefs, limit=20)`
- Sets `state["jobs"]` (same schema as current jobs list)

### `graph/nodes/capture_job_page.py`
- `run(state) -> state`
- Opens Playwright browser via `portals.linkedin.session.get_context()`
- Calls `automation.page_capturer.capture_apply_page(page, job_url, app_id, SCREENSHOTS_DIR)`
- Sets `state["job_screenshots"]` and `state["apply_url"]`

### `graph/nodes/plan_application.py`
- `run(state) -> state`
- Builds candidate dict from `parsed_resume` + `preferences`
- Calls `automation.form_planner.plan_form(llm, screenshots, candidate, resume_path, cover_letter_path)`
- Sets `state["form_plan"]`
- Decorated with `@llm_guarded(est_calls=3)` (vision calls are heavier)

### `graph/nodes/execute_application.py`
- `run(state) -> state`
- Opens Playwright browser
- Navigates to `state["apply_url"]`
- Calls `automation.plan_executor.execute_plan(page, form_plan, resume_path, cover_letter_path, ...)`
- Sets `state["apply_result"]` (same shape as current apply_result)

---

## Modified Files

### `graph/state.py`
Add three fields:
```python
job_screenshots: list[str]   # paths to captured form screenshots
form_plan: dict              # LLM-generated action plan
apply_url: str               # resolved ATS apply URL (from page capturer)
```

### `graph/workflow.py`
Add `build_remotive_graph()` — 9-node graph as above.
Keep `build_graph()` and `build_retry_graph()` unchanged.

### `main.py`
```python
graph = (
    build_retry_graph()   if run_type == "retry_application"
    else build_remotive_graph() if run_type == "run_remotive"
    else build_graph()
)
```

---

## Key Reuse (nothing reimplemented)

| Existing | Reused in |
|---|---|
| `portals.linkedin.session.get_context()` | `capture_job_page`, `execute_application` |
| `automation.captcha_handler.save_screenshot()` | `page_capturer`, `plan_executor` |
| `automation.form_filler.fill_form()` | fallback in `plan_executor` if plan is incomplete |
| `services.llm_limiter.get_llm()` | `form_planner` (Claude Vision) |
| `services.rails_client.create_application()` | `save_application` (unchanged) |
| `rank_jobs`, `select_next_job`, `customize_resume`, `generate_cover_letter`, `save_application` | Wired into new graph unchanged |

---

## Verification

1. Start agent: `cd python-agent && .venv/bin/python main.py`
2. Push test task:
   ```bash
   redis-cli LPUSH job_queue '{"type":"run_remotive","user_id":1,"correlation_id":"test-001"}'
   ```
3. Watch logs: `[fetch_jobs]` → `[capture_job_page]` → `[plan_application]` → `[execute_application]`
4. Check `python-agent/storage/screenshots/` for form PNGs
5. Check Rails dashboard at `http://localhost:3000` for new application records
