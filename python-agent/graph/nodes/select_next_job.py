from loguru import logger
from ..state import JobAgentState


def run(state: JobAgentState) -> JobAgentState:
    ranked = state.get("ranked_jobs", [])
    if ranked:
        state["current_job"] = ranked[0]
        state["ranked_jobs"] = ranked[1:]
        job = ranked[0]
        logger.info(f"[select_next_job] selected | {job.get('title')} @ {job.get('company')} | remaining={len(ranked) - 1}")
    else:
        state["current_job"] = None
        logger.warning("[select_next_job] no jobs remaining")

    state.setdefault("step_log", []).append({"step": "select_next_job", "status": "done"})
    return state
