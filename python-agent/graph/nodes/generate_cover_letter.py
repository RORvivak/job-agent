import os
from pathlib import Path
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from ..state import JobAgentState
from prompts.cover_letter_prompt import COVER_LETTER_SYSTEM, COVER_LETTER_USER
from services.llm_limiter import get_llm, llm_guarded

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")


@llm_guarded(est_calls=1)
def run(state: JobAgentState) -> JobAgentState:
    job = state.get("current_job")
    parsed_resume = state.get("parsed_resume", {})
    user_id = state.get("user_id", 0)
    logger.info(f"[generate_cover_letter] starting | job={job.get('title')} @ {job.get('company')}" if job else "[generate_cover_letter] starting | no job")

    if not job:
        logger.warning("[generate_cover_letter] skipping — no current job")
        return state

    try:
        llm = get_llm()
        exp = parsed_resume.get("experience", [])
        key_exp = "; ".join([f"{e.get('title')} at {e.get('company')}" for e in exp[:3]])
        skills = ", ".join(parsed_resume.get("skills", [])[:10])

        prompt = COVER_LETTER_USER.format(
            company=job.get("company", ""),
            title=job.get("title", ""),
            job_description=job.get("description", "")[:2000],
            resume_summary=parsed_resume.get("summary", ""),
            top_skills=skills,
            key_experience=key_exp,
        )
        messages = [SystemMessage(content=COVER_LETTER_SYSTEM), HumanMessage(content=prompt)]
        logger.info("[generate_cover_letter] calling LLM")
        response = llm.invoke(messages)
        cover_letter_text = response.content

        job_slug = job.get("title", "job").lower().replace(" ", "_")[:30]
        out_dir = Path(STORAGE_DIR) / "cover_letters" / str(user_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(out_dir / f"{job_slug}_cover.pdf")

        _save_as_pdf(cover_letter_text, pdf_path)
        state["cover_letter_path"] = pdf_path
        logger.info(f"[generate_cover_letter] saved | path={pdf_path}")
    except Exception as e:
        logger.error(f"[generate_cover_letter] error | {e}")
        state.setdefault("errors", []).append({"step": "generate_cover_letter", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "generate_cover_letter", "status": "done"})
    logger.info("[generate_cover_letter] done")
    return state


def _save_as_pdf(text: str, path: str) -> None:
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph(line or "&nbsp;", styles["Normal"]) for line in text.split("\n")]
    doc.build(story)
