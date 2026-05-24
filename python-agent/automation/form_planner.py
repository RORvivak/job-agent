import base64
import json
import re
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage


SYSTEM_PROMPT = (
    "You are an expert at analyzing job application forms from screenshots. "
    "Given one or more screenshots of a job application page and a candidate profile, "
    "return ONLY a valid JSON object describing every visible form field and how to fill it. "
    "No markdown, no explanation — raw JSON only."
)

USER_TEMPLATE = """Candidate profile:
Name: {name}
Email: {email}
Phone: {phone}
LinkedIn: {linkedin}
GitHub: {github}
Location: {location}
Years of Experience: {years_experience}
Expected Salary: {expected_salary}
Work Authorization: Yes
Notice Period: 30 days
Resume path: {resume_path}
Cover letter path: {cover_letter_path}

Analyze the form screenshot(s) above. Return this exact JSON schema (fill every field you can see):
{{
  "ats_type": "greenhouse|lever|workable|ashby|other",
  "actions": [
    {{"action": "fill",   "label": "First Name",    "value": "...", "hints": ["first_name", "firstName"]}},
    {{"action": "fill",   "label": "Last Name",     "value": "...", "hints": ["last_name"]}},
    {{"action": "fill",   "label": "Email",         "value": "...", "hints": ["email"]}},
    {{"action": "fill",   "label": "Phone",         "value": "...", "hints": ["phone", "mobile"]}},
    {{"action": "fill",   "label": "LinkedIn URL",  "value": "...", "hints": ["linkedin"]}},
    {{"action": "upload", "label": "Resume",        "value": "{resume_path}", "hints": ["resume", "cv"]}},
    {{"action": "upload", "label": "Cover Letter",  "value": "{cover_letter_path}", "hints": ["cover_letter", "cover"]}},
    {{"action": "submit", "label": "Submit Application"}}
  ],
  "notes": "brief observation about the form"
}}

Include ONLY actions for fields actually visible in the screenshots. Add any additional fields (dropdowns, checkboxes, textareas) you see beyond the template above. The "hints" array should contain likely name/id/placeholder attribute values for the field."""


def _fallback_plan(resume_path: str, cover_letter_path: str) -> dict:
    return {
        "ats_type": "other",
        "actions": [
            {"action": "upload", "label": "Resume", "value": resume_path, "hints": ["resume", "cv"]},
            {"action": "submit", "label": "Submit"},
        ],
        "notes": "fallback plan — LLM parse failed",
    }


def plan_form(llm, screenshots: list[str], candidate: dict, resume_path: str, cover_letter_path: str) -> dict:
    if not screenshots:
        logger.warning("[form_planner] no screenshots provided, using fallback plan")
        return _fallback_plan(resume_path, cover_letter_path)

    # Build image content blocks
    content = []
    for path in screenshots:
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })
        except Exception as e:
            logger.warning(f"[form_planner] could not read screenshot {path}: {e}")

    if not content:
        return _fallback_plan(resume_path, cover_letter_path)

    user_text = USER_TEMPLATE.format(
        name=candidate.get("name", ""),
        email=candidate.get("email", ""),
        phone=candidate.get("phone", ""),
        linkedin=candidate.get("linkedin", ""),
        github=candidate.get("github", ""),
        location=candidate.get("location", ""),
        years_experience=candidate.get("years_experience", ""),
        expected_salary=candidate.get("expected_salary", ""),
        resume_path=resume_path,
        cover_letter_path=cover_letter_path,
    )
    content.append({"type": "text", "text": user_text})

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=content)]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        plan = json.loads(raw)
        logger.info(f"[form_planner] plan parsed | ats={plan.get('ats_type')} actions={len(plan.get('actions', []))}")
        return plan
    except Exception as e:
        logger.error(f"[form_planner] failed to parse LLM response: {e}")
        return _fallback_plan(resume_path, cover_letter_path)
