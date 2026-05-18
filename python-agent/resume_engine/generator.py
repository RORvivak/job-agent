import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT
from docx import Document


def to_pdf(data: dict, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    story = []

    contact = data.get("contact", {})
    name = contact.get("name", "Candidate")
    story.append(Paragraph(f"<b>{name}</b>", ParagraphStyle("Name", fontSize=16, spaceAfter=4)))
    contact_line = " | ".join(filter(None, [
        contact.get("email"), contact.get("phone"),
        contact.get("linkedin"), contact.get("github"), contact.get("location")
    ]))
    story.append(Paragraph(contact_line, styles["Normal"]))
    story.append(Spacer(1, 0.1*inch))

    if data.get("summary"):
        story.append(Paragraph("<b>SUMMARY</b>", ParagraphStyle("Section", fontSize=12, spaceBefore=8, spaceAfter=4)))
        story.append(Paragraph(data["summary"], styles["Normal"]))
        story.append(Spacer(1, 0.1*inch))

    if data.get("skills"):
        story.append(Paragraph("<b>SKILLS</b>", ParagraphStyle("Section", fontSize=12, spaceBefore=8, spaceAfter=4)))
        story.append(Paragraph(", ".join(data["skills"]), styles["Normal"]))
        story.append(Spacer(1, 0.1*inch))

    if data.get("experience"):
        story.append(Paragraph("<b>EXPERIENCE</b>", ParagraphStyle("Section", fontSize=12, spaceBefore=8, spaceAfter=4)))
        for exp in data["experience"]:
            story.append(Paragraph(f"<b>{exp.get('title')}</b> — {exp.get('company')} ({exp.get('duration', '')})", styles["Normal"]))
            for bullet in exp.get("bullets", []):
                story.append(Paragraph(f"• {bullet}", styles["Normal"]))
            story.append(Spacer(1, 0.05*inch))

    if data.get("education"):
        story.append(Paragraph("<b>EDUCATION</b>", ParagraphStyle("Section", fontSize=12, spaceBefore=8, spaceAfter=4)))
        for edu in data["education"]:
            story.append(Paragraph(f"{edu.get('degree')} — {edu.get('institution')} ({edu.get('year', '')})", styles["Normal"]))

    if data.get("projects"):
        story.append(Paragraph("<b>PROJECTS</b>", ParagraphStyle("Section", fontSize=12, spaceBefore=8, spaceAfter=4)))
        for proj in data["projects"]:
            techs = ", ".join(proj.get("technologies", []))
            story.append(Paragraph(f"<b>{proj.get('name')}</b> ({techs})", styles["Normal"]))
            story.append(Paragraph(proj.get("description", ""), styles["Normal"]))
            story.append(Spacer(1, 0.05*inch))

    doc.build(story)
    return output_path


def to_docx(data: dict, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = Document()

    contact = data.get("contact", {})
    doc.add_heading(contact.get("name", "Candidate"), 0)
    contact_line = " | ".join(filter(None, [
        contact.get("email"), contact.get("phone"),
        contact.get("linkedin"), contact.get("github")
    ]))
    doc.add_paragraph(contact_line)

    if data.get("summary"):
        doc.add_heading("Summary", level=1)
        doc.add_paragraph(data["summary"])

    if data.get("skills"):
        doc.add_heading("Skills", level=1)
        doc.add_paragraph(", ".join(data["skills"]))

    if data.get("experience"):
        doc.add_heading("Experience", level=1)
        for exp in data["experience"]:
            doc.add_paragraph(f"{exp.get('title')} — {exp.get('company')} ({exp.get('duration', '')})", style="List Bullet")
            for bullet in exp.get("bullets", []):
                doc.add_paragraph(f"• {bullet}")

    if data.get("education"):
        doc.add_heading("Education", level=1)
        for edu in data["education"]:
            doc.add_paragraph(f"{edu.get('degree')} — {edu.get('institution')} ({edu.get('year', '')})")

    if data.get("projects"):
        doc.add_heading("Projects", level=1)
        for proj in data["projects"]:
            doc.add_paragraph(f"{proj.get('name')}: {proj.get('description', '')}")

    doc.save(output_path)
    return output_path
