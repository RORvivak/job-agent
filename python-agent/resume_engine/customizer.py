import json
import re
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.resume_prompt import CUSTOMIZE_RESUME_SYSTEM, CUSTOMIZE_RESUME_USER
from services.llm_limiter import get_llm


def customize(parsed_resume: dict, job: dict, prefs: dict = None) -> dict:
    prefs = prefs or {}
    llm = get_llm()
    prompt = CUSTOMIZE_RESUME_USER.format(
        company=job.get("company", ""),
        job_title=job.get("title", ""),
        job_description=job.get("description", "")[:4000],
        additional_info=prefs.get("additional_info", ""),
        preferred_stack=", ".join(prefs.get("preferred_stack", [])),
        resume_json=json.dumps(parsed_resume, indent=2)[:4000],
    )
    messages = [
        SystemMessage(content=CUSTOMIZE_RESUME_SYSTEM),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    raw = re.sub(r"^```(?:json)?\s*", "", response.content.strip())
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
        result["_job_id"] = job.get("id")
        result["_job_title"] = job.get("title")
        return result
    except json.JSONDecodeError:
        return {**parsed_resume, "_customization_failed": True}
