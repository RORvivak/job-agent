import httpx
import os
from loguru import logger
from ..state import JobAgentState
from resume_engine.parser import parse
from services.llm_limiter import llm_guarded

_BASE = os.environ.get("RAILS_API_BASE", "http://localhost:3000")


@llm_guarded(est_calls=1)
def run(state: JobAgentState) -> JobAgentState:
    user_id = state.get("user_id")
    logger.info(f"[parse_resume] starting | user_id={user_id}")
    try:
        with httpx.Client(base_url=_BASE, timeout=10) as c:
            r = c.get(f"/api/v1/users/{user_id}/active_resume")
            if r.is_success:
                data = r.json()
                resume_path = data.get("original_resume_path")
                state["resume_path"] = resume_path
                logger.info(f"[parse_resume] resume found | path={resume_path}")
                if resume_path and not data.get("parsed_data"):
                    logger.info("[parse_resume] parsing resume via LLM")
                    parsed = parse(resume_path)
                    state["parsed_resume"] = parsed
                    logger.info(f"[parse_resume] parsed | skills={parsed.get('skills', [])[:5]}")
                else:
                    state["parsed_resume"] = data.get("parsed_data", {})
                    logger.info("[parse_resume] using cached parsed data")
            else:
                logger.warning(f"[parse_resume] no active resume | status={r.status_code}")
    except Exception as e:
        logger.error(f"[parse_resume] error | {e}")
        state.setdefault("errors", []).append({"step": "parse_resume", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "parse_resume", "status": "done"})
    logger.info("[parse_resume] done")
    return state
