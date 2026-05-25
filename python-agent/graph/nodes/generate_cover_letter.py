import os
import unicodedata
from datetime import date as _date
from pathlib import Path
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import JobAgentState
from prompts.cover_letter_prompt import COVER_LETTER_SYSTEM, COVER_LETTER_USER
from services.llm_limiter import get_llm, llm_guarded

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")


@llm_guarded(est_calls=1)
def run(state: JobAgentState) -> JobAgentState:
    job = state.get("current_job")
    parsed_resume = state.get("parsed_resume", {})
    prefs = state.get("preferences", {})
    user_id = state.get("user_id", 0)
    logger.info(f"[generate_cover_letter] starting | job={job.get('title')} @ {job.get('company')}" if job else "[generate_cover_letter] starting | no job")

    if not job:
        logger.warning("[generate_cover_letter] skipping — no current job")
        return state

    try:
        llm = get_llm()
        exp = parsed_resume.get("experience", [])
        full_experience = "\n".join(
            f"- {e.get('title')} at {e.get('company')} ({e.get('duration', '')})"
            for e in exp
        )
        all_skills = ", ".join(parsed_resume.get("skills", []))

        prompt = COVER_LETTER_USER.format(
            company=job.get("company", ""),
            title=job.get("title", ""),
            job_description=job.get("description", "")[:2500],
            resume_summary=parsed_resume.get("summary", ""),
            all_skills=all_skills,
            preferred_stack=", ".join(prefs.get("preferred_stack", [])),
            full_experience=full_experience,
            additional_info=prefs.get("additional_info", ""),
        )
        messages = [SystemMessage(content=COVER_LETTER_SYSTEM), HumanMessage(content=prompt)]
        logger.info("[generate_cover_letter] calling LLM")
        response = llm.invoke(messages)
        cover_letter_text = response.content

        job_slug = job.get("title", "job").lower().replace(" ", "_")[:30]
        out_dir = Path(STORAGE_DIR) / "cover_letters" / str(user_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = str(out_dir / f"{job_slug}_cover.pdf")

        candidate = parsed_resume.get("contact", {})
        _save_as_pdf(cover_letter_text, pdf_path, candidate, job.get("company", ""), job.get("title", ""))
        state["cover_letter_path"] = pdf_path
        logger.info(f"[generate_cover_letter] saved | path={pdf_path}")
    except Exception as e:
        logger.error(f"[generate_cover_letter] error | {e}")
        state.setdefault("errors", []).append({"step": "generate_cover_letter", "msg": str(e)})

    state.setdefault("step_log", []).append({"step": "generate_cover_letter", "status": "done"})
    logger.info("[generate_cover_letter] done")
    return state


def _safe(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("latin-1", errors="replace").decode("latin-1")


def _save_as_pdf(text: str, path: str, candidate: dict, company: str, role: str) -> None:
    from fpdf import FPDF

    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    pdf.set_left_margin(25)
    pdf.set_right_margin(25)

    # Candidate name
    name = candidate.get("name", "")
    if name:
        pdf.set_font("Helvetica", "B", 15)
        pdf.cell(0, 9, _safe(name))
        pdf.ln()

    # Contact line
    contact_parts = [x for x in [
        candidate.get("email"), candidate.get("phone"),
        candidate.get("linkedin"), candidate.get("location"),
    ] if x]
    if contact_parts:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, _safe("  |  ".join(contact_parts)))
        pdf.ln()

    # Horizontal rule
    y = pdf.get_y() + 2
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.3)
    pdf.line(25, y, 185, y)
    pdf.ln(7)

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _date.today().strftime("%B %d, %Y"))
    pdf.ln()
    pdf.ln(4)

    # Re: line
    if company or role:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, _safe(f"Re: {role} - {company}"))
        pdf.ln()
        pdf.ln(5)

    # Body paragraphs
    pdf.set_font("Helvetica", "", 10.5)
    for para in text.strip().split("\n\n"):
        para = para.strip().replace("\n", " ")
        if not para:
            continue
        pdf.multi_cell(0, 5.5, _safe(para))
        pdf.ln(3)

    pdf.output(path)
