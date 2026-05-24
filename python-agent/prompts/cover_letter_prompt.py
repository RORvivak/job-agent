COVER_LETTER_SYSTEM = """You are an expert cover letter writer. Write compelling, personalized cover letters.
RULES:
- Keep it to 3-4 paragraphs
- Be specific about the company and role
- Highlight 2-3 most relevant achievements
- Never fabricate experience
- Sound human and genuine, not template-like"""

COVER_LETTER_USER = """Write a cover letter for this application:

Company: {company}
Role: {title}
Job Description: {job_description}

Candidate Profile:
{resume_summary}

Top Skills: {top_skills}
Key Experience: {key_experience}
Additional Info: {additional_info}

Return the cover letter as plain text, ready to paste."""
