import httpx
import os
from loguru import logger

from ..state import JobAgentState
from services.rails_client import log_step

_BASE = os.environ.get("RAILS_API_BASE", "http://localhost:3000")


def run(state: JobAgentState) -> JobAgentState:
    app_id = state.get("application_id")
    logger.info(f"[retry_failed_application] starting | app_id={app_id}")

    if not app_id:
        logger.error("[retry_failed_application] no application_id in state")
        state.setdefault("errors", []).append({"step": "retry", "msg": "no application_id"})
        return state

    try:
        with httpx.Client(base_url=_BASE, timeout=10) as c:
            r = c.get(f"/api/v1/applications/{app_id}")
            if r.is_success:
                app_data = r.json()
                state["resume_path"] = app_data.get("resume_path")
                state["cover_letter_path"] = app_data.get("cover_letter_path")
                current_job = app_data.get("job")
                if current_job:
                    state["current_job"] = current_job
                    state["ranked_jobs"] = [current_job]
                    logger.info(f"[retry_failed_application] loaded job | {current_job.get('title')} @ {current_job.get('company')}")
                else:
                    logger.warning("[retry_failed_application] no job found on application")
            else:
                logger.warning(f"[retry_failed_application] failed to fetch application | status={r.status_code}")
        log_step(app_id, "retry_failed_application", "info", "Retry initiated", state.get("correlation_id", ""))
    except Exception as e:
        logger.error(f"[retry_failed_application] error | {e}")
        state.setdefault("errors", []).append({"step": "retry_failed_application", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "retry_failed_application", "status": "done"})
    logger.info("[retry_failed_application] done")
    return state
