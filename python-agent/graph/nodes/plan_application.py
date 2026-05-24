from loguru import logger

from ..state import JobAgentState
from services.llm_limiter import get_llm, llm_guarded
from automation.form_planner import plan_form


@llm_guarded(est_calls=3)
def run(state: JobAgentState) -> JobAgentState:
    screenshots = state.get("job_screenshots", [])
    parsed = state.get("parsed_resume", {})
    prefs = state.get("preferences", {})
    resume_path = state.get("customized_resume_path") or state.get("resume_path", "")
    cover_letter_path = state.get("cover_letter_path", "")

    candidate = {
        "name": parsed.get("contact", {}).get("name", ""),
        "email": parsed.get("contact", {}).get("email", ""),
        "phone": parsed.get("contact", {}).get("phone", ""),
        "linkedin": parsed.get("contact", {}).get("linkedin", ""),
        "github": parsed.get("contact", {}).get("github", ""),
        "location": parsed.get("contact", {}).get("location", ""),
        "years_experience": prefs.get("years_experience", ""),
        "expected_salary": prefs.get("salary_max", ""),
    }

    logger.info(f"[plan_application] starting | screenshots={len(screenshots)}")
    llm = get_llm()
    plan = plan_form(llm, screenshots, candidate, resume_path, cover_letter_path)
    state["form_plan"] = plan
    logger.info(f"[plan_application] done | ats={plan.get('ats_type')} actions={len(plan.get('actions', []))}")
    state.setdefault("step_log", []).append({"step": "plan_application", "status": "done"})
    return state
