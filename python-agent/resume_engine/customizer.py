import json
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.resume_prompt import CUSTOMIZE_RESUME_SYSTEM, CUSTOMIZE_RESUME_USER
from services.llm_limiter import get_llm


def customize(parsed_resume: dict, job: dict) -> dict:
    llm = get_llm()
    prompt = CUSTOMIZE_RESUME_USER.format(
        job_description=job.get("description", "")[:4000],
        resume_json=json.dumps(parsed_resume, indent=2)[:4000],
    )
    messages = [
        SystemMessage(content=CUSTOMIZE_RESUME_SYSTEM),
        HumanMessage(content=prompt),
    ]
    response = llm.invoke(messages)
    try:
        result = json.loads(response.content)
        result["_job_id"] = job.get("id")
        result["_job_title"] = job.get("title")
        return result
    except json.JSONDecodeError:
        return {**parsed_resume, "_customization_failed": True}
