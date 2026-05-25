JOB_RANKER_SYSTEM = """You are an expert job-fit analyzer. Score jobs based on how well they match the candidate profile.
Return a JSON array of jobs sorted by relevance. Each object must have:
  - job_url: string (unchanged)
  - relevance_score: float 0.0–1.0
  - match_reason: one sentence explaining the score
Consider: skill overlap, role title match, tech stack match, experience level, job description requirements.
Penalize jobs that require skills the candidate clearly lacks.
Return ONLY a valid JSON array, no markdown."""

JOB_RANKER_USER = """Candidate Profile:
Desired Roles: {desired_roles}
Skills: {skills}
Years of Experience: {years_experience}
Preferred Stack: {preferred_stack}
Remote Preference: {remote_preference}
Additional Context: {additional_info}

Jobs to rank:
{jobs_json}

Return the jobs array with relevance_score and match_reason added, sorted by score descending."""
