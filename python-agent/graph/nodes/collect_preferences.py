import httpx
import os
from loguru import logger
from ..state import JobAgentState

_BASE = os.environ.get("RAILS_API_BASE", "http://localhost:3000")


def run(state: JobAgentState) -> JobAgentState:
    user_id = state.get("user_id")
    preference_ids = state.get("preference_ids")  # optional filter
    logger.info(f"[collect_preferences] starting | user_id={user_id} preference_ids={preference_ids}")

    try:
        with httpx.Client(base_url=_BASE, timeout=10) as c:
            r = c.get(f"/api/v1/users/{user_id}/preferences")
            if r.is_success:
                data = r.json()

                # If specific preference_ids were requested, filter the sets
                if preference_ids:
                    sets = [p for p in data.get("preference_sets", []) if p["id"] in preference_ids]
                    if sets:
                        # Rebuild merged view from the filtered sets
                        data["desired_roles"]   = list({r for p in sets for r in (p.get("desired_roles") or [])})
                        data["preferred_stack"] = list({s for p in sets for s in (p.get("preferred_stack") or [])})
                        data["locations"]       = list({l for p in sets for l in (p.get("locations") or [])})
                        data["additional_info"] = "; ".join(filter(None, [p.get("additional_info") for p in sets]))
                        data["preference_sets"] = sets
                        logger.info(f"[collect_preferences] filtered to {len(sets)} preference set(s)")

                state["preferences"] = data
                roles = data.get("desired_roles", [])
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
