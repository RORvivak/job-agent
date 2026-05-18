import httpx
import os
from loguru import logger
from ..state import JobAgentState

_BASE = os.environ.get("RAILS_API_BASE", "http://localhost:3000")


def run(state: JobAgentState) -> JobAgentState:
    user_id = state.get("user_id")
    logger.info(f"[collect_preferences] starting | user_id={user_id}")
    try:
        with httpx.Client(base_url=_BASE, timeout=10) as c:
            r = c.get(f"/api/v1/users/{user_id}/preferences")
            if r.is_success:
                state["preferences"] = r.json()
                roles = state["preferences"].get("desired_roles", [])
                logger.info(f"[collect_preferences] fetched prefs | roles={roles}")
            else:
                logger.warning(f"[collect_preferences] failed to fetch prefs | status={r.status_code}")
                state.setdefault("preferences", {})
    except Exception as e:
        logger.error(f"[collect_preferences] error | {e}")
        state.setdefault("preferences", {})
        state.setdefault("errors", []).append({"step": "collect_preferences", "msg": str(e)})

    state.setdefault("errors", [])
    state.setdefault("step_log", []).append({"step": "collect_preferences", "status": "done"})
    logger.info("[collect_preferences] done")
    return state
