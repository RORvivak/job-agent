from datetime import datetime
from loguru import logger

from ..state import JobAgentState
from services.rails_client import update_application, create_application, log_step


def run(state: JobAgentState) -> JobAgentState:
    app_id = state.get("application_id")
    apply_result = state.get("apply_result", {})
    correlation_id = state.get("correlation_id", "")
    job = state.get("current_job", {})
    user_id = state.get("user_id", 0)
    logger.info(f"[save_application] starting | job={job.get('title')} @ {job.get('company')} app_id={app_id}")

    if not app_id and job:
        logger.info("[save_application] creating new application record")
        app_id = create_application(user_id, job, correlation_id)
        logger.info(f"[save_application] application created | app_id={app_id}")

    if app_id:
        if apply_result.get("success"):
            update_application(
                app_id,
                status="applied",
                applied_at=datetime.utcnow().isoformat(),
                resume_path=state.get("customized_resume_path", ""),
                cover_letter_path=state.get("cover_letter_path", ""),
                screenshot_path=apply_result.get("screenshot_path", ""),
            )
            log_step(app_id, "save_application", "success", "Application submitted successfully", correlation_id)
            logger.info(f"[save_application] marked as applied | app_id={app_id}")
        else:
            error = apply_result.get("error", "unknown_error")
            update_application(
                app_id,
                status="failed",
                error_message=error,
                screenshot_path=apply_result.get("screenshot_path", ""),
                failed_step="apply_job",
            )
            log_step(app_id, "save_application", "failed", error, correlation_id)
            logger.warning(f"[save_application] marked as failed | app_id={app_id} error={error}")
    else:
        logger.error("[save_application] could not create or find application record")

    remaining = len(state.get("ranked_jobs", []))
    state.setdefault("step_log", []).append({"step": "save_application", "status": "done"})
    logger.info(f"[save_application] done | remaining_jobs={remaining}")
    return state
