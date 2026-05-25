from loguru import logger

from ..state import JobAgentState
from services.rails_client import update_application, create_application, log_step, upload_resume, upload_cover_letter


def run(state: JobAgentState) -> JobAgentState:
    app_id = state.get("application_id")
    correlation_id = state.get("correlation_id", "")
    job = state.get("current_job", {})
    user_id = state.get("user_id", 0)
    logger.info(f"[save_application] starting | job={job.get('title')} @ {job.get('company')} app_id={app_id}")

    if not app_id and job:
        logger.info("[save_application] creating new application record")
        app_id = create_application(user_id, job, correlation_id)
        state["application_id"] = app_id
        logger.info(f"[save_application] application created | app_id={app_id}")

    if app_id:
        resume_path = state.get("customized_resume_path", "")
        cover_letter_path = state.get("cover_letter_path", "")

        if resume_path:
            ok = upload_resume(app_id, resume_path)
            logger.info(f"[save_application] resume upload | app_id={app_id} ok={ok}")
        if cover_letter_path:
            ok = upload_cover_letter(app_id, cover_letter_path)
            logger.info(f"[save_application] cover_letter upload | app_id={app_id} ok={ok}")

        update_application(app_id, status="ready_to_apply")
        log_step(app_id, "save_application", "success", "Ready to apply", correlation_id)
        logger.info(f"[save_application] marked ready_to_apply | app_id={app_id}")
    else:
        logger.error("[save_application] could not create or find application record")

    state["application_id"] = None
    remaining = len(state.get("ranked_jobs", []))
    state.setdefault("step_log", []).append({"step": "save_application", "status": "done"})
    logger.info(f"[save_application] done | remaining_jobs={remaining}")
    return state
