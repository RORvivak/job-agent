from loguru import logger
from ..state import JobAgentState
from services.rails_client import log_step, update_application


def run(state: JobAgentState) -> JobAgentState:
    errors = state.get("errors", [])
    app_id = state.get("application_id")
    correlation_id = state.get("correlation_id", "")
    logger.info(f"[error_handler] starting | errors={len(errors)} app_id={app_id}")

    for err in errors:
        msg = err.get("detail") or err.get("msg", "unknown")
        step = err.get("step", "unknown")

        if err.get("msg") == "llm_quota_exceeded":
            logger.warning(f"[error_handler] quota exceeded | step={step}")
            if app_id:
                update_application(app_id, status="paused_quota", error_message=msg)
            log_step(app_id or 0, step, "quota_exceeded", msg, correlation_id)
        else:
            logger.error(f"[error_handler] error | step={step} msg={msg}")
            if app_id:
                update_application(app_id, status="failed", error_message=msg, failed_step=step)
            log_step(app_id or 0, step, "error", msg, correlation_id)

    remaining = len(state.get("ranked_jobs", []))
    state.setdefault("step_log", []).append({"step": "error_handler", "status": "done"})
    logger.info(f"[error_handler] done | remaining_jobs={remaining}")
    return state
