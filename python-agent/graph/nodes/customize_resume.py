import os
from pathlib import Path
from loguru import logger

from ..state import JobAgentState
from resume_engine.customizer import customize
from resume_engine.generator import to_pdf, to_docx
from services.llm_limiter import llm_guarded

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")


@llm_guarded(est_calls=1)
def run(state: JobAgentState) -> JobAgentState:
    job = state.get("current_job")
    parsed_resume = state.get("parsed_resume", {})
    user_id = state.get("user_id", 0)
    logger.info(f"[customize_resume] starting | job={job.get('title')} @ {job.get('company')}" if job else "[customize_resume] starting | no job")

    if not job or not parsed_resume:
        logger.warning("[customize_resume] skipping — missing job or parsed_resume")
        return state

    try:
        logger.info("[customize_resume] customizing resume via LLM")
        customized = customize(parsed_resume, job)
        job_slug = job.get("title", "job").lower().replace(" ", "_")[:30]
        out_dir = Path(STORAGE_DIR) / "resumes" / str(user_id) / "customized"
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = to_pdf(customized, str(out_dir / f"{job_slug}.pdf"))
        to_docx(customized, str(out_dir / f"{job_slug}.docx"))

        state["customized_resume_path"] = pdf_path
        logger.info(f"[customize_resume] resume saved | path={pdf_path}")
    except Exception as e:
        logger.error(f"[customize_resume] error | {e}")
        state.setdefault("errors", []).append({"step": "customize_resume", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "customize_resume", "status": "done"})
    logger.info("[customize_resume] done")
    return state
