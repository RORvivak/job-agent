import asyncio
import random
from langchain_core.messages import SystemMessage, HumanMessage

from prompts.form_filler_prompt import FORM_FILLER_SYSTEM, FORM_FILLER_USER
from services.llm_limiter import get_llm


async def fill_form(page, candidate: dict) -> list[dict]:
    """Fill all form fields on a page using LLM for unknown fields."""
    filled = []
    inputs = await page.locator("input:visible, select:visible, textarea:visible").all()

    for inp in inputs:
        try:
            input_type = await inp.get_attribute("type") or "text"
            if input_type in ("hidden", "submit", "button", "file"):
                continue

            label = await _get_label(page, inp) or await inp.get_attribute("placeholder") or await inp.get_attribute("name") or ""
            options = []
            tag = await inp.evaluate("el => el.tagName.toLowerCase()")
            if tag == "select":
                options = await inp.locator("option").all_inner_texts()

            value = _try_direct_fill(label, input_type, options, candidate)
            if value is None:
                value = await _llm_fill(label, input_type, options, candidate)

            if value:
                await _fill_element(inp, tag, input_type, value, options)
                filled.append({"label": label, "value": value})
                await page.wait_for_timeout(random.randint(200, 600))
        except Exception:
            continue

    return filled


def _try_direct_fill(label: str, input_type: str, options: list, candidate: dict) -> str | None:
    label_lower = label.lower()
    mapping = {
        ("name", "full name"): candidate.get("name", ""),
        ("email",): candidate.get("email", ""),
        ("phone", "mobile", "telephone"): candidate.get("phone", ""),
        ("linkedin",): candidate.get("linkedin", ""),
        ("github",): candidate.get("github", ""),
        ("location", "city", "address"): candidate.get("location", ""),
        ("salary", "ctc", "compensation", "pay"): str(candidate.get("expected_salary", "")),
        ("notice", "notice period"): candidate.get("notice_period", "30 days"),
        ("experience", "years of experience"): str(candidate.get("years_experience", "")),
    }
    for keys, value in mapping.items():
        if any(k in label_lower for k in keys) and value:
            return value
    return None


async def _llm_fill(label: str, input_type: str, options: list, candidate: dict) -> str:
    try:
        llm = get_llm()
        prompt = FORM_FILLER_USER.format(
            label=label,
            field_type=input_type,
            options=", ".join(options) if options else "N/A",
            name=candidate.get("name", ""),
            email=candidate.get("email", ""),
            phone=candidate.get("phone", ""),
            linkedin=candidate.get("linkedin", ""),
            github=candidate.get("github", ""),
            location=candidate.get("location", ""),
            years_experience=candidate.get("years_experience", ""),
            notice_period=candidate.get("notice_period", "30 days"),
            expected_salary=candidate.get("expected_salary", ""),
            work_authorization=candidate.get("work_authorization", "Yes"),
            remote_preference=candidate.get("remote_preference", "Remote"),
        )
        messages = [SystemMessage(content=FORM_FILLER_SYSTEM), HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception:
        return ""


async def _fill_element(inp, tag: str, input_type: str, value: str, options: list) -> None:
    if tag == "select":
        for opt in options:
            if value.lower() in opt.lower():
                await inp.select_option(label=opt)
                return
        await inp.select_option(index=0)
    elif input_type == "checkbox":
        if value.lower() in ("yes", "true", "1"):
            await inp.check()
    elif input_type == "radio":
        await inp.check()
    else:
        await inp.fill(value)


async def _get_label(page, inp) -> str:
    try:
        input_id = await inp.get_attribute("id")
        if input_id:
            label = page.locator(f"label[for='{input_id}']")
            if await label.count() > 0:
                return (await label.inner_text()).strip()
        aria = await inp.get_attribute("aria-label")
        if aria:
            return aria.strip()
    except Exception:
        pass
    return ""
