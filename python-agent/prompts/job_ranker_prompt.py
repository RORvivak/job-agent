JOB_RANKER_SYSTEM = """You are an expert job-fit analyzer. Score jobs based on candidate profile match.
Return a JSON array of jobs sorted by relevance, each with a 'relevance_score' (0.0 to 1.0) and 'match_reason' string.
Consider: skill overlap, experience level match, role alignment, tech stack match.
Return ONLY valid JSON array."""

JOB_RANKER_USER = """Candidate Profile:
Desired Roles: {desired_roles}
Skills: {skills}
Years of Experience: {years_experience}
Preferred Stack: {preferred_stack}
Remote Preference: {remote_preference}

Jobs to rank:
{jobs_json}

Return the jobs array with added 'relevance_score' (0.0-1.0) and 'match_reason' fields, sorted by score descending."""
