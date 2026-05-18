import json
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import JobAgentState
from prompts.job_ranker_prompt import JOB_RANKER_SYSTEM, JOB_RANKER_USER
from services.llm_limiter import get_llm, llm_guarded


@llm_guarded(est_calls=1)
def run(state: JobAgentState) -> JobAgentState:
    jobs = state.get("jobs", [])
    logger.info(f"[rank_jobs] starting | jobs={len(jobs)}")

    if not jobs:
        logger.warning("[rank_jobs] no jobs to rank")
        state["ranked_jobs"] = []
        return state

    prefs = state.get("preferences", {})
    parsed_resume = state.get("parsed_resume", {})

    try:
        llm = get_llm()
        prompt = JOB_RANKER_USER.format(
            desired_roles=", ".join(prefs.get("desired_roles", [])),
            skills=", ".join(parsed_resume.get("skills", [])[:20]),
            years_experience=prefs.get("years_experience", ""),
            preferred_stack=", ".join(prefs.get("preferred_stack", [])),
            remote_preference=prefs.get("remote_preference", ""),
            jobs_json=json.dumps([{k: v for k, v in j.items() if k != "description"} for j in jobs], indent=2)[:3000],
        )
        messages = [SystemMessage(content=JOB_RANKER_SYSTEM), HumanMessage(content=prompt)]
        logger.info("[rank_jobs] calling LLM to rank jobs")
        response = llm.invoke(messages)

        ranked = json.loads(response.content)
        job_map = {j["job_url"]: j for j in jobs}
        for r in ranked:
            if r.get("job_url") in job_map:
                job_map[r["job_url"]].update({
                    "relevance_score": r.get("relevance_score", 0),
                    "match_reason": r.get("match_reason", ""),
                })
        state["ranked_jobs"] = sorted(jobs, key=lambda j: j.get("relevance_score", 0), reverse=True)
        top = state["ranked_jobs"][0] if state["ranked_jobs"] else {}
        logger.info(f"[rank_jobs] ranked | top_job={top.get('title')} @ {top.get('company')} score={top.get('relevance_score')}")
    except Exception as e:
        logger.error(f"[rank_jobs] error | {e}")
        state["ranked_jobs"] = jobs

    state.setdefault("step_log", []).append({"step": "rank_jobs", "status": "done"})
    logger.info(f"[rank_jobs] done | ranked={len(state['ranked_jobs'])}")
    return state
